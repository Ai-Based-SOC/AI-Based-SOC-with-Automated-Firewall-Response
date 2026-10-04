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

# Try various credential combinations
creds = [
    {'email': 'admin@test.com', 'password': 'admin123'},
    {'email': 'test@test.com', 'password': 'test123'},
    {'email': 'user@test.com', 'password': 'password123'},
    {'email': 'admin', 'password': 'admin123'},
    {'email': 'root', 'password': 'root123'},
    {'email': 'demo', 'password': 'demo123'},
]

for i, c in enumerate(creds):
    status, body, error = test_post('/api/v1/auth/login', c)
    detail = ''
    if body and 'detail' in body:
        detail = body['detail']
    print(f'Cred {i+1} {c}: status={status}, detail={detail}')