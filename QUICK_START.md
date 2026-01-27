# CourseSmith Ultimate Engine - Quick Start Guide

## What is it?

The **CourseSmith Ultimate Engine** generates professional educational courses from a single instruction. It supports both English and Russian languages with full UTF-8 and Cyrillic character support.

## Quick Examples

### 1. Generate a Course (English)

```python
from coursesmith_engine import generate_course_from_instruction

# Simple one-liner
output = generate_course_from_instruction("Introduction to Python Programming")

# Save to file
with open('course.txt', 'w', encoding='utf-8') as f:
    f.write(output)

print("Course generated!")
```

### 2. Generate a Course (Russian)

```python
from coursesmith_engine import generate_course_from_instruction

# Автоматически определяет русский язык
output = generate_course_from_instruction("Основы машинного обучения")

# Сохранить в файл
with open('course_ru.txt', 'w', encoding='utf-8') as f:
    f.write(output)

print("Курс создан!")
```

### 3. With Progress Tracking

```python
from coursesmith_engine import generate_course_from_instruction

def show_progress(step, total, message):
    percent = (step / total) * 100
    print(f"[{percent:.0f}%] {message}")

output = generate_course_from_instruction(
    "Web Development Bootcamp",
    progress_callback=show_progress
)
```

### 4. Using the Engine Class Directly

```python
from coursesmith_engine import CourseSmithEngine

# Initialize engine
engine = CourseSmithEngine()

# Generate course
course_data = engine.generate_full_course("Data Science Fundamentals")

# Get formatted output
output = engine.format_output(course_data)

# Access individual components
print(f"Title: {course_data['title']}")
print(f"Language: {course_data['language']}")
print(f"Chapters: {len(course_data['chapters'])}")
```

## Output Format

The engine produces structured text with these markers:

```
# [Course Title]

---

[CHAPTER_START]
TITLE: [Chapter Title]
CONTENT: [Rich content with markdown formatting]
[CHAPTER_END]

... (10 chapters total)
```

## Requirements

1. **OpenAI API Key**: Set in `.env` file:
   ```
   OPENAI_API_KEY=sk-your-api-key-here
   ```

2. **Python Packages**: Already installed with requirements.txt
   - `openai`
   - `python-dotenv`

## What You Get

Each course includes:
- ✅ Professional title
- ✅ Exactly 10 chapters
- ✅ ~1500 characters per chapter
- ✅ Markdown formatting (headers, bullets, emphasis)
- ✅ Logical progression from basics to advanced
- ✅ Ready for PDF/DOCX/EPUB conversion

## Supported Languages

- **English**: Automatic detection
- **Russian**: Full Cyrillic support with automatic detection
- **Detection**: Based on presence of Cyrillic characters

## Common Use Cases

### Generate Course for PDF Export
```python
output = generate_course_from_instruction("Machine Learning")
# Use with existing pdf_engine.py to create PDF
```

### Generate Multiple Courses
```python
topics = [
    "Python Programming",
    "Web Development",
    "Data Analysis"
]

for topic in topics:
    output = generate_course_from_instruction(topic)
    filename = f"course_{topic.replace(' ', '_').lower()}.txt"
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(output)
```

### Custom API Key
```python
from coursesmith_engine import CourseSmithEngine

my_api_key = "sk-your-key-here"
engine = CourseSmithEngine(api_key=my_api_key)
course_data = engine.generate_full_course("Your Topic")
```

## Testing

Run the test suite to verify everything works:

```bash
# Unit tests
python test_coursesmith_engine.py

# Integration tests
python test_integration.py

# Final validation
python validate_final.py
```

## Example Output

```markdown
# Mastering Python Programming: A Complete Guide

---

[CHAPTER_START]
TITLE: Introduction to Python
CONTENT: ## What is Python?

Python is a high-level programming language known for its simplicity...

## Key Features

* Easy to learn and read
* Versatile and powerful
* Large ecosystem of libraries

## Getting Started

To begin your Python journey...
[CHAPTER_END]

... (9 more chapters)
```

## Troubleshooting

### API Key Not Found
```bash
# Create .env file
echo "OPENAI_API_KEY=sk-your-key" > .env
```

### Cyrillic Characters Don't Display
```python
# Always use UTF-8 encoding
with open('file.txt', 'w', encoding='utf-8') as f:
    f.write(output)
```

### Import Error
```bash
# Make sure you're in the correct directory
cd /path/to/CourseSmith-AI
python your_script.py
```

## More Information

- **Full Documentation**: See `COURSESMITH_ENGINE_README.md`
- **Examples**: See `example_coursesmith_engine.py`
- **Implementation Details**: See `IMPLEMENTATION_SUMMARY.md`

## Command Line Usage

You can also use it from the command line:

```bash
python coursesmith_engine.py "Your course topic here"
```

---

**That's it!** You're ready to generate professional educational courses with the CourseSmith Ultimate Engine.
