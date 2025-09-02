"""
Simple Windows Coordinate Fix Test

This script automatically tests the coordinate fix without requiring user input.
Perfect for testing on Windows to see if the bounding box issue is resolved.
"""

import sys
import os
import platform
import logging

# Add the project root to the path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

try:
    from drone_detection.windows_coordinate_fix import WindowsCoordinateFix
    from drone_detection.human_detector import HumanDetector
    from ultralytics import YOLO
    import cv2
    import numpy as np
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure you're in the correct directory and have installed all requirements.")
    sys.exit(1)

def test_coordinate_fix():
    """Test the coordinate fix with sample data."""
    print("🔧 TESTING WINDOWS COORDINATE FIX")
    print("=" * 40)
    
    fix = WindowsCoordinateFix()
    
    # Test cases that represent common Windows issues
    test_cases = [
        {
            'name': 'Normalized coordinates (0-1 range)',
            'coords': [(0.2, 0.3, 0.8, 0.9)],
            'frame_size': (640, 480),
            'expected': 'Should scale to pixel coordinates'
        },
        {
            'name': 'Small suspicious coordinates', 
            'coords': [(20, 30, 80, 90)],
            'frame_size': (640, 480),
            'expected': 'Might be scaled if too small'
        },
        {
            'name': 'Normal pixel coordinates',
            'coords': [(120, 150, 400, 350)],
            'frame_size': (640, 480),
            'expected': 'Should remain unchanged'
        },
        {
            'name': 'Upper-left corner issue (Windows bug)',
            'coords': [(5, 5, 180, 250)],
            'frame_size': (640, 480),
            'expected': 'May be repositioned if detected as offset'
        }
    ]
    
    for test in test_cases:
        print(f"\n📋 Test: {test['name']}")
        original = test['coords'][0]
        print(f"   Input:     ({original[0]}, {original[1]}, {original[2]}, {original[3]})")
        print(f"   Expected:  {test['expected']}")
        
        fixed = fix.fix_coordinates(test['coords'], test['frame_size'][0], test['frame_size'][1])
        
        if fixed:
            x1, y1, x2, y2 = fixed[0]
            print(f"   Output:    ({x1}, {y1}, {x2}, {y2})")
            print(f"   Box size:  {x2-x1}x{y2-y1}")
            
            # Check if coordinates were changed
            if (x1, y1, x2, y2) != original:
                print(f"   Status:    ✅ COORDINATES FIXED")
            else:
                print(f"   Status:    ℹ️  No change needed")
        else:
            print(f"   Output:    ❌ REJECTED (invalid box)")

def test_yolo_coordinates():
    """Test YOLOv8 coordinate output directly."""
    print("\n🤖 TESTING YOLOV8 COORDINATE OUTPUT")
    print("=" * 45)
    
    try:
        model = YOLO('yolov8n.pt')
        cap = cv2.VideoCapture(0)
        
        if not cap.isOpened():
            print("❌ Cannot open camera for coordinate test")
            return
            
        ret, frame = cap.read()
        if not ret:
            print("❌ Cannot read frame from camera")
            cap.release()
            return
            
        height, width = frame.shape[:2]
        print(f"📹 Frame dimensions: {width}x{height}")
        
        # Run detection
        results = model(frame, verbose=False)
        
        if results[0].boxes is not None:
            boxes = results[0].boxes.xyxy.cpu().numpy()
            confidences = results[0].boxes.conf.cpu().numpy()
            classes = results[0].boxes.cls.cpu().numpy()
            
            print(f"📊 Found {len(boxes)} total detections")
            
            person_count = 0
            for i, (box, conf, cls) in enumerate(zip(boxes, confidences, classes)):
                if int(cls) == 0:  # Person class
                    person_count += 1
                    x1, y1, x2, y2 = box
                    print(f"\n👤 Person {person_count}:")
                    print(f"   Raw coordinates: ({x1:.2f}, {y1:.2f}, {x2:.2f}, {y2:.2f})")
                    print(f"   Confidence: {conf:.3f}")
                    print(f"   Coordinate range: {min(x1,y1,x2,y2):.1f} to {max(x1,y1,x2,y2):.1f}")
                    
                    # Analyze coordinate type
                    if max(x1, y1, x2, y2) <= 1.0:
                        print(f"   ⚠️  NORMALIZED coordinates detected (0-1 range)")
                        print(f"   🔧 Would scale to: ({x1*width:.0f}, {y1*height:.0f}, {x2*width:.0f}, {y2*height:.0f})")
                    else:
                        print(f"   ✅ PIXEL coordinates (normal)")
                        
            if person_count == 0:
                print("ℹ️  No people detected in frame")
        else:
            print("ℹ️  No detections found")
            
        cap.release()
        
    except Exception as e:
        print(f"❌ Error in YOLOv8 coordinate test: {e}")

def main():
    """Run the coordinate fix tests automatically."""
    print("🔧 AUTOMATIC WINDOWS COORDINATE FIX TEST")
    print("=" * 50)
    print(f"Platform: {platform.system()} {platform.release()}")
    print()
    
    # Test 1: Coordinate fix logic
    test_coordinate_fix()
    
    # Test 2: YOLOv8 coordinates
    test_yolo_coordinates()
    
    print("\n" + "=" * 50)
    print("📋 SUMMARY")
    print("=" * 50)
    print()
    print("✅ If YOLOv8 shows PIXEL coordinates (values > 1):")
    print("   The coordinate system is working correctly")
    print()
    print("⚠️  If YOLOv8 shows NORMALIZED coordinates (values ≤ 1):")
    print("   The coordinate fix will automatically scale them")
    print()
    print("🎯 To test the complete system:")
    print("   1. Run: python main.py --gui --confidence 0.5")
    print("   2. Check if bounding boxes appear around people")
    print("   3. The coordinate fix is now integrated automatically")
    print()
    print("📞 If boxes are still in wrong positions:")
    print("   - Try different resolutions: --resolution 1280x720")
    print("   - Lower confidence: --confidence 0.3")
    print("   - Check Windows DPI scaling settings")

if __name__ == "__main__":
    main()
