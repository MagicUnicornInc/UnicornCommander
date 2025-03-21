#!/usr/bin/env python3
# -*- coding: utf-8 -*-

try:
    # Try PyQt6 first (used in main app)
    from PyQt6.QtWidgets import (QWidget, QHBoxLayout, QTextEdit, 
                              QPushButton, QSizePolicy)
    from PyQt6.QtCore import Qt, pyqtSignal, QSize
    from PyQt6.QtGui import QIcon, QKeySequence
    QT6 = True
except ImportError:
    # Fallback to PyQt5 if needed
    from PyQt5.QtWidgets import (QWidget, QHBoxLayout, QTextEdit, 
                              QPushButton, QSizePolicy)
    from PyQt5.QtCore import Qt, pyqtSignal, QSize
    from PyQt5.QtGui import QIcon, QKeySequence
    QT6 = False


class InputArea(QWidget):
    """Widget for user input in the conversation"""
    
    # Signal emitted when a message is submitted
    message_submitted = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Create layout
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 5, 0, 0)
        layout.setSpacing(10)
        
        # Create text input
        self.text_input = QTextEdit()
        self.text_input.setPlaceholderText("Type your message here...")
        self.text_input.setAcceptRichText(False)
        self.text_input.setMinimumHeight(40)
        self.text_input.setMaximumHeight(100)
        
        # Set up text input properties
        font = self.text_input.font()
        font.setPointSize(font.pointSize() + 1)
        self.text_input.setFont(font)
        
        # Make Enter key submit the message (Shift+Enter for new line)
        self.text_input.installEventFilter(self)
        
        # Create send button
        self.send_button = QPushButton()
        self.send_button.setIcon(QIcon.fromTheme("document-send"))
        self.send_button.setToolTip("Send message (Enter)")
        self.send_button.setMinimumSize(QSize(40, 40))
        self.send_button.clicked.connect(self.submit_message)
        
        # Add widgets to layout
        layout.addWidget(self.text_input, 1)  # 1 is the stretch factor
        layout.addWidget(self.send_button, 0)  # 0 means no stretch
        
        # Set size policy
        if QT6:
            self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        else:
            self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        
    def eventFilter(self, obj, event):
        """Event filter to handle key presses in the text edit"""
        if obj is self.text_input and event.type() == event.KeyPress:
            # Check for Enter key (without Shift modifier)
            if QT6:
                shift_modifier = Qt.KeyboardModifier.ShiftModifier
            else:
                shift_modifier = Qt.ShiftModifier
                
            if (event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter) and not event.modifiers() & shift_modifier:
                self.submit_message()
                return True
        
        # Pass event to parent class
        return super().eventFilter(obj, event)
    
    def submit_message(self):
        """Submit the current message"""
        message = self.text_input.toPlainText().strip()
        if message:
            self.message_submitted.emit(message)
            self.text_input.clear()
    
    def set_focus(self):
        """Set focus to the text input"""
        self.text_input.setFocus()
        
    def set_enabled(self, enabled):
        """Enable or disable the input area during processing"""
        self.text_input.setEnabled(enabled)
        self.send_button.setEnabled(enabled)
        
        if enabled:
            # Reset placeholder text when re-enabled
            self.text_input.setPlaceholderText("Type your message here...")
            self.send_button.setToolTip("Send message (Enter)")
        else:
            # Show processing indicator
            self.text_input.setPlaceholderText("Processing message...")
            self.send_button.setToolTip("Processing, please wait...")