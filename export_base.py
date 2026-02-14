"""
Export Base Module - Abstract base class for document exporters.
Provides common functionality for exporting CourseSmith content to various formats.

Supported formats:
- PDF (existing pdf_engine.py)
- DOCX (docx_exporter.py)
- Markdown (markdown_exporter.py)
- HTML (html_exporter.py)
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
import os
from datetime import datetime


class ExporterBase(ABC):
    """
    Abstract base class for all document exporters.
    
    Provides common interface and shared functionality for exporting
    course content to different file formats.
    """
    
    # File extension for this exporter
    file_extension: str = ""
    
    # Display name for this format
    format_name: str = ""
    
    def __init__(self, project, output_path: str = None):
        """
        Initialize the exporter with a project.
        
        Args:
            project: CourseProject object with content to export.
            output_path: Optional output file path. If None, will be generated.
        """
        self.project = project
        self.output_path = output_path
        self.errors: List[str] = []
        
    @abstractmethod
    def export(self) -> str:
        """
        Export the project to the target format.
        
        Returns:
            str: Path to the exported file.
            
        Raises:
            ExportError: If export fails.
        """
        pass
    
    def validate_project(self) -> bool:
        """
        Validate that the project has required content for export.
        
        Returns:
            bool: True if project is valid for export.
        """
        if not self.project:
            self.errors.append("No project provided")
            return False
            
        if not self.project.topic:
            self.errors.append("Project has no topic")
            return False
            
        if not self.project.outline:
            self.errors.append("Project has no outline")
            return False
            
        if not self.project.chapters_content:
            self.errors.append("Project has no chapter content")
            return False
            
        return True
    
    def generate_output_path(self, directory: str = None) -> str:
        """
        Generate an output file path based on project topic.
        
        Args:
            directory: Optional directory path. Defaults to current directory.
            
        Returns:
            str: Generated file path.
        """
        if self.output_path:
            return self.output_path
            
        # Sanitize topic for filename
        safe_topic = self._sanitize_filename(self.project.topic)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{safe_topic}_{timestamp}.{self.file_extension}"
        
        if directory:
            return os.path.join(directory, filename)
        return filename
    
    def _sanitize_filename(self, name: str) -> str:
        """
        Sanitize a string for use as a filename.
        
        Args:
            name: The string to sanitize.
            
        Returns:
            str: Sanitized filename-safe string.
        """
        # Remove/replace invalid characters
        invalid_chars = '<>:"/\\|?*'
        result = name
        for char in invalid_chars:
            result = result.replace(char, '_')
        
        # Limit length
        result = result[:50]
        
        # Remove leading/trailing whitespace and dots
        result = result.strip('. ')
        
        return result if result else "course"
    
    def get_formatted_content(self) -> Dict[str, str]:
        """
        Get chapter content formatted for export.
        
        Returns:
            dict: Dictionary mapping chapter titles to formatted content.
        """
        return dict(self.project.chapters_content)
    
    def get_metadata(self) -> Dict[str, Any]:
        """
        Get project metadata for export.
        
        Returns:
            dict: Metadata including title, author, dates, etc.
        """
        return {
            'title': self.project.topic,
            'audience': self.project.audience,
            'author': self.project.branding.get('author_name', ''),
            'company': self.project.branding.get('company_name', ''),
            'created_at': self.project.created_at,
            'modified_at': self.project.modified_at,
            'chapter_count': len(self.project.outline),
            'product_type': getattr(self.project, 'product_type', 'full_course'),
        }


class ExportError(Exception):
    """Exception raised when export fails."""
    pass


class ExportManager:
    """
    Manager for handling multi-format exports.
    
    Coordinates exporting a project to multiple formats
    and manages the export process.
    """
    
    _exporters: Dict[str, type] = {}
    
    @classmethod
    def register_exporter(cls, format_id: str, exporter_class: type) -> None:
        """
        Register an exporter class for a format.
        
        Args:
            format_id: Unique identifier for the format (e.g., 'pdf', 'docx').
            exporter_class: The exporter class to register.
        """
        cls._exporters[format_id] = exporter_class
    
    @classmethod
    def get_exporter(cls, format_id: str) -> Optional[type]:
        """
        Get the exporter class for a format.
        
        Args:
            format_id: The format identifier.
            
        Returns:
            The exporter class or None if not registered.
        """
        return cls._exporters.get(format_id)
    
    @classmethod
    def get_available_formats(cls) -> List[str]:
        """
        Get list of available export formats.
        
        Returns:
            List of format identifiers.
        """
        return list(cls._exporters.keys())
    
    @classmethod
    def export_to_formats(cls, project, formats: List[str], 
                         output_dir: str = None,
                         progress_callback=None) -> Dict[str, str]:
        """
        Export a project to multiple formats.
        
        Args:
            project: CourseProject object to export.
            formats: List of format identifiers to export to.
            output_dir: Optional output directory.
            progress_callback: Optional callback(format, status, path) for progress.
            
        Returns:
            dict: Mapping of format_id to output file path.
            
        Raises:
            ExportError: If any export fails.
        """
        results = {}
        errors = []
        
        for i, format_id in enumerate(formats):
            exporter_class = cls.get_exporter(format_id)
            
            if not exporter_class:
                errors.append(f"Unknown format: {format_id}")
                continue
            
            try:
                if progress_callback:
                    progress_callback(format_id, 'starting', None)
                
                # Create exporter instance
                exporter = exporter_class(project)
                output_path = exporter.generate_output_path(output_dir)
                exporter.output_path = output_path
                
                # Export
                result_path = exporter.export()
                results[format_id] = result_path
                
                if progress_callback:
                    progress_callback(format_id, 'complete', result_path)
                    
            except Exception as e:
                errors.append(f"{format_id}: {str(e)}")
                if progress_callback:
                    progress_callback(format_id, 'error', str(e))
        
        if errors and not results:
            raise ExportError("All exports failed: " + "; ".join(errors))
        
        return results


def get_export_formats_for_ui() -> List[Dict]:
    """
    Get export format information for UI display.
    
    Returns:
        List of dicts with format info.
    """
    formats = [
        {
            'id': 'pdf',
            'name': 'PDF',
            'description': 'Professional PDF document',
            'icon': '📄',
            'extension': '.pdf'
        },
        {
            'id': 'docx',
            'name': 'DOCX',
            'description': 'Microsoft Word document',
            'icon': '📝',
            'extension': '.docx'
        },
        {
            'id': 'markdown',
            'name': 'Markdown',
            'description': 'Markdown text file',
            'icon': '📋',
            'extension': '.md'
        },
        {
            'id': 'html',
            'name': 'HTML',
            'description': 'Web page document',
            'icon': '🌐',
            'extension': '.html'
        }
    ]
    return formats
