# BOUNDING BOX ALIGNMENT ISSUE - TROUBLESHOOTING GUIDE

## Problem Description
The human detection is working (showing "person: 88%") but the green bounding box appears in the wrong location (upper left corner) instead of around the detected person.

## Diagnostic Steps

### Step 1: Quick Coordinate Test
```cmd
python test_coordinates.py
```
This will show you exactly what coordinates YOLOv8 is returning and whether they need scaling.

### Step 2: Debug Mode
```cmd
debug_windows.bat
```
This will run the application with detailed coordinate logging.

### Step 3: Check Debug Log
After running debug mode, check `drone_detection_debug.log` for coordinate information.

## Common Causes and Solutions

### 1. Normalized Coordinates Issue
**Problem**: YOLOv8 returns coordinates in 0-1 range instead of pixel coordinates
**Symptoms**: Bounding boxes appear in upper-left corner, coordinates are decimal numbers < 1.0
**Solution**: The code now automatically detects and scales normalized coordinates

### 2. Frame Scaling Issue  
**Problem**: Camera frame is different size than expected
**Symptoms**: Bounding boxes offset by constant factor
**Solution**: 
```cmd
python main.py --resolution 640x480 --gui
```
Try different resolutions to match your camera's native resolution.

### 3. YOLOv8 Model Issue
**Problem**: YOLOv8 model configuration issue
**Solution**: Try different model sizes:
```cmd
# Download and test different models
python -c "from ultralytics import YOLO; YOLO('yolov8s.pt')"
```

### 4. Windows DPI Scaling
**Problem**: High-DPI display affects coordinate calculation
**Solution**: 
- Right-click python.exe → Properties → Compatibility → Override high DPI scaling behavior
- Or run application in compatibility mode

### 5. OpenCV Backend Issue
**Problem**: Windows camera backend affects coordinate system
**Solution**: The Windows compatibility module now uses optimized backends

## Immediate Fixes to Try

### Fix 1: Force Coordinate Scaling
Edit `drone_detection/human_detector.py` and force coordinate scaling:
```python
# In filter_detections method, always scale coordinates:
x1 = int(x1 * frame_width if x1 <= 1 else x1)
y1 = int(y1 * frame_height if y1 <= 1 else y1)  
x2 = int(x2 * frame_width if x2 <= 1 else x2)
y2 = int(y2 * frame_height if y2 <= 1 else y2)
```

### Fix 2: Test Different Resolutions
```cmd
# Try these resolutions:
python main.py --resolution 320x240 --gui
python main.py --resolution 640x480 --gui  
python main.py --resolution 1280x720 --gui
```

### Fix 3: Lower Confidence Threshold
```cmd
python main.py --confidence 0.2 --gui
```
This might reveal if detections are being filtered out.

### Fix 4: Use Different Camera Backend
Edit the camera initialization to force a specific backend.

## Verification Commands

### Test 1: Coordinate Range Check
```python
python -c "
import cv2
from ultralytics import YOLO
cap = cv2.VideoCapture(0)
ret, frame = cap.read()
if ret:
    model = YOLO('yolov8n.pt')
    results = model(frame, verbose=False)
    if results[0].boxes is not None:
        boxes = results[0].boxes.xyxy.cpu().numpy()
        print('Coordinate range:', boxes.min(), 'to', boxes.max())
        print('Frame size:', frame.shape[:2])
cap.release()
"
```

### Test 2: Manual Box Drawing
```python
python -c "
import cv2
import numpy as np
cap = cv2.VideoCapture(0)
ret, frame = cap.read()
if ret:
    h, w = frame.shape[:2]
    # Draw test box in center
    cv2.rectangle(frame, (w//4, h//4), (3*w//4, 3*h//4), (0, 255, 0), 3)
    cv2.imshow('Test Box', frame)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
cap.release()
"
```

## Advanced Debugging

### Enable All Debug Logging
Add this to the top of your main script:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Check YOLOv8 Version
```cmd
python -c "import ultralytics; print(ultralytics.__version__)"
```

### Test with Sample Image
```python
python -c "
from ultralytics import YOLO
import cv2
model = YOLO('yolov8n.pt')
# Test with built-in sample
results = model('https://ultralytics.com/images/bus.jpg')
results[0].show()
"
```

## Expected Behavior After Fix

1. **Coordinates should be in pixel range**: e.g., (150, 200, 450, 600) for a 640x480 frame
2. **Bounding boxes should surround detected people**: Green rectangles around faces/bodies
3. **Text labels should appear above boxes**: "person: XX%" above each detection
4. **Boxes should scale with resolution changes**: Bigger boxes for higher resolution

## Recovery Commands

If you need to reset everything:

```cmd
# Clean installation
rmdir /s /q venv
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
pip install -r requirements-windows.txt

# Test basic functionality
python test_coordinates.py
```

## Contact Support

If the issue persists, run the debug session and provide:
1. Contents of `drone_detection_debug.log`
2. Output of `python test_coordinates.py`  
3. Your Windows version and camera model
4. Screenshots showing the misaligned bounding boxes

The coordinate detection and scaling code has been enhanced to automatically handle most common issues, so running the updated version should resolve the bounding box alignment problem.
