# database.py
import os
import logging
from typing import Optional

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class MongoDB:
    """
    MongoDB helper with a singleton AsyncIOMotorClient stored on the class.
    Usage:
        mongodb = MongoDB()                     # uses env vars
        db = mongodb.get_database()             # returns AsyncIOMotorDatabase
        coll = mongodb.get_collection("items")
        mongodb.close()                         # close the client
    """
    # shared Motor client across the process
    _client: Optional[AsyncIOMotorClient] = None

    def __init__(self, uri: Optional[str] = None, db_name: Optional[str] = None):
        # initialize only once for the wrapper instance
        if getattr(self, "_initialized", False):
            return
        self._initialized = True

        self._uri = uri or os.getenv(
            "MONGODB_URL", "mongodb://root:root_password@localhost:27017"
        )
        # do not append slash or database here — we access db via client[db_name]
        self.set_database(db_name if db_name is not None else 'oms_db')

    def _ensure_client(self) -> AsyncIOMotorClient:
        """Create the AsyncIOMotorClient once and reuse it."""
        if MongoDB._client is None:
            logger.info("Creating AsyncIOMotorClient for URI: %s", self._uri)
            MongoDB._client = AsyncIOMotorClient(self._uri)
        return MongoDB._client

    @property
    def client(self) -> AsyncIOMotorClient:
        """Return the shared AsyncIOMotorClient (creates it lazily)."""
        return self._ensure_client()
    
    def set_database(self, db_name: str) -> None:
        """Set the database name for future operations."""
        self._db_name = db_name

    def get_database(self, db_name: Optional[str] = None) -> AsyncIOMotorDatabase:
        """
        Return an AsyncIOMotorDatabase instance. This is a lightweight object (no network action).
        """
        db_name = db_name or self._db_name
        if db_name is None:
            raise RuntimeError("Database name is not set. Call set_database() first.")
        return self.client[db_name]

    def get_collection(self, collection_name: str, db_name: Optional[str] = None):
        """Convenience to get a collection from the configured (or provided) database."""
        return self.get_database(db_name)[collection_name]

    def close(self) -> None:
        """
        Close the shared Motor client and clear the singleton.
        Note: AsyncIOMotorClient.close() is a synchronous call that closes sockets.
        """
        if MongoDB._client is not None:
            logger.info("Closing AsyncIOMotorClient")
            MongoDB._client.close()
            MongoDB._client = None
