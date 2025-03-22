@echo off
echo Installing Face Recognition System with GUI...

REM Check Python installation
python --version 2>nul
if %errorlevel% neq 0 (
    echo Error: Python is not installed or not in PATH
    echo Please install Python 3.10 from https://www.python.org/downloads/release/python-31011/
    pause
    exit /b 1
)

REM Create virtual environment if it doesn't exist
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
call .\venv\Scripts\activate.bat

REM Clean pip cache
echo Cleaning pip cache...
pip cache purge

REM Upgrade pip and install wheel
echo Upgrading pip and installing wheel...
python -m pip install --upgrade pip wheel setuptools

REM Install core dependencies in specific order
echo Installing core dependencies...
pip install numpy==1.23.5
pip install onnxruntime==1.15.1
pip install opencv-python==4.8.1.78

REM Install remaining dependencies
echo Installing remaining packages...
pip install -r requirements.txt

REM Verify installation
python -c "import numpy; import cv2; import onnxruntime; import insightface; import PyQt6; print('All packages installed successfully!')"
if %errorlevel% neq 0 (
    echo Error: Package installation verification failed
    pause
    exit /b 1
)

echo.
echo Installation completed successfully!
echo You can now run the application using run.bat
pause 