"""
Windows Bounding Box Diagnostic Script

This script will help diagnose and fix remaining bounding box alignment issues on Windows.
It provides comprehensive testing and automatic fixes.
"""

import cv2
import numpy as np
import sys
import os
import platform
import logging
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    from ultralytics import YOLO
    from drone_detection.human_detector import HumanDetector
    from drone_detection.display_manager import DisplayManager
    from drone_detection.camera_manager import CameraManager
    from drone_detection.models import Config
    from drone_detection.windows_coordinate_fix import WindowsCoordinateFix
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure you're in the correct directory and have installed all requirements.")
    sys.exit(1)

def test_yolo_directly():
    """Test YOLOv8 directly to see raw coordinate output."""
    print("\n🔍 TESTING YOLOV8 DIRECTLY")
    print("=" * 40)
    
    try:
        model = YOLO('yolov8n.pt')
        cap = cv2.VideoCapture(0)
        
        if not cap.isOpened():
            print("❌ Cannot open camera")
            return
            
        ret, frame = cap.read()
        if not ret:
            print("❌ Cannot read frame")
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
            
            print(f"📊 Found {len(boxes)} detections")
            
            for i, (box, conf, cls) in enumerate(zip(boxes, confidences, classes)):
                if int(cls) == 0:  # Person class
                    x1, y1, x2, y2 = box
                    print(f"👤 Person {i+1}:")
                    print(f"   Raw coordinates: ({x1:.2f}, {y1:.2f}, {x2:.2f}, {y2:.2f})")
                    print(f"   Confidence: {conf:.3f}")
                    print(f"   Coordinate range: {min(x1,y1,x2,y2):.1f} to {max(x1,y1,x2,y2):.1f}")
                    
                    # Check if coordinates look normalized
                    if max(x1, y1, x2, y2) <= 1.0:
                        print(f"   ⚠️  Coordinates appear NORMALIZED (0-1 range)")
                        print(f"   🔧 Scaling: ({x1*width:.0f}, {y1*height:.0f}, {x2*width:.0f}, {y2*height:.0f})")
                    else:
                        print(f"   ✅ Coordinates appear to be PIXEL values")
                        
                    # Draw the box on the frame
                    x1_int, y1_int, x2_int, y2_int = map(int, [x1, y1, x2, y2])
                    if max(x1, y1, x2, y2) <= 1.0:
                        # Scale normalized coordinates
                        x1_int = int(x1 * width)
                        y1_int = int(y1 * height)
                        x2_int = int(x2 * width)
                        y2_int = int(y2 * height)
                    
                    cv2.rectangle(frame, (x1_int, y1_int), (x2_int, y2_int), (0, 255, 0), 2)
                    cv2.putText(frame, f'Person: {conf:.2f}', (x1_int, y1_int-10), 
                              cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        else:
            print("❌ No detections found")
            
        # Display the frame
        cv2.imshow('YOLOv8 Direct Test', frame)
        print("\n🎯 Check if the green boxes are correctly positioned around people.")
        print("Press any key to continue...")
        cv2.waitKey(0)
        cv2.destroyAllWindows()
        
        cap.release()
        
    except Exception as e:
        print(f"❌ Error in direct YOLOv8 test: {e}")

def test_human_detector():
    """Test the HumanDetector class with coordinate fix."""
    print("\n🧠 TESTING HUMAN DETECTOR WITH COORDINATE FIX")
    print("=" * 50)
    
    try:
        # Initialize human detector
        detector = HumanDetector()
        detector.set_confidence_threshold(0.5)
        
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("❌ Cannot open camera")
            return
            
        ret, frame = cap.read()
        if not ret:
            print("❌ Cannot read frame")
            cap.release()
            return
            
        height, width = frame.shape[:2]
        print(f"📹 Frame dimensions: {width}x{height}")
        
        # Run detection through our detector
        detections = detector.detect_humans(frame)
        
        print(f"📊 Human detector found {len(detections)} detections")
        
        for i, detection in enumerate(detections):
            print(f"👤 Detection {i+1}:")
            if hasattr(detection, 'bbox'):
                x1, y1, x2, y2 = detection.bbox
                print(f"   Coordinates: ({x1}, {y1}, {x2}, {y2})")
                print(f"   Box size: {x2-x1}x{y2-y1}")
                print(f"   Confidence: {detection.confidence:.3f}")
                
                # Draw on frame
                cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 0, 0), 2)
                cv2.putText(frame, f'Human: {detection.confidence:.2f}', (x1, y1-10), 
                          cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)
        
        cv2.imshow('Human Detector Test', frame)
        print("\n🎯 Check if the blue boxes are correctly positioned around people.")
        print("Press any key to continue...")
        cv2.waitKey(0)
        cv2.destroyAllWindows()
        
        cap.release()
        
    except Exception as e:
        print(f"❌ Error in human detector test: {e}")

