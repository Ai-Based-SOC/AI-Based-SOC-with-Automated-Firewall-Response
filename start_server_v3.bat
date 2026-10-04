@echo off
cd c:\Users\abhishek\Downloads\ai-based soc
call .venv\Scripts\activate
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8002 --reload