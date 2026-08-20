import asyncio
import json
import sqlite3
import time
from dataclasses import asdict, dataclass
from abc import ABC, abstractmethod
from typing import Tuple, Optional
from states.session import SessionState
from monads import Result, Err, Ok, catching


@dataclass(frozen=True)
class StorageError:
    message: str


class Storage(ABC):
    """Port adapter for basic storage commands."""

    @staticmethod
    @abstractmethod
    def open_db(path: str) -> Result[sqlite3.Connection, StorageError]:
        pass

    @staticmethod
    @abstractmethod
    async def append(db: sqlite3.Connection, kind: str, payload: dict) -> Result[None, StorageError]:
        pass

    @staticmethod
    @abstractmethod
    async def maybe_snapshot(db: sqlite3.Connection, state: SessionState, snapshot_every: int) -> Result[bool, StorageError]:
        pass

    @staticmethod
    @abstractmethod
    async def restore(db: sqlite3.Connection) -> Result[Tuple[Optional[SessionState], int], StorageError]:
        pass


class SQLiteStorage(Storage):
    """SQLite-based storage adapter with Result monad."""

    @staticmethod
    def open_db(path: str) -> Result[sqlite3.Connection, StorageError]:
        SCHEMA = """
            CREATE TABLE IF NOT EXISTS wal (
                id       INTEGER PRIMARY KEY AUTOINCREMENT,
                ts       REAL NOT NULL,
                kind     TEXT NOT NULL,
                payload  TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS snapshot (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                ts         REAL NOT NULL,
                wal_cursor INTEGER NOT NULL,
                state      TEXT NOT NULL
            );
        """

        def _connect() -> sqlite3.Connection:
            conn = sqlite3.connect(path, check_same_thread=False)
            conn.execute("PRAGMA journal_mode=WAL;")
            conn.executescript(SCHEMA)
            conn.commit()
            return conn

        return catching(
            _connect,
            lambda e: StorageError(f"Failed to open database: {e}")
        )

    @staticmethod
    async def append(db: sqlite3.Connection, kind: str, payload: dict) -> Result[None, StorageError]:
        """Insert a new WAL entry."""

        def _insert() -> None:
            db.execute(
                "INSERT INTO wal (ts, kind, payload) VALUES (?, ?, ?)",
                (time.time(), kind, json.dumps(payload))
            )
            db.commit()

        # catching db errors here.
        return await asyncio.to_thread(
            lambda: catching(_insert, lambda e: StorageError(f"Append failed: {e}"))
        )

    @staticmethod
    async def maybe_snapshot(
        db: sqlite3.Connection,
        state: SessionState,
        snapshot_every: int
    ) -> Result[bool, StorageError]:
        """
        Check if we have >= snapshot_every new committed rows since last snapshot.
        If yes, write a new snapshot.
        """

        # Set Theory Formalization
        #
        # Let S be the set of all possible full program states (SessionState)
        # Let W be the set of all write-ahead log (WAL) entries
        # Let Snapshots subset S x N be the set of all snapshots, each paired with a WAL cursor (integer)
        # Let wal: N -> W be a function mapping an integer id to a WAL entry
        # Let snapshot: N -> Snapshots be a function mapping an integer id to a Snapshot (state, wal_cursor)
        # For a given database state db:
        #   - The current WAL cursor c = max({ s.wal_cursor | (s, s.wal_cursor) in Snapshots })
        #   - The number of unsnapshotted WAL entries is |{ w in W | w.id > c and w.kind = "committed" }|
        #   - When |unsnapshotted-wal-entries| >= snapshot_every, we create a new snapshot:
        #       snapshot_new = (state, max WAL id so far)

        def _check_and_write() -> bool:
            # Count rows after the latest snapshot's wal_cursor (or 0 if none)
            row = db.execute(
                """
                SELECT COUNT(*) FROM wal
                WHERE id > COALESCE((SELECT MAX(wal_cursor) FROM snapshot), 0)
                  AND kind = 'committed'
                """
            ).fetchone()
            since = row[0] if row else 0

            if since < snapshot_every:
                return False

            # Get current max WAL id
            cursor_row = db.execute("SELECT MAX(id) FROM wal").fetchone()
            cursor = cursor_row[0] if cursor_row and cursor_row[0] is not None else 0

            # Insert snapshot
            db.execute(
                "INSERT INTO snapshot (ts, wal_cursor, state) VALUES (?, ?, ?)",
                (time.time(), cursor, json.dumps(asdict(state)))
            )
            db.commit()
            return True

        # Adapting db errors by mapping happy path to Ok and uncaught or
        # yet to be defined port side/ adapter errors to be wrapped as StorageError generic for now
        return await asyncio.to_thread(
            lambda: catching(_check_and_write, lambda e: StorageError(f"Snapshot failed: {e}"))
        )

    @staticmethod
    async def restore(db: sqlite3.Connection) -> Result[Tuple[Optional[SessionState], int], StorageError]:
        """
        Load the latest snapshot and its wal_cursor.
        Returns (SessionState | None, last_cursor).
        """

        def _fetch() -> Result[Tuple[Optional[SessionState], int], StorageError]:
            try:
                row = db.execute(
                    "SELECT wal_cursor, state FROM snapshot ORDER BY id DESC LIMIT 1"
                ).fetchone()
                if row is None:
                    return Ok((None, 0))
                cursor, state_json = row
                state_dict = json.loads(state_json)
                # If SessionState has a custom constructor, adjust here.
                state = SessionState(**state_dict)  # adapt to your actual class
                return Ok((state, cursor))
            except Exception as e:
                return Err(StorageError(f"Restore failed: {e}"))

        return await asyncio.to_thread(_fetch)
 