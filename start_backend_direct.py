#!/usr/bin/env python
import subprocess
import sys

cmd = [sys.executable, "-c", 
    "import uvicorn; uvicorn.run('backend.app.main:app', host='127.0.0.1', port=8001)"]
    
print(f"Running: {' '.join(cmd)}")
proc = subprocess.Popen(
    cmd,
    cwd=r"c:\Users\abhishek\Downloads\ai-based soc",
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    encoding='utf-8',
    errors='replace'
)

import time
time.sleep(3)

if proc.poll() is None:
    print("Backend started successfully (PID: {})".format(proc.pid))
else:
    stdout, stderr = proc.communicate()
    print("Backend failed:")
    print("STDOUT:", stdout)
    print("STDERR:", stderr)