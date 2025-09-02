#!/usr/bin/env python3
"""
Quick bounding box coordinate test for Windows.

This script tests YOLOv8 detection coordinates to identify the issue.
"""

import cv2
import numpy as np
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_coordinates():
    """Test YOLOv8 coordinate detection."""
    
    print("=" * 50)
    print("BOUNDING BOX COORDINATE TEST")
    print("=" * 50)
    
    try:
        # Test camera access
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("❌ Cannot open camera")
            return False
        
        # Get a test frame
        ret, frame = cap.read()
        if not ret:
            print("❌ Cannot capture frame")
            cap.release()
            return False
        
        height, width = frame.shape[:2]
        print(f"📷 Frame size: {width}x{height}")
        
        # Test YOLOv8 loading
        try:
            from ultralytics import YOLO
            model = YOLO("yolov8n.pt")
            print("✅ YOLOv8 model loaded")
        except Exception as e:
            print(f"❌ YOLOv8 loading failed: {e}")
            cap.release()
            return False
        
        # Run detection on test frame
        print("🔍 Running detection...")
        results = model(frame, verbose=False)
        
        if len(results) > 0 and results[0].boxes is not None:
            boxes = results[0].boxes.xyxy.cpu().numpy()
            confidences = results[0].boxes.conf.cpu().numpy()
            class_ids = results[0].boxes.cls.cpu().numpy().astype(int)
            
            print(f"📊 Found {len(boxes)} detections")
            
            # Check coordinate ranges
            if len(boxes) > 0:
                min_coord = np.min(boxes)
                max_coord = np.max(boxes)
                print(f"📐 Coordinate range: {min_coord:.2f} to {max_coord:.2f}")
                
                if max_coord <= 1.0:
                    print("⚠️  ISSUE FOUND: Coordinates are normalized (0-1 range)")
                    print("   YOLOv8 should return pixel coordinates, not normalized!")
                else:
                    print("✅ Coordinates appear to be in pixel range")
                
                # Show person detections
                person_detections = 0
                for i, (box, conf, class_id) in enumerate(zip(boxes, confidences, class_ids)):
                    if class_id == 0 and conf > 0.3:  # Person class
                        person_detections += 1
                        x1, y1, x2, y2 = box
                        print(f"👤 Person {person_detections}: ({x1:.1f}, {y1:.1f}, {x2:.1f}, {y2:.1f}) conf={conf:.2f}")
                        
                        # Check if coordinates make sense
                        if max_coord <= 1.0:
                            # Scale to pixel coordinates
                            px1, py1, px2, py2 = int(x1*width), int(y1*height), int(x2*width), int(y2*height)
                            print(f"   Scaled: ({px1}, {py1}, {px2}, {py2})")
                            
                            # Draw both boxes for comparison
                            cv2.rectangle(frame, (int(x1*width), int(y1*height)), (int(x2*width), int(y2*height)), (0, 255, 0), 3)
                            cv2.putText(frame, f"FIXED: {conf:.2f}", (int(x1*width), int(y1*height)-10), 
                                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                        else:
                            # Use coordinates as-is
                            cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 3)
                            cv2.putText(frame, f"Person: {conf:.2f}", (int(x1), int(y1)-10), 
                                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                
                print(f"👥 Total person detections: {person_detections}")
        else:
            print("❌ No detections found")
        
        # Show test result
        cv2.putText(frame, "COORDINATE TEST", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        cv2.putText(frame, f"Frame: {width}x{height}", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        cv2.imshow("Bounding Box Coordinate Test", frame)
        print("\n🎯 Test frame displayed. Press any key to close.")
        cv2.waitKey(0)
        cv2.destroyAllWindows()
        
        cap.release()
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False


if __name__ == "__main__":
    print("This script will help identify the bounding box coordinate issue.")
    print("Make sure you're positioned in front of the camera.")
    print()
    
    input("Press Enter to start the test...")
    
    if test_coordinates():
        print("\n" + "=" * 50)
        print("TEST COMPLETED")
        print("=" * 50)
        print()
        print("If bounding boxes were correctly positioned:")
        print("✅ Coordinates are working properly")
        print()
        print("If bounding boxes were in wrong locations:")
        print("❌ There's a coordinate scaling issue")
        print("   - Check if coordinates are normalized vs pixel")
        print("   - Verify YOLOv8 version and configuration")
        print("   - Test with different resolutions")
    else:
        print("❌ Test could not be completed. Check error messages above.")
    
    input("\nPress Enter to exit...")
