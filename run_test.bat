@echo off
cd C:\Users\abhishek\Downloads\ai-based soc
call .venv\Scripts\activate.bat
python -m pytest backend/tests/test_auth_and_reports.py::test_auth_login_success -v > test_results.txt 2>&1
echo.
echo ===== TEST RESULTS =====
type test_results.txt