# Batch file to run Drone Human Detection on Windows 11
@echo off
cls

echo ====================================
echo Drone Human Detection System
echo Windows 11 Edition
echo ====================================
echo.

REM Check Python installation
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8 or later from https://python.org
    pause
    exit /b 1
)

echo Python detected:
python --version

REM Check if virtual environment exists
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment
        pause
        exit /b 1
    )
)

echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Install requirements
echo Installing dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install main requirements
    pause
    exit /b 1
)

REM Install Windows-specific requirements
echo Installing Windows-specific dependencies...
pip install -r requirements-windows.txt
if errorlevel 1 (
    echo WARNING: Some Windows-specific packages failed to install
    echo The application may still work with reduced functionality
    echo.
)

REM Check for CUDA support
echo Checking for CUDA support...
python -c "import torch; print('CUDA available:', torch.cuda.is_available())" 2>nul
if errorlevel 1 (
    echo WARNING: PyTorch not installed or CUDA check failed
)

echo.
echo Setup complete! Starting application...
echo.
echo Press Ctrl+C to stop the application
echo Use 'c' key to switch cameras, 'q' or ESC to quit
echo Use 'f' key to toggle fullscreen
echo.

REM Run the application with Windows-optimized settings
python main.py --gui %*

echo.
echo Application finished. Press any key to exit...
pause >nul
