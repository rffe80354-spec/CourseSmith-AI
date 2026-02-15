"""
AI Worker Module - Threaded AI Operations for CourseSmith ENTERPRISE.
Provides background workers for outline, chapter, and cover generation.
SECURITY: Requires valid session token to function (anti-tamper protection).

API Key Retrieval:
    The OpenAI API key is retrieved from a Supabase Edge Function
    with TTL-based caching for security and performance.
"""

import os
import re
import threading
import tempfile
import time
import requests
from openai import OpenAI

from session_manager import is_active, SecurityError, get_user_email, get_license_key

# Supabase Edge Function URL for secure API key retrieval (configurable via env var)
SUPABASE_EDGE_FUNCTION_URL = os.getenv(
    "SUPABASE_EDGE_FUNCTION_URL",
    "https://spfwfyjpexktgnusgyib.functions.supabase.co/get_openai_key"
)

# Supabase configuration for credit checking and Edge Function authorization
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://spfwfyjpexktgnusgyib.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "sb_publishable_tmwenU0VyOChNWKG90X_bw_HYf9X5kR")

# Thread-safe singleton for Supabase client to avoid repeated connection overhead
_supabase_client = None
_supabase_lock = threading.Lock()

# Thread-safe cache for OpenAI API key with TTL
_openai_api_key_cache = None
_openai_api_key_cache_time = None
_openai_api_key_lock = threading.Lock()

# Cache TTL in seconds (10 minutes for balance between security and performance)
API_KEY_CACHE_TTL = 600


class KeyRetrievalError(Exception):
    """Exception raised when API key retrieval from Supabase Edge Function fails."""
    pass


def _is_cache_valid() -> bool:
    """
    Check if the cached API key is still valid based on TTL.
    
    Returns:
        bool: True if cache is valid, False if expired or empty.
    """
    if _openai_api_key_cache is None or _openai_api_key_cache_time is None:
        return False
    return (time.time() - _openai_api_key_cache_time) < API_KEY_CACHE_TTL


def fetch_openai_api_key() -> str:
    """
    Fetch the OpenAI API key from Supabase Edge Function.
    
    This function makes a GET request to the Supabase Edge Function
    to retrieve the OpenAI API key securely. The key is cached
    with a TTL (time-to-live) for security and performance.
    
    Returns:
        str: The OpenAI API key.
        
    Raises:
        KeyRetrievalError: If the key cannot be retrieved from the Edge Function.
    """
    global _openai_api_key_cache, _openai_api_key_cache_time
    
    with _openai_api_key_lock:
        # Return cached key if valid (within TTL)
        if _is_cache_valid():
            return _openai_api_key_cache
        
        try:
            # Make GET request to Supabase Edge Function
            headers = {
                "Authorization": f"Bearer {SUPABASE_KEY}",
                "Content-Type": "application/json"
            }
            
            response = requests.get(
                SUPABASE_EDGE_FUNCTION_URL,
                headers=headers,
                timeout=10
            )
            
            # Check for HTTP errors
            if response.status_code == 401:
                raise KeyRetrievalError(
                    "Ошибка авторизации ключа. Проверьте настройки доступа."
                )
            elif response.status_code == 403:
                raise KeyRetrievalError(
                    "Доступ запрещён. Недостаточно прав для получения ключа."
                )
            elif response.status_code != 200:
                raise KeyRetrievalError(
                    f"Ошибка получения ключа. Код ответа: {response.status_code}"
                )
            
            # Parse JSON response and extract key
            data = response.json()
            api_key = data.get("key")
            
            if not api_key:
                raise KeyRetrievalError(
                    "Ключ API не найден в ответе сервера."
                )
            
            # Validate key format (OpenAI keys start with 'sk-')
            if not api_key.startswith("sk-"):
                raise KeyRetrievalError(
                    "Получен некорректный формат ключа API."
                )
            
            # Cache the key with timestamp
            _openai_api_key_cache = api_key
            _openai_api_key_cache_time = time.time()
            return api_key
            
        except requests.exceptions.Timeout:
            raise KeyRetrievalError(
                "Превышено время ожидания ответа от сервера ключей."
            )
        except requests.exceptions.ConnectionError:
            raise KeyRetrievalError(
                "Ошибка подключения к серверу ключей. Проверьте интернет-соединение."
            )
        except requests.exceptions.RequestException as e:
            raise KeyRetrievalError(
                f"Ошибка запроса ключа: {str(e)}"
            )
        except ValueError:  # JSON decode error
            raise KeyRetrievalError(
                "Ошибка разбора ответа сервера ключей."
            )


