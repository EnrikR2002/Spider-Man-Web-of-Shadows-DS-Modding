@echo off
cd /d "%~dp0"
python tools\playtest.py launch --preset renderer-preview
if errorlevel 1 pause
