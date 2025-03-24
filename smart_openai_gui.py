#!/usr/bin/env python3
"""
Enhanced OpenAI-powered GUI for KDE AI Interface with memory features

This script launches an OpenAI-powered GUI with both short-term and
long-term memory capabilities, using a Qdrant vector database for
storing and retrieving context.
"""

import sys
import os
import logging
from pathlib import Path
import json
import asyncio
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("SmartOpenAIGUI")

# Needed for PyQt import
try:
    from PyQt5.QtCore import Qt, QSize, QSettings, QTimer, pyqtSignal, QObject
    from PyQt5.QtGui import QIcon, QPixmap, QFont, QPalette, QColor
    from PyQt5.QtWidgets import (
        QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
        QPushButton, QLabel, QTextEdit, QLineEdit, QScrollArea,
        QSystemTrayIcon, QMenu, QAction, QDialog, QCheckBox,
        QComboBox, QFrame, QSplitter, QTabWidget, QListWidget,
        QListWidgetItem, QFileDialog, QMessageBox, QToolBar, QSizePolicy
    )
    from PyQt5 import QtGui
except ImportError as e:
    print(f"Failed to import PyQt5: {e}")
    print("Please install PyQt5 with: pip install PyQt5")
    sys.exit(1)

# Try to import QDarkStyle for dark mode
try:
    import qdarkstyle
    QDARKSTYLE_AVAILABLE = True
except ImportError:
    QDARKSTYLE_AVAILABLE = False
    print("QDarkStyle not available. Install with: pip install qdarkstyle")

# Import OpenAI backend
try:
    from openai_backend import OpenAIBackend
    OPENAI_AVAILABLE = True
except ImportError as e:
    OPENAI_AVAILABLE = False
    print(f"Failed to import OpenAI backend: {e}")
    print("Please check if openai_backend.py is in the current directory")

# Import memory features
try:
    from app_root.memory import MemoryIntegration
    MEMORY_AVAILABLE = True
except ImportError as e:
    MEMORY_AVAILABLE = False
    print(f"Failed to import memory integration: {e}")
    print("Memory features will be disabled")

