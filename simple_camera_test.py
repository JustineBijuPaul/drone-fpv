#!/usr/bin/env python3
"""Simple Windows camera test that avoids the MSMF error."""

import cv2
import platform

def test_simple_camera():
    """Test camera with DirectShow backend to avoid MSMF issues."""
    print("🎥 SIMPLE WINDOWS CAMERA TEST")
    print("=" * 40)
    print(f"Platform: {platform.system()}")
    print()
    
    print("Testing DirectShow camera access...")
    
    # Try DirectShow backend specifically (avoids MSMF issues)
    for camera_id in range(3):
        print(f"\n📹 Testing camera {camera_id} with DirectShow:")
        try:
            # Use DirectShow backend explicitly
            cap = cv2.VideoCapture(camera_id, cv2.CAP_DSHOW)
            
            if not cap.isOpened():
                print(f"   ❌ Camera {camera_id} not accessible")
                continue
            
            # Set basic properties
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            cap.set(cv2.CAP_PROP_FPS, 15)  # Lower FPS for stability
            
            # Try to read a frame
            print("   🔄 Attempting to read frame...")
            ret, frame = cap.read()
            
            if ret and frame is not None:
                height, width = frame.shape[:2]
                print(f"   ✅ SUCCESS! Resolution: {width}x{height}")
                
                # Test a few more frames
                success_count = 0
                for i in range(5):
                    ret, frame = cap.read()
                    if ret and frame is not None:
                        success_count += 1
                
                print(f"   📊 Read {success_count}/5 additional frames successfully")
                
                if success_count >= 3:
                    print(f"   🎯 Camera {camera_id} is WORKING WELL!")
                    cap.release()
                    return camera_id
                else:
                    print(f"   ⚠️  Camera {camera_id} is unstable")
            else:
                print(f"   ❌ Cannot read frames from camera {camera_id}")
            
            cap.release()
            
        except Exception as e:
            print(f"   ❌ Error with camera {camera_id}: {e}")
    
    print("\n❌ No stable camera found")
    return None

if __name__ == "__main__":
    working_camera = test_simple_camera()
    
    if working_camera is not None:
        print(f"\n🎉 SOLUTION FOUND!")
        print(f"✅ Use camera {working_camera} with DirectShow backend")
        print(f"\n🚀 Try running:")
        print(f"python main.py --device-id {working_camera} --gui")
        print(f"\nOr modify your camera config to use:")
        print(f"- device_id: {working_camera}")
        print(f"- backend: DirectShow (CAP_DSHOW)")
        print(f"- resolution: 640x480")
        print(f"- fps: 15")
    else:
        print(f"\n🔧 TROUBLESHOOTING:")
        print(f"1. Check Windows Camera privacy settings")
        print(f"2. Close other applications using camera (Skype, Teams, etc.)")
        print(f"3. Try running as Administrator")
        print(f"4. Restart your computer")
        print(f"5. Check Device Manager for camera drivers")
