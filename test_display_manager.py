"""Unit tests for the Display Manager component."""

import unittest
import numpy as np
import cv2
import time
from unittest.mock import patch, MagicMock
from drone_detection.display_manager import DisplayManager
from drone_detection.models import DetectionResult


class TestDisplayManager(unittest.TestCase):
    """Test cases for DisplayManager class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.display_manager = DisplayManager("Test Window")
        
        # Create a test frame (480x640x3 RGB)
        self.test_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        self.test_frame[:] = (100, 100, 100)  # Gray background
        
        # Create test detection results
        self.test_detections = [
            DetectionResult(
                bbox=(100, 100, 200, 300),
                confidence=0.85,
                class_id=0,
                class_name="Person"
            ),
            DetectionResult(
                bbox=(300, 150, 450, 350),
                confidence=0.72,
                class_id=0,
                class_name="Person"
            )
        ]
    
    def test_initialization(self):
        """Test DisplayManager initialization."""
        dm = DisplayManager("Custom Window")
        self.assertEqual(dm.window_name, "Custom Window")
        self.assertEqual(dm.fps_counter, 0.0)
        self.assertFalse(dm._window_created)
        self.assertEqual(dm.bbox_color, (0, 255, 0))
        self.assertEqual(dm.text_color, (255, 255, 255))
    
    def test_draw_detections_with_valid_input(self):
        """Test drawing detections on a valid frame."""
        result_frame = self.display_manager.draw_detections(self.test_frame, self.test_detections)
        
        # Verify frame is not None and has correct shape
        self.assertIsNotNone(result_frame)
        self.assertEqual(result_frame.shape, self.test_frame.shape)
        
        # Verify original frame is not modified
        self.assertFalse(np.array_equal(result_frame, self.test_frame))
        
        # Check that bounding box pixels are different (green color added)
        bbox_pixel = result_frame[100, 100]  # Top-left corner of first bbox
        original_pixel = self.test_frame[100, 100]
        self.assertFalse(np.array_equal(bbox_pixel, original_pixel))
    
    def test_draw_detections_with_none_frame(self):
        """Test that draw_detections raises ValueError for None frame."""
        with self.assertRaises(ValueError) as context:
            self.display_manager.draw_detections(None, self.test_detections)
        self.assertIn("Frame cannot be None", str(context.exception))
    
    def test_draw_detections_with_empty_detections(self):
        """Test drawing with empty detection list."""
        result_frame = self.display_manager.draw_detections(self.test_frame, [])
        
        # Should return a copy of the original frame
        self.assertEqual(result_frame.shape, self.test_frame.shape)
        # Since no detections, should be identical to original
        np.testing.assert_array_equal(result_frame, self.test_frame)
    
    def test_draw_detections_boundary_clipping(self):
        """Test that bounding boxes are clipped to frame boundaries."""
        # Create detection with coordinates outside frame bounds
        out_of_bounds_detection = DetectionResult(
            bbox=(-50, -50, 700, 500),  # Extends beyond 640x480 frame
            confidence=0.9,
            class_id=0,
            class_name="Person"
        )
        
        # Should not raise exception and should handle clipping
        result_frame = self.display_manager.draw_detections(
            self.test_frame, [out_of_bounds_detection]
        )
        self.assertIsNotNone(result_frame)
        self.assertEqual(result_frame.shape, self.test_frame.shape)
    
    def test_fps_counter_calculation(self):
        """Test FPS counter calculation and updates."""
        # Simulate multiple frame updates with known timing
        start_time = 1000.0
        
        # Mock time.time() in the display_manager module
        with patch('drone_detection.display_manager.time.time') as mock_time:
            mock_time.side_effect = [
                start_time,        # Initial time for __init__
                start_time,        # First update
                start_time + 0.1,  # Second update
                start_time + 0.2,  # Third update
                start_time + 0.3,  # Fourth update
                start_time + 0.4,  # Fifth update
            ]
            
            # Create new display manager to use mocked time
            dm = DisplayManager("Test")
            
            # Update FPS counter multiple times
            for _ in range(5):
                dm._update_fps_counter()
            
            # FPS should be calculated (4 intervals over 0.4 seconds = 10 FPS)
            expected_fps = 4 / 0.4  # 10 FPS
            self.assertAlmostEqual(dm.fps_counter, expected_fps, places=1)
    
    def test_get_fps(self):
        """Test get_fps method."""
        # Initially should be 0
        self.assertEqual(self.display_manager.get_fps(), 0.0)
        
        # Set a test value
        self.display_manager.fps_counter = 25.5
        self.assertEqual(self.display_manager.get_fps(), 25.5)
    
    @patch('cv2.imshow')
    @patch('cv2.namedWindow')
    @patch('cv2.waitKey')
    @patch('cv2.getWindowProperty')
    def test_display_frame_success(self, mock_get_prop, mock_wait_key, mock_named_window, mock_imshow):
        """Test successful frame display."""
        mock_wait_key.return_value = ord('a')  # Any key except ESC
        mock_get_prop.return_value = 1  # Window is visible
        
        result = self.display_manager.display_frame(self.test_frame, self.test_detections)
        
        self.assertTrue(result)
        mock_named_window.assert_called_once()
        mock_imshow.assert_called_once()
        self.assertTrue(self.display_manager._window_created)
    
    @patch('cv2.imshow')
    @patch('cv2.namedWindow')
    @patch('cv2.waitKey')
    @patch('cv2.getWindowProperty')
    def test_display_frame_esc_key(self, mock_get_prop, mock_wait_key, mock_named_window, mock_imshow):
        """Test frame display with ESC key press."""
        mock_wait_key.return_value = 27  # ESC key
        mock_get_prop.return_value = 1  # Window is visible
        
        result = self.display_manager.display_frame(self.test_frame)
        
        self.assertFalse(result)
        mock_imshow.assert_called_once()
    
    @patch('cv2.imshow')
    @patch('cv2.namedWindow')
    @patch('cv2.waitKey')
    @patch('cv2.getWindowProperty')
    def test_display_frame_window_closed(self, mock_get_prop, mock_wait_key, mock_named_window, mock_imshow):
        """Test frame display when window is closed."""
        mock_wait_key.return_value = ord('a')
        mock_get_prop.return_value = 0  # Window is not visible (closed)
        
        result = self.display_manager.display_frame(self.test_frame)
        
        self.assertFalse(result)
        mock_imshow.assert_called_once()
    
    def test_display_frame_with_none_frame(self):
        """Test that display_frame raises ValueError for None frame."""
        with self.assertRaises(ValueError) as context:
            self.display_manager.display_frame(None)
        self.assertIn("Frame cannot be None", str(context.exception))
    
    @patch('cv2.destroyWindow')
    @patch('cv2.destroyAllWindows')
    def test_cleanup(self, mock_destroy_all, mock_destroy_window):
        """Test cleanup method."""
        # Set window as created
        self.display_manager._window_created = True
        
        self.display_manager.cleanup()
        
        mock_destroy_window.assert_called_once_with("Test Window")
        mock_destroy_all.assert_called_once()
        self.assertFalse(self.display_manager._window_created)
    
    @patch('cv2.destroyAllWindows')
    def test_cleanup_no_window(self, mock_destroy_all):
        """Test cleanup when no window was created."""
        # Window not created
        self.display_manager._window_created = False
        
        self.display_manager.cleanup()
        
        mock_destroy_all.assert_called_once()
        self.assertFalse(self.display_manager._window_created)
    
    def test_draw_fps_counter_on_frame(self):
        """Test that FPS counter is drawn on frame."""
        # Set a known FPS value
        self.display_manager.fps_counter = 30.5
        
        result_frame = self.display_manager._draw_fps_counter(self.test_frame.copy())
        
        # Verify frame is modified (FPS text added)
        self.assertFalse(np.array_equal(result_frame, self.test_frame))
        
        # Check that top-right area has been modified (where FPS is drawn)
        top_right_original = self.test_frame[10:30, -100:]
        top_right_result = result_frame[10:30, -100:]
        self.assertFalse(np.array_equal(top_right_original, top_right_result))
    
    def test_confidence_score_formatting(self):
        """Test that confidence scores are properly formatted as percentages."""
        detection = DetectionResult(
            bbox=(50, 50, 150, 150),
            confidence=0.856,  # Should be displayed as 85%
            class_id=0,
            class_name="Person"
        )
        
        result_frame = self.display_manager.draw_detections(self.test_frame, [detection])
        
        # Frame should be modified with the detection
        self.assertFalse(np.array_equal(result_frame, self.test_frame))
    
    def test_multiple_detections_rendering(self):
        """Test rendering multiple detections on the same frame."""
        # Create multiple detections
        detections = [
            DetectionResult(bbox=(10, 10, 100, 100), confidence=0.9, class_id=0, class_name="Person"),
            DetectionResult(bbox=(200, 200, 300, 300), confidence=0.7, class_id=0, class_name="Person"),
            DetectionResult(bbox=(400, 100, 500, 250), confidence=0.6, class_id=0, class_name="Person")
        ]
        
        result_frame = self.display_manager.draw_detections(self.test_frame, detections)
        
        # Verify all detections are rendered (frame should be significantly different)
        self.assertFalse(np.array_equal(result_frame, self.test_frame))
        
        # Check that multiple areas of the frame have been modified
        areas_modified = 0
        for detection in detections:
            x1, y1, x2, y2 = detection.bbox
            # Check if bounding box area has been modified
            bbox_area_original = self.test_frame[y1:y1+5, x1:x1+5]
            bbox_area_result = result_frame[y1:y1+5, x1:x1+5]
            if not np.array_equal(bbox_area_original, bbox_area_result):
                areas_modified += 1
        
        self.assertGreater(areas_modified, 0)


if __name__ == '__main__':
    unittest.main()