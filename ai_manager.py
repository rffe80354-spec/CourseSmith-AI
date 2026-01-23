"""
AI Manager Module - Handles OpenAI API interactions for CourseSmith AI.
Provides methods for generating outlines, chapter content, and cover images.
"""

import os
import tempfile
import requests
from dotenv import load_dotenv
from openai import OpenAI


class AIGenerator:
    """Class to handle all OpenAI API interactions."""

    def __init__(self):
        """Initialize the AI Generator with OpenAI client."""
        load_dotenv()
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError(
                "OPENAI_API_KEY not found in environment variables. "
                "Please create a .env file with your API key."
            )
        self.client = OpenAI(api_key=api_key)

    def generate_outline(self, topic, audience):
        """
        Generate a table of contents with 5 chapter titles.

        Args:
            topic: The main topic for the course.
            audience: The target audience description.

        Returns:
            list: A list of 5 chapter title strings.

        Raises:
            Exception: If API call fails.
        """
        try:
            prompt = f"""Create a table of contents for an educational course about "{topic}" 
targeted at {audience}. 

Provide exactly 5 chapter titles that progressively build knowledge from basics to advanced concepts.

Format your response as a simple numbered list with just the chapter titles, like:
1. Introduction to [Topic]
2. [Second Chapter Title]
3. [Third Chapter Title]
4. [Fourth Chapter Title]
5. [Fifth Chapter Title]

Only provide the chapter titles, nothing else."""

            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert curriculum designer who creates "
                        "well-structured educational content.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.7,
                max_tokens=500,
            )

            # Parse the response to extract chapter titles
            content = response.choices[0].message.content.strip()
            lines = content.split("\n")

            chapters = []
            for line in lines:
                line = line.strip()
                if line:
                    # Remove numbering (e.g., "1.", "1)", "Chapter 1:")
                    for prefix in ["1.", "2.", "3.", "4.", "5.", "1)", "2)", "3)", "4)", "5)"]:
                        if line.startswith(prefix):
                            line = line[len(prefix) :].strip()
                            break
                    # Remove "Chapter X:" prefix if present
                    if line.lower().startswith("chapter"):
                        parts = line.split(":", 1)
                        if len(parts) > 1:
                            line = parts[1].strip()
                    if line:
                        chapters.append(line)

            # Ensure we have exactly 5 chapters
            if len(chapters) < 5:
                # Fill with generic titles if needed
                generic = [
                    f"Introduction to {topic}",
                    f"Core Concepts of {topic}",
                    f"Practical Applications",
                    f"Advanced Techniques",
                    f"Conclusion and Next Steps",
                ]
                while len(chapters) < 5:
                    chapters.append(generic[len(chapters)])

            return chapters[:5]

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
