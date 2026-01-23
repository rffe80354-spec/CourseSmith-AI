"""
Project Manager Module - Data Model for CourseSmith ENTERPRISE.
Handles project state persistence with JSON serialization.
"""

import json
import os
import re
from datetime import datetime


class CourseProject:
    """
    Data model for a CourseSmith project.
    
    Stores all project data including topic, audience, outline,
    chapter content, and branding information.
    """
    
    def __init__(self):
        """Initialize an empty project."""
        self.topic = ""
        self.audience = ""
        self.outline = []  # List of chapter titles
        self.chapters_content = {}  # Dict mapping chapter title to content
        self.branding = {
            "logo_path": "",
            "website_url": "",
            "author_name": "",
            "company_name": ""
        }
        self.created_at = datetime.now().isoformat()
        self.modified_at = datetime.now().isoformat()
        self.cover_image_path = ""
        self.output_pdf_path = ""
    
    def set_topic(self, topic):
        """Set the course topic."""
        self.topic = topic.strip()
        self._update_modified()
    
    def set_audience(self, audience):
        """Set the target audience."""
        self.audience = audience.strip()
        self._update_modified()
    
    def set_outline(self, outline):
        """
        Set the course outline.
        
        Args:
            outline: List of chapter title strings.
        """
        if isinstance(outline, list):
            self.outline = [str(item).strip() for item in outline if item]
        else:
            # Parse from string (newline separated)
            self.outline = [line.strip() for line in str(outline).split('\n') if line.strip()]
        self._update_modified()
    
    def set_chapter_content(self, chapter_title, content):
        """
        Set content for a specific chapter.
        
        Args:
            chapter_title: The chapter title.
            content: The chapter content text.
        """
        self.chapters_content[chapter_title] = content
        self._update_modified()
    
    def set_branding(self, logo_path="", website_url="", author_name="", company_name=""):
        """
        Set branding information.
        
        Args:
            logo_path: Path to logo image file.
            website_url: Company website URL.
            author_name: Author name for credits.
            company_name: Company name for credits.
        """
        self.branding = {
            "logo_path": logo_path.strip() if logo_path else "",
            "website_url": website_url.strip() if website_url else "",
            "author_name": author_name.strip() if author_name else "",
            "company_name": company_name.strip() if company_name else ""
        }
        self._update_modified()
    
    def set_cover_image(self, path):
        """Set the cover image path."""
        self.cover_image_path = path
        self._update_modified()
    
    def get_outline_text(self):
        """
        Get outline as newline-separated text.
        
        Returns:
            str: Outline with numbered chapters.
        """
        lines = []
        for i, title in enumerate(self.outline, 1):
            lines.append(f"{i}. {title}")
        return '\n'.join(lines)
    
    def parse_outline_text(self, text):
        """
        Parse outline from user-edited text.
        
        Args:
            text: Text with chapter titles (one per line, may have numbers).
            
        Returns:
            list: List of cleaned chapter titles.
        """
        lines = text.strip().split('\n')
        chapters = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Remove common numbering formats
            # "1. Title", "1) Title", "1: Title", "Chapter 1: Title"
            # Remove leading numbers with punctuation
            cleaned = re.sub(r'^(\d+[\.\)\:\-]\s*)', '', line)
            # Remove "Chapter X:" prefix
            cleaned = re.sub(r'^(Chapter\s+\d+[\:\-]?\s*)', '', cleaned, flags=re.IGNORECASE)
            cleaned = cleaned.strip()
            
            if cleaned:
                chapters.append(cleaned)
        
        return chapters
    
    def is_complete(self):
        """
        Check if the project has all required content.
        
        Returns:
            bool: True if project is ready for PDF export.
        """
        return (
            bool(self.topic) and
            bool(self.audience) and
            len(self.outline) > 0 and
            len(self.chapters_content) == len(self.outline)
        )
    
    def _update_modified(self):
        """Update the modified timestamp."""
        self.modified_at = datetime.now().isoformat()
    
    def to_dict(self):
        """
        Convert project to dictionary for serialization.
        
        Returns:
            dict: Project data as dictionary.
        """
        return {
            "topic": self.topic,
            "audience": self.audience,
            "outline": self.outline,
            "chapters_content": self.chapters_content,
            "branding": self.branding,
            "created_at": self.created_at,
            "modified_at": self.modified_at,
            "cover_image_path": self.cover_image_path,
            "output_pdf_path": self.output_pdf_path
        }
    
    @classmethod
    def from_dict(cls, data):
        """
        Create project from dictionary.
        
        Args:
            data: Dictionary with project data.
            
        Returns:
            CourseProject: New project instance.
        """
        project = cls()
        project.topic = data.get("topic", "")
        project.audience = data.get("audience", "")
        project.outline = data.get("outline", [])
        project.chapters_content = data.get("chapters_content", {})
        project.branding = data.get("branding", project.branding)
        project.created_at = data.get("created_at", project.created_at)
        project.modified_at = data.get("modified_at", project.modified_at)
        project.cover_image_path = data.get("cover_image_path", "")
        project.output_pdf_path = data.get("output_pdf_path", "")
        return project
    
    def save_to_json(self, filepath):
        """
        Save project to JSON file.
        
        Args:
            filepath: Path to save the JSON file.
            
        Returns:
            bool: True if saved successfully.
        """
        try:
            self._update_modified()
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)
            return True
        except (IOError, OSError) as e:
            print(f"Failed to save project: {e}")
            return False
    
    @classmethod
    def load_from_json(cls, filepath):
        """
        Load project from JSON file.
        
        Args:
            filepath: Path to the JSON file.
            
        Returns:
            CourseProject: Loaded project or None if failed.
        """
        try:
            if not os.path.exists(filepath):
                return None
            
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            return cls.from_dict(data)
        except (IOError, OSError, json.JSONDecodeError) as e:
            print(f"Failed to load project: {e}")
            return None
