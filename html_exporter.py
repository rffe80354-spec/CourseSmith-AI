"""
HTML Exporter Module - Export CourseSmith content to HTML format.
Creates professional, styled HTML documents.
"""

import os
import re
from datetime import datetime

from export_base import ExporterBase, ExportError, ExportManager


class HTMLExporter(ExporterBase):
    """
    Exporter for HTML format.
    
    Creates styled HTML documents with:
    - Modern CSS styling
    - Responsive design
    - Navigation sidebar
    - Formatted chapter content
    """
    
    file_extension = "html"
    format_name = "HTML"
    
    def export(self) -> str:
        """
        Export the project to HTML format.
        
        Returns:
            str: Path to the exported HTML file.
            
        Raises:
            ExportError: If export fails.
        """
        if not self.validate_project():
            raise ExportError(f"Invalid project: {', '.join(self.errors)}")
        
        try:
            # Build HTML content
            html_content = self._build_html()
            
            # Generate output path if needed
            output_path = self.generate_output_path()
            
            # Write to file
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            return output_path
            
        except Exception as e:
            raise ExportError(f"Failed to export HTML: {str(e)}")
    
    def _build_html(self) -> str:
        """
        Build the complete HTML document.
        
        Returns:
            str: Complete HTML content.
        """
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{self._escape_html(self.project.topic)}</title>
    {self._get_css()}
</head>
<body>
    <div class="container">
        {self._build_sidebar()}
        <main class="content">
            {self._build_header()}
            {self._build_chapters()}
            {self._build_footer()}
        </main>
    </div>
    {self._get_js()}
