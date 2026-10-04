import sys
import os
sys.path.insert(0, os.getcwd())

from backend.app.core.config import get_settings

s = get_settings()
print('DOCS_ENABLED:', s.DOCS_ENABLED)
print('ENV:', s.ENV)
print('All settings loaded successfully')