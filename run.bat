@echo off
echo Starting Face Recognition System...

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
