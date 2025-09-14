import requests
import json
import logging
import os
import sqlite3
import hashlib

# --- Configuration ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
OLLAMA_ENDPOINT = os.getenv("OLLAMA_ENDPOINT", "http://localhost:11434/api/generate")
MODEL_NAME = os.getenv("OLLAMA_MODEL", "llama3")
DB_PATH = 'data/inspection_data.db'

# --- Database Interaction ---
def get_cached_summary(cursor: sqlite3.Cursor, violation_code: str) -> str | None:
    """Checks the cache for an existing summary using the violation code."""
    cursor.execute("SELECT shorthand_summary FROM violation_summary_cache WHERE fingerprint = ?", (violation_code,))
    result = cursor.fetchone()
    return result[0] if result else None

def save_summary_to_cache(cursor: sqlite3.Cursor, violation_code: str, title: str, summary: str):
    """Saves a new summary to the cache using the violation code as the fingerprint."""
    cursor.execute(
        "INSERT INTO violation_summary_cache (fingerprint, original_title, original_observations, shorthand_summary) VALUES (?, ?, ?, ?)",
        (violation_code, title, "N/A - Generic Summary", summary)
    )

# --- AI Summarization ---
def _call_ollama(title: str) -> str | None:
    """Internal function to call the Ollama LLM with a generic prompt."""
    prompt = (
        "You are an expert at creating concise labels for swimming pool violations. "
        "Based ONLY on the violation title, create a short, descriptive summary. "
        "For example, if the title is 'MINIMUM pH LEVEL', the output should be 'Low pH Level'. "
        "If the title is 'MAXIMUM DISINFECTANT RESIDUAL', the output should be 'High Disinfectant Level'. "
        "If the title is 'VGB SUCTION COVERS', the output should be 'VGB Suction Covers'. "
        "Be direct and do not add any extra explanations or markdown.\n\n"
        f"Violation Title: \"{title}\""
    )
    payload = {
        "model": MODEL_NAME, "prompt": prompt, "stream": False,
        "options": {"temperature": 0.0}
    }
    try:
        response = requests.post(OLLAMA_ENDPOINT, json=payload, timeout=45)
        response.raise_for_status()
        response_json = response.json()
        summary = response_json.get("response", "").strip().replace('"', '')
        return summary if summary else None
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to connect to Ollama at {OLLAMA_ENDPOINT}: {e}")
        return None

# --- Main Public Function ---
def summarize_violation(title: str, violation_code: str, cursor: sqlite3.Cursor) -> str | None:
    """
    Generates a generic shorthand summary for a violation type, using a cache.
    """
    if not title or not violation_code:
        return None

    try:
        cached_summary = get_cached_summary(cursor, violation_code)
        if cached_summary:
            # Changed from .info to .debug for quieter logging
            logging.debug(f"Cache HIT for violation code '{violation_code}'.")
            return cached_summary

        logging.info(f"Cache MISS for violation code '{violation_code}'. Calling AI.")
        new_summary = _call_ollama(title)

        if new_summary:
            save_summary_to_cache(cursor, violation_code, title, new_summary)

        return new_summary
    except sqlite3.Error as e:
        logging.error(f"Database error in summarizer: {e}")
        return None

if __name__ == '__main__':
    # Standalone test requires its own DB connection
    try:
        with sqlite3.connect(DB_PATH) as conn:
            test_cursor = conn.cursor()
            print("--- Running Violation Summarizer Test with Caching ---")
            test_cases = [
                {"title": "MAXIMUM DISINFECTANT RESIDUAL", "code": "10b"},
                {"title": "MINIMUM pH LEVEL", "code": "12a"},
                {"title": "MAXIMUM DISINFECTANT RESIDUAL", "code": "10b"} # Duplicate to test hit
            ]
            for case in test_cases:
                print(f"\nInput: {case['title']}")
                summary = summarize_violation(case['title'], case['code'], cursor=test_cursor)
                print(f"--> Summary: {summary or 'Failed'}")
            conn.commit()
    except sqlite3.Error as e:
        print(f"Test failed due to DB error: {e}")
