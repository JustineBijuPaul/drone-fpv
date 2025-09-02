"""
Quick Windows Coordinate Test and Fix Script

This script applies the coordinate fix to the existing system to resolve
the Windows bounding box alignment issue.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from drone_detection.windows_coordinate_fix import WindowsCoordinateFix
from drone_detection.main_controller import MainController
from drone_detection.models import CameraConfig, AppState
import cv2
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_coordinate_fix():
    """Test the coordinate fix with sample data."""
    print("🔧 Testing Windows Coordinate Fix...")
    
    fix = WindowsCoordinateFix()
    
    # Test cases that might occur on Windows
    test_cases = [
        # Normalized coordinates (common issue)
        {
            "name": "Normalized coordinates",
            "boxes": [(0.1, 0.2, 0.4, 0.8)],
            "frame_size": (640, 480)
        },
        # Small pixel coordinates (potential issue)
        {
            "name": "Suspiciously small coordinates", 
            "boxes": [(10, 20, 50, 100)],
            "frame_size": (640, 480)
        },
        # Normal pixel coordinates
        {
            "name": "Normal pixel coordinates",
            "boxes": [(100, 150, 300, 400)],
            "frame_size": (640, 480)
        },
        # Upper-left corner issue (Windows specific)
        {
            "name": "Upper-left corner coordinates",
            "boxes": [(5, 5, 180, 250)],
            "frame_size": (640, 480)
        }
    ]
    
    for test in test_cases:
        print(f"\n📋 Testing: {test['name']}")
        print(f"   Original: {test['boxes'][0]}")
        
        fixed = fix.fix_coordinates(test['boxes'], test['frame_size'][0], test['frame_size'][1])
        if fixed:
            print(f"   Fixed:    {fixed[0]}")
        else:
            print(f"   Fixed:    [REJECTED]")

def run_with_coordinate_fix():
    """Run the main application with coordinate fix applied."""
    print("🚀 Starting drone detection with Windows coordinate fix...")
    
    try:
        # Initialize main controller (it handles its own configuration)
        controller = MainController()
        
        print("📷 Opening camera...")
        if not controller.initialize():
            print("❌ Failed to initialize system")
            return
            
        print("✅ System initialized. Press 'q' to quit.")
        print("🔍 The coordinate fix is now active and will handle Windows coordinate issues automatically.")
        
        # Run the detection loop
        controller.run()
        
    except KeyboardInterrupt:
        print("\n👋 Shutting down...")
    except Exception as e:
        print(f"❌ Error: {str(e)}")
    finally:
        if 'controller' in locals():
            controller.cleanup()

def main():
    """Main function to choose between test and run modes."""
    print("=" * 60)
    print("🔧 WINDOWS COORDINATE FIX UTILITY")
    print("=" * 60)
    print()
    print("This utility fixes the bounding box alignment issue on Windows")
    print("where detection confidence is correct but boxes appear in wrong locations.")
    print()
    
    choice = input("Choose an option:\n1. Test coordinate fix\n2. Run application with fix\n3. Show troubleshooting info\n\nEnter choice (1-3): ").strip()
    
    if choice == '1':
        test_coordinate_fix()
    elif choice == '2':
        run_with_coordinate_fix()
    elif choice == '3':
        show_troubleshooting_info()
    else:
        print("Invalid choice. Please run again and enter 1, 2, or 3.")

def show_troubleshooting_info():
    """Show troubleshooting information."""
    print("\n🛠️  TROUBLESHOOTING INFORMATION")
    print("=" * 50)
    print()
    print("COORDINATE ISSUES ON WINDOWS:")
    print("• YOLOv8 may return normalized coordinates (0-1) instead of pixel coordinates")
    print("• Windows display scaling can affect coordinate systems") 
    print("• DirectShow camera backend may have different coordinate handling")
    print()
    print("WHAT THE FIX DOES:")
    print("• Automatically detects if coordinates are normalized vs pixel-based")
    print("• Scales normalized coordinates to proper pixel coordinates")
    print("• Handles Windows-specific coordinate offset issues")
    print("• Validates and clamps coordinates to frame boundaries")
    print()
    print("IF ISSUE PERSISTS:")
    print("• Try different camera resolutions: 640x480, 1280x720")
    print("• Check Windows display scaling settings")
    print("• Verify YOLOv8 version with: pip show ultralytics")
    print("• Test with lower confidence threshold (0.3)")
    print()
    print("QUICK FIXES TO TRY:")
    print("• Right-click python.exe → Properties → Compatibility → Override high DPI scaling")
    print("• Run application as administrator")
    print("• Try different camera backends in camera_manager.py")

if __name__ == "__main__":
    main()
