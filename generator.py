"""
PDF Content Generator Module - Professional Pagination & Distribution System
Implements smart content splitting and tier-based page limits for CourseSmith AI.

Features:
- Max 1000 characters per page with smart splitting
- Tier-based strict page limits (Trial: 10, Standard: 50, Enterprise: 300)
- Smart text splitting at paragraph/sentence boundaries
- Content truncation when exceeding limits
"""

import re
from session_manager import get_tier, get_max_pages


# Constants
MAX_CHARS_PER_PAGE = 1000


class ContentDistributor:
    """
    Handles intelligent content distribution across pages with strict limits.
    
    Features:
    - Smart splitting at paragraph (\n\n) or sentence (. ) boundaries
    - Respects 1000 character per page limit
    - Enforces tier-based maximum page counts
    - Truncates content at last complete sentence if exceeding limits
    """
    
    def __init__(self, tier=None):
        """
        Initialize the content distributor.
        
        Args:
            tier: License tier ('trial', 'standard', 'enterprise', 'lifetime').
                  If None, will be fetched from session manager.
        """
        self.tier = tier if tier is not None else (get_tier() or 'trial')
        # Use session manager's tier limits for consistency
        self.max_pages = get_max_pages() if tier is None else self._get_max_pages_for_tier(tier)
        self.max_total_chars = self.max_pages * MAX_CHARS_PER_PAGE
    
    def _get_max_pages_for_tier(self, tier):
        """
        Get max pages for a specific tier.
        Fallback method when tier is explicitly provided.
        
        Args:
            tier: License tier string.
            
        Returns:
            int: Maximum pages for the tier.
        """
        tier_limits = {
            'trial': 10,
            'standard': 50,
            'enterprise': 300,
            'lifetime': 300
        }
        return tier_limits.get(tier, 10)
    
    def distribute_content(self, content):
        """
        Distribute content across pages with smart splitting.
        
        Args:
            content: The full content string to distribute.
            
        Returns:
            list: List of content chunks, each <= 1000 chars, respecting page limits.
        """
        if not content:
            return []
        
        # First, check if we need to truncate
        if len(content) > self.max_total_chars:
            content = self._truncate_at_sentence(content, self.max_total_chars)
        
        # Now split into pages using smart splitter
        pages = []
        remaining = content
        
        while remaining and len(pages) < self.max_pages:
            chunk = self._smart_split_chunk(remaining, MAX_CHARS_PER_PAGE)
            if not chunk:
                break
            pages.append(chunk)
            remaining = remaining[len(chunk):].lstrip()
        
        return pages
    
    def _smart_split_chunk(self, text, max_chars):
        """
        Extract a chunk of text up to max_chars, splitting at natural boundaries.
        
        Priority:
        1. Split at paragraph boundary (\n\n) before max_chars
        2. Split at sentence boundary (. ) before max_chars
        3. Split at max_chars as last resort
        
        Args:
            text: The text to split.
            max_chars: Maximum characters for this chunk.
            
        Returns:
            str: The chunk of text.
        """
        if len(text) <= max_chars:
            return text
        
        # Try to find paragraph boundary (\n\n) before max_chars
        search_text = text[:max_chars]
        para_match = None
        
        # Find the last occurrence of \n\n
        for match in re.finditer(r'\n\n', search_text):
            para_match = match
        
        if para_match:
            # Split after the paragraph break
            split_pos = para_match.end()
            return text[:split_pos].rstrip()
        
        # Try to find sentence boundary (. followed by space or \n) before max_chars
        # Look for ". ", ".\n", "! ", "?\n", etc.
        sentence_match = None
        for match in re.finditer(r'[.!?][\s\n]', search_text):
            sentence_match = match
        
        if sentence_match:
            # Split after the sentence end
            split_pos = sentence_match.end()
            return text[:split_pos].rstrip()
        
        # Last resort: split at max_chars at the nearest word boundary
        # Look backwards for a space
        split_pos = max_chars
        for i in range(max_chars - 1, max(0, max_chars - 100), -1):
            if text[i] in ' \n\t':
                split_pos = i
                break
        
        return text[:split_pos].rstrip()
    
    def _truncate_at_sentence(self, text, max_chars):
        """
        Truncate text at the last complete sentence before max_chars.
        
        Args:
            text: The text to truncate.
            max_chars: Maximum characters allowed.
            
        Returns:
            str: Truncated text ending at a sentence boundary.
        """
        if len(text) <= max_chars:
            return text
        
        # Find the last sentence boundary before max_chars
        search_text = text[:max_chars]
        sentence_match = None
        
        for match in re.finditer(r'[.!?][\s\n]', search_text):
            sentence_match = match
        
        if sentence_match:
            # Truncate at the last sentence
            return text[:sentence_match.end()].rstrip()
        
        # If no sentence boundary found, truncate at last word
        for i in range(max_chars - 1, max(0, max_chars - 100), -1):
            if text[i] in ' \n\t':
                return text[:i].rstrip() + '...'
        
        # Last resort: hard truncate
        return text[:max_chars].rstrip() + '...'
    
    def truncate_at_sentence(self, text, max_chars):
        """
        Public method to truncate text at the last complete sentence before max_chars.
        
        Args:
            text: The text to truncate.
            max_chars: Maximum characters allowed.
            
        Returns:
            str: Truncated text ending at a sentence boundary.
        """
        return self._truncate_at_sentence(text, max_chars)
    
    def get_page_info(self):
        """
        Get information about page limits for current tier.
        
        Returns:
            dict: Dictionary with tier, max_pages, and max_total_chars.
        """
        return {
            'tier': self.tier,
            'max_pages': self.max_pages,
            'max_total_chars': self.max_total_chars,
            'chars_per_page': MAX_CHARS_PER_PAGE
        }


def distribute_chapter_content(chapters_dict, tier=None):
    """
    Distribute all chapter content across pages with tier-based limits.
    
    Args:
        chapters_dict: Dictionary mapping chapter titles to content strings.
        tier: License tier (if None, will be fetched from session).
        
    Returns:
        dict: Dictionary mapping chapter titles to lists of page content.
    """
    distributor = ContentDistributor(tier)
    distributed_chapters = {}
    
    total_chars = 0
    for title, content in chapters_dict.items():
        total_chars += len(content)
    
    # If total content exceeds limit, we need to scale down all chapters proportionally
    if total_chars > distributor.max_total_chars:
        # Calculate scaling factor
        scale_factor = distributor.max_total_chars / total_chars
        
        # Truncate each chapter proportionally using public method
        scaled_chapters = {}
        for title, content in chapters_dict.items():
            target_chars = int(len(content) * scale_factor)
            if target_chars > 0:
                scaled_content = distributor.truncate_at_sentence(content, target_chars)
                scaled_chapters[title] = scaled_content
            else:
                scaled_chapters[title] = ""
        
        chapters_dict = scaled_chapters
    
    # Now distribute each chapter into pages
    for title, content in chapters_dict.items():
        pages = distributor.distribute_content(content)
        distributed_chapters[title] = pages
    
    return distributed_chapters


def get_tier_info(tier=None):
    """
    Get tier information for display.
    
    Args:
        tier: License tier (if None, will be fetched from session).
        
    Returns:
        dict: Tier information including limits.
    """
    distributor = ContentDistributor(tier)
    return distributor.get_page_info()