# Custom streaming signal for handling OpenAI streaming responses
class StreamHandler(QObject):
    new_token_signal = pyqtSignal(str)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Initialize window
        self.setWindowTitle("KDE AI Interface - Smart OpenAI")
        self.setMinimumSize(800, 600)
        self.setWindowIcon(QIcon.fromTheme("assistant"))
        
        # Initialize OpenAI client (if available)
        self.openai_backend = None
        if OPENAI_AVAILABLE:
            self.openai_backend = OpenAIBackend()
        
        # Initialize memory integration (if available)
        self.memory_integration = None
        if MEMORY_AVAILABLE and OPENAI_AVAILABLE and self.openai_backend.is_available():
            self.memory_integration = MemoryIntegration(api_key=self.openai_backend.api_key)
        
        # Load settings
        self.settings = QSettings("KognitiveKompanion", "KDE-AI-Interface")
        self.load_settings()
        
        # Set up streaming handler
        self.stream_handler = StreamHandler()
        self.stream_handler.new_token_signal.connect(self.update_response_streaming)
        
        # Set up UI
        self.setup_ui()
        
        # Create system tray icon
        self.setup_system_tray()
        
        # Apply theme
        self.apply_theme()
        
        # Set up model if available
        if self.openai_backend and self.openai_backend.is_available():
            # Get available models and update dropdown
            models = self.openai_backend.get_available_models()
            if models:
                self.model_combo.clear()
                # Filter for appropriate models
                chat_models = [m for m in models if 'gpt' in m.lower()]
                self.model_combo.addItems(chat_models)
                
                # Set default to gpt-4o-mini if available, otherwise first in list
                default_model = "gpt-4o-mini"
                if default_model in chat_models:
                    self.model_combo.setCurrentText(default_model)
                elif chat_models:
                    self.model_combo.setCurrentText(chat_models[0])
        else:
            error_msg = "OpenAI API not available. Please check your API key."
            self.display_message("system", error_msg)

    def setup_ui(self):
        # Create central widget and main layout
        central_widget = QWidget()
        main_layout = QHBoxLayout(central_widget)
        
        # Create splitter for sidebar and main area
        self.splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(self.splitter)
        
        # --- Left Sidebar ---
        sidebar_widget = QWidget()
        sidebar_layout = QVBoxLayout(sidebar_widget)
        sidebar_layout.setContentsMargins(10, 10, 10, 10)
        
        # Model selection
        model_layout = QHBoxLayout()
        model_label = QLabel("Model:")
        self.model_combo = QComboBox()
        # Add default models (will be updated later if API is available)
        self.model_combo.addItems(["gpt-4o-mini", "gpt-3.5-turbo"])
        self.model_combo.setCurrentText("gpt-4o-mini")
        model_layout.addWidget(model_label)
        model_layout.addWidget(self.model_combo)
        sidebar_layout.addLayout(model_layout)
        
        # Memory toggles
        memory_group = QFrame()
        memory_layout = QVBoxLayout(memory_group)
        memory_layout.setContentsMargins(0, 10, 0, 10)
        
        memory_label = QLabel("Memory Options:")
        memory_label.setStyleSheet("font-weight: bold;")
        memory_layout.addWidget(memory_label)
        
        self.long_term_checkbox = QCheckBox("Use Long-term Memory")
        self.long_term_checkbox.setChecked(True)
        memory_layout.addWidget(self.long_term_checkbox)
        
        self.conversation_checkbox = QCheckBox("Use Conversation History")
        self.conversation_checkbox.setChecked(True)
        memory_layout.addWidget(self.conversation_checkbox)
        
        self.screen_checkbox = QCheckBox("Use Screen Context")
        self.screen_checkbox.setChecked(False)  # Off by default until implemented
        self.screen_checkbox.setEnabled(False)  # Disabled until implemented
        memory_layout.addWidget(self.screen_checkbox)
        
        # Connect memory toggles to handlers
        self.long_term_checkbox.toggled.connect(self.toggle_long_term_memory)
        self.conversation_checkbox.toggled.connect(self.toggle_conversation_memory)
        self.screen_checkbox.toggled.connect(self.toggle_screen_memory)
        
        sidebar_layout.addWidget(memory_group)
        
        # Conversation list
        conv_label = QLabel("Recent Conversations:")
        conv_label.setStyleSheet("font-weight: bold;")
        sidebar_layout.addWidget(conv_label)
        
        self.conversation_list = QListWidget()
        self.conversation_list.itemDoubleClicked.connect(self.load_selected_conversation)
        sidebar_layout.addWidget(self.conversation_list)
        
        # Conversation actions
        conv_actions_layout = QHBoxLayout()
        self.load_conv_button = QPushButton("Load")
        self.load_conv_button.clicked.connect(self.load_conversation_dialog)
        self.save_conv_button = QPushButton("Save")
        self.save_conv_button.clicked.connect(self.save_current_conversation)
        conv_actions_layout.addWidget(self.load_conv_button)
        conv_actions_layout.addWidget(self.save_conv_button)
        sidebar_layout.addLayout(conv_actions_layout)
        
        # Settings button
        self.settings_button = QPushButton("Settings")
        self.settings_button.clicked.connect(self.show_settings_dialog)
        sidebar_layout.addWidget(self.settings_button)
        
        # Memory status
        status_label = QLabel("Memory Status:")
        status_label.setStyleSheet("font-weight: bold;")
        sidebar_layout.addWidget(status_label)
        
        self.memory_status_label = QLabel("Loading memory status...")
        self.memory_status_label.setWordWrap(True)
        sidebar_layout.addWidget(self.memory_status_label)
        
        sidebar_layout.addStretch(1)
        
        # --- Main Chat Area ---
        chat_widget = QWidget()
        chat_layout = QVBoxLayout(chat_widget)
        chat_layout.setContentsMargins(10, 10, 10, 10)
        
        # Chat display area
        self.chat_scroll_area = QScrollArea()
        self.chat_scroll_area.setWidgetResizable(True)
        self.chat_scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.chat_scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        self.chat_content = QWidget()
        self.chat_layout = QVBoxLayout(self.chat_content)
        self.chat_layout.setAlignment(Qt.AlignTop)
        self.chat_layout.setSpacing(10)
        
        self.chat_scroll_area.setWidget(self.chat_content)
        chat_layout.addWidget(self.chat_scroll_area)
        
        # Input area
        input_layout = QVBoxLayout()
        
        # Message input
        self.message_input = QTextEdit()
        self.message_input.setPlaceholderText("Type your message here...")
        self.message_input.setAcceptRichText(False)
        self.message_input.setMinimumHeight(80)
        self.message_input.setMaximumHeight(200)
        self.message_input.textChanged.connect(self.adjust_input_height)
        
        # Special input handling for Enter key
        self.message_input.installEventFilter(self)
        
        input_layout.addWidget(self.message_input)
        
        # Buttons row
        buttons_layout = QHBoxLayout()
        
        self.send_button = QPushButton("Send")
        self.send_button.clicked.connect(self.send_message)
        self.send_button.setDefault(True)
        
        self.clear_button = QPushButton("Clear Chat")
        self.clear_button.clicked.connect(self.clear_chat)
        
        buttons_layout.addWidget(self.send_button)
        buttons_layout.addWidget(self.clear_button)
        
        input_layout.addLayout(buttons_layout)
        chat_layout.addLayout(input_layout)
        
        # Add widgets to splitter
        self.splitter.addWidget(sidebar_widget)
        self.splitter.addWidget(chat_widget)
        
        # Set initial splitter sizes (30% sidebar, 70% chat)
        self.splitter.setSizes([300, 700])
        
        # Set central widget
        self.setCentralWidget(central_widget)
        
        # Update UI if OpenAI or memory integration isn't available
        if not self.openai_backend or not self.openai_backend.is_available():
            self.send_button.setEnabled(False)
            self.clear_button.setEnabled(False)
            self.message_input.setEnabled(False)
            
            # Display error message
            error_widget = QWidget()
            error_layout = QVBoxLayout(error_widget)
            error_label = QLabel("OpenAI API not available. Please check your API key in settings.")
            error_label.setStyleSheet("color: red; font-weight: bold;")
            error_layout.addWidget(error_label)
            
            # Add API key input
            api_key_layout = QHBoxLayout()
            api_key_label = QLabel("API Key:")
            self.api_key_input = QLineEdit()
            self.api_key_input.setEchoMode(QLineEdit.Password)
            self.api_key_input.setPlaceholderText("Enter your OpenAI API key")
            api_key_layout.addWidget(api_key_label)
            api_key_layout.addWidget(self.api_key_input)
            
            save_key_button = QPushButton("Save Key")
            save_key_button.clicked.connect(self.save_api_key)
            api_key_layout.addWidget(save_key_button)
            
            error_layout.addLayout(api_key_layout)
            error_layout.addStretch(1)
            
            self.chat_layout.addWidget(error_widget)
        
        # Update conversation list if available
        self.update_conversation_list()
        
        # Update memory status
        self.update_memory_status()
        
        # Set up refresh timer for status
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.update_memory_status)
        self.status_timer.start(30000)  # Update every 30 seconds

    def setup_system_tray(self):
        # Create system tray icon
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(QIcon.fromTheme("assistant"))
        
        # Create tray menu
        tray_menu = QMenu()
        
        restore_action = QAction("Show/Hide", self)
        restore_action.triggered.connect(self.toggle_window)
        
        quit_action = QAction("Quit", self)
        quit_action.triggered.connect(self.close_application)
        
        tray_menu.addAction(restore_action)
        tray_menu.addSeparator()
        tray_menu.addAction(quit_action)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self.tray_icon_activated)
        
        # Show the tray icon
        self.tray_icon.show()

    def tray_icon_activated(self, reason):
        # Toggle window visibility when clicking on tray icon
        if reason == QSystemTrayIcon.Trigger:
            self.toggle_window()

    def toggle_window(self):
        # Toggle window visibility
        if self.isVisible():
            self.hide()
        else:
            self.show()
            self.activateWindow()

    def close_application(self):
        # Save settings before closing
        self.save_settings()
        
        # Close application
        QApplication.quit()

    def apply_theme(self):
        # Apply dark theme if QDarkStyle is available and dark mode is enabled
        if QDARKSTYLE_AVAILABLE and self.use_dark_mode:
            self.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
        else:
            # Use system theme
            self.setStyleSheet("")

    def eventFilter(self, obj, event):
        # Handle key events in the message input
        if obj is self.message_input and event.type() == event.KeyPress:
            if event.key() == Qt.Key_Return and not event.modifiers() & Qt.ShiftModifier:
                # Enter without Shift sends the message
                self.send_message()
                return True
            elif event.key() == Qt.Key_Return and event.modifiers() & Qt.ShiftModifier:
                # Shift+Enter adds a newline
                return False
        
        # Let the event propagate
        return super().eventFilter(obj, event)

    def adjust_input_height(self):
        # Adjust message input height based on content
        document_height = self.message_input.document().size().height()
        
        # Set height within limits
        new_height = max(80, min(200, document_height + 20))
        self.message_input.setMinimumHeight(new_height)

    def display_message(self, role, content):
        # Create a message widget
        message_widget = QWidget()
        message_layout = QVBoxLayout(message_widget)
        message_layout.setContentsMargins(10, 10, 10, 10)
        
        # Style based on role
        if role == "user":
            message_widget.setStyleSheet(
                "background-color: #e3f2fd; border-radius: 10px;"
                if not self.use_dark_mode else
                "background-color: #1e3a5f; border-radius: 10px;"
            )
            role_label = QLabel("You")
        elif role == "assistant":
            message_widget.setStyleSheet(
                "background-color: #f1f8e9; border-radius: 10px;"
                if not self.use_dark_mode else
                "background-color: #2e4537; border-radius: 10px;"
            )
            role_label = QLabel("Assistant")
        else:  # system
            message_widget.setStyleSheet(
                "background-color: #ffecb3; border-radius: 10px;"
                if not self.use_dark_mode else
                "background-color: #4a3f27; border-radius: 10px;"
            )
            role_label = QLabel("System")
        
        # Style the role label
        role_label.setStyleSheet("font-weight: bold; color: #424242;")
        message_layout.addWidget(role_label)
        
        # Add content label
        content_label = QLabel(content)
        content_label.setWordWrap(True)
        content_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        message_layout.addWidget(content_label)
        
        # Add timestamp
        timestamp = QLabel(datetime.now().strftime("%H:%M:%S"))
        timestamp.setStyleSheet("font-size: 8pt; color: gray;")
        timestamp.setAlignment(Qt.AlignRight)
        message_layout.addWidget(timestamp)
        
        # Add to chat layout
        self.chat_layout.addWidget(message_widget)
        
        # Scroll to bottom
        self.chat_scroll_area.verticalScrollBar().setValue(
            self.chat_scroll_area.verticalScrollBar().maximum()
        )
        
        # Add to memory if available
        if self.memory_integration:
            self.memory_integration.add_message_to_memory(role, content)

    def update_response_streaming(self, token):
        # Find the last message widget (should be the assistant's response)
        last_item = self.chat_layout.itemAt(self.chat_layout.count() - 1)
        if last_item:
            message_widget = last_item.widget()
            # Find the content label (second label in the layout)
            message_layout = message_widget.layout()
            if message_layout.count() > 1:
                content_label = message_layout.itemAt(1).widget()
                # Update the content label with the new token
                current_text = content_label.text()
                content_label.setText(current_text + token)
                
                # Scroll to bottom
                self.chat_scroll_area.verticalScrollBar().setValue(
                    self.chat_scroll_area.verticalScrollBar().maximum()
                )
                
                # Update timestamp label (last label in layout)
                if message_layout.count() > 2:
                    timestamp_label = message_layout.itemAt(2).widget()
                    timestamp_label.setText(datetime.now().strftime("%H:%M:%S"))

    def send_message(self):
        # Get message text
        message_text = self.message_input.toPlainText().strip()
        if not message_text:
            return
            
        # Check if OpenAI backend is available
        if not self.openai_backend or not self.openai_backend.is_available():
            self.display_message("system", "OpenAI API not available. Please check your API key.")
            return
            
        # Display user message
        self.display_message("user", message_text)
        
        # Clear input
        self.message_input.clear()
        
        # Show assistant thinking
        assistant_widget = QWidget()
        assistant_layout = QVBoxLayout(assistant_widget)
        assistant_layout.setContentsMargins(10, 10, 10, 10)
        
        # Style widget
        assistant_widget.setStyleSheet(
            "background-color: #f1f8e9; border-radius: 10px;"
            if not self.use_dark_mode else
            "background-color: #2e4537; border-radius: 10px;"
        )
        
        # Add role label
        role_label = QLabel("Assistant")
        role_label.setStyleSheet("font-weight: bold; color: #424242;")
        assistant_layout.addWidget(role_label)
        
        # Add thinking label
        content_label = QLabel("Thinking...")
        content_label.setWordWrap(True)
        assistant_layout.addWidget(content_label)
        
        # Add timestamp
        timestamp = QLabel(datetime.now().strftime("%H:%M:%S"))
        timestamp.setStyleSheet("font-size: 8pt; color: gray;")
        timestamp.setAlignment(Qt.AlignRight)
        assistant_layout.addWidget(timestamp)
        
        # Add to chat layout
        self.chat_layout.addWidget(assistant_widget)
        
        # Scroll to bottom
        self.chat_scroll_area.verticalScrollBar().setValue(
            self.chat_scroll_area.verticalScrollBar().maximum()
        )
        
        # Get model to use
        model = self.model_combo.currentText()
        
        # Process message in a separate thread to avoid blocking UI
        threading_method = "streaming" if self.use_streaming else "threading"
        
        # Enhance prompt with memory if available
        enhanced_message = message_text
        if self.memory_integration:
            enhanced_message = self.memory_integration.enhance_prompt_with_memory(message_text)
        
        if threading_method == "streaming":
            # Remove the temporary thinking widget
            self.chat_layout.removeWidget(assistant_widget)
            assistant_widget.deleteLater()
            
            # Add empty assistant message for streaming
            self.display_message("assistant", "")
            
            # Start streaming in a separate thread
            self.stream_thread = StreamingThread(
                self.openai_backend,
                enhanced_message,
                self.system_prompt,
                model,
                self.temperature,
                self.max_tokens,
                self.memory_integration.get_conversation_history() if self.memory_integration else None
            )
            self.stream_thread.new_token.connect(self.stream_handler.new_token_signal)
            self.stream_thread.start()
        else:
            # Use regular threading
            self.message_thread = MessageThread(
                self.openai_backend,
                enhanced_message,
                self.system_prompt,
                model,
                self.temperature,
                self.max_tokens,
                self.memory_integration.get_conversation_history() if self.memory_integration else None
            )
            self.message_thread.response_ready.connect(self.handle_response)
            self.message_thread.start()

    def handle_response(self, response):
        # Remove the temporary thinking widget if it exists
        if hasattr(self, 'thinking_widget') and self.thinking_widget:
            self.chat_layout.removeWidget(self.thinking_widget)
            self.thinking_widget.deleteLater()
            self.thinking_widget = None
            
        # Display assistant response
        self.display_message("assistant", response)

    def clear_chat(self):
        # Clear chat display
        while self.chat_layout.count():
            item = self.chat_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
                
        # Clear memory if available
        if self.memory_integration:
            self.memory_integration.clear_conversation()
            
        # Update UI
        self.update_conversation_list()
        self.update_memory_status()

    def show_settings_dialog(self):
        # Create settings dialog
        dialog = QDialog(self)
        dialog.setWindowTitle("Settings")
        dialog.setMinimumWidth(400)
        
        layout = QVBoxLayout(dialog)
        
        # API Key section
        api_key_layout = QHBoxLayout()
        api_key_label = QLabel("OpenAI API Key:")
        self.settings_api_key = QLineEdit()
        self.settings_api_key.setEchoMode(QLineEdit.Password)
        self.settings_api_key.setPlaceholderText("Enter your OpenAI API key")
        if self.openai_backend and self.openai_backend.api_key:
            self.settings_api_key.setText("*" * 12)  # Show masked key if present
        api_key_layout.addWidget(api_key_label)
        api_key_layout.addWidget(self.settings_api_key)
        layout.addLayout(api_key_layout)
        
        # System prompt
        system_prompt_layout = QVBoxLayout()
        system_prompt_label = QLabel("System Prompt:")
        self.settings_system_prompt = QTextEdit()
        self.settings_system_prompt.setPlaceholderText("Enter system prompt")
        self.settings_system_prompt.setText(self.system_prompt)
        self.settings_system_prompt.setMaximumHeight(100)
        system_prompt_layout.addWidget(system_prompt_label)
        system_prompt_layout.addWidget(self.settings_system_prompt)
        layout.addLayout(system_prompt_layout)
        
        # Advanced settings
        advanced_group = QFrame()
        advanced_layout = QVBoxLayout(advanced_group)
        
        # Temperature
        temp_layout = QHBoxLayout()
        temp_label = QLabel("Temperature:")
        self.settings_temperature = QLineEdit(str(self.temperature))
        temp_layout.addWidget(temp_label)
        temp_layout.addWidget(self.settings_temperature)
        advanced_layout.addLayout(temp_layout)
        
        # Max tokens
        tokens_layout = QHBoxLayout()
        tokens_label = QLabel("Max Tokens:")
        self.settings_max_tokens = QLineEdit(str(self.max_tokens))
        tokens_layout.addWidget(tokens_label)
        tokens_layout.addWidget(self.settings_max_tokens)
        advanced_layout.addLayout(tokens_layout)
        
        # Use streaming
        self.settings_streaming = QCheckBox("Use streaming responses")
        self.settings_streaming.setChecked(self.use_streaming)
        advanced_layout.addWidget(self.settings_streaming)
        
        # Dark mode
        self.settings_dark_mode = QCheckBox("Use dark mode")
        self.settings_dark_mode.setChecked(self.use_dark_mode)
        advanced_layout.addWidget(self.settings_dark_mode)
        
        layout.addWidget(advanced_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        save_button = QPushButton("Save")
        save_button.clicked.connect(lambda: self.save_settings_dialog(dialog))
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(dialog.reject)
        button_layout.addWidget(save_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)
        
        # Show dialog
        dialog.exec_()

    def save_settings_dialog(self, dialog):
        # Save settings from dialog
        
        # API Key - only save if changed (not masked)
        api_key = self.settings_api_key.text()
        if api_key and not api_key.startswith("*"):
            if self.openai_backend:
                self.openai_backend.save_api_key(api_key)
                
                # Update memory integration with new API key
                if self.memory_integration:
                    self.memory_integration.set_api_key(api_key)
        
        # System prompt
        self.system_prompt = self.settings_system_prompt.toPlainText()
        
        # Temperature
        try:
            self.temperature = float(self.settings_temperature.text())
        except ValueError:
            self.temperature = 0.7  # Default if invalid
        
        # Max tokens
        try:
            self.max_tokens = int(self.settings_max_tokens.text())
        except ValueError:
            self.max_tokens = 1000  # Default if invalid
        
        # Use streaming
        self.use_streaming = self.settings_streaming.isChecked()
        
        # Dark mode
        old_dark_mode = self.use_dark_mode
        self.use_dark_mode = self.settings_dark_mode.isChecked()
        
        # Apply theme if dark mode changed
        if old_dark_mode != self.use_dark_mode:
            self.apply_theme()
        
        # Save settings to disk
        self.save_settings()
        
        # Close dialog
        dialog.accept()
        
        # Update UI if API key changed
        if api_key and not api_key.startswith("*") and self.openai_backend:
            # Enable UI if it was disabled
            self.send_button.setEnabled(True)
            self.clear_button.setEnabled(True)
            self.message_input.setEnabled(True)
            
            # Remove error widget if it exists
            while self.chat_layout.count():
                item = self.chat_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
                    
            # Display welcome message
            self.display_message("system", "OpenAI API connected successfully! You can start chatting.")

    def save_api_key(self):
        # Save API key from error widget
        api_key = self.api_key_input.text()
        if not api_key:
            return
            
        # Initialize OpenAI backend if needed
        if not self.openai_backend:
            self.openai_backend = OpenAIBackend(api_key=api_key)
        else:
            self.openai_backend.save_api_key(api_key)
            
        # Initialize memory integration if needed
        if MEMORY_AVAILABLE and not self.memory_integration:
            self.memory_integration = MemoryIntegration(api_key=api_key)
        elif self.memory_integration:
            self.memory_integration.set_api_key(api_key)
            
        # Test connection
        if self.openai_backend.test_connection():
            # Enable UI
            self.send_button.setEnabled(True)
            self.clear_button.setEnabled(True)
            self.message_input.setEnabled(True)
            
            # Remove error widget
            while self.chat_layout.count():
                item = self.chat_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
                    
            # Display welcome message
            self.display_message("system", "OpenAI API connected successfully! You can start chatting.")
            
            # Update UI
            self.update_conversation_list()
            self.update_memory_status()
            
            # Get available models and update dropdown
            models = self.openai_backend.get_available_models()
            if models:
                self.model_combo.clear()
                # Filter for appropriate models
                chat_models = [m for m in models if 'gpt' in m.lower()]
                self.model_combo.addItems(chat_models)
                
                # Set default to gpt-4o-mini if available, otherwise first in list
                default_model = "gpt-4o-mini"
                if default_model in chat_models:
                    self.model_combo.setCurrentText(default_model)
                elif chat_models:
                    self.model_combo.setCurrentText(chat_models[0])
        else:
            # Display error message
            QMessageBox.critical(self, "API Error", 
                "Could not connect to OpenAI API. Please check your API key.")

    def save_settings(self):
        # Save settings to disk
        self.settings.setValue("geometry", self.saveGeometry())
        self.settings.setValue("windowState", self.saveState())
        self.settings.setValue("splitterSizes", self.splitter.saveState())
        self.settings.setValue("systemPrompt", self.system_prompt)
        self.settings.setValue("temperature", self.temperature)
        self.settings.setValue("maxTokens", self.max_tokens)
        self.settings.setValue("useStreaming", self.use_streaming)
        self.settings.setValue("useDarkMode", self.use_dark_mode)
        
        # Save memory settings if available
        if self.memory_integration:
            self.settings.setValue("useLongTermMemory", 
                                  self.memory_integration.use_long_term_memory)
            self.settings.setValue("useConversationMemory", 
                                  self.memory_integration.use_conversation_memory)
            self.settings.setValue("useScreenMemory", 
                                  self.memory_integration.use_screen_memory)

    def load_settings(self):
        # Load window geometry and state
        if self.settings.contains("geometry"):
            self.restoreGeometry(self.settings.value("geometry"))
        if self.settings.contains("windowState"):
            self.restoreState(self.settings.value("windowState"))
            
        # Load general settings
        self.system_prompt = self.settings.value(
            "systemPrompt", 
            "You are a helpful AI assistant for KDE Plasma desktop users. Provide clear and concise answers."
        )
        
        self.temperature = float(self.settings.value("temperature", 0.7))
        self.max_tokens = int(self.settings.value("maxTokens", 1000))
        self.use_streaming = self.settings.value("useStreaming", "true") == "true"
        self.use_dark_mode = self.settings.value("useDarkMode", "true") == "true"
        
        # Load memory settings if available
        if self.memory_integration:
            use_long_term = self.settings.value("useLongTermMemory", "true") == "true"
            use_conversation = self.settings.value("useConversationMemory", "true") == "true"
            use_screen = self.settings.value("useScreenMemory", "false") == "true"
            
            self.memory_integration.toggle_long_term_memory(use_long_term)
            self.memory_integration.toggle_conversation_memory(use_conversation)
            self.memory_integration.toggle_screen_memory(use_screen)

    def toggle_long_term_memory(self, enabled):
        # Toggle long-term memory if available
        if self.memory_integration:
            self.memory_integration.toggle_long_term_memory(enabled)
            self.update_memory_status()

    def toggle_conversation_memory(self, enabled):
        # Toggle conversation memory if available
        if self.memory_integration:
            self.memory_integration.toggle_conversation_memory(enabled)
            self.update_memory_status()

    def toggle_screen_memory(self, enabled):
        # Toggle screen memory if available
        if self.memory_integration:
            self.memory_integration.toggle_screen_memory(enabled)
            self.update_memory_status()

    def update_memory_status(self):
        # Update memory status label
        if not self.memory_integration:
            self.memory_status_label.setText("Memory integration not available")
            return
            
        try:
            # Get memory status
            status = self.memory_integration.get_memory_status()
            
            # Format status text
            status_text = (
                f"Long-term: {'ON' if status['long_term_enabled'] else 'OFF'} "
                f"({status['long_term_count']} memories)\n"
                f"Conversations: {'ON' if status['conversation_enabled'] else 'OFF'} "
                f"({status['conversation_count']} items)\n"
                f"Screen: {'ON' if status['screen_enabled'] else 'OFF'} "
                f"({status['screen_count']} items)\n"
                f"Current Conversation: {status['current_conversation_length']} messages"
            )
            
            self.memory_status_label.setText(status_text)
        except Exception as e:
            logger.error(f"Error updating memory status: {e}")
            self.memory_status_label.setText("Error getting memory status")

    def update_conversation_list(self):
        # Update conversation list if memory integration is available
        if not self.memory_integration:
            return
            
        try:
            # Clear list
            self.conversation_list.clear()
            
            # Get recent conversations
            conversations = self.memory_integration.get_recent_conversations()
            
            # Add to list
            for conv in conversations:
                timestamp = conv.get("timestamp", "")
                if timestamp:
                    try:
                        # Parse ISO timestamp and format it
                        dt = datetime.fromisoformat(timestamp)
                        timestamp = dt.strftime("%Y-%m-%d %H:%M")
                    except:
                        # Use as is if parsing fails
                        pass
                        
                item_text = f"{timestamp}\n{conv.get('summary', 'No summary')}"
                item = QListWidgetItem(item_text)
                item.setData(Qt.UserRole, conv)  # Store full conversation data
                self.conversation_list.addItem(item)
        except Exception as e:
            logger.error(f"Error updating conversation list: {e}")

    def load_selected_conversation(self, item):
        # Load the selected conversation
        if not self.memory_integration:
            return
            
        # Get conversation data
        conv_data = item.data(Qt.UserRole)
        if not conv_data or "path" not in conv_data:
            return
            
        # Load conversation
        if self.memory_integration.load_conversation(conv_data["path"]):
            # Clear chat display
            while self.chat_layout.count():
                item = self.chat_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
                    
            # Display conversation
            messages = self.memory_integration.get_conversation_history()
            for message in messages:
                role = message.get("role", "system")
                content = message.get("content", "")
                self.display_message(role, content)
                
            # Update memory status
            self.update_memory_status()
        else:
            QMessageBox.warning(self, "Load Error", 
                "Failed to load conversation. The file may be corrupted or missing.")

    def load_conversation_dialog(self):
        # Show dialog to load a conversation file
        if not self.memory_integration:
            return
            
        # Get conversations directory
        conv_dir = str(Path.home() / ".local" / "share" / "kde-ai-interface" / "conversations")
        
        # Show file dialog
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Load Conversation", conv_dir, "JSON Files (*.json)"
        )
        
        if file_path:
            # Load conversation
            if self.memory_integration.load_conversation(file_path):
                # Clear chat display
                while self.chat_layout.count():
                    item = self.chat_layout.takeAt(0)
                    if item.widget():
                        item.widget().deleteLater()
                        
                # Display conversation
                messages = self.memory_integration.get_conversation_history()
                for message in messages:
                    role = message.get("role", "system")
                    content = message.get("content", "")
                    self.display_message(role, content)
                    
                # Update memory status
                self.update_memory_status()
            else:
                QMessageBox.warning(self, "Load Error", 
                    "Failed to load conversation. The file may be corrupted.")

    def save_current_conversation(self):
        # Save the current conversation
        if not self.memory_integration:
            return
            
        # Check if there are messages to save
        if not self.memory_integration.get_conversation_history():
            QMessageBox.information(self, "No Conversation", 
                "There is no conversation to save.")
            return
            
        # Save conversation
        if self.memory_integration.save_current_conversation():
            QMessageBox.information(self, "Save Successful", 
                "Conversation saved successfully.")
                
            # Update conversation list
            self.update_conversation_list()
        else:
            QMessageBox.warning(self, "Save Error", 
                "Failed to save conversation.")

    def closeEvent(self, event):
        # Override close event to minimize to tray instead of closing
        if self.tray_icon.isVisible():
            # Hide window instead of closing
            self.hide()
            event.ignore()
        else:
            # Save settings before closing
            self.save_settings()
            event.accept()


