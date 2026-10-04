import json

with open('openapi.json', 'r') as f:
    spec = json.load(f)

paths = spec.get('paths', {})

print('=== COMPLETE OPENAPI ENDPOINT INVENTORY ===')
print(f'Total endpoints: {sum(len(methods) for methods in paths.values())}')
print()

# Table header
print('Method      Path                                                Auth   Body   Summary')
print('-' * 80)

for path, methods in sorted(paths.items()):
    for method, details in methods.items():
        summary = details.get('summary', 'N/A')
        tags = details.get('tags', [])
        
        # Check authentication
        parameters = details.get('parameters', [])
        required_auth = False
        for param in parameters:
            if param.get('name') == 'authorization' and param.get('in') == 'header':
                required_auth = param.get('required', False)
                break
        
        # Check request body
        request_body = details.get('requestBody', None)
        has_body = request_body is not None and request_body.get('required', False)
        
        auth_str = 'YES' if required_auth else 'NO'
        body_str = 'YES' if has_body else 'NO'
        
        print(f'{method.upper():<6} {path:<45} {auth_str:<6} {body_str:<6} {summary}')

print()
print('=== AUTHENTICATION FLOW ===')
print('1. POST /api/v1/auth/login - email/password -> TokenResponse with access_token')
print('2. GET /api/v1/auth/me - requires Bearer token in Authorization header')
print('3. Token includes: access_token, token_type (bearer), role')
print()

print('=== SCHEMAS SUMMARY ===')
components = spec.get('components', {}).get('schemas', {})
for name, schema in components.items():
    required = schema.get('required', [])
    print(f'{name}: required={required}')