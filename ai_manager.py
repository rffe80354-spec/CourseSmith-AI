"""
AI Manager Module - Handles OpenAI API interactions for CourseSmith AI.
Provides methods for generating outlines, chapter content, and cover images.

API Key Retrieval:
    The OpenAI API key is retrieved from Supabase database using the secrets_manager
    module. This keeps the API key secure and out of the source code.
    
    Supabase Table: 'secrets'
    Secret Name: 'OPENAI_API_KEY'
"""

import os
import re
import tempfile
import requests
from openai import OpenAI

# Import secrets manager for secure API key retrieval from Supabase
# The API key is stored in Supabase 'secrets' table with name='OPENAI_API_KEY'
from secrets_manager import get_openai_api_key, is_supabase_configured


class AIGenerator:
    """Class to handle all OpenAI API interactions."""

    def __init__(self):
        """
        Initialize the AI Generator with OpenAI client.
        
        The API key is retrieved from Supabase 'secrets' table.
        If Supabase is not configured or the key is not found,
        an appropriate error is raised.
        
        Raises:
            ValueError: If API key cannot be retrieved from Supabase.
        """
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
        
        self.client = OpenAI(api_key=api_key)

    def generate_outline(self, topic, audience):
        """
        Generate a table of contents with 10-12 chapter titles.

        Args:
            topic: The main topic for the course.
            audience: The target audience description.

        Returns:
            list: A list of 10-12 chapter title strings.

        Raises:
            Exception: If API call fails.
        """
        try:
            # Detect if input is in Russian (contains Cyrillic characters)
            is_russian = bool(re.search(r'[а-яА-ЯёЁ]', topic + ' ' + audience))
            
            # Build the prompt based on language
            if is_russian:
                system_content = "Вы эксперт по разработке учебных программ, который создает хорошо структурированный образовательный контент."
                prompt = f"""Создайте оглавление для образовательного курса на тему "{topic}" 
для аудитории: {audience}.

Предоставьте ровно 10-12 названий глав, которые последовательно развивают знания от основ до продвинутых концепций.

Форматируйте ответ как простой нумерованный список только с названиями глав:
1. [Название первой главы]
2. [Название второй главы]
...и так далее.

Названия должны быть профессиональными и привлекательными. Предоставьте только названия глав, ничего больше."""
            else:
                system_content = "You are an AI Content Architect who creates well-structured educational content."
                prompt = f"""Create a table of contents for an educational course about "{topic}" 
targeted at {audience}.

Provide exactly 10-12 chapter titles that progressively build knowledge from basics to advanced concepts.

Format your response as a simple numbered list with just the chapter titles:
1. [Title of Chapter 1]
2. [Title of Chapter 2]
...and so on.

The titles must be professional and catchy. Ensure the structure is logical and flows well. Only provide the chapter titles, nothing else."""

            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": system_content,
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.7,
                max_tokens=800,
            )

            # Parse the response to extract chapter titles
            content = response.choices[0].message.content.strip()
            lines = content.split("\n")

            chapters = []
            for line in lines:
                line = line.strip()
                if line:
                    # Remove numbering (works for both English and Russian)
                    line = re.sub(r'^(\d+[\.\)\:\-]\s*)', '', line).strip()
                    # Remove "Chapter X:" prefix if present
                    if line.lower().startswith("chapter") or line.startswith("Глава"):
                        parts = line.split(":", 1)
                        if len(parts) > 1:
                            line = parts[1].strip()
                    if line:
                        chapters.append(line)

            # Ensure we have 10-12 chapters
            if len(chapters) < 10:
                # Fill with generic titles if needed
                if is_russian:
                    generic = [
                        f"Введение в {topic}",
                        f"Основные концепции {topic}",
                        f"Практические применения",
                        f"Продвинутые техники",
                        f"Заключение и следующие шаги",
                        f"Дополнительная тема 6",
                        f"Дополнительная тема 7",
                        f"Дополнительная тема 8",
                        f"Дополнительная тема 9",
                        f"Дополнительная тема 10",
                        f"Дополнительная тема 11",
                        f"Дополнительная тема 12"
                    ]
                else:
                    generic = [
                        f"Introduction to {topic}",
                        f"Core Concepts of {topic}",
                        f"Practical Applications",
                        f"Advanced Techniques",
                        f"Conclusion and Next Steps",
                        f"Additional Topic 6",
                        f"Additional Topic 7",
                        f"Additional Topic 8",
                        f"Additional Topic 9",
                        f"Additional Topic 10",
                        f"Additional Topic 11",
                        f"Additional Topic 12"
                    ]
                while len(chapters) < 10:
                    chapters.append(generic[len(chapters)])

            # Return 10-12 chapters (truncate to 12 if more, already at least 10 from above)
            if len(chapters) > 12:
                return chapters[:12]
            else:
                return chapters

        except Exception as e:
            raise Exception(f"Failed to generate outline: {str(e)}")

    def generate_chapter(self, topic, chapter_title):
        """
        Generate detailed content for a single chapter.

        Args:
            topic: The main topic for the course.
            chapter_title: The title of the chapter to generate.

        Returns:
            str: Detailed chapter content (~400 words).

        Raises:
            Exception: If API call fails.
        """
        try:
            prompt = f"""Write detailed educational content for a chapter titled "{chapter_title}" 
in a course about "{topic}".

Requirements:
- Write approximately 400 words
- Use clear, educational language
- Include practical examples where appropriate
- Structure the content with clear explanations
- Make it engaging and informative

Write the content directly without any chapter title or headers."""

            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert educator who writes clear, engaging, "
                        "and comprehensive educational content.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.7,
                max_tokens=1000,
            )

            content = response.choices[0].message.content.strip()
            return content

        except Exception as e:
            raise Exception(f"Failed to generate chapter content: {str(e)}")

    def generate_cover(self, topic):
        """
        Generate a cover image using DALL-E 3.

        Args:
            topic: The main topic for the course.

        Returns:
            str: Path to the downloaded cover image.

        Raises:
            Exception: If API call or download fails.
        """
        try:
            prompt = f"""Create a professional, modern book cover design for an educational course about "{topic}".

Style requirements:
- Clean, minimalist design
- Professional color scheme
- Abstract or symbolic representation of the topic
- Suitable for an educational/academic publication
- No text or letters in the image"""

            response = self.client.images.generate(
                model="dall-e-3",
                prompt=prompt,
                size="1024x1024",
                quality="standard",
                n=1,
            )

            image_url = response.data[0].url

            # Download the image to a temporary file
            try:
                img_response = requests.get(image_url, timeout=60)
                img_response.raise_for_status()
            except requests.exceptions.Timeout:
                raise Exception("Image download timed out. Please try again.")
            except requests.exceptions.RequestException as req_err:
                raise Exception(f"Failed to download image: {str(req_err)}")

            # Create temporary file for the image
            temp_file = tempfile.NamedTemporaryFile(
                suffix=".png", delete=False, prefix="coursesmith_cover_"
            )
            temp_file.write(img_response.content)
            temp_file.close()

            return temp_file.name

        except Exception as e:
            raise Exception(f"Failed to generate cover image: {str(e)}")
