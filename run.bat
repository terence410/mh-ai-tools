@echo off
echo Starting Face Recognition System...

REM Check for uncommitted changes and pull if clean
git diff --quiet
if %ERRORLEVEL% EQU 0 (
    echo Pulling latest changes...
    git pull
) else (
    echo Warning: You have uncommitted changes. Skipping git pull.
    echo Please commit or stash your changes before running git pull.
)

REM Check if virtual environment exists
if not exist "venv" (
    echo Error: Virtual environment not found
    echo Please run installation.bat first
    pause
    exit /b 1
)

REM Activate virtual environment
call .\venv\Scripts\activate.bat

REM Run the application
python src/main.py

REM Deactivate virtual environment
deactivate

echo.
echo Application closed.
pause 
