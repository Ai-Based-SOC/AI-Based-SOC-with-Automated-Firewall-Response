import urllib.request
import json

def test_post(path, data, headers=None, base_url='http://127.0.0.1:8001'):
    url = base_url + path
    req_data = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=req_data, method='POST')
    req.add_header('Content-Type', 'application/json')
    if headers:
        for k, v in headers.items():
            req.add_header(k, v)
    try:
        response = urllib.request.urlopen(req, timeout=5)
        body = json.loads(response.read())
        return response.status, body, None
    except urllib.error.HTTPError as e:
        body = json.loads(e.read()) if e.code >= 400 else None
        return e.code, body, 'HTTP Error'
    except Exception as e:
        return None, None, str(e)

def test_get(path, headers=None, base_url='http://127.0.0.1:8001'):
    url = base_url + path
    req = urllib.request.Request(url, headers=headers or {})
    try:
        response = urllib.request.urlopen(req, timeout=5)
        body = json.loads(response.read())
        return response.status, body, None
    except urllib.error.HTTPError as e:
        body = json.loads(e.read()) if e.code >= 400 else None
        return e.code, body, 'HTTP Error'
    except Exception as e:
        return None, None, str(e)

# I have a valid token from login
token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI2OWU0NGZiYzNlZmZhMjA0OWQ1YTYzOTgiLCJlbWFpbCI6ImFkbWluQHNvYy5jb20iLCJyb2xlIjoiYWRtaW4iLCJleHAiOjE3ODg4MDEyMTQsImlhdCI6MTc4ODcxNDgxNCwibmJmIjoxNzg4NzE0ODE0LCJpc3MiOiJhaS1zb2MtYmFja2VuZCIsImF1ZCI6ImFpLXNvYy1jbGllbnRzIn0.Y9A4eHSS2LAeCBK-RLIOk3NM5U-6t5k4aiquEcmYABQ'
auth_headers = {'Authorization': 'Bearer ' + token}

print('=== Testing CRUD operations with auth token ===')
print()

# Test GET endpoints that work
endpoints = [
    ('GET', '/api/v1/attacks', auth_headers, 'List attacks'),
    ('GET', '/api/v1/geo/lookup', auth_headers, 'Geo lookup'),
    ('GET', '/api/v1/metrics', auth_headers, 'Metrics'),
    ('GET', '/api/v1/firewall-rules', auth_headers, 'Firewall rules'),
]

print('GET endpoints:')
for method, path, headers, desc in endpoints:
    status, body, error = test_get(path, headers)
    detail = ''
    if body and isinstance(body, dict) and 'detail' in body:
        detail = body['detail']
    print(f'  {method} {path}: status={status}', end='')
    if detail:
        print(f', detail={detail}', end='')
    print(f' ({desc})')
print()

# Test POST endpoints
print('POST endpoints:')

# Firewall block
status, body, error = test_post('/api/v1/firewall/block', {'ip_address': '192.168.1.1', 'reason': 'test blocking'}, auth_headers)
detail = ''
if body and isinstance(body, dict) and 'detail' in body:
    detail = body['detail']
print(f'  POST /api/v1/firewall/block: status={status}', end='')
if detail:
    print(f', detail={detail}', end='')
print()

# Firewall unblock
status, body, error = test_post('/api/v1/firewall/unblock', {'ip_address': '192.168.1.1', 'reason': 'test unblocking'}, auth_headers)
detail = ''
if body and isinstance(body, dict) and 'detail' in body:
    detail = body['detail']
print(f'  POST /api/v1/firewall/unblock: status={status}', end='')
if detail:
    print(f', detail={detail}', end='')
print()

# Threat intel check
status, body, error = test_post('/api/v1/threat-intel/check', {'ip': '8.8.8.8'}, auth_headers)
detail = ''
if body and isinstance(body, dict) and 'detail' in body:
    detail = body['detail']
print(f'  POST /api/v1/threat-intel/check: status={status}', end='')
if detail:
    print(f', detail={detail}', end='')
print()

# Reports generate
status, body, error = test_post('/api/v1/reports/generate', {'incident_id': 'test-incident'}, auth_headers)
detail = ''
if body and isinstance(body, dict) and 'detail' in body:
    detail = body['detail']
print(f'  POST /api/v1/reports/generate: status={status}', end='')
if detail:
    print(f', detail={detail}', end='')
print()