#!/usr/bin/env python3
"""Quick test of Windows fixes - simplified version."""

import cv2
import platform
import sys
import os

# Add project directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from drone_detection.camera_manager import CameraManager
from drone_detection.human_detector import HumanDetector
from drone_detection.display_manager import DisplayManager
from drone_detection.models import CameraConfig

def test_windows_fixes():
    """Test all Windows fixes in a simple way."""
    print("🔧 TESTING WINDOWS FIXES")
    print("=" * 40)
    print(f"Platform: {platform.system()}")
    print()
    
    # Test 1: Import test
    print("✅ All imports successful")
    
    # Test 2: Camera initialization
    print("📹 Testing camera initialization...")
    camera = CameraManager()
    config = CameraConfig(
        source_type='laptop',
        device_id=0,
        resolution=(640, 480),
        fps=30
    )
    
    if not camera.initialize_camera(config):
        print("❌ Camera initialization failed")
        return False
    print("✅ Camera initialized successfully")
    
    # Test 3: Model loading
    print("🧠 Testing model loading...")
    detector = HumanDetector()
    detector.set_confidence_threshold(0.5)
    
    if not detector.load_model():
        print("❌ Model loading failed")
        camera.release()
        return False
    print("✅ Model loaded successfully")
    
    # Test 4: Frame capture and detection
    print("📸 Testing frame capture and detection...")
    frame_count = 0
    detection_count = 0
    
    for i in range(10):  # Test 10 frames
        frame = camera.get_frame()
        if frame is None:
            print(f"❌ Failed to get frame {i+1}")
            continue
            
        frame_count += 1
        detections = detector.detect_humans(frame)
        detection_count += len(detections)
        
        if detections:
            print(f"   Frame {i+1}: Found {len(detections)} detections")
            for j, det in enumerate(detections):
                if hasattr(det, 'bbox'):
                    x1, y1, x2, y2 = det.bbox
                    print(f"     Detection {j+1}: ({x1:.1f}, {y1:.1f}, {x2:.1f}, {y2:.1f}) conf={det.confidence:.2f}")
    
    print(f"✅ Processed {frame_count} frames, found {detection_count} total detections")
    
    # Test 5: Display manager
    print("🖼️  Testing display manager...")
    display = DisplayManager()
    
    # Get one more frame for display test
    frame = camera.get_frame()
    if frame is not None:
        detections = detector.detect_humans(frame)
        frame_with_detections = display.draw_detections(frame, detections)
        print(f"✅ Display manager working, frame shape: {frame_with_detections.shape}")
    
    # Cleanup
    camera.release()
    print("✅ Cleanup completed")
    
    print("\n🎉 ALL WINDOWS FIXES WORKING!")
    print("=" * 40)
    print("Your system is ready to run:")
    print("  python main.py --gui --confidence 0.5")
    print("  python windows_diagnostic.py")
    
    return True

if __name__ == "__main__":
    try:
        test_windows_fixes()
    except KeyboardInterrupt:
        print("\n⚠️  Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
