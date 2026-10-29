@echo off
cd /d "%~dp0"
python maze_escape.py
if errorlevel 1 pause
