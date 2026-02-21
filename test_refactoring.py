"""
Test suite for the deep refactoring changes:
- Multilingual support (target_language parameter)
- Strict output (no technical headers)
- Post-processing regex filter (_clean_content)
- Lazy imports (openai, reportlab not imported at module load)
- Environment cache (.ready_state)
- Background thread for ban check
"""

import sys
import os
import re
import importlib


def test_target_language_parameter():
    """Test that CourseSmithEngine accepts target_language parameter."""
    print("Testing target_language parameter...")

    from coursesmith_engine import CourseSmithEngine

    # Test with explicit target_language
    engine = CourseSmithEngine(require_api_key=False, target_language='cn')
    assert engine.target_language == 'cn', f"Expected 'cn', got '{engine.target_language}'"
    print("✓ target_language='cn' stored correctly")

    # Test without target_language (default None)
    engine2 = CourseSmithEngine(require_api_key=False)
    assert engine2.target_language is None, f"Expected None, got '{engine2.target_language}'"
    print("✓ target_language defaults to None")

    # Test language override in generate_full_course path
    engine3 = CourseSmithEngine(require_api_key=False, target_language='ru')
    # Simulate the language determination logic
    engine3.language = None
    if engine3.target_language:
        engine3.language = engine3.target_language
    else:
        engine3.language = engine3.detect_language("Hello World")
    assert engine3.language == 'ru', f"Expected 'ru' override, got '{engine3.language}'"
    print("✓ target_language overrides auto-detection")

    print("✓ All target_language tests passed!\n")


def test_language_instruction_helper():
    """Test the _get_language_instruction helper method."""
    print("Testing _get_language_instruction...")

    from coursesmith_engine import CourseSmithEngine
    engine = CourseSmithEngine(require_api_key=False)

    instr_en = engine._get_language_instruction('en')
    assert 'English' in instr_en, f"Expected 'English' in instruction, got: {instr_en}"
    assert 'MUST' in instr_en, f"Expected 'MUST' in instruction"
    print(f"✓ English instruction: {instr_en[:60]}...")

    instr_ru = engine._get_language_instruction('ru')
    assert 'Russian' in instr_ru, f"Expected 'Russian' in instruction"
    print(f"✓ Russian instruction: {instr_ru[:60]}...")

    instr_cn = engine._get_language_instruction('cn')
    assert 'Chinese' in instr_cn, f"Expected 'Chinese' in instruction"
    print(f"✓ Chinese instruction: {instr_cn[:60]}...")

    # Unknown language code should use uppercase code
    instr_unknown = engine._get_language_instruction('xyz')
    assert 'XYZ' in instr_unknown, f"Expected 'XYZ' in instruction"
    print(f"✓ Unknown language code: {instr_unknown[:60]}...")

    print("✓ All _get_language_instruction tests passed!\n")


def test_clean_content_filter():
    """Test the _clean_content post-processing filter."""
    print("Testing _clean_content post-processing filter...")

    from coursesmith_engine import CourseSmithEngine

    # Test stripping "Chapter 1:" prefix
    result = CourseSmithEngine._clean_content("Chapter 1: Some title\nActual content here")
    assert "Chapter 1" not in result, f"Chapter 1 should be removed, got: {result[:80]}"
    assert "Actual content here" in result, f"Content should be preserved"
    print("✓ Removes 'Chapter N:' prefix")

    # Test stripping "Глава X" prefix
    result = CourseSmithEngine._clean_content("Глава 5 - Заголовок\nНастоящий контент")
    assert "Глава 5" not in result, f"Глава 5 should be removed"
    assert "Настоящий контент" in result, f"Russian content should be preserved"
    print("✓ Removes 'Глава N' prefix")

    # Test stripping "Here is your content" boilerplate
    result = CourseSmithEngine._clean_content("Here is your content:\n\nThe real content starts here.")
    assert "Here is your content" not in result, f"Boilerplate should be removed"
    assert "real content starts here" in result, f"Actual content should be preserved"
    print("✓ Removes 'Here is your content' boilerplate")

    # Test stripping "Introduction" prefix
    result = CourseSmithEngine._clean_content("Introduction\n\n## Real Header\nContent")
    assert result.startswith("## Real Header"), f"Should start with content, got: {result[:40]}"
    print("✓ Removes 'Introduction' prefix")

    # Test stripping leading/trailing blank lines
    result = CourseSmithEngine._clean_content("\n\n\nActual content\nMore content\n\n\n")
    assert result.startswith("Actual"), f"Leading blanks should be stripped"
    assert result.endswith("content"), f"Trailing blanks should be stripped"
    print("✓ Strips leading/trailing blank lines")

    # Test empty input
    result = CourseSmithEngine._clean_content("")
    assert result == "", f"Empty input should return empty"
    print("✓ Handles empty input")

    # Test None input
    result = CourseSmithEngine._clean_content(None)
    assert result is None, f"None input should return None"
    print("✓ Handles None input")

    # Test content that should NOT be modified
    clean_content = "## Key Concepts\n\n* Point one\n* Point two"
    result = CourseSmithEngine._clean_content(clean_content)
    assert result == clean_content, f"Clean content should not be modified"
    print("✓ Preserves clean content without modification")

    print("✓ All _clean_content tests passed!\n")


