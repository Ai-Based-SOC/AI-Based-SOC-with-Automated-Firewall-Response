#!/usr/bin/env python
import subprocess
import sys
import time

# Start backend
cmd = [
    sys.executable,
    "-c",
    "import uvicorn; uvicorn.run('backend.app.main:app', host='127.0.0.1', port=8001)"
]

print('Starting backend...')
proc = subprocess.Popen(
    cmd,
    cwd=r'c:\Users\abhishek\Downloads\ai-based soc',
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    encoding='utf-8',
    errors='replace'
)

# Wait for startup
time.sleep(3)

# Check if process is still running
if proc.poll() is None:
    print('Backend process started (PID: {})'.format(proc.pid))
else:
    stdout, stderr = proc.communicate()
    print('Backend failed:')
    print('STDOUT:', stdout)
    print('STDERR:', stderr)