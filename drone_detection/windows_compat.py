#!/usr/bin/env python3
"""
Windows 11 compatibility utilities for the Drone Human Detection System.

This module provides Windows-specific optimizations and compatibility fixes.
"""

import os
import sys
import platform
import logging
import subprocess
from pathlib import Path
from typing import Optional, List, Dict, Any
import psutil


class WindowsCompatibility:
    """Handles Windows 11 specific compatibility and optimizations."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.is_windows = platform.system().lower() == 'windows'
        self.windows_version = None
        
        if self.is_windows:
            self.windows_version = platform.version()
            self.logger.info(f"Running on Windows {platform.release()} (version: {self.windows_version})")
    
    def setup_windows_environment(self) -> bool:
        """Configure Windows-specific environment settings."""
        if not self.is_windows:
            return True
            
        try:
            # Enable ANSI color support in Windows terminal
            self._enable_ansi_colors()
            
            # Set optimal process priority
            self._set_process_priority()
            
            # Configure Windows-specific OpenCV backends
            self._configure_opencv_backends()
            
            # Set up Windows camera access permissions
            self._check_camera_permissions()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to setup Windows environment: {e}")
            return False
    
    def _enable_ansi_colors(self):
        """Enable ANSI color codes in Windows terminal."""
        try:
            import colorama
            colorama.init()
            self.logger.debug("ANSI colors enabled for Windows terminal")
        except ImportError:
            # Enable via Windows API if colorama not available
            try:
                import ctypes
                kernel32 = ctypes.windll.kernel32
                kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
                self.logger.debug("ANSI colors enabled via Windows API")
            except Exception:
                self.logger.debug("Could not enable ANSI colors")
    
    def _set_process_priority(self):
        """Set optimal process priority for video processing."""
        try:
            import psutil
            current_process = psutil.Process()
            
            # Set to high priority for better real-time performance
            if hasattr(psutil, 'HIGH_PRIORITY_CLASS'):
                current_process.nice(psutil.HIGH_PRIORITY_CLASS)
                self.logger.debug("Process priority set to HIGH")
            else:
                # Fallback for older psutil versions
                current_process.nice(-10)  # Unix-style nice value
                
        except Exception as e:
            self.logger.warning(f"Could not set process priority: {e}")
    
    def _configure_opencv_backends(self):
        """Configure optimal OpenCV backends for Windows."""
        try:
            import cv2
            
            # Prefer DirectShow backend for cameras on Windows
            os.environ['OPENCV_VIDEOIO_PRIORITY_DSHOW'] = '1'
            
            # Enable GPU acceleration if available
            if cv2.cuda.getCudaEnabledDeviceCount() > 0:
                self.logger.info(f"CUDA devices available: {cv2.cuda.getCudaEnabledDeviceCount()}")
                os.environ['OPENCV_DNN_BACKEND'] = 'CUDA'
            
        except Exception as e:
            self.logger.debug(f"OpenCV backend configuration: {e}")
    
    def _check_camera_permissions(self):
        """Check and warn about camera permissions on Windows."""
        try:
            # Check if camera privacy settings might block access
            self.logger.info("Checking camera permissions...")
            
            # On Windows 10/11, camera access is controlled by privacy settings
            self.logger.info("Ensure camera access is enabled in Windows Settings > Privacy & Security > Camera")
            
        except Exception as e:
            self.logger.debug(f"Camera permission check: {e}")
    
    def get_optimal_camera_backends(self) -> List[int]:
        """Get ordered list of camera backends optimized for Windows."""
        if not self.is_windows:
            return []
        
        try:
            import cv2
            
            # Ordered by preference for Windows
            backends = [
                cv2.CAP_DSHOW,     # DirectShow - best for Windows webcams
                cv2.CAP_MSMF,      # Microsoft Media Foundation
                cv2.CAP_VFW,       # Video for Windows (legacy)
                cv2.CAP_ANY,       # Auto-detect
            ]
            
            return backends
            
        except ImportError:
            return []
    
    def detect_windows_cameras(self) -> List[Dict]:
        """Detect cameras using Windows-specific methods."""
        cameras = []
        
        if not self.is_windows:
            return cameras
        
        try:
            import cv2
            
            # Test with DirectShow backend specifically
            for i in range(10):  # Test more indices on Windows
                try:
                    cap = cv2.VideoCapture(i, cv2.CAP_DSHOW)
                    if cap.isOpened():
                        # Get camera name if possible
                        ret, frame = cap.read()
                        if ret and frame is not None:
                            cameras.append({
                                'id': i,
                                'backend': 'DirectShow',
                                'name': f'Camera {i}',
                                'resolution': frame.shape[:2]
                            })
                    cap.release()
                except Exception:
                    continue
            
            self.logger.info(f"Windows cameras detected: {len(cameras)}")
            return cameras
            
        except Exception as e:
            self.logger.error(f"Windows camera detection failed: {e}")
            return cameras
    
    def optimize_for_windows_performance(self) -> Dict[str, Any]:
        """Get Windows-specific performance optimizations."""
        optimizations = {}
        
        if not self.is_windows:
            return optimizations
        
        try:
            # Get system information
            memory_gb = psutil.virtual_memory().total / (1024**3)
            cpu_count = psutil.cpu_count()
            
            # Optimize based on system specs
            if memory_gb >= 8:
                optimizations['buffer_size'] = 2  # Reduced for better real-time performance
                optimizations['thread_count'] = min(cpu_count, 4)
                optimizations['target_fps'] = 30
            else:
                optimizations['buffer_size'] = 1
                optimizations['thread_count'] = 2
                optimizations['target_fps'] = 20
            
            # Windows-specific optimizations for better FPS
            optimizations['use_directshow'] = True
            optimizations['enable_hardware_acceleration'] = True
            optimizations['use_mjpeg'] = True  # Better compression
            optimizations['reduce_latency'] = True
            optimizations['auto_exposure'] = False  # Disable for consistent FPS
            optimizations['frame_drop_enabled'] = True  # Allow frame dropping for real-time
            
            self.logger.info(f"Windows optimizations: {optimizations}")
            return optimizations
            
        except Exception as e:
            self.logger.error(f"Performance optimization failed: {e}")
            return optimizations
    
    def create_windows_shortcut(self, target_path: str, shortcut_path: str, 
                               description: str = "Drone Human Detection") -> bool:
        """Create a Windows shortcut for the application."""
        if not self.is_windows:
            return False
        
        try:
            import win32com.client
            
            shell = win32com.client.Dispatch("WScript.Shell")
            shortcut = shell.CreateShortCut(shortcut_path)
            shortcut.Targetpath = target_path
            shortcut.Description = description
            shortcut.save()
            
            self.logger.info(f"Windows shortcut created: {shortcut_path}")
            return True
            
        except ImportError:
            self.logger.warning("pywin32 not installed, cannot create shortcuts")
            return False
        except Exception as e:
            self.logger.error(f"Failed to create Windows shortcut: {e}")
            return False
    
    def setup_windows_firewall_rules(self) -> bool:
        """Setup Windows firewall rules for network camera connections."""
        if not self.is_windows:
            return False
        
        try:
            # This would require admin privileges
            self.logger.info("Consider adding firewall rules for drone camera connections")
            self.logger.info("Run as administrator and execute:")
            self.logger.info("netsh advfirewall firewall add rule name='Drone Camera' dir=in action=allow protocol=TCP localport=8080")
            self.logger.info("netsh advfirewall firewall add rule name='Drone RTSP' dir=in action=allow protocol=TCP localport=554")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Firewall configuration guidance failed: {e}")
            return False


# Global instance
windows_compat = WindowsCompatibility()


def ensure_windows_compatibility():
    """Main function to ensure Windows 11 compatibility."""
    if windows_compat.is_windows:
        return windows_compat.setup_windows_environment()
    return True


if __name__ == "__main__":
    # Test Windows compatibility
    ensure_windows_compatibility()
    print(f"Windows compatibility check completed")
    
    if windows_compat.is_windows:
        cameras = windows_compat.detect_windows_cameras()
        print(f"Detected {len(cameras)} cameras")
        
        optimizations = windows_compat.optimize_for_windows_performance()
        print(f"Performance optimizations: {optimizations}")
