$path = "C:\Users\abhishek\Downloads\ai-based soc"
Set-Location $path
git show HEAD:backend/app/main.py > head_main.py
Write-Output "Restored HEAD main.py, lines: $(Get-Content head_main.py | Measure-Object -Line).Lines"