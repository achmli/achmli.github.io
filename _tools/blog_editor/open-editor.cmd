@echo off
setlocal
if exist "%ProgramData%\miniconda3\pythonw.exe" (
    start "" "%ProgramData%\miniconda3\pythonw.exe" -B "%~dp0editor.py"
    exit /b
)
where pythonw.exe >nul 2>&1
if errorlevel 1 (
    python.exe -B "%~dp0editor.py"
    if errorlevel 1 pause
) else (
    start "" pythonw.exe -B "%~dp0editor.py"
)
