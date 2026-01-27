"""
Example usage of CourseSmith Ultimate Engine.
Demonstrates generating a complete educational course from a simple instruction.
"""

import os
from coursesmith_engine import generate_course_from_instruction, CourseSmithEngine


def example_simple_usage():
    """Example: Simple one-line course generation."""
    print("="*80)
    print("Example 1: Simple Usage with English")
    print("="*80 + "\n")
    
    # Simple instruction
    instruction = "Introduction to Python Programming for Beginners"
    
    print(f"Instruction: {instruction}\n")
    print("Generating course (this requires OpenAI API key)...\n")
    
    # Note: This requires OPENAI_API_KEY in environment
    # output = generate_course_from_instruction(instruction)
    # print(output[:500] + "...\n")
    
    print("(Skipped - requires API key)\n")


def example_with_progress():
    """Example: Course generation with progress tracking."""
    print("="*80)
    print("Example 2: Generation with Progress Callback")
    print("="*80 + "\n")
    
    instruction = "Machine Learning: From Theory to Practice"
    
    def progress_callback(step, total, message):
        """Display progress during generation."""
        percent = int((step / total) * 100)
        print(f"[{percent:3d}%] Step {step}/{total}: {message}")
    
    print(f"Instruction: {instruction}\n")
    print("Generating course with progress tracking...\n")
    
    # Note: This requires OPENAI_API_KEY in environment
    # output = generate_course_from_instruction(instruction, progress_callback=progress_callback)
    
    print("(Skipped - requires API key)\n")


def example_russian_language():
    """Example: Russian language course generation."""
    print("="*80)
    print("Example 3: Russian Language Course (Cyrillic Support)")
    print("="*80 + "\n")
    
    instruction = "Основы машинного обучения для начинающих программистов"
    
    print(f"Instruction: {instruction}\n")
    print("Generating Russian course with full Cyrillic support...\n")
    
    # Note: This requires OPENAI_API_KEY in environment
    # engine = CourseSmithEngine()
    # course_data = engine.generate_full_course(instruction)
    # output = engine.format_output(course_data)
    
    print("(Skipped - requires API key)\n")


def example_output_structure():
    """Example: Demonstrate the output structure format."""
    print("="*80)
    print("Example 4: Output Structure Format")
    print("="*80 + "\n")
    
    # Create mock course data to demonstrate structure
    mock_course_data = {
        'language': 'en',
        'title': 'Mastering Web Development: A Comprehensive Guide',
        'chapters': [
            {
                'number': 1,
                'title': 'Introduction to Web Development',
                'content': '''## What is Web Development?

Web development is the process of building and maintaining websites and web applications. It encompasses several aspects including web design, web content development, client-side/server-side scripting, and network security configuration.

## Key Components

* **Frontend Development**: Involves HTML, CSS, and JavaScript
* **Backend Development**: Server-side logic and databases
* **Full-Stack Development**: Combination of both frontend and backend

## Getting Started

To begin your web development journey, you'll need to understand the fundamental technologies that power the web. Start with HTML for structure, CSS for styling, and JavaScript for interactivity.'''
            },
            {
                'number': 2,
                'title': 'HTML Fundamentals',
                'content': '''## Understanding HTML

HTML (HyperText Markup Language) is the standard markup language for creating web pages. It provides the structure and content of web pages through a system of tags and elements.

## Essential HTML Elements

* **Headings**: `<h1>` through `<h6>` for hierarchical structure
* **Paragraphs**: `<p>` for text content
* **Links**: `<a>` for navigation
* **Images**: `<img>` for visual content
* **Lists**: `<ul>`, `<ol>`, and `<li>` for organized content

## Best Practices

Always use semantic HTML to improve accessibility and SEO. Ensure your HTML is well-structured, properly indented, and follows modern standards.'''
            }
        ]
    }
    
    # Format the output
    engine = CourseSmithEngine(require_api_key=False)
    formatted_output = engine.format_output(mock_course_data)
    
    print("Generated Output Structure:\n")
    print(formatted_output)
    
    print("\n" + "="*80)
    print("Key Features of Output Format:")
    print("="*80)
    print("✓ UTF-8 clean encoding")
    print("✓ [CHAPTER_START] and [CHAPTER_END] markers for easy parsing")
    print("✓ Markdown formatting (headers, subheaders, bullet points)")
    print("✓ Structured TITLE: and CONTENT: fields")
    print("✓ Ready for conversion to PDF, DOCX, EPUB")
    print("✓ Full Cyrillic (Russian) character support")
    print("")


def example_custom_api_key():
    """Example: Using a custom API key."""
    print("="*80)
    print("Example 5: Using Custom API Key")
    print("="*80 + "\n")
    
    print("You can provide your API key directly:\n")
    print("```python")
    print('from coursesmith_engine import CourseSmithEngine')
    print('')
    print('api_key = "sk-your-api-key-here"')
    print('engine = CourseSmithEngine(api_key=api_key)')
    print('course_data = engine.generate_full_course("Your instruction here")')
    print('output = engine.format_output(course_data)')
    print('print(output)')
    print("```\n")


def main():
    """Run all examples."""
    print("\n" + "="*80)
    print("COURSESMITH ULTIMATE ENGINE - EXAMPLES")
    print("="*80 + "\n")
    
    # Check for API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("⚠️  Note: OPENAI_API_KEY not found in environment.")
        print("    Examples requiring API access will be skipped.")
        print("    To run full examples, set your OpenAI API key in .env file.\n")
    
    example_simple_usage()
    example_with_progress()
    example_russian_language()
    example_output_structure()
    example_custom_api_key()
    
    print("="*80)
    print("For more information, see the module documentation:")
    print("  python -c 'import coursesmith_engine; help(coursesmith_engine)'")
    print("="*80 + "\n")


if __name__ == "__main__":
    main()