def reset_api_key_cache():
    """
    Reset the cached OpenAI API key.
    
    Call this if you need to force a fresh key retrieval,
    for example after a key rotation.
    """
    global _openai_api_key_cache, _openai_api_key_cache_time
    with _openai_api_key_lock:
        _openai_api_key_cache = None
        _openai_api_key_cache_time = None


def _get_supabase_client():
    """
    Get or create a thread-safe singleton Supabase client.
    
    Performance optimization: Reuses connection instead of creating new client
    for each credit check/deduction, reducing network overhead significantly.
    
    Returns:
        Supabase client instance
    """
    global _supabase_client
    with _supabase_lock:
        if _supabase_client is None:
            from supabase import create_client
            _supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)
        return _supabase_client


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
        # Get current user's license key and email from session
        license_key = get_license_key()
        email = get_user_email()
        
        if not license_key or not email:
            return {
                'has_credits': False,
                'credits': 0,
                'message': 'No active license session. Please log in.'
            }
        
        # Use singleton Supabase client for better performance
        supabase = _get_supabase_client()
        
        # Query for license credits
        response = supabase.table("licenses").select("credits").eq("license_key", license_key).eq("email", email).execute()
        
        if not response.data or len(response.data) == 0:
            # Mask sensitive values for security
            masked_key = '***' + license_key[-4:] if license_key and len(license_key) >= 4 else license_key
            masked_email = email[:3] + '***' + email[email.find('@'):] if email and '@' in email else email
            return {
                'has_credits': False,
                'credits': 0,
                'message': f"License not found in DB.\nSearched Key: '{masked_key}'\nSearched Email: '{masked_email}'"
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


def deduct_credit(amount: int = 1) -> bool:
    """
    Deduct credits from the user's account after a successful generation.
    
    Note: This implementation uses a check-then-update pattern which has a potential
    race condition between SELECT and UPDATE. For high-concurrency scenarios,
    a database-level RPC function with `SET credits = credits - amount` would be
    more appropriate. However, changing the Supabase schema is out of scope.
    In practice, the single-user desktop app nature of CourseSmith mitigates this risk.
    
    Args:
        amount: Number of credits to deduct (default: 1).
                Based on product type:
                - Mini Course / Lead Magnet / Checklist: 1 credit
                - Paid Guide / 30-Day Challenge: 2 credits
                - Full Course: 3 credits
    
    Returns:
        bool: True if credits were successfully deducted, False otherwise.
    """
    try:
        license_key = get_license_key()
        email = get_user_email()
        
        if not license_key or not email:
            print("Credit deduction failed: No license key or email in session")
            return False
        
        # Use singleton Supabase client for better performance
        supabase = _get_supabase_client()
        
        # Check if user has sufficient credits
        response = supabase.table("licenses").select("credits").eq("license_key", license_key).eq("email", email).gte("credits", amount).execute()
        
        if not response.data or len(response.data) == 0:
            print(f"Credit deduction failed: Insufficient credits (need {amount}) or license not found")
            return False
        
        current_credits = response.data[0].get('credits', 0)
        
        # Deduct credits
        # Note: For true atomicity in high-concurrency scenarios, use database RPC
        new_credits = max(0, current_credits - amount)
        supabase.table("licenses").update({"credits": new_credits}).eq("license_key", license_key).eq("email", email).execute()
        
        print(f"Credits deducted successfully: {current_credits} -> {new_credits} (deducted {amount})")
        return True
        
    except Exception as e:
        print(f"Credit deduction error: {str(e)}")
        return False


def get_credit_cost_for_product(product_type: str) -> int:
    """
    Get the credit cost for a product type.
    
    Args:
        product_type: The product template ID.
        
    Returns:
        int: Number of credits required.
    """
    try:
        from product_templates import get_credit_cost
        return get_credit_cost(product_type)
    except ImportError:
        # Fallback costs if templates not available
        costs = {
            'mini_course': 1,
            'lead_magnet': 1,
            'checklist': 1,
            'paid_guide': 2,
            '30_day_challenge': 2,
            'full_course': 3
        }
        return costs.get(product_type, 1)


def check_credits_for_product(product_type: str) -> dict:
    """
    Check if user has enough credits for a product type.
    
    Args:
        product_type: The product template ID.
        
    Returns:
        dict: {
            'has_credits': bool,
            'credits_needed': int,
            'credits_available': int,
            'message': str
        }
    """
    credit_status = check_remaining_credits()
    credits_needed = get_credit_cost_for_product(product_type)
    credits_available = credit_status.get('credits', 0)
    
    has_enough = credits_available >= credits_needed
    
    if has_enough:
        message = f"Ready to generate. This will use {credits_needed} credit(s). You have {credits_available} available."
    else:
        message = f"Insufficient credits. Need {credits_needed}, have {credits_available}."
    
    return {
        'has_credits': has_enough,
        'credits_needed': credits_needed,
        'credits_available': credits_available,
        'message': message
    }


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
        
        Fetches the API key from Supabase Edge Function before each
        generation cycle for enhanced security.
        
        Returns:
            OpenAI: The OpenAI client instance.
            
        Raises:
            ValueError: If API key cannot be retrieved or no credits remaining.
            KeyRetrievalError: If key retrieval from Edge Function fails.
            SecurityError: If no valid session exists.
        """
        # SECURITY CHECK: Require valid session
        cls._check_session()
        
        # CHECK CREDITS: Ensure user has remaining credits
        cls._check_credits()
        
        with cls._client_lock:
            if cls._client is None:
                # Fetch API key from Supabase Edge Function
                try:
                    api_key = fetch_openai_api_key()
                except KeyRetrievalError as e:
                    raise ValueError(str(e))
                
                cls._client = OpenAI(api_key=api_key)
            return cls._client
    
    @classmethod
    def reset_client(cls):
        """Reset the OpenAI client and API key cache."""
        with cls._client_lock:
            cls._client = None
        reset_api_key_cache()


class OutlineGenerator(AIWorkerBase):
    """Worker for generating course outlines using GPT-4o."""
    
    def __init__(self, topic, audience, callback=None, error_callback=None, 
                 product_type='full_course'):
        """
        Initialize the outline generator.
        
        Args:
            topic: The course topic.
            audience: The target audience.
            callback: Function to call with results (list of chapter titles).
            error_callback: Function to call on error (receives error message).
            product_type: Template ID for generation settings.
        """
        self.topic = topic
        self.audience = audience
        self.callback = callback
        self.error_callback = error_callback
        self.product_type = product_type
        self.thread = None
        self.result = None
        self.error = None
    
    def _get_template_config(self):
        """Get template configuration for the product type."""
        try:
            from product_templates import get_template, FULL_COURSE
            template = get_template(self.product_type)
            return template if template else FULL_COURSE
        except ImportError:
            return None
    
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
            
            # Get template configuration
            template = self._get_template_config()
            
            # Build the prompt based on language and template
            if template:
                chapter_count = template.chapter_count
                if is_russian:
                    system_content = template.structure_prompt_ru
                else:
                    system_content = template.structure_prompt_en
            else:
                chapter_count = 10
                if is_russian:
                    system_content = "Вы эксперт по разработке учебных программ, который создает хорошо структурированный образовательный контент."
                else:
                    system_content = "You are an AI Content Architect who creates well-structured educational content."
            
            # Build the prompt based on language
            if is_russian:
                prompt = f"""Создайте оглавление для контента на тему "{self.topic}" 
для аудитории: {self.audience}.

Предоставьте ровно {chapter_count} названий глав/разделов, которые последовательно развивают знания от основ до продвинутых концепций.

Форматируйте ответ как простой нумерованный список только с названиями:
1. [Название первой главы]
2. [Название второй главы]
...и так далее.

Названия должны быть профессиональными и привлекательными. Предоставьте только названия, ничего больше."""
            else:
                prompt = f"""Create a table of contents for content about "{self.topic}" 
targeted at {self.audience}.

Provide exactly {chapter_count} chapter/section titles that progressively build knowledge from basics to advanced concepts.

Format your response as a simple numbered list with just the titles:
1. [Title of Chapter 1]
2. [Title of Chapter 2]
...and so on.

The titles must be professional and catchy. Ensure the structure is logical and flows well. Only provide the titles, nothing else."""

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
            
            # Ensure we have the expected number of chapters based on template
            min_chapters = chapter_count
            if len(chapters) < min_chapters:
                # Fill with generic titles if needed
                if is_russian:
                    generic = [
                        f"Введение в {self.topic}",
                        f"Основные концепции {self.topic}",
                        f"Практические применения",
                        f"Продвинутые техники",
                        f"Заключение и следующие шаги",
                    ]
                    for i in range(6, 32):
                        generic.append(f"Дополнительная тема {i}")
                else:
                    generic = [
                        f"Introduction to {self.topic}",
                        f"Core Concepts of {self.topic}",
                        f"Practical Applications",
                        f"Advanced Techniques",
                        f"Conclusion and Next Steps",
                    ]
                    for i in range(6, 32):
                        generic.append(f"Additional Topic {i}")
                while len(chapters) < min_chapters:
                    chapters.append(generic[len(chapters) % len(generic)])
            
            # Return exact chapter count based on template
            max_chapters = chapter_count + 2  # Allow slight variance
            if len(chapters) > max_chapters:
                self.result = chapters[:chapter_count]
            else:
                self.result = chapters[:chapter_count] if len(chapters) >= chapter_count else chapters
            
            if self.callback:
                self.callback(self.result)
                
        except Exception as e:
            self.error = str(e)
            if self.error_callback:
                self.error_callback(self.error)


class ChapterWriter(AIWorkerBase):
    """Worker for generating chapter content using GPT-4o with streaming support."""
    
    def __init__(self, topic, chapter_title, chapter_num, callback=None, error_callback=None,
                 stream_callback=None, product_type='full_course'):
        """
        Initialize the chapter writer.
        
        Args:
            topic: The course topic.
            chapter_title: The title of the chapter to write.
            chapter_num: The chapter number.
            callback: Function to call with results (chapter_title, content).
            error_callback: Function to call on error (receives error message).
            stream_callback: Function to call with incremental text chunks for live preview.
            product_type: Template ID for generation settings.
        """
        self.topic = topic
        self.chapter_title = chapter_title
        self.chapter_num = chapter_num
        self.callback = callback
        self.error_callback = error_callback
        self.stream_callback = stream_callback
        self.product_type = product_type
        self.thread = None
        self.result = None
        self.error = None
    
    def _get_template_config(self):
        """Get template configuration for the product type."""
        try:
            from product_templates import get_template, FULL_COURSE
            template = get_template(self.product_type)
            return template if template else FULL_COURSE
        except ImportError:
            return None
    
    def start(self):
        """Start the worker thread."""
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()
    
    def _run(self):
        """Execute the chapter content generation with streaming support."""
        try:
            client = self.get_client()
            
            # Get template configuration
            template = self._get_template_config()
            
            # Detect if input is in Russian
            is_russian = bool(re.search(r'[а-яА-ЯёЁ]', self.topic + ' ' + self.chapter_title))
            
            # Build prompt based on template
            if template:
                chars_per_chapter = template.chars_per_chapter
                if is_russian:
                    system_content = template.content_prompt_ru
                else:
                    system_content = template.content_prompt_en
            else:
                chars_per_chapter = 1500
                if is_russian:
                    system_content = "Вы эксперт-преподаватель, который создает четкий, увлекательный и качественный образовательный контент."
                else:
                    system_content = "You are an expert educator who writes clear, engaging, and comprehensive educational content."
            
            # Calculate approximate word count
            word_count = chars_per_chapter // 5  # ~5 chars per word
            
            if is_russian:
                prompt = f"""Напишите образовательный контент для Раздела {self.chapter_num}: "{self.chapter_title}" 
по теме "{self.topic}".

Требования:
- Целевой объем: примерно {chars_per_chapter} символов ({word_count} слов)
- Используйте ясный, образовательный язык
- Включите практические примеры и объяснения где уместно
- Структурируйте контент логически с четкими абзацами
- Можете использовать markdown заголовки (## для подразделов)
- Сделайте контент увлекательным и информативным
- НЕ включайте название главы в начале - только контент

Напишите контент напрямую."""
            else:
                prompt = f"""Write educational content for Section {self.chapter_num}: "{self.chapter_title}" 
about "{self.topic}".

Requirements:
- Target length: approximately {chars_per_chapter} characters ({word_count} words)
- Use clear, educational language suitable for learners
- Include practical examples and explanations where appropriate
- Structure the content logically with clear paragraphs
- You may use markdown headers (## for subsections) to organize content
- Make it engaging and informative
- Do not include the chapter title at the start, just the content

Write the content directly."""

            # Calculate appropriate max_tokens based on template
            max_tokens = max(500, (chars_per_chapter * 2) // 4)  # Rough estimate
            
            # Check if streaming is requested
            if self.stream_callback:
                # Use streaming API for live preview
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
                    max_tokens=max_tokens,
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
                            "content": system_content
                        },
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7,
                    max_tokens=max_tokens
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
