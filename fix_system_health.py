import re

with open('C:\\Users\\abhishek\\Downloads\\ai-based soc\\frontend\\src\\pages\\SystemHealthPage.jsx', 'r') as f:
    content = f.read()

content = content.replace('w-65%', 'style width 65%')
content = content.replace('w-80%', 'style width 80%')
content = content.replace('w-75%', 'style width 75%')

with open('C:\\Users\\abhishek\\Downloads\\ai-based soc\\frontend\\src\\pages\\SystemHealthPage.jsx', 'w') as f:
    f.write(content)

print('Done replacing widths')