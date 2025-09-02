# Batch file to run Drone Human Detection on Windows 11
@echo off
cls

echo ====================================
echo Drone Human Detection System
echo Windows 11 Edition - Enhanced
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
echo ================================================
echo PERFORMANCE OPTIMIZATION OPTIONS
echo ================================================
echo.

echo Current system detected FPS: ~9.5 FPS
echo Target FPS: 15+ FPS for smooth operation
echo.

echo Choose performance preset:
echo [1] High Performance (640x480, 30 FPS) - Best quality
echo [2] Balanced (480x360, 25 FPS) - Good balance 
echo [3] Performance (320x240, 20 FPS) - Best FPS
echo [4] Custom settings
echo [5] Default settings

set /p PRESET="Enter your choice (1-5): "

if "%PRESET%"=="1" (
    set RESOLUTION=640x480
    set FPS=30
    set CONFIDENCE=0.5
    echo Selected: High Performance preset
) else if "%PRESET%"=="2" (
    set RESOLUTION=480x360
    set FPS=25
    set CONFIDENCE=0.4
    echo Selected: Balanced preset
) else if "%PRESET%"=="3" (
    set RESOLUTION=320x240
    set FPS=20
    set CONFIDENCE=0.4
    echo Selected: Performance preset
) else if "%PRESET%"=="4" (
    echo Custom Settings:
    set /p RESOLUTION="Enter resolution (e.g., 640x480): "
    set /p FPS="Enter target FPS (e.g., 25): "
    set /p CONFIDENCE="Enter confidence threshold (e.g., 0.4): "
) else (
    set RESOLUTION=640x480
    set FPS=30
    set CONFIDENCE=0.5
    echo Selected: Default settings
)

echo.
echo Settings:
echo - Resolution: %RESOLUTION%
echo - Target FPS: %FPS%
echo - Confidence: %CONFIDENCE%
echo.

echo Setup complete! Starting application...
echo.
echo CONTROLS:
echo - Press Ctrl+C to stop the application
echo - Use 'c' key to switch cameras
echo - Use 'q' or ESC to quit
echo - Use 'f' key to toggle fullscreen
echo.

echo PERFORMANCE TIPS:
echo - If FPS is still low, try the troubleshoot_fps_windows.bat script
echo - Close other applications for better performance
echo - Ensure camera is connected to USB 3.0 port
echo.

REM Run the application with Windows-optimized settings
python main.py --gui --resolution %RESOLUTION% --fps %FPS% --confidence %CONFIDENCE% %*

echo.
echo Application finished.

REM Performance feedback
echo.
echo ================================================
echo PERFORMANCE FEEDBACK
echo ================================================
echo.

set /p SATISFIED="Were you satisfied with the FPS performance? (Y/N): "
if /i "%SATISFIED%"=="N" (
    echo.
    echo For FPS troubleshooting, run: troubleshoot_fps_windows.bat
    echo Or try the Performance preset next time.
    echo.
    echo Quick fix suggestions:
    echo 1. Try lower resolution: 320x240
    echo 2. Close background applications
    echo 3. Run optimize_windows_performance.bat
)

echo.
echo Press any key to exit...
pause >nul
