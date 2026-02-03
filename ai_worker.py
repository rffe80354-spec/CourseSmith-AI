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
from openai import OpenAI

from session_manager import is_active, SecurityError, get_user_email, get_license_key

# Hardcoded primary API key - users cannot change this
PRIMARY_API_KEY = "sk-proj-REPLACE_WITH_YOUR_PRIMARY_API_KEY"

# Supabase configuration for credit checking
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://spfwfyjpexktgnusgyib.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "sb_publishable_tmwenU0VyOChNWKG90X_bw_HYf9X5kR")


def check_remaining_credits() -> dict:
    """
    Check remaining credits from Supabase for the current user's license.
    
    Returns:
        dict: {
            'has_credits': bool,  # True if user has remaining credits
            'credits': int,       # Number of remaining credits
            'message': str        # Human-readable status message
        }
    """
    try:
        from supabase import create_client
        
        # Get current user's license key and email from session
        license_key = get_license_key()
        email = get_user_email()
        
        if not license_key or not email:
            return {
                'has_credits': False,
                'credits': 0,
                'message': 'No active license session. Please log in.'
            }
        
        # Connect to Supabase
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        # Query for license credits
        response = supabase.table("licenses").select("credits").eq("license_key", license_key).eq("email", email).execute()
        
        if not response.data or len(response.data) == 0:
            return {
                'has_credits': False,
                'credits': 0,
                'message': 'License not found in database.'
            }
        
        credits = response.data[0].get('credits', 0)
        
        if credits <= 0:
            return {
                'has_credits': False,
                'credits': 0,
                'message': 'No remaining credits. Please purchase more credits to continue.'
            }
        
        return {
            'has_credits': True,
            'credits': credits,
            'message': f'{credits} credits remaining.'
        }
        
    except ImportError:
        return {
            'has_credits': False,
            'credits': 0,
            'message': 'Supabase library not available.'
        }
    except Exception as e:
        return {
            'has_credits': False,
            'credits': 0,
            'message': f'Error checking credits: {str(e)}'
        }


