from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Protocol

import aiosqlite

class StorageError(Exception):
    pass

class Storage(ABC):
    """Port adapter for basic storage commands."""

    @abstractmethod
    async def get(self, key: str) -> Any: ...

    @abstractmethod
    async def set(self, key: str, value: Any) -> None: ...

    @abstractmethod
    async def delete(self, key: str) -> None: ...

class SQLiteStorage(Storage):
    """SQLite-based storage adapter."""

    def __init__(self, db_path: str):
        self._db_path = db_path

    async def _ensure_table(self):
        async with aiosqlite.connect(self._db_path) as db:
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS kv (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
                """
            )
            await db.commit()

    async def get(self, key: str) -> Any:
        await self._ensure_table()
        async with aiosqlite.connect(self._db_path) as db:
            async with db.execute("SELECT value FROM kv WHERE key = ?", (key,)) as cursor:
                row = await cursor.fetchone()
                if row is None:
                    return None
                return row[0]  # Raw string; caller expected to deserialize

    async def set(self, key: str, value: Any) -> None:
        await self._ensure_table()
        # Store as string; caller handles serialization
        async with aiosqlite.connect(self._db_path) as db:
            await db.execute(
                "INSERT OR REPLACE INTO kv (key, value) VALUES (?, ?)", (key, str(value))
            )
            await db.commit()

    async def delete(self, key: str) -> None:
        await self._ensure_table()
        async with aiosqlite.connect(self._db_path) as db:
            await db.execute("DELETE FROM kv WHERE key = ?", (key,))
            await db.commit()