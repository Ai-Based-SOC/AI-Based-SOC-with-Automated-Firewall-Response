import urllib.request
import json

def test_post(path, data):
    url = 'http://127.0.0.1:8000' + path
    req = urllib.request.Request(url, data=json.dumps(data).encode(), method='POST')
    req.add_header('Content-Type', 'application/json')
    try:
        response = urllib.request.urlopen(req, timeout=5)
        body = json.loads(response.read())
        return response.status, body, None
    except urllib.error.HTTPError as e:
        body = json.loads(e.read()) if e.code >= 400 else None
        return e.code, body, 'HTTP Error'
    except Exception as e:
        return None, None, str(e)

def test_get(path):
    url = 'http://127.0.0.1:8000' + path
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

# Test login first
print('Testing login endpoint:')
status, body, error = test_post('/api/v1/auth/login', {'email': 'admin@example.com', 'password': 'password123'})
print(f'  Login status: {status}')
if body:
    print(f'  Login body: {body}')
print()

# Test unauthenticated endpoints
endpoints = [
    ('GET', '/', 'Root'),
    ('GET', '/api/v1/health', 'Health'),
    ('GET', '/api/v1/ready', 'Ready'),
    ('GET', '/api/v1/auth/me', 'Auth Me (unauth)'),
    ('GET', '/api/v1/geo/lookup', 'Geo Lookup'),
    ('GET', '/api/v1/siem/export', 'Siem Export (unauth)'),
    ('GET', '/api/v1/metrics', 'Metrics'),
]

print('Testing unauthenticated endpoints:')
print('=' * 70)
for method, path, desc in endpoints:
    status, body, error = test_get(path)
    status_str = str(status) if status else 'ERROR'
    if body and isinstance(body, dict) and 'detail' in body:
        result = body['detail']
    elif body:
        result = str(body)[:80]
    else:
        result = 'Error: ' + error if error else 'No response'
    print(f'{method:6} {path:40} -> {status_str:4} - {result} ({desc})')

print()

# Test POST endpoints without auth
post_endpoints = [
    ('POST', '/api/v1/auth/login', 'Login'),
    ('POST', '/api/v1/firewall/block', 'Firewall Block'),
    ('POST', '/api/v1/firewall/unblock', 'Firewall Unblock'),
    ('POST', '/api/v1/threat-intel/check', 'Threat Intel Check'),
]

print('Testing POST endpoints (unauthenticated):')
print('=' * 70)
for method, path, desc in post_endpoints:
    status, body, error = test_post(path, {'ip': '8.8.8.8'} if 'threat' in path else {'email': 'admin@example.com', 'password': 'password123'} if 'login' in path else {'ip_address': '192.168.1.1', 'reason': 'test'})
    status_str = str(status) if status else 'ERROR'
    if body and isinstance(body, dict) and 'detail' in body:
        result = body['detail']
    elif body:
        result = str(body)[:80]
    else:
        result = 'Error: ' + error if error else 'No response'
    print(f'{method:6} {path:40} -> {status_str:4} - {result} ({desc})')