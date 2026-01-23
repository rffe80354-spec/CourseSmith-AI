"""
AI Worker Module - Threaded AI Operations for CourseSmith ENTERPRISE.
Provides background workers for outline, chapter, and cover generation.
SECURITY: Requires valid session token to function (anti-tamper protection).
"""

import os
import re
import threading
import tempfile
import requests
from dotenv import load_dotenv
from openai import OpenAI

from session_manager import is_active, SecurityError


class AIWorkerBase:
    """Base class for AI workers with common functionality."""
    
    _client = None
    _client_lock = threading.Lock()
    
    @classmethod
    def _check_session(cls):
        """
        Verify that a valid session is active.
        
        Raises:
            SecurityError: If no valid session token exists.
        """
        if not is_active():
            raise SecurityError("Unauthorized: No valid session. Please activate your license.")
    
    @classmethod
    def get_client(cls):
        """
        Get or create the OpenAI client (thread-safe singleton).
        
        Returns:
            OpenAI: The OpenAI client instance.
            
        Raises:
            ValueError: If API key is not configured.
            SecurityError: If no valid session exists.
        """
        # SECURITY CHECK: Require valid session
        cls._check_session()
        
        with cls._client_lock:
            if cls._client is None:
                load_dotenv()
                api_key = os.getenv("OPENAI_API_KEY")
                if not api_key:
                    raise ValueError(
                        "OPENAI_API_KEY not found in environment variables. "
                        "Please configure your API key in Settings."
                    )
                cls._client = OpenAI(api_key=api_key)
            return cls._client
    
    @classmethod
    def reset_client(cls):
        """Reset the OpenAI client (for API key changes)."""
        with cls._client_lock:
            cls._client = None


class OutlineGenerator(AIWorkerBase):
    """Worker for generating course outlines using GPT-4o."""
    
    def __init__(self, topic, audience, callback=None, error_callback=None):
        """
        Initialize the outline generator.
        
        Args:
            topic: The course topic.
            audience: The target audience.
            callback: Function to call with results (list of chapter titles).
            error_callback: Function to call on error (receives error message).
        """
        self.topic = topic
        self.audience = audience
        self.callback = callback
        self.error_callback = error_callback
        self.thread = None
        self.result = None
        self.error = None
    
    def start(self):
        """Start the worker thread."""
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()
    
    def _run(self):
        """Execute the outline generation."""
        try:
            client = self.get_client()
            
            prompt = f"""Create a detailed table of contents for an educational course about "{self.topic}" 
targeted at {self.audience}.

Provide exactly 5 chapter titles that progressively build knowledge from basics to advanced concepts.

Format your response as a simple numbered list with just the chapter titles:
1. [First Chapter Title]
2. [Second Chapter Title]
3. [Third Chapter Title]
4. [Fourth Chapter Title]
5. [Fifth Chapter Title]

Make the titles descriptive and engaging. Only provide the chapter titles, nothing else."""

            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert curriculum designer who creates "
                        "well-structured educational content."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=500
            )
            
            # Parse the response
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
            
            # Ensure we have 5 chapters
            while len(chapters) < 5:
                chapters.append(f"Additional Topic {len(chapters) + 1}")
            
            self.result = chapters[:5]
            
            if self.callback:
                self.callback(self.result)
                
        except Exception as e:
            self.error = str(e)
            if self.error_callback:
                self.error_callback(self.error)


class ChapterWriter(AIWorkerBase):
    """Worker for generating chapter content using GPT-4o."""
    
    def __init__(self, topic, chapter_title, chapter_num, callback=None, error_callback=None):
        """
        Initialize the chapter writer.
        
        Args:
            topic: The course topic.
            chapter_title: The title of the chapter to write.
            chapter_num: The chapter number.
            callback: Function to call with results (chapter_title, content).
            error_callback: Function to call on error (receives error message).
        """
        self.topic = topic
        self.chapter_title = chapter_title
        self.chapter_num = chapter_num
        self.callback = callback
        self.error_callback = error_callback
        self.thread = None
        self.result = None
        self.error = None
    
    def start(self):
        """Start the worker thread."""
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()
    
    def _run(self):
        """Execute the chapter content generation."""
        try:
            client = self.get_client()
            
            prompt = f"""Write detailed educational content for Chapter {self.chapter_num}: "{self.chapter_title}" 
in a comprehensive course about "{self.topic}".

Requirements:
- Write approximately 400-500 words
- Use clear, educational language suitable for learners
- Include practical examples and explanations where appropriate
- Structure the content logically with clear paragraphs
- You may use markdown headers (## for subsections) to organize content
- Make it engaging and informative
- Do not include the chapter title at the start, just the content

Write the content directly."""

            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert educator who writes clear, engaging, "
                        "and comprehensive educational content."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1200
            )
            
            content = response.choices[0].message.content.strip()
            self.result = (self.chapter_title, content)
            
            if self.callback:
                self.callback(self.chapter_title, content)
                
        except Exception as e:
            self.error = str(e)
            if self.error_callback:
                self.error_callback(self.error)


class CoverGenerator(AIWorkerBase):
    """Worker for generating cover images using DALL-E 3."""
    
    def __init__(self, topic, callback=None, error_callback=None):
        """
        Initialize the cover generator.
        
        Args:
            topic: The course topic for cover design.
            callback: Function to call with results (image file path).
            error_callback: Function to call on error (receives error message).
        """
        self.topic = topic
        self.callback = callback
        self.error_callback = error_callback
        self.thread = None
        self.result = None
        self.error = None
    
    def start(self):
        """Start the worker thread."""
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()
    
    def _run(self):
        """Execute the cover image generation."""
        try:
            client = self.get_client()
            
            prompt = f"""Create a professional, modern book cover design for an educational course about "{self.topic}".

Style requirements:
- Clean, minimalist and modern design
- Professional color scheme (blues, greens, or sophisticated neutrals)
- Abstract or symbolic representation of the topic
- Suitable for an educational/academic publication
- High quality, polished appearance
- No text, letters, words, or numbers in the image"""

            response = client.images.generate(
                model="dall-e-3",
                prompt=prompt,
                size="1024x1024",
                quality="standard",
                n=1
            )
            
            image_url = response.data[0].url
            
            # Download the image
            try:
                img_response = requests.get(image_url, timeout=60)
                img_response.raise_for_status()
            except requests.exceptions.Timeout:
                raise Exception("Image download timed out. Please try again.")
            except requests.exceptions.RequestException as req_err:
                raise Exception(f"Failed to download image: {str(req_err)}")
            
            # Save to temporary file
            temp_file = tempfile.NamedTemporaryFile(
                suffix=".png",
                delete=False,
                prefix="coursesmith_cover_"
            )
            temp_file.write(img_response.content)
            temp_file.close()
            
            self.result = temp_file.name
            
            if self.callback:
                self.callback(self.result)
                
        except Exception as e:
            self.error = str(e)
            if self.error_callback:
                self.error_callback(self.error)
