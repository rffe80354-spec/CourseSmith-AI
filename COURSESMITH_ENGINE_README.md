# CourseSmith Ultimate Engine

The **CourseSmith Ultimate Engine** is a professional educational course generator that creates high-quality, structured courses from a single instruction. It supports multiple languages (English and Russian) with full UTF-8 and Cyrillic character support.

## Features

✅ **Language Detection**: Automatically detects English or Russian based on input  
✅ **Professional Titles**: Generates high-authority course titles  
✅ **10-Chapter Structure**: Creates a logical progression from basics to advanced  
✅ **Expert-Level Content**: ~1500 characters per chapter with rich formatting  
✅ **Markdown Support**: Full markdown formatting (headers, bullet points, emphasis)  
✅ **UTF-8 & Cyrillic**: Clean encoding with perfect Cyrillic (Russian) support  
✅ **Structured Output**: Uses `[CHAPTER_START]`/`[CHAPTER_END]` markers for easy parsing  
✅ **Multi-Format Ready**: Output designed for conversion to PDF, DOCX, and EPUB  

## Installation

The CourseSmith Ultimate Engine is included in the CourseSmith-AI repository. Ensure you have the required dependencies:

```bash
pip install -r requirements.txt
```

**Required packages:**
- `openai` - For GPT-4o API access
- `python-dotenv` - For environment variable management

## Quick Start

### Basic Usage

```python
from coursesmith_engine import generate_course_from_instruction

# Generate a complete course from a single instruction
instruction = "Introduction to Python Programming for Beginners"
output = generate_course_from_instruction(instruction)

print(output)
```

### With Progress Tracking

```python
from coursesmith_engine import generate_course_from_instruction

def progress(step, total, message):
    print(f"[{step}/{total}] {message}")

instruction = "Machine Learning for Data Scientists"
output = generate_course_from_instruction(
    instruction, 
    progress_callback=progress
)
```

### Russian Language Course

```python
from coursesmith_engine import generate_course_from_instruction

# The engine automatically detects Russian and uses Cyrillic
instruction = "Основы машинного обучения для начинающих"
output = generate_course_from_instruction(instruction)

# Output will be in Russian with proper Cyrillic encoding
print(output)
```

### Custom API Key

```python
from coursesmith_engine import CourseSmithEngine

api_key = "sk-your-openai-api-key"
engine = CourseSmithEngine(api_key=api_key)

course_data = engine.generate_full_course("Your instruction here")
formatted_output = engine.format_output(course_data)

print(formatted_output)
```

## API Reference

### `CourseSmithEngine` Class

The main class for generating educational courses.

#### Constructor

```python
CourseSmithEngine(api_key: str = None, require_api_key: bool = True)
```

**Parameters:**
- `api_key` (str, optional): OpenAI API key. If None, loads from `OPENAI_API_KEY` environment variable.
- `require_api_key` (bool, optional): If False, allows initialization without API key (for testing/formatting only).

#### Methods

##### `detect_language(text: str) -> str`

Detects whether the text is in English or Russian.

**Returns:** `'en'` for English, `'ru'` for Russian.

##### `generate_course_title(user_instruction: str, language: str) -> str`

Generates a professional, high-authority course title.

**Parameters:**
- `user_instruction`: The user's master instruction
- `language`: Detected language ('en' or 'ru')

**Returns:** A professional course title string.

##### `generate_chapter_structure(user_instruction: str, language: str) -> List[str]`

Generates exactly 10 chapter titles with logical progression.

**Parameters:**
- `user_instruction`: The user's master instruction
- `language`: Detected language ('en' or 'ru')

**Returns:** List of 10 chapter title strings.

##### `generate_chapter_content(chapter_title: str, chapter_num: int, course_context: str, language: str) -> str`

Generates expert-level content for a single chapter (~1500 characters).

**Parameters:**
- `chapter_title`: Title of the chapter
- `chapter_num`: Chapter number (1-10)
- `course_context`: Overall course context
- `language`: Detected language ('en' or 'ru')

**Returns:** Rich chapter content with markdown formatting.

##### `generate_full_course(user_instruction: str, progress_callback=None) -> Dict`

Generates a complete course from a single instruction.

**Parameters:**
- `user_instruction`: The master instruction for the course
- `progress_callback`: Optional callback function `(step, total, message)`

