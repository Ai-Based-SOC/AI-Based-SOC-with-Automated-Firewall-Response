import os
backend_dir = r'C:\Users\abhishek\Downloads\ai-based soc\backend'
for item in os.listdir(backend_dir):
    full_path = os.path.join(backend_dir, item)
    if os.path.isdir(full_path):
        print(f"DIR: {item}")
        for sub in os.listdir(full_path):
            print(f"  - {sub}")
    else:
        print(f"FILE: {item}")