def deduct_credit() -> bool:
    """
    Deduct one credit from the user's account after a successful generation.
    
    Returns:
        bool: True if credit was successfully deducted, False otherwise.
    """
    try:
        from supabase import create_client
        
        license_key = get_license_key()
        email = get_user_email()
        
        if not license_key or not email:
            return False
        
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        # Get current credits
        response = supabase.table("licenses").select("credits").eq("license_key", license_key).eq("email", email).execute()
        
        if not response.data or len(response.data) == 0:
            return False
        
        current_credits = response.data[0].get('credits', 0)
        
        if current_credits <= 0:
            return False
        
        # Deduct one credit
        new_credits = current_credits - 1
        supabase.table("licenses").update({"credits": new_credits}).eq("license_key", license_key).eq("email", email).execute()
        
        return True
        
    except Exception:
        return False


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
    def _check_credits(cls):
        """
        Verify that the user has remaining credits before making an AI request.
        
        Raises:
            ValueError: If user has no remaining credits.
        """
        credit_status = check_remaining_credits()
        if not credit_status['has_credits']:
            raise ValueError(credit_status['message'])
    
    @classmethod
    def get_client(cls):
        """
        Get or create the OpenAI client (thread-safe singleton).
        Uses the hardcoded primary API key.
        
        Returns:
            OpenAI: The OpenAI client instance.
            
        Raises:
            ValueError: If API key is not configured or no credits remaining.
            SecurityError: If no valid session exists.
        """
        # SECURITY CHECK: Require valid session
        cls._check_session()
        
        # CHECK CREDITS: Ensure user has remaining credits
        cls._check_credits()
        
        with cls._client_lock:
            if cls._client is None:
                # Use hardcoded primary API key
                api_key = PRIMARY_API_KEY
                if not api_key or api_key == "sk-proj-REPLACE_WITH_YOUR_PRIMARY_API_KEY":
                    raise ValueError(
                        "Primary API key not configured. "
                        "Please contact the administrator."
                    )
                cls._client = OpenAI(api_key=api_key)
            return cls._client
    
    @classmethod
    def reset_client(cls):
        """Reset the OpenAI client."""
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
            
            # Detect if input is in Russian (contains Cyrillic characters)
            is_russian = bool(re.search(r'[а-яА-ЯёЁ]', self.topic + ' ' + self.audience))
            
            # Build the prompt based on language
            if is_russian:
                system_content = "Вы эксперт по разработке учебных программ, который создает хорошо структурированный образовательный контент."
                prompt = f"""Создайте оглавление для образовательного курса на тему "{self.topic}" 
для аудитории: {self.audience}.

Предоставьте ровно 10-12 названий глав, которые последовательно развивают знания от основ до продвинутых концепций.

Форматируйте ответ как простой нумерованный список только с названиями глав:
1. [Название первой главы]
2. [Название второй главы]
...и так далее.

Названия должны быть профессиональными и привлекательными. Предоставьте только названия глав, ничего больше."""
            else:
                system_content = "You are an AI Content Architect who creates well-structured educational content."
                prompt = f"""Create a table of contents for an educational course about "{self.topic}" 
targeted at {self.audience}.

Provide exactly 10-12 chapter titles that progressively build knowledge from basics to advanced concepts.

Format your response as a simple numbered list with just the chapter titles:
1. [Title of Chapter 1]
2. [Title of Chapter 2]
...and so on.

The titles must be professional and catchy. Ensure the structure is logical and flows well. Only provide the chapter titles, nothing else."""

            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": system_content
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=800
            )
            
            # Parse the response
            content = response.choices[0].message.content.strip()
            lines = content.split('\n')
            
            chapters = []
            for line in lines:
                line = line.strip()
                if line:
                    # Remove numbering (works for both English and Russian)
                    cleaned = re.sub(r'^(\d+[\.\)\:\-]\s*)', '', line).strip()
                    if cleaned:
                        chapters.append(cleaned)
            
            # Ensure we have 10-12 chapters
            if len(chapters) < 10:
                # Fill with generic titles if needed
                if is_russian:
                    generic = [
                        f"Введение в {self.topic}",
                        f"Основные концепции {self.topic}",
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
                        f"Introduction to {self.topic}",
                        f"Core Concepts of {self.topic}",
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
                self.result = chapters[:12]
            else:
                self.result = chapters
            
            if self.callback:
                self.callback(self.result)
                
        except Exception as e:
            self.error = str(e)
            if self.error_callback:
                self.error_callback(self.error)


class ChapterWriter(AIWorkerBase):
    """Worker for generating chapter content using GPT-4o with streaming support."""
    
    def __init__(self, topic, chapter_title, chapter_num, callback=None, error_callback=None,
                 stream_callback=None):
        """
        Initialize the chapter writer.
        
        Args:
            topic: The course topic.
            chapter_title: The title of the chapter to write.
            chapter_num: The chapter number.
            callback: Function to call with results (chapter_title, content).
            error_callback: Function to call on error (receives error message).
            stream_callback: Function to call with incremental text chunks for live preview.
        """
        self.topic = topic
        self.chapter_title = chapter_title
        self.chapter_num = chapter_num
        self.callback = callback
        self.error_callback = error_callback
        self.stream_callback = stream_callback
        self.thread = None
        self.result = None
        self.error = None
    
    def start(self):
        """Start the worker thread."""
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()
    
    def _run(self):
        """Execute the chapter content generation with streaming support."""
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

            # Check if streaming is requested
            if self.stream_callback:
                # Use streaming API for live preview
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
                    max_tokens=1200,
                    stream=True
                )
                
                # Collect full content while streaming chunks
                full_content = []
                chunk_count = 0
                for chunk in response:
                    chunk_count += 1
                    # Security check every 20 chunks to reduce overhead
                    if chunk_count % 20 == 0 and not is_active():
                        raise SecurityError("Session expired during generation.")
                    
                    if chunk.choices and chunk.choices[0].delta.content:
                        text_chunk = chunk.choices[0].delta.content
                        full_content.append(text_chunk)
                        # Send chunk to stream callback for live preview
                        if self.stream_callback:
                            self.stream_callback(text_chunk)
                
                content = "".join(full_content).strip()
            else:
                # Non-streaming mode (original behavior)
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