</body>
</html>"""
    
    def _get_css(self) -> str:
        """Get the CSS styles."""
        return """<style>
        :root {
            --primary-color: #7F5AF0;
            --primary-hover: #9D7BF2;
            --bg-dark: #0B0E14;
            --bg-sidebar: #151921;
            --bg-card: #1A1F2E;
            --text-primary: #FFFFFF;
            --text-secondary: #8B92A8;
            --border-color: #2A3142;
        }
        
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: var(--bg-dark);
            color: var(--text-primary);
            line-height: 1.6;
        }
        
        .container {
            display: flex;
            min-height: 100vh;
        }
        
        .sidebar {
            width: 280px;
            background-color: var(--bg-sidebar);
            padding: 30px 20px;
            position: fixed;
            height: 100vh;
            overflow-y: auto;
            border-right: 1px solid var(--border-color);
        }
        
        .sidebar h2 {
            color: var(--text-primary);
            font-size: 1.2rem;
            margin-bottom: 20px;
            padding-bottom: 15px;
            border-bottom: 1px solid var(--border-color);
        }
        
        .sidebar nav ul {
            list-style: none;
        }
        
        .sidebar nav li {
            margin-bottom: 8px;
        }
        
        .sidebar nav a {
            color: var(--text-secondary);
            text-decoration: none;
            display: block;
            padding: 10px 15px;
            border-radius: 8px;
            transition: all 0.3s ease;
            font-size: 0.95rem;
        }
        
        .sidebar nav a:hover {
            background-color: var(--bg-card);
            color: var(--primary-color);
        }
        
        .sidebar nav a.active {
            background-color: var(--primary-color);
            color: var(--text-primary);
        }
        
        .content {
            flex: 1;
            margin-left: 280px;
            padding: 40px 60px;
            max-width: 900px;
        }
        
        .header {
            text-align: center;
            margin-bottom: 60px;
            padding-bottom: 40px;
            border-bottom: 1px solid var(--border-color);
        }
        
        .header h1 {
            font-size: 2.5rem;
            margin-bottom: 15px;
            color: var(--text-primary);
        }
        
        .header .subtitle {
            font-size: 1.2rem;
            color: var(--text-secondary);
            margin-bottom: 20px;
        }
        
        .header .meta {
            font-size: 0.9rem;
            color: var(--text-secondary);
        }
        
        .chapter {
            margin-bottom: 60px;
            padding: 30px;
            background-color: var(--bg-card);
            border-radius: 15px;
            border: 1px solid var(--border-color);
        }
        
        .chapter h2 {
            font-size: 1.8rem;
            color: var(--primary-color);
            margin-bottom: 25px;
            padding-bottom: 15px;
            border-bottom: 1px solid var(--border-color);
        }
        
        .chapter h3 {
            font-size: 1.3rem;
            color: var(--text-primary);
            margin-top: 25px;
            margin-bottom: 15px;
        }
        
        .chapter p {
            margin-bottom: 15px;
            color: var(--text-secondary);
        }
        
        .chapter ul, .chapter ol {
            margin: 15px 0;
            padding-left: 25px;
            color: var(--text-secondary);
        }
        
        .chapter li {
            margin-bottom: 8px;
        }
        
        .chapter strong {
            color: var(--text-primary);
        }
        
        .chapter em {
            font-style: italic;
        }
        
        .footer {
            text-align: center;
            padding: 40px 0;
            margin-top: 40px;
            border-top: 1px solid var(--border-color);
            color: var(--text-secondary);
            font-size: 0.9rem;
        }
        
        @media (max-width: 768px) {
            .sidebar {
                display: none;
            }
            
            .content {
                margin-left: 0;
                padding: 20px;
            }
            
            .header h1 {
                font-size: 1.8rem;
            }
        }
        
        @media print {
            .sidebar {
                display: none;
            }
            
            .content {
                margin-left: 0;
            }
            
            .chapter {
                page-break-inside: avoid;
            }
        }
    </style>"""
    
    def _get_js(self) -> str:
        """Get JavaScript for interactivity."""
        return """<script>
        // Highlight active chapter on scroll
        document.addEventListener('scroll', function() {
            const chapters = document.querySelectorAll('.chapter');
            const navLinks = document.querySelectorAll('.sidebar nav a');
            
            let currentChapter = '';
            
            chapters.forEach(chapter => {
                const rect = chapter.getBoundingClientRect();
                if (rect.top <= 100) {
                    currentChapter = chapter.id;
                }
            });
            
            navLinks.forEach(link => {
                link.classList.remove('active');
                if (link.getAttribute('href') === '#' + currentChapter) {
                    link.classList.add('active');
                }
            });
        });
        
        // Smooth scroll for navigation
        document.querySelectorAll('.sidebar nav a').forEach(link => {
            link.addEventListener('click', function(e) {
                e.preventDefault();
                const targetId = this.getAttribute('href').slice(1);
                const target = document.getElementById(targetId);
                if (target) {
                    target.scrollIntoView({ behavior: 'smooth' });
                }
            });
        });
    </script>"""
    
    def _build_sidebar(self) -> str:
        """Build the navigation sidebar."""
        nav_items = []
        for i, title in enumerate(self.project.outline, 1):
            chapter_id = f"chapter-{i}"
            nav_items.append(
                f'<li><a href="#{chapter_id}">Chapter {i}: {self._escape_html(title)}</a></li>'
            )
        
        nav_items_html = '\n                    '.join(nav_items)
        return f"""<aside class="sidebar">
            <h2>📚 Contents</h2>
            <nav>
                <ul>
                    {nav_items_html}
                </ul>
            </nav>
        </aside>"""
    
    def _build_header(self) -> str:
        """Build the document header."""
        branding = self.project.branding
        meta_parts = []
        
        if branding.get('author_name'):
            meta_parts.append(f"By {self._escape_html(branding['author_name'])}")
        if branding.get('company_name'):
            meta_parts.append(self._escape_html(branding['company_name']))
        
        meta_parts.append(f"Generated on {datetime.now().strftime('%B %d, %Y')}")
        
        meta_html = " • ".join(meta_parts)
        
        return f"""<header class="header">
            <h1>{self._escape_html(self.project.topic)}</h1>
            <p class="subtitle">A Comprehensive Guide for {self._escape_html(self.project.audience)}</p>
            <p class="meta">{meta_html}</p>
        </header>"""
    
    def _build_chapters(self) -> str:
        """Build all chapter content."""
        chapters_html = []
        
        for i, chapter_title in enumerate(self.project.outline, 1):
            chapter_html = self._build_chapter(i, chapter_title)
            chapters_html.append(chapter_html)
        
        return '\n'.join(chapters_html)
    
    def _build_chapter(self, chapter_num: int, chapter_title: str) -> str:
        """
        Build a single chapter section.
        
        Args:
            chapter_num: The chapter number.
            chapter_title: The chapter title.
            
        Returns:
            str: HTML content for the chapter.
        """
        content = self.project.chapters_content.get(chapter_title, "")
        content_html = self._markdown_to_html(content)
        
        return f"""<section class="chapter" id="chapter-{chapter_num}">
            <h2>Chapter {chapter_num}: {self._escape_html(chapter_title)}</h2>
            {content_html}
        </section>"""
    
    def _markdown_to_html(self, content: str) -> str:
        """
        Convert markdown content to HTML.
        
        Args:
            content: Markdown content.
            
        Returns:
            str: HTML content.
        """
        lines = content.split('\n')
        html_parts = []
        current_para = []
        in_list = False
        
        for line in lines:
            stripped = line.strip()
            
            # Headers
            if stripped.startswith('## '):
                self._flush_paragraph(html_parts, current_para)
                current_para = []
                if in_list:
                    html_parts.append('</ul>')
                    in_list = False
                header_text = self._escape_html(stripped[3:])
                html_parts.append(f'<h3>{header_text}</h3>')
                
            elif stripped.startswith('# '):
                self._flush_paragraph(html_parts, current_para)
                current_para = []
                if in_list:
                    html_parts.append('</ul>')
                    in_list = False
                header_text = self._escape_html(stripped[2:])
                html_parts.append(f'<h3>{header_text}</h3>')
                
            # Bullet points
            elif stripped.startswith('* ') or stripped.startswith('- '):
                self._flush_paragraph(html_parts, current_para)
                current_para = []
                if not in_list:
                    html_parts.append('<ul>')
                    in_list = True
                item_text = self._process_inline_markdown(stripped[2:])
                html_parts.append(f'<li>{item_text}</li>')
                
            # Empty line
            elif stripped == '':
                self._flush_paragraph(html_parts, current_para)
                current_para = []
                if in_list:
                    html_parts.append('</ul>')
                    in_list = False
                    
            # Regular text
            else:
                if in_list:
                    html_parts.append('</ul>')
                    in_list = False
                current_para.append(stripped)
        
        # Flush remaining content
        self._flush_paragraph(html_parts, current_para)
        if in_list:
            html_parts.append('</ul>')
        
        return '\n'.join(html_parts)
    
    def _flush_paragraph(self, html_parts: list, para_lines: list):
        """Flush accumulated paragraph lines to HTML."""
        if para_lines:
            text = ' '.join(para_lines)
            processed = self._process_inline_markdown(text)
            html_parts.append(f'<p>{processed}</p>')
    
    def _process_inline_markdown(self, text: str) -> str:
        """Process inline markdown (bold, italic) to HTML."""
        # First escape HTML, then process markdown
        text = self._escape_html(text)
        
        # Bold: **text**
        text = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', text)
        
        # Italic: *text*
        text = re.sub(r'\*([^*]+)\*', r'<em>\1</em>', text)
        
        return text
    
    def _build_footer(self) -> str:
        """Build the document footer."""
        branding = self.project.branding
        website = ""
        if branding.get('website_url'):
            url = self._escape_html(branding['website_url'])
            website = f'<br><a href="{url}" style="color: var(--primary-color);">{url}</a>'
        
        return f"""<footer class="footer">
            <p>Generated by CourseSmith AI{website}</p>
        </footer>"""
    
    def _escape_html(self, text: str) -> str:
        """
        Escape HTML special characters.
        
        Args:
            text: Text to escape.
            
        Returns:
            str: Escaped text.
        """
        if not text:
            return ""
        return (text
                .replace('&', '&amp;')
                .replace('<', '&lt;')
                .replace('>', '&gt;')
                .replace('"', '&quot;')
                .replace("'", '&#39;'))


# Register the exporter
ExportManager.register_exporter('html', HTMLExporter)
