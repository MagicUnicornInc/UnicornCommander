#!/usr/bin/env python3
# -*- coding: utf-8 -*-

try:
    # Try PyQt6 first (used in main app)
    from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QScrollArea, 
                                QLabel, QFrame, QSizePolicy)
    from PyQt6.QtCore import Qt, pyqtSignal, QSize
    from PyQt6.QtGui import QFont, QColor, QPalette
    QT6 = True
except ImportError:
    # Fallback to PyQt5 if needed
    from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QScrollArea, 
                                QLabel, QFrame, QSizePolicy)
    from PyQt5.QtCore import Qt, pyqtSignal, QSize
    from PyQt5.QtGui import QFont, QColor, QPalette
    QT6 = False

from app_root.utils.markdown import markdown_to_html


class MessageWidget(QFrame):
    """Widget for displaying a single message in the conversation"""
    
    def __init__(self, text="", is_user=False, is_placeholder=False, parent=None):
        super().__init__(parent)
        self.is_user = is_user
        self.is_placeholder = is_placeholder
        self.current_text = text
        
        # Set up frame appearance
        if QT6:
            self.setFrameShape(QFrame.Shape.StyledPanel)
            self.setFrameShadow(QFrame.Shadow.Raised)
        else:
            self.setFrameShape(QFrame.StyledPanel)
            self.setFrameShadow(QFrame.Raised)
        
        # Create layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Create and add label for message content
        self.label = QLabel()
        if QT6:
            self.label.setTextFormat(Qt.TextFormat.RichText)
            self.label.setWordWrap(True)
            self.label.setOpenExternalLinks(True)
            self.label.setTextInteractionFlags(
                Qt.TextInteractionFlag.TextSelectableByMouse | 
                Qt.TextInteractionFlag.TextSelectableByKeyboard | 
                Qt.TextInteractionFlag.LinksAccessibleByMouse
            )
        else:
            self.label.setTextFormat(Qt.RichText)
            self.label.setWordWrap(True)
            self.label.setOpenExternalLinks(True)
            self.label.setTextInteractionFlags(
                Qt.TextSelectableByMouse | 
                Qt.TextSelectableByKeyboard | 
                Qt.LinksAccessibleByMouse
            )
        
        # Set text with markdown rendering
        if text:
            html_content = markdown_to_html(text)
            self.label.setText(html_content)
            
        # Add label to layout
        layout.addWidget(self.label)
        
        # Add typing indicator for placeholder
        if is_placeholder:
            self.typing_indicator = QLabel("▌")
            self.typing_indicator.setStyleSheet("color: #666; font-weight: bold;")
            layout.addWidget(self.typing_indicator)
        
        # Style based on message type
        self.style_message()
        
    def update_text(self, new_text):
        """Update the message text (for streaming responses)"""
        self.current_text = new_text
        html_content = markdown_to_html(new_text)
        self.label.setText(html_content)
        
    def get_text(self):
        """Get the current message text"""
        return self.current_text
        
    def style_message(self):
        """Apply appropriate styling based on message type"""
        palette = self.palette()
        
        if self.is_user:
            # User message styling
            if QT6:
                palette.setColor(QPalette.ColorRole.Window, QColor(240, 240, 255))
            else:
                palette.setColor(QPalette.Window, QColor(240, 240, 255))
            self.setAutoFillBackground(True)
            self.setPalette(palette)
            self.setStyleSheet("""
                MessageWidget {
                    border-radius: 10px;
                    background-color: #e1f5fe;
                    border: 1px solid #81d4fa;
                    margin-left: 50px;
                }
            """)
        else:
            # Assistant message styling
            if QT6:
                palette.setColor(QPalette.ColorRole.Window, QColor(240, 255, 240))
            else:
                palette.setColor(QPalette.Window, QColor(240, 255, 240))
            self.setAutoFillBackground(True)
            self.setPalette(palette)
            self.setStyleSheet("""
                MessageWidget {
                    border-radius: 10px;
                    background-color: #f1f8e9;
                    border: 1px solid #aed581;
                    margin-right: 50px;
                }
            """)


class ConversationView(QScrollArea):
    """Widget for displaying the conversation history"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Setup scroll area
        self.setWidgetResizable(True)
        if QT6:
            self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        else:
            self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        # Create container widget and layout
        self.container = QWidget()
        self.layout = QVBoxLayout(self.container)
        if QT6:
            self.layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        else:
            self.layout.setAlignment(Qt.AlignTop)
        self.layout.setSpacing(10)
        self.layout.setContentsMargins(10, 10, 10, 10)
        
        # Set container as the scroll area widget
        self.setWidget(self.container)
        
        # Placeholder for streaming responses
        self.current_placeholder = None
        
        # Welcome message
        self.add_assistant_message("Hello! I'm the KDE AI Assistant powered by Ollama. How can I assist you today?")
        
    def add_user_message(self, text):
        """Add a user message to the conversation"""
        message_widget = MessageWidget(text, is_user=True)
        self.layout.addWidget(message_widget)
        self.scroll_to_bottom()
        
    def add_assistant_message(self, text):
        """Add an assistant message to the conversation"""
        message_widget = MessageWidget(text, is_user=False)
        self.layout.addWidget(message_widget)
        self.scroll_to_bottom()
        
    def add_assistant_placeholder(self):
        """Add a placeholder for streaming assistant messages"""
        self.current_placeholder = MessageWidget("", is_user=False, is_placeholder=True)
        self.layout.addWidget(self.current_placeholder)
        self.scroll_to_bottom()
        
    def update_assistant_placeholder(self, chunk):
        """Update the placeholder with new text chunk"""
        if self.current_placeholder:
            # Append new chunk to existing text
            current_text = self.current_placeholder.get_text()
            new_text = current_text + chunk
            self.current_placeholder.update_text(new_text)
            self.scroll_to_bottom()
        
    def replace_assistant_placeholder(self, full_text):
        """Replace the placeholder with final message"""
        if self.current_placeholder:
            # Create new message widget to replace placeholder
            index = self.layout.indexOf(self.current_placeholder)
            if index >= 0:
                # Remove placeholder
                self.layout.removeWidget(self.current_placeholder)
                self.current_placeholder.deleteLater()
                
                # Add final message
                final_message = MessageWidget(full_text, is_user=False)
                self.layout.insertWidget(index, final_message)
                self.current_placeholder = None
                self.scroll_to_bottom()
        
    def scroll_to_bottom(self):
        """Scroll to the bottom of the conversation"""
        self.verticalScrollBar().setValue(self.verticalScrollBar().maximum())