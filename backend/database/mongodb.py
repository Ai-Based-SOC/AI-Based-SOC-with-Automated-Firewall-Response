from backend.core.config import settings
from pymongo import MongoClient

_client = None
_db = None


def connect_mongo():
    global _client, _db
    _client = MongoClient(
        settings.mongodb_uri,
        serverSelectionTimeoutMS=2000,
    )
    try:
        _client.admin.command("ping")
    except Exception:
        _client.close()
        _client = None
        _db = None
        raise
    _db = _client[settings.mongodb_db]
    return _db


def close_mongo():
    global _client, _db
    if _client is not None:
        _client.close()
    _client = None
    _db = None


def db():
    if _db is None:
        raise RuntimeError("MongoDB is not connected. Call connect_mongo() first.")
    return _db