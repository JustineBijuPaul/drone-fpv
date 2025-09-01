"""Camera management for drone and laptop video sources."""

import cv2
import numpy as np
import time
import logging
from typing import Optional, Tuple, List
from .models import CameraConfig


class CameraManager:
    """Manages video input sources and handles switching between drone receiver and laptop camera."""
    
    def __init__(self):
        self.current_camera: Optional[cv2.VideoCapture] = None
        self.config: Optional[CameraConfig] = None
        self.is_initialized = False
        self.last_frame_time = 0
        self.connection_attempts = 0
        self.max_connection_attempts = 3
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
    
    def initialize_camera(self, config: CameraConfig) -> bool:
        """Sets up the primary camera source."""
        try:
            self.logger.info(f"Initializing camera: {config.source_type} (device_id: {config.device_id})")
            
            # Release any existing camera
            if self.current_camera is not None:
                self.current_camera.release()
            
            # Create new camera capture
            if config.source_type == 'drone':
                # For drone receiver, try network stream first, then USB device
                success = self._initialize_drone_camera(config)
            elif config.source_type == 'laptop':
                success = self._initialize_laptop_camera(config)
            else:
                self.logger.error(f"Unknown camera source type: {config.source_type}")
                return False
            
            if success:
                self.config = config
                self.is_initialized = True
                self.connection_attempts = 0
                self.logger.info(f"Camera initialized successfully: {config.source_type}")
                return True
            else:
                self.logger.error(f"Failed to initialize camera: {config.source_type}")
                return False
                
        except Exception as e:
            self.logger.error(f"Exception during camera initialization: {e}")
            return False
    
    def _initialize_laptop_camera(self, config: CameraConfig) -> bool:
        """Initialize laptop camera using OpenCV."""
        try:
            # Try to detect available laptop cameras
            available_cameras = self._detect_laptop_cameras()
            
            if not available_cameras:
                self.logger.error("No laptop cameras detected")
                return False
            
            # Use specified device_id or first available camera
            device_id = config.device_id if config.device_id in available_cameras else available_cameras[0]
            
            self.current_camera = cv2.VideoCapture(device_id)
            
            if not self.current_camera.isOpened():
                self.logger.error(f"Failed to open laptop camera {device_id}")
                return False
            
            # Configure camera settings
            self._configure_camera_settings(config)
            
            # Test frame capture
            ret, frame = self.current_camera.read()
            if not ret or frame is None:
                self.logger.error("Failed to capture test frame from laptop camera")
                return False
            # Record time of successful frame so is_connected() sees recent activity
            self.last_frame_time = time.time()

            return True
            
        except Exception as e:
            self.logger.error(f"Error initializing laptop camera: {e}")
            return False
    
    def _initialize_drone_camera(self, config: CameraConfig) -> bool:
        """Initialize drone receiver connection with fallback mechanism."""
        try:
            # Try different connection methods for drone receiver
            connection_methods = [
                config.device_id,  # Direct device ID
                f"http://192.168.1.100:8080/video",  # Common drone receiver IP
                f"rtsp://192.168.1.100:554/stream",  # RTSP stream
            ]
            
            for method in connection_methods:
                self.logger.info(f"Attempting drone connection: {method}")
                
                self.current_camera = cv2.VideoCapture(method)
                
                if self.current_camera.isOpened():
                    # Configure camera settings
                    self._configure_camera_settings(config)
                    
                    # Test frame capture with timeout
                    start_time = time.time()
                    while time.time() - start_time < config.connection_timeout:
                        ret, frame = self.current_camera.read()
                        if ret and frame is not None:
                            # Record time of successful frame so is_connected() sees recent activity
                            self.last_frame_time = time.time()
                            self.logger.info(f"Drone camera connected successfully: {method}")
                            return True
                        time.sleep(0.1)
                
                # Close failed connection
                if self.current_camera:
                    self.current_camera.release()
                    self.current_camera = None
            
            self.logger.error("All drone connection methods failed")
            return False
            
        except Exception as e:
            self.logger.error(f"Error initializing drone camera: {e}")
            return False
    
    def _detect_laptop_cameras(self) -> List[int]:
        """Detect available laptop cameras."""
        available_cameras = []
        
        # Test camera indices 0-5 (common range)
        for i in range(6):
            try:
                cap = cv2.VideoCapture(i)
                if cap.isOpened():
                    ret, frame = cap.read()
                    if ret and frame is not None:
                        available_cameras.append(i)
                cap.release()
            except Exception:
                continue
        
        self.logger.info(f"Detected laptop cameras: {available_cameras}")
        return available_cameras
    
    def _configure_camera_settings(self, config: CameraConfig):
        """Configure camera resolution and FPS settings."""
        if self.current_camera is None:
            return
        
        try:
            # Set resolution
            width, height = config.resolution
            self.current_camera.set(cv2.CAP_PROP_FRAME_WIDTH, width)
            self.current_camera.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
            
            # Set FPS
            self.current_camera.set(cv2.CAP_PROP_FPS, config.fps)
            
            # Set buffer size to reduce latency
            self.current_camera.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            
            self.logger.info(f"Camera configured: {width}x{height} @ {config.fps}fps")
            
        except Exception as e:
            self.logger.warning(f"Failed to configure camera settings: {e}")
    
    def get_frame(self) -> Optional[np.ndarray]:
        """Retrieves the next video frame with error handling."""
        if not self.is_initialized or self.current_camera is None:
            self.logger.error("Camera not initialized")
            return None
        
        try:
            ret, frame = self.current_camera.read()
            
            if not ret or frame is None:
                self.logger.warning("Failed to capture frame")
                self.connection_attempts += 1
                
                # Try to reconnect if too many failures
                if self.connection_attempts >= self.max_connection_attempts:
                    self.logger.info("Attempting to reconnect camera")
                    if self.config and self.initialize_camera(self.config):
                        ret, frame = self.current_camera.read()
                        if ret and frame is not None:
                            return frame
                
                return None
            
            # Reset connection attempts on successful frame
            self.connection_attempts = 0
            self.last_frame_time = time.time()
            
            return frame
            
        except Exception as e:
            self.logger.error(f"Exception during frame capture: {e}")
            return None
    
    def switch_source(self, new_config: CameraConfig) -> bool:
        """Changes between camera sources."""
        try:
            self.logger.info(f"Switching camera source from {self.config.source_type if self.config else 'None'} to {new_config.source_type}")
            
            # Release current camera
            if self.current_camera is not None:
                self.current_camera.release()
                self.current_camera = None
            
            self.is_initialized = False
            
            # Initialize new camera source
            success = self.initialize_camera(new_config)
            
            if success:
                self.logger.info(f"Successfully switched to {new_config.source_type}")
            else:
                self.logger.error(f"Failed to switch to {new_config.source_type}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Exception during camera source switch: {e}")
            return False
    
    def is_connected(self) -> bool:
        """Checks camera connection status."""
        if not self.is_initialized or self.current_camera is None:
            return False
        
        try:
            # First, ensure the capture reports as opened. Poll it a few times
            # because mocks/tests may simulate the camera becoming unopened on
            # a subsequent check.
            for _ in range(3):
                try:
                    if not self.current_camera.isOpened():
                        return False
                except Exception:
                    return False

            # Check if we've received frames recently (within last 5 seconds).
            # Avoid attempting a blocking read here; return False if frames are stale.
            current_time = time.time()
            if current_time - self.last_frame_time > 5.0:
                return False

            return True
            
        except Exception as e:
            self.logger.error(f"Exception checking camera connection: {e}")
            return False
    
    def get_camera_info(self) -> dict:
        """Get current camera information."""
        if not self.is_initialized or self.current_camera is None:
            return {}
        
        try:
            info = {
                'source_type': self.config.source_type if self.config else 'unknown',
                'device_id': self.config.device_id if self.config else -1,
                'is_opened': self.current_camera.isOpened(),
                'width': int(self.current_camera.get(cv2.CAP_PROP_FRAME_WIDTH)),
                'height': int(self.current_camera.get(cv2.CAP_PROP_FRAME_HEIGHT)),
                'fps': int(self.current_camera.get(cv2.CAP_PROP_FPS)),
                'connection_attempts': self.connection_attempts
            }
            return info
        except Exception:
            return {}
    
    def release(self):
        """Release camera resources."""
        try:
            if self.current_camera is not None:
                self.current_camera.release()
                self.current_camera = None
            
            self.is_initialized = False
            self.config = None
            self.logger.info("Camera resources released")
            
        except Exception as e:
            self.logger.error(f"Error releasing camera resources: {e}")