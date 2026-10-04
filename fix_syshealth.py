import re

with open(r'C:\\Users\\abhishek\\Downloads\\ai-based soc\\frontend\\src\\pages\\SystemHealthPage.jsx', 'r') as f:
    content = f.read()

# Replace hardcoded connection hosts with null (will be fetched from API)
content = content.replace('{ protocol: \"SSH\", hosts: 12, status: \"healthy\" }', '{ protocol: \"SSH\", hosts: null, status: \"healthy\" }')
content = content.replace('{ protocol: \"HTTP\", hosts: 47, status: \"healthy\" }', '{ protocol: \"HTTP\", hosts: null, status: \"healthy\" }')
content = content.replace('{ protocol: \"HTTPS\", hosts: 89, status: \"healthy\" }', '{ protocol: \"HTTPS\", hosts: null, status: \"healthy\" }')
content = content.replace('{ protocol: \"DNS\", hosts: 12, status: \"healthy\" }', '{ protocol: \"DNS\", hosts: null, status: \"healthy\" }')

# Replace hardcoded alert counts with dynamic health values
content = content.replace('128', 'health.alerts.total')
content = content.replace('96', 'health.alerts.blocked')

with open(r'C:\\Users\\abhishek\\Downloads\\ai-based soc\\frontend\\src\\pages\\SystemHealthPage.jsx', 'w') as f:
    f.write(content)

print('Done replacing hardcoded values')