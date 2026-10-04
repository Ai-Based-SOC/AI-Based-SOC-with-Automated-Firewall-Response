import urllib.request, json

req = urllib.request.urlopen('http://127.0.0.1:8001/openapi.json', timeout=5)
spec = json.loads(req.read())
paths = spec.get('paths', {})

for path, methods in paths.items():
    if 'geo' in path.lower():
        print(f'\n=== {path} ===')
        for method, details in methods.items():
            print(f'  {method.upper()}:')
            summary = details.get('summary', 'N/A')
            print(f'    summary: {summary}')
            if 'parameters' in details:
                for p in details['parameters']:
                    pname = p.get('name', '')
                    pin = p.get('in', '')
                    prec = p.get('required', False)
                    pschema = p.get('schema', {})
                    ptitle = pschema.get('title', 'N/A')
                    print(f'    param: {pname} in {pin} required={prec} title={ptitle}')
            if 'requestBody' in details:
                print(f'    requestBody: required={details["requestBody"].get("required", False)}')
            if 'responses' in details:
                for code, resp in details['responses'].items():
                    print(f'    {code}: {resp.get("description", "N/A")}')