param([string]$GitPath = "C:\Users\abhishek\Downloads\ai-based soc")

& cmd /c "cd $GitPath && git diff --stat > diff_stat.txt"
& cmd /c "cd $GitPath && git diff -- backend/app/main.py > main_py_diff.txt"
& cmd /c "cd $GitPath && git diff -- frontend/src/App.jsx > app_jsx_diff.txt"
& cmd /c "cd $GitPath && git diff -- frontend/src/services/api.js > api_js_diff.txt"
& cmd /c "cd $GitPath && git diff -- backend/routes/auth.py > auth_py_diff.txt"
& cmd /c "cd $GitPath && git diff -- backend/services/auth_service.py > auth_service_py_diff.txt"
& cmd /c "cd $GitPath && git diff -- backend/services/db_service.py > db_service_py_diff.txt"

# Show the diffs
Write-Output "=== DIFF STAT ==="
Get-Content "$GitPath\diff_stat.txt"

Write-Output "=== MAIN.PY DIFF (first 100 lines) ==="
Get-Content "$GitPath\main_py_diff.txt" | Select-Object -First 100

Write-Output "=== APP.JSX DIFF (first 100 lines) ==="
Get-Content "$GitPath\app_jsx_diff.txt" | Select-Object -First 100

Write-Output "=== API.JS DIFF (first 100 lines) ==="
Get-Content "$GitPath\api_js_diff.txt" | Select-Object -First 100

Write-Output "=== AUTH.PY DIFF (first 100 lines) ==="
Get-Content "$GitPath\auth_py_diff.txt" | Select-Object -First 100

Write-Output "=== AUTH.SERVICE.PY DIFF (first 100 lines) ==="
Get-Content "$GitPath\auth_service_py_diff.txt" | Select-Object -First 100

Write-Output "=== DB.SERVICE.PY DIFF (first 100 lines) ==="
Get-Content "$GitPath\db_service_py_diff.txt" | Select-Object -First 100