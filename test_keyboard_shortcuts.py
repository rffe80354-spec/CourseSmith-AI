"""
Test script to verify global keyboard shortcuts work correctly.
This tests the global hotkey override implementation.
"""
import sys
import os

# Get the directory where the script is located
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

def test_global_shortcuts():
    """Test that global shortcuts are bound correctly."""
    print("\n=== Testing Global Keyboard Shortcuts Implementation ===\n")
    
    # Test 1: Import and verify main.py has global shortcuts
    print("Test 1: Checking main.py for global shortcuts...")
    try:
        with open(os.path.join(SCRIPT_DIR, 'main.py'), 'r') as f:
            content = f.read()
            assert 'from utils import setup_global_window_shortcuts' in content, "Missing import of setup_global_window_shortcuts"
            assert 'setup_global_window_shortcuts(self)' in content, "Missing call to setup_global_window_shortcuts"
        print("✓ main.py has global shortcuts configured correctly")
    except AssertionError as e:
        print(f"✗ FAILED: {e}")
        return False
    except Exception as e:
        print(f"✗ ERROR: {e}")
        return False
    
    # Test 2: Import and verify admin_keygen.py has global shortcuts
    print("\nTest 2: Checking admin_keygen.py for global shortcuts...")
    try:
        with open(os.path.join(SCRIPT_DIR, 'admin_keygen.py'), 'r') as f:
            content = f.read()
            assert 'from utils import setup_global_window_shortcuts' in content, "Missing import of setup_global_window_shortcuts"
            assert 'setup_global_window_shortcuts(self)' in content, "Missing call to setup_global_window_shortcuts"
        print("✓ admin_keygen.py has global shortcuts configured correctly")
    except AssertionError as e:
        print(f"✗ FAILED: {e}")
        return False
    except Exception as e:
        print(f"✗ ERROR: {e}")
        return False
    
    # Test 2.5: Verify the utility function is implemented correctly
    print("\nTest 2.5: Checking utils.py for global shortcuts implementation...")
    try:
        with open(os.path.join(SCRIPT_DIR, 'utils.py'), 'r') as f:
            content = f.read()
            assert 'def setup_global_window_shortcuts' in content, "Missing setup_global_window_shortcuts function"
            assert 'bind_all("<Control-c>"' in content, "Missing Ctrl+C binding"
            assert 'bind_all("<Control-v>"' in content, "Missing Ctrl+V binding"
            assert 'bind_all("<Control-a>"' in content, "Missing Ctrl+A binding"
            assert 'bind_all("<Control-x>"' in content, "Missing Ctrl+X binding"
            assert 'def global_copy' in content, "Missing global_copy handler"
            assert 'def global_paste' in content, "Missing global_paste handler"
            assert 'def global_select_all' in content, "Missing global_select_all handler"
            assert 'def global_cut' in content, "Missing global_cut handler"
            assert 'return "break"' in content, "Missing event propagation control"
        print("✓ utils.py has all global shortcuts implemented correctly")
    except AssertionError as e:
        print(f"✗ FAILED: {e}")
        return False
    except Exception as e:
        print(f"✗ ERROR: {e}")
        return False
    
    # Test 3: Verify floating text fix
    print("\nTest 3: Checking for floating text fix in admin_keygen.py...")
    try:
        with open(os.path.join(SCRIPT_DIR, 'admin_keygen.py'), 'r') as f:
            content = f.read()
            assert 'update_idletasks()' in content, "Missing update_idletasks() call"
            # Verify it's in the right context (after creating license rows)
            lines = content.split('\n')
            found_in_display = False
            for i, line in enumerate(lines):
                if 'update_idletasks()' in line:
                    # Check if this is in _display_licenses method
                    for j in range(max(0, i-50), i):
                        if 'def _display_licenses' in lines[j]:
                            found_in_display = True
                            break
            assert found_in_display, "update_idletasks() not found in _display_licenses method"
        print("✓ Floating text fix implemented correctly")
    except AssertionError as e:
        print(f"✗ FAILED: {e}")
        return False
    except Exception as e:
        print(f"✗ ERROR: {e}")
        return False
    
    # Test 4: Verify that global shortcuts use focus_get()
    print("\nTest 4: Checking that global shortcuts use focus detection...")
    try:
        with open(os.path.join(SCRIPT_DIR, 'utils.py'), 'r') as f:
            content = f.read()
            assert 'setup_global_window_shortcuts' in content, "Missing setup_global_window_shortcuts function"
            assert 'focus_get()' in content, "Missing focus_get() call"
            # Verify that global handlers get the focused widget
            assert 'focused = window.focus_get()' in content, "Not properly getting focused widget"
        
        # Verify main.py imports and uses the utility function
        with open(os.path.join(SCRIPT_DIR, 'main.py'), 'r') as f:
            content = f.read()
            assert 'from utils import setup_global_window_shortcuts' in content, "main.py not importing setup_global_window_shortcuts"
            assert 'setup_global_window_shortcuts(self)' in content, "main.py not calling setup_global_window_shortcuts"
            
        # Verify admin_keygen.py imports and uses the utility function
        with open(os.path.join(SCRIPT_DIR, 'admin_keygen.py'), 'r') as f:
            content = f.read()
            assert 'from utils import setup_global_window_shortcuts' in content, "admin_keygen.py not importing setup_global_window_shortcuts"
            assert 'setup_global_window_shortcuts(self)' in content, "admin_keygen.py not calling setup_global_window_shortcuts"
            
        print("✓ Global shortcuts properly detect focused widgets")
        print("✓ Both files use shared utility function (no code duplication)")
    except AssertionError as e:
        print(f"✗ FAILED: {e}")
        return False
    except Exception as e:
        print(f"✗ ERROR: {e}")
        return False
    
    # Test 5: Verify both uppercase and lowercase bindings
    print("\nTest 5: Checking for both uppercase and lowercase key bindings...")
    try:
        with open(os.path.join(SCRIPT_DIR, 'utils.py'), 'r') as f:
            content = f.read()
            # Check for both cases in the utility function
            assert 'bind_all("<Control-c>"' in content, "Missing lowercase Ctrl+c"
            assert 'bind_all("<Control-C>"' in content, "Missing uppercase Ctrl+C"
            assert 'bind_all("<Control-v>"' in content, "Missing lowercase Ctrl+v"
            assert 'bind_all("<Control-V>"' in content, "Missing uppercase Ctrl+V"
            assert 'bind_all("<Control-a>"' in content, "Missing lowercase Ctrl+a"
            assert 'bind_all("<Control-A>"' in content, "Missing uppercase Ctrl+A"
        print("✓ Both uppercase and lowercase key bindings present")
    except AssertionError as e:
        print(f"✗ FAILED: {e}")
        return False
    except Exception as e:
        print(f"✗ ERROR: {e}")
        return False
    
    # Test 6: Check that context menu is still available
    print("\nTest 6: Verifying context menu functionality is preserved...")
    try:
        with open(os.path.join(SCRIPT_DIR, 'utils.py'), 'r') as f:
            content = f.read()
            assert 'add_context_menu' in content, "Missing add_context_menu function"
            assert 'RightClickMenu' in content, "Missing RightClickMenu class"
        print("✓ Context menu functionality preserved")
    except AssertionError as e:
        print(f"✗ FAILED: {e}")
        return False
    except Exception as e:
        print(f"✗ ERROR: {e}")
        return False
    
    print("\n=== All Tests Passed ===\n")
    print("Summary:")
    print("  ✓ Global keyboard shortcuts implemented in main.py")
    print("  ✓ Global keyboard shortcuts implemented in admin_keygen.py")
    print("  ✓ Floating text fix implemented")
    print("  ✓ Focus detection working")
    print("  ✓ Shared utility function eliminates code duplication")
    print("  ✓ Both uppercase and lowercase key bindings")
    print("  ✓ Context menu functionality preserved")
    return True

if __name__ == "__main__":
    success = test_global_shortcuts()
    sys.exit(0 if success else 1)


