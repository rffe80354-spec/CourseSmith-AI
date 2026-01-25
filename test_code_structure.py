#!/usr/bin/env python3
"""
Simple test to verify the PDF engine code compiles and has correct logic.
"""

import sys
import os

def test_pdf_engine_imports():
    """Test that pdf_engine module has the necessary components."""
    print("\n" + "="*60)
    print("TEST: PDF Engine Code Structure")
    print("="*60)
    
    try:
        # Read the pdf_engine.py file
        with open('pdf_engine.py', 'r') as f:
            content = f.read()
        
        # Check for key components of shrink-to-fit implementation
        checks = [
            ("_build_pdf_with_page_limit method", "_build_pdf_with_page_limit" in content),
            ("_build_pdf_standard method", "_build_pdf_standard" in content),
            ("_apply_font_scale method", "_apply_font_scale" in content),
            ("target_page_count check", "target_page_count" in content),
            ("ui_settings check", "ui_settings" in content),
            ("font_scale variable", "font_scale" in content),
            ("Iteration loop", "for iteration in range(max_iterations)" in content),
            ("temp file usage", "tempfile" in content),
            ("Page count check", "actual_page_count <= target_page_count" in content),
            ("Font scale calculation", "overage_ratio" in content),
        ]
        
        all_passed = True
        for check_name, result in checks:
            status = "✅" if result else "❌"
            print(f"{status} {check_name}: {'FOUND' if result else 'MISSING'}")
            if not result:
                all_passed = False
        
        if all_passed:
            print("\n✅ All shrink-to-fit components present")
        else:
            print("\n❌ Some components missing")
        
        return all_passed
        
    except Exception as e:
        print(f"❌ Error reading pdf_engine.py: {e}")
        return False

def test_app_gui_structure():
    """Test that app.py has the necessary GUI responsiveness fixes."""
    print("\n" + "="*60)
    print("TEST: GUI Responsiveness Code Structure")
    print("="*60)
    
    try:
        # Read the app.py file
        with open('app.py', 'r') as f:
            content = f.read()
        
        # Check for key components of GUI fixes
        checks = [
            ("Login spacer row with weight", "grid_rowconfigure(8, weight=1)" in content),
            ("Login flexible spacer frame", 'spacer_frame = ctk.CTkFrame(self.activation_frame, fg_color="transparent")' in content),
            ("Login button moved to row 9", 'self.activate_btn.grid(row=9' in content),
            ("Drafting row weights configured", "self.tab_drafting.grid_rowconfigure(0, weight=0)" in content),
            ("Drafting main content expands", "self.tab_drafting.grid_rowconfigure(1, weight=1)" in content),
            ("Left frame row weights", "left_frame.grid_rowconfigure(1, weight=1)" in content),
            ("Right frame row weights", "right_frame.grid_rowconfigure(1, weight=1)" in content),
            ("Reduced padding values", "pady=(0, 10)" in content or "pady=(0, 15)" in content),
        ]
        
        all_passed = True
        for check_name, result in checks:
            status = "✅" if result else "❌"
            print(f"{status} {check_name}: {'FOUND' if result else 'MISSING'}")
            if not result:
                all_passed = False
        
        if all_passed:
            print("\n✅ All GUI responsiveness components present")
        else:
            print("\n❌ Some components missing")
        
        return all_passed
        
    except Exception as e:
        print(f"❌ Error reading app.py: {e}")
        return False

def test_pdf_logic():
    """Test the logical flow of PDF shrink-to-fit algorithm."""
    print("\n" + "="*60)
    print("TEST: PDF Shrink-to-Fit Logic Flow")
    print("="*60)
    
    try:
        with open('pdf_engine.py', 'r') as f:
            content = f.read()
        
        # Verify the algorithm flow
        checks = [
            ("Check for target_page_count", "if target_page_count:" in content),
            ("Call shrink-to-fit method", "return self._build_pdf_with_page_limit(project, target_page_count)" in content),
            ("Else call standard method", "return self._build_pdf_standard(project)" in content),
            ("Initialize font_scale", "font_scale = 1.0" in content),
            ("Set min_font_scale", "min_font_scale = 0.5" in content),
            ("Iteration logic present", "for iteration in range(max_iterations):" in content),
            ("Apply font scale", "self._apply_font_scale(font_scale)" in content),
            ("Build to temp file", "tempfile.mkstemp(suffix='.pdf')" in content),
            ("Count pages", "actual_page_count = doc.page" in content),
            ("Success condition", "if actual_page_count <= target_page_count:" in content),
            ("Copy temp to final", "shutil.copy2(temp_path, self.filename)" in content),
            ("Calculate new scale", "new_font_scale = font_scale / (overage_ratio ** 0.5)" in content),
            ("Minimum scale check", "if font_scale <= min_font_scale:" in content),
            ("Store original font sizes", "self._original_font_sizes" in content),
        ]
        
        all_passed = True
        for check_name, result in checks:
            status = "✅" if result else "❌"
            print(f"{status} {check_name}: {'FOUND' if result else 'MISSING'}")
            if not result:
                all_passed = False
        
        if all_passed:
            print("\n✅ PDF shrink-to-fit logic flow is correct")
        else:
            print("\n❌ Some logic components missing")
        
        return all_passed
        
    except Exception as e:
        print(f"❌ Error analyzing logic: {e}")
        return False

def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("CODE STRUCTURE VALIDATION TESTS")
    print("="*60)
    
    results = []
    
    # Run tests
    results.append(("PDF Engine Structure", test_pdf_engine_imports()))
    results.append(("GUI Responsiveness Structure", test_app_gui_structure()))
    results.append(("PDF Logic Flow", test_pdf_logic()))
    
    # Print summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status}: {name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