# Thread for processing messages
from PyQt5.QtCore import QThread, pyqtSignal

class MessageThread(QThread):
    response_ready = pyqtSignal(str)
    
    def __init__(self, openai_backend, message, system_prompt, model, temperature, max_tokens, conversation_history=None):
        super().__init__()
        self.openai_backend = openai_backend
        self.message = message
        self.system_prompt = system_prompt
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.conversation_history = conversation_history
    
    def run(self):
        try:
            response = self.openai_backend.generate(
                prompt=self.message,
                system_prompt=self.system_prompt,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                conversation_history=self.conversation_history
            )
            self.response_ready.emit(response)
        except Exception as e:
            logger.error(f"Error in message thread: {e}")
            self.response_ready.emit(f"Error: {str(e)}")


class StreamingThread(QThread):
    new_token = pyqtSignal(str)
    
    def __init__(self, openai_backend, message, system_prompt, model, temperature, max_tokens, conversation_history=None):
        super().__init__()
        self.openai_backend = openai_backend
        self.message = message
        self.system_prompt = system_prompt
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.conversation_history = conversation_history
    
    def run(self):
        try:
            # Update the model in the backend
            self.openai_backend.model = self.model
            
            # Get streaming response
            for token in self.openai_backend.stream(
                prompt=self.message,
                system_prompt=self.system_prompt,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                conversation_history=self.conversation_history
            ):
                self.new_token.emit(token)
                
        except Exception as e:
            logger.error(f"Error in streaming thread: {e}")
            self.new_token.emit(f"\nError: {str(e)}")


if __name__ == "__main__":
    # Create the application
    app = QApplication(sys.argv)
    app.setApplicationName("KDE AI Interface - Smart OpenAI")
    
    # Create and show the main window
    main_window = MainWindow()
    main_window.show()
    
    # Start the application event loop
    sys.exit(app.exec_())