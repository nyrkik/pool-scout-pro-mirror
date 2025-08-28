#!/usr/bin/env python3
import os
import re
import sqlite3
import sys
from datetime import datetime
from collections import defaultdict

# ---- Adjust these paths if needed ----
DB_PATH = "data/inspection_data.db"
REPORTS_DIR = "/mnt/nas/pool_scout_pro/reports"

# Make both the project root and src/ importable
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC_DIR = os.path.join(PROJECT_ROOT, "src")
for p in (PROJECT_ROOT, SRC_DIR):
    if p not in sys.path:
        sys.path.insert(0, p)

# Import your extractor (it lives in src/services) and is already wired to parse text
from services.pdf_extractor import PDFExtractor  # uses your updated function

# -------------------------------------------------------------------
# Filename parsing rules (accept both strict and legacy variants)
# Expected/Preferred:  YYYYMMDD_FACILITYNOSPACES_IDSUFFIX.pdf
# Legacy accepted:     YYYYMMDD_FACILITY.pdf
# Where:
#   - YYYYMMDD is 8 digits
#   - FACILITYNOSPACES can contain letters/digits/underscores/dashes (we normalize anyway)
#   - IDSUFFIX is typically the last segment of the UUID from the URL (A-F0-9+ letters/digits)
# -------------------------------------------------------------------
FNAME_STRICT = re.compile(
    r"^(?P<date>\d{8})_(?P<facility>[^_]+)_(?P<suffix>[A-Za-z0-9]+)\.pdf$",
    re.I,
)
FNAME_WITH_TAIL = re.compile(
    r"^(?P<date>\d{8})_(?P<facility>.+?)_(?P<suffix>[^/]+?)\.pdf$",
    re.I,
)
FNAME_NO_SUFFIX = re.compile(
    r"^(?P<date>\d{8})_(?P<facility>.+?)\.pdf$",
    re.I,
)

def norm_name(s: str) -> str:
    """
    Normalize facility names for matching (case/spacing/punct tolerant).
    Also maps '&' -> 'and' before stripping non-alnum.
    """
    s = (s or "").strip().lower()
    s = s.replace("&", "and")
    s = re.sub(r"[^a-z0-9]+", "", s)  # drop non-alnum
    return s

def parse_fname(fname: str):
    """
    Return (iso_date, facility_token_raw, suffix_or_none) or None if format not recognized.
    - iso_date is 'YYYY-MM-DD'
    - facility_token_raw is whatever appears in the filename (we will normalize as needed)
    - suffix_or_none is the trailing token after the last underscore, if present
    """
    base = os.path.basename(fname)
    m = FNAME_STRICT.match(base) or FNAME_WITH_TAIL.match(base) or FNAME_NO_SUFFIX.match(base)
    if not m:
        return None
    yyyymmdd = m.group("date")
    try:
        dt = datetime.strptime(yyyymmdd, "%Y%m%d").date()
        iso = dt.isoformat()
    except Exception:
        return None
    facility = m.group("facility")
    suffix = m.groupdict().get("suffix")
    # Clean obvious trailing .pdf fragments if any edge-case captured
    if suffix:
        suffix = suffix.replace(".pdf", "")
    return (iso, facility, suffix)

def has_column(cur: sqlite3.Cursor, table: str, col: str) -> bool:
    cur.execute(f"PRAGMA table_info({table})")
    info = cur.fetchall()
    for row in info:
        # row: cid, name, type, notnull, dflt_value, pk
        if str(row[1]).lower() == col.lower():
            return True
    return False

def last_uuid_segment(uuid_str: str) -> str:
    """
    Return the trailing segment after the last '-' in a UUID-like string.
    If no hyphen is present, return the string uppercased.
    """
    if not uuid_str:
        return ""
    seg = uuid_str.split("-")[-1]
    return seg.upper()

def pick_first(seq):
    for x in seq:
        return x
    return None

