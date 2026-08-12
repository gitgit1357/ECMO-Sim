@echo off
setlocal
cd /d "%~dp0"
python examples\run_ecmo_workspace.py
if errorlevel 1 pause
endlocal
