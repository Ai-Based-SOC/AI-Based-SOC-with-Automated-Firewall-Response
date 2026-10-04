import re

with open(r'C:\Users\abhishek\Downloads\ai-based soc\frontend\src\App.jsx', 'r') as f:
    content = f.read()

# Replace the problematic LiveMapRoute line
old = 'element={<LiveMapPage profile={profile} onLogout={() => localStorage.removeItem("soc_token")} />} />'
new = 'element={protectedPage(<LiveMapPage />)}'

content = content.replace(old, new)

with open(r'C:\Users\abhishek\Downloads\ai-based soc\frontend\src\App.jsx', 'w') as f:
    f.write(content)
print('Done')