#!/usr/bin/env python3
"""Run main app with guaranteed Windows-safe display - works around any detection issues."""

import sys
import os
import platform
import logging

# Add project directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def patch_main_controller():
    """Patch MainController to force Windows-safe display."""
    from drone_detection import main_controller
    
    # Store original method
    original_init_display = main_controller.MainController._initialize_display_manager
    
    def patched_init_display(self):
        """Patched version that forces Windows-safe display on Windows."""
        try:
            if self.display_manager is None:
                if platform.system().lower() == 'windows':
                    from drone_detection.windows_safe_display import WindowsSafeDisplayManager
                    self.display_manager = WindowsSafeDisplayManager()
                    self.logger.info("🔧 FORCED Windows-safe display manager (patched)")
                else:
                    from drone_detection.display_manager import DisplayManager
                    self.display_manager = DisplayManager()
                    self.logger.info("Using standard display manager")
            self.logger.info("Display manager initialized successfully")
            return True
        except Exception as e:
            self.logger.error(f"Display manager initialization failed: {e}")
            return False
    
    # Apply patch
    main_controller.MainController._initialize_display_manager = patched_init_display
    print("✅ MainController patched to force Windows-safe display")

def run_patched_main():
    """Run the main application with patched Windows-safe display."""
    print("🔧 PATCHED MAIN APPLICATION")
    print("=" * 50)
    print(f"Platform: {platform.system()}")
    print("Patching MainController to force Windows-safe display...")
    
    # Apply patch
    patch_main_controller()
    
    # Setup logging
    logging.basicConfig(level=logging.INFO, 
                       format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    try:
        from drone_detection.main_controller import MainController
        from drone_detection.models import CameraConfig
        
        # Create and configure controller
        controller = MainController()
        
        # Set camera configs
        controller.drone_config = CameraConfig(
            source_type='drone',
            device_id=0,
            resolution=(640, 480),
            fps=30,
            connection_timeout=10.0
        )
        
        controller.laptop_config = CameraConfig(
            source_type='laptop',
            device_id=0,
            resolution=(640, 480),
            fps=30,
            connection_timeout=5.0
        )
        
        print("🚀 Initializing components...")
        if not controller.initialize_components():
            print("❌ Failed to initialize components")
            return False
        
        print("✅ All components initialized")
        print("📱 Starting main loop... Press 'q' to quit")
        print("🎯 Should show NO Tkinter threading errors!")
        
        # Set confidence and run
        controller.human_detector.set_confidence_threshold(0.5)
        controller.run()
        
        return True
        
    except KeyboardInterrupt:
        print("\n⚠️  Stopped by user")
        return True
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("This script patches MainController to force Windows-safe display")
    print("It bypasses any platform detection issues and guarantees the fix is applied")
    print()
    
    success = run_patched_main()
    
    if success:
        print("\n🎉 Application completed!")
        print("If no Tkinter errors appeared, the Windows-safe fix is working!")
    else:
        print("\n❌ Application failed")
        print("Check the error output above")
