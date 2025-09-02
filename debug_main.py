#!/usr/bin/env python3
"""
Debug version of main.py to help troubleshoot bounding box coordinate issues.

This script provides detailed logging and debugging information for detection coordinates.
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


def setup_debug_logging():
    """Set up detailed debug logging."""
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('drone_detection_debug.log')
        ]
    )
    
    # Set specific logger levels for detailed debugging
    logging.getLogger('drone_detection.human_detector').setLevel(logging.DEBUG)
    logging.getLogger('drone_detection.display_manager').setLevel(logging.DEBUG)
    logging.getLogger('drone_detection.camera_manager').setLevel(logging.DEBUG)


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Drone Human Detection System - Debug Version"
    )
    parser.add_argument(
        "--camera-source",
        choices=["auto", "laptop", "drone"],
        default="laptop",  # Default to laptop for debugging
        help="Camera source to use (default: laptop)"
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
        default=0.3,  # Lower threshold for debugging
        help="Detection confidence threshold (default: 0.3)"
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
        default=15,  # Lower FPS for debugging
        help="Camera frames-per-second target (default: 15)"
    )
    parser.add_argument(
        "--gui",
        action="store_true",
        default=True,
        help="Start with GUI display (default: True)"
    )
    parser.add_argument(
        "--debug-frames",
        action="store_true",
        help="Save debug frames to disk"
    )
    return parser.parse_args()


def main():
    """Main application entry point with debug features."""
    args = parse_arguments()
    
    # Set up debug logging
    setup_debug_logging()
    logger = logging.getLogger('debug_main')
    
    # Display system information
    logger.info("=" * 60)
    logger.info("DRONE HUMAN DETECTION - DEBUG MODE")
    logger.info("=" * 60)
    logger.info(f"Platform: {platform.system()} {platform.release()}")
    logger.info(f"Python: {platform.python_version()}")
    logger.info(f"Debug mode: ENABLED")
    logger.info(f"Arguments: {vars(args)}")
    
    # Initialize Windows compatibility if needed
    if ensure_windows_compatibility and platform.system().lower() == 'windows':
        logger.info("Setting up Windows 11 compatibility...")
        if not ensure_windows_compatibility():
            logger.warning("Windows compatibility setup failed, but continuing...")

    # Parse resolution
    try:
        width, height = map(int, args.resolution.split('x'))
        resolution = (width, height)
        logger.info(f"Target resolution: {width}x{height}")
    except ValueError:
        logger.error(f"Invalid resolution format: {args.resolution}")
        sys.exit(1)

    # Basic startup validation
    try:
        import cv2
        logger.info(f"OpenCV version: {cv2.__version__}")
        
        # Test camera access
        if args.camera_source in ["laptop", "auto"]:
            test_cap = cv2.VideoCapture(args.device_id)
            if test_cap.isOpened():
                ret, test_frame = test_cap.read()
                if ret and test_frame is not None:
                    frame_height, frame_width = test_frame.shape[:2]
                    logger.info(f"Camera test successful: {frame_width}x{frame_height}")
                else:
                    logger.warning("Camera test: Could not capture frame")
                test_cap.release()
            else:
                logger.warning(f"Camera test: Could not open camera {args.device_id}")
        
    except Exception as e:
        logger.error(f"Missing dependency: OpenCV is required ({e})")
        sys.exit(1)

    # Test YOLOv8 model loading
    try:
        from drone_detection.human_detector import HumanDetector
        detector = HumanDetector(confidence_threshold=args.confidence)
        if detector.load_model():
            logger.info("YOLOv8 model loaded successfully")
        else:
            logger.error("Failed to load YOLOv8 model")
            sys.exit(1)
    except Exception as e:
        logger.error(f"YOLOv8 test failed: {e}")
        sys.exit(1)

    # Build controller and camera config
    controller = MainController()
    
    # Inject debug-enhanced GUI display manager
    if args.gui:
        try:
            from drone_detection.display_manager import DisplayManager
            # Use enhanced display manager with debugging
            controller.display_manager = DisplayManager("🔍 Debug: Drone Human Detection")
            logger.info("Debug display manager loaded")
        except Exception as e:
            logger.warning(f'Display manager setup failed: {e}')

    # Apply configuration
    if args.camera_source in ('drone', 'laptop'):
        cfg = CameraConfig(
            source_type=args.camera_source, 
            device_id=args.device_id,
            resolution=resolution, 
            fps=args.fps, 
            connection_timeout=5.0
        )
        controller.drone_config = cfg if args.camera_source == 'drone' else controller.drone_config
        controller.laptop_config = cfg if args.camera_source == 'laptop' else controller.laptop_config

    # Set detector confidence threshold
    desired_confidence = args.confidence

    # Initialize components
    logger.info("Initializing system components...")
    if not controller.initialize_components():
        logger.error('Failed to initialize system components')
        sys.exit(1)

    # Apply confidence threshold
    if controller.human_detector:
        controller.human_detector.set_confidence_threshold(desired_confidence)
        logger.info(f"Detection confidence threshold set to: {desired_confidence}")

    logger.info("=" * 60)
    logger.info('DEBUG MODE ACTIVE - Starting main loop')
    logger.info("Controls: 'q' or ESC to quit, 'c' to switch camera, 'f' for fullscreen")
    logger.info("Check 'drone_detection_debug.log' for detailed coordinate information")
    logger.info("=" * 60)

    try:
        controller.app_state.is_running = True
        frame_count = 0

        while controller.app_state.is_running:
            frame_count += 1
            
            # Process frame with debug info
            if frame_count % 30 == 0:  # Every 30 frames
                logger.info(f"Processing frame {frame_count}...")
            
            controller.process_frame()

            # Keyboard controls
            if controller.display_manager:
                key = getattr(controller.display_manager, 'last_key', None)
                if key == ord('c'):
                    logger.info("Camera switch requested")
                    controller.force_camera_switch()
                if key == ord('q') or key == 27:
                    logger.info("Quit requested")
                    controller.app_state.is_running = False
                if key == ord('d'):
                    logger.info("Debug info requested")
                    # Print current detection stats
                    if hasattr(controller, 'last_detections'):
                        logger.info(f"Last detection count: {len(controller.last_detections)}")

            # Small sleep to avoid tight loop
            time.sleep(0.001)

    except KeyboardInterrupt:
        logger.info('Keyboard interrupt received')
    except Exception as e:
        logger.error(f'Unexpected error in main loop: {e}', exc_info=True)
    finally:
        controller._graceful_shutdown()
        logger.info('Debug session completed')
        logger.info(f'Debug log saved to: drone_detection_debug.log')


if __name__ == "__main__":
    main()
