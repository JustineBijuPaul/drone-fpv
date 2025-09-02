#!/usr/bin/env python3
"""
Main entry point for the Drone Human Detection System.

This script initializes and runs the human detection system with support
for both drone receiver feeds and laptop camera fallback.
"""

import argparse
import sys
import logging
import time
import platform

from drone_detection.models import CameraConfig, AppState
from drone_detection.main_controller import MainController

# Import Windows compatibility utilities
try:
    from drone_detection.windows_compat import ensure_windows_compatibility
except ImportError:
    ensure_windows_compatibility = None


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Drone Human Detection System using YOLOv8"
    )
    parser.add_argument(
        "--camera-source",
        choices=["auto", "laptop", "drone"],
        default="auto",
        help="Camera source to use (default: auto)"
    )
    parser.add_argument(
        "--device-id",
        type=int,
        default=0,
        help="Camera device ID (default: 0)"
    )
    parser.add_argument(
        "--confidence",
        type=float,
        default=0.5,
        help="Detection confidence threshold (default: 0.5)"
    )
    parser.add_argument(
        "--resolution",
        type=str,
        default="640x480",
        help="Camera resolution (default: 640x480)"
    )
    parser.add_argument(
        "--fps",
        type=int,
        default=30,
        help="Camera frames-per-second target (default: 30)"
    )
    parser.add_argument(
        "--gui",
        action="store_true",
        help="Start with the Tkinter GUI display (if available)"
    )
    return parser.parse_args()


def main():
    """Main application entry point."""
    args = parse_arguments()
    
    # Configure logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logger = logging.getLogger('main')
    
    # Display system information
    logger.info(f"Running on {platform.system()} {platform.release()}")
    
    # Initialize Windows compatibility if needed
    if ensure_windows_compatibility and platform.system().lower() == 'windows':
        logger.info("Setting up Windows 11 compatibility...")
        if not ensure_windows_compatibility():
            logger.warning("Windows compatibility setup failed, but continuing...")

    # Parse resolution
    try:
        width, height = map(int, args.resolution.split('x'))
        resolution = (width, height)
    except ValueError:
        logger.error(f"Invalid resolution format: {args.resolution}")
        sys.exit(1)

    # Basic startup validation
    try:
        import cv2  # ensure opencv is importable
        logger.info(f"OpenCV version: {cv2.__version__}")
    except Exception as e:
        logger.error(f"Missing dependency: OpenCV is required ({e})")
        sys.exit(1)

    # Build controller and camera config
    controller = MainController()
    # Optionally inject a Tkinter-based GUI display manager
    if args.gui:
        try:
            from drone_detection.tk_display_manager import TkDisplayManager
            controller.display_manager = TkDisplayManager()
        except Exception:
            logger = logging.getLogger('main')
            logger.warning('Tkinter GUI not available; falling back to default display manager')

    # Apply configuration to controller's camera configs when possible
    if args.camera_source in ('drone', 'laptop'):
        cfg = CameraConfig(source_type=args.camera_source, device_id=args.device_id,
                           resolution=resolution, fps=args.fps, connection_timeout=5.0)
        # replace both configs conservatively
        controller.drone_config = cfg if args.camera_source == 'drone' else controller.drone_config
        controller.laptop_config = cfg if args.camera_source == 'laptop' else controller.laptop_config

    # Set detector confidence threshold if detector exists later
    desired_confidence = args.confidence

    # Initialize components
    if not controller.initialize_components():
        logger.error('Failed to initialize system components')
        sys.exit(1)

    # Apply confidence threshold
    if controller.human_detector:
        controller.human_detector.set_confidence_threshold(desired_confidence)

    logger.info('Starting main loop. Press q or ESC to quit, c to switch camera')

    try:
        controller.app_state.is_running = True

        while controller.app_state.is_running:
            controller.process_frame()

            # Keyboard controls: read last key from display manager
            if controller.display_manager:
                key = getattr(controller.display_manager, 'last_key', None)
                if key == ord('c'):
                    controller.force_camera_switch()
                if key == ord('q') or key == 27:
                    controller.app_state.is_running = False

            # small sleep to avoid tight loop
            time.sleep(0.001)

    except KeyboardInterrupt:
        logger.info('Keyboard interrupt received')
    finally:
        controller._graceful_shutdown()
        logger.info('Application exited')


if __name__ == "__main__":
    main()