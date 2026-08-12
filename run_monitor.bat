@echo off
cd /d "%~dp0"
py .\examples\run_monitor.py
if errorlevel 1 pause
