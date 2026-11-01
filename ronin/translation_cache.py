"""Persistent exact-match translation cache.

Only byte-identical source and translator fingerprints hit this cache. There is
intentionally no embedding/semantic fallback: a similar COBOL program is not
guaranteed to have equivalent semantics, so approximate retrieval must never
silently supply executable output.
"""
from __future__ import annotations

import hashlib
import sqlite3
import threading
from pathlib import Path


class TranslationCache:
    """SQLite cache safe for repeated runs and per-thread connections.

    Include a translator/build fingerprint in every lookup so changes to
    translation logic invalidate stale results. The default database is local;
    callers choose a writable persistent path explicitly.
    """

    def __init__(self, db_path: str | Path = "translation_cache.sqlite3", *, timeout: float = 10.0):
        self.db_path = str(db_path)
        self.timeout = max(0.1, float(timeout))
        self._local = threading.local()
        self._init_lock = threading.Lock()
        self._initialize()

    @staticmethod
    def compute_key(source_code: str, translator_fingerprint: str) -> str:
        payload = (
            "cobol2py-cache-v1\0"
            + translator_fingerprint
            + "\0"
            + source_code
        ).encode("utf-8")
        return hashlib.sha256(payload).hexdigest()

    def _get_conn(self) -> sqlite3.Connection:
        conn = getattr(self._local, "conn", None)
        if conn is None:
            conn = sqlite3.connect(self.db_path, timeout=self.timeout)
            conn.execute("PRAGMA busy_timeout = %d" % int(self.timeout * 1000))
            self._local.conn = conn
        return conn

    def _initialize(self) -> None:
        # Schema creation can be reached concurrently by multiple instances.
        with self._init_lock:
            conn = self._get_conn()
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS translation_cache (
                    cache_key TEXT PRIMARY KEY,
                    source_code TEXT NOT NULL,
                    translator_fingerprint TEXT NOT NULL,
                    python_code TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            conn.commit()

    def get(self, source_code: str, translator_fingerprint: str) -> str | None:
        key = self.compute_key(source_code, translator_fingerprint)
        row = self._get_conn().execute(
            """SELECT python_code, source_code, translator_fingerprint
               FROM translation_cache WHERE cache_key = ?""",
            (key,),
        ).fetchone()
        if row is None:
            return None
        # Defense in depth: never trust the digest alone.
        if row[1] != source_code or row[2] != translator_fingerprint:
            return None
        return str(row[0])

    def put(self, source_code: str, python_code: str, translator_fingerprint: str) -> None:
        key = self.compute_key(source_code, translator_fingerprint)
        conn = self._get_conn()
        conn.execute(
            """INSERT INTO translation_cache
               (cache_key, source_code, translator_fingerprint, python_code)
               VALUES (?, ?, ?, ?)
               ON CONFLICT(cache_key) DO UPDATE SET
                 source_code=excluded.source_code,
                 translator_fingerprint=excluded.translator_fingerprint,
                 python_code=excluded.python_code,
                 created_at=CURRENT_TIMESTAMP""",
            (key, source_code, translator_fingerprint, python_code),
        )
        conn.commit()

    def close(self) -> None:
        """Close this thread's connection; safe to call more than once."""
        conn = getattr(self._local, "conn", None)
        if conn is not None:
            conn.close()
            del self._local.conn

    def __enter__(self) -> "TranslationCache":
        return self

    def __exit__(self, exc_type, exc, traceback) -> None:
        self.close()
