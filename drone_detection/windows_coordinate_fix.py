"""
Windows Coordinate Fix for YOLOv8 Bounding Box Issue

This module provides a fix for the coordinate misalignment issue experienced on Windows
where YOLOv8 detections appear with correct confidence but wrong box positions.
"""
import logging
from typing import List, Tuple, Optional
import platform

class WindowsCoordinateFix:
    """
    Fixes coordinate issues specific to Windows environments.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.is_windows = platform.system() == 'Windows'
        self.coordinate_adjustments_enabled = True
        
    def fix_coordinates(self, boxes: List[Tuple[float, float, float, float]], 
                       frame_width: int, frame_height: int,
                       force_scaling: bool = None) -> List[Tuple[int, int, int, int]]:
        """
        Fix coordinate issues commonly seen on Windows.
        
        Args:
            boxes: List of (x1, y1, x2, y2) coordinate tuples
            frame_width: Frame width in pixels
            frame_height: Frame height in pixels  
            force_scaling: Force coordinate scaling (overrides auto-detection)
            
        Returns:
            List of fixed coordinate tuples as integers
        """
        if not boxes:
            return []
            
        fixed_boxes = []
        
        for i, (x1, y1, x2, y2) in enumerate(boxes):
            self.logger.debug(f"Original coordinates {i}: ({x1:.2f}, {y1:.2f}, {x2:.2f}, {y2:.2f})")
            
            # Determine if coordinates need scaling
            needs_scaling = self._needs_coordinate_scaling(x1, y1, x2, y2, frame_width, frame_height)
            
            if force_scaling is not None:
                needs_scaling = force_scaling
                
            if needs_scaling:
                x1, y1, x2, y2 = self._scale_normalized_coordinates(
                    x1, y1, x2, y2, frame_width, frame_height
                )
                self.logger.info(f"Scaled coordinates {i}: ({x1}, {y1}, {x2}, {y2})")
            
            # Apply Windows-specific coordinate fixes
            x1, y1, x2, y2 = self._apply_windows_fixes(x1, y1, x2, y2, frame_width, frame_height)
            
            # Ensure coordinates are valid integers within bounds
            x1, y1, x2, y2 = self._clamp_coordinates(x1, y1, x2, y2, frame_width, frame_height)
            
            # Validate final coordinates
            if self._validate_box(x1, y1, x2, y2):
                fixed_boxes.append((x1, y1, x2, y2))
                self.logger.debug(f"Final coordinates {i}: ({x1}, {y1}, {x2}, {y2})")
            else:
                self.logger.warning(f"Invalid box rejected: ({x1}, {y1}, {x2}, {y2})")
                
        return fixed_boxes
    
    def _needs_coordinate_scaling(self, x1: float, y1: float, x2: float, y2: float,
                                frame_width: int, frame_height: int) -> bool:
        """Determine if coordinates are normalized and need scaling."""
        # Only treat coordinates as normalized when they are in the 0..1 range.
        # Previous heuristics that treated small pixel values as normalized
        # were too aggressive and caused valid pixel coordinates to be
        # scaled incorrectly (leading to mis-positioned boxes).
        try:
            max_coord = max(abs(x1), abs(y1), abs(x2), abs(y2))
        except Exception:
            return False

        # If all coordinates are within 0..1 assume normalized coordinates
        return max_coord <= 1.0
    
    def _scale_normalized_coordinates(self, x1: float, y1: float, x2: float, y2: float,
                                    frame_width: int, frame_height: int) -> Tuple[int, int, int, int]:
        """Scale normalized (0-1) coordinates to pixel coordinates."""
        x1_scaled = int(x1 * frame_width)
        y1_scaled = int(y1 * frame_height)
        x2_scaled = int(x2 * frame_width)
        y2_scaled = int(y2 * frame_height)
        
        return x1_scaled, y1_scaled, x2_scaled, y2_scaled
    
    def _apply_windows_fixes(self, x1: float, y1: float, x2: float, y2: float,
                           frame_width: int, frame_height: int) -> Tuple[int, int, int, int]:
        """Apply Windows-specific coordinate fixes."""
        # Convert to ints for further processing
        x1_i, y1_i, x2_i, y2_i = int(x1), int(y1), int(x2), int(y2)

        # If not on Windows, do nothing special
        if not self.is_windows:
            return x1_i, y1_i, x2_i, y2_i

        # Keep behavior minimal on Windows: do not attempt to guess new
        # positions. Only ensure coordinates are within bounds; aggressive
        # auto-repositioning was removed because it produced incorrect boxes.
        return x1_i, y1_i, x2_i, y2_i
    
    def _clamp_coordinates(self, x1: int, y1: int, x2: int, y2: int,
                         frame_width: int, frame_height: int) -> Tuple[int, int, int, int]:
        """Clamp coordinates to valid frame bounds."""
        # Ensure all coordinates are within frame bounds
        x1 = max(0, min(x1, frame_width - 1))
        y1 = max(0, min(y1, frame_height - 1))
        x2 = max(0, min(x2, frame_width - 1))  
        y2 = max(0, min(y2, frame_height - 1))
        
        # Ensure x2 > x1 and y2 > y1
        if x2 <= x1:
            x2 = min(x1 + 10, frame_width - 1)  # Minimum box width
        if y2 <= y1:
            y2 = min(y1 + 10, frame_height - 1)  # Minimum box height
            
        return x1, y1, x2, y2
    
    def _validate_box(self, x1: int, y1: int, x2: int, y2: int,
                     min_size: int = 10) -> bool:
        """Validate that the bounding box is reasonable."""
        width = x2 - x1
        height = y2 - y1
        
        # Check minimum size
        if width < min_size or height < min_size:
            return False
            
        # Check coordinates make sense
        if x1 >= x2 or y1 >= y2:
            return False
            
        return True


def apply_coordinate_fix_to_detections(detections, frame_width: int, frame_height: int):
    """
    Apply coordinate fixes to a list of detection results.
    
    This is a convenience function that can be used with existing detection results.
    """
    if not detections:
        return detections
        
    fix = WindowsCoordinateFix()
    
    # Extract coordinate boxes from detections
    boxes = []
    for detection in detections:
        if hasattr(detection, 'bbox'):
            boxes.append(detection.bbox)
        elif hasattr(detection, 'x1'):
            boxes.append((detection.x1, detection.y1, detection.x2, detection.y2))
        else:
            continue
    
    # Apply coordinate fixes
    fixed_boxes = fix.fix_coordinates(boxes, frame_width, frame_height)
    
    # Update detection objects with fixed coordinates
    for i, detection in enumerate(detections):
        if i < len(fixed_boxes):
            x1, y1, x2, y2 = fixed_boxes[i]
            
            if hasattr(detection, 'bbox'):
                detection.bbox = (x1, y1, x2, y2)
            elif hasattr(detection, 'x1'):
                detection.x1 = x1
                detection.y1 = y1
                detection.x2 = x2
                detection.y2 = y2
    
    return detections[:len(fixed_boxes)]  # Return only valid detections


if __name__ == "__main__":
    # Test the coordinate fix
    import numpy as np
    
    # Test with normalized coordinates (common Windows issue)
    test_boxes = [
        (0.1, 0.2, 0.5, 0.8),  # Normalized coordinates
        (50, 100, 200, 400),   # Pixel coordinates
    ]
    
    fix = WindowsCoordinateFix()
    fixed = fix.fix_coordinates(test_boxes, 640, 480)
    
    print("Original boxes:", test_boxes)
    print("Fixed boxes:", fixed)
