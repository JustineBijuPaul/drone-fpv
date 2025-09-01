"""Unit tests for CameraManager component."""

import unittest
from unittest.mock import Mock, patch, MagicMock
import numpy as np
import cv2
import time
from drone_detection.camera_manager import CameraManager
from drone_detection.models import CameraConfig


class TestCameraManager(unittest.TestCase):
    """Test cases for CameraManager class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.camera_manager = CameraManager()
        
        # Test configurations
        self.laptop_config = CameraConfig(
            source_type='laptop',
            device_id=0,
            resolution=(640, 480),
            fps=30,
            connection_timeout=5.0
        )
        
        self.drone_config = CameraConfig(
            source_type='drone',
            device_id=1,
            resolution=(1280, 720),
            fps=25,
            connection_timeout=10.0
        )
    
    def tearDown(self):
        """Clean up after tests."""
        if self.camera_manager:
            self.camera_manager.release()
    
    @patch('cv2.VideoCapture')
    def test_initialize_laptop_camera_success(self, mock_video_capture):
        """Test successful laptop camera initialization."""
        # Mock successful camera
        mock_camera = Mock()
        mock_camera.isOpened.return_value = True
        mock_camera.read.return_value = (True, np.zeros((480, 640, 3), dtype=np.uint8))
        mock_video_capture.return_value = mock_camera
        
        # Mock camera detection
        with patch.object(self.camera_manager, '_detect_laptop_cameras', return_value=[0, 1]):
            result = self.camera_manager.initialize_camera(self.laptop_config)
        
        self.assertTrue(result)
        self.assertTrue(self.camera_manager.is_initialized)
        self.assertEqual(self.camera_manager.config, self.laptop_config)
        mock_video_capture.assert_called_with(0)
    
    @patch('cv2.VideoCapture')
    def test_initialize_laptop_camera_no_cameras_detected(self, mock_video_capture):
        """Test laptop camera initialization when no cameras are detected."""
        # Mock camera detection returning empty list
        with patch.object(self.camera_manager, '_detect_laptop_cameras', return_value=[]):
            result = self.camera_manager.initialize_camera(self.laptop_config)
        
        self.assertFalse(result)
        self.assertFalse(self.camera_manager.is_initialized)
    
    @patch('cv2.VideoCapture')
    def test_initialize_laptop_camera_failed_to_open(self, mock_video_capture):
        """Test laptop camera initialization when camera fails to open."""
        # Mock failed camera
        mock_camera = Mock()
        mock_camera.isOpened.return_value = False
        mock_video_capture.return_value = mock_camera
        
        with patch.object(self.camera_manager, '_detect_laptop_cameras', return_value=[0]):
            result = self.camera_manager.initialize_camera(self.laptop_config)
        
        self.assertFalse(result)
        self.assertFalse(self.camera_manager.is_initialized)
    
    @patch('cv2.VideoCapture')
    def test_initialize_drone_camera_success(self, mock_video_capture):
        """Test successful drone camera initialization."""
        # Mock successful camera
        mock_camera = Mock()
        mock_camera.isOpened.return_value = True
        mock_camera.read.return_value = (True, np.zeros((720, 1280, 3), dtype=np.uint8))
        mock_video_capture.return_value = mock_camera
        
        result = self.camera_manager.initialize_camera(self.drone_config)
        
        self.assertTrue(result)
        self.assertTrue(self.camera_manager.is_initialized)
        self.assertEqual(self.camera_manager.config, self.drone_config)
    
    @patch('cv2.VideoCapture')
    def test_initialize_drone_camera_all_methods_fail(self, mock_video_capture):
        """Test drone camera initialization when all connection methods fail."""
        # Mock failed camera for all attempts
        mock_camera = Mock()
        mock_camera.isOpened.return_value = False
        mock_video_capture.return_value = mock_camera
        
        result = self.camera_manager.initialize_camera(self.drone_config)
        
        self.assertFalse(result)
        self.assertFalse(self.camera_manager.is_initialized)
    
    def test_initialize_unknown_source_type(self):
        """Test initialization with unknown source type."""
        unknown_config = CameraConfig(
            source_type='unknown',
            device_id=0,
            resolution=(640, 480),
            fps=30,
            connection_timeout=5.0
        )
        
        result = self.camera_manager.initialize_camera(unknown_config)
        
        self.assertFalse(result)
        self.assertFalse(self.camera_manager.is_initialized)
    
    @patch('cv2.VideoCapture')
    def test_detect_laptop_cameras(self, mock_video_capture):
        """Test laptop camera detection."""
        # Mock cameras at indices 0 and 2
        def mock_camera_side_effect(index):
            mock_camera = Mock()
            if index in [0, 2]:
                mock_camera.isOpened.return_value = True
                mock_camera.read.return_value = (True, np.zeros((480, 640, 3), dtype=np.uint8))
            else:
                mock_camera.isOpened.return_value = False
                mock_camera.read.return_value = (False, None)
            return mock_camera
        
        mock_video_capture.side_effect = mock_camera_side_effect
        
        cameras = self.camera_manager._detect_laptop_cameras()
        
        self.assertEqual(cameras, [0, 2])
        self.assertEqual(mock_video_capture.call_count, 6)  # Tests indices 0-5
    
    @patch('cv2.VideoCapture')
    def test_get_frame_success(self, mock_video_capture):
        """Test successful frame retrieval."""
        # Setup initialized camera
        mock_camera = Mock()
        mock_camera.isOpened.return_value = True
        test_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        mock_camera.read.return_value = (True, test_frame)
        mock_video_capture.return_value = mock_camera
        
        with patch.object(self.camera_manager, '_detect_laptop_cameras', return_value=[0]):
            self.camera_manager.initialize_camera(self.laptop_config)
        
        frame = self.camera_manager.get_frame()
        
        self.assertIsNotNone(frame)
        np.testing.assert_array_equal(frame, test_frame)
        self.assertEqual(self.camera_manager.connection_attempts, 0)
    
    @patch('cv2.VideoCapture')
    def test_get_frame_not_initialized(self, mock_video_capture):
        """Test frame retrieval when camera is not initialized."""
        frame = self.camera_manager.get_frame()
        
        self.assertIsNone(frame)
    
    @patch('cv2.VideoCapture')
    def test_get_frame_failed_with_reconnect(self, mock_video_capture):
        """Test frame retrieval failure with reconnection attempts."""
        # Setup initialized camera
        mock_camera = Mock()
        mock_camera.isOpened.return_value = True
        mock_camera.read.side_effect = [
            (True, np.zeros((480, 640, 3), dtype=np.uint8)),  # Initial success for setup
            (False, None),  # First failure
            (False, None),  # Second failure  
            (False, None),  # Third failure (triggers reconnect attempt)
        ]
        mock_video_capture.return_value = mock_camera
        
        with patch.object(self.camera_manager, '_detect_laptop_cameras', return_value=[0]):
            self.camera_manager.initialize_camera(self.laptop_config)
        
        # First 3 calls should fail and increment connection attempts
        frame1 = self.camera_manager.get_frame()
        frame2 = self.camera_manager.get_frame()
        frame3 = self.camera_manager.get_frame()
        
        self.assertIsNone(frame1)
        self.assertIsNone(frame2)
        self.assertIsNone(frame3)
        self.assertEqual(self.camera_manager.connection_attempts, 3)
    
    @patch('cv2.VideoCapture')
    def test_switch_source_success(self, mock_video_capture):
        """Test successful camera source switching."""
        # Mock cameras
        mock_camera = Mock()
        mock_camera.isOpened.return_value = True
        mock_camera.read.return_value = (True, np.zeros((480, 640, 3), dtype=np.uint8))
        mock_video_capture.return_value = mock_camera
        
        # Initialize with laptop camera
        with patch.object(self.camera_manager, '_detect_laptop_cameras', return_value=[0]):
            self.camera_manager.initialize_camera(self.laptop_config)
        
        # Switch to drone camera
        result = self.camera_manager.switch_source(self.drone_config)
        
        self.assertTrue(result)
        self.assertEqual(self.camera_manager.config, self.drone_config)
        self.assertTrue(self.camera_manager.is_initialized)
    
    @patch('cv2.VideoCapture')
    def test_switch_source_failure(self, mock_video_capture):
        """Test camera source switching failure."""
        # Mock successful initial camera
        mock_camera1 = Mock()
        mock_camera1.isOpened.return_value = True
        mock_camera1.read.return_value = (True, np.zeros((480, 640, 3), dtype=np.uint8))
        
        # Mock failed new camera
        mock_camera2 = Mock()
        mock_camera2.isOpened.return_value = False
        
        mock_video_capture.side_effect = [mock_camera1, mock_camera2]
        
        # Initialize with laptop camera
        with patch.object(self.camera_manager, '_detect_laptop_cameras', return_value=[0]):
            self.camera_manager.initialize_camera(self.laptop_config)
        
        # Try to switch to drone camera (should fail)
        result = self.camera_manager.switch_source(self.drone_config)
        
        self.assertFalse(result)
        self.assertFalse(self.camera_manager.is_initialized)
    
    @patch('cv2.VideoCapture')
    def test_is_connected_true(self, mock_video_capture):
        """Test connection status check when connected."""
        # Setup initialized camera
        mock_camera = Mock()
        mock_camera.isOpened.return_value = True
        mock_camera.read.return_value = (True, np.zeros((480, 640, 3), dtype=np.uint8))
        mock_video_capture.return_value = mock_camera
        
        with patch.object(self.camera_manager, '_detect_laptop_cameras', return_value=[0]):
            self.camera_manager.initialize_camera(self.laptop_config)
        
        # Set recent frame time
        self.camera_manager.last_frame_time = time.time()
        
        result = self.camera_manager.is_connected()
        
        self.assertTrue(result)
    
    @patch('cv2.VideoCapture')
    def test_is_connected_false_not_initialized(self, mock_video_capture):
        """Test connection status check when not initialized."""
        result = self.camera_manager.is_connected()
        
        self.assertFalse(result)
    
    @patch('cv2.VideoCapture')
    def test_is_connected_false_camera_not_opened(self, mock_video_capture):
        """Test connection status check when camera is not opened."""
        # Setup camera that becomes unopened
        mock_camera = Mock()
        # First calls for initialization, then False for is_connected check
        mock_camera.isOpened.side_effect = [True, True, True, False]
        mock_camera.read.return_value = (True, np.zeros((480, 640, 3), dtype=np.uint8))
        mock_video_capture.return_value = mock_camera
        
        with patch.object(self.camera_manager, '_detect_laptop_cameras', return_value=[0]):
            self.camera_manager.initialize_camera(self.laptop_config)
        
        result = self.camera_manager.is_connected()
        
        self.assertFalse(result)
    
    @patch('cv2.VideoCapture')
    def test_get_camera_info(self, mock_video_capture):
        """Test camera information retrieval."""
        # Setup initialized camera
        mock_camera = Mock()
        mock_camera.isOpened.return_value = True
        mock_camera.read.return_value = (True, np.zeros((480, 640, 3), dtype=np.uint8))
        mock_camera.get.side_effect = lambda prop: {
            cv2.CAP_PROP_FRAME_WIDTH: 640,
            cv2.CAP_PROP_FRAME_HEIGHT: 480,
            cv2.CAP_PROP_FPS: 30
        }.get(prop, 0)
        mock_video_capture.return_value = mock_camera
        
        with patch.object(self.camera_manager, '_detect_laptop_cameras', return_value=[0]):
            self.camera_manager.initialize_camera(self.laptop_config)
        
        info = self.camera_manager.get_camera_info()
        
        expected_info = {
            'source_type': 'laptop',
            'device_id': 0,
            'is_opened': True,
            'width': 640,
            'height': 480,
            'fps': 30,
            'connection_attempts': 0
        }
        
        self.assertEqual(info, expected_info)
    
    def test_get_camera_info_not_initialized(self):
        """Test camera information retrieval when not initialized."""
        info = self.camera_manager.get_camera_info()
        
        self.assertEqual(info, {})
    
    @patch('cv2.VideoCapture')
    def test_release(self, mock_video_capture):
        """Test camera resource release."""
        # Setup initialized camera
        mock_camera = Mock()
        mock_camera.isOpened.return_value = True
        mock_camera.read.return_value = (True, np.zeros((480, 640, 3), dtype=np.uint8))
        mock_video_capture.return_value = mock_camera
        
        with patch.object(self.camera_manager, '_detect_laptop_cameras', return_value=[0]):
            self.camera_manager.initialize_camera(self.laptop_config)
        
        self.camera_manager.release()
        
        mock_camera.release.assert_called_once()
        self.assertIsNone(self.camera_manager.current_camera)
        self.assertFalse(self.camera_manager.is_initialized)
        self.assertIsNone(self.camera_manager.config)
    
    @patch('cv2.VideoCapture')
    def test_configure_camera_settings(self, mock_video_capture):
        """Test camera settings configuration."""
        mock_camera = Mock()
        mock_camera.isOpened.return_value = True
        mock_camera.read.return_value = (True, np.zeros((480, 640, 3), dtype=np.uint8))
        mock_video_capture.return_value = mock_camera
        
        with patch.object(self.camera_manager, '_detect_laptop_cameras', return_value=[0]):
            self.camera_manager.initialize_camera(self.laptop_config)
        
        # Verify camera settings were configured
        mock_camera.set.assert_any_call(cv2.CAP_PROP_FRAME_WIDTH, 640)
        mock_camera.set.assert_any_call(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        mock_camera.set.assert_any_call(cv2.CAP_PROP_FPS, 30)
        mock_camera.set.assert_any_call(cv2.CAP_PROP_BUFFERSIZE, 1)


if __name__ == '__main__':
    unittest.main()