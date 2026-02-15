"""
Tests for new product templates and export system.
Tests the AI Digital Product Factory functionality.
"""

import os
import tempfile


def test_product_templates_import():
    """Test that product_templates module imports correctly."""
    from product_templates import (
        get_template, get_all_templates, get_template_ids,
        get_credit_cost, get_structure_prompt, get_content_prompt,
        ProductTemplateRegistry, MINI_COURSE, LEAD_MAGNET,
        PAID_GUIDE, CHALLENGE_30_DAY, CHECKLIST, FULL_COURSE
    )
    assert True


def test_product_template_definitions():
    """Test that all product templates are correctly defined."""
    from product_templates import get_all_templates, get_template
    
    templates = get_all_templates()
    assert len(templates) == 6, f"Expected 6 templates, got {len(templates)}"
    
    # Check each template has required fields
    for template in templates:
        assert template.id is not None
        assert template.name is not None
        assert template.chapter_count > 0
        assert template.chars_per_chapter > 0
        assert template.credit_cost > 0
        assert template.structure_prompt_en
        assert template.structure_prompt_ru
        assert template.content_prompt_en
        assert template.content_prompt_ru


def test_credit_costs():
    """Test credit costs for different product types."""
    from product_templates import get_credit_cost
    
    # Test credit costs match spec
    assert get_credit_cost('mini_course') == 1
    assert get_credit_cost('lead_magnet') == 1
    assert get_credit_cost('checklist') == 1
    assert get_credit_cost('paid_guide') == 2
    assert get_credit_cost('30_day_challenge') == 2
    assert get_credit_cost('full_course') == 3


def test_template_chapter_counts():
    """Test that templates have correct chapter counts."""
    from product_templates import get_template
    
    assert get_template('mini_course').chapter_count == 5
    assert get_template('lead_magnet').chapter_count == 3
    assert get_template('checklist').chapter_count == 5
    assert get_template('paid_guide').chapter_count == 12
    assert get_template('30_day_challenge').chapter_count == 30
    assert get_template('full_course').chapter_count == 10


def test_export_base_import():
    """Test that export_base module imports correctly."""
    from export_base import (
        ExporterBase, ExportError, ExportManager,
        get_export_formats_for_ui
    )
    assert True


def test_export_formats_for_ui():
    """Test that export formats are correctly defined for UI."""
    from export_base import get_export_formats_for_ui
    
    formats = get_export_formats_for_ui()
    assert len(formats) == 5  # PDF, DOCX, HTML, EPUB, Markdown
    
    format_ids = [f['id'] for f in formats]
    assert 'pdf' in format_ids
    assert 'docx' in format_ids
    assert 'markdown' in format_ids
    assert 'html' in format_ids
    assert 'epub' in format_ids


def test_markdown_exporter():
    """Test Markdown exporter basic functionality."""
    from markdown_exporter import MarkdownExporter
    from project_manager import CourseProject
    
    # Create test project
    project = CourseProject()
    project.set_topic("Test Topic")
    project.set_audience("Test Audience")
    project.set_outline(["Chapter 1", "Chapter 2"])
    project.set_chapter_content("Chapter 1", "This is chapter 1 content.")
    project.set_chapter_content("Chapter 2", "This is chapter 2 content.")
    
    # Create exporter
    exporter = MarkdownExporter(project)
    
    # Generate output path
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = exporter.generate_output_path(tmpdir)
        assert output_path.endswith('.md')
        
        # Export
        result = exporter.export()
        assert os.path.exists(result)
        
        # Read and verify content
        with open(result, 'r', encoding='utf-8') as f:
            content = f.read()
        
        assert "Test Topic" in content
        assert "Chapter 1" in content
        assert "Chapter 2" in content


def test_html_exporter():
    """Test HTML exporter basic functionality."""
    from html_exporter import HTMLExporter
    from project_manager import CourseProject
    
    # Create test project
    project = CourseProject()
    project.set_topic("Test Topic")
    project.set_audience("Test Audience")
    project.set_outline(["Chapter 1", "Chapter 2"])
    project.set_chapter_content("Chapter 1", "This is chapter 1 content.")
    project.set_chapter_content("Chapter 2", "This is chapter 2 content.")
    
    # Create exporter
    exporter = HTMLExporter(project)
    
    # Generate output path
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = exporter.generate_output_path(tmpdir)
        assert output_path.endswith('.html')
        
        # Export
        result = exporter.export()
        assert os.path.exists(result)
        
        # Read and verify content
        with open(result, 'r', encoding='utf-8') as f:
            content = f.read()
        
        assert "<!DOCTYPE html>" in content
        assert "Test Topic" in content
        assert "Chapter 1" in content


