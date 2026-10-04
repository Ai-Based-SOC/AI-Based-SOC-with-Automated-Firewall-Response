import sys
sys.path.insert(0, r"C:\Users\abhishek\Downloads\ai-based soc\backend")
from backend.services.db_service import DBService
user = DBService.get_user_by_email("admin@soc.local")
print("exists:", user is not None)
if user:
    print("keys:", list(user.keys()))
    print("email:", user.get("email", "N/A"))
    print("role:", user.get("role", "N/A"))
    print("disabled:", user.get("disabled", "N/A"))
    # Check both password_hash and hashed_password
    pw_hash = user.get("password_hash", "")
    hashed_pw = user.get("hashed_password", "")
    print("password_hash present:", bool(str(pw_hash).strip()))
    print("hashed_password present:", bool(str(hashed_pw).strip()))
    # Show first 30 chars only if present
    if pw_hash:
        print("password_hash (first 30):", str(pw_hash)[:30])
    if hashed_pw:
        print("hashed_password (first 30):", str(hashed_pw)[:30])
else:
    print("User not found")