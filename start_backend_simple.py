import subprocess
import time
import socket

print("Starting backend...")
proc = subprocess.Popen(
    [r"c:\Users\abhishek\anaconda3\python.exe", r"c:\Users\abhishek\Downloads\ai-based soc\start_backend.py"],
    cwd=r"c:\Users\abhishek\Downloads\ai-based soc",
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    encoding='utf-8',
    errors='replace'
)

time.sleep(3)

# Check if process is still running
if proc.poll() is None:
    print("Backend process is running")
else:
    stdout, stderr = proc.communicate()
    print(f"Backend exited with stdout: {stdout}")
    print(f"Backend exited with stderr: {stderr}")
    exit(1)

# Check ports
for port in [8001, 5173]:
    s = socket.socket()
    result = s.connect_ex(('127.0.0.1', port))
    print(f'Port {port}: {"OPEN" if result == 0 else "CLOSED"}')
    s.close()