#!/usr/bin/env python
"""Start backend and frontend services, then validate they work."""

import subprocess
import sys
import time
import socket
import os

print("=" * 60)
print("AI-Based SOC - Service Startup and Validation")
print("=" * 60)

# ============ Step 1: Start Backend ============
print("\n[1] Starting backend server on port 8001...")

backend_cmd = [
    sys.executable, "-c",
    "import uvicorn; uvicorn.run('backend.app.main:app', host='127.0.0.1', port=8001)"
]

backend_proc = subprocess.Popen(
    backend_cmd,
    cwd=r"c:\Users\abhishek\Downloads\ai-based soc",
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    encoding='utf-8',
    errors='replace'
)

# Wait for backend to start
time.sleep(3)

# Check if backend process is still running
if backend_proc.poll() is not None:
    stdout, stderr = backend_proc.communicate()
    print("ERROR: Backend process exited!")
    print("STDOUT:", stdout)
    print("STDERR:", stderr)
    sys.exit(1)

print("  Backend process running (PID: {})".format(backend_proc.pid))

# ============ Step 2: Wait and check port ============
print("\n[2] Checking port 8001...")

for attempt in range(10):
    s = socket.socket()
    result = s.connect_ex(('127.0.0.1', 8001))
    s.close()
    if result == 0:
        print("  Port 8001: OPEN")
        break
    time.sleep(1)
else:
    print("  Port 8001: Still closed after 10 seconds")
    sys.exit(1)

# ============ Step 3: Health check ============
print("\n[3] Running health checks...")

import urllib.request

# Check /openapi.json
try:
    req = urllib.request.Request('http://127.0.0.1:8001/openapi.json')
    with urllib.request.urlopen(req, timeout=5) as response:
        status = response.status
        print("  /openapi.json: Status {}".format(status))
except Exception as e:
    print("  /openapi.json: ERROR - {}".format(e))

# Check /docs
try:
    req = urllib.request.Request('http://127.0.0.1:8001/docs')
    with urllib.request.urlopen(req, timeout=5) as response:
        status = response.status
        print("  /docs: Status {}".format(status))
except Exception as e:
    print("  /docs: ERROR - {}".format(e))

# Check /auth/me
try:
    req = urllib.request.Request('http://127.0.0.1:8001/auth/me')
    with urllib.request.urlopen(req, timeout=5) as response:
        status = response.status
        body = response.read().decode('utf-8')
        print("  /auth/me: Status {} - {}".format(status, body[:100]))
except Exception as e:
    print("  /auth/me: ERROR - {}".format(e))

# ============ Step 4: Start Frontend ============
print("\n[4] Starting frontend on port 5173...")

# Check if npm is available
try:
    npm_proc = subprocess.run(
        ["npm", "--version"],
        capture_output=True, text=True, timeout=5
    )
    if npm_proc.returncode != 0:
        print("  npm not available, skipping frontend")
        frontend_available = False
    else:
        frontend_available = True
except Exception:
    print("  npm not available, skipping frontend")
    frontend_available = False

if frontend_available:
    # Navigate to frontend and start
    frontend_cmd = ["npm", "run", "dev"]
    frontend_proc = subprocess.Popen(
        frontend_cmd,
        cwd=r"c:\Users\abhishek\Downloads\ai-based soc\frontend",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        encoding='utf-8',
        errors='replace'
    )
    
    print("  Frontend process started (PID: {})".format(frontend_proc.pid))
    
    # Wait for frontend to start
    time.sleep(3)
    
    # Check port 5173
    for attempt in range(10):
        s = socket.socket()
        result = s.connect_ex(('127.0.0.1', 5173))
        s.close()
        if result == 0:
            print("  Port 5173: OPEN")
            break
        time.sleep(1)
    else:
        print("  Port 5173: Still closed after 10 seconds")
else else:
    print("  Skipping frontend startup")

print("\n" + "=" * 60)
print("Validation complete!")
print("=" * 60)