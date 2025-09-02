"""Display Manager for video display and visual feedback."""

import logging
import cv2
import numpy as np
import time
import platform
import os
from typing import List, Optional
from .models import DetectionResult

# Import Windows compatibility utilities
try:
    from .windows_compat import windows_compat
except ImportError:
    windows_compat = None


class DisplayManager:
    """Manages video display and visual feedback for the drone human detection system."""

    def __init__(self, window_name: str = "Drone Human Detection"):
        """Initialize the Display Manager.

        Args:
            window_name: Name of the OpenCV display window
        """
        self.window_name = window_name
        self.fps_counter = 0.0
        self._frame_times = []
        self._max_frame_history = 30  # Keep last 30 frame times for FPS calculation
        self._last_fps_update = time.time()
        self._window_created = False

        # Whether display is currently fullscreen (for windowed backends)
        self._fullscreen = False

        # Last key pressed (set by display_frame)
        self.last_key: Optional[int] = None

        # Headless mode when GUI cannot be created (CI, headless server)
        self._headless = False
        # Whether we've saved a preview frame for headless inspection
        self._preview_saved = False

        # Logger
        self.logger = logging.getLogger(__name__)

        # Visual styling constants
        self.bbox_color = (0, 255, 0)  # Green bounding boxes
        self.text_color = (255, 255, 255)  # White text
        self.bbox_thickness = 2
        self.text_thickness = 1
        self.font = cv2.FONT_HERSHEY_SIMPLEX
        self.font_scale = 0.6

    def draw_detections(self, frame: np.ndarray, detections: List[DetectionResult]) -> np.ndarray:
        """Draw bounding boxes and confidence scores on the frame.

        Args:
            frame: Input video frame
            detections: List of detection results to draw

        Returns:
            Frame with drawn detections
        """
        if frame is None:
            raise ValueError("Frame cannot be None")

        # Create a copy to avoid modifying the original frame
        display_frame = frame.copy()

        for detection in detections:
            # Extract bounding box coordinates
            x1, y1, x2, y2 = detection.bbox

            # Ensure coordinates are within frame bounds
            height, width = display_frame.shape[:2]
            x1 = int(max(0, min(x1, width - 1)))
            y1 = int(max(0, min(y1, height - 1)))
            x2 = int(max(0, min(x2, width - 1)))
            y2 = int(max(0, min(y2, height - 1)))

            # Draw bounding box
            cv2.rectangle(display_frame, (x1, y1), (x2, y2), self.bbox_color, self.bbox_thickness)

            # Prepare label text with confidence score
            confidence_percent = int(detection.confidence * 100)
            label = f"{detection.class_name}: {confidence_percent}%"

            # Calculate text size for background rectangle
            (text_width, text_height), baseline = cv2.getTextSize(
                label, self.font, self.font_scale, self.text_thickness
            )

            # Draw background rectangle for text
            text_bg_x1 = x1
            text_bg_y1 = y1 - text_height - baseline - 5
            text_bg_x2 = x1 + text_width + 10
            text_bg_y2 = y1

            # Ensure text background is within frame bounds
            text_bg_y1 = max(0, text_bg_y1)
            text_bg_x2 = min(width, text_bg_x2)

            cv2.rectangle(display_frame, (text_bg_x1, text_bg_y1), (text_bg_x2, text_bg_y2), self.bbox_color, -1)

            # Draw text label
            text_x = x1 + 5
            text_y = y1 - 5
            if text_y < text_height:
                text_y = y1 + text_height + 5

            cv2.putText(display_frame, label, (text_x, text_y), self.font, self.font_scale, self.text_color, self.text_thickness)

        return display_frame

    def _update_fps_counter(self) -> None:
        """Update FPS counter based on frame processing times."""
        current_time = time.time()
        self._frame_times.append(current_time)

        # Keep only recent frame times
        if len(self._frame_times) > self._max_frame_history:
            self._frame_times.pop(0)

        # Calculate FPS if we have enough samples and enough time has passed
        if len(self._frame_times) >= 2:
            time_span = self._frame_times[-1] - self._frame_times[0]
            if time_span > 0:
                self.fps_counter = (len(self._frame_times) - 1) / time_span
                self._last_fps_update = current_time

    def _draw_fps_counter(self, frame: np.ndarray) -> np.ndarray:
        """Draw FPS counter on the frame.

        Args:
            frame: Input frame to draw FPS on

        Returns:
            Frame with FPS counter drawn
        """
        fps_text = f"FPS: {self.fps_counter:.1f}"

        # Position FPS counter at top-right corner
        height, width = frame.shape[:2]
        (text_width, text_height), baseline = cv2.getTextSize(fps_text, self.font, self.font_scale, self.text_thickness)

        # Calculate position
        text_x = width - text_width - 10
        text_y = text_height + 10

        # Draw background rectangle
        bg_x1 = text_x - 5
        bg_y1 = text_y - text_height - 5
        bg_x2 = text_x + text_width + 5
        bg_y2 = text_y + 5

        cv2.rectangle(frame, (bg_x1, bg_y1), (bg_x2, bg_y2), (0, 0, 0), -1)

        # Draw FPS text
        cv2.putText(frame, fps_text, (text_x, text_y), self.font, self.font_scale, self.text_color, self.text_thickness)

        return frame

    def display_frame(self, frame: np.ndarray, detections: Optional[List[DetectionResult]] = None) -> bool:
        """Display the processed frame with detections and FPS counter.

        Args:
            frame: Video frame to display
            detections: Optional list of detections to draw

        Returns:
            True if display was successful, False if window should close
        """
        if frame is None:
            raise ValueError("Frame cannot be None")

        # Update FPS counter
        self._update_fps_counter()

        # Create display frame
        display_frame = frame.copy()

        # Draw detections if provided
        if detections:
            display_frame = self.draw_detections(display_frame, detections)

        # Draw FPS counter
        display_frame = self._draw_fps_counter(display_frame)

        # If we're in headless mode, save a preview frame once and continue
        if getattr(self, '_headless', False):
            if not getattr(self, '_preview_saved', False):
                preview_path = self._get_preview_path()
                try:
                    cv2.imwrite(preview_path, display_frame)
                    self._preview_saved = True
                    self.logger.info(f"Headless mode: saved preview frame to {preview_path}")
                except Exception:
                    pass
            # No GUI to interact with; keep running
            self.last_key = None
            return True

        # Create window if not already created
        if not self._window_created:
            try:
                # Windows-specific window creation optimizations
                if windows_compat and windows_compat.is_windows:
                    # Create a normal/resizable window with Windows optimizations
                    cv2.namedWindow(self.window_name, cv2.WINDOW_NORMAL | cv2.WINDOW_KEEPRATIO)
                    # Set initial window size for better Windows experience
                    cv2.resizeWindow(self.window_name, frame.shape[1], frame.shape[0])
                else:
                    # Create a normal/resizable window so we can toggle fullscreen via setWindowProperty
                    cv2.namedWindow(self.window_name, cv2.WINDOW_NORMAL)
                
                self._window_created = True
                self.logger.info(f"Display window created: {self.window_name}")
                
            except Exception as e:
                # Failed to create a GUI window (headless environment or missing backend)
                self.logger.error(f"Failed to create display window: {e}")
                self._headless = True
                # Save preview frame with Windows-compatible path
                preview_path = self._get_preview_path()
                try:
                    cv2.imwrite(preview_path, display_frame)
                    self._preview_saved = True
                    self.logger.info(f"Headless mode: saved preview frame to {preview_path}")
                except Exception:
                    pass
                self.last_key = None
                return True

        # Display the frame
        try:
            cv2.imshow(self.window_name, display_frame)
        except Exception as e:
            self.logger.error(f"Failed to display frame: {e}")
            self._headless = True
            preview_path = self._get_preview_path()
            try:
                cv2.imwrite(preview_path, display_frame)
                self._preview_saved = True
                self.logger.info(f"Headless mode: saved preview frame to {preview_path}")
            except Exception:
                pass
            self.last_key = None
            return True

        # Check for window close or ESC key
        try:
            key = cv2.waitKey(1) & 0xFF
            # store last key for external handlers
            self.last_key = key
        except Exception:
            # If waitKey fails, enter headless fallback
            self.logger.error("waitKey failed; switching to headless mode")
            self._headless = True
            self.last_key = None
            return True

        try:
            # Toggle fullscreen on 'f' key press
            if key == ord('f'):
                try:
                    self.toggle_fullscreen()
                except Exception:
                    pass

            if key == 27 or cv2.getWindowProperty(self.window_name, cv2.WND_PROP_VISIBLE) < 1:
                return False
        except Exception:
            # getWindowProperty may fail if backend lacks windowing support
            self.logger.error("getWindowProperty failed; switching to headless mode")
            self._headless = True
            return True

        return True

    def cleanup(self) -> None:
        """Clean up OpenCV windows and resources."""
        if getattr(self, '_window_created', False):
            try:
                cv2.destroyWindow(self.window_name)
            except Exception:
                pass
            self._window_created = False
        try:
            cv2.destroyAllWindows()
        except Exception:
            pass

    def toggle_fullscreen(self) -> None:
        """Toggle fullscreen mode for the OpenCV window (best-effort).

        This uses cv2.setWindowProperty to request fullscreen. Not all backends
        support it; failures are swallowed and logged.
        """
        try:
            # Flip the state
            self._fullscreen = not getattr(self, '_fullscreen', False)
            if self._fullscreen:
                cv2.setWindowProperty(self.window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
            else:
                cv2.setWindowProperty(self.window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_NORMAL)
        except Exception as e:
            self.logger.debug(f"Failed to toggle fullscreen: {e}")

    def get_fps(self) -> float:
        """Get current FPS counter value.

        Returns:
            Current FPS value
        """
        return self.fps_counter

    def _get_preview_path(self) -> str:
        """Get appropriate preview file path for the current platform."""
        if platform.system().lower() == 'windows':
            import tempfile
            return os.path.join(tempfile.gettempdir(), 'drone_preview.jpg')
        else:
            return '/tmp/preview.jpg'