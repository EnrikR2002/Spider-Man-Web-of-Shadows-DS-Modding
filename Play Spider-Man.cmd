@echo off
cd /d "%~dp0"
python tools\playtest.py launch
if errorlevel 1 pause
