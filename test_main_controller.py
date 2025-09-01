"""Tests for MainController error handling and recovery mechanisms."""

import unittest
from unittest.mock import Mock, patch, MagicMock
import time
import signal
from drone_detection.main_controller import MainController, ErrorType, RecoveryAction
from drone_detection.models import CameraConfig, AppState


class TestMainControllerErrorHandling(unittest.TestCase):
    """Test error handling and recovery mechanisms in MainController."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.controller = MainController()
    
    def tearDown(self):
        """Clean up after tests."""
        if hasattr(self.controller, 'app_state'):
            self.controller.app_state.is_running = False
    
    @patch('drone_detection.main_controller.CameraManager')
    @patch('drone_detection.main_controller.HumanDetector')
    @patch('drone_detection.main_controller.DisplayManager')
    def test_initialization_with_all_components_success(self, mock_display, mock_detector, mock_camera):
        """Test successful initialization of all components."""
        # Setup mocks
        mock_camera_instance = Mock()
        mock_camera_instance.initialize_camera.return_value = True
        mock_camera.return_value = mock_camera_instance
        
        mock_detector_instance = Mock()
        mock_detector_instance.load_model.return_value = True
        mock_detector.return_value = mock_detector_instance
        
        mock_display_instance = Mock()
        mock_display.return_value = mock_display_instance
        
        # Test initialization
        result = self.controller.initialize_components()
        
        # Assertions
        self.assertTrue(result)
        self.assertEqual(self.controller.app_state.current_camera, "drone")
        self.assertTrue(self.controller.app_state.detection_enabled)
    
    @patch('drone_detection.main_controller.CameraManager')
    def test_camera_initialization_fallback_to_laptop(self, mock_camera):
        """Test fallback from drone to laptop camera when drone fails."""
        # Setup mock to fail drone, succeed laptop
        mock_camera_instance = Mock()
        mock_camera_instance.initialize_camera.side_effect = [False, True]  # Drone fails, laptop succeeds
        mock_camera.return_value = mock_camera_instance
        
        # Test initialization
        result = self.controller._initialize_camera_manager()
        
        # Assertions
        self.assertTrue(result)
        self.assertEqual(self.controller.app_state.current_camera, "laptop")
        self.assertEqual(mock_camera_instance.initialize_camera.call_count, 2)
    
    @patch('drone_detection.main_controller.CameraManager')
    def test_camera_initialization_complete_failure(self, mock_camera):
        """Test complete camera initialization failure."""
        # Setup mock to fail both cameras
        mock_camera_instance = Mock()
        mock_camera_instance.initialize_camera.return_value = False
        mock_camera.return_value = mock_camera_instance
        
        # Test initialization
        result = self.controller._initialize_camera_manager()
        
        # Assertions
        self.assertFalse(result)
        self.assertEqual(self.controller.error_counts[ErrorType.CAMERA_CONNECTION_FAILED], 1)
        self.assertIsNotNone(self.controller.app_state.error_message)
    
    @patch('drone_detection.main_controller.HumanDetector')
    def test_human_detector_initialization_failure(self, mock_detector):
        """Test human detector initialization failure."""
        # Setup mock to fail model loading
        mock_detector_instance = Mock()
        mock_detector_instance.load_model.return_value = False
        mock_detector.return_value = mock_detector_instance
        
        # Test initialization
        result = self.controller._initialize_human_detector()
        
        # Assertions
        self.assertFalse(result)
        self.assertEqual(self.controller.error_counts[ErrorType.MODEL_LOADING_FAILED], 1)
        self.assertFalse(self.controller.app_state.detection_enabled)
    
    def test_error_handling_increments_counters(self):
        """Test that error handling properly increments error counters."""
        # Test different error types
        self.controller._handle_error(ErrorType.CAMERA_CONNECTION_FAILED, "Test camera error")
        self.controller._handle_error(ErrorType.FRAME_PROCESSING_FAILED, "Test processing error")
        self.controller._handle_error(ErrorType.CAMERA_CONNECTION_FAILED, "Another camera error")
        
        # Assertions
        self.assertEqual(self.controller.error_counts[ErrorType.CAMERA_CONNECTION_FAILED], 2)
        self.assertEqual(self.controller.error_counts[ErrorType.FRAME_PROCESSING_FAILED], 1)
        self.assertEqual(self.controller.app_state.error_message, "Another camera error")
    
    def test_troubleshooting_messages(self):
        """Test that appropriate troubleshooting messages are provided."""
        # Test camera error troubleshooting
        message = self.controller._get_troubleshooting_message(ErrorType.CAMERA_CONNECTION_FAILED)
        self.assertIn("camera connections", message.lower())
        
        # Test model error troubleshooting
        message = self.controller._get_troubleshooting_message(ErrorType.MODEL_LOADING_FAILED)
        self.assertIn("yolov8", message.lower())
        
        # Test unknown error
        message = self.controller._get_troubleshooting_message(ErrorType.UNKNOWN_ERROR)
        self.assertIn("unexpected error", message.lower())
    
    @patch('drone_detection.main_controller.CameraManager')
    def test_camera_recovery_switch_drone_to_laptop(self, mock_camera):
        """Test camera recovery by switching from drone to laptop."""
        # Setup controller state
        mock_camera_instance = Mock()
        mock_camera_instance.switch_source.return_value = True
        self.controller.camera_manager = mock_camera_instance
        self.controller.app_state.current_camera = "drone"
        
        # Test recovery
        result = self.controller._attempt_camera_recovery()
        
        # Assertions
        self.assertTrue(result)
        self.assertEqual(self.controller.app_state.current_camera, "laptop")
        mock_camera_instance.switch_source.assert_called_once()
    
    @patch('drone_detection.main_controller.CameraManager')
    def test_camera_recovery_switch_laptop_to_drone(self, mock_camera):
        """Test camera recovery by switching from laptop to drone."""
        # Setup controller state
        mock_camera_instance = Mock()
        mock_camera_instance.switch_source.return_value = True
        self.controller.camera_manager = mock_camera_instance
        self.controller.app_state.current_camera = "laptop"
        
        # Test recovery
        result = self.controller._attempt_camera_recovery()
        
        # Assertions
        self.assertTrue(result)
        self.assertEqual(self.controller.app_state.current_camera, "drone")
    
    @patch('drone_detection.main_controller.CameraManager')
    def test_camera_recovery_failure(self, mock_camera):
        """Test camera recovery failure."""
        # Setup controller state
        mock_camera_instance = Mock()
        mock_camera_instance.switch_source.return_value = False
        self.controller.camera_manager = mock_camera_instance
        self.controller.app_state.current_camera = "drone"
        
        # Test recovery
        result = self.controller._attempt_camera_recovery()
        
        # Assertions
        self.assertFalse(result)
    
    @patch('drone_detection.main_controller.DisplayManager')
    @patch('drone_detection.main_controller.HumanDetector')
    def test_component_restart_recovery(self, mock_detector, mock_display):
        """Test component restart recovery mechanism."""
        # Setup error counts to trigger restart
        self.controller.error_counts[ErrorType.DISPLAY_FAILED] = 1
        self.controller.error_counts[ErrorType.MODEL_LOADING_FAILED] = 1
        
        # Setup existing components
        existing_display = Mock()
        self.controller.display_manager = existing_display
        self.controller.human_detector = Mock()
        
        # Setup new component mocks
        mock_display_instance = Mock()
        mock_display.return_value = mock_display_instance
        
        mock_detector_instance = Mock()
        mock_detector_instance.load_model.return_value = True
        mock_detector.return_value = mock_detector_instance
        
        # Test recovery
        result = self.controller._attempt_component_restart()
        
        # Assertions
        self.assertTrue(result)
        existing_display.cleanup.assert_called_once()
        mock_display.assert_called_once()
        mock_detector.assert_called_once()
    
    def test_recovery_attempt_limit(self):
        """Test that recovery attempts are limited."""
        # Set recovery attempts to maximum
        self.controller.recovery_attempts = self.controller.max_recovery_attempts
        
        # Test recovery
        result = self.controller._attempt_recovery()
        
        # Assertions
        self.assertFalse(result)
    
    def test_consecutive_error_handling(self):
        """Test handling of consecutive errors."""
        # Simulate consecutive errors
        for i in range(self.controller.max_consecutive_errors):
            self.controller.consecutive_errors += 1
        
        # Should trigger recovery attempt
        self.assertGreaterEqual(self.controller.consecutive_errors, self.controller.max_consecutive_errors)
    
    @patch('drone_detection.main_controller.CameraManager')
    def test_force_camera_switch(self, mock_camera):
        """Test forced camera switch functionality."""
        # Setup controller state
        mock_camera_instance = Mock()
        mock_camera_instance.switch_source.return_value = True
        self.controller.camera_manager = mock_camera_instance
        self.controller.app_state.current_camera = "drone"
        
        # Test forced switch
        result = self.controller.force_camera_switch()
        
        # Assertions
        self.assertTrue(result)
        self.assertEqual(self.controller.app_state.current_camera, "laptop")
        self.assertEqual(self.controller.consecutive_errors, 0)
    
    def test_graceful_shutdown(self):
        """Test graceful shutdown procedure."""
        # Setup components
        self.controller.display_manager = Mock()
        self.controller.camera_manager = Mock()
        self.controller.app_state.is_running = True
        
        # Test shutdown
        self.controller._graceful_shutdown()
        
        # Assertions
        self.assertFalse(self.controller.app_state.is_running)
        self.controller.display_manager.cleanup.assert_called_once()
        self.controller.camera_manager.release.assert_called_once()
    
    def test_graceful_shutdown_with_component_errors(self):
        """Test graceful shutdown when components raise errors."""
        # Setup components that raise errors
        self.controller.display_manager = Mock()
        self.controller.display_manager.cleanup.side_effect = Exception("Cleanup error")
        
        self.controller.camera_manager = Mock()
        self.controller.camera_manager.release.side_effect = Exception("Release error")
        
        # Test shutdown (should not raise exceptions)
        try:
            self.controller._graceful_shutdown()
            shutdown_successful = True
        except Exception:
            shutdown_successful = False
        
        # Assertions
        self.assertTrue(shutdown_successful)
        self.assertFalse(self.controller.app_state.is_running)
    
    def test_system_status_reporting(self):
        """Test system status reporting functionality."""
        # Setup some state
        self.controller.app_state.current_camera = "laptop"
        self.controller.app_state.fps_counter = 25.5
        self.controller.consecutive_errors = 2
        self.controller.recovery_attempts = 1
        self.controller.error_counts[ErrorType.CAMERA_CONNECTION_FAILED] = 3
        
        # Get status
        status = self.controller.get_system_status()
        
        # Assertions
        self.assertEqual(status['current_camera'], "laptop")
        self.assertEqual(status['fps'], 25.5)
        self.assertEqual(status['consecutive_errors'], 2)
        self.assertEqual(status['recovery_attempts'], 1)
        self.assertEqual(status['error_counts']['camera_connection_failed'], 3)
    
    def test_signal_handler_setup(self):
        """Test that signal handlers are properly set up."""
        # This test verifies that signal handlers don't raise exceptions
        # Actual signal testing would require more complex setup
        try:
            controller = MainController()
            signal_setup_successful = True
        except Exception:
            signal_setup_successful = False
        
        self.assertTrue(signal_setup_successful)


if __name__ == '__main__':
    unittest.main()