from drone_detection.windows_coordinate_fix import WindowsCoordinateFix
fix = WindowsCoordinateFix()
print('is_windows:', fix.is_windows)
boxes = [(50,20,150,120), (0.1,0.1,0.3,0.4), (10,10,60,40)]
print('Original:', boxes)
print('Fixed:', fix.fix_coordinates(boxes, 640, 480))
