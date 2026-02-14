"""
CourseSmith Ultimate Engine - Professional Educational Course Generator
Generates multi-format educational courses with UTF-8 and Cyrillic support.

Features:
- Language detection (English/Russian)
- Professional course titles
- 10-chapter logical structure
- Expert-level content (~1500 chars per chapter)
- Markdown formatting with subheaders and bullet points
- Clean UTF-8 output with full Cyrillic support
- Structured output format for easy conversion to PDF, DOCX, EPUB

API Key Management:
    The OpenAI API key is retrieved from Supabase database using the secrets_manager
    module. This keeps the API key secure and out of the source code.
    
    Supabase Table: 'secrets'
    Secret Name: 'OPENAI_API_KEY'
"""

import os
import re
from typing import Dict, List, Tuple
from openai import OpenAI

# Import secrets manager for secure API key retrieval from Supabase
# The API key is stored in Supabase 'secrets' table with name='OPENAI_API_KEY'
from secrets_manager import get_openai_api_key, is_supabase_configured


class CourseSmithEngine:
    """
    The CourseSmith Ultimate Engine for generating professional educational courses.
    
    API Key Retrieval:
        The OpenAI API key is retrieved from Supabase 'secrets' table.
        If no api_key is provided, it will be fetched automatically.
    """

    def __init__(self, api_key: str = None, require_api_key: bool = True):
        """
        Initialize the CourseSmith Ultimate Engine.

        Args:
            api_key: OpenAI API key. If None, will be retrieved from Supabase.
            require_api_key: If False, allows initialization without API key (for testing).
        
        Raises:
            ValueError: If API key is required but cannot be retrieved from Supabase.
        """
        if api_key is None and require_api_key:
            # Retrieve API key from Supabase database
            # The key is stored in 'secrets' table with name='OPENAI_API_KEY'
            api_key = get_openai_api_key()
            
            if not api_key:
                # Provide helpful error message based on configuration state
                if not is_supabase_configured():
                    raise ValueError(
                        "Supabase not configured. Please set SUPABASE_URL and SUPABASE_KEY "
                        "in your .env file to enable API key retrieval."
                    )
                else:
                    raise ValueError(
                        "OpenAI API key not found in Supabase. "
                        "Please ensure 'OPENAI_API_KEY' exists in the 'secrets' table."
                    )
        
        self.client = OpenAI(api_key=api_key) if api_key else None
        self.language = None
        self.course_title = None
        self.chapters = []

    def _sanitize_input(self, text: str, max_length: int = 2000) -> str:
        """
        Sanitize user input to prevent prompt injection.
        
        Args:
            text: The input text to sanitize.
            max_length: Maximum allowed length.
            
        Returns:
            str: Sanitized text.
        """
        if not text:
            return ""
        
        # Limit length
        text = text[:max_length]
        
        # Remove potential prompt injection patterns
        # Remove system-like instructions
        text = re.sub(r'(?i)(ignore\s+(previous|above|all)\s+(instructions?|prompts?))', '', text)
        text = re.sub(r'(?i)(system\s*:|assistant\s*:|user\s*:)', '', text)
        
        # Strip excessive whitespace
        text = ' '.join(text.split())
        
        return text.strip()

    def detect_language(self, text: str) -> str:
        """
        Detect if the text is in Russian or English.

        Args:
            text: The text to analyze.

        Returns:
            str: 'ru' for Russian, 'en' for English.
        """
        # Check for Cyrillic characters
        if re.search(r'[а-яА-ЯёЁ]', text):
            return 'ru'
        return 'en'

    def generate_course_title(self, user_instruction: str, language: str) -> str:
        """
        Generate a high-authority professional course title.

        Args:
            user_instruction: The user's master instruction.
            language: The detected language ('en' or 'ru').

        Returns:
            str: A professional course title.
        """
        try:
            # Sanitize input
            user_instruction = self._sanitize_input(user_instruction)
            
            if language == 'ru':
                system_content = "Вы эксперт по созданию профессиональных образовательных курсов."
                prompt = f"""На основе следующей инструкции создайте профессиональное, авторитетное название для образовательного курса:

"{user_instruction}"

Требования:
- Название должно быть привлекательным и профессиональным
- Отражать главную тему курса
- Быть кратким (максимум 10-12 слов)
- Подходить для образовательного материала высокого уровня

Предоставьте только название курса, без дополнительных объяснений."""
            else:
                system_content = "You are an expert at creating professional educational courses."
                prompt = f"""Based on the following instruction, create a professional, high-authority title for an educational course:

"{user_instruction}"

Requirements:
- The title must be catchy and professional
- Reflect the main theme of the course
- Be concise (maximum 10-12 words)
- Suitable for high-level educational material

Provide only the course title, without additional explanations."""

            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_content},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=100
            )

            title = response.choices[0].message.content.strip()
            # Remove quotes if present
            title = title.strip('"\'')
            return title

        except Exception as e:
            raise Exception(f"Failed to generate course title: {str(e)}")

    def generate_chapter_structure(self, user_instruction: str, language: str) -> List[str]:
        """
        Generate a logical 10-chapter structure.

        Args:
            user_instruction: The user's master instruction.
            language: The detected language ('en' or 'ru').

        Returns:
            list: A list of exactly 10 chapter titles.
        """
        try:
            # Sanitize input
            user_instruction = self._sanitize_input(user_instruction)
            
            if language == 'ru':
                system_content = "Вы эксперт по разработке структуры образовательных курсов."
                prompt = f"""На основе следующей инструкции создайте структуру из РОВНО 10 глав для образовательного курса:

"{user_instruction}"

Требования:
- Ровно 10 глав
- Логическая прогрессия от основ к продвинутым темам
- Каждое название должно быть профессиональным и информативным
- Главы должны последовательно раскрывать тему

Форматируйте ответ как нумерованный список:
1. [Название главы 1]
2. [Название главы 2]
...
10. [Название главы 10]

Предоставьте только список глав, ничего больше."""
            else:
                system_content = "You are an expert at structuring educational courses."
                prompt = f"""Based on the following instruction, create a structure of EXACTLY 10 chapters for an educational course:

"{user_instruction}"

Requirements:
- Exactly 10 chapters
- Logical progression from basics to advanced topics
- Each title must be professional and informative
- Chapters should sequentially develop the topic

Format your response as a numbered list:
1. [Chapter 1 Title]
2. [Chapter 2 Title]
...
10. [Chapter 10 Title]

Provide only the list of chapters, nothing else."""

            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_content},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=600
            )

            content = response.choices[0].message.content.strip()
            lines = content.split('\n')

            chapters = []
            for line in lines:
                line = line.strip()
                if line:
                    # Remove numbering
                    cleaned = re.sub(r'^(\d+[\.\)\:\-]\s*)', '', line).strip()
                    if cleaned:
                        chapters.append(cleaned)

            # Ensure exactly 10 chapters
            if len(chapters) < 10:
                # Fill with generic titles if needed
                if language == 'ru':
                    generic_base = "Дополнительная глава"
                else:
                    generic_base = "Additional Chapter"
                
                while len(chapters) < 10:
                    chapters.append(f"{generic_base} {len(chapters) + 1}")
            elif len(chapters) > 10:
                chapters = chapters[:10]

            return chapters

        except Exception as e:
            raise Exception(f"Failed to generate chapter structure: {str(e)}")

    def generate_chapter_content(self, chapter_title: str, chapter_num: int, 
                                 course_context: str, language: str) -> str:
        """
        Generate expert-level content for a single chapter (~1500 characters).

        Args:
            chapter_title: The title of the chapter.
            chapter_num: The chapter number (1-10).
            course_context: The overall course context/instruction.
            language: The detected language ('en' or 'ru').

        Returns:
            str: Professional chapter content with markdown formatting.
        """
        try:
            # Sanitize inputs
            chapter_title = self._sanitize_input(chapter_title, max_length=500)
            course_context = self._sanitize_input(course_context)
            
            if language == 'ru':
                system_content = "Вы эксперт-преподаватель, который создает профессиональный образовательный контент высокого уровня."
                prompt = f"""Напишите экспертный контент для Главы {chapter_num}: "{chapter_title}"
в образовательном курсе на тему: "{course_context}"

Требования:
- Объем: примерно 1500 символов (около 250-300 слов)
- Используйте подзаголовки (## для разделов) для структурирования
- Включите маркированные списки (* пункт) где уместно
- Профессиональный, экспертный язык
- Практические примеры и объяснения
- Четкая структура и логика изложения
- Используйте markdown форматирование
- НЕ включайте номер или название главы в начале - только контент

Напишите содержание главы напрямую."""
            else:
                system_content = "You are an expert educator who creates professional high-level educational content."
                prompt = f"""Write expert-level content for Chapter {chapter_num}: "{chapter_title}"
in an educational course about: "{course_context}"

Requirements:
- Length: approximately 1500 characters (about 250-300 words)
- Use subheaders (## for sections) to structure the content
- Include bullet points (* item) where appropriate
- Professional, expert-level language
- Practical examples and explanations
- Clear structure and logical flow
- Use markdown formatting
- Do NOT include the chapter number or title at the start - just the content

Write the chapter content directly."""

            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_content},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1000
            )

            content = response.choices[0].message.content.strip()
            return content

        except Exception as e:
            raise Exception(f"Failed to generate chapter {chapter_num} content: {str(e)}")

    def generate_full_course(self, user_instruction: str, 
                           progress_callback=None) -> Dict[str, any]:
        """
        Generate a complete educational course from a single instruction.

        Args:
            user_instruction: The user's master instruction.
            progress_callback: Optional callback function(step, total, message).

        Returns:
            dict: Complete course data with title and chapters.
        """
        try:
            # Step 1: Detect language
            if progress_callback:
                progress_callback(1, 12, "Detecting language...")
            
            self.language = self.detect_language(user_instruction)

            # Step 2: Generate course title
            if progress_callback:
                progress_callback(2, 12, "Generating course title...")
            
            self.course_title = self.generate_course_title(user_instruction, self.language)

            # Step 3: Generate chapter structure
            if progress_callback:
                progress_callback(3, 12, "Creating chapter structure...")
            
            chapter_titles = self.generate_chapter_structure(user_instruction, self.language)

            # Steps 4-13: Generate content for each chapter
            self.chapters = []
            for i, chapter_title in enumerate(chapter_titles, start=1):
                if progress_callback:
                    progress_callback(3 + i, 12, f"Writing chapter {i}/10: {chapter_title[:30]}...")
                
                content = self.generate_chapter_content(
                    chapter_title, i, user_instruction, self.language
                )
                
                self.chapters.append({
                    'number': i,
                    'title': chapter_title,
                    'content': content
                })

            return {
                'language': self.language,
                'title': self.course_title,
                'chapters': self.chapters
            }

        except Exception as e:
            raise Exception(f"Failed to generate full course: {str(e)}")

    def format_output(self, course_data: Dict = None) -> str:
        """
        Format the course data in the required output structure.

        Args:
            course_data: Optional course data dict. If None, uses internal data.

        Returns:
            str: Formatted course output with [CHAPTER_START]/[CHAPTER_END] markers.
        """
        if course_data is None:
            if not self.course_title or not self.chapters:
                raise ValueError("No course data available. Generate a course first.")
            course_data = {
                'title': self.course_title,
                'chapters': self.chapters
            }

        # Build the output
        output_lines = []
        
        # Add course title at the top
        output_lines.append(f"# {course_data['title']}")
        output_lines.append("")
        output_lines.append("---")
        output_lines.append("")

        # Add each chapter with the required format
        for chapter in course_data['chapters']:
            output_lines.append("[CHAPTER_START]")
            output_lines.append(f"TITLE: {chapter['title']}")
            output_lines.append(f"CONTENT: {chapter['content']}")
            output_lines.append("[CHAPTER_END]")
            output_lines.append("")

        return "\n".join(output_lines)


def generate_course_from_instruction(user_instruction: str, api_key: str = None,
                                     progress_callback=None) -> str:
    """
    Convenience function to generate a complete course and return formatted output.

    Args:
        user_instruction: The user's master instruction for the course.
        api_key: Optional OpenAI API key. If None, loads from environment.
        progress_callback: Optional callback function(step, total, message).

    Returns:
        str: Formatted course output ready for conversion to PDF/DOCX/EPUB.

    Example:
        >>> output = generate_course_from_instruction("Machine Learning for Beginners")
        >>> print(output)
    """
    engine = CourseSmithEngine(api_key=api_key)
    course_data = engine.generate_full_course(user_instruction, progress_callback)
    return engine.format_output(course_data)


if __name__ == "__main__":
    # Example usage
    import sys
    
    if len(sys.argv) > 1:
        instruction = " ".join(sys.argv[1:])
    else:
        instruction = "Introduction to Python Programming for Beginners"
    
    print(f"Generating course for: {instruction}\n")
    
    def progress(step, total, message):
        print(f"[{step}/{total}] {message}")
    
    try:
        output = generate_course_from_instruction(instruction, progress_callback=progress)
        print("\n" + "="*80)
        print(output)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
