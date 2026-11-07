"""SQLite persistence for published-article interactions."""

from contextlib import closing
from datetime import datetime, timezone
import hashlib
import hmac
from pathlib import Path
import secrets
import sqlite3
from time import time


PAGE_SIZE = 30


class InteractionStore:
    def __init__(self, path: Path):
        self.path = path
        with self.connect() as db, db:
            db.execute("PRAGMA journal_mode = WAL")
            db.executescript("""
                CREATE TABLE IF NOT EXISTS views (
                    article_path TEXT PRIMARY KEY,
                    total INTEGER NOT NULL
                );
                CREATE TABLE IF NOT EXISTS view_sessions (
                    article_path TEXT NOT NULL,
                    session_hash TEXT NOT NULL,
                    PRIMARY KEY (article_path, session_hash)
                );
                CREATE TABLE IF NOT EXISTS comments (
                    id INTEGER PRIMARY KEY,
                    article_path TEXT NOT NULL,
                    submission_id TEXT NOT NULL,
                    body TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    status TEXT NOT NULL CHECK (status IN ('pending', 'published', 'rejected')),
                    UNIQUE (article_path, submission_id)
                );
                CREATE INDEX IF NOT EXISTS comments_by_article
                    ON comments (article_path, status, id);
                CREATE INDEX IF NOT EXISTS comments_by_status ON comments (status, id);
                CREATE TABLE IF NOT EXISTS rate_limits (
                    action TEXT NOT NULL,
                    client_hash TEXT NOT NULL,
                    expires INTEGER NOT NULL,
                    hits INTEGER NOT NULL,
                    PRIMARY KEY (action, client_hash, expires)
                );
                CREATE INDEX IF NOT EXISTS rate_limits_expiry ON rate_limits (expires);
                CREATE TABLE IF NOT EXISTS service_metadata (
                    name TEXT PRIMARY KEY,
                    value BLOB NOT NULL
                );
            """)
            db.execute("INSERT OR IGNORE INTO service_metadata VALUES ('rate_key', ?)", (secrets.token_bytes(32),))
            self.rate_key = db.execute("SELECT value FROM service_metadata WHERE name = 'rate_key'").fetchone()[0]

    def connect(self):
        db = sqlite3.connect(self.path, timeout=5)
        db.row_factory = sqlite3.Row
        return closing(db)

    def allow(self, action, client, limit, seconds):
        client_hash = hmac.digest(self.rate_key, client.encode(), "sha256").hex()
        now = int(time())
        expires = now - now % seconds + seconds
        with self.connect() as db, db:
            db.execute("DELETE FROM rate_limits WHERE expires <= ?", (now,))
            cursor = db.execute("""
                INSERT INTO rate_limits VALUES (?, ?, ?, 1)
                ON CONFLICT(action, client_hash, expires) DO UPDATE SET hits = hits + 1 WHERE hits < ?
            """, (action, client_hash, expires, limit))
            return cursor.rowcount == 1

    def count(self, article_path):
        with self.connect() as db:
            row = db.execute("SELECT total FROM views WHERE article_path = ?", (article_path,)).fetchone()
            return row["total"] if row else 0

    def record_view(self, article_path, session_id):
        session_hash = hashlib.sha256(session_id.bytes).hexdigest()
        with self.connect() as db, db:
            inserted = db.execute("INSERT OR IGNORE INTO view_sessions VALUES (?, ?)", (article_path, session_hash))
            if inserted.rowcount:
                db.execute("""
                    INSERT INTO views VALUES (?, 1)
                    ON CONFLICT(article_path) DO UPDATE SET total = total + 1
                """, (article_path,))
            return db.execute("SELECT total FROM views WHERE article_path = ?", (article_path,)).fetchone()["total"]

    def submit(self, article_path, submission_id, body):
        created_at = datetime.now(timezone.utc).isoformat()
        with self.connect() as db, db:
            cursor = db.execute("""
                INSERT INTO comments (article_path, submission_id, body, created_at, status)
                VALUES (?, ?, ?, ?, 'pending') ON CONFLICT(article_path, submission_id) DO NOTHING
            """, (article_path, str(submission_id), body, created_at))
            if cursor.rowcount:
                return True
            existing = db.execute("SELECT body FROM comments WHERE article_path = ? AND submission_id = ?",
                                  (article_path, str(submission_id))).fetchone()
            return existing["body"] == body

    def comments(self, status, before, *, article_path=None):
        columns = "id, body, created_at"
        clauses = ["status = ?"]
        args = [status]
        if article_path is None:
            columns += ", article_path, status"
        else:
            clauses.append("article_path = ?")
            args.append(article_path)
        if before is not None:
            clauses.append("id < ?")
            args.append(before)
        with self.connect() as db:
            rows = db.execute(
                f"SELECT {columns} FROM comments WHERE {' AND '.join(clauses)} ORDER BY id DESC LIMIT ?",
                (*args, PAGE_SIZE + 1),
            ).fetchall()
        return {
            "comments": [dict(row) for row in rows[:PAGE_SIZE]],
            "next_before": rows[PAGE_SIZE - 1]["id"] if len(rows) > PAGE_SIZE else None,
        }

    def moderate(self, comment_id, status):
        with self.connect() as db, db:
            cursor = db.execute("UPDATE comments SET status = ? WHERE id = ?", (status, comment_id))
            if cursor.rowcount:
                return dict(db.execute("""
                    SELECT id, body, created_at, article_path, status FROM comments WHERE id = ?
                """, (comment_id,)).fetchone())
        return None
