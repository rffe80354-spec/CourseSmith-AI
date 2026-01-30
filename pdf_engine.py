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

from utils import resource_path, _register_roboto_fonts
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
    - Clean typography using Roboto fonts with Unicode support
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
        self.custom_images = []  # List of custom image paths to embed
        self.styles = getSampleStyleSheet()
        
        # Register Roboto fonts for proper Unicode/Cyrillic support
        self._fonts_available = _register_roboto_fonts()
        self._font_regular = 'Roboto' if self._fonts_available else 'Helvetica'
        self._font_bold = 'Roboto-Bold' if self._fonts_available else 'Helvetica-Bold'
        
        self._setup_custom_styles()

    def _setup_custom_styles(self):
        """Setup custom paragraph styles for the document."""
        # Update base styles to use proper fonts for Unicode support
        self.styles['Normal'].fontName = self._font_regular
        self.styles['BodyText'].fontName = self._font_regular
        self.styles['Title'].fontName = self._font_bold
        self.styles['Heading1'].fontName = self._font_bold
        self.styles['Heading2'].fontName = self._font_bold
        self.styles['Heading3'].fontName = self._font_bold
        
        # Cover title style
        self.styles.add(
            ParagraphStyle(
                name="CoverTitle",
                parent=self.styles["Heading1"],
                fontName=self._font_bold,
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
                fontName=self._font_regular,
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
                fontName=self._font_bold,
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
                fontName=self._font_bold,
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
                fontName=self._font_regular,
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
                fontName=self._font_regular,
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
        canvas_obj.setFont(self._font_regular, 9)
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

    def _create_chapter_image(self, image_path):
        """
        Create an Image element for embedding at the top of a chapter.
        Handles scaling, aspect ratio preservation, and error handling.
        
        Args:
            image_path: Absolute path to the image file.
            
        Returns:
            Image: ReportLab Image object, or None if image cannot be loaded.
        """
        if not image_path or not os.path.exists(image_path):
            print(f"Warning: Image not found, skipping: {image_path}")
            return None
        
        # Validate image file extension as a first check
        # Note: This is a basic check; actual validation happens in ReportLab's Image()
        valid_extensions = ('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp')
        if not image_path.lower().endswith(valid_extensions):
            print(f"Warning: Unsupported image format, skipping: {image_path}")
            return None
        
        try:
            # Create Image object - this validates the actual image format
            img = Image(image_path)
            
            # Validate image dimensions
            if img.imageWidth <= 0 or img.imageHeight <= 0:
                print(f"Warning: Invalid image dimensions, skipping: {image_path}")
                return None
            
            # Calculate available page width (minus margins)
            available_width = self.page_width - (2 * self.margin)
            
            # Get original aspect ratio (safe from division by zero after validation)
            aspect_ratio = img.imageHeight / float(img.imageWidth)
            
            # Scale to fit page width while maintaining aspect ratio
            img_width = available_width
            img_height = img_width * aspect_ratio
            
            # Limit maximum height to prevent images from being too tall
            max_height = 4 * inch
            if img_height > max_height:
                img_height = max_height
                img_width = img_height / aspect_ratio
            
            # Set the dimensions
            img.drawWidth = img_width
            img.drawHeight = img_height
            img.hAlign = "CENTER"
            
            return img
            
        except (IOError, OSError) as e:
            # File I/O errors
            print(f"Error reading image file {image_path}: {str(e)}")
            return None
        except (ValueError, ZeroDivisionError) as e:
            # Image dimension or calculation errors
            print(f"Error processing image dimensions {image_path}: {str(e)}")
            return None
        except Exception as e:
            # Catch-all for other ReportLab or unexpected errors
            print(f"Unexpected error loading image {image_path}: {str(e)}")
            return None

    def _add_chapters(self, project, story):
        """
        Add chapter content to the document with smart pagination.
        Uses generator.py for intelligent content distribution with tier-based limits.
        Embeds custom images at the top of chapters.

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
            
            # Embed custom image at the top of this chapter (if available)
            # Distribute images across chapters: first image -> first chapter, etc.
            chapter_index = i - 1  # 0-based index
            if chapter_index < len(self.custom_images):
                image_path = self.custom_images[chapter_index]
                image_element = self._create_chapter_image(image_path)
                if image_element:
                    story.append(image_element)
                    story.append(Spacer(1, 0.2 * inch))  # Small spacer after image
            
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

    def build_pdf(self, project, output_path=None, tier=None, custom_images=None):
        """
        Build the complete PDF document from a project.
        Implements strict page limits and smart content distribution.

        Args:
            project: CourseProject object with all project data.
            output_path: Optional output path (uses self.filename if not provided).
            tier: License tier for pagination (if None, uses session tier).
            custom_images: Optional list of image file paths to embed at chapter tops.

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
        
        # Store custom images (convert to absolute paths for safety)
        self.custom_images = []
        if custom_images:
            for img_path in custom_images:
                if img_path:
                    abs_path = os.path.abspath(img_path)
                    if os.path.exists(abs_path):
                        self.custom_images.append(abs_path)
                    else:
                        print(f"Warning: Image not found, skipping: {img_path}")
        
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
        Has infinite loop protection with MIN_FONT_SIZE = 7pt.
        
        Args:
            project: CourseProject object with all project data.
            target_page_count: Maximum number of pages allowed.
            
        Returns:
            str: The path of the generated PDF.
        """
        # Start with default font scale (1.0 = 100%)
        font_scale = 1.0
        MIN_FONT_SIZE = 7  # Absolute minimum font size in points (infinite loop protection)
        # Calculate minimum scale based on original body text size (12pt)
        original_body_size = 12
        min_font_scale = MIN_FONT_SIZE / original_body_size  # ~0.583 for 7pt minimum
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
                
                # If we're already at minimum and still over, truncate content
                if font_scale <= min_font_scale:
                    print(f"PDF Shrink-to-Fit: Minimum font size ({MIN_FONT_SIZE}pt) reached. Truncating content to fit {target_page_count} pages.")
                    # Truncate content to fit within page limit
                    self._truncate_project_content(project, target_page_count)
                    # Rebuild with truncated content
                    self._apply_font_scale(min_font_scale)
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
    
    def _truncate_project_content(self, project, target_page_count):
        """
        Truncate project content to fit within target page count.
        Used when MIN_FONT_SIZE is reached and content still doesn't fit.
        
        Args:
            project: CourseProject object to truncate
            target_page_count: Maximum number of pages allowed
        """
        if not project.chapters_content:
            return
        
        # Calculate target characters based on page count
        # Use ContentDistributor's constants
        from generator import MAX_CHARS_PER_PAGE
        target_chars = target_page_count * MAX_CHARS_PER_PAGE
        
        # Calculate current total characters
        total_chars = sum(len(content) for content in project.chapters_content.values())
        
        if total_chars <= target_chars:
            return  # No truncation needed
        
        # Calculate scaling factor
        scale_factor = target_chars / total_chars
        
        # Truncate each chapter proportionally
        truncated_content = {}
        for chapter_title, content in project.chapters_content.items():
            target_chapter_chars = int(len(content) * scale_factor)
            if target_chapter_chars > 0:
                # Truncate at sentence boundary
                truncated = self.distributor.truncate_at_sentence(content, target_chapter_chars)
                truncated_content[chapter_title] = truncated
            else:
                truncated_content[chapter_title] = ""
        
        # Update project with truncated content
        project.chapters_content = truncated_content
        print(f"PDF Truncation: Content reduced from {total_chars} to ~{target_chars} characters to fit {target_page_count} pages")


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

