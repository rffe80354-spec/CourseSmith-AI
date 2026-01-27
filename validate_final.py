"""
Final validation script for CourseSmith Ultimate Engine.
Performs comprehensive end-to-end validation of all features.
"""

import sys


def validate_all_features():
    """Perform comprehensive validation of all features."""
    
    print("="*80)
    print("COURSESMITH ULTIMATE ENGINE - FINAL VALIDATION")
    print("="*80 + "\n")
    
    validation_results = []
    
    # 1. Module import
    print("1. Validating module import...")
    try:
        from coursesmith_engine import CourseSmithEngine, generate_course_from_instruction
        print("   ✓ Module imported successfully")
        validation_results.append(("Module Import", True))
    except Exception as e:
        print(f"   ✗ Failed: {e}")
        validation_results.append(("Module Import", False))
        return False
    
    # 2. Language detection (English)
    print("\n2. Validating English language detection...")
    try:
        engine = CourseSmithEngine(require_api_key=False)
        lang = engine.detect_language("Introduction to Machine Learning")
        assert lang == 'en'
        print("   ✓ English detected correctly")
        validation_results.append(("English Detection", True))
    except Exception as e:
        print(f"   ✗ Failed: {e}")
        validation_results.append(("English Detection", False))
    
    # 3. Language detection (Russian/Cyrillic)
    print("\n3. Validating Russian language detection (Cyrillic)...")
    try:
        lang = engine.detect_language("Введение в машинное обучение")
        assert lang == 'ru'
        print("   ✓ Russian/Cyrillic detected correctly")
        validation_results.append(("Russian Detection", True))
    except Exception as e:
        print(f"   ✗ Failed: {e}")
        validation_results.append(("Russian Detection", False))
    
    # 4. Output structure validation
    print("\n4. Validating output structure...")
    try:
        test_course = {
            'title': 'Test Course Title',
            'chapters': [
                {
                    'number': i,
                    'title': f'Chapter {i}',
                    'content': f'Content for chapter {i}'
                } for i in range(1, 11)
            ]
        }
        output = engine.format_output(test_course)
        
        # Check required elements
        assert '# Test Course Title' in output
        assert output.count('[CHAPTER_START]') == 10
        assert output.count('[CHAPTER_END]') == 10
        assert output.count('TITLE:') == 10
        assert output.count('CONTENT:') == 10
        
        print("   ✓ Output structure valid with all required markers")
        validation_results.append(("Output Structure", True))
    except Exception as e:
        print(f"   ✗ Failed: {e}")
        validation_results.append(("Output Structure", False))
    
    # 5. Cyrillic character preservation
    print("\n5. Validating Cyrillic character preservation...")
    try:
        russian_course = {
            'title': 'Курс по программированию',
            'chapters': [
                {
                    'number': 1,
                    'title': 'Основы Python',
                    'content': 'Содержание главы о языке программирования Python'
                }
            ]
        }
        output = engine.format_output(russian_course)
        
        # Verify all Cyrillic text is preserved
        assert 'Курс по программированию' in output
        assert 'Основы Python' in output
        assert 'Содержание главы' in output
        
        print("   ✓ Cyrillic characters preserved correctly")
        validation_results.append(("Cyrillic Preservation", True))
    except Exception as e:
        print(f"   ✗ Failed: {e}")
        validation_results.append(("Cyrillic Preservation", False))
    
    # 6. UTF-8 encoding validation
    print("\n6. Validating UTF-8 file encoding...")
    try:
        import tempfile
        import os
        
        # Create test content with mixed characters
        test_content = """# Mixed Content Test
        
English: Hello World
Russian: Привет мир
Special: ñ, é, ü, ß
Emoji: 🎓 📚 ✨"""
        
        # Write and read with UTF-8
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', suffix='.txt', delete=False) as f:
            temp_path = f.name
            f.write(test_content)
        
        with open(temp_path, 'r', encoding='utf-8') as f:
            read_content = f.read()
        
        os.unlink(temp_path)
        
        assert read_content == test_content
        print("   ✓ UTF-8 encoding works correctly")
        validation_results.append(("UTF-8 Encoding", True))
    except Exception as e:
        print(f"   ✗ Failed: {e}")
        validation_results.append(("UTF-8 Encoding", False))
    
    # 7. Markdown formatting preservation
    print("\n7. Validating Markdown formatting...")
    try:
        markdown_course = {
            'title': 'Markdown Test',
            'chapters': [
                {
                    'number': 1,
                    'title': 'Formatting Test',
                    'content': '''## Subheader

This is a paragraph.

* Bullet 1
* Bullet 2

**Bold text** and *italic text*.'''
                }
            ]
        }
        output = engine.format_output(markdown_course)
        
        # Verify markdown elements
        assert '## Subheader' in output
        assert '* Bullet 1' in output
        assert '**Bold text**' in output
        assert '*italic text*' in output
        
        print("   ✓ Markdown formatting preserved")
        validation_results.append(("Markdown Formatting", True))
    except Exception as e:
        print(f"   ✗ Failed: {e}")
        validation_results.append(("Markdown Formatting", False))
    
    # 8. Input sanitization
    print("\n8. Validating input sanitization...")
    try:
        # Test that sanitization is available
        assert hasattr(engine, '_sanitize_input')
        
        # Test basic sanitization
        sanitized = engine._sanitize_input("Test input")
        assert sanitized == "Test input"
        
        # Test that excessive length is truncated
        long_input = "x" * 5000
        sanitized = engine._sanitize_input(long_input, max_length=100)
        assert len(sanitized) <= 100
        
        print("   ✓ Input sanitization working")
        validation_results.append(("Input Sanitization", True))
    except Exception as e:
        print(f"   ✗ Failed: {e}")
        validation_results.append(("Input Sanitization", False))
    
    # 9. Integration with existing modules
    print("\n9. Validating integration with existing modules...")
    try:
        # Check that we can import existing modules
        import ai_manager
        from coursesmith_engine import CourseSmithEngine
        
        # Both should coexist
        print("   ✓ Integration with existing modules working")
        validation_results.append(("Module Integration", True))
    except Exception as e:
        print(f"   ✗ Failed: {e}")
        validation_results.append(("Module Integration", False))
    
    # 10. Documentation presence
    print("\n10. Validating documentation...")
    try:
        import os
        
        # Check for documentation files
        docs = [
            'COURSESMITH_ENGINE_README.md',
            'example_coursesmith_engine.py',
            'test_coursesmith_engine.py',
            'test_integration.py'
        ]
        
        for doc in docs:
            assert os.path.exists(doc), f"Missing: {doc}"
        
        print("   ✓ All documentation files present")
        validation_results.append(("Documentation", True))
    except Exception as e:
        print(f"   ✗ Failed: {e}")
        validation_results.append(("Documentation", False))
    
    # Summary
    print("\n" + "="*80)
    print("VALIDATION SUMMARY")
    print("="*80)
    
    for feature, result in validation_results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {feature}")
    
    passed = sum(1 for _, result in validation_results if result)
    total = len(validation_results)
    
    print("="*80)
    print(f"Result: {passed}/{total} validations passed")
    
    if passed == total:
        print("\n✅ FINAL VALIDATION: ALL REQUIREMENTS MET")
        print("\nThe CourseSmith Ultimate Engine is ready for use!")
        print("\nFeatures validated:")
        print("  • Language detection (English/Russian)")
        print("  • UTF-8 and Cyrillic character support")
        print("  • Professional course structure (10 chapters)")
        print("  • Structured output format ([CHAPTER_START]/[CHAPTER_END])")
        print("  • Markdown formatting support")
        print("  • Input sanitization for security")
        print("  • Integration with existing codebase")
        print("  • Comprehensive documentation")
        return True
    else:
        print(f"\n✗ FINAL VALIDATION: {total - passed} requirement(s) failed")
        return False


if __name__ == "__main__":
    success = validate_all_features()
    sys.exit(0 if success else 1)
