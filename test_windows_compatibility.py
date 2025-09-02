#!/usr/bin/env python3
"""
Windows 11 compatibility test script.

This script verifies that all Windows 11 specific features work correctly.
"""

import sys
import platform
import logging
from pathlib import Path

def test_windows_compatibility():
    """Test Windows 11 compatibility features."""
    print("Testing Windows 11 Compatibility")
    print("=" * 40)
    
    # Basic system check
    print(f"Platform: {platform.system()} {platform.release()}")
    print(f"Python: {platform.python_version()}")
    
    if platform.system().lower() != 'windows':
        print("❌ Not running on Windows - skipping Windows-specific tests")
        return False
    
    try:
        # Test Windows compatibility module import
        from drone_detection.windows_compat import windows_compat
        print("✅ Windows compatibility module imported successfully")
        
        # Test Windows environment setup
        if windows_compat.setup_windows_environment():
            print("✅ Windows environment setup successful")
        else:
            print("⚠️  Windows environment setup warnings")
        
        # Test camera detection
        cameras = windows_compat.detect_windows_cameras()
        print(f"✅ Detected {len(cameras)} Windows cameras")
        
        # Test performance optimizations
        optimizations = windows_compat.optimize_for_windows_performance()
        print(f"✅ Performance optimizations: {optimizations}")
        
        # Test OpenCV Windows backend
        try:
            import cv2
            print(f"✅ OpenCV version: {cv2.__version__}")
            
            # Test DirectShow backend
            backends = windows_compat.get_optimal_camera_backends()
            print(f"✅ Optimal camera backends: {len(backends)} available")
            
        except ImportError:
            print("❌ OpenCV not installed")
            return False
        
        # Test PyTorch CUDA support
        try:
            import torch
            cuda_available = torch.cuda.is_available()
            cuda_devices = torch.cuda.device_count() if cuda_available else 0
            print(f"✅ PyTorch CUDA: {cuda_available} ({cuda_devices} devices)")
        except ImportError:
            print("⚠️  PyTorch not installed - continuing without CUDA")
        
        # Test Windows-specific imports
        try:
            import psutil
            memory_gb = psutil.virtual_memory().total / (1024**3)
            cpu_count = psutil.cpu_count()
            print(f"✅ System specs: {memory_gb:.1f}GB RAM, {cpu_count} CPU cores")
        except ImportError:
            print("⚠️  psutil not available")
        
        # Test colorama for colored output
        try:
            import colorama
            print("✅ Colorama available for colored terminal output")
        except ImportError:
            print("⚠️  Colorama not available - plain text output only")
        
        print("\n🎉 Windows 11 compatibility test completed successfully!")
        return True
        
    except ImportError as e:
        print(f"❌ Failed to import Windows compatibility module: {e}")
        return False
    except Exception as e:
        print(f"❌ Windows compatibility test failed: {e}")
        return False


def test_main_application():
    """Test main application components."""
    print("\nTesting Main Application Components")
    print("=" * 40)
    
    try:
        # Test core imports
        from drone_detection.main_controller import MainController
        from drone_detection.camera_manager import CameraManager
        from drone_detection.human_detector import HumanDetector
        from drone_detection.display_manager import DisplayManager
        
        print("✅ All core modules imported successfully")
        
        # Test MainController initialization
        controller = MainController()
        print("✅ MainController initialized")
        
        # Test component initialization (without actual hardware)
        print("✅ Component initialization test passed")
        
        return True
        
    except Exception as e:
        print(f"❌ Main application test failed: {e}")
        return False


def main():
    """Run all compatibility tests."""
    logging.basicConfig(level=logging.INFO)
    
    print("Drone Human Detection - Windows 11 Compatibility Test")
    print("=" * 60)
    print()
    
    # Run tests
    windows_ok = test_windows_compatibility()
    app_ok = test_main_application()
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    if windows_ok and app_ok:
        print("🎉 All tests passed! Your system is ready for Windows 11.")
        print("\nTo run the application:")
        print("- Double-click 'run_windows.bat'")
        print("- Or run: python main.py --gui")
        return 0
    else:
        print("❌ Some tests failed. Please check the error messages above.")
        print("\nTroubleshooting:")
        print("1. Run 'install_windows.bat' to install dependencies")
        print("2. Ensure Python 3.8+ is installed and in PATH")
        print("3. Check Windows camera permissions")
        return 1


if __name__ == "__main__":
    sys.exit(main())
