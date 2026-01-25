"""
PDF Engine Module - Professional PDF creation for Faleovad AI Enterprise.
Uses ReportLab's Platypus engine for complex layout with headers/footers.
SECURITY: Requires valid session token to function (anti-tamper protection).
TIER CHECK: Standard licenses cannot use custom branding (logo/website).
PAGINATION: Implements smart content distribution with tier-based page limits.
"""

import os
import re
import tempfile
import shutil
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, mm
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
from session_manager import is_active, get_tier, SecurityError
from generator import ContentDistributor, distribute_chapter_content


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

    def __init__(self, filename, tier=None):
        """
        Initialize the PDF builder with document settings.

        Args:
            filename: The output PDF filename.
            tier: License tier for pagination limits (if None, fetched from session).
        """
        self.filename = filename
        self.page_width, self.page_height = letter
        self.margin = 20 * mm  # 20mm margins on all sides as per spec
        self.logo_path = None
        self.website_url = ""
        self.tier = tier if tier is not None else (get_tier() or 'trial')
        self.distributor = None  # Will be created when needed
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
        generated_note = "Generated by Faleovad AI Enterprise"
        story.append(Paragraph(generated_note, self.styles["Footer"]))

        # Page break after cover
        story.append(PageBreak())
    
    def _create_metadata_page(self, project, story):
        """
        Create a metadata page with generation information.
        
        Args:
            project: CourseProject object with project data.
            story: The story list to append elements to.
        """
        # Add spacer at top
        story.append(Spacer(1, 0.5 * inch))
        
        # Metadata header
        metadata_title = "Document Information"
        story.append(Paragraph(metadata_title, self.styles["ChapterHeader"]))
        story.append(Spacer(1, 0.3 * inch))
        
        # Calculate total pages
        if not self.distributor:
            self.distributor = ContentDistributor(self.tier)
        
        total_pages = 0
        if project.chapters_content:
            distributed_content = distribute_chapter_content(
                project.chapters_content, 
                tier=self.tier
            )
            for chapter_pages in distributed_content.values():
                total_pages += len(chapter_pages)
        
        # Check for custom images
        has_media = False
        media_status = "No custom media included"
        if hasattr(project, 'ui_settings') and project.ui_settings:
            custom_images = project.ui_settings.get('custom_images', [])
            if custom_images and len(custom_images) > 0:
                has_media = True
                media_status = f"{len(custom_images)} custom image(s) included"
        
        # Get generation date
        from datetime import datetime
        generation_date = datetime.now().strftime("%B %d, %Y at %I:%M %p")
        
        # Create metadata content
        metadata_style = self.styles["Normal"]
        metadata_items = [
            f"<b>Generation Date:</b> {generation_date}",
            f"<b>Total Pages:</b> {total_pages} pages",
            f"<b>Media Status:</b> {media_status}",
            f"<b>License Tier:</b> {self.tier.title()}",
        ]
        
        for item in metadata_items:
            story.append(Paragraph(item, metadata_style))
            story.append(Spacer(1, 0.15 * inch))
        
        # Add separator
        story.append(Spacer(1, 0.5 * inch))
        story.append(Paragraph("─" * 60, metadata_style))
        
        # Page break after metadata
        story.append(PageBreak())

    def _parse_markdown_content_with_style(self, content, body_style):
        """
        Parse markdown content with a specific body text style.
        Allows for per-page font scaling.
        
        Args:
            content: The markdown content string.
            body_style: The paragraph style to use for body text.
            
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
                    elements.append(Paragraph(para_text, body_style))
                    current_para = []
                
                # Add section header
                header_text = stripped[3:].strip()
                elements.append(Paragraph(header_text, self.styles["SectionHeader"]))
                
            elif stripped.startswith('# '):
                # Flush current paragraph
                if current_para:
                    para_text = ' '.join(current_para)
                    elements.append(Paragraph(para_text, body_style))
                    current_para = []
                
                # Add main header (less common in chapter content)
                header_text = stripped[1:].strip()
                elements.append(Paragraph(header_text, self.styles["ChapterHeader"]))
                
            elif stripped == '':
                # Empty line - flush paragraph
                if current_para:
                    para_text = ' '.join(current_para)
                    elements.append(Paragraph(para_text, body_style))
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
            elements.append(Paragraph(para_text, body_style))
        
        return elements

    def _add_chapters(self, project, story):
        """
        Add chapter content to the document with smart pagination.
        Uses generator.py for intelligent content distribution with tier-based limits.

        Args:
            project: CourseProject object with outline and chapter content.
            story: The story list to append elements to.
        """
        # Create distributor if not exists
        if not self.distributor:
            self.distributor = ContentDistributor(self.tier)
        
        # Use smart content distribution
        distributed_content = distribute_chapter_content(
            project.chapters_content, 
            tier=self.tier
        )
        
        # Track total content to ensure we respect page limits
        total_pages_used = 0
        max_pages = self.distributor.max_pages
        
        for i, chapter_title in enumerate(project.outline, 1):
            # Check if we've hit the page limit
            if total_pages_used >= max_pages:
                break
            
            # Chapter header
            header_text = f"Chapter {i}: {chapter_title}"
            story.append(Paragraph(header_text, self.styles["ChapterHeader"]))
            
            # Get distributed pages for this chapter
            chapter_pages = distributed_content.get(chapter_title, [])
            
            if chapter_pages:
                for page_content in chapter_pages:
                    # Check page limit before adding
                    if total_pages_used >= max_pages:
                        break
                    
                    # Parse content with standard style
                    # The distributor already ensures content is <= 1000 chars
                    elements = self._parse_markdown_content_with_style(
                        page_content, 
                        self.styles["CustomBodyText"]
                    )
                    
                    story.extend(elements)
                    total_pages_used += 1
            
            # Page break after each chapter (if not at limit)
            if total_pages_used < max_pages:
                story.append(PageBreak())

    def build_pdf(self, project, output_path=None, tier=None):
        """
        Build the complete PDF document from a project.
        Implements strict page limits and smart content distribution.

        Args:
            project: CourseProject object with all project data.
            output_path: Optional output path (uses self.filename if not provided).
            tier: License tier for pagination (if None, uses session tier).

        Returns:
            str: The path of the generated PDF, or None if unauthorized.
            
        Raises:
            SecurityError: If no valid session token exists.
        """
        # SECURITY CHECK: Require valid session
        if not is_active():
            raise SecurityError("Unauthorized: No valid session. Please activate your license.")
        
        if output_path:
            self.filename = output_path
        
        # Update tier if provided and recreate distributor
        if tier:
            self.tier = tier
            self.distributor = ContentDistributor(tier)
        elif not self.distributor:
            self.distributor = ContentDistributor(self.tier)
        
        # Get branding options from project
        branding = project.branding
        
        # TIER CHECK: Standard licenses cannot use custom branding
        current_tier = self.tier
        if current_tier == 'standard':
            # Force branding to empty for Standard tier
            self.logo_path = ""
            self.website_url = ""
        else:
            # Extended tier gets full branding support
            self.logo_path = branding.get("logo_path", "")
            self.website_url = branding.get("website_url", "")
        
        # Get target page count from project settings (legacy support)
        target_page_count = None
        if hasattr(project, 'ui_settings') and project.ui_settings:
            target_page_count = project.ui_settings.get('target_page_count')
        
        # Use tier-based limits or legacy target page count
        if target_page_count:
            return self._build_pdf_with_page_limit(project, target_page_count)
        else:
            # Standard build with tier-based pagination
            return self._build_pdf_standard(project)
    
    def _build_pdf_standard(self, project):
        """
        Build PDF without page limit enforcement (standard behavior).
        
        Args:
            project: CourseProject object with all project data.
            
        Returns:
            str: The path of the generated PDF.
        """
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
        
        # Add metadata page after cover
        self._create_metadata_page(project, story)
        
        # Switch to content template for remaining pages
        story.insert(-1, NextPageTemplate('content'))
        
        # Add chapters
        self._add_chapters(project, story)
        
        # Build the document
        doc.build(story)
        
        return self.filename
    
    def _build_pdf_with_page_limit(self, project, target_page_count):
        """
        Build PDF with strict page limit using Shrink-to-Fit algorithm.
        If content exceeds target pages, recursively reduces font sizes to fit.
        
        Args:
            project: CourseProject object with all project data.
            target_page_count: Maximum number of pages allowed.
            
        Returns:
            str: The path of the generated PDF.
        """
        # Start with default font scale (1.0 = 100%)
        font_scale = 1.0
        min_font_scale = 0.5  # Don't shrink below 50% of original size
        max_iterations = 10  # Prevent infinite loops
        
        for iteration in range(max_iterations):
            # Apply current font scale to styles
            self._apply_font_scale(font_scale)
            
            # Build to temporary file to count pages
            temp_fd, temp_path = tempfile.mkstemp(suffix='.pdf')
            os.close(temp_fd)
            
            try:
                # Create document
                doc = BaseDocTemplate(
                    temp_path,
                    pagesize=letter,
                    rightMargin=self.margin,
                    leftMargin=self.margin,
                    topMargin=self.margin + 0.3 * inch,
                    bottomMargin=self.margin + 0.3 * inch,
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
                
                # Create cover page
                self._create_cover_page(project, story)
                
                # Add metadata page after cover
                self._create_metadata_page(project, story)
                
                # Switch to content template for remaining pages
                story.insert(-1, NextPageTemplate('content'))
                
                # Add chapters
                self._add_chapters(project, story)
                
                # Build the document
                doc.build(story)
                
                # Count pages in the generated PDF
                actual_page_count = doc.page
                
                # Check if we fit within target
                if actual_page_count <= target_page_count:
                    # Success! Copy temp file to final destination
                    shutil.copy2(temp_path, self.filename)
                    os.unlink(temp_path)
                    print(f"PDF Shrink-to-Fit: Success at {font_scale*100:.0f}% font scale ({actual_page_count}/{target_page_count} pages)")
                    return self.filename
                
                # Need to shrink more
                # Calculate overage ratio and reduce font scale
                overage_ratio = actual_page_count / target_page_count
                # Reduce font scale proportionally (conservative estimate)
                new_font_scale = font_scale / (overage_ratio ** 0.5)
                
                # Don't go below minimum
                if new_font_scale < min_font_scale:
                    new_font_scale = min_font_scale
                
                # If we're already at minimum and still over, we're done
                if font_scale <= min_font_scale:
                    print(f"PDF Shrink-to-Fit: Warning - Cannot fit content in {target_page_count} pages even at minimum font size. Generated {actual_page_count} pages.")
                    # Use the best attempt we have
                    shutil.copy2(temp_path, self.filename)
                    os.unlink(temp_path)
                    return self.filename
                
                print(f"PDF Shrink-to-Fit: Iteration {iteration+1} - {actual_page_count} pages (target: {target_page_count}), reducing font scale to {new_font_scale*100:.0f}%")
                font_scale = new_font_scale
                
                # Clean up temp file
                os.unlink(temp_path)
                
            except Exception as e:
                # Clean up temp file on error
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
                raise e
        
        # Should not reach here, but if we do, build with minimum scale
        print(f"PDF Shrink-to-Fit: Max iterations reached. Building with minimum font scale.")
        self._apply_font_scale(min_font_scale)
        return self._build_pdf_standard(project)
    
    def _apply_font_scale(self, scale):
        """
        Apply font scale factor to all paragraph styles.
        
        Args:
            scale: Font scale factor (1.0 = 100%, 0.5 = 50%, etc.)
        """
        # Store original font sizes if not already stored
        if not hasattr(self, '_original_font_sizes'):
            self._original_font_sizes = {}
            for style_name in ['CoverTitle', 'CoverSubtitle', 'ChapterHeader', 
                              'SectionHeader', 'CustomBodyText', 'Footer']:
                if style_name in self.styles:
                    style = self.styles[style_name]
                    self._original_font_sizes[style_name] = {
                        'fontSize': style.fontSize,
                        'leading': style.leading
                    }
        
        # Apply scale to all styles
        for style_name, original in self._original_font_sizes.items():
            if style_name in self.styles:
                style = self.styles[style_name]
                style.fontSize = original['fontSize'] * scale
                style.leading = original['leading'] * scale


# Legacy function for backward compatibility
def build_pdf_simple(title, audience, cover_image_path, chapters_data, output_path, tier=None):
    """
    Simple PDF builder for backward compatibility.
    
    Args:
        title: Course title.
        audience: Target audience.
        cover_image_path: Path to cover image.
        chapters_data: List of dicts with 'title' and 'content'.
        output_path: Output PDF path.
        tier: License tier for pagination limits.
        
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
    
    builder = PDFBuilder(output_path, tier=tier)
    return builder.build_pdf(project, tier=tier)

