"""Integration tests for MainController complete processing pipeline."""

import unittest
from unittest.mock import Mock, patch, MagicMock
import numpy as np
import time
import threading
from drone_detection.main_controller import MainController
from drone_detection.models import DetectionResult, CameraConfig, AppState


class TestMainControllerIntegration(unittest.TestCase):
    """Integration tests for the complete processing pipeline."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.controller = MainController()
        
        # Create test frame
        self.test_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        
        # Create test detection results
        self.test_detections = [
            DetectionResult(
                bbox=(100, 100, 200, 300),
                confidence=0.85,
                class_id=0,
                class_name="person"
            ),
            DetectionResult(
                bbox=(300, 150, 400, 350),
                confidence=0.72,
                class_id=0,
                class_name="person"
            )
        ]
    
    def tearDown(self):
        """Clean up after tests."""
        if hasattr(self.controller, 'app_state'):
            self.controller.app_state.is_running = False
    
    @patch('drone_detection.main_controller.CameraManager')
    @patch('drone_detection.main_controller.HumanDetector')
    @patch('drone_detection.main_controller.DisplayManager')
    def test_complete_pipeline_integration(self, mock_display, mock_detector, mock_camera):
        """Test the complete camera → detection → display pipeline."""
        # Setup camera manager mock
        mock_camera_instance = Mock()
        mock_camera_instance.initialize_camera.return_value = True
        mock_camera_instance.is_connected.return_value = True
        mock_camera_instance.get_frame.return_value = self.test_frame
        mock_camera.return_value = mock_camera_instance
        
        # Setup human detector mock
        mock_detector_instance = Mock()
        mock_detector_instance.load_model.return_value = True
        mock_detector_instance.detect_humans.return_value = self.test_detections
        mock_detector.return_value = mock_detector_instance
        
        # Setup display manager mock
        mock_display_instance = Mock()
        mock_display_instance.display_frame.return_value = True
        mock_display_instance.get_fps.return_value = 30.0
        mock_display.return_value = mock_display_instance
        
        # Initialize components
        self.assertTrue(self.controller.initialize_components())
        
        # Process a single frame through the complete pipeline
        result = self.controller.process_frame()
        
        # Verify the complete pipeline executed
        self.assertTrue(result)
        mock_camera_instance.get_frame.assert_called_once()
        mock_detector_instance.detect_humans.assert_called_once_with(self.test_frame)
        mock_display_instance.display_frame.assert_called_once_with(self.test_frame, self.test_detections)
        
        # Verify app state is updated
        self.assertEqual(self.controller.app_state.fps_counter, 30.0)
    
    @patch('drone_detection.main_controller.CameraManager')
    @patch('drone_detection.main_controller.HumanDetector')
    @patch('drone_detection.main_controller.DisplayManager')
    def test_pipeline_with_no_detections(self, mock_display, mock_detector, mock_camera):
        """Test pipeline when no humans are detected."""
        # Setup mocks with no detections
        mock_camera_instance = Mock()
        mock_camera_instance.initialize_camera.return_value = True
        mock_camera_instance.is_connected.return_value = True
        mock_camera_instance.get_frame.return_value = self.test_frame
        mock_camera.return_value = mock_camera_instance
        
        mock_detector_instance = Mock()
        mock_detector_instance.load_model.return_value = True
        mock_detector_instance.detect_humans.return_value = []  # No detections
        mock_detector.return_value = mock_detector_instance
        
        mock_display_instance = Mock()
        mock_display_instance.display_frame.return_value = True
        mock_display_instance.get_fps.return_value = 25.0
        mock_display.return_value = mock_display_instance
        
        # Initialize and process frame
        self.assertTrue(self.controller.initialize_components())
        result = self.controller.process_frame()
        
        # Verify pipeline executed with empty detections
        self.assertTrue(result)
        mock_display_instance.display_frame.assert_called_once_with(self.test_frame, [])
    
    @patch('drone_detection.main_controller.CameraManager')
    @patch('drone_detection.main_controller.HumanDetector')
    @patch('drone_detection.main_controller.DisplayManager')
    def test_pipeline_with_detection_failure(self, mock_display, mock_detector, mock_camera):
        """Test pipeline when detection fails but continues processing."""
        # Setup mocks with detection failure
        mock_camera_instance = Mock()
        mock_camera_instance.initialize_camera.return_value = True
        mock_camera_instance.is_connected.return_value = True
        mock_camera_instance.get_frame.return_value = self.test_frame
        mock_camera.return_value = mock_camera_instance
        
        mock_detector_instance = Mock()
        mock_detector_instance.load_model.return_value = True
        mock_detector_instance.detect_humans.side_effect = Exception("Detection failed")
        mock_detector.return_value = mock_detector_instance
        
        mock_display_instance = Mock()
        mock_display_instance.display_frame.return_value = True
        mock_display_instance.get_fps.return_value = 20.0
        mock_display.return_value = mock_display_instance
        
        # Initialize and process frame
        self.assertTrue(self.controller.initialize_components())
        result = self.controller.process_frame()
        
        # Verify pipeline continues without detections when detection fails
        self.assertTrue(result)
        mock_display_instance.display_frame.assert_called_once_with(self.test_frame, [])
    
    @patch('drone_detection.main_controller.CameraManager')
    @patch('drone_detection.main_controller.HumanDetector')
    @patch('drone_detection.main_controller.DisplayManager')
    def test_pipeline_with_camera_disconnection(self, mock_display, mock_detector, mock_camera):
        """Test pipeline behavior when camera becomes disconnected."""
        # Setup mocks with camera disconnection
        mock_camera_instance = Mock()
        mock_camera_instance.initialize_camera.return_value = True
        mock_camera_instance.is_connected.return_value = False  # Camera disconnected
        mock_camera.return_value = mock_camera_instance
        
        mock_detector_instance = Mock()
        mock_detector_instance.load_model.return_value = True
        mock_detector.return_value = mock_detector_instance
        
        mock_display_instance = Mock()
        mock_display.return_value = mock_display_instance
        
        # Initialize and process frame
        self.assertTrue(self.controller.initialize_components())
        result = self.controller.process_frame()
        
        # Verify pipeline fails gracefully when camera is disconnected
        self.assertFalse(result)
        mock_camera_instance.get_frame.assert_not_called()
    
    @patch('drone_detection.main_controller.CameraManager')
    @patch('drone_detection.main_controller.HumanDetector')
    @patch('drone_detection.main_controller.DisplayManager')
    def test_pipeline_with_frame_capture_failure(self, mock_display, mock_detector, mock_camera):
        """Test pipeline when frame capture fails."""
        # Setup mocks with frame capture failure
        mock_camera_instance = Mock()
        mock_camera_instance.initialize_camera.return_value = True
        mock_camera_instance.is_connected.return_value = True
        mock_camera_instance.get_frame.return_value = None  # Frame capture failed
        mock_camera.return_value = mock_camera_instance
        
        mock_detector_instance = Mock()
        mock_detector_instance.load_model.return_value = True
        mock_detector.return_value = mock_detector_instance
        
        mock_display_instance = Mock()
        mock_display.return_value = mock_display_instance
        
        # Initialize and process frame
        self.assertTrue(self.controller.initialize_components())
        result = self.controller.process_frame()
        
        # Verify pipeline fails when frame capture fails
        self.assertFalse(result)
        mock_detector_instance.detect_humans.assert_not_called()
        mock_display_instance.display_frame.assert_not_called()
    
    @patch('drone_detection.main_controller.CameraManager')
    @patch('drone_detection.main_controller.HumanDetector')
    @patch('drone_detection.main_controller.DisplayManager')
    def test_pipeline_with_display_failure(self, mock_display, mock_detector, mock_camera):
        """Test pipeline when display fails."""
        # Setup mocks with display failure
        mock_camera_instance = Mock()
        mock_camera_instance.initialize_camera.return_value = True
        mock_camera_instance.is_connected.return_value = True
        mock_camera_instance.get_frame.return_value = self.test_frame
        mock_camera.return_value = mock_camera_instance
        
        mock_detector_instance = Mock()
        mock_detector_instance.load_model.return_value = True
        mock_detector_instance.detect_humans.return_value = self.test_detections
        mock_detector.return_value = mock_detector_instance
        
        mock_display_instance = Mock()
        mock_display_instance.display_frame.side_effect = Exception("Display failed")
        mock_display.return_value = mock_display_instance
        
        # Initialize and process frame
        self.assertTrue(self.controller.initialize_components())
        result = self.controller.process_frame()
        
        # Verify pipeline fails when display fails
        self.assertFalse(result)
    
    @patch('drone_detection.main_controller.CameraManager')
    @patch('drone_detection.main_controller.HumanDetector')
    @patch('drone_detection.main_controller.DisplayManager')
    def test_pipeline_user_closes_window(self, mock_display, mock_detector, mock_camera):
        """Test pipeline when user closes display window."""
        # Setup mocks with user closing window
        mock_camera_instance = Mock()
        mock_camera_instance.initialize_camera.return_value = True
        mock_camera_instance.is_connected.return_value = True
        mock_camera_instance.get_frame.return_value = self.test_frame
        mock_camera.return_value = mock_camera_instance
        
        mock_detector_instance = Mock()
        mock_detector_instance.load_model.return_value = True
        mock_detector_instance.detect_humans.return_value = self.test_detections
        mock_detector.return_value = mock_detector_instance
        
        mock_display_instance = Mock()
        mock_display_instance.display_frame.return_value = False  # User closed window
        mock_display_instance.get_fps.return_value = 30.0
        mock_display.return_value = mock_display_instance
        
        # Initialize and process frame
        self.assertTrue(self.controller.initialize_components())
        result = self.controller.process_frame()
        
        # Verify pipeline handles window closure gracefully
        self.assertTrue(result)
        self.assertFalse(self.controller.app_state.is_running)
    
    @patch('drone_detection.main_controller.CameraManager')
    @patch('drone_detection.main_controller.HumanDetector')
    @patch('drone_detection.main_controller.DisplayManager')
    def test_multiple_frame_processing_sequence(self, mock_display, mock_detector, mock_camera):
        """Test processing multiple frames in sequence."""
        # Setup mocks for multiple frames
        mock_camera_instance = Mock()
        mock_camera_instance.initialize_camera.return_value = True
        mock_camera_instance.is_connected.return_value = True
        mock_camera_instance.get_frame.return_value = self.test_frame
        mock_camera.return_value = mock_camera_instance
        
        mock_detector_instance = Mock()
        mock_detector_instance.load_model.return_value = True
        mock_detector_instance.detect_humans.return_value = self.test_detections
        mock_detector.return_value = mock_detector_instance
        
        mock_display_instance = Mock()
        mock_display_instance.display_frame.return_value = True
        mock_display_instance.get_fps.return_value = 30.0
        mock_display.return_value = mock_display_instance
        
        # Initialize components
        self.assertTrue(self.controller.initialize_components())
        
        # Process multiple frames
        num_frames = 5
        for i in range(num_frames):
            result = self.controller.process_frame()
            self.assertTrue(result)
        
        # Verify all frames were processed
        self.assertEqual(mock_camera_instance.get_frame.call_count, num_frames)
        self.assertEqual(mock_detector_instance.detect_humans.call_count, num_frames)
        self.assertEqual(mock_display_instance.display_frame.call_count, num_frames)
    
    @patch('drone_detection.main_controller.CameraManager')
    @patch('drone_detection.main_controller.HumanDetector')
    @patch('drone_detection.main_controller.DisplayManager')
    def test_pipeline_performance_monitoring(self, mock_display, mock_detector, mock_camera):
        """Test that pipeline performance is properly monitored."""
        # Setup mocks with varying FPS
        mock_camera_instance = Mock()
        mock_camera_instance.initialize_camera.return_value = True
        mock_camera_instance.is_connected.return_value = True
        mock_camera_instance.get_frame.return_value = self.test_frame
        mock_camera.return_value = mock_camera_instance
        
        mock_detector_instance = Mock()
        mock_detector_instance.load_model.return_value = True
        mock_detector_instance.detect_humans.return_value = self.test_detections
        mock_detector.return_value = mock_detector_instance
        
        mock_display_instance = Mock()
        mock_display_instance.display_frame.return_value = True
        mock_display_instance.get_fps.side_effect = [15.0, 20.0, 25.0, 30.0]
        mock_display.return_value = mock_display_instance
        
        # Initialize components
        self.assertTrue(self.controller.initialize_components())
        
        # Process frames and monitor FPS changes
        fps_values = []
        for i in range(4):
            result = self.controller.process_frame()
            self.assertTrue(result)
            fps_values.append(self.controller.app_state.fps_counter)
        
        # Verify FPS monitoring
        expected_fps = [15.0, 20.0, 25.0, 30.0]
        self.assertEqual(fps_values, expected_fps)
    
    @patch('drone_detection.main_controller.CameraManager')
    @patch('drone_detection.main_controller.HumanDetector')
    @patch('drone_detection.main_controller.DisplayManager')
    def test_pipeline_with_detection_disabled(self, mock_display, mock_detector, mock_camera):
        """Test pipeline when detection is disabled."""
        # Setup mocks
        mock_camera_instance = Mock()
        mock_camera_instance.initialize_camera.return_value = True
        mock_camera_instance.is_connected.return_value = True
        mock_camera_instance.get_frame.return_value = self.test_frame
        mock_camera.return_value = mock_camera_instance
        
        mock_detector_instance = Mock()
        mock_detector_instance.load_model.return_value = True
        mock_detector.return_value = mock_detector_instance
        
        mock_display_instance = Mock()
        mock_display_instance.display_frame.return_value = True
        mock_display_instance.get_fps.return_value = 30.0
        mock_display.return_value = mock_display_instance
        
        # Initialize components and disable detection
        self.assertTrue(self.controller.initialize_components())
        self.controller.app_state.detection_enabled = False
        
        # Process frame
        result = self.controller.process_frame()
        
        # Verify pipeline works without detection
        self.assertTrue(result)
        mock_detector_instance.detect_humans.assert_not_called()
        mock_display_instance.display_frame.assert_called_once_with(self.test_frame, [])
    
    @patch('drone_detection.main_controller.CameraManager')
    @patch('drone_detection.main_controller.HumanDetector')
    @patch('drone_detection.main_controller.DisplayManager')
    def test_end_to_end_initialization_and_processing(self, mock_display, mock_detector, mock_camera):
        """Test complete end-to-end initialization and processing flow."""
        # Setup all mocks for successful operation
        mock_camera_instance = Mock()
        mock_camera_instance.initialize_camera.return_value = True
        mock_camera_instance.is_connected.return_value = True
        mock_camera_instance.get_frame.return_value = self.test_frame
        mock_camera.return_value = mock_camera_instance
        
        mock_detector_instance = Mock()
        mock_detector_instance.load_model.return_value = True
        mock_detector_instance.detect_humans.return_value = self.test_detections
        mock_detector.return_value = mock_detector_instance
        
        mock_display_instance = Mock()
        mock_display_instance.display_frame.return_value = True
        mock_display_instance.get_fps.return_value = 30.0
        mock_display.return_value = mock_display_instance
        
        # Test complete flow
        # 1. Initialize components
        init_result = self.controller.initialize_components()
        self.assertTrue(init_result)
        
        # 2. Verify all components are initialized
        self.assertIsNotNone(self.controller.camera_manager)
        self.assertIsNotNone(self.controller.human_detector)
        self.assertIsNotNone(self.controller.display_manager)
        self.assertTrue(self.controller.app_state.detection_enabled)
        
        # 3. Process frames
        for i in range(3):
            frame_result = self.controller.process_frame()
            self.assertTrue(frame_result)
        
        # 4. Verify system status
        status = self.controller.get_system_status()
        self.assertTrue(status['detection_enabled'])
        self.assertEqual(status['fps'], 30.0)
        self.assertEqual(status['consecutive_errors'], 0)
        
        # 5. Test graceful shutdown
        self.controller._graceful_shutdown()
        self.assertFalse(self.controller.app_state.is_running)


if __name__ == '__main__':
    unittest.main()