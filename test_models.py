"""Unit tests for data models in the drone human detection system."""

import unittest
from dataclasses import asdict
from drone_detection.models import DetectionResult, CameraConfig, AppState


class TestDetectionResult(unittest.TestCase):
    """Test cases for DetectionResult dataclass."""
    
    def test_detection_result_creation(self):
        """Test creating a DetectionResult with valid data."""
        result = DetectionResult(
            bbox=(100, 200, 300, 400),
            confidence=0.85,
            class_id=0,
            class_name="person"
        )
        
        self.assertEqual(result.bbox, (100, 200, 300, 400))
        self.assertEqual(result.confidence, 0.85)
        self.assertEqual(result.class_id, 0)
        self.assertEqual(result.class_name, "person")
    
    def test_detection_result_serialization(self):
        """Test serializing DetectionResult to dictionary."""
        result = DetectionResult(
            bbox=(50, 75, 150, 225),
            confidence=0.92,
            class_id=0,
            class_name="person"
        )
        
        expected_dict = {
            'bbox': (50, 75, 150, 225),
            'confidence': 0.92,
            'class_id': 0,
            'class_name': 'person'
        }
        
        self.assertEqual(asdict(result), expected_dict)
    
    def test_detection_result_validation(self):
        """Test DetectionResult field validation."""
        # Test with valid confidence range
        result = DetectionResult(
            bbox=(0, 0, 100, 100),
            confidence=0.5,
            class_id=0,
            class_name="person"
        )
        self.assertTrue(0.0 <= result.confidence <= 1.0)
        
        # Test bbox coordinates are integers
        self.assertIsInstance(result.bbox[0], int)
        self.assertIsInstance(result.bbox[1], int)
        self.assertIsInstance(result.bbox[2], int)
        self.assertIsInstance(result.bbox[3], int)


class TestCameraConfig(unittest.TestCase):
    """Test cases for CameraConfig dataclass."""
    
    def test_camera_config_creation(self):
        """Test creating a CameraConfig with valid data."""
        config = CameraConfig(
            source_type="laptop",
            device_id=0,
            resolution=(640, 480),
            fps=30,
            connection_timeout=5.0
        )
        
        self.assertEqual(config.source_type, "laptop")
        self.assertEqual(config.device_id, 0)
        self.assertEqual(config.resolution, (640, 480))
        self.assertEqual(config.fps, 30)
        self.assertEqual(config.connection_timeout, 5.0)
    
    def test_camera_config_serialization(self):
        """Test serializing CameraConfig to dictionary."""
        config = CameraConfig(
            source_type="drone",
            device_id=1,
            resolution=(1280, 720),
            fps=25,
            connection_timeout=10.0
        )
        
        expected_dict = {
            'source_type': 'drone',
            'device_id': 1,
            'resolution': (1280, 720),
            'fps': 25,
            'connection_timeout': 10.0
        }
        
        self.assertEqual(asdict(config), expected_dict)
    
    def test_camera_config_validation(self):
        """Test CameraConfig field validation."""
        config = CameraConfig(
            source_type="laptop",
            device_id=0,
            resolution=(640, 480),
            fps=30,
            connection_timeout=5.0
        )
        
        # Test source_type is valid
        self.assertIn(config.source_type, ["laptop", "drone"])
        
        # Test device_id is non-negative
        self.assertGreaterEqual(config.device_id, 0)
        
        # Test fps is positive
        self.assertGreater(config.fps, 0)
        
        # Test connection_timeout is positive
        self.assertGreater(config.connection_timeout, 0.0)
        
        # Test resolution contains positive integers
        self.assertGreater(config.resolution[0], 0)
        self.assertGreater(config.resolution[1], 0)


class TestAppState(unittest.TestCase):
    """Test cases for AppState dataclass."""
    
    def test_app_state_creation(self):
        """Test creating an AppState with valid data."""
        state = AppState(
            is_running=True,
            current_camera="laptop",
            detection_enabled=True,
            fps_counter=25.5,
            error_message=None
        )
        
        self.assertTrue(state.is_running)
        self.assertEqual(state.current_camera, "laptop")
        self.assertTrue(state.detection_enabled)
        self.assertEqual(state.fps_counter, 25.5)
        self.assertIsNone(state.error_message)
    
    def test_app_state_with_error(self):
        """Test creating an AppState with error message."""
        state = AppState(
            is_running=False,
            current_camera="drone",
            detection_enabled=False,
            fps_counter=0.0,
            error_message="Camera connection failed"
        )
        
        self.assertFalse(state.is_running)
        self.assertEqual(state.current_camera, "drone")
        self.assertFalse(state.detection_enabled)
        self.assertEqual(state.fps_counter, 0.0)
        self.assertEqual(state.error_message, "Camera connection failed")
    
    def test_app_state_serialization(self):
        """Test serializing AppState to dictionary."""
        state = AppState(
            is_running=True,
            current_camera="laptop",
            detection_enabled=True,
            fps_counter=30.0,
            error_message=None
        )
        
        expected_dict = {
            'is_running': True,
            'current_camera': 'laptop',
            'detection_enabled': True,
            'fps_counter': 30.0,
            'error_message': None
        }
        
        self.assertEqual(asdict(state), expected_dict)
    
    def test_app_state_validation(self):
        """Test AppState field validation."""
        state = AppState(
            is_running=True,
            current_camera="laptop",
            detection_enabled=True,
            fps_counter=15.0,
            error_message=None
        )
        
        # Test boolean fields
        self.assertIsInstance(state.is_running, bool)
        self.assertIsInstance(state.detection_enabled, bool)
        
        # Test fps_counter is non-negative
        self.assertGreaterEqual(state.fps_counter, 0.0)
        
        # Test current_camera is valid
        self.assertIn(state.current_camera, ["laptop", "drone"])


if __name__ == '__main__':
    unittest.main()