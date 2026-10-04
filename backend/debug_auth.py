#!/usr/bin/env python
import sys
sys.path.insert(0, r"C:\Users\abhishek\Downloads\ai-based soc\backend")
from backend.services.db_service import DBService
user = DBService.get_user_by_email("admin@soc.local")
if user:
    print("User found!")
    print("All keys:", list(user.keys()))
    pw = user.get("password_hash", "")
    print("password_hash value:", pw[:50] if pw else "EMPTY")
    pw2 = user.get("hashed_password", "")
    print("hashed_password value:", pw2[:50] if pw2 else "EMPTY")
else:
    print("User NOT found")