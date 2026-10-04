import os

files = []
for root, dirs, fn in os.walk(r'c:\Users\abhishek\Downloads\ai-based soc\backend'):
    for f in fn:
        files.append(os.path.join(root, f))

for f in files[:30]:
    print(f)