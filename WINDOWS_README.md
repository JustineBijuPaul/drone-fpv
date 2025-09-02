# Windows 11 Setup and Usage Guide

This guide provides specific instructions for running the Drone Human Detection System on Windows 11.

## Quick Start (Windows 11)

### Option 1: Automatic Installation (Recommended)
1. Download or clone this repository
2. Run `install_windows.bat` as Administrator
3. Follow the installation prompts
4. Use the desktop shortcut to start the application

### Option 2: Manual Installation
1. Install Python 3.8+ from [python.org](https://python.org/downloads/)
   - ⚠️ **Important**: Check "Add Python to PATH" during installation
2. Open Command Prompt or PowerShell
3. Navigate to the project directory
4. Run: `run_windows.bat`

### Option 3: PowerShell Script
1. Open PowerShell as Administrator
2. Run: `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`
3. Navigate to project directory
4. Run: `.\run_windows.ps1`

## Windows 11 Specific Features

### Enhanced Camera Support
- **DirectShow Backend**: Optimized camera detection for Windows webcams
- **Multiple Camera Detection**: Automatically detects up to 10 camera devices
- **Hardware Acceleration**: Utilizes Windows hardware acceleration when available
- **MJPEG Support**: Better compression for improved performance

### Performance Optimizations
- **High Priority Process**: Automatically sets high priority for better real-time performance
- **Memory Management**: Optimized for Windows memory management
- **Multi-threading**: Takes advantage of Windows threading capabilities
- **CUDA Support**: Automatic GPU acceleration detection

### Windows-Specific Controls
- **Fullscreen Toggle**: Press `F` key for fullscreen mode
- **Window Management**: Native Windows window controls
- **System Tray Integration**: Minimizes to system tray (if supported)

## System Requirements

### Minimum Requirements
- Windows 10 version 1903 or Windows 11
- Python 3.8 or later
- 4GB RAM
- DirectX 11 compatible graphics
- USB camera or network camera access

### Recommended Requirements
- Windows 11 (latest version)
- Python 3.9 or later
- 8GB RAM or more
- Dedicated GPU with CUDA support
- High-speed USB 3.0 ports for cameras

## Camera Setup (Windows 11)

### Built-in Camera
1. Ensure camera privacy settings allow access:
   - Go to Settings > Privacy & Security > Camera
   - Enable "Allow apps to access your camera"
   - Enable "Allow desktop apps to access your camera"

### External USB Camera
1. Connect USB camera
2. Install camera drivers if required
3. Test camera in Windows Camera app
4. Run the detection application

### Drone Receiver Setup
1. Connect drone receiver via USB
2. Install any required drivers
3. Configure network settings if using WiFi receiver:
   - Default IP: 192.168.1.100
   - Ports: 8080 (HTTP), 554 (RTSP)

## Windows Firewall Configuration

For drone receiver network connections, you may need to configure Windows Firewall:

```batch
# Run as Administrator
netsh advfirewall firewall add rule name="Drone Camera HTTP" dir=in action=allow protocol=TCP localport=8080
netsh advfirewall firewall add rule name="Drone Camera RTSP" dir=in action=allow protocol=TCP localport=554
```

## Troubleshooting Windows Issues

### Camera Not Detected
1. **Check Camera Privacy Settings**:
   - Settings > Privacy & Security > Camera
   - Ensure camera access is enabled

2. **Update Camera Drivers**:
   - Device Manager > Cameras
   - Right-click camera > Update driver

3. **Check Camera in Device Manager**:
   - Look for yellow warning icons
   - Reinstall problematic devices

4. **Test with Windows Camera App**:
   - Verify camera works outside our application

### Application Won't Start
1. **Check Python Installation**:
   ```cmd
   python --version
   pip --version
   ```

2. **Reinstall Dependencies**:
   ```cmd
   pip uninstall -r requirements.txt -y
   pip install -r requirements.txt
   pip install -r requirements-windows.txt
   ```

3. **Run as Administrator**:
   - Right-click on run_windows.bat
   - Select "Run as administrator"

### Performance Issues
1. **Enable GPU Acceleration**:
   - Install CUDA toolkit if you have NVIDIA GPU
   - Verify with: `python -c "import torch; print(torch.cuda.is_available())"`

2. **Adjust Process Priority**:
   - Task Manager > Details
   - Find python.exe > Set priority > High

3. **Close Background Applications**:
   - Disable unnecessary startup programs
   - Close resource-heavy applications

### Display Issues
1. **Multiple Monitors**:
   - Application may open on secondary monitor
   - Use Windows + Shift + Arrow to move windows

2. **High DPI Scaling**:
   - Right-click python.exe > Properties > Compatibility
   - Check "Override high DPI scaling behavior"

3. **Graphics Driver Issues**:
   - Update graphics drivers from manufacturer
   - NVIDIA: GeForce Experience
   - AMD: AMD Software
   - Intel: Intel Graphics Command Center

## Windows Security Considerations

### Windows Defender
Windows Defender may flag the application as potentially unwanted:
1. Add folder exclusion for installation directory
2. Allow application in real-time protection settings

### User Account Control (UAC)
For full functionality, consider:
1. Running as Administrator for first setup
2. Creating scheduled task for regular use

## Performance Monitoring

### Windows Task Manager
Monitor application performance:
- CPU usage should be moderate (20-40%)
- Memory usage depends on camera resolution
- GPU usage indicates hardware acceleration

### Windows Performance Toolkit (Advanced)
For detailed analysis:
1. Install Windows Performance Toolkit
2. Use Windows Performance Recorder
3. Analyze with Windows Performance Analyzer

## Command Line Options (Windows)

```cmd
# Basic usage
python main.py

# With GUI (recommended for Windows)
python main.py --gui

# Specify camera
python main.py --camera-source laptop --device-id 0

# High resolution
python main.py --resolution 1280x720 --fps 30

# Network drone camera
python main.py --camera-source drone
```

## Batch File Options

The `run_windows.bat` file accepts the same parameters:
```cmd
run_windows.bat --gui --resolution 1280x720
```

## Registry Settings (Advanced)

For persistent camera settings, you may need to modify registry:
- Location: `HKEY_CURRENT_USER\SOFTWARE\Microsoft\Windows\CurrentVersion\CapabilityAccessManager\ConsentStore\webcam`
- Ensure `Value` is set to `Allow`

## Windows Updates

Keep Windows 11 updated for:
- Latest camera drivers
- Security patches
- Performance improvements
- Hardware acceleration support

## Getting Help

1. **Check Windows Event Viewer**:
   - Look for application errors
   - Check System and Application logs

2. **Run Windows Troubleshooter**:
   - Settings > Update & Security > Troubleshoot
   - Run Camera troubleshooter

3. **Community Support**:
   - Include Windows version in bug reports
   - Provide system specifications
   - Include error messages from Command Prompt

## File Locations (Windows 11)

- **Application**: `%LOCALAPPDATA%\DroneDetection\`
- **Logs**: `%TEMP%\drone_detection_logs\`
- **Preview Images**: `%TEMP%\drone_preview.jpg`
- **Configuration**: `%APPDATA%\DroneDetection\config.json`

## Uninstallation

To completely remove the application:
1. Delete installation folder: `%LOCALAPPDATA%\DroneDetection\`
2. Remove desktop shortcut
3. Remove start menu entry
4. Clear temporary files in `%TEMP%`
