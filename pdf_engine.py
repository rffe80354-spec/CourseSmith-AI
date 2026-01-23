"""
PDF Engine Module - Professional PDF creation for CourseSmith ENTERPRISE.
Uses ReportLab's Platypus engine for complex layout with headers/footers.
"""

import os
import re
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT
from reportlab.platypus import (
    BaseDocTemplate,
    PageTemplate,
    Frame,
    Paragraph,
    Spacer,
    Image,
    PageBreak,
    NextPageTemplate,
)
from reportlab.lib.colors import HexColor, Color
from reportlab.pdfgen import canvas

from utils import resource_path


class PDFBuilder:
    """
    Professional PDF document builder with headers, footers, and branding.
    
    Features:
    - Cover page with image, title, and subtitle
    - Header with optional logo
    - Footer with page numbers and website URL
    - Markdown header support (# and ##)
    - Clean typography using Helvetica
    """

    def __init__(self, filename):
        """
        Initialize the PDF builder with document settings.

        Args:
            filename: The output PDF filename.
        """
        self.filename = filename
        self.page_width, self.page_height = letter
        self.margin = 0.75 * inch
        self.logo_path = None
        self.website_url = ""
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()

    def _setup_custom_styles(self):
        """Setup custom paragraph styles for the document."""
        # Cover title style
        self.styles.add(
            ParagraphStyle(
                name="CoverTitle",
                parent=self.styles["Heading1"],
                fontName="Helvetica-Bold",
                fontSize=36,
                leading=44,
                alignment=TA_CENTER,
                spaceAfter=20,
                textColor=HexColor("#1a1a2e"),
            )
        )

        # Cover subtitle style
        self.styles.add(
            ParagraphStyle(
                name="CoverSubtitle",
                parent=self.styles["Normal"],
                fontName="Helvetica",
                fontSize=18,
                leading=24,
                alignment=TA_CENTER,
                spaceAfter=30,
                textColor=HexColor("#4a4a6a"),
            )
        )

        # Chapter header style (for # headers)
        self.styles.add(
            ParagraphStyle(
                name="ChapterHeader",
                parent=self.styles["Heading1"],
                fontName="Helvetica-Bold",
                fontSize=24,
                leading=30,
                spaceBefore=20,
                spaceAfter=15,
                textColor=HexColor("#1a1a2e"),
            )
        )

        # Section header style (for ## headers)
        self.styles.add(
            ParagraphStyle(
                name="SectionHeader",
                parent=self.styles["Heading2"],
                fontName="Helvetica-Bold",
                fontSize=16,
                leading=20,
                spaceBefore=15,
                spaceAfter=10,
                textColor=HexColor("#2a2a4e"),
            )
        )

        # Body text style
        self.styles.add(
            ParagraphStyle(
                name="CustomBodyText",
                parent=self.styles["Normal"],
                fontName="Helvetica",
                fontSize=11,
                leading=16,
                alignment=TA_JUSTIFY,
                spaceBefore=4,
                spaceAfter=10,
            )
        )

        # Footer style
        self.styles.add(
            ParagraphStyle(
                name="Footer",
                parent=self.styles["Normal"],
                fontName="Helvetica",
                fontSize=9,
                leading=11,
                alignment=TA_CENTER,
                textColor=HexColor("#666666"),
            )
        )

    def _header_footer(self, canvas_obj, doc):
        """
        Draw header and footer on each page.
        
        Args:
            canvas_obj: The canvas object for drawing.
            doc: The document object.
        """
        canvas_obj.saveState()
        
        # Draw header with logo if available
        if self.logo_path and os.path.exists(self.logo_path):
            valid_extensions = ('.png', '.jpg', '.jpeg', '.gif', '.bmp')
            if self.logo_path.lower().endswith(valid_extensions):
                try:
                    # Draw small logo in top-left corner
                    logo_height = 0.4 * inch
                    canvas_obj.drawImage(
                        self.logo_path,
                        self.margin,
                        self.page_height - self.margin + 0.1 * inch,
                        height=logo_height,
                        preserveAspectRatio=True,
                        mask='auto'
                    )
                except Exception:
                    pass  # Skip logo if it can't be loaded
        
        # Draw footer
        footer_y = 0.4 * inch
        
        # Page number on right
        page_num = f"Page {doc.page}"
        canvas_obj.setFont("Helvetica", 9)
        canvas_obj.setFillColor(HexColor("#666666"))
        canvas_obj.drawRightString(
            self.page_width - self.margin,
            footer_y,
            page_num
        )
        
        # Website URL on left (if provided)
        if self.website_url:
            canvas_obj.drawString(
                self.margin,
                footer_y,
                self.website_url
            )
        
        # Horizontal line above footer
        canvas_obj.setStrokeColor(HexColor("#cccccc"))
        canvas_obj.setLineWidth(0.5)
        canvas_obj.line(
            self.margin,
            footer_y + 0.15 * inch,
            self.page_width - self.margin,
            footer_y + 0.15 * inch
        )
        
        canvas_obj.restoreState()

    def _create_cover_page(self, project, story):
        """
        Create the cover page with image, title, and subtitle.

        Args:
            project: CourseProject object with project data.
            story: The story list to append elements to.
        """
        # Add spacer at top
        story.append(Spacer(1, 1 * inch))

        # Add cover image if it exists and is valid
        cover_image_path = project.cover_image_path
        if cover_image_path and os.path.exists(cover_image_path):
            valid_extensions = ('.png', '.jpg', '.jpeg', '.gif', '.bmp')
            if cover_image_path.lower().endswith(valid_extensions):
                try:
                    # Calculate image dimensions to fit page
                    page_width = self.page_width - (2 * self.margin)
                    img = Image(cover_image_path)

                    # Scale image to fit width while maintaining aspect ratio
                    aspect = img.imageHeight / float(img.imageWidth)
                    img_width = min(page_width, 5 * inch)
                    img_height = img_width * aspect

                    # Limit height if too tall
                    max_height = 4 * inch
                    if img_height > max_height:
                        img_height = max_height
                        img_width = img_height / aspect

                    img.drawWidth = img_width
                    img.drawHeight = img_height
                    img.hAlign = "CENTER"
                    story.append(img)
                    story.append(Spacer(1, 0.5 * inch))
                except Exception:
                    pass  # Skip image if it can't be loaded

        # Add title
        story.append(Paragraph(project.topic, self.styles["CoverTitle"]))

        # Add subtitle with audience
        subtitle = f"A Comprehensive Guide for {project.audience}"
        story.append(Paragraph(subtitle, self.styles["CoverSubtitle"]))

        # Add branding info if available
        story.append(Spacer(1, 1.5 * inch))
        
        branding = project.branding
        if branding.get("author_name"):
            author_text = f"By {branding['author_name']}"
            story.append(Paragraph(author_text, self.styles["CoverSubtitle"]))
        
        if branding.get("company_name"):
            company_text = branding["company_name"]
            story.append(Paragraph(company_text, self.styles["CoverSubtitle"]))

        # Generated by note
        story.append(Spacer(1, 0.5 * inch))
        generated_note = "Generated by CourseSmith ENTERPRISE"
        story.append(Paragraph(generated_note, self.styles["Footer"]))

        # Page break after cover
        story.append(PageBreak())

    def _parse_markdown_content(self, content):
        """
        Parse markdown content and convert to Paragraph objects.
        
        Handles:
        - # for section headers
        - ## for subsection headers
        - Regular paragraphs
        
        Args:
            content: The markdown content string.
            
        Returns:
            list: List of Paragraph/Spacer objects.
        """
        elements = []
        lines = content.split('\n')
        current_para = []
        
        for line in lines:
            stripped = line.strip()
            
            # Check for headers
            if stripped.startswith('## '):
                # Flush current paragraph
                if current_para:
                    para_text = ' '.join(current_para)
                    elements.append(Paragraph(para_text, self.styles["CustomBodyText"]))
                    current_para = []
                
                # Add section header
                header_text = stripped[3:].strip()
                elements.append(Paragraph(header_text, self.styles["SectionHeader"]))
                
            elif stripped.startswith('# '):
                # Flush current paragraph
                if current_para:
                    para_text = ' '.join(current_para)
                    elements.append(Paragraph(para_text, self.styles["CustomBodyText"]))
                    current_para = []
                
                # Add main header (less common in chapter content)
                header_text = stripped[1:].strip()
                elements.append(Paragraph(header_text, self.styles["ChapterHeader"]))
                
            elif stripped == '':
                # Empty line - flush paragraph
                if current_para:
                    para_text = ' '.join(current_para)
                    elements.append(Paragraph(para_text, self.styles["CustomBodyText"]))
                    current_para = []
            else:
                # Regular text - accumulate
                # Handle bold/italic markdown
                processed = stripped
                processed = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', processed)
                processed = re.sub(r'\*(.+?)\*', r'<i>\1</i>', processed)
                current_para.append(processed)
        
        # Flush remaining paragraph
        if current_para:
            para_text = ' '.join(current_para)
            elements.append(Paragraph(para_text, self.styles["CustomBodyText"]))
        
        return elements

    def _add_chapters(self, project, story):
        """
        Add chapter content to the document.

        Args:
            project: CourseProject object with outline and chapter content.
            story: The story list to append elements to.
        """
        for i, chapter_title in enumerate(project.outline, 1):
            # Chapter header
            header_text = f"Chapter {i}: {chapter_title}"
            story.append(Paragraph(header_text, self.styles["ChapterHeader"]))

            # Get chapter content
            content = project.chapters_content.get(chapter_title, "")
            
            if content:
                # Parse and add content with markdown support
                elements = self._parse_markdown_content(content)
                story.extend(elements)
            
            # Page break after each chapter
            story.append(PageBreak())

    def build_pdf(self, project, output_path=None):
        """
        Build the complete PDF document from a project.

        Args:
            project: CourseProject object with all project data.
            output_path: Optional output path (uses self.filename if not provided).

        Returns:
            str: The path of the generated PDF.
        """
        if output_path:
            self.filename = output_path
        
        # Set branding options
        branding = project.branding
        self.logo_path = branding.get("logo_path", "")
        self.website_url = branding.get("website_url", "")
        
        # Create document with custom page template
        doc = BaseDocTemplate(
            self.filename,
            pagesize=letter,
            rightMargin=self.margin,
            leftMargin=self.margin,
            topMargin=self.margin + 0.3 * inch,  # Extra space for header
            bottomMargin=self.margin + 0.3 * inch,  # Extra space for footer
        )
        
        # Define frame for content
        frame = Frame(
            doc.leftMargin,
            doc.bottomMargin,
            doc.width,
            doc.height,
            id='normal'
        )
        
        # Create page template with header/footer
        template = PageTemplate(
            id='content',
            frames=[frame],
            onPage=self._header_footer
        )
        
        # Cover page template (no header/footer)
        cover_frame = Frame(
            doc.leftMargin,
            doc.bottomMargin,
            doc.width,
            doc.height,
            id='cover'
        )
        cover_template = PageTemplate(id='cover', frames=[cover_frame])
        
        doc.addPageTemplates([cover_template, template])
        
        # Build story
        story = []
        
        # Create cover page (uses cover template automatically for first page)
        self._create_cover_page(project, story)
        
        # Switch to content template for remaining pages
        story.insert(-1, NextPageTemplate('content'))
        
        # Add chapters
        self._add_chapters(project, story)
        
        # Build the document
        doc.build(story)
        
        return self.filename


# Legacy function for backward compatibility
def build_pdf_simple(title, audience, cover_image_path, chapters_data, output_path):
    """
    Simple PDF builder for backward compatibility.
    
    Args:
        title: Course title.
        audience: Target audience.
        cover_image_path: Path to cover image.
        chapters_data: List of dicts with 'title' and 'content'.
        output_path: Output PDF path.
        
    Returns:
        str: Path to generated PDF.
    """
    from project_manager import CourseProject
    
    project = CourseProject()
    project.topic = title
    project.audience = audience
    project.cover_image_path = cover_image_path or ""
    project.outline = [ch['title'] for ch in chapters_data]
    for ch in chapters_data:
        project.chapters_content[ch['title']] = ch['content']
    
    builder = PDFBuilder(output_path)
    return builder.build_pdf(project)

