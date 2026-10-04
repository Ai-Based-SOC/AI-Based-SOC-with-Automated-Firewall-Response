import os
import re

# Read the file
with open('C:/Users/abhishek/Downloads/ai-based soc/backend/app/main.py', 'r') as f:
    content = f.read()

# Replace the DOCS_ENABLED references
old = '''docs_url="/docs" if DOCS_ENABLED else None,
    redoc_url="/redoc" if DOCS_ENABLED else None,
    openapi_url="/openapi.json" if DOCS_ENABLED else None,'''

new = '''docs_url="/docs" if settings.DOCS_ENABLED else None,
    redoc_url="/redoc" if settings.DOCS_ENABLED else None,
    openapi_url="/openapi.json" if settings.DOCS_ENABLED else None,'''

content = content.replace(old, new)

# Write back
with open('C:/Users/abhishek/Downloads/ai-based soc/backend/app/main.py', 'w') as f:
    f.write(content)

print('Done - replaced DOCS_ENABLED with settings.DOCS_ENABLED')