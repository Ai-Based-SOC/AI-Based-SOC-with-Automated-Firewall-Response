@echo off
cd C:\Users\abhishek\Downloads\ai-based soc
python -m uvicorn backend.app.main:app --port 8001 > server.log 2>&1
timeout /t 3 > nul
echo Server started, checking...