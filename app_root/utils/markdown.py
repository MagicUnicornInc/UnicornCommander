#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import markdown
from pygments import highlight
from pygments.lexers import get_lexer_by_name, guess_lexer
from pygments.formatters import HtmlFormatter


def markdown_to_html(text):
    """Convert markdown text to HTML with syntax highlighting"""
    
    # Create markdown converter with extensions
    md = markdown.Markdown(extensions=[
        'markdown.extensions.fenced_code',
        'markdown.extensions.tables',
        'markdown.extensions.nl2br',
        'markdown.extensions.sane_lists'
    ])
    
    # Process code blocks for syntax highlighting
    code_blocks = {}
    
    def replace_code_block(match):
        code = match.group(2)
        lang = match.group(1) or ''
        
        # Generate a unique placeholder
        placeholder = f"CODE_BLOCK_{len(code_blocks)}"
        
        # Store the code block for later processing
        code_blocks[placeholder] = (code, lang.strip())
        
        return placeholder
    
    # Replace code blocks with placeholders
    pattern = r'```(\w*)\n([\s\S]*?)```'
    processed_text = re.sub(pattern, replace_code_block, text)
    
    # Convert markdown to HTML
    html = md.convert(processed_text)
    
    # Process code blocks with syntax highlighting
    for placeholder, (code, lang) in code_blocks.items():
        try:
            if lang:
                lexer = get_lexer_by_name(lang, stripall=True)
            else:
                lexer = guess_lexer(code)
                
            formatter = HtmlFormatter(style='default', noclasses=True)
            highlighted_code = highlight(code, lexer, formatter)
            
            # Wrap in pre and code tags
            if not highlighted_code.startswith('<pre>'):
                highlighted_code = f'<pre><code class="language-{lang}">{highlighted_code}</code></pre>'
                
            html = html.replace(placeholder, highlighted_code)
        except Exception:
            # Fallback if highlighting fails
            html = html.replace(placeholder, f'<pre><code>{code}</code></pre>')
    
    return html


def strip_markdown(text):
    """Strip markdown formatting from text"""
    # Remove code blocks
    text = re.sub(r'```[\s\S]*?```', '', text)
    
    # Remove headers
    text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)
    
    # Remove bold/italic
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
    text = re.sub(r'\*(.+?)\*', r'\1', text)
    text = re.sub(r'__(.+?)__', r'\1', text)
    text = re.sub(r'_(.+?)_', r'\1', text)
    
    # Remove links
    text = re.sub(r'\[(.+?)\]\(.+?\)', r'\1', text)
    
    # Remove images
    text = re.sub(r'!\[.+?\]\(.+?\)', '', text)
    
    # Remove blockquotes
    text = re.sub(r'^>\s+', '', text, flags=re.MULTILINE)
    
    # Remove horizontal rules
    text = re.sub(r'^-{3,}$', '', text, flags=re.MULTILINE)
    text = re.sub(r'^_{3,}$', '', text, flags=re.MULTILINE)
    text = re.sub(r'^\*{3,}$', '', text, flags=re.MULTILINE)
    
    return text.strip()