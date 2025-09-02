# PowerShell script to run Drone Human Detection on Windows 11
# Run this script in PowerShell: .\run_windows.ps1

Write-Host "====================================" -ForegroundColor Cyan
Write-Host "Drone Human Detection System" -ForegroundColor Cyan
Write-Host "Windows 11 Edition" -ForegroundColor Cyan
Write-Host "====================================" -ForegroundColor Cyan
Write-Host ""

# Check Python installation
try {
    $pythonVersion = python --version 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "Python not found"
    }
    Write-Host "Python detected: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "ERROR: Python is not installed or not in PATH" -ForegroundColor Red
    Write-Host "Please install Python 3.8 or later from https://python.org" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

# Check execution policy
$executionPolicy = Get-ExecutionPolicy
if ($executionPolicy -eq "Restricted") {
    Write-Host "WARNING: PowerShell execution policy is restricted." -ForegroundColor Yellow
    Write-Host "You may need to run: Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser" -ForegroundColor Yellow
}

# Check if virtual environment exists
if (-not (Test-Path "venv")) {
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    python -m venv venv
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Failed to create virtual environment" -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit 1
    }
}

Write-Host "Activating virtual environment..." -ForegroundColor Yellow
& "venv\Scripts\Activate.ps1"

# Install requirements
Write-Host "Installing dependencies..." -ForegroundColor Yellow
pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Failed to install main requirements" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Install Windows-specific requirements
Write-Host "Installing Windows-specific dependencies..." -ForegroundColor Yellow
pip install -r requirements-windows.txt
if ($LASTEXITCODE -ne 0) {
    Write-Host "WARNING: Some Windows-specific packages failed to install" -ForegroundColor Yellow
    Write-Host "The application may still work with reduced functionality" -ForegroundColor Yellow
}

# Check for CUDA support
Write-Host "Checking for CUDA support..." -ForegroundColor Yellow
try {
    $cudaCheck = python -c "import torch; print('CUDA available:', torch.cuda.is_available())" 2>&1
    Write-Host $cudaCheck -ForegroundColor Green
} catch {
    Write-Host "WARNING: PyTorch not installed or CUDA check failed" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Setup complete! Starting application..." -ForegroundColor Green
Write-Host ""
Write-Host "Controls:" -ForegroundColor Cyan
Write-Host "  - Press Ctrl+C to stop the application" -ForegroundColor White
Write-Host "  - Use 'c' key to switch cameras" -ForegroundColor White
Write-Host "  - Use 'q' or ESC to quit" -ForegroundColor White
Write-Host "  - Use 'f' key to toggle fullscreen" -ForegroundColor White
Write-Host ""

# Parse command line arguments
$args_string = $args -join " "

# Run the application with Windows-optimized settings
python main.py --gui $args_string

Write-Host ""
Write-Host "Application finished." -ForegroundColor Green
Read-Host "Press Enter to exit"
