from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from typing import Optional
import os

# Global client
_client: Optional[AsyncIOMotorClient] = None


def get_mongo_client() -> AsyncIOMotorClient:
    global _client
    if _client is None:
        mongodb_url = os.getenv("MONGODB_URL", "mongodb://root:root_password@localhost:27017")
        _client = AsyncIOMotorClient(mongodb_url)
    return _client


async def get_database() -> AsyncIOMotorDatabase:
    client = get_mongo_client()
    db_name = os.getenv("MONGODB_DB_NAME", "oms_db")
    return client[db_name]


async def close_mongo_connection():
    global _client
    if _client is not None:
        _client.close()
        _client = None
