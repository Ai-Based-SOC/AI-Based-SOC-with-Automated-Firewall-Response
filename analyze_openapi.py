import json

with open('openapi.json', 'r') as f:
    spec = json.load(f)

paths = spec.get('paths', {})

print('=== OPENAPI ENDPOINT INVENTORY ===')
print('OpenAPI Version:', spec.get('openapi'))
print('API Title:', spec.get('info', {}).get('title'))
print('API Version:', spec.get('info', {}).get('version'))
print()

for path, methods in sorted(paths.items()):
    for method, details in methods.items():
        summary = details.get('summary', 'N/A')
        operation_id = details.get('operationId', 'N/A')
        tags = details.get('tags', [])
        
        # Check for auth parameter
        parameters = details.get('parameters', [])
        required_auth = False
        for param in parameters:
            if param.get('name') == 'authorization' and param.get('in') == 'header':
                required_auth = param.get('required', False)
                break
        
        # Check request body
        request_body = details.get('requestBody', None)
        has_body = request_body is not None and request_body.get('required', False)
        
        # Get request schema ref
        request_schema = 'N/A'
        if request_body:
            schema_ref = request_body.get('content', {}).get('application/json', {}).get('schema', {})
            if '$ref' in schema_ref:
                request_schema = schema_ref['$ref'].split('/')[-1]
        
        # Get response schema ref
        response_200 = details.get('responses', {}).get('200', {})
        response_422 = details.get('responses', {}).get('422', {})
        resp_200_schema = 'N/A'
        resp_422_schema = 'N/A'
        if 'content' in response_200:
            resp_200_schema = response_200['content'].get('application/json', {}).get('schema', {}).get('$ref', 'N/A')
        if 'content' in response_422:
            resp_422_schema = response_422['content'].get('application/json', {}).get('schema', {}).get('$ref', 'N/A')
        
        auth_str = 'YES' if required_auth else 'NO'
        body_str = 'YES' if has_body else 'NO'
        
        print(f'{method.upper():6} {path:40}  Auth={auth_str:3}  Body={body_str:3}  Summary: {summary}')
        print(f'     Operation: {operation_id}')
        print(f'     Request Schema: {request_schema}')
        print(f'     200 Response: {resp_200_schema}')
        print(f'     422 Response: {resp_422_schema}')
        print()