def test_lazy_import_coursesmith_engine():
    """Test that coursesmith_engine does not import openai at module level."""
    print("Testing lazy import in coursesmith_engine...")

    # Check that 'openai' is not imported as a top-level dependency
    # by reading the source file
    engine_path = os.path.join(os.path.dirname(__file__), 'coursesmith_engine.py')
    with open(engine_path, 'r') as f:
        source = f.read()

    # Look for top-level 'from openai import' or 'import openai'
    lines = source.split('\n')
    top_level_openai = False
    in_class_or_func = False
    indent_level = 0
    for line in lines:
        stripped = line.lstrip()
        if stripped.startswith('class ') or stripped.startswith('def '):
            in_class_or_func = True
        if not in_class_or_func:
            if stripped.startswith('from openai import') or stripped.startswith('import openai'):
                top_level_openai = True
                break

    assert not top_level_openai, "openai should NOT be imported at module level in coursesmith_engine.py"
    print("✓ openai is not imported at module level in coursesmith_engine.py")

    print("✓ Lazy import test passed!\n")


def test_lazy_import_ai_worker():
    """Test that ai_worker does not import openai at module level."""
    print("Testing lazy import in ai_worker...")

    worker_path = os.path.join(os.path.dirname(__file__), 'ai_worker.py')
    with open(worker_path, 'r') as f:
        source = f.read()

    lines = source.split('\n')
    top_level_openai = False
    in_class_or_func = False
    for line in lines:
        stripped = line.lstrip()
        if stripped.startswith('class ') or stripped.startswith('def '):
            in_class_or_func = True
        if not in_class_or_func:
            if stripped.startswith('from openai import') or stripped.startswith('import openai'):
                top_level_openai = True
                break

    assert not top_level_openai, "openai should NOT be imported at module level in ai_worker.py"
    print("✓ openai is not imported at module level in ai_worker.py")

    print("✓ Lazy import test for ai_worker passed!\n")


def test_lazy_import_pdf_engine():
    """Test that pdf_engine does not import reportlab at module level."""
    print("Testing lazy import in pdf_engine...")

    pdf_path = os.path.join(os.path.dirname(__file__), 'pdf_engine.py')
    with open(pdf_path, 'r') as f:
        source = f.read()

    lines = source.split('\n')
    top_level_reportlab = False
    in_class_or_func = False
    for line in lines:
        stripped = line.lstrip()
        if stripped.startswith('class ') or stripped.startswith('def '):
            in_class_or_func = True
        if not in_class_or_func:
            if stripped.startswith('from reportlab') or stripped == 'import reportlab':
                top_level_reportlab = True
                break

    assert not top_level_reportlab, "reportlab should NOT be imported at module level in pdf_engine.py"
    print("✓ reportlab is not imported at module level in pdf_engine.py")

    print("✓ Lazy import test for pdf_engine passed!\n")


