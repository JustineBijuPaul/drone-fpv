"""Data models for the drone human detection system."""

from dataclasses import dataclass
from typing import Tuple, Optional


@dataclass
class DetectionResult:
    """Represents a human detection result."""
    bbox: Tuple[int, int, int, int]  # x1, y1, x2, y2
    confidence: float
    class_id: int
    class_name: str


@dataclass
class CameraConfig:
    """Configuration for camera sources."""
    source_type: str  # 'drone' or 'laptop'
    device_id: int
    resolution: Tuple[int, int]
    fps: int
    connection_timeout: float


@dataclass
class AppState:
    """Application state management."""
    is_running: bool
    current_camera: str
    detection_enabled: bool
    fps_counter: float
    error_message: Optional[str]