def main():
    # Safety checks
    if not os.path.isdir(REPORTS_DIR):
        print(f"ERROR: reports dir not found: {REPORTS_DIR}", file=sys.stderr)
        return 2
    if not os.path.exists(DB_PATH):
        print(f"ERROR: DB not found: {DB_PATH}", file=sys.stderr)
        return 2

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # Detect if inspection_reports has a full inspection_id column
    has_inspection_id = has_column(cur, "inspection_reports", "inspection_id")

    # Load all reports with necessary fields
    # We always need: id, inspection_date, facility_id, facility name
    base_sql = """
        SELECT r.id AS report_id,
               r.inspection_date,
               r.facility_id,
               f.name AS facility
        {maybe_id}
        FROM inspection_reports r
        JOIN facilities f ON f.id = r.facility_id
    """
    maybe_id = ", r.inspection_id" if has_inspection_id else ""
    cur.execute(base_sql.format(maybe_id=maybe_id))
    rows = cur.fetchall()

    # Build lookups
    # 1) (date + normalized facility) -> [reports]
    reports_by_key = defaultdict(list)
    # 2) ID suffix (last UUID segment uppercased) -> [reports]  (only if we have inspection_id)
    reports_by_suffix = defaultdict(list) if has_inspection_id else None

    for r in rows:
        key = (r["inspection_date"], norm_name(r["facility"]))
        reports_by_key[key].append(dict(r))
        if has_inspection_id:
            suffix = last_uuid_segment(r["inspection_id"])
            if suffix:
                reports_by_suffix[suffix].append(dict(r))

    # For end-of-run accounting: which DB report-keys we saw PDFs for (by date+name)
    db_report_keys = set(reports_by_key.keys())
    pdf_seen_keys = set()

    extractor = PDFExtractor()

    processed = 0
    updated   = 0
    skipped_name = 0

    unmatched_no_report = []   # PDFs that matched no DB report (even by suffix)
    unmatched_multi = []       # PDFs that matched >1 DB reports after both passes
    parse_failures = []        # PDFs that failed during text/extraction

    # Prepare insert for equipment
    EQUIP_COLS = [
        "report_id","facility_id",
        "pool_capacity_gallons","flow_rate_gpm",
        "filter_pump_1_make","filter_pump_1_model","filter_pump_1_hp",
        "filter_pump_2_make","filter_pump_2_model","filter_pump_2_hp",
        "filter_pump_3_make","filter_pump_3_model","filter_pump_3_hp",
        "jet_pump_1_make","jet_pump_1_model","jet_pump_1_hp",
        "jet_pump_2_make","jet_pump_2_model","jet_pump_2_hp",
        "filter_1_type","filter_1_make","filter_1_model","filter_1_capacity_gpm",
        "filter_2_type","filter_2_make","filter_2_model","filter_2_capacity_gpm",
        "sanitizer_1_type","sanitizer_1_details",
        "sanitizer_2_type","sanitizer_2_details",
        "main_drain_type","main_drain_model","main_drain_install_date",
        "equalizer_model","equalizer_install_date",
        "equipment_matches_emd",
        "filter_notes","pump_notes","jet_pump_notes","sanitizer_notes","main_drain_notes","equalizer_notes","equipment_notes"
    ]
    placeholders = ",".join("?" for _ in EQUIP_COLS)
    insert_sql = f"INSERT INTO equipment ({','.join(EQUIP_COLS)}) VALUES ({placeholders})"

    pdf_count = 0

    for root, _, files in os.walk(REPORTS_DIR):
        for f in files:
            if not f.lower().endswith(".pdf"):
                continue
            pdf_count += 1
            full = os.path.join(root, f)

            parsed = parse_fname(f)
            if not parsed:
                print(f"[skip name] {f}")
                skipped_name += 1
                continue

            iso_date, fac_raw, suffix = parsed
            candidates = []

            # Try ID-suffix match first (only if DB has inspection_id and filename had a suffix)
            if has_inspection_id and suffix:
                suffix_u = suffix.upper()
                cand_by_suffix = reports_by_suffix.get(suffix_u, [])
                if cand_by_suffix:
                    # If more than one, try to disambiguate by date
                    if len(cand_by_suffix) > 1:
                        cand_by_suffix = [c for c in cand_by_suffix if c["inspection_date"] == iso_date] or cand_by_suffix
                    candidates = cand_by_suffix

            # If no candidates by suffix, fall back to (date + normalized facility)
            if not candidates:
                key = (iso_date, norm_name(fac_raw))
                candidates = reports_by_key.get(key)

                # Be lenient: replace '_' and '-' with spaces and retry normalization
                if not candidates:
                    fac_alt = fac_raw.replace("_", " ").replace("-", " ")
                    key2 = (iso_date, norm_name(fac_alt))
                    candidates = reports_by_key.get(key2)
                    if candidates:
                        # We found a lenient match; treat key2 as the "seen" key for coverage
                        seen_key = key2
                    else:
                        seen_key = key
                else:
                    seen_key = key
            else:
                # For coverage stats, synthesize a normalized key from the first candidate
                c0 = candidates[0]
                seen_key = (c0["inspection_date"], norm_name(c0["facility"]))

            if not candidates:
                unmatched_no_report.append({
                    "file": f, "date": iso_date, "facility": fac_raw, "suffix": suffix
                })
                print(f"[unmatched NO REPORT] {f} -> date={iso_date}, name='{fac_raw}', suffix='{suffix}'")
                continue

            if len(candidates) > 1:
                unmatched_multi.append({
                    "file": f, "date": iso_date, "facility": fac_raw, "suffix": suffix,
                    "report_ids": [c["report_id"] for c in candidates]
                })
                print(f"[unmatched MULTI] {f} -> {len(candidates)} candidates: "
                      f"{[c['report_id'] for c in candidates]}")
                continue

            rpt = pick_first(candidates)
            report_id   = rpt["report_id"]
            facility_id = rpt["facility_id"]
            facility_nm = rpt["facility"]

            processed += 1
            pdf_seen_keys.add(seen_key)
            print(f"[rebuild] report_id={report_id} date={iso_date} facility='{facility_nm}' <- {f}")

            # --- get PDF text using whatever API the extractor exposes ---
            try:
                if hasattr(extractor, "_extract_pdf_text"):
                    pdf_text = extractor._extract_pdf_text(full)
                elif hasattr(extractor, "extract_text"):
                    pdf_text = extractor.extract_text(full)
                elif hasattr(extractor, "get_pdf_text"):
                    pdf_text = extractor.get_pdf_text(full)
                elif hasattr(extractor, "_get_pdf_text"):
                    pdf_text = extractor._get_pdf_text(full)
                else:
                    raise RuntimeError(
                        "PDFExtractor has no method to extract text. "
                        "Expected _extract_pdf_text / extract_text / get_pdf_text / _get_pdf_text."
                    )
                if not isinstance(pdf_text, str):
                    raise RuntimeError(f"Expected string from extractor, got {type(pdf_text)}")

                # Parse equipment from the raw text
                if hasattr(extractor, "_extract_equipment_comprehensive"):
                    equip = extractor._extract_equipment_comprehensive(pdf_text)
                else:
                    # Fallback: try public method if you exposed one
                    if hasattr(extractor, "extract_equipment_comprehensive"):
                        equip = extractor.extract_equipment_comprehensive(pdf_text)
                    else:
                        raise RuntimeError("Extractor missing _extract_equipment_comprehensive()")
            except Exception as e:
                parse_failures.append({
                    "file": f, "date": iso_date, "facility": fac_raw,
                    "report_id": report_id, "error": str(e)
                })
                print(f"[parse FAIL] {f} -> report_id={report_id}: {e}")
                continue

            # DELETE old equipment rows for this report
            cur.execute("DELETE FROM equipment WHERE report_id = ?", (report_id,))

            # Prepare values with defaults
            def gv(k): return equip.get(k)
            values = [
                report_id, facility_id,
                gv("pool_capacity_gallons"), gv("flow_rate_gpm"),
                gv("filter_pump_1_make"), gv("filter_pump_1_model"), gv("filter_pump_1_hp"),
                gv("filter_pump_2_make"), gv("filter_pump_2_model"), gv("filter_pump_2_hp"),
                gv("filter_pump_3_make"), gv("filter_pump_3_model"), gv("filter_pump_3_hp"),
                gv("jet_pump_1_make"), gv("jet_pump_1_model"), gv("jet_pump_1_hp"),
                gv("jet_pump_2_make"), gv("jet_pump_2_model"), gv("jet_pump_2_hp"),
                gv("filter_1_type"), gv("filter_1_make"), gv("filter_1_model"), gv("filter_1_capacity_gpm"),
                gv("filter_2_type"), gv("filter_2_make"), gv("filter_2_model"), gv("filter_2_capacity_gpm"),
                gv("sanitizer_1_type"), gv("sanitizer_1_details"),
                gv("sanitizer_2_type"), gv("sanitizer_2_details"),
                gv("main_drain_type"), gv("main_drain_model"), gv("main_drain_install_date"),
                gv("equalizer_model"), gv("equalizer_install_date"),
                True,  # equipment_matches_emd default
                gv("filter_notes"), gv("pump_notes"), gv("jet_pump_notes"), gv("sanitizer_notes"),
                gv("main_drain_notes"), gv("equalizer_notes"), gv("equipment_notes"),
            ]
            cur.execute(insert_sql, values)

            updated += 1
            # commit in small batches to avoid large transactions
            if updated % 50 == 0:
                conn.commit()

    conn.commit()
    conn.close()

    # Reports in DB that had no matching PDF seen in this run (by date+name)
    missing_pdf_keys = sorted(db_report_keys - pdf_seen_keys)
    db_missing = [{"date": d, "norm_name": n} for (d, n) in missing_pdf_keys]

    # ---------------------------- Summary ----------------------------
    print("\n========== REBUILD SUMMARY ==========")
    print(f"PDFs found: {pdf_count}")
    print(f"Processed (matched & attempted): {processed}")
    print(f"Updated (rows inserted): {updated}")
    print(f"Skipped (filename format not recognized): {skipped_name}")
    print(f"Unmatched NO REPORT (PDFs with no DB report): {len(unmatched_no_report)}")
    print(f"Unmatched MULTI (PDFs matched >1 DB report): {len(unmatched_multi)}")
    print(f"Parse failures (extraction errors): {len(parse_failures)}")
    print(f"DB reports with NO matching PDF in this run: {len(missing_pdf_keys)}")

    def preview(items, keys, label, maxn=8):
        if not items:
            return
        print(f"\n--- {label} (showing up to {maxn}) ---")
        for i, row in enumerate(items[:maxn], 1):
            want = ", ".join(f"{k}={row.get(k)}" for k in keys)
            print(f"{i:>2}. {want}")

    preview(unmatched_no_report, ["file", "date", "facility", "suffix"], "UNMATCHED: PDFs with no DB report")
    preview(unmatched_multi, ["file", "date", "facility", "suffix", "report_ids"], "UNMATCHED: PDFs matching >1 DB report")
    preview(parse_failures, ["file", "date", "facility", "report_id", "error"], "PARSE FAILURES")
    preview(db_missing, ["date", "norm_name"], "DB REPORTS missing PDFs (by normalized key)")

    print("=====================================\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
