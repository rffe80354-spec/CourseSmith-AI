"""
Markdown Exporter Module - Export CourseSmith content to Markdown format.
Creates clean, well-structured Markdown documents.
"""

import os
from datetime import datetime

from export_base import ExporterBase, ExportError, ExportManager


class MarkdownExporter(ExporterBase):
    """
    Exporter for Markdown format.
    
    Creates clean Markdown documents with:
    - Title and metadata header
    - Table of contents
    - Formatted chapter content
    - Proper markdown structure
    """
    
    file_extension = "md"
    format_name = "Markdown"
    
    def export(self) -> str:
        """
        Export the project to Markdown format.
        
        Returns:
            str: Path to the exported Markdown file.
            
        Raises:
            ExportError: If export fails.
        """
        if not self.validate_project():
            raise ExportError(f"Invalid project: {', '.join(self.errors)}")
        
        try:
            # Build markdown content
            md_content = self._build_markdown()
            
            # Generate output path if needed
            output_path = self.generate_output_path()
            
            # Write to file
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(md_content)
            
            return output_path
            
        except Exception as e:
            raise ExportError(f"Failed to export Markdown: {str(e)}")
    
    def _build_markdown(self) -> str:
        """
        Build the complete Markdown document.
        
        Returns:
            str: Complete Markdown content.
        """
        sections = []
        
        # Title and metadata
        sections.append(self._build_header())
        
        # Table of contents
        sections.append(self._build_toc())
        
        # Chapters
        sections.append(self._build_chapters())
        
        # Footer
        sections.append(self._build_footer())
        
        return '\n\n'.join(sections)
    
    def _build_header(self) -> str:
        """Build the document header with title and metadata."""
        lines = []
        
        # Title
        lines.append(f"# {self.project.topic}")
        lines.append("")
        
        # Subtitle
        lines.append(f"*A Comprehensive Guide for {self.project.audience}*")
        lines.append("")
        
        # Metadata
        lines.append("---")
        lines.append("")
        
        branding = self.project.branding
        if branding.get('author_name'):
            lines.append(f"**Author:** {branding['author_name']}")
        if branding.get('company_name'):
            lines.append(f"**Organization:** {branding['company_name']}")
        
        # Product type if available
        product_type = getattr(self.project, 'product_type', 'full_course')
        product_type_display = product_type.replace('_', ' ').title()
        lines.append(f"**Type:** {product_type_display}")
        
        # Generation date
        lines.append(f"**Generated:** {datetime.now().strftime('%B %d, %Y')}")
        
        lines.append("")
        lines.append("---")
        
        return '\n'.join(lines)
    
    def _build_toc(self) -> str:
        """Build the table of contents."""
        lines = []
        
        lines.append("## Table of Contents")
        lines.append("")
        
        for i, title in enumerate(self.project.outline, 1):
            # Create anchor-friendly slug
            slug = self._create_slug(f"chapter-{i}-{title}")
            lines.append(f"{i}. [{title}](#{slug})")
        
        return '\n'.join(lines)
    
    def _build_chapters(self) -> str:
        """Build all chapter content."""
        chapters = []
        
        for i, chapter_title in enumerate(self.project.outline, 1):
            chapter_md = self._build_chapter(i, chapter_title)
            chapters.append(chapter_md)
        
        return '\n\n---\n\n'.join(chapters)
    
    def _build_chapter(self, chapter_num: int, chapter_title: str) -> str:
        """
        Build a single chapter section.
        
        Args:
            chapter_num: The chapter number.
            chapter_title: The chapter title.
            
        Returns:
            str: Markdown content for the chapter.
        """
        lines = []
        
        # Chapter heading
        lines.append(f"## Chapter {chapter_num}: {chapter_title}")
        lines.append("")
        
        # Chapter content
        content = self.project.chapters_content.get(chapter_title, "")
        
        # Content is already in markdown format, but we may need to adjust heading levels
        # Increase heading levels to fit chapter structure (## becomes ###)
        adjusted_content = self._adjust_heading_levels(content)
        lines.append(adjusted_content)
        
        return '\n'.join(lines)
    
    def _adjust_heading_levels(self, content: str) -> str:
        """
        Adjust heading levels in content to fit chapter structure.
        
        Args:
            content: The markdown content.
            
        Returns:
            str: Content with adjusted heading levels.
        """
        lines = content.split('\n')
        adjusted_lines = []
        
        for line in lines:
            stripped = line.strip()
            
            # ## Section -> ### Section (within chapters)
            if stripped.startswith('## '):
                adjusted_lines.append('### ' + stripped[3:])
            elif stripped.startswith('# '):
                adjusted_lines.append('### ' + stripped[2:])
            else:
                adjusted_lines.append(line)
        
        return '\n'.join(adjusted_lines)
    
    def _build_footer(self) -> str:
        """Build the document footer."""
        lines = []
        
        lines.append("---")
        lines.append("")
        lines.append("*Generated by CourseSmith AI*")
        
        branding = self.project.branding
        if branding.get('website_url'):
            lines.append(f"*{branding['website_url']}*")
        
        return '\n'.join(lines)
    
    def _create_slug(self, text: str) -> str:
        """
        Create a URL-friendly slug from text.
        
        Args:
            text: The text to convert.
            
        Returns:
            str: URL-friendly slug.
        """
        # Convert to lowercase
        slug = text.lower()
        
        # Replace spaces and special chars with hyphens
        import re
        slug = re.sub(r'[^a-z0-9\-]', '-', slug)
        
        # Remove multiple consecutive hyphens
        slug = re.sub(r'-+', '-', slug)
        
        # Remove leading/trailing hyphens
        slug = slug.strip('-')
        
        return slug


# Register the exporter
ExportManager.register_exporter('markdown', MarkdownExporter)
