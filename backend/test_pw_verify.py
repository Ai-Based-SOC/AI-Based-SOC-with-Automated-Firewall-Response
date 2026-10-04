"""Test password verify directly."""
import sys
sys.path.insert(0, r"C:\Users\abhishek\Downloads\ai-based soc\backend")
from backend.core.security import hash_password, verify_password

# Test hash_password and verify_password
hashed = hash_password('Admin@123')
print(f'Hashed: {hashed[:50]}...')
result = verify_password('Admin@123', hashed)
print(f'verify_password(Admin@123, hashed): {result}')
result2 = verify_password('WrongPassword', hashed)
print(f'verify_password(WrongPassword, hashed): {result2}')