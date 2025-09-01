"""Unit tests for HumanDetector component."""

import unittest
from unittest.mock import Mock, patch, MagicMock
import numpy as np
import logging
from drone_detection.human_detector import HumanDetector
from drone_detection.models import DetectionResult


class TestHumanDetector(unittest.TestCase):
    """Test cases for HumanDetector class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.detector = HumanDetector(confidence_threshold=0.5)
        
        # Create a mock frame
        self.mock_frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        
        # Disable logging during tests
        logging.disable(logging.CRITICAL)
    
    def tearDown(self):
        """Clean up after tests."""
        logging.disable(logging.NOTSET)
    
    def test_init_default_values(self):
        """Test HumanDetector initialization with default values."""
        detector = HumanDetector()
        self.assertEqual(detector.confidence_threshold, 0.5)
        self.assertIsNone(detector.model)
        self.assertFalse(detector.is_loaded)
        self.assertEqual(detector.PERSON_CLASS_ID, 0)
        self.assertEqual(detector.PERSON_CLASS_NAME, "person")
    
    def test_init_custom_threshold(self):
        """Test HumanDetector initialization with custom threshold."""
        detector = HumanDetector(confidence_threshold=0.7)
        self.assertEqual(detector.confidence_threshold, 0.7)
    
    @patch('drone_detection.human_detector.YOLO')
    def test_load_model_success(self, mock_yolo):
        """Test successful model loading."""
        mock_model = Mock()
        mock_yolo.return_value = mock_model
        
        result = self.detector.load_model("yolov8n.pt")
        
        self.assertTrue(result)
        self.assertTrue(self.detector.is_loaded)
        self.assertEqual(self.detector.model, mock_model)
        mock_yolo.assert_called_once_with("yolov8n.pt")
    
    @patch('drone_detection.human_detector.YOLO')
    def test_load_model_failure(self, mock_yolo):
        """Test model loading failure."""
        mock_yolo.side_effect = Exception("Model not found")
        
        result = self.detector.load_model("invalid_model.pt")
        
        self.assertFalse(result)
        self.assertFalse(self.detector.is_loaded)
        self.assertIsNone(self.detector.model)
    
    def test_detect_humans_model_not_loaded(self):
        """Test detection when model is not loaded."""
        result = self.detector.detect_humans(self.mock_frame)
        
        self.assertEqual(result, [])
    
    def test_detect_humans_invalid_frame(self):
        """Test detection with invalid frame."""
        self.detector.is_loaded = True
        self.detector.model = Mock()
        
        # Test with None frame
        result = self.detector.detect_humans(None)
        self.assertEqual(result, [])
        
        # Test with empty frame
        empty_frame = np.array([])
        result = self.detector.detect_humans(empty_frame)
        self.assertEqual(result, [])
    
    @patch('drone_detection.human_detector.YOLO')
    def test_detect_humans_success(self, mock_yolo):
        """Test successful human detection."""
        # Set up mock model and results
        mock_model = Mock()
        mock_yolo.return_value = mock_model
        
        # Create mock detection results
        mock_result = Mock()
        mock_boxes = Mock()
        mock_boxes.xyxy.cpu.return_value.numpy.return_value = np.array([[100, 100, 200, 300]])
        mock_boxes.conf.cpu.return_value.numpy.return_value = np.array([0.8])
        mock_boxes.cls.cpu.return_value.numpy.return_value.astype.return_value = np.array([0])
        mock_result.boxes = mock_boxes
        
        mock_model.return_value = [mock_result]
        
        # Load model and run detection
        self.detector.load_model("yolov8n.pt")
        result = self.detector.detect_humans(self.mock_frame)
        
        # Verify results
        self.assertEqual(len(result), 1)
        detection = result[0]
        self.assertIsInstance(detection, DetectionResult)
        self.assertEqual(detection.bbox, (100, 100, 200, 300))
        self.assertEqual(detection.confidence, 0.8)
        self.assertEqual(detection.class_id, 0)
        self.assertEqual(detection.class_name, "person")
    
    @patch('drone_detection.human_detector.YOLO')
    def test_detect_humans_processing_error(self, mock_yolo):
        """Test detection with processing error."""
        mock_model = Mock()
        mock_model.side_effect = Exception("Processing error")
        mock_yolo.return_value = mock_model
        
        self.detector.load_model("yolov8n.pt")
        result = self.detector.detect_humans(self.mock_frame)
        
        self.assertEqual(result, [])
    
    def test_filter_detections_no_boxes(self):
        """Test filtering when no boxes are detected."""
        mock_detections = Mock()
        mock_detections.boxes = None
        
        result = self.detector.filter_detections(mock_detections)
        
        self.assertEqual(result, [])
    
    def test_filter_detections_human_above_threshold(self):
        """Test filtering human detections above confidence threshold."""
        mock_detections = Mock()
        mock_boxes = Mock()
        
        # Mock detection data - human with high confidence
        mock_boxes.xyxy.cpu.return_value.numpy.return_value = np.array([[50, 60, 150, 200]])
        mock_boxes.conf.cpu.return_value.numpy.return_value = np.array([0.9])
        mock_boxes.cls.cpu.return_value.numpy.return_value.astype.return_value = np.array([0])
        
        mock_detections.boxes = mock_boxes
        
        result = self.detector.filter_detections(mock_detections)
        
        self.assertEqual(len(result), 1)
        detection = result[0]
        self.assertEqual(detection.bbox, (50, 60, 150, 200))
        self.assertEqual(detection.confidence, 0.9)
        self.assertEqual(detection.class_id, 0)
        self.assertEqual(detection.class_name, "person")
    
    def test_filter_detections_human_below_threshold(self):
        """Test filtering human detections below confidence threshold."""
        mock_detections = Mock()
        mock_boxes = Mock()
        
        # Mock detection data - human with low confidence
        mock_boxes.xyxy.cpu.return_value.numpy.return_value = np.array([[50, 60, 150, 200]])
        mock_boxes.conf.cpu.return_value.numpy.return_value = np.array([0.3])  # Below 0.5 threshold
        mock_boxes.cls.cpu.return_value.numpy.return_value.astype.return_value = np.array([0])
        
        mock_detections.boxes = mock_boxes
        
        result = self.detector.filter_detections(mock_detections)
        
        self.assertEqual(len(result), 0)
    
    def test_filter_detections_non_human_class(self):
        """Test filtering non-human detections."""
        mock_detections = Mock()
        mock_boxes = Mock()
        
        # Mock detection data - car (class_id = 2) with high confidence
        mock_boxes.xyxy.cpu.return_value.numpy.return_value = np.array([[50, 60, 150, 200]])
        mock_boxes.conf.cpu.return_value.numpy.return_value = np.array([0.9])
        mock_boxes.cls.cpu.return_value.numpy.return_value.astype.return_value = np.array([2])
        
        mock_detections.boxes = mock_boxes
        
        result = self.detector.filter_detections(mock_detections)
        
        self.assertEqual(len(result), 0)
    
    def test_filter_detections_multiple_humans(self):
        """Test filtering multiple human detections."""
        mock_detections = Mock()
        mock_boxes = Mock()
        
        # Mock detection data - multiple humans with different confidences
        mock_boxes.xyxy.cpu.return_value.numpy.return_value = np.array([
            [50, 60, 150, 200],   # Human 1
            [200, 100, 300, 250], # Human 2
            [400, 150, 500, 300]  # Human 3
        ])
        mock_boxes.conf.cpu.return_value.numpy.return_value = np.array([0.8, 0.6, 0.3])  # Third below threshold
        mock_boxes.cls.cpu.return_value.numpy.return_value.astype.return_value = np.array([0, 0, 0])
        
        mock_detections.boxes = mock_boxes
        
        result = self.detector.filter_detections(mock_detections)
        
        # Should only return first two detections (above threshold)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].bbox, (50, 60, 150, 200))
        self.assertEqual(result[0].confidence, 0.8)
        self.assertEqual(result[1].bbox, (200, 100, 300, 250))
        self.assertEqual(result[1].confidence, 0.6)
    
    def test_filter_detections_processing_error(self):
        """Test filtering with processing error."""
        mock_detections = Mock()
        mock_boxes = Mock()
        mock_boxes.xyxy.cpu.side_effect = Exception("Processing error")
        mock_detections.boxes = mock_boxes
        
        result = self.detector.filter_detections(mock_detections)
        
        self.assertEqual(result, [])
    
    def test_get_confidence_threshold(self):
        """Test getting confidence threshold."""
        self.assertEqual(self.detector.get_confidence_threshold(), 0.5)
        
        detector_custom = HumanDetector(confidence_threshold=0.7)
        self.assertEqual(detector_custom.get_confidence_threshold(), 0.7)
    
    def test_set_confidence_threshold_valid(self):
        """Test setting valid confidence threshold."""
        self.detector.set_confidence_threshold(0.8)
        self.assertEqual(self.detector.confidence_threshold, 0.8)
        
        self.detector.set_confidence_threshold(0.0)
        self.assertEqual(self.detector.confidence_threshold, 0.0)
        
        self.detector.set_confidence_threshold(1.0)
        self.assertEqual(self.detector.confidence_threshold, 1.0)
    
    def test_set_confidence_threshold_invalid(self):
        """Test setting invalid confidence threshold."""
        original_threshold = self.detector.confidence_threshold
        
        # Test values outside valid range
        self.detector.set_confidence_threshold(-0.1)
        self.assertEqual(self.detector.confidence_threshold, original_threshold)
        
        self.detector.set_confidence_threshold(1.1)
        self.assertEqual(self.detector.confidence_threshold, original_threshold)
    
    def test_is_model_loaded_false(self):
        """Test is_model_loaded when model is not loaded."""
        self.assertFalse(self.detector.is_model_loaded())
    
    @patch('drone_detection.human_detector.YOLO')
    def test_is_model_loaded_true(self, mock_yolo):
        """Test is_model_loaded when model is loaded."""
        mock_model = Mock()
        mock_yolo.return_value = mock_model
        
        self.detector.load_model("yolov8n.pt")
        self.assertTrue(self.detector.is_model_loaded())


if __name__ == '__main__':
    unittest.main()