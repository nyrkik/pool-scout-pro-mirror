#!/usr/bin/env python3
"""
DownloadLockService - Pool Scout Pro
Single-flight guard with BOTH:
- process-local mutex (blocks re-entrancy inside same Gunicorn worker)
- cross-process file lock via flock (blocks other workers/processes)

Never throws; returns structured {acquired: bool, info}.
"""

import fcntl
import json
import os
import time
import threading
from typing import Tuple, Dict, Optional

# Process-local guard (per interpreter / worker)
_PROCESS_LOCK = threading.Lock()
_PROCESS_HELD = False
_PROCESS_HOLDER = {"job_id": None, "pid": None, "ts": None}

class DownloadLockService:
    def __init__(self, lock_file: str = "/tmp/pool_scout_pro.download.lock", ttl_seconds: int = 1800):
        self.lock_file = lock_file
        self.ttl_seconds = ttl_seconds
        self._fd: Optional[int] = None
        self._owns_file_lock = False

    def acquire(self, job_id: str) -> Tuple[bool, Dict]:
        """
        Acquire both the process-local and file lock. If either is held, deny.
        """
        global _PROCESS_HELD, _PROCESS_HOLDER

        # 1) Process-local guard
        if _PROCESS_HELD:
            age = int(time.time() - (_PROCESS_HOLDER.get("ts") or time.time()))
            msg = f"Local download already in progress (job {_PROCESS_HOLDER.get('job_id','?')}, pid {_PROCESS_HOLDER.get('pid','?')}, age {age}s)."
            return False, {"message": msg, "holder": dict(_PROCESS_HOLDER)}

        with _PROCESS_LOCK:
            if _PROCESS_HELD:
                age = int(time.time() - (_PROCESS_HOLDER.get("ts") or time.time()))
                msg = f"Local download already in progress (job {_PROCESS_HOLDER.get('job_id','?')}, pid {_PROCESS_HOLDER.get('pid','?')}, age {age}s)."
                return False, {"message": msg, "holder": dict(_PROCESS_HOLDER)}

            # set local ownership BEFORE file lock to block re-entrancy
            _PROCESS_HELD = True
            _PROCESS_HOLDER = {"job_id": job_id, "pid": os.getpid(), "ts": int(time.time())}

        # 2) Cross-process file lock
        try:
            os.makedirs(os.path.dirname(self.lock_file), exist_ok=True)
        except Exception:
            pass

        try:
            fd = os.open(self.lock_file, os.O_CREAT | os.O_RDWR, 0o644)
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                holder = self._read_holder(fd)
                msg = "Download already in progress by another worker."
                if holder:
                    age = int(time.time() - holder.get("ts", 0))
                    msg = f"Download already in progress (job {holder.get('job_id','unknown')}, pid {holder.get('pid','?')}, age {age}s)."
                # release process-local ownership since we didn't get file lock
                self._release_process_local()
                os.close(fd)
                return False, {"message": msg, "holder": holder or {}}

            # we hold the file lock
            self._fd = fd
            self._owns_file_lock = True
            holder_data = {"job_id": job_id, "pid": os.getpid(), "ts": int(time.time())}
            os.ftruncate(self._fd, 0)
            os.lseek(self._fd, 0, os.SEEK_SET)
            os.write(self._fd, json.dumps(holder_data).encode("utf-8"))
            os.fsync(self._fd)
            return True, {"message": "Lock acquired", "holder": holder_data}

        except Exception as e:
            # release process-local guard on error
            self._release_process_local()
            return False, {"message": f"Failed to acquire lock: {e}"}

    def release(self) -> None:
        try:
            # release file lock first
            if self._fd is not None and self._owns_file_lock:
                try:
                    fcntl.flock(self._fd, fcntl.LOCK_UN)
                finally:
                    os.close(self._fd)
                self._fd = None
                self._owns_file_lock = False
                try:
                    os.remove(self.lock_file)
                except Exception:
                    pass
        finally:
            # always release local guard
            self._release_process_local()

    def _release_process_local(self):
        global _PROCESS_HELD, _PROCESS_HOLDER
        with _PROCESS_LOCK:
            _PROCESS_HELD = False
            _PROCESS_HOLDER = {"job_id": None, "pid": None, "ts": None}

    def _read_holder(self, fd: int):
        try:
            os.lseek(fd, 0, os.SEEK_SET)
            raw = os.read(fd, 4096)
            if not raw:
                return None
            return json.loads(raw.decode("utf-8"))
        except Exception:
            return None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.release()
