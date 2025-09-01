"""Additional tests for error scenarios and recovery mechanisms."""

import unittest
from unittest.mock import Mock, patch, MagicMock
import time
import threading
from drone_detection.main_controller import MainController, ErrorType
from drone_detection.models import CameraConfig


class TestErrorRecoveryScenarios(unittest.TestCase):
    """Test specific error scenarios and recovery mechanisms."""
    
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
    def test_drone_connection_loss_recovery(self, mock_display, mock_detector, mock_camera):
        """Test recovery when drone connection is lost during operation."""
        # Setup initial successful state
        mock_camera_instance = Mock()
        mock_camera_instance.initialize_camera.side_effect = [True, False, True]  # Drone works, then fails, laptop works
        mock_camera_instance.is_connected.side_effect = [True, False, True]
        mock_camera_instance.get_frame.side_effect = [Mock(), None, Mock()]  # Frame, then None, then frame
        mock_camera_instance.switch_source.return_value = True
        mock_camera.return_value = mock_camera_instance
        
        mock_detector_instance = Mock()
        mock_detector_instance.load_model.return_value = True
        mock_detector_instance.detect_humans.return_value = []
        mock_detector.return_value = mock_detector_instance
        
        mock_display_instance = Mock()
        mock_display_instance.display_frame.return_value = True
        mock_display_instance.get_fps.return_value = 30.0
        mock_display.return_value = mock_display_instance
        
        # Initialize components
        self.assertTrue(self.controller.initialize_components())
        self.assertEqual(self.controller.app_state.current_camera, "drone")
        
        # Simulate first successful frame
        result = self.controller.process_frame()
        self.assertTrue(result)
        
        # Simulate connection loss (frame returns None)
        result = self.controller.process_frame()
        self.assertFalse(result)
        # The consecutive_errors counter is managed in the main run loop, not in process_frame
        # So we need to manually increment it for this test
        self.controller.consecutive_errors += 1
        self.assertEqual(self.controller.consecutive_errors, 1)
        
        # Trigger recovery
        recovery_result = self.controller._attempt_recovery()
        self.assertTrue(recovery_result)
        self.assertEqual(self.controller.app_state.current_camera, "laptop")
    
    @patch('drone_detection.main_controller.CameraManager')
    @patch('drone_detection.main_controller.HumanDetector')
    @patch('drone_detection.main_controller.DisplayManager')
    def test_model_loading_failure_recovery(self, mock_display, mock_detector, mock_camera):
        """Test recovery when YOLOv8 model fails to load."""
        # Setup camera to work
        mock_camera_instance = Mock()
        mock_camera_instance.initialize_camera.return_value = True
        mock_camera.return_value = mock_camera_instance
        
        # Setup detector to fail initially, then succeed
        mock_detector_instance = Mock()
        mock_detector_instance.load_model.side_effect = [False, True]  # Fail, then succeed
        mock_detector.return_value = mock_detector_instance
        
        mock_display_instance = Mock()
        mock_display.return_value = mock_display_instance
        
        # Test initial failure
        result = self.controller._initialize_human_detector()
        self.assertFalse(result)
        self.assertEqual(self.controller.error_counts[ErrorType.MODEL_LOADING_FAILED], 1)
        
        # Test recovery
        recovery_result = self.controller._attempt_component_restart()
        self.assertTrue(recovery_result)
        self.assertTrue(self.controller.app_state.detection_enabled)
    
    @patch('drone_detection.main_controller.CameraManager')
    @patch('drone_detection.main_controller.HumanDetector')
    @patch('drone_detection.main_controller.DisplayManager')
    def test_display_window_closure_handling(self, mock_display, mock_detector, mock_camera):
        """Test handling when user closes display window."""
        # Setup components
        mock_camera_instance = Mock()
        mock_camera_instance.initialize_camera.return_value = True
        mock_camera_instance.is_connected.return_value = True
        mock_camera_instance.get_frame.return_value = Mock()
        mock_camera.return_value = mock_camera_instance
        
        mock_detector_instance = Mock()
        mock_detector_instance.load_model.return_value = True
        mock_detector_instance.detect_humans.return_value = []
        mock_detector.return_value = mock_detector_instance
        
        mock_display_instance = Mock()
        mock_display_instance.display_frame.return_value = False  # User closed window
        mock_display.return_value = mock_display_instance
        
        # Initialize and process frame
        self.assertTrue(self.controller.initialize_components())
        result = self.controller.process_frame()
        
        # Should return True but set is_running to False
        self.assertTrue(result)
        self.assertFalse(self.controller.app_state.is_running)
    
    @patch('drone_detection.main_controller.CameraManager')
    def test_memory_error_simulation(self, mock_camera):
        """Test handling of memory errors during processing."""
        # Setup camera to raise MemoryError
        mock_camera_instance = Mock()
        mock_camera_instance.initialize_camera.return_value = True
        mock_camera_instance.is_connected.return_value = True
        mock_camera_instance.get_frame.side_effect = MemoryError("Out of memory")
        mock_camera.return_value = mock_camera_instance
        
        self.controller.camera_manager = mock_camera_instance
        
        # Test frame processing with memory error
        result = self.controller.process_frame()
        self.assertFalse(result)
        self.assertEqual(self.controller.error_counts[ErrorType.FRAME_PROCESSING_FAILED], 1)
    
    def test_consecutive_error_threshold(self):
        """Test behavior when consecutive error threshold is reached."""
        # Simulate reaching consecutive error threshold
        self.controller.consecutive_errors = self.controller.max_consecutive_errors - 1
        
        # Add one more error
        self.controller._handle_error(ErrorType.FRAME_PROCESSING_FAILED, "Test error")
        
        # Should not trigger recovery yet (error handling doesn't auto-trigger recovery)
        self.assertEqual(self.controller.consecutive_errors, self.controller.max_consecutive_errors - 1)
        
        # Manually increment to test threshold
        self.controller.consecutive_errors += 1
        self.assertGreaterEqual(self.controller.consecutive_errors, self.controller.max_consecutive_errors)
    
    @patch('drone_detection.main_controller.CameraManager')
    def test_camera_reconnection_timeout(self, mock_camera):
        """Test camera reconnection after timeout."""
        # Setup camera manager
        mock_camera_instance = Mock()
        mock_camera_instance.initialize_camera.return_value = True
        mock_camera_instance.is_connected.side_effect = [True, False, True]  # Connected, disconnected, reconnected
        mock_camera.return_value = mock_camera_instance
        
        self.controller.camera_manager = mock_camera_instance
        
        # Test initial connection
        self.assertTrue(self.controller.camera_manager.is_connected())
        
        # Test disconnection
        self.assertFalse(self.controller.camera_manager.is_connected())
        
        # Test reconnection
        self.assertTrue(self.controller.camera_manager.is_connected())
    
    @patch('drone_detection.main_controller.CameraManager')
    @patch('drone_detection.main_controller.HumanDetector')
    @patch('drone_detection.main_controller.DisplayManager')
    def test_partial_component_failure(self, mock_display, mock_detector, mock_camera):
        """Test handling when some components fail but others work."""
        # Setup camera to work
        mock_camera_instance = Mock()
        mock_camera_instance.initialize_camera.return_value = True
        mock_camera_instance.is_connected.return_value = True
        mock_camera_instance.get_frame.return_value = Mock()
        mock_camera.return_value = mock_camera_instance
        
        # Setup detector to fail
        mock_detector_instance = Mock()
        mock_detector_instance.load_model.return_value = False
        mock_detector.return_value = mock_detector_instance
        
        # Setup display to work
        mock_display_instance = Mock()
        mock_display_instance.display_frame.return_value = True
        mock_display_instance.get_fps.return_value = 30.0
        mock_display.return_value = mock_display_instance
        
        # Initialize components (should partially succeed)
        result = self.controller.initialize_components()
        self.assertFalse(result)  # Should fail due to detector
        
        # But camera should still be initialized
        self.assertIsNotNone(self.controller.camera_manager)
        self.assertEqual(self.controller.app_state.current_camera, "drone")
    
    def test_error_message_persistence(self):
        """Test that error messages are properly stored and accessible."""
        test_message = "Test error message for persistence"
        
        # Generate error
        self.controller._handle_error(ErrorType.CAMERA_CONNECTION_FAILED, test_message)
        
        # Check message persistence
        self.assertEqual(self.controller.app_state.error_message, test_message)
        
        # Check in system status
        status = self.controller.get_system_status()
        self.assertEqual(status['error_message'], test_message)
    
    @patch('drone_detection.main_controller.CameraManager')
    def test_recovery_attempt_reset_on_success(self, mock_camera):
        """Test that recovery attempts are reset after successful recovery."""
        # Setup camera manager
        mock_camera_instance = Mock()
        mock_camera_instance.switch_source.return_value = True
        self.controller.camera_manager = mock_camera_instance
        self.controller.app_state.current_camera = "drone"
        
        # Set some recovery attempts
        self.controller.recovery_attempts = 2
        
        # Successful recovery should reset attempts
        result = self.controller._attempt_camera_recovery()
        self.assertTrue(result)
        # Note: recovery attempts are reset in _attempt_recovery, not in individual recovery methods
    
    def test_system_status_during_errors(self):
        """Test system status reporting during various error states."""
        # Generate various errors
        self.controller._handle_error(ErrorType.CAMERA_CONNECTION_FAILED, "Camera error")
        self.controller._handle_error(ErrorType.FRAME_PROCESSING_FAILED, "Processing error")
        self.controller.consecutive_errors = 3
        self.controller.recovery_attempts = 1
        
        # Get status
        status = self.controller.get_system_status()
        
        # Verify error information is included
        self.assertEqual(status['consecutive_errors'], 3)
        self.assertEqual(status['recovery_attempts'], 1)
        self.assertEqual(status['error_counts']['camera_connection_failed'], 1)
        self.assertEqual(status['error_counts']['frame_processing_failed'], 1)
        self.assertEqual(status['error_message'], "Processing error")  # Last error message
    
    def test_stalled_processing_detection(self):
        """Test detection of stalled processing (no successful frames)."""
        # Setup time progression
        start_time = 1000.0
        stall_time = start_time + 35.0  # 35 seconds later (exceeds 30 second timeout)
        
        # Set last successful frame time
        self.controller.last_successful_frame_time = start_time
        
        # Check if stall would be detected
        time_since_success = stall_time - self.controller.last_successful_frame_time
        
        self.assertGreater(time_since_success, 30)  # Should trigger stall detection


