@echo off
REM Windows Debug Script for Drone Human Detection Bounding Box Issues
REM This script runs the debug version to help identify coordinate problems

title Drone Detection - Debug Mode (Bounding Box Fix)

echo ================================================
echo Drone Human Detection - DEBUG MODE
echo Bounding Box Coordinate Troubleshooting
echo ================================================
echo.

echo This debug version will help identify why bounding boxes
echo are not properly outlining detected humans.
echo.

REM Check Python installation
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    pause
    exit /b 1
)

echo Python detected:
python --version
echo.

REM Activate virtual environment if it exists
if exist "venv" (
    echo Activating virtual environment...
    call venv\Scripts\activate.bat
) else (
    echo No virtual environment found - using system Python
)

echo.
echo DEBUG SESSION STARTING...
echo ================================================
echo.

echo Debug Features Enabled:
echo [✓] Detailed coordinate logging
echo [✓] Frame dimension validation  
echo [✓] Bounding box size checking
echo [✓] Enhanced error reporting
echo [✓] Debug log file creation

echo.
echo The debug session will:
echo 1. Show detailed coordinate information in console
echo 2. Save debug log to 'drone_detection_debug.log'
echo 3. Validate bounding box coordinates
echo 4. Test coordinate scaling and transformation
echo.

echo Controls during debug:
echo - Press 'q' or ESC to quit
echo - Press 'c' to switch cameras  
echo - Press 'd' to dump current detection info
echo - Press 'f' for fullscreen
echo.

set /p START_DEBUG="Ready to start debug session? (Y/N): "
if /i "%START_DEBUG%" NEQ "Y" (
    echo Debug session cancelled.
    pause
    exit /b 0
)

echo.
echo Starting debug mode...
echo Watch the console for coordinate information!
echo.

REM Run the debug version with optimal settings for coordinate debugging
python debug_main.py --camera-source laptop --resolution 640x480 --confidence 0.3 --fps 15 --gui

echo.
echo ================================================
echo DEBUG SESSION COMPLETED
echo ================================================
echo.

echo Debug information has been saved to:
echo - Console output (above)
echo - drone_detection_debug.log (detailed log file)
echo.

echo Analysis:
echo 1. Check the console output for coordinate values
echo 2. Look for patterns in bounding box coordinates
echo 3. Verify frame dimensions match camera resolution
echo 4. Check if coordinates are being properly scaled
echo.

if exist "drone_detection_debug.log" (
    echo Opening debug log file...
    timeout /t 2 >nul
    notepad drone_detection_debug.log 2>nul
    if errorlevel 1 (
        echo Could not open notepad. Debug log location:
        echo %CD%\drone_detection_debug.log
    )
) else (
    echo Debug log file was not created.
    echo This may indicate an issue with file permissions.
)

echo.
echo TROUBLESHOOTING RECOMMENDATIONS:
echo.

echo If bounding boxes are still misaligned:
echo.
echo 1. COORDINATE SCALING ISSUE:
echo    - Check if YOLOv8 model is resizing input images
echo    - Verify coordinate scaling back to original size
echo.
echo 2. FRAME DIMENSION MISMATCH:  
echo    - Ensure camera resolution matches display resolution
echo    - Check for any image preprocessing that changes size
echo.
echo 3. WINDOWS-SPECIFIC ISSUE:
echo    - Test with different camera backends (DirectShow, etc.)
echo    - Check for DPI scaling issues on high-DPI displays
echo.
echo 4. YOLO MODEL ISSUE:
echo    - Try different YOLOv8 model version (yolov8s.pt, yolov8m.pt)
echo    - Verify model is properly loaded and not corrupted
echo.

set /p VIEW_LOG="Would you like to view the debug log now? (Y/N): "
if /i "%VIEW_LOG%"=="Y" (
    if exist "drone_detection_debug.log" (
        echo.
        echo === DEBUG LOG CONTENTS ===
        type "drone_detection_debug.log"
        echo.
        echo === END DEBUG LOG ===
    )
)

echo.
echo For additional help:
echo 1. Share the debug log contents with support
echo 2. Run troubleshoot_fps_windows.bat for performance issues  
echo 3. Check WINDOWS_README.md for Windows-specific troubleshooting
echo.

pause
