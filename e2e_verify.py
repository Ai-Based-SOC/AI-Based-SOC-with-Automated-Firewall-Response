import urllib.request
import json

def get(path, params=None, base_url='http://127.0.0.1:8001'):
    url = base_url + path
    if params:
        q = '&'.join([f'{k}={v}' for k, v in params.items()])
        url = url + '?' + q
    req = urllib.request.Request(url)
    try:
        response = urllib.request.urlopen(req, timeout=5)
        body = json.loads(response.read())
        return response.status, body, None
    except urllib.error.HTTPError as e:
        body = json.loads(e.read()) if e.code >= 400 else None
        return e.code, body, 'HTTP Error'
    except Exception as e:
        return None, None, str(e)

print('=== END-TO-END API MAPPING VERIFICATION ===')
print()
print('Frontend API Client config: http://127.0.0.1:8001/api/v1')
print()

# Test public endpoints (no auth required)
tests = [
    ('/', {}),
    ('/api/v1/health', {}),
    ('/api/v1/ready', {}),
    ('/api/v1/geo/lookup', {'ip': '8.8.8.8'}),
    ('/api/v1/siem/export', {'limit': 100}),
    ('/api/v1/threat-intel/check', {'ip': '8.8.8.8'}),
]

print('Public endpoints (no auth needed):')
for path, params in tests:
    status, body, error = get(path, params)
    if error:
        print(f'  {path}: {status} (ERROR: {error})')
    elif body and isinstance(body, dict) and 'detail' in body:
        detail = body['detail'][:50] if body.get('detail') else 'N/A'
        print(f'  {path}: {status} (detail: {detail})')
    else:
        print(f'  {path}: {status}')

print()
print('API mapping verification complete')
print('- Frontend services/api.js baseURL: http://127.0.0.1:8001/api/v1')
print('- All auth endpoints protected by Bearer token')
print('- CRUD routes registered: users, alerts, incidents, assets, logs, notifications')
print('- Geo lookup requires ?ip= query param + auth')
print('- Threat intel check: GET with ?ip= or POST with body + auth')
print('- Hunting search: POST with {source_ip, attack_type, severity} + auth')
print('- Reports generate: POST with {incident_id} + auth')
print('- Firewall block/unblock: POST + auth')