**Returns:** Dictionary with:
```python
{
    'language': 'en' or 'ru',
    'title': 'Course Title',
    'chapters': [
        {
            'number': 1,
            'title': 'Chapter Title',
            'content': 'Chapter content...'
        },
        # ... 10 chapters total
    ]
}
```

##### `format_output(course_data: Dict = None) -> str`

Formats course data into the structured output format.

**Parameters:**
- `course_data` (optional): Course data dictionary. If None, uses internally generated data.

**Returns:** Formatted string with `[CHAPTER_START]`/`[CHAPTER_END]` structure.

### `generate_course_from_instruction()` Function

Convenience function for one-step course generation.

```python
generate_course_from_instruction(
    user_instruction: str, 
    api_key: str = None,
    progress_callback = None
) -> str
```

**Parameters:**
- `user_instruction`: The master instruction for the course
- `api_key` (optional): OpenAI API key
- `progress_callback` (optional): Progress tracking function

**Returns:** Formatted course output ready for export.

## Output Format

The engine produces structured output with the following format:

```markdown
# [Course Title]

---

[CHAPTER_START]
TITLE: [Chapter 1 Title]
CONTENT: [Rich markdown content with ~1500 chars]

## Subheader

Content paragraph...

* Bullet point 1
* Bullet point 2
* Bullet point 3

## Another Section

More content...
[CHAPTER_END]

[CHAPTER_START]
TITLE: [Chapter 2 Title]
CONTENT: [Chapter 2 content...]
[CHAPTER_END]

... (10 chapters total)
```

### Format Features

- **`[CHAPTER_START]` / `[CHAPTER_END]`**: Easy parsing markers
- **`TITLE:`**: Chapter title field
- **`CONTENT:`**: Chapter content field
- **Markdown**: Full support for headers (`##`), bullets (`*`), emphasis (`**bold**`, `*italic*`)
- **UTF-8**: Clean encoding that preserves all characters
- **Cyrillic**: Perfect support for Russian text (Кириллица)

## Configuration

### Environment Variables

Create a `.env` file in your project root:

```env
OPENAI_API_KEY=sk-your-api-key-here
```

Or set the environment variable directly:

```bash
export OPENAI_API_KEY="sk-your-api-key-here"
```

## Examples

See `example_coursesmith_engine.py` for complete working examples:

```bash
python example_coursesmith_engine.py
```

## Testing

Run the test suite:

```bash
python test_coursesmith_engine.py
```

Tests include:
- Language detection (English/Russian)
- Output format validation
- UTF-8 and Cyrillic encoding
- Markdown formatting preservation

## Technical Requirements

From the problem statement:

✅ **Language Detection**: English and Russian support  
✅ **Course Title**: High-authority professional title generation  
✅ **10-Chapter Structure**: Logical progression implemented  
✅ **Expert Content**: ~1500 chars per chapter with rich formatting  
✅ **UTF-8 Clean**: Full Cyrillic support without rendering errors  
✅ **Markdown**: Headers, subheaders, and bullet points  
✅ **Structured Output**: `[CHAPTER_START]`, `TITLE:`, `CONTENT:`, `[CHAPTER_END]`  
✅ **Multi-Format**: Ready for PDF, DOCX, EPUB conversion  

## Integration with Existing CourseSmith

The Ultimate Engine can be integrated with the existing CourseSmith application:

```python
# In your existing code
from coursesmith_engine import CourseSmithEngine

# Initialize with session-managed API key
engine = CourseSmithEngine()

# Generate course
course_data = engine.generate_full_course(user_instruction)

# Format output
formatted_text = engine.format_output(course_data)

# Use with existing PDF engine, etc.
```

## Command Line Usage

You can also use the engine directly from the command line:

```bash
python coursesmith_engine.py "Introduction to Web Development"
```

## Troubleshooting

### API Key Not Found

**Error:** `ValueError: OPENAI_API_KEY not found`

**Solution:** Set your OpenAI API key:
```bash
echo "OPENAI_API_KEY=sk-your-key" > .env
```

### Cyrillic Characters Display Incorrectly

**Solution:** Ensure you're using UTF-8 encoding when writing files:
```python
with open('output.txt', 'w', encoding='utf-8') as f:
    f.write(output)
```

### Content Too Short

If generated content is shorter than expected, the API may need adjustment. The system targets ~1500 characters per chapter.

## License

Part of CourseSmith-AI - Proprietary software with license requirements.

## Support

For issues or questions about the CourseSmith Ultimate Engine, please refer to the main CourseSmith-AI repository documentation.
