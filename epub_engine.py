"""
EPUB Engine Module - Professional E-book creation for CourseSmith AI.
Uses ebooklib for generating EPUB format e-books for digital readers.
SECURITY: Requires valid session token to function (anti-tamper protection).
"""

import os
import re
import uuid
from ebooklib import epub

from session_manager import is_active, get_tier, SecurityError


class EpubBuilder:
    """
    Professional EPUB e-book builder with styling and formatting.
    
    Features:
    - Cover page with title
    - Chapter structure with navigation
    - Markdown parsing (# and ##, bullet points)
    - Clean CSS styling
    - Table of Contents (NCX and HTML)
    - Compatible with most e-readers
    """

    def __init__(self, filename, tier=None):
        """
        Initialize the EPUB builder with document settings.

        Args:
            filename: The output EPUB filename.
            tier: License tier (if None, fetched from session).
        """
        # Security check
        if not is_active():
            raise SecurityError("Unauthorized: No valid session. Please activate your license.")
        
        self.filename = filename
        self.tier = tier if tier is not None else (get_tier() or 'trial')
        self.book = epub.EpubBook()
        self.chapters = []
        self.title = ""
        self.subtitle = ""
        self.author = "CourseSmith AI"
        
        # Generate unique identifier
        self.book.set_identifier(str(uuid.uuid4()))
        self.book.set_language('en')
        
        # Setup default CSS
        self._setup_styles()

    def _setup_styles(self):
        """Setup CSS styles for the e-book."""
        self.css_content = '''
@namespace epub "http://www.idpf.org/2007/ops";

body {
    font-family: Georgia, serif;
    margin: 5%;
    text-align: justify;
    line-height: 1.6;
}

h1 {
    font-family: Arial, sans-serif;
    color: #1a1a2e;
    font-size: 2em;
    text-align: center;
    margin-top: 2em;
    margin-bottom: 1em;
    border-bottom: 2px solid #7F5AF0;
    padding-bottom: 0.5em;
}

h2 {
    font-family: Arial, sans-serif;
    color: #363656;
    font-size: 1.5em;
    margin-top: 1.5em;
    margin-bottom: 0.5em;
}

h3 {
    font-family: Arial, sans-serif;
    color: #4a4a6a;
    font-size: 1.2em;
    margin-top: 1em;
    margin-bottom: 0.5em;
}

p {
    margin-bottom: 1em;
    text-indent: 1.5em;
}

p.first {
    text-indent: 0;
}

ul, ol {
    margin-left: 1.5em;
    margin-bottom: 1em;
}

li {
    margin-bottom: 0.5em;
}

.cover-title {
    font-size: 2.5em;
    text-align: center;
    margin-top: 30%;
    color: #1a1a2e;
}

.cover-subtitle {
    font-size: 1.2em;
    text-align: center;
    color: #4a4a6a;
    margin-top: 2em;
}

.cover-author {
    font-size: 1em;
    text-align: center;
    color: #8B92A8;
    margin-top: 5em;
}

.chapter-number {
    font-size: 0.8em;
    color: #7F5AF0;
    text-transform: uppercase;
    letter-spacing: 2px;
}

.toc-title {
    font-size: 1.8em;
    margin-bottom: 1em;
}

.toc-item {
    margin-bottom: 0.5em;
}

.toc-item a {
    text-decoration: none;
    color: #363656;
}

.toc-item a:hover {
    color: #7F5AF0;
}
'''
        # Create CSS file
        self.css = epub.EpubItem(
            uid="style_default",
            file_name="style/default.css",
            media_type="text/css",
            content=self.css_content
        )
        self.book.add_item(self.css)

    def set_metadata(self, title, subtitle="", author="CourseSmith AI", language="en"):
        """
        Set the e-book metadata.
        
        Args:
            title: Book title.
            subtitle: Book subtitle.
            author: Author name.
            language: Language code (default: en).
        """
        self.title = title
        self.subtitle = subtitle
        self.author = author
        
        self.book.set_title(title)
        self.book.set_language(language)
        self.book.add_author(author)
        
        if subtitle:
            self.book.add_metadata('DC', 'description', subtitle)

    def _markdown_to_html(self, text):
        """
        Convert markdown text to HTML.
        
        Args:
            text: Markdown text.
            
        Returns:
            str: HTML content.
        """
        lines = text.split('\n')
        html_lines = []
        in_list = False
        
        for line in lines:
            line = line.strip()
            
            if not line:
                if in_list:
                    html_lines.append('</ul>')
                    in_list = False
                continue
            
            # Headers
            if line.startswith('## '):
                if in_list:
                    html_lines.append('</ul>')
                    in_list = False
                html_lines.append(f'<h3>{line[3:]}</h3>')
            elif line.startswith('# '):
                if in_list:
                    html_lines.append('</ul>')
                    in_list = False
                html_lines.append(f'<h2>{line[2:]}</h2>')
            # Bullet points
            elif line.startswith('- ') or line.startswith('* '):
                if not in_list:
                    html_lines.append('<ul>')
                    in_list = True
                html_lines.append(f'<li>{line[2:]}</li>')
            elif line.startswith('• '):
                if not in_list:
                    html_lines.append('<ul>')
                    in_list = True
                html_lines.append(f'<li>{line[1:].lstrip()}</li>')
            # Regular paragraph
            else:
                if in_list:
                    html_lines.append('</ul>')
                    in_list = False
                html_lines.append(f'<p>{line}</p>')
        
        if in_list:
            html_lines.append('</ul>')
        
        return '\n'.join(html_lines)

    def add_cover_page(self):
        """Add a cover page chapter."""
        cover_html = f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops">
