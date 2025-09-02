#!/usr/bin/env python3
"""Windows Camera Diagnostic and Fix Tool"""

import cv2
import platform
import time

def test_camera_access():
    """Test different ways to access camera on Windows."""
    print("🔧 WINDOWS CAMERA DIAGNOSTIC")
    print("=" * 50)
    print(f"Platform: {platform.system()}")
    print()
    
    # Test different camera indices
    print("1️⃣ Testing Camera Indices:")
    working_cameras = []
    
    for i in range(5):  # Test cameras 0-4
        print(f"   Testing camera {i}...", end=" ")
        try:
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                ret, frame = cap.read()
                if ret and frame is not None:
                    height, width = frame.shape[:2]
                    print(f"✅ Working - {width}x{height}")
                    working_cameras.append(i)
                else:
                    print("❌ Can't read frames")
            else:
                print("❌ Can't open")
            cap.release()
            time.sleep(0.5)  # Small delay between tests
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print()
    print("2️⃣ Testing DirectShow Backend:")
    for i in working_cameras[:2]:  # Test first 2 working cameras
        print(f"   Testing camera {i} with DirectShow...", end=" ")
        try:
            cap = cv2.VideoCapture(i, cv2.CAP_DSHOW)
            if cap.isOpened():
                ret, frame = cap.read()
                if ret and frame is not None:
                    height, width = frame.shape[:2]
                    print(f"✅ Working - {width}x{height}")
                else:
                    print("❌ Can't read frames")
            else:
                print("❌ Can't open")
            cap.release()
            time.sleep(0.5)
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print()
    print("3️⃣ Testing Different Resolutions:")
    if working_cameras:
        test_camera = working_cameras[0]
        resolutions = [(640, 480), (320, 240), (1280, 720)]
        
        for width, height in resolutions:
            print(f"   Testing {width}x{height}...", end=" ")
            try:
                cap = cv2.VideoCapture(test_camera, cv2.CAP_DSHOW)
                cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
                cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
                
                if cap.isOpened():
                    ret, frame = cap.read()
                    if ret and frame is not None:
                        actual_height, actual_width = frame.shape[:2]
                        print(f"✅ Got {actual_width}x{actual_height}")
                    else:
                        print("❌ Can't read frames")
                else:
                    print("❌ Can't open")
                cap.release()
                time.sleep(0.5)
            except Exception as e:
                print(f"❌ Error: {e}")
    
    print()
    print("4️⃣ Testing MSMF Backend:")
    if working_cameras:
        test_camera = working_cameras[0]
        print(f"   Testing camera {test_camera} with MSMF...", end=" ")
        try:
            cap = cv2.VideoCapture(test_camera, cv2.CAP_MSMF)
            if cap.isOpened():
                ret, frame = cap.read()
                if ret and frame is not None:
                    height, width = frame.shape[:2]
                    print(f"✅ Working - {width}x{height}")
                else:
                    print("❌ Can't read frames")
            else:
                print("❌ Can't open")
            cap.release()
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print()
    print("📊 RESULTS:")
    if working_cameras:
        print(f"✅ Working cameras found: {working_cameras}")
        print(f"🎯 Recommended camera: {working_cameras[0]}")
        print(f"🔧 Try: python main.py --device-id {working_cameras[0]} --gui")
    else:
        print("❌ No working cameras found")
        print("🔧 Suggestions:")
        print("   - Check Windows Camera privacy settings")
        print("   - Close other applications using the camera")
        print("   - Try running as administrator")
    
    return working_cameras

def create_windows_camera_fix():
    """Create a script that uses the best camera settings for Windows."""
    working_cameras = test_camera_access()
    
    if not working_cameras:
        print("\n❌ Cannot create fix - no working cameras found")
        return
    
    best_camera = working_cameras[0]
    
    fix_script = f'''#!/usr/bin/env python3
"""Run drone detection with Windows-optimized camera settings."""

import sys
import os
import logging

# Add project directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from drone_detection.main_controller import MainController
from drone_detection.models import CameraConfig

def main():
    """Run with optimized Windows camera settings."""
    print("🚀 WINDOWS-OPTIMIZED DRONE DETECTION")
    print("=" * 50)
    
    # Setup logging
    logging.basicConfig(level=logging.INFO, 
                       format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    try:
        # Create controller
        controller = MainController()
        
        # Override camera configs with working settings
        controller.drone_config = CameraConfig(
            source_type='laptop',  # Force laptop camera
            device_id={best_camera},        # Use working camera
            resolution=(640, 480),  # Safe resolution
            fps=15,                 # Lower FPS for stability
            backend='dshow'         # DirectShow backend
        )
        
        controller.laptop_config = CameraConfig(
            source_type='laptop',
            device_id={best_camera},
            resolution=(320, 240),  # Even lower resolution fallback
            fps=15,
            backend='dshow'
        )
        
        print(f"🎯 Using camera {best_camera} with DirectShow backend")
        print("🔧 Optimized for Windows stability")
        
        # Initialize and run
        if not controller.initialize_components():
            print("❌ Failed to initialize components")
            return False
        
        print("✅ Starting detection... Press 'q' to quit")
        controller.human_detector.set_confidence_threshold(0.5)
        controller.run()
        
        return True
        
    except KeyboardInterrupt:
        print("\\n⚠️  Stopped by user")
        return True
    except Exception as e:
        print(f"\\n❌ Error: {{e}}")
        return False

if __name__ == "__main__":
    main()
'''
    
    with open('run_windows_optimized.py', 'w') as f:
        f.write(fix_script)
    
    print(f"\n✅ Created run_windows_optimized.py")
    print("🚀 Run it with: python run_windows_optimized.py")

if __name__ == "__main__":
    create_windows_camera_fix()
