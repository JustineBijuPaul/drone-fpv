#!/usr/bin/env python3
"""Force Windows-safe mode test - Run main application with guaranteed Windows-safe display."""

import os
import sys
import platform
import logging

# Add project directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from drone_detection.main_controller import MainController
from drone_detection.windows_safe_display import WindowsSafeDisplayManager
from drone_detection.models import CameraConfig

def run_with_windows_safe_display():
    """Run the application with forced Windows-safe display."""
    print("🔧 FORCE WINDOWS-SAFE DISPLAY TEST")
    print("=" * 50)
    print(f"Platform: {platform.system()}")
    print("Forcing Windows-safe display manager...")
    print()
    
    # Setup logging
    logging.basicConfig(level=logging.INFO, 
                       format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    try:
        # Create controller
        controller = MainController()
        
        # Force Windows-safe display manager
        controller.display_manager = WindowsSafeDisplayManager()
        print("✅ Forced WindowsSafeDisplayManager")
        
        # Configure for laptop camera
        controller.drone_config = CameraConfig(
            source_type='drone',
            device_id=0,
            resolution=(640, 480),
            fps=30
        )
        
        controller.laptop_config = CameraConfig(
            source_type='laptop',
            device_id=0,
            resolution=(640, 480),
            fps=30
        )
        
        # Initialize components
        print("🚀 Initializing components...")
        if not controller.initialize_components():
            print("❌ Failed to initialize components")
            return False
        
        print("✅ All components initialized successfully")
        print("📱 Starting main loop... Press 'q' to quit")
        print("🎯 Watch for bounding boxes - they should appear around detected people")
        print("🔧 No Tkinter threading errors should occur")
        
        # Set confidence threshold
        controller.human_detector.set_confidence_threshold(0.5)
        
        # Run main loop
        controller.run()
        
        return True
        
    except KeyboardInterrupt:
        print("\n⚠️  Application interrupted by user")
        return True
    except Exception as e:
        print(f"\n❌ Application failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("This script forces the use of WindowsSafeDisplayManager")
    print("It should resolve the 'Calling Tcl from different apartment' error on Windows")
    print()
    
    success = run_with_windows_safe_display()
    
    if success:
        print("\n🎉 Application completed successfully!")
        print("If you saw detection working without Tkinter errors, the fix is working!")
    else:
        print("\n❌ Application encountered errors")
        print("Check the logs above for debugging information")
