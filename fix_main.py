#!/usr/bin/env python
import re

with open('backend/app/main.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Add the router import after starlette.responses import
import_line = 'from starlette.responses import PlainTextResponse'
new_import = '''from starlette.responses import PlainTextResponse

# Include API routes
from backend.routes import auth, attacks, firewall, threat_intel, ws_routes, health, db_admin, geo_routes, ingestion, ml_routes, reports, hunting, siem_routes'''

if import_line in content:
    content = content.replace(import_line, new_import)
    print("Added router import")

# Add router inclusion after app = FastAPI(
app_init_marker = 'app = FastAPI('
# Find the position after the closing paren of FastAPI
fastapi_end = content.find(')\n', content.find(app_init_marker))
if fastapi_end != -1:
    # Insert after the FastAPI() block
    insertion_point = fastapi_end + 1
    router_code = '''

# Include all API routers with /api/v1 prefix
API_PREFIX = "/api/v1"
app.include_router(auth.router, prefix=API_PREFIX, tags=["Auth"])
app.include_router(attacks.router, prefix=API_PREFIX, tags=["Attacks"])
app.include_router(firewall.router, prefix=API_PREFIX, tags=["Firewall"])
app.include_router(threat_intel.router, prefix=API_PREFIX, tags=["Threat Intelligence"])
app.include_router(ws_routes.router, prefix=API_PREFIX, tags=["WebSocket"])
app.include_router(health.router, prefix=API_PREFIX, tags=["Health"])
app.include_router(db_admin.router, prefix=API_PREFIX, tags=["DB Admin"])
app.include_router(geo_routes.router, prefix=API_PREFIX, tags=["Geo"])
app.include_router(ingestion.router, prefix=API_PREFIX, tags=["Ingestion"])
app.include_router(ml_routes.router, prefix=API_PREFIX, tags=["ML"])
app.include_router(reports.router, prefix=API_PREFIX, tags=["Reports"])
app.include_router(hunting.router, prefix=API_PREFIX, tags=["Hunting"])
app.include_router(siem_routes.router, prefix=API_PREFIX, tags=["Siem"])
'''
    content = content[:insertion_point] + router_code + content[insertion_point:]
    print("Added router inclusion")

with open('backend/app/main.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("File updated successfully")