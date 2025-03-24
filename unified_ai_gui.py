#!/usr/bin/env python3
"""
Unified AI Interface for KDE with Multi-Backend Support and Memory Integration

This script provides a unified interface for the KDE AI Assistant with support for 
multiple backends (OpenAI, Ollama), integrated memory features, and agent capabilities.
It combines the functionality of all specialized interfaces into a single, cohesive GUI.
"""

import sys
import os
import logging
from pathlib import Path
import json
import asyncio
from datetime import datetime
import uuid
import threading

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("UnifiedAIGUI")

# Needed for PyQt import
try:
    from PyQt5.QtCore import Qt, QSize, QSettings, QTimer, pyqtSignal, QObject, QThread
    from PyQt5.QtGui import QIcon, QPixmap, QFont, QPalette, QColor
    from PyQt5.QtWidgets import (
        QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
        QPushButton, QLabel, QTextEdit, QLineEdit, QScrollArea,
        QSystemTrayIcon, QMenu, QAction, QDialog, QCheckBox,
        QComboBox, QFrame, QSplitter, QTabWidget, QListWidget,
        QListWidgetItem, QFileDialog, QMessageBox, QToolBar, QSizePolicy,
        QGroupBox, QRadioButton, QStackedWidget, QToolButton
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

# Import backend components
try:
    # Import backend providers
    from openai_backend import OpenAIBackend
    from ollama_backend import OllamaBackend
    OPENAI_AVAILABLE = True
    OLLAMA_AVAILABLE = True
except ImportError as e:
    OPENAI_AVAILABLE = False
    OLLAMA_AVAILABLE = False
    print(f"Failed to import backend modules: {e}")
    print("Please check if backend modules are in the current directory")

# Import backend manager
try:
    from app_root.config.backends import BackendManager
    BACKEND_MANAGER_AVAILABLE = True
except ImportError as e:
    BACKEND_MANAGER_AVAILABLE = False
    print(f"Failed to import backend manager: {e}")

# Import memory features
try:
    from app_root.memory.memory_integration import MemoryIntegration
    from app_root.memory.structured_storage import StructuredStorage
    MEMORY_AVAILABLE = True
except ImportError as e:
    MEMORY_AVAILABLE = False
    print(f"Failed to import memory integration: {e}")
    print("Memory features will be disabled")

# Import agent system
try:
    from app_root.agents.agent_manager import AgentManager
    AGENTS_AVAILABLE = True
except ImportError as e:
    AGENTS_AVAILABLE = False
    print(f"Failed to import agent manager: {e}")
    print("Agent features will be disabled")

# Import MCP client for agent tools
try:
    from app_root.mcp.client import MCPCoordinatorClient
    MCP_AVAILABLE = True
except ImportError as e:
    MCP_AVAILABLE = False
    print(f"Failed to import MCP client: {e}")
    print("MCP features will be disabled")

# Custom streaming signal for handling streaming responses
class StreamHandler(QObject):
    new_token_signal = pyqtSignal(str)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Initialize window
        self.setWindowTitle("KDE AI Interface - Unified")
        self.setMinimumSize(1000, 700)
        self.setWindowIcon(QIcon.fromTheme("assistant"))
        
        # Load settings
        self.settings = QSettings("KognitiveKompanion", "KDE-AI-Interface")
        self.load_settings()
        
        # Initialize backend manager
        self.backend_manager = None
        if BACKEND_MANAGER_AVAILABLE:
            self.backend_manager = BackendManager()
        
        # Initialize current backend
        self.current_backend = None
        self.backend_type = "openai"  # Default backend type
        
        # Initialize backend instances
        self.openai_backend = None
        self.ollama_backend = None
        
        # Initialize default backend
        self._initialize_backends()
        
        # Initialize structured storage for persistence
        self.structured_storage = None
        if MEMORY_AVAILABLE:
            try:
                self.structured_storage = StructuredStorage()
            except Exception as e:
                logger.error(f"Failed to initialize structured storage: {e}")
        
        # Initialize memory integration
        self.memory_integration = None
        if MEMORY_AVAILABLE and self.current_backend:
            try:
                # Get API key from current backend if it's OpenAI
                api_key = ""
                if self.backend_type == "openai" and self.openai_backend:
                    api_key = self.openai_backend.api_key
                
                self.memory_integration = MemoryIntegration(api_key=api_key)
            except Exception as e:
                logger.error(f"Failed to initialize memory integration: {e}")
        
        # Initialize MCP client for agent tools
        self.mcp_client = None
        if MCP_AVAILABLE:
            try:
                self.mcp_client = MCPCoordinatorClient()
            except Exception as e:
                logger.error(f"Failed to initialize MCP client: {e}")
        
        # Initialize agent manager
        self.agent_manager = None
        if AGENTS_AVAILABLE:
            try:
                self.agent_manager = AgentManager(
                    llm_backend=self.current_backend,
                    mcp_client=self.mcp_client,
                    structured_storage=self.structured_storage
                )
            except Exception as e:
                logger.error(f"Failed to initialize agent manager: {e}")
        
        # Set up streaming handler
        self.stream_handler = StreamHandler()
        self.stream_handler.new_token_signal.connect(self.update_response_streaming)
        
        # Set up UI
        self.setup_ui()
        
        # Create system tray icon
        self.setup_system_tray()
        
        # Apply theme
        self.apply_theme()
        
        # Update UI components based on available backends
        self.update_ui_for_backends()
        
        # Update memory status
        self.update_memory_status()
        
        # Set up refresh timer for status
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.update_memory_status)
        self.status_timer.start(30000)  # Update every 30 seconds

    def _initialize_backends(self):
        """Initialize backend instances based on preferences"""
        # Try to initialize OpenAI backend
        if OPENAI_AVAILABLE:
            try:
                self.openai_backend = OpenAIBackend()
                
                # Set as current backend if available and preferred
                if self.openai_backend.is_available() and self.backend_type == "openai":
                    self.current_backend = self.openai_backend
            except Exception as e:
                logger.error(f"Failed to initialize OpenAI backend: {e}")
        
        # Try to initialize Ollama backend
        if OLLAMA_AVAILABLE:
            try:
                self.ollama_backend = OllamaBackend()
                
                # Set as current backend if available and preferred or if OpenAI isn't available
                if self.ollama_backend.is_available() and (self.backend_type == "ollama" or not self.current_backend):
                    self.current_backend = self.ollama_backend
                    self.backend_type = "ollama"
            except Exception as e:
                logger.error(f"Failed to initialize Ollama backend: {e}")
        
        # If no backend is available, use OpenAI as placeholder
        if not self.current_backend and OPENAI_AVAILABLE:
            self.current_backend = self.openai_backend
            self.backend_type = "openai"

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
        
        # Backend selection
        backend_group = QGroupBox("Backend")
        backend_layout = QVBoxLayout(backend_group)
        
        # Radio buttons for backend selection
        self.openai_radio = QRadioButton("OpenAI")
        self.openai_radio.setChecked(self.backend_type == "openai")
        self.openai_radio.toggled.connect(lambda checked: self.switch_backend("openai") if checked else None)
        backend_layout.addWidget(self.openai_radio)
        
        # OpenAI models (only visible when OpenAI is selected)
        self.openai_model_layout = QHBoxLayout()
        openai_model_label = QLabel("Model:")
        self.openai_model_combo = QComboBox()
        self.openai_model_combo.addItems(["gpt-4o-mini", "gpt-3.5-turbo", "gpt-4o"])
        self.openai_model_combo.setCurrentText("gpt-4o-mini")
        self.openai_model_layout.addWidget(openai_model_label)
        self.openai_model_layout.addWidget(self.openai_model_combo)
        backend_layout.addLayout(self.openai_model_layout)
        
        # Ollama radio button
        self.ollama_radio = QRadioButton("Ollama (Local)")
        self.ollama_radio.setChecked(self.backend_type == "ollama")
        self.ollama_radio.toggled.connect(lambda checked: self.switch_backend("ollama") if checked else None)
        backend_layout.addWidget(self.ollama_radio)
        
        # Ollama models (only visible when Ollama is selected)
        self.ollama_model_layout = QHBoxLayout()
        ollama_model_label = QLabel("Model:")
        self.ollama_model_combo = QComboBox()
        self.ollama_model_combo.addItems(["llama3", "mistral", "phi3", "llama3:8b"])
        self.ollama_model_combo.setCurrentText("llama3")
        self.ollama_model_layout.addWidget(ollama_model_label)
        self.ollama_model_layout.addWidget(self.ollama_model_combo)
        backend_layout.addLayout(self.ollama_model_layout)
        
        # Add backend group to sidebar
        sidebar_layout.addWidget(backend_group)
        
        # Memory toggles
        memory_group = QGroupBox("Memory Options")
        memory_layout = QVBoxLayout(memory_group)
        
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
        
        # Agent selection
        agent_group = QGroupBox("Agent Selection")
        agent_layout = QVBoxLayout(agent_group)
        
        agent_label = QLabel("Select Agent Type:")
        agent_layout.addWidget(agent_label)
        
        self.agent_combo = QComboBox()
        self.agent_combo.addItem("Default Assistant", "default")
        if AGENTS_AVAILABLE and self.agent_manager:
            # Add available agents from agent manager
            agents = self.agent_manager.list_agents()
            for agent_id, agent in agents.items():
                self.agent_combo.addItem(agent.name, agent_id)
        
        agent_layout.addWidget(self.agent_combo)
        sidebar_layout.addWidget(agent_group)
        
        # Conversation list
        conv_group = QGroupBox("Recent Conversations")
        conv_layout = QVBoxLayout(conv_group)
        
        self.conversation_list = QListWidget()
        self.conversation_list.itemDoubleClicked.connect(self.load_selected_conversation)
        conv_layout.addWidget(self.conversation_list)
        
        # Conversation actions
        conv_actions_layout = QHBoxLayout()
        self.load_conv_button = QPushButton("Load")
        self.load_conv_button.clicked.connect(self.load_conversation_dialog)
        self.save_conv_button = QPushButton("Save")
        self.save_conv_button.clicked.connect(self.save_current_conversation)
        conv_actions_layout.addWidget(self.load_conv_button)
        conv_actions_layout.addWidget(self.save_conv_button)
        conv_layout.addLayout(conv_actions_layout)
        
        sidebar_layout.addWidget(conv_group)
        
        # Memory status
        status_group = QGroupBox("Memory Status")
        status_layout = QVBoxLayout(status_group)
        
        self.memory_status_label = QLabel("Loading memory status...")
        self.memory_status_label.setWordWrap(True)
        status_layout.addWidget(self.memory_status_label)
        
        sidebar_layout.addWidget(status_group)
        
        # Settings button
        self.settings_button = QPushButton("Settings")
        self.settings_button.clicked.connect(self.show_settings_dialog)
        sidebar_layout.addWidget(self.settings_button)
        
        # --- Main Chat Area ---
        chat_widget = QWidget()
        chat_layout = QVBoxLayout(chat_widget)
        chat_layout.setContentsMargins(10, 10, 10, 10)
        
        # Toolbar with actions
        toolbar = QToolBar()
        toolbar.setIconSize(QSize(24, 24))
        
        # Add RAG toggle
        self.rag_action = QAction(QIcon.fromTheme("search"), "Toggle RAG", self)
        self.rag_action.setCheckable(True)
        self.rag_action.setChecked(True)
        self.rag_action.toggled.connect(self.toggle_rag)
        toolbar.addAction(self.rag_action)
        
        # Add screen capture button (disabled for now)
        self.capture_action = QAction(QIcon.fromTheme("camera-photo"), "Capture Screen", self)
        self.capture_action.setEnabled(False)  # Disabled until implemented
        toolbar.addAction(self.capture_action)
        
        # Add toolbar to layout
        chat_layout.addWidget(toolbar)
        
        # Tab widget for chat and agent workspace
        self.tab_widget = QTabWidget()
        
        # Chat tab
        chat_tab = QWidget()
        chat_tab_layout = QVBoxLayout(chat_tab)
        
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
        chat_tab_layout.addWidget(self.chat_scroll_area)
        
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
        chat_tab_layout.addLayout(input_layout)
        
        # Add chat tab to tab widget
        self.tab_widget.addTab(chat_tab, "Chat")
        
        # Agent workspace tab (placeholder)
        workspace_tab = QWidget()
        workspace_layout = QVBoxLayout(workspace_tab)
        
        workspace_placeholder = QLabel("Agent workspace will be implemented here")
        workspace_layout.addWidget(workspace_placeholder)
        
        # Add agent workspace tab to tab widget
        self.tab_widget.addTab(workspace_tab, "Agent Workspace")
        
        # Add tab widget to layout
        chat_layout.addWidget(self.tab_widget)
        
        # Add widgets to splitter
        self.splitter.addWidget(sidebar_widget)
        self.splitter.addWidget(chat_widget)
        
        # Set initial splitter sizes (30% sidebar, 70% chat)
        self.splitter.setSizes([300, 700])
        
        # Set central widget
        self.setCentralWidget(central_widget)
        
        # Update UI if no backend is available
        if not self.current_backend:
            self.send_button.setEnabled(False)
            self.clear_button.setEnabled(False)
            self.message_input.setEnabled(False)
            
            # Display error message
            error_widget = QWidget()
            error_layout = QVBoxLayout(error_widget)
            error_label = QLabel("No AI backend available. Please check your settings.")
            error_label.setStyleSheet("color: red; font-weight: bold;")
            error_layout.addWidget(error_label)
            
            # Add backend configuration options
            self.setup_backend_config_widget(error_layout)
            
            error_layout.addStretch(1)
            
            self.chat_layout.addWidget(error_widget)
        else:
            # Display welcome message
            self.display_message("system", f"Welcome to the Unified AI Interface! Using {self.backend_type.capitalize()} backend.")
        
        # Update conversation list if available
        self.update_conversation_list()

    def setup_backend_config_widget(self, parent_layout):
        """Set up the backend configuration widget for when no backend is available"""
        backend_config = QGroupBox("Backend Configuration")
        config_layout = QVBoxLayout(backend_config)
        
        # OpenAI configuration
        openai_group = QGroupBox("OpenAI")
        openai_layout = QVBoxLayout(openai_group)
        
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
        
        openai_layout.addLayout(api_key_layout)
        config_layout.addWidget(openai_group)
        
        # Ollama configuration
        ollama_group = QGroupBox("Ollama")
        ollama_layout = QVBoxLayout(ollama_group)
        
        server_layout = QHBoxLayout()
        server_label = QLabel("Server URL:")
        self.server_input = QLineEdit("http://localhost:11434")
        server_layout.addWidget(server_label)
        server_layout.addWidget(self.server_input)
        
        test_ollama_button = QPushButton("Test Connection")
        test_ollama_button.clicked.connect(self.test_ollama_connection)
        server_layout.addWidget(test_ollama_button)
        
        ollama_layout.addLayout(server_layout)
        config_layout.addWidget(ollama_group)
        
        parent_layout.addWidget(backend_config)

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

    def update_ui_for_backends(self):
        """Update UI components based on available backends"""
        # Update OpenAI components
        openai_available = False
        if self.openai_backend and self.openai_backend.is_available():
            openai_available = True
            
            # Update model dropdown if needed
            models = self.openai_backend.get_available_models()
            if models:
                self.openai_model_combo.clear()
                # Filter for appropriate models
                chat_models = [m for m in models if 'gpt' in m.lower()]
                self.openai_model_combo.addItems(chat_models)
                
                # Set default to gpt-4o-mini if available, otherwise first in list
                default_model = "gpt-4o-mini"
                if default_model in chat_models:
                    self.openai_model_combo.setCurrentText(default_model)
                elif chat_models:
                    self.openai_model_combo.setCurrentText(chat_models[0])
        
        # Update Ollama components
        ollama_available = False
        if self.ollama_backend and self.ollama_backend.is_available():
            ollama_available = True
            
            # Update model dropdown if needed
            models = self.ollama_backend.list_models()
            if models:
                self.ollama_model_combo.clear()
                self.ollama_model_combo.addItems(models)
                
                # Set current model
                current_model = self.ollama_backend.model
                if current_model in models:
                    self.ollama_model_combo.setCurrentText(current_model)
                elif models:
                    self.ollama_model_combo.setCurrentText(models[0])
        
        # Update backend radio buttons
        self.openai_radio.setEnabled(openai_available)
        self.ollama_radio.setEnabled(ollama_available)
        
        # Show/hide model selections based on current backend
        show_openai = self.backend_type == "openai" and openai_available
        show_ollama = self.backend_type == "ollama" and ollama_available
        
        for i in range(self.openai_model_layout.count()):
            widget = self.openai_model_layout.itemAt(i).widget()
            if widget:
                widget.setVisible(show_openai)
        
        for i in range(self.ollama_model_layout.count()):
            widget = self.ollama_model_layout.itemAt(i).widget()
            if widget:
                widget.setVisible(show_ollama)

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
            
        # Check if backend is available
        if not self.current_backend:
            self.display_message("system", "No AI backend available. Please check your settings.")
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
        
        # Check for agent selection
        agent_id = self.agent_combo.currentData()
        
        # Enhance prompt with memory if available and RAG is enabled
        enhanced_message = message_text
        if self.memory_integration and self.rag_action.isChecked():
            enhanced_message = self.memory_integration.enhance_prompt_with_memory(message_text)
        
        # Check if we should use an agent
        if agent_id != "default" and AGENTS_AVAILABLE and self.agent_manager:
            # Remove the temporary thinking widget
            self.chat_layout.removeWidget(assistant_widget)
            assistant_widget.deleteLater()
            
            # Add empty assistant message for streaming
            self.display_message("assistant", "")
            
            # Run agent in a separate thread
            self.agent_thread = AgentThread(
                self.agent_manager,
                agent_id,
                enhanced_message,
                {
                    "conversation_history": self.memory_integration.get_conversation_history() if self.memory_integration else None
                }
            )
            self.agent_thread.response_ready.connect(self.handle_response)
            self.agent_thread.start()
            
        else:
            # Process with regular backend
            threading_method = "streaming" if self.use_streaming else "threading"
            
            if threading_method == "streaming":
                # Remove the temporary thinking widget
                self.chat_layout.removeWidget(assistant_widget)
                assistant_widget.deleteLater()
                
                # Add empty assistant message for streaming
                self.display_message("assistant", "")
                
                # Start streaming in a separate thread
                self.stream_thread = StreamingThread(
                    self.current_backend,
                    enhanced_message,
                    self.system_prompt,
                    self.memory_integration.get_conversation_history() if self.memory_integration else None
                )
                self.stream_thread.new_token.connect(self.stream_handler.new_token_signal)
                self.stream_thread.start()
            else:
                # Use regular threading
                self.message_thread = MessageThread(
                    self.current_backend,
                    enhanced_message,
                    self.system_prompt,
                    self.memory_integration.get_conversation_history() if self.memory_integration else None
                )
                self.message_thread.response_ready.connect(self.handle_response)
                self.message_thread.start()

    def handle_response(self, response):
        # Find and remove the temporary thinking widget if it exists
        for i in range(self.chat_layout.count()):
            item = self.chat_layout.itemAt(i)
            if item and item.widget():
                widget = item.widget()
                message_layout = widget.layout()
                if message_layout and message_layout.count() > 1:
                    content_label = message_layout.itemAt(1).widget()
                    if isinstance(content_label, QLabel) and content_label.text() == "Thinking...":
                        self.chat_layout.removeWidget(widget)
                        widget.deleteLater()
                        break
        
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

    def switch_backend(self, backend_type):
        # Check if the backend is available
        if backend_type == "openai" and (not self.openai_backend or not self.openai_backend.is_available()):
            QMessageBox.warning(self, "Backend Unavailable", "OpenAI backend is not available. Please configure it in settings.")
            self.ollama_radio.setChecked(True)
            return
        
        if backend_type == "ollama" and (not self.ollama_backend or not self.ollama_backend.is_available()):
            QMessageBox.warning(self, "Backend Unavailable", "Ollama backend is not available. Please configure it in settings.")
            self.openai_radio.setChecked(True)
            return
        
        # Switch backend
        self.backend_type = backend_type
        
        if backend_type == "openai":
            self.current_backend = self.openai_backend
        elif backend_type == "ollama":
            self.current_backend = self.ollama_backend
        
        # Update memory integration if needed
        if self.memory_integration and backend_type == "openai" and self.openai_backend:
            self.memory_integration.set_api_key(self.openai_backend.api_key)
        
        # Update agent manager if available
        if AGENTS_AVAILABLE and self.agent_manager:
            self.agent_manager.set_llm_backend(self.current_backend)
        
        # Update UI
        self.update_ui_for_backends()
        
        # Save settings
        self.save_settings()
        
        # Display message
        self.display_message("system", f"Switched to {backend_type.capitalize()} backend")

    def toggle_rag(self, enabled):
        # Toggle RAG functionality
        if enabled:
            self.display_message("system", "RAG enabled - Responses will include relevant context from memory")
        else:
            self.display_message("system", "RAG disabled - Responses will not include additional context")

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

    def show_settings_dialog(self):
        # Create settings dialog
        dialog = QDialog(self)
        dialog.setWindowTitle("Settings")
        dialog.setMinimumWidth(600)
        
        layout = QVBoxLayout(dialog)
        
        # Create tab widget for settings
        settings_tabs = QTabWidget()
        
        # General settings tab
        general_tab = QWidget()
        general_layout = QVBoxLayout(general_tab)
        
        # System prompt
        system_prompt_layout = QVBoxLayout()
        system_prompt_label = QLabel("System Prompt:")
        self.settings_system_prompt = QTextEdit()
        self.settings_system_prompt.setPlaceholderText("Enter system prompt")
        self.settings_system_prompt.setText(self.system_prompt)
        self.settings_system_prompt.setMaximumHeight(100)
        system_prompt_layout.addWidget(system_prompt_label)
        system_prompt_layout.addWidget(self.settings_system_prompt)
        general_layout.addLayout(system_prompt_layout)
        
        # Advanced settings
        advanced_group = QGroupBox("Advanced Settings")
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
        
        general_layout.addWidget(advanced_group)
        general_layout.addStretch(1)
        
        # OpenAI settings tab
        openai_tab = QWidget()
        openai_layout = QVBoxLayout(openai_tab)
        
        # API Key
        api_key_layout = QHBoxLayout()
        api_key_label = QLabel("OpenAI API Key:")
        self.settings_api_key = QLineEdit()
        self.settings_api_key.setEchoMode(QLineEdit.Password)
        self.settings_api_key.setPlaceholderText("Enter your OpenAI API key")
        if self.openai_backend and self.openai_backend.api_key:
            self.settings_api_key.setText("*" * 12)  # Show masked key if present
        api_key_layout.addWidget(api_key_label)
        api_key_layout.addWidget(self.settings_api_key)
        openai_layout.addLayout(api_key_layout)
        
        # Base URL
        base_url_layout = QHBoxLayout()
        base_url_label = QLabel("API Base URL:")
        self.settings_base_url = QLineEdit()
        if self.openai_backend:
            self.settings_base_url.setText(self.openai_backend.base_url or "https://api.openai.com/v1")
        else:
            self.settings_base_url.setText("https://api.openai.com/v1")
        self.settings_base_url.setPlaceholderText("https://api.openai.com/v1")
        base_url_layout.addWidget(base_url_label)
        base_url_layout.addWidget(self.settings_base_url)
        openai_layout.addLayout(base_url_layout)
        
        # Default model
        default_model_layout = QHBoxLayout()
        default_model_label = QLabel("Default Model:")
        self.settings_default_model = QComboBox()
        self.settings_default_model.addItems(["gpt-4o-mini", "gpt-3.5-turbo", "gpt-4o"])
        if self.openai_backend:
            self.settings_default_model.setCurrentText(self.openai_backend.model or "gpt-4o-mini")
        default_model_layout.addWidget(default_model_label)
        default_model_layout.addWidget(self.settings_default_model)
        openai_layout.addLayout(default_model_layout)
        
        # Test connection button
        test_openai_button = QPushButton("Test Connection")
        test_openai_button.clicked.connect(self.test_openai_connection)
        openai_layout.addWidget(test_openai_button)
        
        openai_layout.addStretch(1)
        
        # Ollama settings tab
        ollama_tab = QWidget()
        ollama_layout = QVBoxLayout(ollama_tab)
        
        # Server URL
        server_url_layout = QHBoxLayout()
        server_url_label = QLabel("Ollama Server URL:")
        self.settings_server_url = QLineEdit()
        if self.ollama_backend:
            self.settings_server_url.setText(self.ollama_backend.server_url or "http://localhost:11434")
        else:
            self.settings_server_url.setText("http://localhost:11434")
        server_url_layout.addWidget(server_url_label)
        server_url_layout.addWidget(self.settings_server_url)
        ollama_layout.addLayout(server_url_layout)
        
        # Default model
        ollama_model_layout = QHBoxLayout()
        ollama_model_label = QLabel("Default Model:")
        self.settings_ollama_model = QComboBox()
        
        # Add default models
        default_ollama_models = ["llama3", "mistral", "phi3", "llama3:8b"]
        
        # Add models from Ollama if available
        if self.ollama_backend and self.ollama_backend.is_available():
            models = self.ollama_backend.list_models()
            if models:
                self.settings_ollama_model.clear()
                self.settings_ollama_model.addItems(models)
            else:
                self.settings_ollama_model.addItems(default_ollama_models)
        else:
            self.settings_ollama_model.addItems(default_ollama_models)
        
        # Set current model
        if self.ollama_backend:
            current_model = self.ollama_backend.model
            if current_model:
                self.settings_ollama_model.setCurrentText(current_model)
        
        ollama_model_layout.addWidget(ollama_model_label)
        ollama_model_layout.addWidget(self.settings_ollama_model)
        ollama_layout.addLayout(ollama_model_layout)
        
        # Test connection button
        test_ollama_button = QPushButton("Test Connection")
        test_ollama_button.clicked.connect(self.test_ollama_connection)
        ollama_layout.addWidget(test_ollama_button)
        
        # Pull model button
        pull_model_layout = QHBoxLayout()
        pull_model_label = QLabel("Pull Model:")
        self.pull_model_input = QLineEdit("llama3")
        pull_model_button = QPushButton("Pull")
        pull_model_button.clicked.connect(self.pull_ollama_model)
        pull_model_layout.addWidget(pull_model_label)
        pull_model_layout.addWidget(self.pull_model_input)
        pull_model_layout.addWidget(pull_model_button)
        ollama_layout.addLayout(pull_model_layout)
        
        ollama_layout.addStretch(1)
        
        # Memory settings tab
        memory_tab = QWidget()
        memory_layout = QVBoxLayout(memory_tab)
        
        # Vector database settings
        vector_db_group = QGroupBox("Vector Database")
        vector_db_layout = QVBoxLayout(vector_db_group)
        
        # Database type
        db_type_layout = QHBoxLayout()
        db_type_label = QLabel("Database Type:")
        self.settings_db_type = QComboBox()
        self.settings_db_type.addItems(["Qdrant", "ChromaDB", "JSON"])
        db_type_layout.addWidget(db_type_label)
        db_type_layout.addWidget(self.settings_db_type)
        vector_db_layout.addLayout(db_type_layout)
        
        # Database URL
        db_url_layout = QHBoxLayout()
        db_url_label = QLabel("Database URL:")
        self.settings_db_url = QLineEdit("http://localhost:6333")
        db_url_layout.addWidget(db_url_label)
        db_url_layout.addWidget(self.settings_db_url)
        vector_db_layout.addLayout(db_url_layout)
        
        # Enable cloud toggle
        self.settings_cloud_toggle = QCheckBox("Use Cloud Instance")
        vector_db_layout.addWidget(self.settings_cloud_toggle)
        
        memory_layout.addWidget(vector_db_group)
        
        # Embedding settings
        embedding_group = QGroupBox("Embeddings")
        embedding_layout = QVBoxLayout(embedding_group)
        
        # Embedding model
        embedding_model_layout = QHBoxLayout()
        embedding_model_label = QLabel("Embedding Model:")
        self.settings_embedding_model = QComboBox()
        self.settings_embedding_model.addItems([
            "text-embedding-3-small", 
            "text-embedding-3-large", 
            "text-embedding-ada-002"
        ])
        embedding_model_layout.addWidget(embedding_model_label)
        embedding_model_layout.addWidget(self.settings_embedding_model)
        embedding_layout.addLayout(embedding_model_layout)
        
        memory_layout.addWidget(embedding_group)
        memory_layout.addStretch(1)
        
        # Add tabs to settings
        settings_tabs.addTab(general_tab, "General")
        settings_tabs.addTab(openai_tab, "OpenAI")
        settings_tabs.addTab(ollama_tab, "Ollama")
        settings_tabs.addTab(memory_tab, "Memory")
        
        layout.addWidget(settings_tabs)
        
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

    def test_openai_connection(self):
        # Get settings from dialog
        api_key = self.settings_api_key.text()
        if api_key.startswith("*"):  # Masked key
            if self.openai_backend:
                api_key = self.openai_backend.api_key
            else:
                QMessageBox.warning(self, "API Key Required", "Please enter your OpenAI API key")
                return
                
        base_url = self.settings_base_url.text()
        
        # Create test backend
        test_backend = OpenAIBackend(api_key=api_key, base_url=base_url)
        
        # Test connection
        if test_backend.test_connection():
            QMessageBox.information(self, "Connection Successful", "Successfully connected to OpenAI API")
        else:
            QMessageBox.critical(self, "Connection Failed", "Failed to connect to OpenAI API. Please check your API key and settings.")

    def test_ollama_connection(self):
        # Get settings from dialog (if in settings) or from the error widget
        if hasattr(self, "settings_server_url"):
            server_url = self.settings_server_url.text()
        elif hasattr(self, "server_input"):
            server_url = self.server_input.text()
        else:
            server_url = "http://localhost:11434"
            
        # Create test backend
        test_backend = OllamaBackend(server_url=server_url)
        
        # Test connection
        if test_backend.test_connection():
            QMessageBox.information(self, "Connection Successful", "Successfully connected to Ollama server")
            
            # Get available models
            models = test_backend.list_models()
            if models:
                model_list = "\n".join(models)
                QMessageBox.information(self, "Available Models", f"Available models:\n{model_list}")
        else:
            QMessageBox.critical(self, "Connection Failed", "Failed to connect to Ollama server. Please check the server URL and ensure Ollama is running.")

    def pull_ollama_model(self):
        # Get model name
        model_name = self.pull_model_input.text()
        if not model_name:
            QMessageBox.warning(self, "Model Required", "Please enter a model name")
            return
            
        # Get server URL
        server_url = self.settings_server_url.text()
        
        # Create Ollama backend
        ollama = OllamaBackend(server_url=server_url)
        
        # Show progress dialog
        progress_dialog = QMessageBox(self)
        progress_dialog.setWindowTitle("Pulling Model")
        progress_dialog.setText(f"Pulling model {model_name}...\nThis may take a while depending on the model size.")
        progress_dialog.setStandardButtons(QMessageBox.NoButton)
        progress_dialog.show()
        
        # Pull model in a separate thread
        self.pull_thread = PullModelThread(ollama, model_name)
        self.pull_thread.finished.connect(lambda: self.handle_pull_finished(progress_dialog))
        self.pull_thread.start()

    def handle_pull_finished(self, dialog):
        # Close progress dialog
        dialog.close()
        
        # Show result
        if self.pull_thread.success:
            QMessageBox.information(self, "Model Pulled", f"Successfully pulled model {self.pull_thread.model_name}")
            
            # Refresh model list
            if self.ollama_backend:
                models = self.ollama_backend.list_models()
                if models:
                    self.settings_ollama_model.clear()
                    self.settings_ollama_model.addItems(models)
                    
                    # Select the pulled model
                    if self.pull_thread.model_name in models:
                        self.settings_ollama_model.setCurrentText(self.pull_thread.model_name)
        else:
            QMessageBox.critical(self, "Pull Failed", f"Failed to pull model {self.pull_thread.model_name}:\n{self.pull_thread.error}")

    def save_settings_dialog(self, dialog):
        # Save OpenAI settings
        api_key = self.settings_api_key.text()
        if api_key and not api_key.startswith("*"):
            # Initialize OpenAI backend if needed
            if not self.openai_backend:
                self.openai_backend = OpenAIBackend(api_key=api_key)
            else:
                self.openai_backend.save_api_key(api_key)
                
            # Update memory integration with new API key
            if self.memory_integration:
                self.memory_integration.set_api_key(api_key)
        
        # Save base URL
        base_url = self.settings_base_url.text()
        if self.openai_backend and base_url:
            self.openai_backend.base_url = base_url
        
        # Save OpenAI model
        default_model = self.settings_default_model.currentText()
        if self.openai_backend and default_model:
            self.openai_backend.model = default_model
        
        # Save Ollama settings
        server_url = self.settings_server_url.text()
        if server_url:
            # Initialize Ollama backend if needed
            if not self.ollama_backend:
                self.ollama_backend = OllamaBackend(server_url=server_url)
            else:
                self.ollama_backend.server_url = server_url
        
        # Save Ollama model
        ollama_model = self.settings_ollama_model.currentText()
        if self.ollama_backend and ollama_model:
            self.ollama_backend.model = ollama_model
        
        # Save general settings
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
        
        # Re-initialize backends and update UI
        self._initialize_backends()
        self.update_ui_for_backends()
        
        # Update agent manager with new backend
        if AGENTS_AVAILABLE and self.agent_manager:
            self.agent_manager.set_llm_backend(self.current_backend)
        
        # Close dialog
        dialog.accept()
        
        # Show success message
        self.display_message("system", "Settings saved successfully")

    def save_api_key(self):
        # Get API key from error widget
        api_key = self.api_key_input.text()
        if not api_key:
            return
            
        # Initialize OpenAI backend
        try:
            if not self.openai_backend:
                self.openai_backend = OpenAIBackend(api_key=api_key)
            else:
                self.openai_backend.save_api_key(api_key)
                
            # Test connection
            if self.openai_backend.test_connection():
                # Enable OpenAI as current backend
                self.current_backend = self.openai_backend
                self.backend_type = "openai"
                
                # Initialize memory integration if needed
                if MEMORY_AVAILABLE and not self.memory_integration:
                    self.memory_integration = MemoryIntegration(api_key=api_key)
                elif self.memory_integration:
                    self.memory_integration.set_api_key(api_key)
                
                # Update agent manager with new backend
                if AGENTS_AVAILABLE and self.agent_manager:
                    self.agent_manager.set_llm_backend(self.current_backend)
                
                # Save settings
                self.save_settings()
                
                # Update UI
                self.update_ui_for_backends()
                
                # Clear error widget and enable UI
                self.clear_chat()
                self.send_button.setEnabled(True)
                self.clear_button.setEnabled(True)
                self.message_input.setEnabled(True)
                
                # Display success message
                self.display_message("system", "OpenAI API connected successfully! You can start chatting.")
                
                # Update conversation list and memory status
                self.update_conversation_list()
                self.update_memory_status()
            else:
                QMessageBox.critical(self, "API Error", "Could not connect to OpenAI API. Please check your API key.")
        except Exception as e:
            QMessageBox.critical(self, "API Error", f"Error initializing OpenAI API: {str(e)}")

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
        self.settings.setValue("backendType", self.backend_type)
        
        # Save backend-specific settings
        if self.openai_backend:
            self.settings.setValue("openaiModel", self.openai_backend.model)
            self.settings.setValue("openaiBaseUrl", self.openai_backend.base_url)
        
        if self.ollama_backend:
            self.settings.setValue("ollamaModel", self.ollama_backend.model)
            self.settings.setValue("ollamaServerUrl", self.ollama_backend.server_url)
        
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
        self.backend_type = self.settings.value("backendType", "openai")
        
        # Load backend-specific settings (will be applied when initializing backends)
        self.openai_model = self.settings.value("openaiModel", "gpt-4o-mini")
        self.openai_base_url = self.settings.value("openaiBaseUrl", "https://api.openai.com/v1")
        self.ollama_model = self.settings.value("ollamaModel", "llama3")
        self.ollama_server_url = self.settings.value("ollamaServerUrl", "http://localhost:11434")

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
class MessageThread(QThread):
    response_ready = pyqtSignal(str)
    
    def __init__(self, backend, message, system_prompt, conversation_history=None):
        super().__init__()
        self.backend = backend
        self.message = message
        self.system_prompt = system_prompt
        self.conversation_history = conversation_history
    
    def run(self):
        try:
            response = self.backend.generate(
                prompt=self.message,
                system_prompt=self.system_prompt,
                conversation_history=self.conversation_history
            )
            self.response_ready.emit(response)
        except Exception as e:
            logger.error(f"Error in message thread: {e}")
            self.response_ready.emit(f"Error: {str(e)}")


