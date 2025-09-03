"""Human detection using YOLOv8 model."""

import numpy as np
import logging
try:
    # Avoid importing heavy ML libraries at module import time in test environments.
    from ultralytics import YOLO  # type: ignore
except Exception:
    YOLO = None
from typing import List, Optional
from .models import DetectionResult


class HumanDetector:
    """Handles YOLOv8 model loading and human detection processing."""
    
    # COCO dataset class ID for person
    PERSON_CLASS_ID = 0
    PERSON_CLASS_NAME = "person"
    
    def __init__(self, confidence_threshold: float = 0.5):
        self.model = None
        self.confidence_threshold = confidence_threshold
        self.is_loaded = False
        self.logger = logging.getLogger(__name__)
    
    def load_model(self, model_path: str = "yolov8n.pt") -> bool:
        """
        Loads the YOLOv8 model.
        
        Args:
            model_path: Path to the YOLOv8 model file
            
        Returns:
            bool: True if model loaded successfully, False otherwise
        """
        try:
            self.logger.info(f"Loading YOLOv8 model from {model_path}")
            if YOLO is None:
                # Attempt to import lazily now
                try:
                    from ultralytics import YOLO as _YOLO  # type: ignore
                    self.model = _YOLO(model_path)
                except Exception as ie:
                    self.logger.error(f"Failed to import ultralytics.YOLO: {ie}")
                    self.is_loaded = False
                    return False
            else:
                self.model = YOLO(model_path)

            self.is_loaded = True
            self.logger.info("YOLOv8 model loaded successfully")
            return True
        except Exception as e:
            self.logger.error(f"Failed to load YOLOv8 model: {str(e)}")
            self.is_loaded = False
            return False
    
    def detect_humans(self, frame: np.ndarray) -> List[DetectionResult]:
        """
        Processes frame and returns detection results for humans only.
        
        Args:
            frame: Input video frame as numpy array
            
        Returns:
            List[DetectionResult]: List of human detection results
        """
        if not self.is_loaded or self.model is None:
            self.logger.warning("Model not loaded, cannot perform detection")
            return []
        
        if frame is None or frame.size == 0:
            self.logger.warning("Invalid frame provided for detection")
            return []
        
        try:
            # Store original frame dimensions for coordinate scaling
            original_height, original_width = frame.shape[:2]
            self.logger.debug(f"Processing frame: {original_width}x{original_height}")
            
            # Run YOLOv8 inference on the frame
            # YOLOv8 automatically handles resizing and coordinate scaling
            results = self.model(frame, verbose=False)
            
            # Filter and convert detections to our format
            human_detections = self.filter_detections(results[0], original_width, original_height)
            
            self.logger.debug(f"Detected {len(human_detections)} humans in frame")
            return human_detections
            
        except Exception as e:
            self.logger.error(f"Error during detection processing: {str(e)}")
            return []
    
    def filter_detections(self, detections, frame_width: int, frame_height: int) -> List[DetectionResult]:
        """
        Filters results for human class only and applies confidence threshold.
        
        Args:
            detections: Raw YOLOv8 detection results
            frame_width: Original frame width for coordinate validation
            frame_height: Original frame height for coordinate validation
            
        Returns:
            List[DetectionResult]: Filtered human detection results
        """
        human_detections = []
        
        if detections.boxes is None:
            return human_detections
        
        try:
            # Extract detection data
            boxes = detections.boxes.xyxy.cpu().numpy()  # x1, y1, x2, y2
            confidences = detections.boxes.conf.cpu().numpy()
            class_ids = detections.boxes.cls.cpu().numpy().astype(int)
            
            self.logger.debug(f"Raw detections: {len(boxes)} boxes found for frame {frame_width}x{frame_height}")
            
            # Check if coordinates might be normalized (0-1 range) vs pixel coordinates
            if len(boxes) > 0:
                max_coord = np.max(boxes)
                self.logger.debug(f"Maximum coordinate value: {max_coord}")
                if max_coord <= 1.0:
                    self.logger.warning("Coordinates appear to be normalized (0-1), but YOLOv8 should return pixel coordinates")
            
            # Apply Windows coordinate fix if needed
            from .windows_coordinate_fix import WindowsCoordinateFix
            coordinate_fix = WindowsCoordinateFix()
            
            # Filter for human detections with sufficient confidence
            for i, (box, confidence, class_id) in enumerate(zip(boxes, confidences, class_ids)):
                if (class_id == self.PERSON_CLASS_ID and 
                    confidence >= self.confidence_threshold):
                    
                    # Debug: Log raw coordinates before processing
                    x1, y1, x2, y2 = box
                    self.logger.debug(f"Raw detection {i}: bbox=({x1:.2f}, {y1:.2f}, {x2:.2f}, {y2:.2f}), conf={confidence:.3f}")
                    
                    # Apply coordinate fix (handles scaling and Windows-specific issues)
                    fixed_boxes = coordinate_fix.fix_coordinates([(x1, y1, x2, y2)], frame_width, frame_height)
                    
                    if not fixed_boxes:
                        self.logger.warning(f"Detection {i} rejected by coordinate fix")
                        continue
                        
                    x1, y1, x2, y2 = fixed_boxes[0]
                    self.logger.debug(f"Fixed detection {i}: bbox=({x1}, {y1}, {x2}, {y2})")
                    
                    # Validate bounding box dimensions
                    if x2 > x1 and y2 > y1:
                        self.logger.debug(f"Final detection {i}: bbox=({x1}, {y1}, {x2}, {y2}), size=({x2-x1}x{y2-y1}), conf={confidence:.3f}")
                        
                        detection = DetectionResult(
                            bbox=(x1, y1, x2, y2),
                            confidence=float(confidence),
                            class_id=class_id,
                            class_name=self.PERSON_CLASS_NAME
                        )
                        # Attach raw bbox as reported by the model for debugging
                        detection.raw_bbox = (float(box[0]), float(box[1]), float(box[2]), float(box[3]))
                        
                        human_detections.append(detection)
                    else:
                        self.logger.warning(f"Invalid bounding box detected: ({x1}, {y1}, {x2}, {y2})")
            
        except Exception as e:
            self.logger.error(f"Error filtering detections: {str(e)}")
        
        return human_detections
    
    def get_confidence_threshold(self) -> float:
        """Returns current confidence threshold."""
        return self.confidence_threshold
    
    def set_confidence_threshold(self, threshold: float):
        """
        Sets confidence threshold for detections.
        
        Args:
            threshold: New confidence threshold (0.0 to 1.0)
        """
        if 0.0 <= threshold <= 1.0:
            self.confidence_threshold = threshold
            self.logger.info(f"Confidence threshold set to {threshold}")
        else:
            self.logger.warning(f"Invalid confidence threshold {threshold}, must be between 0.0 and 1.0")
    
    def is_model_loaded(self) -> bool:
        """
        Check if the model is loaded and ready for detection.
        
        Returns:
            bool: True if model is loaded, False otherwise
        """
        return self.is_loaded and self.model is not None