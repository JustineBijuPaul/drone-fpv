@echo off
REM Windows FPS Troubleshooting Script for Drone Human Detection
REM This script helps diagnose and fix low FPS issues on Windows 11

title Drone Detection - FPS Troubleshooting Tool

echo ================================================
echo Drone Human Detection - FPS Troubleshooting Tool
echo ================================================
echo.

echo This tool will help diagnose and fix low FPS issues.
echo Current issue: Your application is showing ~9.5 FPS
echo Target: 15+ FPS for smooth operation
echo.

echo Running system diagnostics...
echo.

REM Check Python and dependencies
echo [1/10] Checking Python installation...
python --version 2>nul
if errorlevel 1 (
    echo [✗] Python not found in PATH
    goto :python_issue
) else (
    echo [✓] Python installation OK
)

REM Check OpenCV with CUDA
echo [2/10] Checking OpenCV GPU acceleration...
python -c "import cv2; print('OpenCV version:', cv2.__version__); print('CUDA devices:', cv2.cuda.getCudaEnabledDeviceCount())" 2>nul
if errorlevel 1 (
    echo [!] OpenCV check failed - may impact performance
) else (
    echo [✓] OpenCV check completed
)

REM Check PyTorch CUDA
echo [3/10] Checking PyTorch CUDA support...
python -c "import torch; print('PyTorch CUDA available:', torch.cuda.is_available()); print('CUDA devices:', torch.cuda.device_count())" 2>nul
if errorlevel 1 (
    echo [!] PyTorch CUDA check failed
    echo [→] Recommendation: Install PyTorch with CUDA support
) else (
    echo [✓] PyTorch check completed
)

REM Check system resources
echo [4/10] Checking system resources...
python -c "import psutil; print('CPU cores:', psutil.cpu_count()); print('RAM:', round(psutil.virtual_memory().total/1024**3, 1), 'GB'); print('CPU usage:', psutil.cpu_percent(), '%%')" 2>nul

REM Check camera capabilities
echo [5/10] Checking camera capabilities...
python -c "
import cv2
cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
if cap.isOpened():
    print('Camera FPS capability:', cap.get(cv2.CAP_PROP_FPS))
    print('Camera resolution:', int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), 'x', int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)))
    cap.release()
else:
    print('Camera not accessible')
" 2>nul

REM Check graphics drivers
echo [6/10] Checking graphics drivers...
dxdiag /t "%TEMP%\dxdiag.txt" >nul 2>&1
timeout /t 3 >nul
if exist "%TEMP%\dxdiag.txt" (
    findstr /i "driver" "%TEMP%\dxdiag.txt" | findstr /i "date version" | head -3
    del "%TEMP%\dxdiag.txt"
    echo [✓] Graphics driver info retrieved
) else (
    echo [!] Could not retrieve graphics driver info
)

REM Check running processes that might interfere
echo [7/10] Checking for resource-intensive processes...
wmic process get name,percentprocessortime,privatepagecount /format:list | findstr /i "chrome firefox obs vlc" >nul 2>&1
if %errorlevel% == 0 (
    echo [!] Found resource-intensive applications running
    echo [→] Consider closing unnecessary applications
) else (
    echo [✓] No major resource conflicts detected
)

REM Check power settings
echo [8/10] Checking power settings...
powercfg /getactivescheme | findstr /i "high performance" >nul 2>&1
if %errorlevel% == 0 (
    echo [✓] High performance power plan active
) else (
    echo [!] Not using high performance power plan
    echo [→] Recommendation: Switch to high performance mode
)

REM Check Windows Game Mode
echo [9/10] Checking Windows Game Mode...
reg query "HKCU\SOFTWARE\Microsoft\GameBar" /v "AllowAutoGameMode" 2>nul | findstr "0x0" >nul 2>&1
if %errorlevel% == 0 (
    echo [✓] Windows Game Mode disabled (good for real-time processing)
) else (
    echo [!] Windows Game Mode may be interfering
    echo [→] Recommendation: Disable Game Mode
)

REM Check camera privacy settings
echo [10/10] Checking camera privacy settings...
echo [→] Manual check required: Settings ^> Privacy ^& Security ^> Camera

echo.
echo ================================================
echo DIAGNOSIS COMPLETE
echo ================================================
echo.

echo PERFORMANCE IMPROVEMENT RECOMMENDATIONS:
echo.

echo 1. IMMEDIATE FIXES (High Impact):
echo    • Reduce resolution: Use --resolution 320x240 or 640x480
echo    • Lower confidence threshold: Use --confidence 0.3
echo    • Enable frame dropping (already enabled by default)
echo.

echo 2. CAMERA OPTIMIZATIONS:
echo    • Use USB 3.0 port for camera connection
echo    • Enable MJPEG compression (automatic in Windows mode)
echo    • Set manual exposure for consistent FPS
echo.

echo 3. SYSTEM OPTIMIZATIONS:
echo    • Close Chrome, Firefox, OBS, or other heavy applications
echo    • Switch to High Performance power plan
echo    • Update graphics drivers
echo    • Add Windows Defender exclusion for project folder
echo.

echo 4. ADVANCED OPTIMIZATIONS:
echo    • Install CUDA-enabled PyTorch: pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
echo    • Use dedicated GPU for processing
echo    • Increase virtual memory (pagefile)
echo.

echo ================================================
echo QUICK FIX COMMANDS
echo ================================================
echo.

echo To test with optimized settings, try:
echo run_windows.bat --resolution 480x360 --confidence 0.4 --fps 20
echo.

set /p APPLY_FIXES="Would you like to apply automatic optimizations now? (Y/N): "
if /i "%APPLY_FIXES%"=="Y" (
    echo.
    echo Applying optimizations...
    
    REM Apply high performance power plan
    echo Setting high performance power plan...
    powercfg /setactive 8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c
    
    REM Set high priority for Python
    echo Setting high priority for Python processes...
    wmic process where name="python.exe" CALL setpriority "high priority" >nul 2>&1
    
    REM Disable Game Mode
    echo Disabling Windows Game Mode...
    reg add "HKCU\SOFTWARE\Microsoft\GameBar" /v "AllowAutoGameMode" /t REG_DWORD /d 0 /f >nul
    
    echo.
    echo [✓] Basic optimizations applied!
    echo.
    
    set /p TEST_NOW="Would you like to test the application with optimized settings? (Y/N): "
    if /i "%TEST_NOW%"=="Y" (
        echo.
        echo Starting application with performance optimizations...
        echo Press 'q' or ESC to quit, 'c' to switch cameras
        echo.
        call "%~dp0run_windows.bat" --gui --resolution 640x480 --confidence 0.4 --fps 25
    )
)

echo.
echo Troubleshooting complete!
echo For persistent issues, check the full Windows guide: WINDOWS_README.md
pause

:python_issue
echo.
echo PYTHON INSTALLATION ISSUE DETECTED
echo ===================================
echo Python is not installed or not in PATH.
echo.
echo Please install Python 3.8 or later:
echo 1. Visit https://python.org/downloads/
echo 2. Download Python 3.8+ 
echo 3. During installation, check "Add Python to PATH"
echo 4. Restart this troubleshooting tool
echo.
pause
exit /b 1