def test_docx_exporter():
    """Test DOCX exporter basic functionality."""
    try:
        from docx_exporter import DOCXExporter, DOCX_AVAILABLE
    except ImportError:
        print("python-docx not available, skipping DOCX test")
        return
    
    if not DOCX_AVAILABLE:
        print("DOCX export not available")
        return
    
    from project_manager import CourseProject
    
    # Create test project
    project = CourseProject()
    project.set_topic("Test Topic")
    project.set_audience("Test Audience")
    project.set_outline(["Chapter 1", "Chapter 2"])
    project.set_chapter_content("Chapter 1", "This is chapter 1 content.")
    project.set_chapter_content("Chapter 2", "This is chapter 2 content.")
    
    # Create exporter
    exporter = DOCXExporter(project)
    
    # Generate output path
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = exporter.generate_output_path(tmpdir)
        assert output_path.endswith('.docx')
        
        # Export
        result = exporter.export()
        assert os.path.exists(result)


def test_epub_exporter():
    """Test EPUB exporter basic functionality."""
    try:
        from epub_exporter import EPUBExporter, EPUB_AVAILABLE
    except ImportError:
        print("ebooklib not available, skipping EPUB test")
        return
    
    if not EPUB_AVAILABLE:
        print("EPUB export not available")
        return
    
    from project_manager import CourseProject
    
    # Create test project
    project = CourseProject()
    project.set_topic("Test Topic")
    project.set_audience("Test Audience")
    project.set_outline(["Chapter 1", "Chapter 2"])
    project.set_chapter_content("Chapter 1", "This is chapter 1 content.")
    project.set_chapter_content("Chapter 2", "This is chapter 2 content.")
    
    # Create exporter
    exporter = EPUBExporter(project)
    
    # Generate output path
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = exporter.generate_output_path(tmpdir)
        assert output_path.endswith('.epub')
        
        # Export
        result = exporter.export()
        assert os.path.exists(result)


def test_project_manager_new_fields():
    """Test that CourseProject has new fields."""
    from project_manager import CourseProject
    
    project = CourseProject()
    
    # Check new fields exist with defaults
    assert project.product_type == "full_course"
    assert project.export_formats == ["pdf"]
    assert project.credits_used == 0
    assert project.exported_files == {}
    
    # Test setters
    project.set_product_type("mini_course")
    assert project.product_type == "mini_course"
    
    project.set_export_formats(["pdf", "docx"])
    assert "pdf" in project.export_formats
    assert "docx" in project.export_formats
    
    project.set_credits_used(3)
    assert project.credits_used == 3
    
    project.add_exported_file("pdf", "/path/to/file.pdf")
    assert project.exported_files["pdf"] == "/path/to/file.pdf"


def test_project_serialization_with_new_fields():
    """Test that new fields are correctly serialized/deserialized."""
    from project_manager import CourseProject
    
    project = CourseProject()
    project.set_topic("Test")
    project.set_audience("Testers")
    project.set_product_type("lead_magnet")
    project.set_export_formats(["markdown", "html"])
    project.set_credits_used(2)
    project.add_exported_file("markdown", "/test.md")
    
    # Serialize to dict
    data = project.to_dict()
    
    assert data['product_type'] == "lead_magnet"
    assert data['export_formats'] == ["markdown", "html"]
    assert data['credits_used'] == 2
    assert data['exported_files']['markdown'] == "/test.md"
    
    # Deserialize from dict
    project2 = CourseProject.from_dict(data)
    
    assert project2.product_type == "lead_magnet"
    assert project2.export_formats == ["markdown", "html"]
    assert project2.credits_used == 2
    assert project2.exported_files['markdown'] == "/test.md"


def test_ai_worker_credit_functions():
    """Test new credit functions in ai_worker."""
    from ai_worker import get_credit_cost_for_product
    
    # Test credit costs
    assert get_credit_cost_for_product('mini_course') == 1
    assert get_credit_cost_for_product('lead_magnet') == 1
    assert get_credit_cost_for_product('paid_guide') == 2
    assert get_credit_cost_for_product('30_day_challenge') == 2
    assert get_credit_cost_for_product('full_course') == 3


if __name__ == "__main__":
    # Run tests manually
    test_product_templates_import()
    print("✓ test_product_templates_import passed")
    
    test_product_template_definitions()
    print("✓ test_product_template_definitions passed")
    
    test_credit_costs()
    print("✓ test_credit_costs passed")
    
    test_template_chapter_counts()
    print("✓ test_template_chapter_counts passed")
    
    test_export_base_import()
    print("✓ test_export_base_import passed")
    
    test_export_formats_for_ui()
    print("✓ test_export_formats_for_ui passed")
    
    test_markdown_exporter()
    print("✓ test_markdown_exporter passed")
    
    test_html_exporter()
    print("✓ test_html_exporter passed")
    
    test_docx_exporter()
    print("✓ test_docx_exporter passed")
    
    test_project_manager_new_fields()
    print("✓ test_project_manager_new_fields passed")
    
    test_project_serialization_with_new_fields()
    print("✓ test_project_serialization_with_new_fields passed")
    
    test_ai_worker_credit_functions()
    print("✓ test_ai_worker_credit_functions passed")
    
    print("\n✅ All tests passed!")
