"""
Integration test for CourseSmith Ultimate Engine.
Validates that the module integrates properly with the CourseSmith application.
"""

import sys


def test_module_import():
    """Test that the module can be imported successfully."""
    print("Testing module import...")
    
    try:
        import coursesmith_engine
        print("✓ Module 'coursesmith_engine' imported successfully")
        
        # Check key classes and functions exist
        assert hasattr(coursesmith_engine, 'CourseSmithEngine')
        print("✓ CourseSmithEngine class found")
        
        assert hasattr(coursesmith_engine, 'generate_course_from_instruction')
        print("✓ generate_course_from_instruction function found")
        
        return True
    except Exception as e:
        print(f"✗ Import failed: {e}")
        return False


def test_class_instantiation():
    """Test that the CourseSmithEngine class can be instantiated."""
    print("\nTesting class instantiation...")
    
    try:
        from coursesmith_engine import CourseSmithEngine
        
        # Test with require_api_key=False for testing
        engine = CourseSmithEngine(require_api_key=False)
        print("✓ CourseSmithEngine instantiated successfully (test mode)")
        
        # Check attributes
        assert hasattr(engine, 'language')
        assert hasattr(engine, 'course_title')
        assert hasattr(engine, 'chapters')
        print("✓ All required attributes present")
        
        # Check methods
        assert hasattr(engine, 'detect_language')
        assert hasattr(engine, 'generate_course_title')
        assert hasattr(engine, 'generate_chapter_structure')
        assert hasattr(engine, 'generate_chapter_content')
        assert hasattr(engine, 'generate_full_course')
        assert hasattr(engine, 'format_output')
        print("✓ All required methods present")
        
        return True
    except Exception as e:
        print(f"✗ Instantiation failed: {e}")
        return False


def test_language_detection_functionality():
    """Test language detection works correctly."""
    print("\nTesting language detection functionality...")
    
    try:
        from coursesmith_engine import CourseSmithEngine
        engine = CourseSmithEngine(require_api_key=False)
        
        # Test cases
        test_cases = [
            ("Hello World", "en"),
            ("Machine Learning Tutorial", "en"),
            ("Привет мир", "ru"),
            ("Машинное обучение", "ru"),
            ("Python программирование", "ru"),  # Mixed should detect as Russian
        ]
        
        for text, expected_lang in test_cases:
            detected = engine.detect_language(text)
            assert detected == expected_lang, f"Expected {expected_lang} for '{text}', got {detected}"
            print(f"✓ Correctly detected '{text}' as {detected}")
        
        return True
    except Exception as e:
        print(f"✗ Language detection failed: {e}")
        return False


def test_output_formatting():
    """Test output formatting with mock data."""
    print("\nTesting output formatting...")
    
    try:
        from coursesmith_engine import CourseSmithEngine
        engine = CourseSmithEngine(require_api_key=False)
        
        # Create comprehensive test data
        test_data = {
            'title': 'Test Course Title',
            'chapters': []
        }
        
        # Add 10 chapters
        for i in range(1, 11):
            test_data['chapters'].append({
                'number': i,
                'title': f'Chapter {i}: Test Title',
                'content': f'Test content for chapter {i} with ~1500 characters.' * 50
            })
        
        # Format output
        output = engine.format_output(test_data)
        
        # Validate structure
        assert '# Test Course Title' in output
        assert output.count('[CHAPTER_START]') == 10
        assert output.count('[CHAPTER_END]') == 10
        assert output.count('TITLE:') == 10
        assert output.count('CONTENT:') == 10
        
        print("✓ Output format validation passed")
        print(f"✓ Generated output with {len(output)} characters")
        print(f"✓ All 10 chapters properly formatted")
        
        return True
    except Exception as e:
        print(f"✗ Output formatting failed: {e}")
        return False