<head>
    <title>Cover</title>
    <link rel="stylesheet" type="text/css" href="style/default.css"/>
</head>
<body>
    <div class="cover-title">{self.title}</div>
    <div class="cover-subtitle">{self.subtitle}</div>
    <div class="cover-author">Generated by {self.author}</div>
</body>
</html>'''
        
        cover = epub.EpubHtml(
            title='Cover',
            file_name='cover.xhtml',
            content=cover_html
        )
        cover.add_item(self.css)
        self.book.add_item(cover)
        self.chapters.append(cover)

    def add_toc_page(self, chapter_titles):
        """
        Add a table of contents page.
        
        Args:
            chapter_titles: List of chapter titles.
        """
        toc_items = []
        for i, title in enumerate(chapter_titles, 1):
            toc_items.append(f'<div class="toc-item"><a href="chapter_{i}.xhtml">Chapter {i}: {title}</a></div>')
        
        toc_html = f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops">
<head>
    <title>Table of Contents</title>
    <link rel="stylesheet" type="text/css" href="style/default.css"/>
</head>
<body>
    <h1 class="toc-title">Table of Contents</h1>
    {''.join(toc_items)}
</body>
</html>'''
        
        toc = epub.EpubHtml(
            title='Table of Contents',
            file_name='toc.xhtml',
            content=toc_html
        )
        toc.add_item(self.css)
        self.book.add_item(toc)
        self.chapters.append(toc)

    def add_chapter(self, title, content, chapter_num=None):
        """
        Add a chapter to the e-book.
        
        Args:
            title: Chapter title.
            content: Chapter content (markdown supported).
            chapter_num: Optional chapter number.
        """
        chapter_id = len(self.chapters)
        file_name = f'chapter_{chapter_num if chapter_num else chapter_id}.xhtml'
        
        # Convert markdown to HTML
        html_content = self._markdown_to_html(content)
        
        # Create chapter header
        if chapter_num:
            header = f'<div class="chapter-number">Chapter {chapter_num}</div><h1>{title}</h1>'
        else:
            header = f'<h1>{title}</h1>'
        
        chapter_html = f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops">
<head>
    <title>{title}</title>
    <link rel="stylesheet" type="text/css" href="style/default.css"/>
</head>
<body>
    {header}
    {html_content}
</body>
</html>'''
        
        chapter = epub.EpubHtml(
            title=title,
            file_name=file_name,
            content=chapter_html
        )
        chapter.add_item(self.css)
        self.book.add_item(chapter)
        self.chapters.append(chapter)
        
        return chapter

    def build(self):
        """
        Build and save the e-book.
        
        Returns:
            str: Path to the saved e-book.
        """
        # Security check before saving
        if not is_active():
            raise SecurityError("Unauthorized: Session expired. Please re-activate your license.")
        
        # Create table of contents
        self.book.toc = [(epub.Section('Chapters'), self.chapters)]
        
        # Add navigation files
        self.book.add_item(epub.EpubNcx())
        self.book.add_item(epub.EpubNav())
        
        # Create spine
        self.book.spine = ['nav'] + self.chapters
        
        # Write the epub file
        epub.write_epub(self.filename, self.book, {})
        
        return self.filename


def create_course_epub(filename, title, subtitle, chapters, contents, author="CourseSmith AI"):
    """
    Create a complete course EPUB e-book.
    
    Args:
        filename: Output filename.
        title: Course title.
        subtitle: Course subtitle.
        chapters: List of chapter titles.
        contents: List of chapter contents (same order as chapters).
        author: Author name.
        
    Returns:
        str: Path to the saved e-book.
    """
    # Detect language from content
    language = 'en'
    if any(re.search(r'[а-яА-ЯёЁ]', c) for c in contents):
        language = 'ru'
    
    builder = EpubBuilder(filename)
    builder.set_metadata(title, subtitle, author, language)
    builder.add_cover_page()
    builder.add_toc_page(chapters)
    
    for i, (chapter_title, chapter_content) in enumerate(zip(chapters, contents), 1):
        builder.add_chapter(chapter_title, chapter_content, chapter_num=i)
    
    return builder.build()
