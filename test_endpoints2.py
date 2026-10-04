import urllib.request
import json

def get(path, headers=None, params=None, base_url='http://127.0.0.1:8001'):
    url = base_url + path
    if params:
        q = '&'.join([f'{k}={v}' for k, v in params.items()])
        url = url + '?' + q
    req = urllib.request.Request(url)
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

def post(path, data, headers=None, base_url='http://127.0.0.1:8001'):
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

# Get auth token
print('Step 1: Login to get auth token...')
status, body, _ = post('/api/v1/auth/login', {'email': 'admin@soc.local', 'password': 'Admin@123'})
print('  Login status: ' + str(status))
if body and 'access_token' in body:
    token = body['access_token']
    auth_headers = {'Authorization': 'Bearer ' + token}
    print('  Got token, proceeding with endpoint tests...\n')
else:
    print('  Could not get token, using fallback token')
    token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI2OWU0NGZiYzNlZmZhMjA0OWQ1YTYzOTgiLCJlbWFpbCI6ImFkbWluQHNvYy5jb20iLCJyb2xlIjoiYWRtaW4iLCJleHAiOjE3ODg4MDEyMTQsImlhdCI6MTc4ODcxNDgxNCwibmJmIjoxNzg4NzE0ODE0LCJpc3MiOiJhaS1zb2MtYmFja2VuZCIsImF1ZCI6ImFpLXNvYy1jbGllbnRzIn0.Y9A4eHSS2LAeCBK-RLIOk3NM5U-6t5k4aiquEcmYABQ'
    auth_headers = {'Authorization': 'Bearer ' + token}
    print('  Using fallback token\n')

print('=== ENDPOINT TESTS ===')
print()

# Test 1-14 (from previous successful test)
tests = [
    ('1. GET /', lambda: get('/')),
    ('2. GET /api/v1/health', lambda: get('/api/v1/health')),
    ('3. GET /api/v1/ready', lambda: get('/api/v1/ready')),
    ('4. POST /api/v1/auth/login', lambda: post('/api/v1/auth/login', {'email': 'admin@soc.local', 'password': 'Admin@123'})),
    ('5. GET /api/v1/auth/me', lambda: get('/api/v1/auth/me', auth_headers)),
    ('6. GET /api/v1/attacks', lambda: get('/api/v1/attacks', auth_headers)),
    ('7. POST /api/v1/firewall/block', lambda: post('/api/v1/firewall/block', {'ip_address': '1.2.3.4', 'reason': 'test'}, auth_headers)),
    ('8. POST /api/v1/firewall/unblock', lambda: post('/api/v1/firewall/unblock', {'ip_address': '1.2.3.4'}, auth_headers)),
    ('9. GET /api/v1/geo/lookup with ip + auth', lambda: get('/api/v1/geo/lookup', auth_headers, {'ip': '8.8.8.8'})),
    ('10. GET /api/v1/siem/export', lambda: get('/api/v1/siem/export', auth_headers)),
    ('11. POST /api/v1/ml/predict', lambda: post('/api/v1/ml/predict', {'source_port': 80, 'dest_port': 443, 'bytes_sent': 1000, 'bytes_received': 2000, 'failed_logins': 0, 'request_rate': 10, 'is_internal_src': 0, 'proto': 'TCP', 'severity_num': 1}, auth_headers)),
    ('12. POST /api/v1/threat-intel/check', lambda: post('/api/v1/threat-intel/check', {'ip': '8.8.8.8'}, auth_headers)),
    ('13. GET /api/v1/threat-intel/check with ip + auth', lambda: get('/api/v1/threat-intel/check', auth_headers, {'ip': '8.8.8.8'})),
    ('14. POST /api/v1/hunting/search', lambda: post('/api/v1/hunting/search', {'source_ip': '8.8.8.8', 'attack_type': 'DDoS', 'severity': 'high'}, auth_headers)),
    ('15. POST /api/v1/reports/generate', lambda: post('/api/v1/reports/generate', {'incident_id': 'inc-001'}, auth_headers)),
    ('16. POST /api/v1/ingestion/file', lambda: post('/api/v1/ingestion/file', {'file_path': '/tmp/test.log'}, auth_headers)),
]

for label, test_fn in tests:
    status, body, error = test_fn()
    if error:
        print(label + ': ' + str(status) + ' (ERROR: ' + error + ')')
    elif body and isinstance(body, dict) and 'detail' in body:
        print(label + ': ' + str(status) + ' (detail: ' + body['detail'][:60] + ')')
    else:
        print(label + ': ' + str(status))

print()
print('=== DONE ===')