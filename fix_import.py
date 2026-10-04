import re

with open(r'C:\\Users\\abhishek\\Downloads\\ai-based soc\\frontend\\src\\pages\\SystemHealthPage.jsx', 'r') as f:
    content = f.read()

# Replace default import with named import
old = 'import StatusBadge from \"../components/StatusBadge\";'
new = 'import { StatusBadge } from \"../components/StatusBadge\";'

content = content.replace(old, new)

with open(r'C:\\Users\\abhishek\\Downloads\\ai-based soc\\frontend\\src\\pages\\SystemHealthPage.jsx', 'w') as f:
    f.write(content)
print('Done')