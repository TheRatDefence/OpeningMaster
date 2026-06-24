import os
import sqlite3 as sq
import dotenv

import config

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes


# Default openings that are stored in the db in string (PGN notation) format
_DEFAULT_OPENINGS = [
    ("Italian Game",     "1. e4 e5 2. Nf3 Nc6 3. Bc4"),
    ("Sicilian Defence", "1. e4 c5 2. Nf3 d6 3. d4 cxd4 4. Nxd4 Nf6 5. Nc3"),
    ("London System",    "1. d4 d5 2. Bf4 Nf6 3. e3 e6 4. Nf3 Bd6 5. Bg3"),
    ("King's Indian",    "1. d4 Nf6 2. c4 g6 3. Nc3 Bg7 4. e4 d6 5. Nf3"),
    ("Queen's Gambit",   "1. d4 d5 2. c4 e6 3. Nc3 Nf6 4. Bg5 Be7 5. e3"),
]


class DatabaseManager:
    """Manages the encrypted SQLite database for openings and progress.
    Loads from / saves to an AES-256-GCM encrypted file at DB_PATH."""

    @staticmethod
    def _load_environmental_variables() -> tuple[bytes, bytes]:
        if not dotenv.find_dotenv(".env"):
            raise Exception(".env does not exist")

        env_values = dotenv.dotenv_values()
        secret = env_values["APP_SECRET"]
        salt = env_values["SALT"]

        if not secret or not salt:
            raise ValueError("APP_SECRET or SALT are not defined in .env")

        secret_bytes = secret.encode() if isinstance(secret, str) else secret
        salt_bytes = salt.encode() if isinstance(salt, str) else salt
        return secret_bytes, salt_bytes

    def _derive_key(self) -> bytes:
        """Derives a 32-byte AES key from the app secret and salt using PBKDF2HMAC."""
        key = PBKDF2HMAC(algorithm=hashes.SHA256(),
                         length=32,
                         salt=self._salt,
                         iterations=100000).derive(self._secret)
        return key

    def __init__(self):
        """Opens the database, creating and seeding a fresh one if no save file exists."""
        self._secret, self._salt = self._load_environmental_variables()
        self._key = self._derive_key()

        os.makedirs(config.DATA_DIR, exist_ok=True)
        self._db = sq.connect(":memory:")
        self._db.row_factory = sq.Row

        if not os.path.exists(config.DB_PATH):
            self._create_tables()
            self._seed_defaults()
            self.save()

        self.load()

    def _encrypt(self, data: bytes) -> bytes:
        """Encrypts the in-memory database to bytes using AES-256-GCM."""
        nonce = os.urandom(12)
        encrypted = AESGCM(key=self._key).encrypt(nonce=nonce, data=data, associated_data=None)
        return nonce + encrypted

    def _decrypt(self, encrypted: bytes) -> bytes:
        """Decrypts the given bytes and loads them into the in-memory database."""
        nonce, cipher = encrypted[:12], encrypted[12:]
        data = AESGCM(key=self._key).decrypt(nonce=nonce, data=cipher, associated_data=None)
        return data

    def _create_tables(self) -> None:
        """Creates the openings and progress tables if they don't already exist."""
        db = self._db

        db.execute("CREATE TABLE IF NOT EXISTS openings "
                   "( id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, pgn TEXT )")

        db.execute("CREATE TABLE IF NOT EXISTS user_progress "
                   "(opening_id INTEGER PRIMARY KEY, review_count INTEGER, memory_points REAL, next_review_date TEXT, status TEXT)")

        db.commit()

    def _seed_defaults(self) -> None:
        """Seeds the openings table with default openings."""
        db = self._db
        db.executemany("INSERT INTO openings (name, pgn) VALUES (?, ?)", _DEFAULT_OPENINGS)
        db.commit()

    def load(self):
        """Opens the database file, decrypts it, and loads it into memory."""
        db = self._db

        try:
            with open(config.DB_PATH, "rb") as file:
                raw = self._decrypt(file.read())
            db.deserialize(raw)
            db.commit()
        except Exception:
            self._create_tables()
            self._seed_defaults()
            self.save()

    def save(self) -> None:
        """Encrypts the in-memory database and saves it to disk."""
        db = self._db
        raw = db.serialize()
        encrypted = self._encrypt(raw)

        with open(config.DB_PATH, "wb") as file:
            file.write(encrypted)

    def get_all_openings(self) -> list[dict]:
        """Returns all openings from the database."""
        db = self._db
        rows = db.execute("SELECT * FROM openings").fetchall()
        openings = [dict(row) for row in rows]
        return openings

    def get_opening_by_id(self, opening_id: int) -> dict | None:
        """Returns the opening with the given id, or None if not found."""
        db = self._db
        row = db.execute("SELECT * FROM openings WHERE id = ?", (opening_id,)).fetchone()
        return dict(row) if row else None

    def get_progress(self, opening_id: int) -> dict | None:
        """Returns the user progress for the given opening, or None if no progress is recorded."""
        db = self._db
        row = db.execute("SELECT * FROM user_progress WHERE opening_id = ?", (opening_id,)).fetchone()
        return dict(row) if row else None

    def upsert_progress(self, opening_id: int, **kwargs) -> None:
        """Inserts or updates the user progress for the given opening."""
        db = self._db

        existing = self.get_progress(opening_id) or {}

        defaults = {"review_count": 0,
                    "memory_points": 0,
                    "next_review_date": None,
                    "status": "new"}

        merged = {**defaults, **existing, **kwargs}

        db.execute("INSERT OR REPLACE INTO user_progress "
                   "(opening_id, review_count, memory_points, next_review_date, status) VALUES (?, ?, ?, ?, ?)",
                   (opening_id,
                              merged["review_count"],
                              merged["memory_points"],
                              merged["next_review_date"],
                              merged["status"],))

        db.commit()
        return None