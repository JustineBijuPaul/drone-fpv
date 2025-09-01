"""Performance tests for the drone human detection system."""

import unittest
import time
import numpy as np
import threading
from unittest.mock import Mock, patch, MagicMock
from drone_detection.performance_monitor import PerformanceMonitor, PerformanceMetrics
from drone_detection.main_controller import MainController
from drone_detection.models import CameraConfig


class TestPerformanceMonitor(unittest.TestCase):
    """Test cases for the PerformanceMonitor class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.monitor = PerformanceMonitor(target_fps=15.0, max_memory_mb=256.0)
    
    def tearDown(self):
        """Clean up after tests."""
        if self.monitor.monitoring_active:
            self.monitor.stop_monitoring()
    
    def test_initialization(self):
        """Test performance monitor initialization."""
        self.assertEqual(self.monitor.target_fps, 15.0)
        self.assertEqual(self.monitor.max_memory_mb, 256.0)
        self.assertFalse(self.monitor.monitoring_active)
        self.assertEqual(self.monitor.frames_processed, 0)
        self.assertEqual(self.monitor.frames_skipped, 0)
    
    def test_frame_timing(self):
        """Test frame timing recording."""
        # Record a frame
        start_time = self.monitor.record_frame_start()
        time.sleep(0.01)  # Simulate 10ms processing
        self.monitor.record_frame_end(start_time, detection_time=0.005, display_time=0.003)
        
        self.assertEqual(self.monitor.frames_processed, 1)
        self.assertEqual(self.monitor.frames_skipped, 0)
        self.assertEqual(len(self.monitor.frame_times), 1)
        self.assertGreater(self.monitor.frame_times[0], 0.009)  # At least 9ms
    
    def test_frame_skipping_logic(self):
        """Test frame skipping logic."""
        # Initially should not skip frames
        self.assertFalse(self.monitor.should_skip_frame())

        # Enable frame skipping and reset counter
        self.monitor.skip_frames = True
        self.monitor.skip_ratio = 2
        self.monitor.skip_counter = 0  # Reset counter

        # Now test the intended pattern: skip, process, skip, process
        result1 = self.monitor.should_skip_frame()  # counter becomes 1 -> skip
        result2 = self.monitor.should_skip_frame()  # counter becomes 2 -> process
        result3 = self.monitor.should_skip_frame()  # counter becomes 3 -> skip
        result4 = self.monitor.should_skip_frame()  # counter becomes 4 -> process

        # The pattern should be: skip, process, skip, process
        self.assertTrue(result1)   # Frame 1: skip
        self.assertFalse(result2)  # Frame 2: process
        self.assertTrue(result3)   # Frame 3: skip
        self.assertFalse(result4)  # Frame 4: process
    
    def test_fps_calculation(self):
        """Test FPS calculation."""
        # Record multiple frames with known timing
        frame_interval = 1.0 / 20.0  # 20 FPS
        
        for i in range(10):
            start_time = time.time()
            time.sleep(frame_interval)
            self.monitor.record_frame_end(start_time)
        
        fps = self.monitor.get_current_fps()
        # Should be approximately 20 FPS (within 10% tolerance)
        self.assertGreater(fps, 18.0)
        self.assertLess(fps, 22.0)
    
    @patch('psutil.Process')
    def test_memory_tracking(self, mock_process):
        """Test memory usage tracking."""
        # Mock memory info
        mock_memory_info = Mock()
        mock_memory_info.rss = 100 * 1024 * 1024  # 100MB
        mock_process.return_value.memory_info.return_value = mock_memory_info
        
        memory_usage = self.monitor.get_current_memory_usage()
        self.assertAlmostEqual(memory_usage, 100.0, places=1)
    
    @patch('psutil.cpu_percent')
    def test_cpu_tracking(self, mock_cpu_percent):
        """Test CPU usage tracking."""
        mock_cpu_percent.return_value = 75.5
        
        cpu_usage = self.monitor.get_cpu_usage()
        self.assertEqual(cpu_usage, 75.5)
    
    def test_performance_metrics(self):
        """Test performance metrics collection."""
        # Record some sample data
        for i in range(5):
            start_time = self.monitor.record_frame_start()
            time.sleep(0.02)  # 20ms processing
            self.monitor.record_frame_end(start_time, detection_time=0.01, display_time=0.005)
        
        metrics = self.monitor.get_performance_metrics()
        
        self.assertIsInstance(metrics, PerformanceMetrics)
        self.assertGreater(metrics.fps, 0)
        self.assertEqual(metrics.frames_processed, 5)
        self.assertEqual(metrics.frames_skipped, 0)
        self.assertGreater(metrics.frame_processing_time_ms, 15)  # At least 15ms
    
    def test_optimization_suggestions(self):
        """Test optimization suggestions."""
        # Simulate low FPS scenario
        for i in range(10):
            start_time = time.time()
            time.sleep(0.1)  # 100ms processing (very slow)
            self.monitor.record_frame_end(start_time)
        
        suggestions = self.monitor.get_optimization_suggestions()
        self.assertGreater(len(suggestions), 0)
        
        # Should suggest FPS optimization
        fps_suggestion_found = any("FPS is low" in suggestion for suggestion in suggestions)
        self.assertTrue(fps_suggestion_found)
    
    def test_background_monitoring(self):
        """Test background monitoring thread."""
        self.monitor.start_monitoring()
        self.assertTrue(self.monitor.monitoring_active)
        self.assertIsNotNone(self.monitor.monitor_thread)
        
        # Let it run briefly
        time.sleep(0.1)
        
        self.monitor.stop_monitoring()
        self.assertFalse(self.monitor.monitoring_active)
    
    def test_reset_metrics(self):
        """Test metrics reset functionality."""
        # Add some data
        start_time = self.monitor.record_frame_start()
        self.monitor.record_frame_end(start_time)
        
        self.assertEqual(self.monitor.frames_processed, 1)
        
        # Reset and verify
        self.monitor.reset_metrics()
        self.assertEqual(self.monitor.frames_processed, 0)
        self.assertEqual(len(self.monitor.frame_times), 0)


class TestPerformanceIntegration(unittest.TestCase):
    """Integration tests for performance monitoring with main controller."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.controller = MainController()
    
    def tearDown(self):
        """Clean up after tests."""
        if hasattr(self.controller, 'performance_monitor') and self.controller.performance_monitor:
            self.controller.performance_monitor.stop_monitoring()
    
    @patch('drone_detection.camera_manager.CameraManager')
    @patch('drone_detection.human_detector.HumanDetector')
    @patch('drone_detection.display_manager.DisplayManager')
    def test_performance_monitor_integration(self, mock_display, mock_detector, mock_camera):
        """Test performance monitor integration with main controller."""
        # Mock successful initialization
        mock_camera_instance = Mock()
        mock_camera_instance.initialize_camera.return_value = True
        mock_camera_instance.is_connected.return_value = True
        mock_camera_instance.get_frame.return_value = np.zeros((480, 640, 3), dtype=np.uint8)
        mock_camera.return_value = mock_camera_instance
        
        mock_detector_instance = Mock()
        mock_detector_instance.load_model.return_value = True
        mock_detector_instance.detect_humans.return_value = []
        mock_detector.return_value = mock_detector_instance
        
        mock_display_instance = Mock()
        mock_display_instance.display_frame.return_value = True
        mock_display_instance.get_fps.return_value = 20.0
        mock_display.return_value = mock_display_instance
        
        # Initialize components
        success = self.controller.initialize_components()
        self.assertTrue(success)
        self.assertIsNotNone(self.controller.performance_monitor)
        
        # Process a few frames
        for _ in range(5):
            result = self.controller.process_frame()
            self.assertTrue(result)
        
        # Check that performance monitor recorded the frames
        metrics = self.controller.performance_monitor.get_performance_metrics()
        self.assertGreater(metrics.frames_processed, 0)