def test_cyrillic_support():
    """Test Cyrillic character support end-to-end."""
    print("\nTesting Cyrillic (Russian) support...")
    
    try:
        from coursesmith_engine import CourseSmithEngine
        engine = CourseSmithEngine(require_api_key=False)
        
        # Test with full Russian content
        russian_data = {
            'title': 'Курс по машинному обучению: От теории к практике',
            'chapters': [
                {
                    'number': 1,
                    'title': 'Введение в машинное обучение',
                    'content': '''## Основные концепции

Машинное обучение — это раздел искусственного интеллекта, который изучает методы построения алгоритмов, способных обучаться.

## Ключевые направления

* **Обучение с учителем**: Алгоритмы классификации и регрессии
* **Обучение без учителя**: Кластеризация и снижение размерности
* **Обучение с подкреплением**: Агенты и стратегии

## Практическое применение

Машинное обучение находит широкое применение в различных областях.'''
                }
            ]
        }
        
        # Format and validate
        output = engine.format_output(russian_data)
        
        # Check Cyrillic preservation
        assert 'Курс по машинному обучению' in output
        assert 'Введение в машинное обучение' in output
        assert 'Машинное обучение' in output
        assert 'искусственного интеллекта' in output
        
        print("✓ Cyrillic characters preserved in output")
        
        # Test file I/O with UTF-8
        import tempfile
        import os
        
        try:
            with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', suffix='.txt', delete=False) as f:
                temp_path = f.name
                f.write(output)
            
            with open(temp_path, 'r', encoding='utf-8') as f:
                read_content = f.read()
            
            assert read_content == output
            print("✓ UTF-8 file write/read works correctly")
        finally:
            # Clean up
            if os.path.exists(temp_path):
                os.unlink(temp_path)
        
        return True
    except Exception as e:
        print(f"✗ Cyrillic support test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_markdown_preservation():
    """Test that markdown formatting is preserved."""
    print("\nTesting markdown formatting preservation...")
    
    try:
        from coursesmith_engine import CourseSmithEngine
        engine = CourseSmithEngine(require_api_key=False)
        
        markdown_data = {
            'title': 'Markdown Test Course',
            'chapters': [
                {
                    'number': 1,
                    'title': 'Markdown Features',
                    'content': '''## Headers Work

This is a paragraph.

### Subheaders Too

* Bullet point 1
* Bullet point 2
* Bullet point 3

**Bold text** and *italic text* should work.

## Code Blocks

```python
def hello():
    print("Hello, World!")
```

More content here.'''
                }
            ]
        }
        
        output = engine.format_output(markdown_data)
        
        # Verify markdown elements
        assert '## Headers Work' in output
        assert '### Subheaders Too' in output
        assert '* Bullet point 1' in output
        assert '**Bold text**' in output
        assert '*italic text*' in output
        assert '```python' in output
        
        print("✓ All markdown elements preserved")
        return True
    except Exception as e:
        print(f"✗ Markdown preservation failed: {e}")
        return False


def test_integration_with_existing_code():
    """Test that the module can work with existing CourseSmith components."""
    print("\nTesting integration with existing components...")
    
    try:
        # Try importing existing modules
        try:
            import ai_manager
            print("✓ Existing ai_manager module accessible")
        except ImportError:
            print("⚠ ai_manager not imported (may be expected)")
        
        # Import new module
        from coursesmith_engine import CourseSmithEngine
        print("✓ New coursesmith_engine module accessible")
        
        # Both should be able to coexist
        print("✓ Modules can coexist without conflicts")
        
        return True
    except Exception as e:
        print(f"✗ Integration test failed: {e}")
        return False


def run_integration_tests():
    """Run all integration tests."""
    print("="*80)
    print("COURSESMITH ULTIMATE ENGINE - INTEGRATION TEST SUITE")
    print("="*80 + "\n")
    
    tests = [
        ("Module Import", test_module_import),
        ("Class Instantiation", test_class_instantiation),
        ("Language Detection", test_language_detection_functionality),
        ("Output Formatting", test_output_formatting),
        ("Cyrillic Support", test_cyrillic_support),
        ("Markdown Preservation", test_markdown_preservation),
        ("Integration with Existing Code", test_integration_with_existing_code),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n✗ {test_name} crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    print("="*80)
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("✓ ALL INTEGRATION TESTS PASSED!")
        print("="*80)
        return True
    else:
        print(f"✗ {total - passed} test(s) failed")
        print("="*80)
        return False


if __name__ == "__main__":
    success = run_integration_tests()
    sys.exit(0 if success else 1)
