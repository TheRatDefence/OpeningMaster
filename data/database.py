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
    """
    Manages a database with two tables:
        1. Openings - Columns: id, name, pgn - This table stores the openings and their sequence of moves
        2. User Progress - id, review count, score, next review, etc - Changes after each session and stores user practice data for each opening

    Key Design idea: Keep the opening moves and user progress data separate.

    The database is also stored in memory during runtime inorder to keep the data encrypted:
    	Startup:  disk (encrypted blob) → decrypt → load into RAM
        Running:  all queries hit the in-memory database
        Shutdown: RAM → encrypt → write to disk

    Encryption:
        AES-256 is symmetrical - Only one key is needed:"chess-opening-trainer-secret-key"
        However, AES-256 needs a 32 byte, randomish key - Hash the key to output a fixed 32 byte key
        Slow hashing algorithm has to be used - PBKDF2HMAC runs the hash thousands of times in a loop
        A nonce is also generated, appended to the front of the cipher text and passed too AES-256 to prevent pattern matching attacks.

    """

    # ----------| Encryption |---------- #

    @staticmethod
    def _load_environmental_variables() -> tuple[bytes,bytes]:
        """
        Loads APP_SECRET and SALT from the .env file.
        :return: tuple containing secret, salt as bytes
        """

        if not dotenv.find_dotenv(".env"):  # If dotenv.dotenv_values returns an empty string
            raise Exception(".env does not exist")

        env_values = dotenv.dotenv_values()

        secret = env_values["APP_SECRET"]
        salt = env_values["SALT"]

        if not secret or not salt:
            raise ValueError("APP_SECRET or SALT are not defined in .env")

        return secret.encode(), salt.encode()

    def _derive_key(self) -> bytes:
        """
        Key generation process:
        _APP_SECRET + _SALT -> PBKDF2HMAC -> 32-byte AES key
        :return: 32 byte key
        """

        key = PBKDF2HMAC(algorithm=hashes.SHA256(),
                         length=32,
                         salt=self._salt,
                         iterations=100000).derive(self._secret)
        return key

    # ----------| Constructor |---------- #

    def __init__(self):
        """
        Looks for the database file:
        - If the file exists: decrypts -> loads it into memory
        - If the file doesn't exist: create tables -> seed defaults -> save to disk
        """

        # -----| Encryption |----- #
        self._secret, self._salt = self._load_environmental_variables()
        self._key = self._derive_key()

        # -----|  Database  |----- #
        os.makedirs(config.DATA_DIR, exist_ok=True) # Create the data directory if it doesn't exist

        self._db = sq.connect(":memory:")           # Opens an empty database in memory
        self._db.row_factory = sq.Row

        if not os.path.exists(config.DB_PATH):      # Create a database file with defaults if one doesn't exist
            self._create_tables()
            self._seed_defaults()
            self.save()

        self.load()

    # ----------| Private Methods |---------- #

    def _encrypt(self, data: bytes) -> bytes:
        """
        1. Generate a fresh random nonce
        2. Encrypt the data using the key and nonce
        3. Return nonce + ciphertext

        :return: nonce + ciphertext as bytes
        """
        nonce = os.urandom(12)
        encrypted = AESGCM(key=self._key).encrypt(nonce=nonce, data=data, associated_data=None)
        return nonce + encrypted

    def _decrypt(self, encrypted: bytes) -> bytes:
        """
        1. Split nonce from ciphertext
        2. Decrypt the data using the key and nonce
        3. Return decrypted data

        :param encrypted: the encrypted data in bytes
        :return: The decrypted data in bytes
        """
        nonce, cipher = encrypted[:12], encrypted[12:]
        data = AESGCM(key=self._key).decrypt(nonce=nonce, data=cipher, associated_data=None)
        return data

    def _create_tables(self) -> None:
        """
        Creates openings and user_progress tables:

        openings:
            | id | name | pgn |

        user_progress:
            | opening_id | review_count | memory_points | next_review_date | status |
        """
        db = self._db

        db.execute("CREATE TABLE IF NOT EXISTS openings "
                   "( id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, pgn TEXT )")

        db.execute("CREATE TABLE IF NOT EXISTS user_progress "
                   "(opening_id INTEGER PRIMARY KEY, review_count INTEGER, memory_points REAL, next_review_date TEXT, status TEXT)")

        db.commit()

        return None

    def _seed_defaults(self) -> None:
        """
        Inserts the default openings into the openings table
        """
        db = self._db

        db.executemany("INSERT INTO openings (name, pgn) VALUES (?, ?)", _DEFAULT_OPENINGS)

        db.commit()
        return None

    # ----------| Persistence |---------- #

    def load(self):
        """
        Opens the database file then decrypts and deserializes it into memory
        """
        db = self._db

        with open(config.DB_PATH, "rb") as file:
            raw = self._decrypt(file.read())

        db.deserialize(raw)
        db.commit()

        return None

    def save(self) -> None:
        """
        Encrypts the database in memory and saves to the database file
        """
        db = self._db

        raw = db.serialize()
        encrypted = self._encrypt(raw)

        with open(config.DB_PATH, "wb") as file: # Creates a new database file if none exists at DB_PATH
            file.write(encrypted)

        return None

    # ----------| Public Methods |---------- #

    def get_all_openings(self) -> list[dict]:
        """
        Queries every row of the openings table and returns them as a list of dicts.
        :return: [{"id": 1, "name": "Italian Game", "pgn": "1. e4 ..."}, ...]
        """
        db = self._db

        rows = db.execute("SELECT * FROM openings").fetchall()
        openings = [dict(row) for row in rows]
        return openings

    def get_opening_by_id(self, opening_id: int) -> dict | None:
        """
        Queries a single row from openings where id matches, returns it as a dict or None if not found.
        :param opening_id: The id of the opening
        :return: {"id": 1, "name": "Italian Game", "pgn": "1. e4 ..."} | None
        """
        db = self._db

        row = db.execute("SELECT * FROM openings WHERE id = ?", (opening_id,)).fetchone()
        return dict(row) if row else None

    def get_progress(self, opening_id: int) -> dict | None:
        """
        Queries the user_progress row for a given opening, returns it as a dict or None if no progress is recorded.
        :param opening_id: The id of the opening
        :return: {"opening_id": 1, "review_count": 3, "memory_points": 2.5, "next_review_date": "2026-06-25", "status": "in-progress"} | None
        """
        db = self._db

        row = db.execute("SELECT * FROM user_progress WHERE opening_id = ?", (opening_id,)).fetchone()
        return dict(row) if row else None

    def upsert_progress(self, opening_id: int, **kwargs) -> None:
        """
        Inserts or updates the user_progress row for a given opening.
        :param opening_id: The id of the opening
        :param kwargs: Fields to be updated: e.g. status="mastered"
        """
        db = self._db

        existing = self.get_progress(opening_id) or {}

        defaults = {"review_count": 0,
                    "memory_points": 0,
                    "next_review_date": None,
                    "status": "new"}

        merged = {**defaults, **existing, **kwargs} # Creates a dict with merged values prioritising kwargs, then existing, then defaults

        db.execute("INSERT OR REPLACE INTO user_progress "
                   "(opening_id, review_count, memory_points, next_review_date, status) VALUES (?, ?, ?, ?, ?)",
                   (opening_id,
                              merged["review_count"],
                              merged["memory_points"],
                              merged["next_review_date"],
                              merged["status"],))

        db.commit()
        return None