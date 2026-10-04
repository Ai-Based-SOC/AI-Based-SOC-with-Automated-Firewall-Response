import sys
sys.path.insert(0, r'C:\Users\abhishek\Downloads\ai-based soc')

try:
    from backend.app.main import app
    print('Backend imports OK - FastAPI app created successfully')
except Exception as e:
    print(f'Import error: {type(e).__name__}: {e}')

try:
    from backend.core.config import settings
    print(f'Config OK - ENV: {settings.ENV}, APP_NAME: {settings.app_name}')
except Exception as e:
    print(f'Config error: {type(e).__name__}: {e}')

try:
    from backend.core.security import hash_password, verify_password, create_access_token, decode_access_token
    print('Security imports OK')
except Exception as e:
    print(f'Security import error: {type(e).__name__}: {e}')

try:
    from backend.database.mongodb import connect_mongo, close_mongo, db
    print('MongoDB imports OK')
except Exception as e:
    print(f'MongoDB import error: {type(e).__name__}: {e}')