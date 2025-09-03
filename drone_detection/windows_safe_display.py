"""
Windows-safe Display Manager

This version fixes the Windows Tkinter threading issue by using 
OpenCV display instead of Tkinter threads.
"""

import cv2
import logging
import platform
from typing import List, Optional
from .models import DetectionResult
from .display_manager import DisplayManager


class WindowsSafeDisplayManager(DisplayManager):
    """
    Windows-safe display manager that uses OpenCV instead of problematic Tkinter threading.
    """
    
    def __init__(self, window_title: str = "Drone Human Detection"):
        super().__init__()
        self.window_title = window_title
        self.is_windows = platform.system().lower() == 'windows'
        self.logger = logging.getLogger(__name__)
        self._window_created = False
        
        if self.is_windows:
            self.logger.info("Using Windows-safe OpenCV display (no Tkinter threading)")
        
    def show_frame(self, frame, detections: List[DetectionResult] = None) -> Optional[str]:
        """
        Display frame with detections using OpenCV (Windows-safe).
        
        Args:
            frame: The video frame to display
            detections: List of detection results to draw
            
        Returns:
            Key pressed by user, or None
        """
        if frame is None:
            return None
            
        try:
            # Draw detections on the frame
            display_frame = self.draw_detections(frame, detections or [])
            
            # Add system info for debugging
            height, width = display_frame.shape[:2]
            
            # Add debug info
            cv2.putText(display_frame, f'Platform: {platform.system()}', 
                       (10, height - 80), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            cv2.putText(display_frame, f'Resolution: {width}x{height}', 
                       (10, height - 60), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            cv2.putText(display_frame, f'Detections: {len(detections) if detections else 0}', 
                       (10, height - 40), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            cv2.putText(display_frame, 'Press Q or ESC to quit', 
                       (10, height - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            
            # Create window if not already created
            if not self._window_created:
                cv2.namedWindow(self.window_title, cv2.WINDOW_NORMAL)
                # Request a default window size of 1920x1080 on Windows
                try:
                    cv2.resizeWindow(self.window_title, 1920, 1080)
                except Exception:
                    # Fallback to frame size if resize fails
                    cv2.resizeWindow(self.window_title, width, height)
                self._window_created = True
                self.logger.info(f"Display window created: {self.window_title}")
            
            # Show frame
            cv2.imshow(self.window_title, display_frame)
            
            # Check for key press (Windows-safe)
            key = cv2.waitKey(1) & 0xFF
            if key != 255:  # A key was pressed
                if key == ord('q') or key == 27:  # 'q' or ESC
                    return 'quit'
                elif key == ord('c'):
                    return 'switch_camera'
                elif key == ord('s'):
                    return 'screenshot'
                else:
                    return chr(key) if 32 <= key <= 126 else None
                    
        except Exception as e:
            self.logger.error(f"Error displaying frame: {e}")
            # Fallback to headless mode
            self.save_preview_frame(frame, "/tmp/preview.jpg" if not self.is_windows else "preview.jpg")
            self.logger.info("Headless mode: saved preview frame")
        
        return None
    
    def cleanup(self):
        """Clean up display resources."""
        try:
            if self._window_created:
                cv2.destroyWindow(self.window_title)
                cv2.destroyAllWindows()
                self.logger.info("Display windows closed")
        except Exception as e:
            self.logger.error(f"Error during display cleanup: {e}")
            
    def is_display_available(self) -> bool:
        """Check if display is available."""
        return True  # OpenCV display should always work
    
    def save_preview_frame(self, frame, filename: str = None):
        """Save a preview frame to disk."""
        if filename is None:
            filename = "preview.jpg" if self.is_windows else "/tmp/preview.jpg"
            
        try:
            cv2.imwrite(filename, frame)
            self.logger.info(f"Preview frame saved: {filename}")
        except Exception as e:
            self.logger.error(f"Failed to save preview frame: {e}")


def create_windows_safe_display_manager():
    """
    Factory function to create the appropriate display manager for Windows.
    """
    if platform.system().lower() == 'windows':
        return WindowsSafeDisplayManager()
    else:
        # On non-Windows systems, use the regular display manager
        from .display_manager import DisplayManager
        return DisplayManager()