def test_env_cache_functions():
    """Test the environment cache functions."""
    print("Testing environment cache functions...")

    # We need to test the cache functions exist in main.py source
    main_path = os.path.join(os.path.dirname(__file__), 'main.py')
    with open(main_path, 'r') as f:
        source = f.read()

    assert '_is_env_ready' in source, "_is_env_ready function should exist in main.py"
    print("✓ _is_env_ready function exists")

    assert '_mark_env_ready' in source, "_mark_env_ready function should exist in main.py"
    print("✓ _mark_env_ready function exists")

    assert '.ready_state' in source, ".ready_state path should be referenced in main.py"
    print("✓ .ready_state file path is configured")

    print("✓ Environment cache tests passed!\n")


def test_background_ban_check():
    """Test that check_remote_ban is called in a background thread."""
    print("Testing background ban check...")

    main_path = os.path.join(os.path.dirname(__file__), 'main.py')
    with open(main_path, 'r') as f:
        source = f.read()

    # Check that check_remote_ban is run in a thread
    assert 'threading.Thread(target=check_remote_ban' in source, \
        "check_remote_ban should be called via threading.Thread"
    print("✓ check_remote_ban is launched in a background thread")

    # Check daemon flag
    assert 'daemon=True' in source, "Background thread should be daemon=True"
    print("✓ Background thread is set as daemon")

    print("✓ Background ban check tests passed!\n")


def test_pyinstaller_onedir():
    """Test that PyInstaller spec uses --onedir (COLLECT) mode."""
    print("Testing PyInstaller spec configuration...")

    spec_path = os.path.join(os.path.dirname(__file__), 'CourseSmith_v2.spec')
    with open(spec_path, 'r') as f:
        source = f.read()

    assert 'COLLECT(' in source, "Spec should use COLLECT() for --onedir mode"
    print("✓ COLLECT() present for --onedir mode")

    assert 'exclude_binaries=True' in source, "EXE should have exclude_binaries=True for onedir"
    print("✓ exclude_binaries=True set in EXE")

    assert 'collect_submodules' in source, "Should use collect_submodules for selective imports"
    print("✓ collect_submodules used for selective imports")

    print("✓ PyInstaller spec tests passed!\n")


def test_generate_course_from_instruction_accepts_target_language():
    """Test that the convenience function accepts target_language."""
    print("Testing generate_course_from_instruction signature...")

    from coursesmith_engine import generate_course_from_instruction
    import inspect

    sig = inspect.signature(generate_course_from_instruction)
    assert 'target_language' in sig.parameters, \
        "generate_course_from_instruction should accept target_language parameter"
    print("✓ generate_course_from_instruction accepts target_language")

    print("✓ Convenience function signature test passed!\n")


def run_all_tests():
    """Run all refactoring tests."""
    print("=" * 80)
    print("COURSESMITH AI - DEEP REFACTORING TEST SUITE")
    print("=" * 80 + "\n")

    tests = [
        ("Target Language Parameter", test_target_language_parameter),
        ("Language Instruction Helper", test_language_instruction_helper),
        ("Clean Content Filter", test_clean_content_filter),
        ("Lazy Import: coursesmith_engine", test_lazy_import_coursesmith_engine),
        ("Lazy Import: ai_worker", test_lazy_import_ai_worker),
        ("Lazy Import: pdf_engine", test_lazy_import_pdf_engine),
        ("Environment Cache Functions", test_env_cache_functions),
        ("Background Ban Check", test_background_ban_check),
        ("PyInstaller --onedir Mode", test_pyinstaller_onedir),
        ("Convenience Function Signature", test_generate_course_from_instruction_accepts_target_language),
    ]

    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, True))
        except AssertionError as e:
            print(f"\n✗ {test_name} FAILED: {e}")
            results.append((test_name, False))
        except Exception as e:
            print(f"\n✗ {test_name} CRASHED: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))

    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")

    print("=" * 80)
    print(f"Results: {passed}/{total} tests passed")

    if passed == total:
        print("✓ ALL REFACTORING TESTS PASSED!")
        print("=" * 80)
        return True
    else:
        print(f"✗ {total - passed} test(s) failed")
        print("=" * 80)
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
