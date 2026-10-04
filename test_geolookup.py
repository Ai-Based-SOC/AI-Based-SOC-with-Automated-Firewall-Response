import urllib.request
import json

def test_get(path, params=None, headers=None, base_url='http://127.0.0.1:8001'):
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

token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI2OWU0NGZiYzNlZmZhMjA0OWQ1YTYzOTgiLCJlbWFpbCI6ImFkbWluQHNvYy5jb20iLCJyb2xlIjoiYWRtaW4iLCJleHAiOjE3ODg4MDEyMTQsImlhdCI6MTc4ODcxNDgxNCwibmJmIjoxNzg4NzE0ODE0LCJpc3MiOiJhaS1zb2MtYmFja2VuZCIsImF1ZCI6ImFpLXNvYy1jbGllbnRzIn0.Y9A4eHSS2LAeCBK-RLIOk3NM5U-6t5k4aiquEcmYABQ'
auth_headers = {'Authorization': 'Bearer ' + token}

# Test geo/lookup with ip query parameter
print('Testing /api/v1/geo/lookup with ip=8.8.8.8:')
status, body, error = test_get('/api/v1/geo/lookup', {'ip': '8.8.8.8'}, auth_headers)
print(f'  Status: {status}', end='')
if body:
    if isinstance(body, dict) and 'detail' in body:
        print(f', detail={body["detail"]}', end='')
    else:
        print(f', body keys: {list(body.keys()) if isinstance(body, dict) else body}', end='')
print()

# Test without auth
print('Testing /api/v1/geo/lookup without auth:')
status, body, error = test_get('/api/v1/geo/lookup', {'ip': '8.8.8.8'})
print(f'  Status: {status}', end='')
if body:
    if isinstance(body, dict) and 'detail' in body:
        print(f', detail={body["detail"]}', end='')
    else:
        print(f', body: {str(body)[:80]}', end='')
print()