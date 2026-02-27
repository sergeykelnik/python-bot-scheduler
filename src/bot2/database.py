"""
Async SQLite database service.
"""

import json
import logging
import os
from typing import Any, Dict, List, Optional

import aiosqlite

from src.bot2.config import DB_PATH

logger = logging.getLogger(__name__)


class Database:
    """Async SQLite database for schedules and user preferences."""

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def init(self) -> None:
        """Create tables and run migrations."""
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)

        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS schedules (
                    job_id TEXT PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    chat_id TEXT NOT NULL,
                    message TEXT NOT NULL,
                    schedule_data TEXT NOT NULL,
                    is_paused INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    language TEXT DEFAULT 'ru',
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    recent_chat_ids TEXT DEFAULT '[]'
                )
                """
            )
            await db.commit()

        await self._migrate()
        logger.info("Database initialized")

    async def _migrate(self) -> None:
        """Add missing columns to existing tables."""
        expected: Dict[str, Dict[str, str]] = {
            "schedules": {
                "job_id": "TEXT PRIMARY KEY",
                "user_id": "INTEGER NOT NULL",
                "chat_id": "TEXT NOT NULL",
                "message": "TEXT NOT NULL",
                "schedule_data": "TEXT NOT NULL",
                "is_paused": "INTEGER DEFAULT 0",
                "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
            },
            "users": {
                "user_id": "INTEGER PRIMARY KEY",
                "language": "TEXT DEFAULT 'ru'",
                "updated_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
                "recent_chat_ids": "TEXT DEFAULT '[]'",
            },
        }
        try:
            async with aiosqlite.connect(self.db_path) as db:
                for table, columns in expected.items():
                    cursor = await db.execute(f"PRAGMA table_info({table})")
                    existing = {row[1] for row in await cursor.fetchall()}
                    for col_name, col_def in columns.items():
                        if col_name not in existing:
                            if "PRIMARY KEY" in col_def:
                                continue
                            col_type = col_def.split("PRIMARY KEY")[0].strip()
                            await db.execute(
                                f"ALTER TABLE {table} ADD COLUMN {col_name} {col_type}"
                            )
                            logger.info("Added column %s to table %s", col_name, table)
                await db.commit()
        except Exception as e:
            logger.error("Schema migration error: %s", e)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    async def _execute(
        self,
        query: str,
        params: tuple = (),
        *,
        fetch_all: bool = False,
        fetch_one: bool = False,
    ) -> Any:
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(query, params)
            await db.commit()
            if fetch_all:
                return await cursor.fetchall()
            if fetch_one:
                return await cursor.fetchone()
            return None

    # ------------------------------------------------------------------
    # Schedules
    # ------------------------------------------------------------------

    async def save_schedule(
        self,
        job_id: str,
        user_id: int,
        chat_id: str,
        message: str,
        schedule_data: dict,
        is_paused: bool = False,
    ) -> None:
        await self._execute(
            """
            INSERT OR REPLACE INTO schedules
            (job_id, user_id, chat_id, message, schedule_data, is_paused)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (job_id, user_id, str(chat_id), message, json.dumps(schedule_data), int(is_paused)),
        )
        logger.info("Schedule saved: %s", job_id)

    async def delete_schedule(self, job_id: str) -> None:
        await self._execute("DELETE FROM schedules WHERE job_id = ?", (job_id,))
        logger.info("Schedule deleted: %s", job_id)

    async def update_schedule_pause_status(self, job_id: str, is_paused: bool) -> None:
        await self._execute(
            "UPDATE schedules SET is_paused = ? WHERE job_id = ?",
            (int(is_paused), job_id),
        )
        logger.info("Schedule %s pause → %s", job_id, is_paused)

    async def get_schedules(self, user_id: Optional[int] = None) -> List[Dict]:
        if user_id is not None:
            rows = await self._execute(
                "SELECT * FROM schedules WHERE user_id = ?",
                (user_id,),
                fetch_all=True,
            )
        else:
            rows = await self._execute("SELECT * FROM schedules", fetch_all=True)

        schedules: List[Dict] = []
        if rows:
            for row in rows:
                schedules.append(
                    {
                        "job_id": row[0],
                        "user_id": row[1],
                        "chat_id": row[2],
                        "message": row[3],
                        "schedule_data": json.loads(row[4]),
                        "is_paused": bool(row[5]),
                        "created_at": row[6],
                    }
                )
        return schedules

    # ------------------------------------------------------------------
    # User preferences
    # ------------------------------------------------------------------

    async def get_user_language(self, user_id: int, default: str = "ru") -> str:
        row = await self._execute(
            "SELECT language FROM users WHERE user_id = ?",
            (user_id,),
            fetch_one=True,
        )
        return row[0] if row and row[0] else default

    async def set_user_language(self, user_id: int, language: str) -> None:
        try:
            await self._execute(
                "INSERT INTO users (user_id, language, updated_at) VALUES (?, ?, CURRENT_TIMESTAMP)",
                (user_id, language),
            )
        except Exception:
            await self._execute(
                "UPDATE users SET language = ?, updated_at = CURRENT_TIMESTAMP WHERE user_id = ?",
                (language, user_id),
            )

    async def add_recent_chat_id(
        self, user_id: int, chat_id: int, max_items: int = 5
    ) -> None:
        try:
            row = await self._execute(
                "SELECT recent_chat_ids FROM users WHERE user_id = ?",
                (user_id,),
                fetch_one=True,
            )
            recent: list = json.loads(row[0]) if row and row[0] else []
            if chat_id in recent:
                recent.remove(chat_id)
            recent.insert(0, chat_id)
            recent = recent[:max_items]

            try:
                await self._execute(
                    "INSERT INTO users (user_id, recent_chat_ids) VALUES (?, ?)",
                    (user_id, json.dumps(recent)),
                )
            except Exception:
                await self._execute(
                    "UPDATE users SET recent_chat_ids = ? WHERE user_id = ?",
                    (json.dumps(recent), user_id),
                )
        except Exception as e:
            logger.error("Error adding recent chat_id: %s", e)

    async def get_recent_chat_ids(self, user_id: int) -> List[int]:
        try:
            row = await self._execute(
                "SELECT recent_chat_ids FROM users WHERE user_id = ?",
                (user_id,),
                fetch_one=True,
            )
            if row and row[0]:
                return json.loads(row[0])
        except Exception as e:
            logger.error("Error getting recent chat_ids: %s", e)
        return []

