#!/usr/bin/env python3
"""Debug why Windows-safe display manager is not being used."""

import platform
import sys
import os

# Add project directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def debug_display_manager_selection():
    """Debug the display manager selection process."""
    print("🔍 DEBUGGING DISPLAY MANAGER SELECTION")
    print("=" * 50)
    
    # Step 1: Check platform detection
    print("1️⃣ Platform Detection:")
    system = platform.system()
    is_windows = system.lower() == 'windows'
    print(f"   platform.system(): '{system}'")
    print(f"   system.lower(): '{system.lower()}'")
    print(f"   is_windows check: {is_windows}")
    
    # Step 2: Check imports
    print("\n2️⃣ Import Check:")
    try:
        from drone_detection.main_controller import MainController
        print("   ✅ MainController imported successfully")
    except Exception as e:
        print(f"   ❌ MainController import failed: {e}")
        return
    
    try:
        from drone_detection.main_controller import WindowsSafeDisplayManager
        print(f"   WindowsSafeDisplayManager: {WindowsSafeDisplayManager}")
        if WindowsSafeDisplayManager is None:
            print("   ⚠️  WindowsSafeDisplayManager is None - import failed")
        else:
            print("   ✅ WindowsSafeDisplayManager imported successfully")
    except Exception as e:
        print(f"   ❌ WindowsSafeDisplayManager import failed: {e}")
    
    # Step 3: Check the actual condition in MainController
    print("\n3️⃣ Testing Condition Logic:")
    try:
        from drone_detection.main_controller import platform as mc_platform
        from drone_detection.main_controller import WindowsSafeDisplayManager as mc_wsm
        
        condition1 = mc_platform.system().lower() == 'windows'
        condition2 = mc_wsm is not None
        
        print(f"   platform.system().lower() == 'windows': {condition1}")
        print(f"   WindowsSafeDisplayManager is not None: {condition2}")
        print(f"   Combined condition: {condition1 and condition2}")
        
        if condition1 and condition2:
            print("   ✅ Should use WindowsSafeDisplayManager")
        else:
            print("   ❌ Will use standard DisplayManager")
            if not condition1:
                print("       Problem: Not detected as Windows")
            if not condition2:
                print("       Problem: WindowsSafeDisplayManager not available")
                
    except Exception as e:
        print(f"   ❌ Condition test failed: {e}")
    
    # Step 4: Test direct instantiation
    print("\n4️⃣ Direct Instantiation Test:")
    try:
        from drone_detection.display_manager import DisplayManager
        from drone_detection.windows_safe_display import WindowsSafeDisplayManager
        
        dm = DisplayManager()
        print("   ✅ DisplayManager created")
        
        wsm = WindowsSafeDisplayManager()
        print("   ✅ WindowsSafeDisplayManager created")
        print(f"   WSM is_windows: {wsm.is_windows}")
        
    except Exception as e:
        print(f"   ❌ Direct instantiation failed: {e}")
    
    # Step 5: Simulate MainController logic
    print("\n5️⃣ Simulating MainController Logic:")
    try:
        from drone_detection.main_controller import MainController
        from drone_detection.windows_safe_display import WindowsSafeDisplayManager
        
        controller = MainController()
        
        # Force the same logic as in _initialize_display_manager
        if platform.system().lower() == 'windows':
            if WindowsSafeDisplayManager:
                controller.display_manager = WindowsSafeDisplayManager()
                print("   ✅ Set WindowsSafeDisplayManager")
                print("   This should work in the main app!")
            else:
                print("   ❌ WindowsSafeDisplayManager not available")
                controller.display_manager = None
        else:
            print("   ℹ️  Not Windows - would use standard DisplayManager")
            
    except Exception as e:
        print(f"   ❌ Simulation failed: {e}")
    
    print(f"\n🎯 CONCLUSION:")
    if is_windows:
        print(f"   On Windows system - should use WindowsSafeDisplayManager")
        print(f"   If main app shows Tkinter errors, there's a logic bug")
    else:
        print(f"   On {system} system - standard DisplayManager is fine")

if __name__ == "__main__":
    debug_display_manager_selection()
