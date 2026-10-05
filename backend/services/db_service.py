from datetime import datetime, timezone
from typing import Any

from backend.database.mongodb import db
from bson import ObjectId
from bson.errors import InvalidId

# In-memory fallback (used only when Mongo is unavailable in CI/tests)
_FAKE_USERS: dict[str, dict[str, Any]] = {}


class DBService:
    @staticmethod
    def get_attack_collection():
        return db()["attacks"]

    @staticmethod
    def get_user_collection():
        return db()["users"]

    @staticmethod
    def get_firewall_collection():
        return db()["firewall_rules"]

    @staticmethod
    def get_incident_collection():
        return db()["incidents"]

    @staticmethod
    def _normalize_doc(doc: dict[str, Any] | None) -> dict[str, Any] | None:
        if not doc:
            return doc
        out = dict(doc)
        if "_id" in out:
            out["id"] = str(out["_id"])
            del out["_id"]
        for k, v in list(out.items()):
            if isinstance(v, datetime):
                out[k] = v.isoformat()
        return out

    @staticmethod
    def _normalize_many(docs: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return [d for d in (DBService._normalize_doc(x) for x in docs) if d is not None]

    @staticmethod
    def create_user(user_doc: dict[str, Any]) -> dict[str, Any]:
        now = datetime.now(timezone.utc)
        user_doc = dict(user_doc)
        user_doc.setdefault("created_at", now)
        user_doc.setdefault("updated_at", now)
        user_doc.setdefault("disabled", False)

        email = (user_doc.get("email") or "").lower()
        if email:
            user_doc["email"] = email

        try:
            col = DBService.get_user_collection()
            res = col.insert_one(user_doc)
            saved = col.find_one({"_id": res.inserted_id})
            normalized = DBService._normalize_doc(saved)
            return normalized or {}
        except RuntimeError:
            if "id" not in user_doc:
                user_doc["id"] = f"mem-{len(_FAKE_USERS)+1}"
            _FAKE_USERS[email] = dict(user_doc)
            normalized = DBService._normalize_doc(_FAKE_USERS[email])
            return normalized or {}

    @staticmethod
    def get_user_by_email(email: str) -> dict[str, Any] | None:
        email = (email or "").lower().strip()
        try:
            doc = DBService.get_user_collection().find_one({"email": email})
            return DBService._normalize_doc(doc)
        except RuntimeError:
            doc = _FAKE_USERS.get(email)
            return DBService._normalize_doc(doc)

    @staticmethod
    def get_user_by_id(user_id: str) -> dict[str, Any] | None:
        user_id = str(user_id).strip()
        if not user_id:
            return None

        try:
            col = DBService.get_user_collection()
            doc: dict[str, Any] | None = None
            try:
                doc = col.find_one({"_id": ObjectId(user_id)})
            except (InvalidId, TypeError, ValueError):
                doc = None

            if not doc:
                doc = col.find_one({"id": user_id})

            return DBService._normalize_doc(doc)
        except RuntimeError:
            for u in _FAKE_USERS.values():
                if str(u.get("id")) == user_id:
                    return DBService._normalize_doc(u)
            return None

    @staticmethod
    def upsert_seed_user(user_doc: dict[str, Any]) -> None:
        email = (user_doc.get("email") or "").lower().strip()
        if not email:
            return

        now = datetime.now(timezone.utc)
        safe_doc = dict(user_doc)
        safe_doc["email"] = email
        safe_doc.setdefault("created_at", now)
        safe_doc["updated_at"] = now
        safe_doc.setdefault("disabled", False)

        try:
            DBService.get_user_collection().update_one(
                {"email": email},
                {"$setOnInsert": safe_doc},
                upsert=True,
            )
        except RuntimeError:
            _FAKE_USERS.setdefault(email, safe_doc)

    @staticmethod
    def update_user_by_id(user_id: str, updates: dict[str, Any]) -> dict[str, Any] | None:
        user_id = str(user_id).strip()
        if not user_id:
            return None

        patch = {
            k: v for k, v in updates.items() if v is not None
        }
        patch["updated_at"] = datetime.now(timezone.utc)

        try:
            col = DBService.get_user_collection()
            doc: dict[str, Any] | None = None
            try:
                oid = ObjectId(user_id)
                col.update_one({"_id": oid}, {"$set": patch})
                doc = col.find_one({"_id": oid})
            except (InvalidId, TypeError, ValueError):
                doc = None

            if not doc:
                col.update_one({"id": user_id}, {"$set": patch})
                doc = col.find_one({"id": user_id})

            return DBService._normalize_doc(doc)
        except RuntimeError:
            for email, user in _FAKE_USERS.items():
                if str(user.get("id")) == user_id:
                    user.update(patch)
                    _FAKE_USERS[email] = user
                    return DBService._normalize_doc(user)
            return None

    @staticmethod
    def insert_attack(item: dict[str, Any]) -> dict[str, Any]:
        col = DBService.get_attack_collection()
        now = datetime.now(timezone.utc)
        item = dict(item)
        item.setdefault("timestamp", now)
        item.setdefault("created_at", now)
        item.setdefault("updated_at", now)
        res = col.insert_one(item)
        saved = col.find_one({"_id": res.inserted_id})
        normalized = DBService._normalize_doc(saved)
        return normalized or {}

    @staticmethod
    def list_attacks(limit: int = 500) -> list[dict[str, Any]]:
        docs = list(
            DBService.get_attack_collection()
            .find({})
            .sort("timestamp", -1)
            .limit(limit)
        )
        return DBService._normalize_many(docs)

    @staticmethod
    def search_attacks(filters: dict[str, Any]) -> list[dict[str, Any]]:
        docs = list(DBService.get_attack_collection().find(filters).sort("timestamp", -1))
        return DBService._normalize_many(docs)

    @staticmethod
    def insert_firewall_rule(rule: dict[str, Any]) -> dict[str, Any]:
        col = DBService.get_firewall_collection()
        now = datetime.now(timezone.utc)
        rule = dict(rule)
        rule.setdefault("created_at", now)
        rule.setdefault("updated_at", now)
        res = col.insert_one(rule)
        saved = col.find_one({"_id": res.inserted_id})
        normalized = DBService._normalize_doc(saved)
        return normalized or {}

    @staticmethod
    def list_firewall_rules(limit: int = 500) -> list[dict[str, Any]]:
        docs = list(
            DBService.get_firewall_collection()
            .find({})
            .sort("created_at", -1)
            .limit(limit)
        )
        return DBService._normalize_many(docs)

    @staticmethod
    def insert_incident(incident: dict[str, Any]) -> dict[str, Any]:
        col = DBService.get_incident_collection()
        now = datetime.now(timezone.utc)
        incident = dict(incident)
        incident.setdefault("created_at", now)
        incident.setdefault("updated_at", now)
        res = col.insert_one(incident)
        saved = col.find_one({"_id": res.inserted_id})
        normalized = DBService._normalize_doc(saved)
        return normalized or {}