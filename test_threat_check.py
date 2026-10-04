import urllib.request
import json

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

token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI2OWU0NGZiYzNlZmZhMjA0OWQ1YTYzOTgiLCJlbWFpbCI6ImFkbWluQHNvYy5jb20iLCJyb2xlIjoiYWRtaW4iLCJleHAiOjE3ODg4MDEyMTQsImlhdCI6MTc4ODcxNDgxNCwibmJmIjoxNzg4NzE0ODE0LCJpc3MiOiJhaS1zb2MtYmFja2VuZCIsImF1ZCI6ImFpLXNvYy1jbGllbnRzIn0.Y9A4eHSS2LAeCBK-RLIOk3NM5U-6t5k4aiquEcmYABQ'
auth_headers = {'Authorization': 'Bearer ' + token}

# Test threat-intel/check GET
print('Threat Intelligence Check:')
print('  GET:')
status, body, error = test_get('/api/v1/threat-intel/check', auth_headers)
if body and isinstance(body, dict) and 'detail' in body:
    print(f'    Status: {status}, detail={body["detail"]}')
else:
    print(f'    Status: {status}, body: {body}')

print('  POST:')
status, body, error = test_post('/api/v1/threat-intel/check', {'ip': '8.8.8.8'}, auth_headers)
if body and isinstance(body, dict) and 'detail' in body:
    print(f'    Status: {status}, detail={body["detail"]}')
else:
    print(f'    Status: {status}, body: {body}')