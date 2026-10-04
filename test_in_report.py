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

token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI2OWU0NGZiYzNlZmZhMjA0OWQ1YTYzOTgiLCJlbWFpbCI6ImFkbWluQHNvYy5jb20iLCJyb2xlIjoiYWRtaW4iLCJleHAiOjE3ODg4MDEyMTQsImlhdCI6MTc4ODcxNDgxNCwibmJmIjoxNzg4NzE0ODE0LCJpc3MiOiJhaS1zb2MtYmFja2VuZCIsImF1ZCI6ImFpLXNvYy1jbGllbnRzIn0.Y9A4eHSS2LAeCBK-RLIOk3NM5U-6t5k4aiquEcmYABQ'
auth_headers = {'Authorization': 'Bearer ' + token}

# Test ingestion/file
print('Testing /api/v1/ingestion/file POST:')
status, body, error = test_post('/api/v1/ingestion/file', {'file_path': '/tmp/test.log'}, auth_headers)
print(f'  Status: {status}', end='')
if body:
    if isinstance(body, dict) and 'detail' in body:
        print(f', detail={body["detail"]}')
    else:
        print(f', body keys: {list(body.keys()) if isinstance(body, dict) else body}', end='')
print()

# Test reports/generate
print('Testing /api/v1/reports/generate POST:')
status, body, error = test_post('/api/v1/reports/generate', {'incident_id': 'test-inc-123'}, auth_headers)
print(f'  Status: {status}', end='')
if body:
    if isinstance(body, dict) and 'detail' in body:
        print(f', detail={body["detail"]}')
    else:
        print(f', report: {str(body)[:80]}', end='')
print()