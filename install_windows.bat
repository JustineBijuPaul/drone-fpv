# Windows 11 Installation Script for Drone Human Detection System
@echo off
setlocal enabledelayedexpansion

cls
echo ================================================
echo Drone Human Detection System
echo Windows 11 Installer
echo ================================================
echo.

REM Check for administrator privileges
net session >nul 2>&1
if %errorLevel% == 0 (
    echo Running with administrator privileges...
    echo.
) else (
    echo WARNING: Not running as administrator
    echo Some features may not work properly
    echo Consider running as administrator for full functionality
    echo.
    timeout /t 3 >nul
)

REM Check Windows version
echo Checking Windows version...
for /f "tokens=4-5 delims=. " %%i in ('ver') do set VERSION=%%i.%%j
echo Windows version: %VERSION%

if "%VERSION%" geq "10.0" (
    echo Windows 10/11 detected - Compatible!
) else (
    echo WARNING: This system is designed for Windows 10/11
    echo Compatibility on older versions is not guaranteed
)
echo.

REM Check Python installation
echo Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo.
    echo Please install Python 3.8 or later:
    echo 1. Visit https://python.org/downloads/
    echo 2. Download Python 3.8 or later
    echo 3. During installation, check "Add Python to PATH"
    echo 4. Restart this installer after Python installation
    echo.
    pause
    exit /b 1
)

python --version
echo Python installation found!
echo.

REM Check pip
echo Checking pip...
python -m pip --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: pip is not available
    echo Please reinstall Python with pip included
    pause
    exit /b 1
)
echo pip is available
echo.

REM Create application directory
set APP_DIR=%LOCALAPPDATA%\DroneDetection
echo Creating application directory: %APP_DIR%
if not exist "%APP_DIR%" mkdir "%APP_DIR%"

REM Copy files to application directory
echo Copying application files...
xcopy /E /I /Y . "%APP_DIR%" >nul 2>&1

REM Change to app directory
cd /d "%APP_DIR%"

REM Create virtual environment
echo Creating virtual environment...
if exist "venv" (
    echo Removing existing virtual environment...
    rmdir /s /q venv
)

python -m venv venv
if errorlevel 1 (
    echo ERROR: Failed to create virtual environment
    echo Please check Python installation
    pause
    exit /b 1
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip

REM Install main requirements
echo Installing main requirements...
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install main requirements
    echo Check your internet connection and try again
    pause
    exit /b 1
)

REM Install Windows-specific requirements
echo Installing Windows-specific requirements...
pip install -r requirements-windows.txt
if errorlevel 1 (
    echo WARNING: Some Windows-specific packages failed to install
    echo The application will still work with reduced functionality
    timeout /t 3 >nul
)

REM Test installation
echo Testing installation...
python -c "import cv2, torch, numpy; print('Core dependencies OK')"
if errorlevel 1 (
    echo ERROR: Installation test failed
    echo Some dependencies may not be properly installed
    pause
    exit /b 1
)

REM Create desktop shortcut
echo Creating desktop shortcut...
set SHORTCUT_PATH=%USERPROFILE%\Desktop\Drone Detection.lnk
set TARGET_PATH=%APP_DIR%\run_windows.bat
set ICON_PATH=%APP_DIR%\icon.ico

REM Use PowerShell to create shortcut
powershell -Command "& {$WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%SHORTCUT_PATH%'); $Shortcut.TargetPath = '%TARGET_PATH%'; $Shortcut.WorkingDirectory = '%APP_DIR%'; $Shortcut.Description = 'Drone Human Detection System'; $Shortcut.Save()}" >nul 2>&1

if exist "%SHORTCUT_PATH%" (
    echo Desktop shortcut created successfully!
) else (
    echo WARNING: Could not create desktop shortcut
    echo You can run the application from: %APP_DIR%\run_windows.bat
)

REM Create start menu shortcut
echo Creating start menu shortcut...
set START_MENU_PATH=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Drone Detection.lnk
powershell -Command "& {$WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%START_MENU_PATH%'); $Shortcut.TargetPath = '%TARGET_PATH%'; $Shortcut.WorkingDirectory = '%APP_DIR%'; $Shortcut.Description = 'Drone Human Detection System'; $Shortcut.Save()}" >nul 2>&1

REM Check camera permissions
echo.
echo ================================================
echo IMPORTANT: Camera Permissions
echo ================================================
echo For the application to work properly, ensure:
echo 1. Camera access is enabled in Windows Settings
echo 2. Go to Settings ^> Privacy ^& Security ^> Camera
echo 3. Enable "Allow apps to access your camera"
echo 4. Enable "Allow desktop apps to access your camera"
echo.

REM Check Windows Defender
echo Windows Defender may flag the application
echo If needed, add an exclusion for: %APP_DIR%
echo.

REM Installation complete
echo ================================================
echo INSTALLATION COMPLETE!
echo ================================================
echo.
echo Application installed to: %APP_DIR%
echo.
echo To run the application:
echo - Use the desktop shortcut "Drone Detection"
echo - Or run: %APP_DIR%\run_windows.bat
echo.
echo First-time setup:
echo 1. Ensure your camera/drone receiver is connected
echo 2. Check camera permissions in Windows Settings
echo 3. Run the application and test camera detection
echo.
echo For help and documentation, see README.md
echo.

REM Offer to run now
set /p RUN_NOW="Would you like to run the application now? (y/n): "
if /i "!RUN_NOW!"=="y" (
    echo.
    echo Starting Drone Human Detection System...
    call "%TARGET_PATH%"
)

echo.
echo Thank you for installing Drone Human Detection System!
pause