def test_coordinate_fix_specifically():
    """Test the Windows coordinate fix specifically."""
    print("\n🔧 TESTING WINDOWS COORDINATE FIX")
    print("=" * 40)
    
    try:
        fix = WindowsCoordinateFix()
        
        # Test cases
        test_cases = [
            {
                'name': 'Normalized coordinates (0-1)',
                'coords': [(0.2, 0.3, 0.8, 0.9)],
                'frame_size': (640, 480)
            },
            {
                'name': 'Small suspicious coordinates',
                'coords': [(20, 30, 80, 90)],
                'frame_size': (640, 480)
            },
            {
                'name': 'Normal pixel coordinates',
                'coords': [(120, 150, 400, 350)],
                'frame_size': (640, 480)
            }
        ]
        
        for test in test_cases:
            print(f"\n📋 Test: {test['name']}")
            original = test['coords'][0]
            print(f"   Input:  ({original[0]}, {original[1]}, {original[2]}, {original[3]})")
            
            fixed = fix.fix_coordinates(test['coords'], test['frame_size'][0], test['frame_size'][1])
            
            if fixed:
                x1, y1, x2, y2 = fixed[0]
                print(f"   Output: ({x1}, {y1}, {x2}, {y2})")
                print(f"   Size:   {x2-x1}x{y2-y1}")
            else:
                print(f"   Output: REJECTED")
                
    except Exception as e:
        print(f"❌ Error in coordinate fix test: {e}")

def run_full_application_test():
    """Run the full application with enhanced debugging."""
    print("\n🚀 RUNNING FULL APPLICATION TEST")
    print("=" * 40)
    
    try:
        # Enable debug logging
        logging.basicConfig(level=logging.DEBUG)
        
        config = Config()
        config.display_gui = True
        config.confidence_threshold = 0.5
        
        # Initialize components
        camera = CameraManager()
        detector = HumanDetector()
        display = DisplayManager()
        
        if not camera.initialize():
            print("❌ Failed to initialize camera")
            return
            
        print("✅ Camera initialized")
        print("📱 Application running... Press 'q' to quit")
        print("🔍 Watch for bounding box positions - they should be around detected people")
        
        frame_count = 0
        while True:
            frame = camera.get_frame()
            if frame is None:
                continue
                
            # Run detection
            detections = detector.detect_humans(frame)
            
            # Add debug info to frame
            height, width = frame.shape[:2]
            cv2.putText(frame, f'Frame: {width}x{height}', (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            cv2.putText(frame, f'Detections: {len(detections)}', (10, 60), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            cv2.putText(frame, f'Platform: {platform.system()}', (10, 90), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            
            if frame_count % 30 == 0 and detections:  # Every 30 frames
                print(f"🔍 Frame {frame_count}: Found {len(detections)} detections")
                for i, det in enumerate(detections):
                    if hasattr(det, 'bbox'):
                        x1, y1, x2, y2 = det.bbox
                        print(f"   Detection {i}: ({x1}, {y1}, {x2}, {y2}) conf={det.confidence:.2f}")
            
            frame_count += 1
            
            # Display frame
            frame_with_detections = display.draw_detections(frame, detections)
            cv2.imshow('Full Application Test', frame_with_detections)
            
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q') or key == 27:  # q or ESC
                break
                
        cv2.destroyAllWindows()
        camera.cleanup()
        
    except Exception as e:
        print(f"❌ Error in full application test: {e}")

def main():
    print("🔧 WINDOWS BOUNDING BOX DIAGNOSTIC TOOL")
    print("=" * 50)
    print()
    print("This tool will help diagnose and fix bounding box alignment issues on Windows.")
    print(f"Running on: {platform.system()} {platform.release()}")
    print()
    
    while True:
        print("\nSelect a test to run:")
        print("1. Test YOLOv8 directly (raw coordinates)")
        print("2. Test Human Detector with coordinate fix")
        print("3. Test coordinate fix logic")
        print("4. Run full application test") 
        print("5. Show system info")
        print("6. Exit")
        print()
        
        choice = input("Enter your choice (1-6): ").strip()
        
        if choice == '1':
            test_yolo_directly()
        elif choice == '2':
            test_human_detector()
        elif choice == '3':
            test_coordinate_fix_specifically()
        elif choice == '4':
            run_full_application_test()
        elif choice == '5':
            show_system_info()
        elif choice == '6':
            print("👋 Exiting...")
            break
        else:
            print("❌ Invalid choice. Please select 1-6.")

def show_system_info():
    """Show system information for debugging."""
    print("\n💻 SYSTEM INFORMATION")
    print("=" * 30)
    print(f"Platform: {platform.system()} {platform.release()}")
    print(f"Python: {sys.version}")
    
    try:
        import cv2
        print(f"OpenCV: {cv2.__version__}")
    except:
        print("OpenCV: Not installed")
        
    try:
        from ultralytics import YOLO
        import ultralytics
        print(f"Ultralytics: {ultralytics.__version__}")
    except:
        print("Ultralytics: Not installed")
        
    try:
        import numpy as np
        print(f"NumPy: {np.__version__}")
    except:
        print("NumPy: Not installed")
        
    print("\n📹 CAMERA TEST")
    try:
        cap = cv2.VideoCapture(0)
        if cap.isOpened():
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            print(f"Camera 0: {width}x{height} @ {fps}fps ✅")
        else:
            print("Camera 0: Not available ❌")
        cap.release()
    except Exception as e:
        print(f"Camera test error: {e}")

if __name__ == "__main__":
    main()
