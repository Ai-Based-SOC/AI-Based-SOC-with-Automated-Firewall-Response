"""Debug the user document structure from DBService."""
import sys
sys.path.insert(0, r"C:\Users\abhishek\Downloads\ai-based soc\backend")
sys.path.insert(0, r"C:\Users\abhishek\Downloads\ai-based soc\backend\.venv\Lib\site-packages")
from backend.services.db_service import DBService

# Get the user document
user = DBService.get_user_by_email("admin@soc.local")
print(f"User document: {user}")
print(f"User type: {type(user)}")
if user:
    print(f"\nAll keys in user dict:")
    for key in user.keys():
        val = user[key]
        val_str = str(val)[:50] if len(str(val)) > 50 else str(val)
        print(f"  {key}: {val_str}")
    
    # Check specific fields
    print(f"\n  password_hash: {user.get('password_hash', 'NOT FOUND')}")
    print(f"  hashed_password: {user.get('hashed_password', 'NOT FOUND')}")
    print(f"  email: {user.get('email', 'NOT FOUND')}")
    print(f"  role: {user.get('role', 'NOT FOUND')}")
    print(f"  disabled: {user.get('disabled', 'NOT FOUND')}")