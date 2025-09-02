#!/usr/bin/env python3
"""Test script to verify Windows-safe display manager works correctly."""

import platform
import sys
import os

# Add project directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from drone_detection.display_manager import DisplayManager
from drone_detection.windows_safe_display import WindowsSafeDisplayManager

def test_display_managers():
    """Test both display managers to verify Windows compatibility."""
    print("🖼️  DISPLAY MANAGER TEST")
    print("=" * 40)
    print(f"Platform: {platform.system()}")
    print()
    
    # Test standard display manager
    print("1️⃣ Testing Standard Display Manager:")
    try:
        display1 = DisplayManager()
        print("✅ Standard DisplayManager created successfully")
    except Exception as e:
        print(f"❌ Standard DisplayManager failed: {e}")
    
    # Test Windows-safe display manager
    print("\n2️⃣ Testing Windows-Safe Display Manager:")
    try:
        display2 = WindowsSafeDisplayManager()
        print("✅ WindowsSafeDisplayManager created successfully")
        print(f"   Windows mode: {display2.is_windows}")
        print(f"   Window title: {display2.window_title}")
    except Exception as e:
        print(f"❌ WindowsSafeDisplayManager failed: {e}")
    
    # Test platform detection logic
    print("\n3️⃣ Platform Detection Logic:")
    is_windows = platform.system().lower() == 'windows'
    print(f"   platform.system(): {platform.system()}")
    print(f"   is_windows check: {is_windows}")
    
    if is_windows:
        print("   🔧 On Windows: Should use WindowsSafeDisplayManager")
        recommended = "WindowsSafeDisplayManager"
    else:
        print("   🔧 On non-Windows: Can use either DisplayManager")
        recommended = "DisplayManager (standard)"
    
    print(f"   Recommended: {recommended}")
    
    print("\n4️⃣ Import Test:")
    try:
        from drone_detection.main_controller import MainController
        print("✅ MainController imports WindowsSafeDisplayManager correctly")
        
        # Check if WindowsSafeDisplayManager import worked
        from drone_detection.main_controller import WindowsSafeDisplayManager as WSM
        if WSM is None:
            print("⚠️  WindowsSafeDisplayManager import is None")
        else:
            print("✅ WindowsSafeDisplayManager import successful")
            
    except Exception as e:
        print(f"❌ Import test failed: {e}")
    
    print("\n🎯 Summary:")
    if is_windows:
        print("   - On Windows, use WindowsSafeDisplayManager to avoid Tkinter threading issues")
        print("   - The 'RuntimeError: Calling Tcl from different apartment' should be resolved")
    else:
        print("   - On non-Windows systems, standard DisplayManager works fine")
        print("   - No Tkinter threading issues expected")

if __name__ == "__main__":
    test_display_managers()