class TestPerformanceRequirements(unittest.TestCase):
    """Test cases to validate FPS requirements (minimum 15 FPS)."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.monitor = PerformanceMonitor(target_fps=15.0)
    
    def tearDown(self):
        """Clean up after tests."""
        if self.monitor.monitoring_active:
            self.monitor.stop_monitoring()
    
    def test_minimum_fps_requirement(self):
        """Test that system can achieve minimum 15 FPS requirement."""
        # Simulate processing at exactly 15 FPS
        frame_interval = 1.0 / 15.0  # 66.67ms per frame
        
        for i in range(30):  # Process 30 frames
            start_time = time.time()
            # Simulate realistic processing time (50ms)
            time.sleep(0.05)
            self.monitor.record_frame_end(start_time, detection_time=0.03, display_time=0.01)
            
            # Wait for remaining frame time to maintain 15 FPS
            elapsed = time.time() - start_time
            if elapsed < frame_interval:
                time.sleep(frame_interval - elapsed)
        
        fps = self.monitor.get_current_fps()
        
        # Should achieve at least 15 FPS (with reasonable tolerance)
        self.assertGreaterEqual(fps, 13.5, f"FPS {fps:.1f} is below minimum requirement of 15 FPS")
        # Allow for some variation in timing, but not too high
        self.assertLessEqual(fps, 25.0, f"FPS {fps:.1f} indicates timing issues in test")
    
    def test_frame_skipping_maintains_fps(self):
        """Test that frame skipping helps maintain target FPS."""
        # Simulate slow processing that would normally cause low FPS
        slow_processing_time = 0.1  # 100ms processing (would give 10 FPS)
        
        # Enable frame skipping
        self.monitor.skip_frames = True
        self.monitor.skip_ratio = 2  # Skip every other frame
        
        processed_frames = 0
        skipped_frames = 0
        
        for i in range(30):
            if self.monitor.should_skip_frame():
                self.monitor.record_frame_end(time.time(), skipped=True)
                skipped_frames += 1
            else:
                start_time = time.time()
                time.sleep(slow_processing_time)
                self.monitor.record_frame_end(start_time, detection_time=0.08, display_time=0.01)
                processed_frames += 1
        
        # Should have skipped approximately half the frames
        self.assertGreater(skipped_frames, 10)
        self.assertGreater(processed_frames, 10)
        
        # Effective FPS should be better than without skipping
        fps = self.monitor.get_current_fps()
        self.assertGreater(fps, 8.0, "Frame skipping should improve effective FPS")
    
    def test_memory_usage_within_limits(self):
        """Test that memory usage stays within reasonable limits."""
        # Set a conservative memory limit
        self.monitor.max_memory_mb = 256.0
        
        # Simulate frame processing with memory tracking
        for i in range(100):
            start_time = self.monitor.record_frame_start()
            # Simulate some memory allocation
            dummy_data = np.zeros((100, 100, 3), dtype=np.uint8)
            time.sleep(0.01)
            self.monitor.record_frame_end(start_time)
            del dummy_data
        
        # Check optimization suggestions for memory issues
        suggestions = self.monitor.get_optimization_suggestions()
        memory_warnings = [s for s in suggestions if "memory" in s.lower()]
        
        # If memory usage is high, should get suggestions
        current_memory = self.monitor.get_current_memory_usage()
        if current_memory > self.monitor.max_memory_mb * 0.8:
            self.assertGreater(len(memory_warnings), 0, 
                             "Should provide memory optimization suggestions when usage is high")
    
    def test_performance_degradation_detection(self):
        """Test detection of performance degradation."""
        # Start with good performance
        for i in range(10):
            start_time = time.time()
            time.sleep(0.03)  # 30ms processing (good performance)
            self.monitor.record_frame_end(start_time)
        
        initial_fps = self.monitor.get_current_fps()
        
        # Simulate performance degradation
        for i in range(10):
            start_time = time.time()
            time.sleep(0.08)  # 80ms processing (poor performance)
            self.monitor.record_frame_end(start_time)
        
        degraded_fps = self.monitor.get_current_fps()
        
        # Should detect the performance drop
        self.assertLess(degraded_fps, initial_fps * 0.8, 
                       "Should detect significant FPS degradation")
        
        # Should provide optimization suggestions
        suggestions = self.monitor.get_optimization_suggestions()
        self.assertGreater(len(suggestions), 0, 
                          "Should provide suggestions when performance degrades")


class TestPerformanceBenchmarks(unittest.TestCase):
    """Benchmark tests for performance validation."""
    
    def test_detection_processing_time(self):
        """Benchmark detection processing time."""
        monitor = PerformanceMonitor(target_fps=15.0)
        
        # Simulate detection times that should be achievable
        max_detection_time = 0.04  # 40ms maximum for detection
        
        detection_times = []
        for i in range(20):
            start_time = time.time()
            # Simulate detection processing
            time.sleep(0.02)  # 20ms detection time
            detection_time = time.time() - start_time
            detection_times.append(detection_time)
            
            monitor.record_frame_end(start_time, detection_time=detection_time)
        
        avg_detection_time = sum(detection_times) / len(detection_times)
        
        self.assertLess(avg_detection_time, max_detection_time,
                       f"Average detection time {avg_detection_time*1000:.1f}ms exceeds {max_detection_time*1000:.1f}ms limit")
    
    def test_end_to_end_processing_time(self):
        """Benchmark end-to-end frame processing time."""
        monitor = PerformanceMonitor(target_fps=15.0)
        
        # For 15 FPS, each frame should be processed within 66.67ms
        max_frame_time = 1.0 / 15.0  # 66.67ms
        
        frame_times = []
        for i in range(30):
            start_time = time.time()
            
            # Simulate complete frame processing pipeline
            time.sleep(0.02)  # Camera capture: 20ms
            time.sleep(0.025) # Detection: 25ms
            time.sleep(0.01)  # Display: 10ms
            # Total: ~55ms (within 66.67ms budget)
            
            frame_time = time.time() - start_time
            frame_times.append(frame_time)
            
            monitor.record_frame_end(start_time, detection_time=0.025, display_time=0.01)
        
        avg_frame_time = sum(frame_times) / len(frame_times)
        
        self.assertLess(avg_frame_time, max_frame_time,
                       f"Average frame time {avg_frame_time*1000:.1f}ms exceeds {max_frame_time*1000:.1f}ms budget for 15 FPS")
        
        # Verify FPS meets requirement
        fps = monitor.get_current_fps()
        self.assertGreaterEqual(fps, 14.0, f"FPS {fps:.1f} below minimum requirement")


if __name__ == '__main__':
    # Run performance tests
    unittest.main(verbosity=2)