class StreamingThread(QThread):
    new_token = pyqtSignal(str)
    
    def __init__(self, backend, message, system_prompt, conversation_history=None):
        super().__init__()
        self.backend = backend
        self.message = message
        self.system_prompt = system_prompt
        self.conversation_history = conversation_history
    
    def run(self):
        try:
            # Get streaming response
            for token in self.backend.stream(
                prompt=self.message,
                system_prompt=self.system_prompt,
                conversation_history=self.conversation_history
            ):
                self.new_token.emit(token)
                
        except Exception as e:
            logger.error(f"Error in streaming thread: {e}")
            self.new_token.emit(f"\nError: {str(e)}")


class AgentThread(QThread):
    response_ready = pyqtSignal(str)
    
    def __init__(self, agent_manager, agent_id, message, context=None):
        super().__init__()
        self.agent_manager = agent_manager
        self.agent_id = agent_id
        self.message = message
        self.context = context or {}
    
    def run(self):
        try:
            # Create event loop for this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # Run agent
            response = loop.run_until_complete(
                self.agent_manager.run_agent(
                    agent_id=self.agent_id,
                    user_input=self.message,
                    context=self.context
                )
            )
            
            # Close loop
            loop.close()
            
            self.response_ready.emit(response)
        except Exception as e:
            logger.error(f"Error in agent thread: {e}")
            self.response_ready.emit(f"Error running agent: {str(e)}")


class PullModelThread(QThread):
    def __init__(self, ollama_backend, model_name):
        super().__init__()
        self.ollama_backend = ollama_backend
        self.model_name = model_name
        self.success = False
        self.error = ""
    
    def run(self):
        try:
            # Pull model
            self.success = self.ollama_backend.pull_model(self.model_name)
        except Exception as e:
            self.success = False
            self.error = str(e)


if __name__ == "__main__":
    # Create the application
    app = QApplication(sys.argv)
    app.setApplicationName("KDE AI Interface - Unified")
    
    # Create and show the main window
    main_window = MainWindow()
    main_window.show()
    
    # Start the application event loop
    sys.exit(app.exec_())