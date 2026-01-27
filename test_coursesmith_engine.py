"""
Test script for CourseSmith Ultimate Engine.
Tests English and Russian language course generation with proper UTF-8 and Cyrillic support.
"""

import os
import sys
from coursesmith_engine import CourseSmithEngine, generate_course_from_instruction


def test_language_detection():
    """Test language detection for English and Russian."""
    print("Testing language detection...")
    
    engine = CourseSmithEngine(require_api_key=False)
    
    # Test English
    lang_en = engine.detect_language("Machine Learning for Beginners")
    assert lang_en == 'en', f"Expected 'en', got '{lang_en}'"
    print(f"✓ English detection: '{lang_en}'")
    
    # Test Russian
    lang_ru = engine.detect_language("Машинное обучение для начинающих")
    assert lang_ru == 'ru', f"Expected 'ru', got '{lang_ru}'"
    print(f"✓ Russian detection: '{lang_ru}'")
    
    # Test mixed (should detect as Russian)
    lang_mixed = engine.detect_language("Machine Learning для начинающих")
    assert lang_mixed == 'ru', f"Expected 'ru', got '{lang_mixed}'"
    print(f"✓ Mixed text detection: '{lang_mixed}'")
    
    print("✓ All language detection tests passed!\n")


def test_output_format():
    """Test that the output format matches the required structure."""
    print("Testing output format structure...")
    
    # Create mock course data
    mock_data = {
        'title': 'Test Course',
        'chapters': [
            {
                'number': 1,
                'title': 'Introduction',
                'content': 'This is test content for chapter 1.'
            },
            {
                'number': 2,
                'title': 'Advanced Topics',
                'content': 'This is test content for chapter 2.'
            }
        ]
    }
    
    engine = CourseSmithEngine(require_api_key=False)
    output = engine.format_output(mock_data)
    
    # Verify required elements are present
    assert '# Test Course' in output, "Course title not found in output"
    assert '[CHAPTER_START]' in output, "[CHAPTER_START] marker not found"
    assert '[CHAPTER_END]' in output, "[CHAPTER_END] marker not found"
    assert 'TITLE: Introduction' in output, "Chapter title format incorrect"
    assert 'CONTENT: This is test content' in output, "Chapter content format incorrect"
    
    # Count chapter markers
    start_count = output.count('[CHAPTER_START]')
    end_count = output.count('[CHAPTER_END]')
    assert start_count == 2, f"Expected 2 [CHAPTER_START] markers, found {start_count}"
    assert end_count == 2, f"Expected 2 [CHAPTER_END] markers, found {end_count}"
    
    print("✓ Output format structure is correct!\n")
    return output


def test_utf8_encoding():
    """Test UTF-8 and Cyrillic character support."""
    print("Testing UTF-8 and Cyrillic encoding...")
    
    # Test with Russian text
    test_text = "Машинное обучение: основы и практика для начинающих программистов"
    
    # Ensure we can encode and decode properly
    encoded = test_text.encode('utf-8')
    decoded = encoded.decode('utf-8')
    assert decoded == test_text, "UTF-8 encoding/decoding failed"
    
    # Test with mock data containing Cyrillic
    mock_data = {
        'title': 'Курс по машинному обучению',
        'chapters': [
            {
                'number': 1,
                'title': 'Введение в ML',
                'content': 'Машинное обучение — это раздел искусственного интеллекта.'
            }
        ]
    }
    
    engine = CourseSmithEngine(require_api_key=False)
    output = engine.format_output(mock_data)
    
    # Verify Cyrillic characters are preserved
    assert 'Курс по машинному обучению' in output, "Cyrillic title not preserved"
    assert 'Введение в ML' in output, "Cyrillic chapter title not preserved"
    assert 'Машинное обучение' in output, "Cyrillic content not preserved"
    
    # Ensure output can be written to file
    test_file = '/tmp/test_cyrillic_output.txt'
    with open(test_file, 'w', encoding='utf-8') as f:
        f.write(output)
    
    # Read it back
    with open(test_file, 'r', encoding='utf-8') as f:
        read_content = f.read()
    
    assert read_content == output, "File write/read failed for Cyrillic text"
    
    print("✓ UTF-8 and Cyrillic encoding tests passed!\n")


def test_markdown_formatting():
    """Test that markdown formatting is present in generated content."""
    print("Testing markdown formatting...")
    
    # Create mock data with markdown
    mock_data = {
        'title': 'Test Course',
        'chapters': [
            {
                'number': 1,
                'title': 'Introduction',
                'content': '''## Key Concepts

* First point
* Second point
* Third point

## Advanced Topics

This is a paragraph with **bold** and *italic* text.'''
            }
        ]
    }
    
    engine = CourseSmithEngine(require_api_key=False)
    output = engine.format_output(mock_data)
    
    # Verify markdown elements are preserved
    assert '## Key Concepts' in output, "Markdown subheader not found"
    assert '* First point' in output, "Bullet point not found"
    assert '**bold**' in output or '* Second point' in output, "Markdown formatting not preserved"
    
    print("✓ Markdown formatting tests passed!\n")


def run_all_tests():
    """Run all tests."""
    print("="*80)
    print("CourseSmith Ultimate Engine - Test Suite")
    print("="*80 + "\n")
    
    try:
        test_language_detection()
        test_output_format()
        test_utf8_encoding()
        test_markdown_formatting()
        
        print("="*80)
        print("✓ ALL TESTS PASSED!")
        print("="*80)
        return True
        
    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
        return False
    except Exception as e:
        print(f"\n✗ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