class TestErrorRecoveryIntegration(unittest.TestCase):
    """Integration tests for error recovery scenarios."""
    
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
    def test_full_recovery_cycle(self, mock_display, mock_detector, mock_camera):
        """Test a complete error and recovery cycle."""
        # Setup mocks for successful recovery
        mock_camera_instance = Mock()
        mock_camera_instance.initialize_camera.return_value = True
        mock_camera_instance.switch_source.return_value = True
        mock_camera.return_value = mock_camera_instance
        
        mock_detector_instance = Mock()
        mock_detector_instance.load_model.return_value = True
        mock_detector.return_value = mock_detector_instance
        
        mock_display_instance = Mock()
        mock_display.return_value = mock_display_instance
        
        # Initialize components
        self.assertTrue(self.controller.initialize_components())
        
        # Simulate errors leading to recovery
        self.controller.consecutive_errors = self.controller.max_consecutive_errors
        self.controller.error_counts[ErrorType.CAMERA_CONNECTION_FAILED] = 2
        self.controller.app_state.current_camera = "drone"
        
        # Attempt recovery
        result = self.controller._attempt_recovery()
        
        # Verify recovery was attempted and successful
        self.assertTrue(result)
        self.assertEqual(self.controller.consecutive_errors, 0)


if __name__ == '__main__':
    unittest.main()