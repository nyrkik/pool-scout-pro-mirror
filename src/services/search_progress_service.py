import time
import sqlite3
import logging
from datetime import datetime
from core.database_config import db_config

logger = logging.getLogger(__name__)

class SearchProgressService:
    DEFAULT_ESTIMATED_DURATION = 25  # seconds
    TIMING_TABLE = "search_timings"

    def __init__(self, database_service=None):
        # Use the central config for the system management database
        self.db_path = db_config.system_db_path
        logger.info(f"📊 Progress DB path initialized: {self.db_path}")
        self._ensure_table_exists()

    def start_search(self, search_date):
        self.search_start_time = time.time()
        self.search_date = search_date
        logger.info(f"🚀 Search started at {self.search_start_time:.2f} for {search_date}")

    def complete_search(self, result_count):
        if not hasattr(self, 'search_start_time'):
            logger.warning("⚠️ No start time recorded — cannot complete search timing.")
            return

        duration = time.time() - self.search_start_time
        logger.info(f"✅ Search complete — duration: {duration:.2f}s, results: {result_count}")
        self._save_timing_to_database(self.search_date, duration)

    def get_estimated_duration(self):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute(f"""
                SELECT duration FROM {self.TIMING_TABLE}
                ORDER BY timestamp DESC LIMIT 10
            """)
            rows = cursor.fetchall()
            conn.close()

            durations = [r[0] for r in rows if r[0] > 0]
            if durations:
                avg = sum(durations) / len(durations)
                logger.info(f"📈 Avg estimated duration from history: {avg:.2f}s")
                return avg
            else:
                logger.info("📉 No historical data found — using default estimate.")
        except Exception as e:
            logger.warning(f"⚠️ Failed to read average duration: {e}")

        return self.DEFAULT_ESTIMATED_DURATION

    def _save_timing_to_database(self, search_date, duration):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(f"""
                INSERT INTO {self.TIMING_TABLE} (search_date, duration, timestamp)
                VALUES (?, ?, ?)
            """, (search_date, duration, datetime.now()))
            conn.commit()
            conn.close()
            logger.info(f"💾 Search duration ({duration:.2f}s) saved to DB.")
        except Exception as e:
            logger.warning(f"⚠️ Failed to save duration to database: {e}")

    def _ensure_table_exists(self):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS {self.TIMING_TABLE} (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    search_date TEXT NOT NULL,
                    duration REAL NOT NULL,
                    timestamp TIMESTAMP NOT NULL
                )
            """)
            conn.commit()
            conn.close()
            logger.info(f"📁 Ensured table '{self.TIMING_TABLE}' exists in DB.")
        except Exception as e:
            logger.warning(f"⚠️ Failed to ensure timing table exists: {e}")

    def estimate_search_duration(self):
        return self.get_estimated_duration()
