@echo off
echo Calling force reset...
powershell -Command "Invoke-RestMethod -Uri 'http://localhost:8000/documents/force-reset' -Method Post"

echo.
echo Checking status...
powershell -Command "Invoke-RestMethod -Uri 'http://localhost:8000/documents/status' -Method Get"

pause