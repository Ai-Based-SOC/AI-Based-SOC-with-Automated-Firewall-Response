from backend.app.api.v1.alerts import router as alerts
from backend.app.api.v1.assets import router as assets
from backend.app.api.v1.auth import router as auth
from backend.app.api.v1.firewall import router as firewall
from backend.app.api.v1.incidents import router as incidents
from backend.app.api.v1.logs import router as logs
from backend.app.api.v1.notifications import router as notifications
from backend.app.api.v1.reports import router as reports
from backend.app.api.v1.threat_intel import router as threat_intel
from backend.app.api.v1.threat_intel_new import router as threat_intel_new
from backend.app.api.v1.users import router as users
from backend.app.api.v1.admin import router as admin

__all__ = [
    'alerts', 'assets', 'auth', 'firewall',
    'incidents', 'logs', 'notifications', 'reports',
    'threat_intel', 'threat_intel_new', 'users', 'admin',
]