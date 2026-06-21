import os
import sqlite3
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

    @staticmethod
    def load_environmental_variables() -> tuple[bytes,bytes]:
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

    def __init__(self):
        """
        Looks for the database file:
        - If the file exists: decrypts -> loads it into memory
        - If the file doesn't exist: create tables -> seed defaults -> save to disk
        """

        self._secret, self._salt = self.load_environmental_variables()

        self._key = self._derive_key()

        # TODO(): Implement rest of init
        pass


