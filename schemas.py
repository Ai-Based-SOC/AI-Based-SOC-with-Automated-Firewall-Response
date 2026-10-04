import json

with open('openapi.json', 'r') as f:
    spec = json.load(f)

# Print schemas
components = spec.get('components', {}).get('schemas', {})
for schema_name, schema in components.items():
    print(f'=== {schema_name} ===')
    print(json.dumps(schema, indent=2)[:500])
    print()