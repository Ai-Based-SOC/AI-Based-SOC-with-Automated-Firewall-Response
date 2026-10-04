import sys
sys.path.insert(0, r'C:\Users\abhishek\Downloads\ai-based soc\backend')
from backend.services.db_service import DBService
from backend.core.security import verify_password
from backend.models.schemas import LoginRequest

# Simulate the exact login flow

# Step 1: What the frontend sends (as would come from HTTP POST)
payload_email = "admin@soc.local"
payload_password = "Admin@123"

# Step 2: FastAPI LoginRequest model processes it
login_req = LoginRequest(email=payload_email, password=payload_password)
print(f"LoginRequest.email: '{login_req.email}'")
print(f"LoginRequest.password: '{login_req.password}'")

# Step 3: DBService.get_user_by_email processes the email
# From the code: email = (email or "").lower().strip()
normalized_email = (login_req.email or "").lower().strip()
print(f"\nNormalized email: '{normalized_email}'")

# Step 4: Look up user
user = DBService.get_user_by_email(normalized_email)
print(f"User found: {user is not None}")
if user:
    print(f"User email in DB: '{user.get('email')}'")
    print(f"User disabled: {user.get('disabled')}")
    
    # Step 5: verify_password
    pw_hash = str(user.get("password_hash", ""))
    verify_result = verify_password(login_req.password, pw_hash)
    print(f"\nverify_password result: {verify_result}")
    
    # Step 6: Check disabled
    disabled = user.get("disabled") is True
    print(f"User disabled check: {disabled}")
else:
    print("User NOT found - this could be the issue!")