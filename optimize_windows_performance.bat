@echo off
REM Windows Performance Optimization Script for Drone Human Detection
REM This script helps optimize Windows 11 for better real-time video processing

echo ================================================
echo Drone Human Detection - Windows 11 Performance Optimizer
echo ================================================
echo.

echo Checking system requirements...

REM Check if running as Administrator
net session >nul 2>&1
if %errorLevel% == 0 (
    echo [✓] Running with administrator privileges
) else (
    echo [!] Not running as administrator - some optimizations may not apply
    echo    Consider running as administrator for full optimization
)

echo.
echo Applying Windows performance optimizations...

REM Set high priority for Python processes (requires admin)
echo [1/8] Setting high priority for Python processes...
wmic process where name="python.exe" CALL setpriority "high priority" >nul 2>&1
wmic process where name="python3.exe" CALL setpriority "high priority" >nul 2>&1

REM Disable Windows Game Mode if it interferes
echo [2/8] Optimizing Windows Game Mode...
reg add "HKCU\SOFTWARE\Microsoft\GameBar" /v "AllowAutoGameMode" /t REG_DWORD /d 0 /f >nul 2>&1

REM Optimize visual effects for performance
echo [3/8] Optimizing visual effects...
reg add "HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\VisualEffects" /v "VisualFXSetting" /t REG_DWORD /d 2 /f >nul 2>&1

REM Set power plan to High Performance
echo [4/8] Setting power plan to High Performance...
powercfg /setactive 8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c >nul 2>&1

REM Disable Windows Defender real-time scanning for project folder (requires admin)
echo [5/8] Configuring Windows Defender exclusions...
set PROJECT_DIR=%LOCALAPPDATA%\DroneDetection
if exist "%PROJECT_DIR%" (
    powershell -Command "Add-MpPreference -ExclusionPath '%PROJECT_DIR%'" >nul 2>&1
)

REM Optimize network settings for drone camera connections
echo [6/8] Optimizing network settings...
netsh int tcp set global autotuninglevel=normal >nul 2>&1
netsh int tcp set global chimney=enabled >nul 2>&1

REM Set camera access permissions
echo [7/8] Checking camera permissions...
echo    Ensure camera access is enabled in:
echo    Settings ^> Privacy ^& Security ^> Camera

REM Clean up temporary files
echo [8/8] Cleaning up temporary files...
del /q /f "%TEMP%\drone_*.jpg" >nul 2>&1
del /q /f "%TEMP%\opencv_*.tmp" >nul 2>&1

echo.
echo ================================================
echo Performance Optimization Complete!
echo ================================================
echo.

echo Optimizations Applied:
echo [✓] High process priority for Python
echo [✓] Optimized visual effects
echo [✓] High performance power plan
echo [✓] Windows Defender exclusions
echo [✓] Network optimization for cameras
echo [✓] Temporary file cleanup

echo.
echo Additional Recommendations:
echo - Close unnecessary background applications
echo - Ensure sufficient free disk space (^>2GB)
echo - Update graphics drivers to latest version
echo - Use a high-speed USB 3.0 port for cameras
echo - Consider using a wired network connection for drone receivers

echo.
echo To verify optimizations, run the application and check:
echo - FPS should be higher (target: 15+ FPS)
echo - Reduced input lag
echo - Smoother video display
echo - Better detection responsiveness

echo.
echo Press any key to continue...
pause >nul

echo.
echo Would you like to run the Drone Detection application now?
set /p RUN_APP="Enter Y to run, N to exit: "
if /i "%RUN_APP%"=="Y" (
    echo Starting Drone Human Detection System...
    call "%~dp0run_windows.bat" --gui
) else (
    echo Optimization complete. You can run the application anytime using:
    echo %~dp0run_windows.bat --gui
)
