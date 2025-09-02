"""Main application controller with comprehensive error handling and recovery mechanisms."""

import logging
import time
import signal
import traceback
from typing import Optional, Dict, Any
from enum import Enum

from .camera_manager import CameraManager
from .human_detector import HumanDetector
from .display_manager import DisplayManager
from .performance_monitor import PerformanceMonitor
from .models import CameraConfig, AppState

# Import Windows compatibility utilities
try:
    from .windows_compat import ensure_windows_compatibility
except ImportError:
    ensure_windows_compatibility = None


class ErrorType(Enum):
    CAMERA_CONNECTION_FAILED = "camera_connection_failed"
    MODEL_LOADING_FAILED = "model_loading_failed"
    FRAME_PROCESSING_FAILED = "frame_processing_failed"
    DISPLAY_FAILED = "display_failed"
    MEMORY_ERROR = "memory_error"
    UNKNOWN_ERROR = "unknown_error"


class RecoveryAction(Enum):
    RETRY = "retry"
    SWITCH_CAMERA = "switch_camera"
    RESTART_COMPONENT = "restart_component"
    GRACEFUL_SHUTDOWN = "graceful_shutdown"
    CONTINUE = "continue"


class MainController:
    """Orchestrates camera, detection, display and performance monitoring.

    Responsibilities:
    - Initialize and manage CameraManager, HumanDetector, DisplayManager and PerformanceMonitor
    - Provide robust error handling with exponential-backoff logging to avoid log flooding
    - Attempt recovery strategies when errors accumulate
    """

    def __init__(self):
        # Core components
        self.camera_manager: Optional[CameraManager] = None
        self.human_detector: Optional[HumanDetector] = None
        self.display_manager: Optional[DisplayManager] = None
        self.performance_monitor: Optional[PerformanceMonitor] = None

        # Application state
        self.app_state = AppState(
            is_running=False,
            current_camera="none",
            detection_enabled=False,
            fps_counter=0.0,
            error_message=None,
        )

        # Error handling configuration
        self.max_consecutive_errors = 5
        self.consecutive_errors = 0
        self.error_counts: Dict[ErrorType, int] = {error_type: 0 for error_type in ErrorType}
        self.last_successful_frame_time = time.time()
        self.recovery_attempts = 0
        self.max_recovery_attempts = 3

        # Camera configurations for fallback
        self.drone_config = CameraConfig(
            source_type="drone",
            device_id=0,
            resolution=(640, 480),
            fps=30,
            connection_timeout=5.0,
        )

        self.laptop_config = CameraConfig(
            source_type="laptop",
            device_id=0,
            resolution=(640, 480),
            fps=30,
            connection_timeout=2.0,
        )

        # Timestamp of last memory cleanup log to avoid noisy repeated messages
        self._last_mem_cleanup_time = 0.0
        # Per-error-type rate limiting to avoid flooding logs when errors repeat rapidly
        self._last_error_log_times: Dict[ErrorType, float] = {error_type: 0.0 for error_type in ErrorType}
        # Exponential backoff intervals per error type (starts at base, doubles on each logged repeat)
        self._error_log_base_interval = 1.0  # seconds
        self._error_log_intervals: Dict[ErrorType, float] = {error_type: self._error_log_base_interval for error_type in ErrorType}
        self._error_log_max_interval = 60.0  # cap interval

        # Setup logging and signal handlers
        self.logger = self._setup_logging()
        self._setup_signal_handlers()

        self.logger.info("MainController initialized with comprehensive error handling")

    def _setup_logging(self) -> logging.Logger:
        logger = logging.getLogger(__name__)
        # If the root logger already has handlers (e.g., main.py called basicConfig),
        # don't add a new handler here to avoid duplicate output. Otherwise, add
        # a console handler and prevent propagation to the root logger.
        root_logger = logging.getLogger()
        if root_logger.handlers:
            # Let the root handlers handle output; ensure logger inherits level
            logger.setLevel(root_logger.level if root_logger.level else logging.INFO)
            logger.propagate = True
            return logger

        if not logger.handlers:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)
            logger.setLevel(logging.INFO)
            logger.propagate = False
        return logger

    def _setup_signal_handlers(self):
        def signal_handler(signum, frame):
            self.logger.info(f"Received signal {signum}, initiating graceful shutdown")
            self.app_state.is_running = False

        try:
            signal.signal(signal.SIGINT, signal_handler)
            signal.signal(signal.SIGTERM, signal_handler)
        except Exception:
            # Signal setup may fail in some test harnesses; ignore in that case
            pass

    def initialize_components(self) -> bool:
        try:
            self.logger.info("Initializing system components...")

            # Initialize Windows compatibility first
            if ensure_windows_compatibility:
                self.logger.info("Setting up Windows 11 compatibility...")
                if not ensure_windows_compatibility():
                    self.logger.warning("Windows compatibility setup failed, but continuing...")

            if not self._initialize_camera_manager():
                return False

            if not self._initialize_human_detector():
                return False

            if not self._initialize_display_manager():
                return False

            if not self._initialize_performance_monitor():
                return False

            self.logger.info("All components initialized successfully")
            return True
        except Exception as e:
            self._handle_error(ErrorType.UNKNOWN_ERROR, f"Failed to initialize components: {e}")
            return False

    def _initialize_camera_manager(self) -> bool:
        try:
            self.camera_manager = CameraManager()
            self.logger.info("Attempting to initialize drone camera...")
            if self.camera_manager.initialize_camera(self.drone_config):
                self.app_state.current_camera = "drone"
                self.logger.info("Drone camera initialized successfully")
                return True

            self.logger.info("Drone camera failed, falling back to laptop camera...")
            if self.camera_manager.initialize_camera(self.laptop_config):
                self.app_state.current_camera = "laptop"
                self.logger.info("Laptop camera initialized successfully")
                return True

            self._handle_error(ErrorType.CAMERA_CONNECTION_FAILED, "No camera sources available. Please check camera connections.")
            return False
        except Exception as e:
            self._handle_error(ErrorType.CAMERA_CONNECTION_FAILED, f"Camera manager initialization failed: {e}")
            return False

    def _initialize_human_detector(self) -> bool:
        try:
            self.human_detector = HumanDetector(confidence_threshold=0.5)
            if not self.human_detector.load_model():
                self._handle_error(ErrorType.MODEL_LOADING_FAILED, "Failed to load YOLOv8 model. Please ensure the model file is available.")
                return False
            self.app_state.detection_enabled = True
            self.logger.info("Human detector initialized successfully")
            return True
        except Exception as e:
            self._handle_error(ErrorType.MODEL_LOADING_FAILED, f"Human detector initialization failed: {e}")
            return False

    def _initialize_display_manager(self) -> bool:
        try:
            # If a display manager was pre-set (e.g. GUI injection), keep it.
            if self.display_manager is None:
                self.display_manager = DisplayManager()
            self.logger.info("Display manager initialized successfully")
            return True
        except Exception as e:
            self._handle_error(ErrorType.DISPLAY_FAILED, f"Display manager initialization failed: {e}")
            return False

    def _initialize_performance_monitor(self) -> bool:
        try:
            target_fps = min(self.drone_config.fps, self.laptop_config.fps) * 0.5
            target_fps = max(15.0, target_fps)
            self.performance_monitor = PerformanceMonitor(target_fps=target_fps, max_memory_mb=512.0)
            self.performance_monitor.start_monitoring()
            self.logger.info(f"Performance monitor initialized successfully (target FPS: {target_fps})")
            return True
        except Exception as e:
            self.logger.error(f"Performance monitor initialization failed: {e}")
            return True

    def run(self) -> int:
        try:
            self.logger.info("Starting drone human detection system...")
            if not self.initialize_components():
                self.logger.error("Failed to initialize components, exiting")
                return 1

            self.app_state.is_running = True
            self.logger.info("System started successfully, entering main loop")

            while self.app_state.is_running:
                try:
                    if not self.process_frame():
                        self.consecutive_errors += 1
                        if self.consecutive_errors >= self.max_consecutive_errors:
                            self.logger.error(f"Too many consecutive errors ({self.consecutive_errors}), attempting recovery")
                            if not self._attempt_recovery():
                                self.logger.error("Recovery failed, shutting down")
                                break
                    else:
                        self.consecutive_errors = 0
                        self.last_successful_frame_time = time.time()

                    if time.time() - self.last_successful_frame_time > 30:
                        self.logger.warning("No successful frames for 30 seconds, attempting recovery")
                        if not self._attempt_recovery():
                            self.logger.error("Recovery failed after timeout, shutting down")
                            break

                    time.sleep(0.001)
                except KeyboardInterrupt:
                    self.logger.info("Keyboard interrupt received, shutting down")
                    break
                except Exception as e:
                    self._handle_error(ErrorType.UNKNOWN_ERROR, f"Unexpected error in main loop: {e}")
                    if self.consecutive_errors >= self.max_consecutive_errors:
                        break

            self.logger.info("Main loop ended, performing cleanup")
            return 0
        except Exception as e:
            self.logger.error(f"Critical error in main application: {e}")
            self.logger.error(traceback.format_exc())
            return 1
        finally:
            self._graceful_shutdown()

    def process_frame(self) -> bool:
        if self.performance_monitor and self.performance_monitor.should_skip_frame():
            if self.performance_monitor:
                self.performance_monitor.record_frame_end(time.time(), skipped=True)
            return True

        frame_start_time = time.time()
        detection_time = 0.0
        display_time = 0.0

        try:
            if not self.camera_manager or not self.camera_manager.is_connected():
                self._handle_error(ErrorType.CAMERA_CONNECTION_FAILED, "Camera not connected")
                if self.performance_monitor:
                    self.performance_monitor.record_frame_end(frame_start_time, detection_time, display_time, skipped=False)
                return False

            frame = self.camera_manager.get_frame()
            if frame is None:
                self._handle_error(ErrorType.FRAME_PROCESSING_FAILED, "Failed to get frame from camera")
                if self.performance_monitor:
                    self.performance_monitor.record_frame_end(frame_start_time, detection_time, display_time, skipped=False)
                return False

            detections = []
            if self.human_detector and self.app_state.detection_enabled:
                try:
                    detection_frame = frame
                    if self.performance_monitor and self.performance_monitor.current_quality_level < 1.0:
                        try:
                            q = self.performance_monitor.current_quality_level
                            if q <= 0:
                                q = 1.0
                            h, w = frame.shape[:2]
                            new_w = max(1, int(w * q))
                            new_h = max(1, int(h * q))
                            import cv2
                            detection_frame = cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
                        except Exception as e:
                            self.logger.debug(f"Failed to resize frame for detection: {e}")

                    detection_start = time.time()
                    detections = self.human_detector.detect_humans(detection_frame)
                    detection_time = time.time() - detection_start
                except Exception as e:
                    self._handle_error(ErrorType.FRAME_PROCESSING_FAILED, f"Detection failed: {e}")

            if self.display_manager:
                try:
                    display_start = time.time()
                    if not self.display_manager.display_frame(frame, detections):
                        self.app_state.is_running = False
                        if self.performance_monitor:
                            self.performance_monitor.record_frame_end(frame_start_time, detection_time, display_time, skipped=False)
                        return True
                    display_time = time.time() - display_start
                    self.app_state.fps_counter = self.display_manager.get_fps()
                except Exception as e:
                    self._handle_error(ErrorType.DISPLAY_FAILED, f"Display failed: {e}")
                    if self.performance_monitor:
                        self.performance_monitor.record_frame_end(frame_start_time, detection_time, display_time, skipped=False)
                    return False

            # On successful processing, reset backoff for error logging so future errors are reported promptly
            try:
                for et in self._error_log_intervals:
                    self._error_log_intervals[et] = self._error_log_base_interval
                    self._last_error_log_times[et] = 0.0
            except Exception:
                pass

            if self.performance_monitor:
                self.performance_monitor.record_frame_end(frame_start_time, detection_time, display_time, skipped=False)

            try:
                if self.performance_monitor:
                    mem = self.performance_monitor.get_current_memory_usage()
                    if mem > self.performance_monitor.max_memory_mb * 0.85:
                        import gc
                        gc.collect()
                        now = time.time()
                        if now - getattr(self, '_last_mem_cleanup_time', 0) > 5.0:
                            self.logger.info(f"High memory detected ({mem:.1f}MB). Performed explicit garbage collection")
                            self._last_mem_cleanup_time = now
            except Exception as e:
                self.logger.debug(f"Memory cleanup attempt failed: {e}")

            return True
        except Exception as e:
            self._handle_error(ErrorType.FRAME_PROCESSING_FAILED, f"Frame processing error: {e}")
            if self.performance_monitor:
                self.performance_monitor.record_frame_end(frame_start_time, detection_time, display_time, skipped=False)
            return False

    def _handle_error(self, error_type: ErrorType, message: str):
        # Update counters and backoff-aware logging to prevent flooding
        try:
            self.error_counts[error_type] += 1
        except Exception:
            # Ensure error_counts exists during unusual states
            self.error_counts = getattr(self, 'error_counts', {et: 0 for et in ErrorType})
            self.error_counts[error_type] = self.error_counts.get(error_type, 0) + 1

        self.app_state.error_message = message
        now = time.time()
        last_logged = self._last_error_log_times.get(error_type, 0.0)
        interval = self._error_log_intervals.get(error_type, self._error_log_base_interval)

        if now - last_logged >= interval:
            if error_type in [ErrorType.CAMERA_CONNECTION_FAILED, ErrorType.MODEL_LOADING_FAILED]:
                self.logger.error(f"{error_type.value}: {message}")
            else:
                self.logger.warning(f"{error_type.value}: {message}")

            troubleshooting_msg = self._get_troubleshooting_message(error_type)
            if troubleshooting_msg:
                self.logger.info(f"Troubleshooting: {troubleshooting_msg}")

            # record when we logged and increase backoff interval up to the cap
            self._last_error_log_times[error_type] = now
            new_interval = min(self._error_log_intervals.get(error_type, self._error_log_base_interval) * 2.0,
                               self._error_log_max_interval)
            self._error_log_intervals[error_type] = new_interval
        else:
            # Skip logging to avoid flood; counts still increment
            pass

    def _get_troubleshooting_message(self, error_type: ErrorType) -> str:
        troubleshooting_messages = {
            ErrorType.CAMERA_CONNECTION_FAILED:
                "Check camera connections. Ensure drone receiver is powered on and connected, or verify laptop camera is not in use by other applications.",
            ErrorType.MODEL_LOADING_FAILED:
                "Ensure YOLOv8 model file is available. The system will attempt to download it automatically on first run.",
            ErrorType.FRAME_PROCESSING_FAILED:
                "This may be a temporary issue. The system will attempt to continue processing.",
            ErrorType.DISPLAY_FAILED:
                "Check display settings and ensure the system has access to create windows.",
            ErrorType.MEMORY_ERROR:
                "Close other applications to free up memory, or restart the application.",
            ErrorType.UNKNOWN_ERROR:
                "An unexpected error occurred. Check logs for more details.",
        }
        return troubleshooting_messages.get(error_type, "")

    def _attempt_recovery(self) -> bool:
        self.recovery_attempts += 1
        if self.recovery_attempts > self.max_recovery_attempts:
            self.logger.error(f"Maximum recovery attempts ({self.max_recovery_attempts}) exceeded")
            return False

        self.logger.info(f"Attempting recovery (attempt {self.recovery_attempts}/{self.max_recovery_attempts})")

        camera_errors = (self.error_counts.get(ErrorType.CAMERA_CONNECTION_FAILED, 0) +
                         self.error_counts.get(ErrorType.FRAME_PROCESSING_FAILED, 0))
        if camera_errors > 0 and self.camera_manager:
            if self._attempt_camera_recovery():
                self.logger.info("Camera recovery successful")
                self.consecutive_errors = 0
                return True

        if self._attempt_component_restart():
            self.logger.info("Component restart successful")
            self.consecutive_errors = 0
            return True

        self.logger.warning("Recovery attempt failed")
        return False

    def _attempt_camera_recovery(self) -> bool:
        try:
            if not self.camera_manager:
                return False
            current_source = self.app_state.current_camera
            if current_source == "drone":
                self.logger.info("Attempting to switch from drone to laptop camera")
                if self.camera_manager.switch_source(self.laptop_config):
                    self.app_state.current_camera = "laptop"
                    return True
            elif current_source == "laptop":
                self.logger.info("Attempting to switch from laptop to drone camera")
                if self.camera_manager.switch_source(self.drone_config):
                    self.app_state.current_camera = "drone"
                    return True
            else:
                self.logger.info("Attempting to reinitialize current camera")
                config = self.drone_config if current_source == "drone" else self.laptop_config
                if self.camera_manager.initialize_camera(config):
                    return True
            return False
        except Exception as e:
            self.logger.error(f"Camera recovery failed: {e}")
            return False

    def _attempt_component_restart(self) -> bool:
        try:
            self.logger.info("Attempting to restart components")
            if self.error_counts.get(ErrorType.DISPLAY_FAILED, 0) > 0:
                try:
                    if self.display_manager:
                        self.display_manager.cleanup()
                    self.display_manager = DisplayManager()
                    self.logger.info("Display manager restarted")
                except Exception as e:
                    self.logger.error(f"Failed to restart display manager: {e}")

            if self.error_counts.get(ErrorType.MODEL_LOADING_FAILED, 0) > 0:
                try:
                    self.human_detector = HumanDetector(confidence_threshold=0.5)
                    if self.human_detector.load_model():
                        self.app_state.detection_enabled = True
                        self.logger.info("Human detector restarted")
                    else:
                        self.logger.warning("Failed to restart human detector")
                except Exception as e:
                    self.logger.error(f"Failed to restart human detector: {e}")

            return True
        except Exception as e:
            self.logger.error(f"Component restart failed: {e}")
            return False

    def _graceful_shutdown(self):
        self.logger.info("Performing graceful shutdown...")
        try:
            self.app_state.is_running = False
            if self.display_manager:
                try:
                    self.display_manager.cleanup()
                    self.logger.info("Display manager cleaned up")
                except Exception as e:
                    self.logger.error(f"Error cleaning up display manager: {e}")

            if self.camera_manager:
                try:
                    self.camera_manager.release()
                    self.logger.info("Camera manager resources released")
                except Exception as e:
                    self.logger.error(f"Error releasing camera resources: {e}")

            if self.performance_monitor:
                try:
                    self.performance_monitor.stop_monitoring()
                    self.performance_monitor.log_performance_summary()
                    self.logger.info("Performance monitor stopped")
                except Exception as e:
                    self.logger.error(f"Error stopping performance monitor: {e}")

            self._log_final_statistics()
            self.logger.info("Graceful shutdown completed")
        except Exception as e:
            self.logger.error(f"Error during graceful shutdown: {e}")

    def _log_final_statistics(self):
        self.logger.info("=== Final System Statistics ===")
        self.logger.info(f"Total recovery attempts: {self.recovery_attempts}")
        self.logger.info(f"Final camera source: {self.app_state.current_camera}")
        self.logger.info(f"Detection enabled: {self.app_state.detection_enabled}")
        self.logger.info(f"Final FPS: {self.app_state.fps_counter:.1f}")
        self.logger.info("Error counts by type:")
        for error_type, count in self.error_counts.items():
            if count > 0:
                self.logger.info(f"  {error_type.value}: {count}")

    def get_system_status(self) -> Dict[str, Any]:
        return {
            'is_running': self.app_state.is_running,
            'current_camera': self.app_state.current_camera,
            'detection_enabled': self.app_state.detection_enabled,
            'fps': self.app_state.fps_counter,
            'error_message': self.app_state.error_message,
            'consecutive_errors': self.consecutive_errors,
            'recovery_attempts': self.recovery_attempts,
            'error_counts': {error_type.value: count for error_type, count in self.error_counts.items()},
            'camera_connected': self.camera_manager.is_connected() if self.camera_manager else False,
            'model_loaded': self.human_detector.is_model_loaded() if self.human_detector else False,
        }

    def force_camera_switch(self) -> bool:
        try:
            if not self.camera_manager:
                return False
            current_source = self.app_state.current_camera
            target_config = self.laptop_config if current_source == "drone" else self.drone_config
            self.logger.info(f"Forcing camera switch from {current_source} to {target_config.source_type}")
            if self.camera_manager.switch_source(target_config):
                self.app_state.current_camera = target_config.source_type
                self.consecutive_errors = 0
                self.logger.info(f"Successfully switched to {target_config.source_type} camera")
                return True
            else:
                self.logger.error(f"Failed to switch to {target_config.source_type} camera")
                return False
        except Exception as e:
            self.logger.error(f"Error during forced camera switch: {e}")
            return False

        self.logger.warning("Recovery attempt failed")
        return False

    def _attempt_camera_recovery(self) -> bool:
        try:
            if not self.camera_manager:
                return False
            current_source = self.app_state.current_camera
            if current_source == "drone":
                self.logger.info("Attempting to switch from drone to laptop camera")
                if self.camera_manager.switch_source(self.laptop_config):
                    self.app_state.current_camera = "laptop"
                    return True
            elif current_source == "laptop":
                self.logger.info("Attempting to switch from laptop to drone camera")
                if self.camera_manager.switch_source(self.drone_config):
                    self.app_state.current_camera = "drone"
                    return True
            else:
                self.logger.info("Attempting to reinitialize current camera")
                config = self.drone_config if current_source == "drone" else self.laptop_config
                if self.camera_manager.initialize_camera(config):
                    return True
            return False
        except Exception as e:
            self.logger.error(f"Camera recovery failed: {e}")
            return False

    def _attempt_component_restart(self) -> bool:
        try:
            self.logger.info("Attempting to restart components")
            if self.error_counts[ErrorType.DISPLAY_FAILED] > 0:
                try:
                    if self.display_manager:
                        self.display_manager.cleanup()
                    self.display_manager = DisplayManager()
                    self.logger.info("Display manager restarted")
                except Exception as e:
                    self.logger.error(f"Failed to restart display manager: {e}")

            if self.error_counts[ErrorType.MODEL_LOADING_FAILED] > 0:
                try:
                    self.human_detector = HumanDetector(confidence_threshold=0.5)
                    if self.human_detector.load_model():
                        self.app_state.detection_enabled = True
                        self.logger.info("Human detector restarted")
                    else:
                        self.logger.warning("Failed to restart human detector")
                except Exception as e:
                    self.logger.error(f"Failed to restart human detector: {e}")

            return True
        except Exception as e:
            self.logger.error(f"Component restart failed: {e}")
            return False

    def _graceful_shutdown(self):
        self.logger.info("Performing graceful shutdown...")
        try:
            self.app_state.is_running = False
            if self.display_manager:
                try:
                    self.display_manager.cleanup()
                    self.logger.info("Display manager cleaned up")
                except Exception as e:
                    self.logger.error(f"Error cleaning up display manager: {e}")

            if self.camera_manager:
                try:
                    self.camera_manager.release()
                    self.logger.info("Camera manager resources released")
                except Exception as e:
                    self.logger.error(f"Error releasing camera resources: {e}")

            if self.performance_monitor:
                try:
                    self.performance_monitor.stop_monitoring()
                    self.performance_monitor.log_performance_summary()
                    self.logger.info("Performance monitor stopped")
                except Exception as e:
                    self.logger.error(f"Error stopping performance monitor: {e}")

            self._log_final_statistics()
            self.logger.info("Graceful shutdown completed")
        except Exception as e:
            self.logger.error(f"Error during graceful shutdown: {e}")

    def _log_final_statistics(self):
        self.logger.info("=== Final System Statistics ===")
        self.logger.info(f"Total recovery attempts: {self.recovery_attempts}")
        self.logger.info(f"Final camera source: {self.app_state.current_camera}")
        self.logger.info(f"Detection enabled: {self.app_state.detection_enabled}")
        self.logger.info(f"Final FPS: {self.app_state.fps_counter:.1f}")
        self.logger.info("Error counts by type:")
        for error_type, count in self.error_counts.items():
            if count > 0:
                self.logger.info(f"  {error_type.value}: {count}")

    def get_system_status(self) -> Dict[str, Any]:
        return {
            'is_running': self.app_state.is_running,
            'current_camera': self.app_state.current_camera,
            'detection_enabled': self.app_state.detection_enabled,
            'fps': self.app_state.fps_counter,
            'error_message': self.app_state.error_message,
            'consecutive_errors': self.consecutive_errors,
            'recovery_attempts': self.recovery_attempts,
            'error_counts': {error_type.value: count for error_type, count in self.error_counts.items()},
            'camera_connected': self.camera_manager.is_connected() if self.camera_manager else False,
            'model_loaded': self.human_detector.is_model_loaded() if self.human_detector else False,
        }

    def force_camera_switch(self) -> bool:
        try:
            if not self.camera_manager:
                return False
            current_source = self.app_state.current_camera
            target_config = self.laptop_config if current_source == "drone" else self.drone_config
            self.logger.info(f"Forcing camera switch from {current_source} to {target_config.source_type}")
            if self.camera_manager.switch_source(target_config):
                self.app_state.current_camera = target_config.source_type
                self.consecutive_errors = 0
                self.logger.info(f"Successfully switched to {target_config.source_type} camera")
                return True
            else:
                self.logger.error(f"Failed to switch to {target_config.source_type} camera")
                return False
        except Exception as e:
            self.logger.error(f"Error during forced camera switch: {e}")
            return False