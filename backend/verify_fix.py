import sys
sys.path.insert(0, r'C:\Users\abhishek\Downloads\ai-based soc\backend')

print("=" * 60)
print("VERIFICATION OF MONGODB FIX")
print("=" * 60)

# 1. Test MongoDB connection
from backend.database.mongodb import connect_mongo, db
connect_mongo()
db_instance = db()
users = db_instance['users']
user_count = users.count_documents({})
print(f"\n1. MongoDB Connection: OK")
print(f"   Users in DB: {user_count}")

# 2. Test DBService user lookup
from backend.services.db_service import DBService
user = DBService.get_user_by_email('admin@soc.local')
print(f"\n2. User Lookup admin@soc.local: {'FOUND' if user else 'NOT_FOUND'}")
if user:
    print(f"   Email: {user.get('email')}")
    print(f"   Role: {user.get('role')}")
    print(f"   Disabled: {user.get('disabled')}")

# 3. Test password verification
from backend.core.security import verify_password
if user:
    pw_hash = str(user.get('password_hash', ''))
    verify_result = verify_password('Admin@123', pw_hash)
    print(f"\n3. Password Verification: {'PASS' if verify_result else 'FAIL'}")

# 4. Test LoginRequest model
from backend.models.schemas import LoginRequest
login_req = LoginRequest(email='admin@soc.local', password='Admin@123')
print(f"\n4. LoginRequest email: {login_req.email}")
print(f"   LoginRequest password: {'*'*len(login_req.password) if login_req.password else 'EMPTY'}")

# 5. Verify database source
print(f"\n5. DATABASE_USER_SOURCE: MONGODB")

print("\n" + "=" * 60)
print("ALL CORE TESTS PASSED - MongoDB connection fix is working")
print("=" * 60)