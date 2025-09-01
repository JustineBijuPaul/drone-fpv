"""Comprehensive integration and error-handling tests.

Covers:
- Camera switching logic
- End-to-end pipeline with mock camera feeds and known detection
- Performance benchmark for processing speed
- Automated tests for error handling paths
"""

import time
import unittest
from unittest.mock import patch, Mock
import numpy as np

from drone_detection.main_controller import MainController, ErrorType
from drone_detection.models import DetectionResult


class TestCameraSwitchingIntegration(unittest.TestCase):
    def test_initialize_fallback_to_laptop(self):
        """If drone init fails, controller should fall back to laptop camera."""
        controller = MainController()
        with patch('drone_detection.main_controller.CameraManager') as MockCam:
            inst = MockCam.return_value
            # First call (drone) fails, second call (laptop) succeeds
            inst.initialize_camera.side_effect = [False, True]

            success = controller._initialize_camera_manager()

            self.assertTrue(success)
            self.assertEqual(controller.app_state.current_camera, 'laptop')

    def test_force_camera_switch(self):
        """force_camera_switch should call CameraManager.switch_source and update state."""
        controller = MainController()
        # Prepare controller with mock camera manager and current camera
        controller.camera_manager = Mock()
        controller.app_state.current_camera = 'drone'

        controller.camera_manager.switch_source.return_value = True

        res = controller.force_camera_switch()
        self.assertTrue(res)
        self.assertEqual(controller.app_state.current_camera, 'laptop')


class TestEndToEndWithMockFeeds(unittest.TestCase):
    def setUp(self):
        self.controller = MainController()

    @patch('drone_detection.main_controller.CameraManager')
    @patch('drone_detection.main_controller.HumanDetector')
    @patch('drone_detection.main_controller.DisplayManager')
    def test_pipeline_with_mock_feed_and_detection(self, MockDisplay, MockDetector, MockCamera):
        """Run one processing step with mocked components and a known detection."""
        # Mock camera to provide a frame
        cam_inst = MockCamera.return_value
        cam_inst.initialize_camera.return_value = True
        cam_inst.is_connected.return_value = True
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        cam_inst.get_frame.return_value = frame

        # Mock detector to return one detection with known bbox
        det_inst = MockDetector.return_value
        det_inst.load_model.return_value = True
        known_detection = DetectionResult(bbox=(10, 20, 100, 200), confidence=0.9, class_id=0, class_name='person')
        det_inst.detect_humans.return_value = [known_detection]

        # Mock display to accept frames
        disp_inst = MockDisplay.return_value
        disp_inst.display_frame.return_value = True
        disp_inst.get_fps.return_value = 30.0

        # Initialize components and run a single frame
        ok = self.controller.initialize_components()
        self.assertTrue(ok)

        res = self.controller.process_frame()
        self.assertTrue(res)

        # Verify display called with detection list
        disp_inst.display_frame.assert_called()
        self.assertGreater(self.controller.performance_monitor.frames_processed, 0)

    @patch('drone_detection.main_controller.CameraManager')
    @patch('drone_detection.main_controller.HumanDetector')
    @patch('drone_detection.main_controller.DisplayManager')
    def test_performance_benchmark_simulated_detection_time(self, MockDisplay, MockDetector, MockCamera):
        """Simple benchmark to ensure average detection time remains reasonable with mock workload."""
        cam_inst = MockCamera.return_value
        cam_inst.initialize_camera.return_value = True
        cam_inst.is_connected.return_value = True
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        cam_inst.get_frame.return_value = frame

        det_inst = MockDetector.return_value
        det_inst.load_model.return_value = True

        # Simulate detection that takes ~10ms
        def fake_detect(f):
            time.sleep(0.01)
            return []

        det_inst.detect_humans.side_effect = fake_detect

        disp_inst = MockDisplay.return_value
        disp_inst.display_frame.return_value = True
        disp_inst.get_fps.return_value = 20.0

        ok = self.controller.initialize_components()
        self.assertTrue(ok)

        # Process multiple frames and collect detection times via performance monitor
        runs = 20
        for _ in range(runs):
            self.controller.process_frame()

        metrics = self.controller.performance_monitor.get_performance_metrics()
        # Acceptable average detection time ~ <= 50ms for this simulated workload
        self.assertLess(metrics.detection_time_ms, 50.0)


class TestErrorHandlingPaths(unittest.TestCase):
    def test_camera_get_frame_failure_triggers_error(self):
        controller = MainController()
        with patch('drone_detection.main_controller.CameraManager') as MockCam:
            cam_inst = MockCam.return_value
            cam_inst.initialize_camera.return_value = True
            cam_inst.is_connected.return_value = True
            cam_inst.get_frame.return_value = None  # Simulate failure

            # Minimal other components
            with patch('drone_detection.main_controller.HumanDetector') as MockDet, \
                 patch('drone_detection.main_controller.DisplayManager') as MockDisp:
                det_inst = MockDet.return_value
                det_inst.load_model.return_value = True
                disp_inst = MockDisp.return_value
                disp_inst.display_frame.return_value = True

                controller.initialize_components()
                ok = controller.process_frame()

                # process_frame should return False and error count should increment
                self.assertFalse(ok)
                self.assertGreater(controller.error_counts[ErrorType.FRAME_PROCESSING_FAILED], 0)

    def test_model_loading_failure_handled(self):
        controller = MainController()
        with patch('drone_detection.main_controller.HumanDetector') as MockDet, \
             patch('drone_detection.main_controller.CameraManager') as MockCam, \
             patch('drone_detection.main_controller.DisplayManager') as MockDisp:
            det_inst = MockDet.return_value
            det_inst.load_model.return_value = False

            cam_inst = MockCam.return_value
            cam_inst.initialize_camera.return_value = True

            disp_inst = MockDisp.return_value
            disp_inst.display_frame.return_value = True

            ok = controller.initialize_components()
            self.assertFalse(ok)
            self.assertGreater(controller.error_counts[ErrorType.MODEL_LOADING_FAILED], 0)

    def test_display_failure_shuts_down_loop(self):
        controller = MainController()
        with patch('drone_detection.main_controller.CameraManager') as MockCam, \
             patch('drone_detection.main_controller.HumanDetector') as MockDet, \
             patch('drone_detection.main_controller.DisplayManager') as MockDisp:
            cam_inst = MockCam.return_value
            cam_inst.initialize_camera.return_value = True
            cam_inst.is_connected.return_value = True
            cam_inst.get_frame.return_value = np.zeros((480, 640, 3), dtype=np.uint8)

            det_inst = MockDet.return_value
            det_inst.load_model.return_value = True
            det_inst.detect_humans.return_value = []

            disp_inst = MockDisp.return_value
            # Simulate user closed window
            disp_inst.display_frame.return_value = False

            ok = controller.initialize_components()
            self.assertTrue(ok)

            res = controller.process_frame()
            # process_frame returns True but should set is_running False to indicate shutdown
            self.assertFalse(controller.app_state.is_running)


if __name__ == '__main__':
    unittest.main(verbosity=2)
