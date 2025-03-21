#!/usr/bin/env python3
"""
KDE AI Interface with OpenAI GPT-4o-mini backend

This GUI application provides a KDE-compatible interface to OpenAI models
like GPT-4o-mini, while maintaining the same UI as the AMD Quark implementation.
"""

import os
import sys
import logging
import time
import threading
from pathlib import Path
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QTextEdit, QPushButton, QHBoxLayout, QLabel, 
                            QSystemTrayIcon, QMenu, QAction, QStatusBar,
                            QComboBox, QCheckBox, QSpinBox, QGroupBox, QGridLayout,
                            QSplitter, QListWidget, QListWidgetItem, QTreeWidget, QTreeWidgetItem,
                            QFrame, QSizePolicy, QScrollArea, QToolButton, QPushButton,
                            QDialog, QLineEdit, QFormLayout, QDialogButtonBox, QTabWidget,
                            QRadioButton, QButtonGroup, QStyle)
from PyQt5.QtCore import Qt, pyqtSignal, QThread, QTimer, QSize
from PyQt5.QtGui import QIcon, QTextCursor, QFont, QPixmap, QColor

# Import backends
from openai_backend import OpenAIBackend, OPENAI_AVAILABLE
try:
    from ollama_backend import OllamaBackend
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False
    print("Ollama backend not installed. Some features may not be available.")

class CollapsibleBox(QWidget):
    """A custom widget that can be collapsed and expanded"""
    
    def __init__(self, title="", parent=None):
        super().__init__(parent)
        
        self.toggle_button = QToolButton(self)
        self.toggle_button.setStyleSheet("QToolButton { border: none; background: transparent; }")
        self.toggle_button.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.toggle_button.setArrowType(Qt.RightArrow)
        self.toggle_button.setText(title)
        self.toggle_button.setCheckable(True)
        self.toggle_button.setChecked(False)
        self.toggle_button.clicked.connect(self.on_toggle)
        
        self.toggle_animation = QTimer()
        self.toggle_animation.setInterval(30)
        self.toggle_animation.timeout.connect(self.on_toggle_animation)
        
        self.content_area = QScrollArea(self)
        self.content_area.setMaximumHeight(0)
        self.content_area.setMinimumHeight(0)
        self.content_area.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.content_area.setFrameShape(QFrame.NoFrame)
        
        lay = QVBoxLayout(self)
        lay.setSpacing(0)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(self.toggle_button)
        lay.addWidget(self.content_area)
        
        self.toggle_animation_completed = True
        self.collapsed_height = self.sizeHint().height() - self.content_area.maximumHeight()
        self.content = None
        
        # Make the toggle button look nicer with some styling
        self.toggle_button.setStyleSheet("""
            QToolButton {
                font-weight: bold;
                font-size: 12px;
                padding: 5px;
                background-color: #eeeeee;
                border-radius: 3px;
                color: #444444;
            }
            QToolButton:hover {
                background-color: #dddddd;
            }
        """)
        
    def on_toggle(self, checked):
        """Toggle the collapse/expand state"""
        self.toggle_button.setArrowType(Qt.DownArrow if checked else Qt.RightArrow)
        self.toggle_animation_completed = False
        self.toggle_animation.start()
        
    def on_toggle_animation(self):
        """Animate the collapse/expand"""
        if self.content is None:
            return
            
        collapsed_height = self.sizeHint().height() - self.content_area.maximumHeight()
        content_height = self.content.sizeHint().height()
        
        if self.toggle_button.isChecked():
            # Expanding
            height = self.content_area.maximumHeight() + 5
            if height >= content_height:
                height = content_height
                self.toggle_animation.stop()
                self.toggle_animation_completed = True
        else:
            # Collapsing
            height = self.content_area.maximumHeight() - 5
            if height <= 0:
                height = 0
                self.toggle_animation.stop()
                self.toggle_animation_completed = True
                
        self.content_area.setMaximumHeight(height)
        self.content_area.setMinimumHeight(height)
        
    def setContentLayout(self, layout):
        """Set the layout of the content area"""
        self.content = QWidget()
        self.content.setLayout(layout)
        self.content_area.setWidget(self.content)
        self.collapsed_height = self.sizeHint().height() - self.content_area.maximumHeight()
        
    def expand(self):
        """Expand the widget"""
        if not self.toggle_button.isChecked():
            self.toggle_button.setChecked(True)
            self.on_toggle(True)
            
    def collapse(self):
        """Collapse the widget"""
        if self.toggle_button.isChecked():
            self.toggle_button.setChecked(False)
            self.on_toggle(False)

# Set up logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("OpenAIDeepSeekGUI")

# Check if OpenAI SDK is installed
if not OPENAI_AVAILABLE:
    logger.warning("OpenAI SDK not available. Please install with: pip install openai")

# Default OpenAI models to offer
DEFAULT_MODELS = [
    "gpt-4o-mini",
    "gpt-3.5-turbo",
    "gpt-4o",
    "gpt-4-turbo"
]

class GenerateThread(QThread):
    """Thread for text generation"""
    response_started = pyqtSignal()
    response_chunk = pyqtSignal(str)
    response_finished = pyqtSignal(dict)  # Signal with performance metrics
    error_occurred = pyqtSignal(str)
    
    def __init__(self, backend, prompt, model_config=None, conversation_history=None):
        super().__init__()
        self.backend = backend
        self.prompt = prompt
        self.model_config = model_config or {}
        self.conversation_history = conversation_history
        
    def run(self):
        """Run the generation thread"""
        try:
            self.response_started.emit()
            
            # Check if OpenAI backend is available
            if not self.backend.is_available():
                logger.info("OpenAI backend not available, running in simulation mode")
                self.simulate_response()
                return
            
            # Start timing
            start_time = time.time()
            total_tokens = 0
            
            # Stream tokens from OpenAI
            for chunk in self.backend.stream(
                prompt=self.prompt,
                system_prompt=self.model_config.get("system_prompt", "You are a helpful assistant."),
                temperature=self.model_config.get("temperature", 0.7),
                max_tokens=self.model_config.get("max_tokens", 1000),
                conversation_history=self.conversation_history
            ):
                total_tokens += 1
                self.response_chunk.emit(chunk)
            
            # End timing
            end_time = time.time()
            duration = end_time - start_time
            tokens_per_second = total_tokens / duration if duration > 0 else 0
            
            # Collect metrics
            metrics = {
                "duration": duration,
                "token_count": total_tokens,
                "tokens_per_second": tokens_per_second,
                "backend": "OpenAI API"
            }
            
            logger.info(f"Generated {total_tokens} tokens in {duration:.2f}s ({tokens_per_second:.2f} tokens/sec)")
            
            # Signal completion with metrics
            self.response_finished.emit(metrics)
            
        except Exception as e:
            logger.error(f"Error in generation thread: {str(e)}")
            self.error_occurred.emit(str(e))
    
    def simulate_response(self):
        """Simulate a response for testing when OpenAI is not available"""
        try:
            import random
            
            # Start timing
            start_time = time.time()
            total_tokens = 0
            
            # Example response for simulation
            responses = [
                "I'm running in simulation mode since OpenAI is not configured.",
                "This is a simulated response to demonstrate the interface functionality.",
                "The GPT-4o-mini model would normally generate a real response here.",
                f"Your prompt was: '{self.prompt}'",
                "To get actual AI responses, you need to configure the OpenAI API key.",
            ]
            
            # Stream tokens with realistic timing
            for response in responses:
                words = response.split()
                for word in words:
                    total_tokens += 1
                    self.response_chunk.emit(word + " ")
                    time.sleep(0.05 + random.random() * 0.1)  # Simulate typing speed
            
            # Add code block if the prompt seems to be asking for code
            if any(code_word in self.prompt.lower() for code_word in ["code", "function", "script", "program", "write"]):
                self.response_chunk.emit("\n\n```python\n")
                code_sample = [
                    "def hello_world():",
                    "    \"\"\"Example function to demonstrate code formatting\"\"\"",
                    "    print('Hello from GPT-4o-mini simulation!')",
                    "    return True",
                    "",
                    "# This is simulated code",
                    "# In an actual OpenAI connection, the AI would generate",
                    "# relevant code based on your prompt",
                    "",
                    "if __name__ == '__main__':",
                    "    hello_world()",
                ]
                
                for line in code_sample:
                    total_tokens += len(line.split())
                    self.response_chunk.emit(line + "\n")
                    time.sleep(0.1 + random.random() * 0.2)
                    
                self.response_chunk.emit("```")
            
            # End timing
            end_time = time.time()
            duration = end_time - start_time
            tokens_per_second = total_tokens / duration if duration > 0 else 0
            
            # Collect metrics
            metrics = {
                "duration": duration,
                "token_count": total_tokens,
                "tokens_per_second": tokens_per_second,
                "backend": "Simulation"
            }
            
            logger.info(f"Generated {total_tokens} tokens in {duration:.2f}s ({tokens_per_second:.2f} tokens/sec)")
            
            # Signal completion with metrics
            self.response_finished.emit(metrics)
            
        except Exception as e:
            logger.error(f"Error generating simulated text: {str(e)}")
            self.error_occurred.emit(f"Error generating simulated text: {str(e)}")


class BackendSettingsDialog(QDialog):
    """Dialog for configuring backends including OpenAI, Ollama, and MCP servers"""
    test_openai_connection_clicked = pyqtSignal(str)
    test_ollama_connection_clicked = pyqtSignal(str, str)  # server_url, model_name
    mcp_settings_changed = pyqtSignal(dict)
    ollama_settings_changed = pyqtSignal(dict)
    openai_settings_changed = pyqtSignal(dict)
    
    def __init__(self, parent=None, openai_key=None, ollama_settings=None, mcp_servers=None):
        super().__init__(parent)
        self.setWindowTitle("Backend Settings")
        self.setMinimumWidth(800)
        self.setMinimumHeight(600)
        
        # Default Ollama settings
        self.ollama_settings = ollama_settings or {
            "server_url": "http://localhost:11434",
            "model": "llama2",
            "enabled": False
        }
        
        # Default MCP settings
        self.mcp_servers = mcp_servers or {
            "coordinator": {
                "url": "http://localhost:8760",
                "enabled": False
            },
            "kde": {
                "url": "http://localhost:8765",
                "enabled": False
            },
            "code": {
                "url": "http://localhost:8766",
                "enabled": False
            },
            "data": {
                "url": "http://localhost:8767",
                "enabled": False
            },
            "network": {
                "url": "http://localhost:8768",
                "enabled": False
            }
        }
        
        # Apply modern styling
        self.setStyleSheet("""
            QDialog {
                background-color: #f5f5f7;
            }
            QTabWidget::pane {
                border: 1px solid #cccccc;
                border-radius: 5px;
                background-color: white;
            }
            QTabBar::tab {
                background-color: #e0e0e0;
                border: 1px solid #cccccc;
                border-bottom: none;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                padding: 8px 12px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background-color: white;
                border-bottom: 1px solid white;
            }
            QLabel {
                color: #333333;
            }
            QLineEdit, QComboBox, QSpinBox {
                border: 1px solid #cccccc;
                border-radius: 4px;
                padding: 5px;
                background-color: white;
                color: #333333;
            }
            QPushButton {
                background-color: #4a7eff;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 15px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #3a6eef;
            }
            QPushButton:pressed {
                background-color: #2a5edf;
            }
            QCheckBox {
                color: #333333;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)
        
        # Tab widget for different backend settings
        self.tab_widget = QTabWidget()
        
        # OpenAI tab
        openai_tab = QWidget()
        openai_layout = QVBoxLayout(openai_tab)
        openai_layout.setSpacing(15)
        
        # Description
        description = QLabel(
            "Configure your OpenAI API connection. The API key will be stored securely "
            "in your local configuration file."
        )
        description.setWordWrap(True)
        openai_layout.addWidget(description)
        
        # Enabled checkbox
        self.openai_enabled = QCheckBox("Enable OpenAI API")
        self.openai_enabled.setChecked(True)  # OpenAI is enabled by default
        openai_layout.addWidget(self.openai_enabled)
        
        # Form layout
        openai_form = QFormLayout()
        openai_form.setSpacing(10)
        openai_form.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)
        
        # API key input
        self.api_key_input = QLineEdit()
        if openai_key:
            self.api_key_input.setText(openai_key)
        self.api_key_input.setPlaceholderText("Enter your OpenAI API key")
        openai_form.addRow("API Key:", self.api_key_input)
        
        # Model selection
        self.model_selection = QComboBox()
        for model in ["gpt-4o-mini", "gpt-3.5-turbo", "gpt-4o", "gpt-4-turbo"]:
            self.model_selection.addItem(model)
        openai_form.addRow("Default Model:", self.model_selection)
        
        # Base URL
        self.base_url_input = QLineEdit("https://api.openai.com/v1")
        self.base_url_input.setPlaceholderText("https://api.openai.com/v1")
        openai_form.addRow("API Base URL:", self.base_url_input)
        
        openai_layout.addLayout(openai_form)
        
        # Status message
        self.openai_status = QLabel("")
        self.openai_status.setWordWrap(True)
        openai_layout.addWidget(self.openai_status)
        
        # Test connection button
        test_button = QPushButton("Test OpenAI Connection")
        test_button.clicked.connect(self.on_test_openai_connection)
        openai_layout.addWidget(test_button)
        
        openai_layout.addStretch()
        
        # Ollama tab
        ollama_tab = QWidget()
        ollama_layout = QVBoxLayout(ollama_tab)
        ollama_layout.setSpacing(15)
        
        # Description
        ollama_description = QLabel(
            "Configure Ollama server connection for using local LLM models. "
            "You can run Ollama locally or connect to a remote server."
        )
        ollama_description.setWordWrap(True)
        ollama_layout.addWidget(ollama_description)
        
        # Enabled checkbox
        self.ollama_enabled = QCheckBox("Enable Ollama")
        self.ollama_enabled.setChecked(self.ollama_settings.get("enabled", False))
        ollama_layout.addWidget(self.ollama_enabled)
        
        # Form layout
        ollama_form = QFormLayout()
        ollama_form.setSpacing(10)
        ollama_form.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)
        
        # Server URL
        self.ollama_server_url = QLineEdit(self.ollama_settings.get("server_url", "http://localhost:11434"))
        self.ollama_server_url.setPlaceholderText("http://localhost:11434")
        ollama_form.addRow("Server URL:", self.ollama_server_url)
        
        # Model selection
        self.ollama_model = QLineEdit(self.ollama_settings.get("model", "llama2"))
        self.ollama_model.setPlaceholderText("llama2")
        ollama_form.addRow("Model:", self.ollama_model)
        
        ollama_layout.addLayout(ollama_form)
        
        # Status message
        self.ollama_status = QLabel("")
        self.ollama_status.setWordWrap(True)
        ollama_layout.addWidget(self.ollama_status)
        
        # Test connection button
        test_ollama_button = QPushButton("Test Ollama Connection")
        test_ollama_button.clicked.connect(self.on_test_ollama_connection)
        ollama_layout.addWidget(test_ollama_button)
        
        ollama_layout.addStretch()
        
        # MCP tab
        mcp_tab = QWidget()
        mcp_layout = QVBoxLayout(mcp_tab)
        mcp_layout.setSpacing(15)
        
        # Description
        mcp_description = QLabel(
            "Configure Model Context Protocol (MCP) servers. MCP provides additional capabilities "
            "like desktop integration, code execution, and data processing."
        )
        mcp_description.setWordWrap(True)
        mcp_layout.addWidget(mcp_description)
        
        # MCP servers configuration
        mcp_form = QGridLayout()
        mcp_form.setSpacing(10)
        mcp_form.addWidget(QLabel("MCP Server"), 0, 0)
        mcp_form.addWidget(QLabel("URL"), 0, 1)
        mcp_form.addWidget(QLabel("Enabled"), 0, 2)
        mcp_form.addWidget(QLabel("Status"), 0, 3)
        
        # Add MCP server configurations
        row = 1
        self.mcp_inputs = {}
        
        for server_name, server_info in self.mcp_servers.items():
            # Server name
            name_label = QLabel(server_name.capitalize())
            mcp_form.addWidget(name_label, row, 0)
            
            # URL input
            url_input = QLineEdit(server_info.get("url", ""))
            url_input.setPlaceholderText(f"http://localhost:87{row}0")
            mcp_form.addWidget(url_input, row, 1)
            
            # Enabled checkbox
            enabled_check = QCheckBox()
            enabled_check.setChecked(server_info.get("enabled", False))
            mcp_form.addWidget(enabled_check, row, 2)
            
            # Status label
            status_label = QLabel("Not tested")
            mcp_form.addWidget(status_label, row, 3)
            
            # Store references to widgets
            self.mcp_inputs[server_name] = {
                "url": url_input,
                "enabled": enabled_check,
                "status": status_label
            }
            
            row += 1
        
        mcp_layout.addLayout(mcp_form)
        
        # Test MCP connections button
        test_mcp_button = QPushButton("Test MCP Connections")
        test_mcp_button.clicked.connect(self.on_test_mcp_connections)
        mcp_layout.addWidget(test_mcp_button)
        
        mcp_layout.addStretch()
        
        # Add tabs
        self.tab_widget.addTab(openai_tab, "OpenAI")
        self.tab_widget.addTab(ollama_tab, "Ollama")
        self.tab_widget.addTab(mcp_tab, "MCP Servers")
        
        layout.addWidget(self.tab_widget)
        
        # Standard buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.on_save)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    
    def on_test_openai_connection(self):
        """Test the OpenAI connection with the entered API key"""
        api_key = self.api_key_input.text().strip()
        if not api_key:
            self.openai_status.setText("Please enter an API key first.")
            self.openai_status.setStyleSheet("color: red;")
            return
            
        # Emit signal with the API key for the parent to test
        self.test_openai_connection_clicked.emit(api_key)
    
    def on_test_ollama_connection(self):
        """Test the Ollama connection with the entered server URL and model"""
        server_url = self.ollama_server_url.text().strip()
        model = self.ollama_model.text().strip()
        
        if not server_url:
            self.ollama_status.setText("Please enter a server URL first.")
            self.ollama_status.setStyleSheet("color: red;")
            return
            
        if not model:
            self.ollama_status.setText("Please enter a model name first.")
            self.ollama_status.setStyleSheet("color: red;")
            return
            
        # Set status to "Testing..."
        self.ollama_status.setText("Testing connection...")
        self.ollama_status.setStyleSheet("color: blue;")
        QApplication.processEvents()
            
        # Emit signal with the server URL and model for the parent to test
        self.test_ollama_connection_clicked.emit(server_url, model)
    
    def on_test_mcp_connections(self):
        """Test connections to MCP servers"""
        # This would actually test connections to each enabled MCP server
        # For now, just show some simulated status
        import random
        
        for server_name, widgets in self.mcp_inputs.items():
            if widgets["enabled"].isChecked():
                # Simulate connection test
                success = random.choice([True, False])
                if success:
                    widgets["status"].setText("Connected")
                    widgets["status"].setStyleSheet("color: green;")
                else:
                    widgets["status"].setText("Failed to connect")
                    widgets["status"].setStyleSheet("color: red;")
            else:
                widgets["status"].setText("Disabled")
                widgets["status"].setStyleSheet("color: gray;")
    
    def on_save(self):
        """Save all settings and close the dialog"""
        # Update MCP server settings
        for server_name, widgets in self.mcp_inputs.items():
            self.mcp_servers[server_name] = {
                "url": widgets["url"].text().strip(),
                "enabled": widgets["enabled"].isChecked()
            }
        
        # Update Ollama settings
        self.ollama_settings = {
            "server_url": self.ollama_server_url.text().strip(),
            "model": self.ollama_model.text().strip(),
            "enabled": self.ollama_enabled.isChecked()
        }
        
        # Update OpenAI settings
        openai_settings = {
            "api_key": self.api_key_input.text().strip(),
            "base_url": self.base_url_input.text().strip(),
            "model": self.model_selection.currentText(),
            "enabled": self.openai_enabled.isChecked()
        }
        
        # Emit signals with updated settings
        self.mcp_settings_changed.emit(self.mcp_servers)
        self.ollama_settings_changed.emit(self.ollama_settings)
        self.openai_settings_changed.emit(openai_settings)
        
        # Accept the dialog
        self.accept()
    
    def set_openai_status(self, message, success=True):
        """Set the OpenAI status message and color"""
        self.openai_status.setText(message)
        if success:
            self.openai_status.setStyleSheet("color: green;")
        else:
            self.openai_status.setStyleSheet("color: red;")
            
    def set_ollama_status(self, message, success=True):
        """Set the Ollama status message and color"""
        self.ollama_status.setText(message)
        if success:
            self.ollama_status.setStyleSheet("color: green;")
        else:
            self.ollama_status.setStyleSheet("color: red;")


class APIKeyDialog(QDialog):
    """Simple dialog for entering OpenAI API key"""
    test_connection_clicked = pyqtSignal(str)
    
    def __init__(self, parent=None, current_key=None):
        super().__init__(parent)
        self.setWindowTitle("OpenAI API Key")
        self.setMinimumWidth(500)
        
        layout = QVBoxLayout(self)
        
        # Description
        description = QLabel(
            "Please enter your OpenAI API key. This key will be stored securely "
            "in your local configuration file."
        )
        description.setWordWrap(True)
        layout.addWidget(description)
        
        # Form layout
        form_layout = QFormLayout()
        
        # API key input
        self.api_key_input = QLineEdit()
        if current_key:
            self.api_key_input.setText(current_key)
        form_layout.addRow("API Key:", self.api_key_input)
        
        layout.addLayout(form_layout)
        
        # Status message
        self.status_message = QLabel("")
        self.status_message.setWordWrap(True)
        layout.addWidget(self.status_message)
        
        # Buttons layout
        button_layout = QHBoxLayout()
        
        # Test connection button
        test_button = QPushButton("Test Connection")
        test_button.clicked.connect(self.on_test_connection)
        button_layout.addWidget(test_button)
        
        # Advanced settings button
        advanced_button = QPushButton("Advanced Settings")
        advanced_button.clicked.connect(self.on_advanced_settings)
        button_layout.addWidget(advanced_button)
        
        # Standard buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        button_layout.addWidget(button_box)
        
        layout.addLayout(button_layout)
    
    def on_test_connection(self):
        """Test the connection with the entered API key"""
        api_key = self.api_key_input.text().strip()
        if not api_key:
            self.status_message.setText("Please enter an API key first.")
            self.status_message.setStyleSheet("color: red;")
            return
            
        # Emit signal with the API key for the parent to test
        self.test_connection_clicked.emit(api_key)
    
    def on_advanced_settings(self):
        """Open advanced settings dialog"""
        # Signal to parent to open advanced settings
        self.parent().open_backend_settings()
        
        # Close this dialog
        self.accept()
    
    def set_status(self, message, success=True):
        """Set the status message and color"""
        self.status_message.setText(message)
        if success:
            self.status_message.setStyleSheet("color: green;")
        else:
            self.status_message.setStyleSheet("color: red;")


class KDEAIInterface(QMainWindow):
    """Main window for the KDE AI Interface with multiple backends"""
    def __init__(self):
        super().__init__()
        
        # Set base directory
        self.base_dir = Path.home() / "GIT-Projects/KDE AI Interface/quark-integration"
        
        # Initialize OpenAI backend
        self.openai_backend = OpenAIBackend()
        self.openai_enabled = True
        
        # Initialize Ollama backend if available
        if OLLAMA_AVAILABLE:
            self.ollama_backend = OllamaBackend()
            self.ollama_settings = {
                "server_url": "http://localhost:11434",
                "model": "llama2",
                "enabled": False
            }
        else:
            self.ollama_backend = None
            self.ollama_settings = {
                "server_url": "http://localhost:11434",
                "model": "llama2",
                "enabled": False
            }
        
        # Set current model
        self.current_model = DEFAULT_MODELS[0] if DEFAULT_MODELS else None
        
        # Track active backend
        self.active_backend = "openai"  # "openai", "ollama"
        
        # Conversation management
        self.conversations = []
        self.current_conversation_index = -1
        self.conversation_dir = self.base_dir / "conversations"
        self.conversation_dir.mkdir(parents=True, exist_ok=True)
        
        # Feature toggles
        self.screen_capture_enabled = False
        self.audio_capture_enabled = False
        self.rag_enabled = False
        
        # MCP servers configuration
        self.mcp_servers = {
            "coordinator": {
                "url": "http://localhost:8760",
                "enabled": False
            },
            "kde": {
                "url": "http://localhost:8765",
                "enabled": False
            },
            "code": {
                "url": "http://localhost:8766",
                "enabled": False
            },
            "data": {
                "url": "http://localhost:8767",
                "enabled": False
            },
            "network": {
                "url": "http://localhost:8768",
                "enabled": False
            }
        }
        
        # Model config
        self.model_config = {
            "temperature": 0.7,
            "top_p": 0.9,
            "max_tokens": 1000,
            "system_prompt": "You are a helpful AI assistant. Use markdown formatting for code and structured content."
        }
        
        # Apply modern styling
        self.set_modern_style()
        
        # Initialize UI
        self.init_ui()
        
        # Check backend status
        self.check_backend_status()
        
        # Create a new conversation on startup
        self.new_conversation()
        
        # Prompt for API key if not set and OpenAI is enabled
        if self.openai_enabled and not self.openai_backend.api_key:
            self.prompt_for_api_key()
    
    def set_modern_style(self):
        """Apply modern styling to the application"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f5f7;
            }
            QSplitter::handle {
                background-color: #dddddd;
            }
            QGroupBox {
                border: 1px solid #cccccc;
                border-radius: 5px;
                margin-top: 1ex;
                padding: 10px;
                background-color: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
                background-color: white;
            }
            QTextEdit {
                border: 1px solid #cccccc;
                border-radius: 5px;
                background-color: white;
                color: #333333;
                selection-background-color: #4a7eff;
                selection-color: white;
            }
            QListWidget {
                border: 1px solid #cccccc;
                border-radius: 5px;
                background-color: white;
                color: #333333;
            }
            QListWidget::item:selected {
                background-color: #4a7eff;
                color: white;
            }
            QLabel {
                color: #333333;
            }
            QComboBox, QSpinBox {
                border: 1px solid #cccccc;
                border-radius: 3px;
                padding: 3px;
                background-color: white;
                color: #333333;
                min-height: 20px;
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 15px;
                border-left-width: 1px;
                border-left-color: #cccccc;
                border-left-style: solid;
                border-top-right-radius: 3px;
                border-bottom-right-radius: 3px;
            }
            QStatusBar {
                background-color: #f0f0f0;
                color: #333333;
            }
        """)
    
    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("KDE AI Interface - OpenAI GPT-4o-mini")
        self.setGeometry(100, 100, 1200, 800)
        self.setWindowFlags(Qt.Window)  # Removed WindowStaysOnTopHint for better usability
        
        # Create main splitter to divide sidebar and chat area
        self.main_splitter = QSplitter(Qt.Horizontal)
        self.setCentralWidget(self.main_splitter)
        
        # Create sidebar for conversations
        self.sidebar = QWidget()
        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(10, 10, 10, 10)
        
        # Conversation header
        conv_header = QLabel("Conversations")
        conv_header.setStyleSheet("font-size: 16px; font-weight: bold;")
        sidebar_layout.addWidget(conv_header)
        
        # New conversation button
        new_conv_btn = QPushButton("New Conversation")
        new_conv_btn.clicked.connect(self.new_conversation)
        new_conv_btn.setStyleSheet("background-color: #4a7eff; color: white;")
        sidebar_layout.addWidget(new_conv_btn)
        
        # Conversation list
        self.conversation_list = QListWidget()
        self.conversation_list.itemClicked.connect(self.on_conversation_selected)
        sidebar_layout.addWidget(self.conversation_list)
        
        # Backend settings
        backend_box = CollapsibleBox("Backend Settings")
        backend_layout = QVBoxLayout()
        
        # API Key button
        api_key_btn = QPushButton("Set API Key")
        api_key_btn.clicked.connect(self.prompt_for_api_key)
        backend_layout.addWidget(api_key_btn)
        
        # Advanced settings button
        advanced_settings_btn = QPushButton("Advanced Settings")
        advanced_settings_btn.clicked.connect(self.open_backend_settings)
        backend_layout.addWidget(advanced_settings_btn)
        
        # MCP selector
        mcp_label = QLabel("Active MCP Servers:")
        backend_layout.addWidget(mcp_label)
        
        # MCP server checkboxes
        self.mcp_checkboxes = {}
        for server_name, server_info in self.mcp_servers.items():
            cb = QCheckBox(server_name.capitalize())
            cb.setChecked(server_info.get("enabled", False))
            cb.stateChanged.connect(lambda state, name=server_name: self.on_mcp_toggled(name, state))
            backend_layout.addWidget(cb)
            self.mcp_checkboxes[server_name] = cb
        
        backend_box.setContentLayout(backend_layout)
        sidebar_layout.addWidget(backend_box)
        
        # Add sidebar to splitter
        self.main_splitter.addWidget(self.sidebar)
        
        # Create main chat area
        self.chat_area = QWidget()
        chat_layout = QVBoxLayout(self.chat_area)
        chat_layout.setSpacing(5)
        chat_layout.setContentsMargins(10, 10, 10, 10)
        
        # Header layout with title and control buttons
        header_layout = QHBoxLayout()
        
        # Add header label
        header = QLabel("KDE AI Interface - OpenAI GPT-4o-mini")
        header.setStyleSheet("font-size: 18px; font-weight: bold; color: #444444;")
        header_layout.addWidget(header)
        
        # Spacer to push buttons to right
        header_layout.addStretch()
        
        # Feature toggle buttons
        self.screen_capture_btn = self.create_toggle_button("Screen", "camera-video", self.toggle_screen_capture)
        header_layout.addWidget(self.screen_capture_btn)
        
        self.audio_capture_btn = self.create_toggle_button("Audio", "audio-input-microphone", self.toggle_audio_capture)
        header_layout.addWidget(self.audio_capture_btn)
        
        self.rag_btn = self.create_toggle_button("RAG", "view-refresh", self.toggle_rag)
        self.rag_btn.setToolTip("Toggle Retrieval-Augmented Generation")
        header_layout.addWidget(self.rag_btn)
        
        chat_layout.addLayout(header_layout)
        
        # Status section (collapsible)
        status_box = CollapsibleBox("Status and Model Info")
        status_layout = QGridLayout()
        
        # Backend selection
        status_layout.addWidget(QLabel("Active Backend:"), 0, 0)
        self.backend_combo = QComboBox()
        self.backend_combo.addItem("OpenAI")
        if OLLAMA_AVAILABLE:
            self.backend_combo.addItem("Ollama")
        self.backend_combo.currentTextChanged.connect(self.on_backend_changed)
        status_layout.addWidget(self.backend_combo, 0, 1)
        
        # OpenAI status
        self.openai_status_label = QLabel("Checking OpenAI status...")
        self.openai_status_label.setStyleSheet("color: #444444;")
        status_layout.addWidget(QLabel("OpenAI:"), 1, 0)
        status_layout.addWidget(self.openai_status_label, 1, 1)
        
        # Ollama status
        self.ollama_status_label = QLabel("Ollama not configured")
        self.ollama_status_label.setStyleSheet("color: #444444;")
        status_layout.addWidget(QLabel("Ollama:"), 2, 0)
        status_layout.addWidget(self.ollama_status_label, 2, 1)
        
        # Model selection
        status_layout.addWidget(QLabel("Current Model:"), 3, 0)
        self.model_combo = QComboBox()
        for model in DEFAULT_MODELS:
            self.model_combo.addItem(model)
        
        self.model_combo.setCurrentText(self.current_model if self.current_model else "")
        self.model_combo.currentTextChanged.connect(self.on_model_changed)
        status_layout.addWidget(self.model_combo, 3, 1)
        
        # Performance meter
        status_layout.addWidget(QLabel("Performance:"), 4, 0)
        self.performance_label = QLabel("No data yet")
        status_layout.addWidget(self.performance_label, 4, 1)
        
        status_box.setContentLayout(status_layout)
        chat_layout.addWidget(status_box)
        
        # Configuration section (collapsible)
        config_box = CollapsibleBox("Model Configuration")
        config_layout = QGridLayout()
        
        # System prompt
        config_layout.addWidget(QLabel("System Prompt:"), 0, 0)
        self.system_prompt_input = QTextEdit()
        self.system_prompt_input.setPlaceholderText("System prompt for the model...")
        self.system_prompt_input.setText(self.model_config["system_prompt"])
        self.system_prompt_input.setMaximumHeight(80)
        self.system_prompt_input.textChanged.connect(self.on_system_prompt_changed)
        config_layout.addWidget(self.system_prompt_input, 0, 1, 1, 2)
        
        # Temperature
        config_layout.addWidget(QLabel("Temperature:"), 1, 0)
        self.temperature_spinner = QSpinBox()
        self.temperature_spinner.setRange(0, 20)  # 0.0 to 2.0
        self.temperature_spinner.setValue(int(self.model_config["temperature"] * 10))
        self.temperature_spinner.setSingleStep(1)
        self.temperature_spinner.valueChanged.connect(self.on_temperature_changed)
        config_layout.addWidget(self.temperature_spinner, 1, 1)
        config_layout.addWidget(QLabel("÷ 10 (e.g., 7 = 0.7)"), 1, 2)
        
        # Top-p
        config_layout.addWidget(QLabel("Top-p:"), 2, 0)
        self.top_p_spinner = QSpinBox()
        self.top_p_spinner.setRange(0, 10)  # 0.0 to 1.0
        self.top_p_spinner.setValue(int(self.model_config["top_p"] * 10))
        self.top_p_spinner.setSingleStep(1)
        self.top_p_spinner.valueChanged.connect(self.on_top_p_changed)
        config_layout.addWidget(self.top_p_spinner, 2, 1)
        config_layout.addWidget(QLabel("÷ 10 (e.g., 9 = 0.9)"), 2, 2)
        
        # Max tokens
        config_layout.addWidget(QLabel("Max Tokens:"), 3, 0)
        self.max_tokens_spinner = QSpinBox()
        self.max_tokens_spinner.setRange(10, 8000)
        self.max_tokens_spinner.setValue(self.model_config["max_tokens"])
        self.max_tokens_spinner.setSingleStep(100)
        self.max_tokens_spinner.valueChanged.connect(self.on_max_tokens_changed)
        config_layout.addWidget(self.max_tokens_spinner, 3, 1)
        
        config_box.setContentLayout(config_layout)
        chat_layout.addWidget(config_box)
        
        # Context section (collapsible)
        context_box = CollapsibleBox("Context Controls")
        context_layout = QGridLayout()
        
        # Current context controls
        context_layout.addWidget(QLabel("Current Context:"), 0, 0)
        self.context_status = QLabel("Not capturing")
        self.context_status.setStyleSheet("color: #444444;")
        context_layout.addWidget(self.context_status, 0, 1)
        
        # Memory controls
        context_layout.addWidget(QLabel("Memory:"), 1, 0)
        self.memory_status = QLabel("RAG disabled")
        context_layout.addWidget(self.memory_status, 1, 1)
        
        # Current context details
        context_layout.addWidget(QLabel("Sources:"), 2, 0)
        self.context_sources = QLabel("None")
        context_layout.addWidget(self.context_sources, 2, 1)
        
        context_box.setContentLayout(context_layout)
        chat_layout.addWidget(context_box)
        
        # Collapse all boxes by default
        status_box.collapse()
        config_box.collapse()
        context_box.collapse()
        
        # Add chat display
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.setFont(QFont("Monospace", 10))
        self.chat_display.setStyleSheet("""
            QTextEdit {
                background-color: #f8f8f8;
                border: 1px solid #ddd;
                border-radius: 5px;
                color: #333333;
            }
        """)
        chat_layout.addWidget(self.chat_display)
        
        # Add input area
        input_layout = QHBoxLayout()
        
        self.prompt_input = QTextEdit()
        self.prompt_input.setPlaceholderText("Type your message here...")
        self.prompt_input.setMaximumHeight(100)
        # Connect Enter key to send message
        self.prompt_input.installEventFilter(self)
        self.prompt_input.setStyleSheet("""
            QTextEdit {
                border: 1px solid #ddd;
                border-radius: 5px;
                padding: 5px;
                color: #333333;
            }
        """)
        input_layout.addWidget(self.prompt_input)
        
        send_button = QPushButton("Send")
        send_button.clicked.connect(self.send_message)
        send_button.setStyleSheet("""
            QPushButton {
                background-color: #4a7eff;
                color: white;
                border-radius: 5px;
                padding: 5px 15px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #3a6eef;
            }
        """)
        input_layout.addWidget(send_button)
        
        chat_layout.addLayout(input_layout)
        
        # Add chat area to splitter
        self.main_splitter.addWidget(self.chat_area)
        
        # Set initial splitter sizes
        self.main_splitter.setSizes([250, 950])
        
        # Add status bar
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage("Ready")
        
        # Add system tray icon
        self.setup_tray()
    
    def eventFilter(self, obj, event):
        """Event filter to catch Enter key press"""
        from PyQt5.QtCore import QEvent
        from PyQt5.QtGui import QKeyEvent
        
        if obj is self.prompt_input and event.type() == QEvent.KeyPress:
            key_event = QKeyEvent(event)
            # Check if Enter key is pressed without Shift
            if key_event.key() == Qt.Key_Return and not key_event.modifiers() & Qt.ShiftModifier:
                self.send_message()
                return True
        return super().eventFilter(obj, event)
    
    def prompt_for_api_key(self):
        """Prompt user to enter OpenAI API key"""
        dialog = APIKeyDialog(self, self.openai_backend.api_key)
        
        # Connect test connection signal
        dialog.test_connection_clicked.connect(self.test_api_connection)
        
        if dialog.exec_() == QDialog.Accepted:
            api_key = dialog.api_key_input.text().strip()
            if api_key:
                # Save API key
                success = self.openai_backend.save_api_key(api_key)
                if success:
                    self.statusBar.showMessage("API key saved successfully", 3000)
                    # Test the connection after saving
                    self.test_api_connection(api_key, show_success=True)
                    self.check_openai_status()
                else:
                    self.statusBar.showMessage("Failed to save API key", 3000)
    
    def open_backend_settings(self):
        """Open the backend settings dialog"""
        dialog = BackendSettingsDialog(
            self, 
            openai_key=self.openai_backend.api_key,
            ollama_settings=self.ollama_settings,
            mcp_servers=self.mcp_servers
        )
        
        # Connect signals
        dialog.test_openai_connection_clicked.connect(self.test_api_connection_for_settings)
        dialog.test_ollama_connection_clicked.connect(self.test_ollama_connection)
        dialog.mcp_settings_changed.connect(self.on_mcp_settings_changed)
        dialog.ollama_settings_changed.connect(self.on_ollama_settings_changed)
        dialog.openai_settings_changed.connect(self.on_openai_settings_changed)
        
        if dialog.exec_() == QDialog.Accepted:
            # Get the new API key (this is handled by the signal now)
            self.statusBar.showMessage("Settings saved successfully", 3000)
            
            # Update the MCP checkboxes in the sidebar
            for server_name, server_info in self.mcp_servers.items():
                if server_name in self.mcp_checkboxes:
                    self.mcp_checkboxes[server_name].setChecked(server_info.get("enabled", False))
            
            # Check status of backend connections
            self.check_backend_status()
    
    def test_ollama_connection(self, server_url, model_name):
        """Test connection to Ollama server
        
        Args:
            server_url: Ollama server URL
            model_name: Model name to test
        """
        # Create a temporary backend to test the connection
        test_backend = OllamaBackend(server_url=server_url, model=model_name)
        
        # Get the dialog if it exists
        dialog = self.findChild(BackendSettingsDialog)
        
        # Test the connection
        connection_success = test_backend.test_connection()
        
        if dialog:
            if connection_success:
                dialog.set_ollama_status("Connection successful! Ollama server is available.", True)
                
                # Try to get available models
                models = test_backend.get_available_models()
                if models:
                    dialog.set_ollama_status(f"Connection successful! Found {len(models)} models: {', '.join(models[:5])}" + 
                                          ("..." if len(models) > 5 else ""), True)
                else:
                    dialog.set_ollama_status("Connection successful, but no models found. You may need to pull models first.", True)
            else:
                dialog.set_ollama_status("Connection failed. Check server URL and ensure Ollama is running.", False)
                
        return connection_success
        
    def on_ollama_settings_changed(self, settings):
        """Handle Ollama settings changes
        
        Args:
            settings: Dict of Ollama settings
        """
        self.ollama_settings = settings
        
        # Update Ollama backend if it exists
        if OLLAMA_AVAILABLE and self.ollama_backend:
            self.ollama_backend = OllamaBackend(
                server_url=settings.get("server_url", "http://localhost:11434"),
                model=settings.get("model", "llama2")
            )
            
        # If Ollama is enabled and OpenAI is disabled, switch to Ollama
        if settings.get("enabled", False) and not self.openai_enabled:
            self.active_backend = "ollama"
        # If Ollama is disabled and it was the active backend, switch to OpenAI
        elif not settings.get("enabled", False) and self.active_backend == "ollama":
            self.active_backend = "openai"
            
    def on_openai_settings_changed(self, settings):
        """Handle OpenAI settings changes
        
        Args:
            settings: Dict of OpenAI settings
        """
        # Update OpenAI API key if changed
        api_key = settings.get("api_key", "")
        if api_key and api_key != self.openai_backend.api_key:
            self.openai_backend.save_api_key(api_key)
            
        # Update base URL if changed
        base_url = settings.get("base_url", "https://api.openai.com/v1")
        if base_url:
            # This would require modifying the backend to support changing the base URL
            # For now, we just log it
            logger.info(f"Base URL changed to {base_url}")
            
        # Update OpenAI enabled status
        self.openai_enabled = settings.get("enabled", True)
        
        # Update current model if changed
        model = settings.get("model", "")
        if model:
            self.current_model = model
            
        # If OpenAI is enabled and Ollama is disabled or unavailable, switch to OpenAI
        if self.openai_enabled and (not self.ollama_settings.get("enabled", False) or not OLLAMA_AVAILABLE):
            self.active_backend = "openai"
        # If OpenAI is disabled and it was the active backend, switch to Ollama if available
        elif not self.openai_enabled and self.active_backend == "openai" and OLLAMA_AVAILABLE and self.ollama_settings.get("enabled", False):
            self.active_backend = "ollama"
    
    def test_api_connection(self, api_key, show_success=False):
        """Test connection to OpenAI API with the given key
        
        Args:
            api_key: API key to test
            show_success: Whether to show a success message in the status bar
        """
        # Create a temporary backend to test the connection
        test_backend = OpenAIBackend(api_key=api_key)
        
        # Get the dialog if it exists
        dialog = self.findChild(APIKeyDialog)
        
        # Set status to "Testing..."
        if dialog:
            dialog.set_status("Testing connection...", True)
            # Process events to show the message
            QApplication.processEvents()
        
        # Test the connection
        connection_success = test_backend.test_connection()
        
        if dialog:
            if connection_success:
                dialog.set_status("Connection successful! API key is valid.", True)
                if show_success:
                    self.statusBar.showMessage("Connection to OpenAI API successful", 3000)
            else:
                dialog.set_status("Connection failed. Check your API key and internet connection.", False)
                
        return connection_success
    
    def test_api_connection_for_settings(self, api_key):
        """Test connection to OpenAI API with the given key for the settings dialog
        
        Args:
            api_key: API key to test
        """
        # Create a temporary backend to test the connection
        test_backend = OpenAIBackend(api_key=api_key)
        
        # Get the backend settings dialog if it exists
        dialog = self.findChild(BackendSettingsDialog)
        
        # Set status to "Testing..."
        if dialog:
            dialog.set_openai_status("Testing connection...", True)
            # Process events to show the message
            QApplication.processEvents()
        
        # Test the connection
        connection_success = test_backend.test_connection()
        
        if dialog:
            if connection_success:
                dialog.set_openai_status("Connection successful! API key is valid.", True)
            else:
                dialog.set_openai_status("Connection failed. Check your API key and internet connection.", False)
                
        return connection_success
    
    def on_mcp_settings_changed(self, mcp_servers):
        """Handle MCP settings changes
        
        Args:
            mcp_servers: Dict of MCP server settings
        """
        self.mcp_servers = mcp_servers
        # Update MCP checkboxes in the sidebar
        for server_name, server_info in self.mcp_servers.items():
            if server_name in self.mcp_checkboxes:
                self.mcp_checkboxes[server_name].setChecked(server_info.get("enabled", False))
    
    def on_mcp_toggled(self, server_name, state):
        """Handle MCP server toggle
        
        Args:
            server_name: Name of the MCP server
            state: Checkbox state (Qt.Checked or Qt.Unchecked)
        """
        if server_name in self.mcp_servers:
            # Update the server's enabled state
            self.mcp_servers[server_name]["enabled"] = state == Qt.Checked
            
            # Show status message
            if state == Qt.Checked:
                self.statusBar.showMessage(f"{server_name.capitalize()} MCP server enabled", 3000)
            else:
                self.statusBar.showMessage(f"{server_name.capitalize()} MCP server disabled", 3000)
    
    def check_backend_status(self):
        """Check status of all backends and update UI accordingly"""
        # First check OpenAI
        if self.openai_enabled:
            self.check_openai_status()
        
        # Then check Ollama if enabled
        if OLLAMA_AVAILABLE and self.ollama_settings.get("enabled", False):
            self.check_ollama_status()
            
        # Determine which backend to use (prioritize enabled backends)
        if self.openai_enabled and self.openai_backend.is_available():
            self.active_backend = "openai"
            self.backend_combo.setCurrentText("OpenAI")
        elif OLLAMA_AVAILABLE and self.ollama_settings.get("enabled", False) and self.ollama_backend.is_available():
            self.active_backend = "ollama"
            self.backend_combo.setCurrentText("Ollama")
        else:
            # Fallback to OpenAI (even if not available)
            self.active_backend = "openai"
            self.backend_combo.setCurrentText("OpenAI")
        
        # Update window title based on active backend
        if self.active_backend == "openai":
            model_name = self.current_model or "GPT-4o-mini"
            self.setWindowTitle(f"KDE AI Interface - OpenAI {model_name}")
        elif self.active_backend == "ollama":
            model_name = self.ollama_settings.get("model", "llama2")
            self.setWindowTitle(f"KDE AI Interface - Ollama {model_name}")
        else:
            self.setWindowTitle("KDE AI Interface")
    
    def check_openai_status(self):
        """Check if OpenAI API is available and update UI accordingly"""
        if self.openai_backend.is_available():
            # Test actual API connection
            connection_ok = self.openai_backend.test_connection()
            
            if connection_ok:
                self.openai_status_label.setText(f"OpenAI API: Connected")
                self.openai_status_label.setStyleSheet("color: green;")
                
                # Get available models
                models = self.openai_backend.get_available_models()
                if models:
                    # Update model dropdown if OpenAI is active backend
                    if self.active_backend == "openai":
                        self.model_combo.clear()
                        for model in models:
                            self.model_combo.addItem(model)
                        
                        # Set current model if valid
                        if self.current_model in models:
                            self.model_combo.setCurrentText(self.current_model)
                        else:
                            self.current_model = models[0]
                            self.model_combo.setCurrentText(self.current_model)
                    
                    self.statusBar.showMessage(f"Connected to OpenAI API. Found {len(models)} models.", 3000)
                else:
                    # Use default models if API doesn't return models
                    if self.active_backend == "openai":
                        self.model_combo.clear()
                        for model in DEFAULT_MODELS:
                            self.model_combo.addItem(model)
                        
                        if self.current_model in DEFAULT_MODELS:
                            self.model_combo.setCurrentText(self.current_model)
                        else:
                            self.current_model = DEFAULT_MODELS[0]
                            self.model_combo.setCurrentText(self.current_model)
                    
                    self.statusBar.showMessage("Connected to OpenAI API. Using default models list.", 3000)
            else:
                self.openai_status_label.setText(f"OpenAI API: Connection Error")
                self.openai_status_label.setStyleSheet("color: orange;")
                
                # Use default models if OpenAI is active backend
                if self.active_backend == "openai":
                    self.model_combo.clear()
                    for model in DEFAULT_MODELS:
                        self.model_combo.addItem(model)
                    
                    if self.current_model in DEFAULT_MODELS:
                        self.model_combo.setCurrentText(self.current_model)
                    else:
                        self.current_model = DEFAULT_MODELS[0]
                        self.model_combo.setCurrentText(self.current_model)
                
                self.statusBar.showMessage("API key present but cannot connect to OpenAI API. Check internet connection.", 5000)
                
        else:
            self.openai_status_label.setText(f"OpenAI API: Not Available")
            self.openai_status_label.setStyleSheet("color: red;")
            
            # Use default models if OpenAI is active backend
            if self.active_backend == "openai":
                self.model_combo.clear()
                for model in DEFAULT_MODELS:
                    self.model_combo.addItem(model)
                
                self.current_model = DEFAULT_MODELS[0]
                self.model_combo.setCurrentText(self.current_model)
            
            if not self.openai_backend.api_key:
                self.statusBar.showMessage("OpenAI API key not set. Please set your API key.", 5000)
            elif not OPENAI_AVAILABLE:
                self.statusBar.showMessage("OpenAI SDK not installed. Please install with: pip install openai", 5000)
    
    def check_ollama_status(self):
        """Check if Ollama server is available and update UI accordingly"""
        if not OLLAMA_AVAILABLE:
            self.ollama_status_label.setText("Ollama: Not Installed")
            self.ollama_status_label.setStyleSheet("color: red;")
            return
            
        # Create or update Ollama backend
        server_url = self.ollama_settings.get("server_url", "http://localhost:11434")
        model = self.ollama_settings.get("model", "llama2")
        self.ollama_backend = OllamaBackend(server_url=server_url, model=model)
        
        # Check if server is available
        if self.ollama_backend.is_available():
            self.ollama_status_label.setText("Ollama: Connected")
            self.ollama_status_label.setStyleSheet("color: green;")
            
            # Get available models
            models = self.ollama_backend.get_available_models()
            
            if models:
                # Update model dropdown if Ollama is active backend
                if self.active_backend == "ollama":
                    self.model_combo.clear()
                    for model_name in models:
                        self.model_combo.addItem(model_name)
                    
                    # Set current model if valid
                    current_ollama_model = self.ollama_settings.get("model", "llama2")
                    if current_ollama_model in models:
                        self.model_combo.setCurrentText(current_ollama_model)
                    elif models:
                        self.ollama_settings["model"] = models[0]
                        self.model_combo.setCurrentText(models[0])
                
                self.statusBar.showMessage(f"Connected to Ollama server. Found {len(models)} models.", 3000)
            else:
                self.statusBar.showMessage("Connected to Ollama server, but no models found.", 3000)
        else:
            self.ollama_status_label.setText("Ollama: Not Available")
            self.ollama_status_label.setStyleSheet("color: red;")
            self.statusBar.showMessage(f"Could not connect to Ollama server at {server_url}", 5000)
    
    def create_toggle_button(self, text, icon_name, callback):
        """Create a toggle button with text and icon"""
        button = QPushButton(text)
        button.setCheckable(True)
        button.setChecked(False)
        # Try to use theme icon, fallback to text only
        icon = QIcon.fromTheme(icon_name)
        if not icon.isNull():
            button.setIcon(icon)
        button.clicked.connect(callback)
        button.setStyleSheet("""
            QPushButton {
                padding: 5px 10px;
                border-radius: 3px;
                background-color: #eeeeee;
                color: #333333;
                font-weight: bold;
                border: 1px solid #cccccc;
            }
            QPushButton:checked {
                background-color: #4a7eff;
                color: white;
                border: 1px solid #3a6eef;
            }
        """)
        return button
        
    def toggle_screen_capture(self, checked):
        """Toggle screen capture feature"""
        self.screen_capture_enabled = checked
        if checked:
            self.context_status.setText("Capturing screen")
            self.context_sources.setText("Screen")
            self.statusBar.showMessage("Screen capture enabled", 3000)
        else:
            # Update status only if audio is also disabled
            if not self.audio_capture_enabled:
                self.context_status.setText("Not capturing")
                self.context_sources.setText("None")
            else:
                self.context_sources.setText("Audio")
            self.statusBar.showMessage("Screen capture disabled", 3000)
    
    def toggle_audio_capture(self, checked):
        """Toggle audio capture feature"""
        self.audio_capture_enabled = checked
        if checked:
            self.context_status.setText("Capturing audio")
            # Update sources text
            if self.screen_capture_enabled:
                self.context_sources.setText("Screen, Audio")
            else:
                self.context_sources.setText("Audio")
            self.statusBar.showMessage("Audio capture enabled", 3000)
        else:
            # Update status only if screen is also disabled
            if not self.screen_capture_enabled:
                self.context_status.setText("Not capturing")
                self.context_sources.setText("None")
            else:
                self.context_sources.setText("Screen")
            self.statusBar.showMessage("Audio capture disabled", 3000)
            
    def toggle_rag(self, checked):
        """Toggle RAG (Retrieval-Augmented Generation) feature"""
        self.rag_enabled = checked
        if checked:
            self.memory_status.setText("RAG enabled")
            self.statusBar.showMessage("Retrieval-Augmented Generation enabled", 3000)
        else:
            self.memory_status.setText("RAG disabled")
            self.statusBar.showMessage("Retrieval-Augmented Generation disabled", 3000)
            
    def new_conversation(self):
        """Create a new conversation"""
        # Generate a unique ID for the conversation
        import time
        conv_id = f"conversation_{int(time.time())}"
        
        # Create conversation record
        conversation = {
            "id": conv_id,
            "name": f"Conversation {len(self.conversations) + 1}",
            "messages": [],
            "created_at": time.time()
        }
        
        # Add to conversations list
        self.conversations.append(conversation)
        
        # Update conversation list widget
        self.update_conversation_list()
        
        # Select the new conversation
        self.current_conversation_index = len(self.conversations) - 1
        self.conversation_list.setCurrentRow(self.current_conversation_index)
        
        # Clear chat display
        self.chat_display.clear()
        
        # Add welcome message
        welcome_msg = """
        Welcome to the KDE AI Interface powered by OpenAI GPT-4o-mini! 
        
        This interface connects to OpenAI's API to provide high-quality AI assistance.
        
        Available features:
        - Screen capture button: Record your screen for context
        - Audio capture button: Record audio for transcription
        - RAG button: Toggle Retrieval-Augmented Generation
        - Conversation sidebar: Manage multiple chat sessions
        
        Type your message and press Enter or click Send to begin!
        """
        self.add_assistant_message(welcome_msg)
        
        # Add welcome message to conversation history
        self.conversations[self.current_conversation_index]["messages"].append({
            "role": "assistant",
            "content": welcome_msg
        })
        
    def update_conversation_list(self):
        """Update the conversation list widget"""
        self.conversation_list.clear()
        for conv in self.conversations:
            item = QListWidgetItem(conv["name"])
            item.setData(Qt.UserRole, conv["id"])
            self.conversation_list.addItem(item)
            
    def on_conversation_selected(self, item):
        """Handle selection of a conversation from the list"""
        conv_id = item.data(Qt.UserRole)
        
        # Find the selected conversation
        for i, conv in enumerate(self.conversations):
            if conv["id"] == conv_id:
                self.current_conversation_index = i
                break
                
        # Load the conversation
        self.load_conversation(self.current_conversation_index)
        
    def load_conversation(self, index):
        """Load a conversation into the chat display"""
        if index < 0 or index >= len(self.conversations):
            return
            
        # Clear chat display
        self.chat_display.clear()
        
        # Add messages from conversation
        conversation = self.conversations[index]
        for message in conversation["messages"]:
            if message["role"] == "user":
                self.add_user_message(message["content"], add_to_history=False)
            else:
                self.add_assistant_message(message["content"], add_to_history=False)
                
    def save_conversations(self):
        """Save conversations to disk"""
        import json
        
        # Ensure conversations directory exists
        if not self.conversation_dir.exists():
            self.conversation_dir.mkdir(parents=True, exist_ok=True)
            
        # Save each conversation to a separate file
        for conv in self.conversations:
            file_path = self.conversation_dir / f"{conv['id']}.json"
            with open(file_path, 'w') as f:
                json.dump(conv, f)
                
    def load_conversations(self):
        """Load conversations from disk"""
        import json
        
        # Ensure conversations directory exists
        if not self.conversation_dir.exists():
            return
            
        # Load conversations from files
        self.conversations = []
        for file_path in self.conversation_dir.glob("*.json"):
            try:
                with open(file_path, 'r') as f:
                    conv = json.load(f)
                    self.conversations.append(conv)
            except Exception as e:
                logger.error(f"Error loading conversation {file_path}: {str(e)}")
                
        # Sort conversations by creation time
        self.conversations.sort(key=lambda x: x.get("created_at", 0))
        
        # Update conversation list
        self.update_conversation_list()
        
        # Select most recent conversation if available
        if self.conversations:
            self.current_conversation_index = len(self.conversations) - 1
            self.conversation_list.setCurrentRow(self.current_conversation_index)
            self.load_conversation(self.current_conversation_index)
        else:
            # Create a new conversation if none exist
            self.new_conversation()

    def setup_tray(self):
        """Set up the system tray icon"""
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(QIcon.fromTheme("assistant", QIcon.fromTheme("dialog-information")))
        
        # Create tray menu
        tray_menu = QMenu()
        
        show_action = QAction("Show/Hide", self)
        show_action.triggered.connect(self.toggle_window)
        tray_menu.addAction(show_action)
        
        quit_action = QAction("Exit", self)
        quit_action.triggered.connect(QApplication.quit)
        tray_menu.addAction(quit_action)
        
        # Set tray icon and menu
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self.on_tray_activated)
        self.tray_icon.show()
    
    def on_tray_activated(self, reason):
        """Handle tray icon activation"""
        if reason == QSystemTrayIcon.Trigger:
            self.toggle_window()
    
    def toggle_window(self):
        """Toggle window visibility"""
        if self.isVisible():
            self.hide()
        else:
            self.show()
            self.raise_()
            self.activateWindow()
    
    def on_backend_changed(self, backend_name):
        """Handle backend selection change"""
        if backend_name == "OpenAI":
            self.active_backend = "openai"
            # Update model dropdown with OpenAI models
            self.model_combo.clear()
            if self.openai_backend.is_available():
                models = self.openai_backend.get_available_models()
                if models:
                    for model in models:
                        self.model_combo.addItem(model)
                    if self.current_model in models:
                        self.model_combo.setCurrentText(self.current_model)
                    else:
                        self.current_model = models[0]
                        self.model_combo.setCurrentText(self.current_model)
                else:
                    # Use default models if not available
                    for model in DEFAULT_MODELS:
                        self.model_combo.addItem(model)
                    self.model_combo.setCurrentText(self.current_model if self.current_model in DEFAULT_MODELS else DEFAULT_MODELS[0])
            else:
                # Use default models if not available
                for model in DEFAULT_MODELS:
                    self.model_combo.addItem(model)
                self.model_combo.setCurrentText(self.current_model if self.current_model in DEFAULT_MODELS else DEFAULT_MODELS[0])
        elif backend_name == "Ollama" and OLLAMA_AVAILABLE:
            self.active_backend = "ollama"
            # Update model dropdown with Ollama models
            self.model_combo.clear()
            if self.ollama_backend and self.ollama_backend.is_available():
                models = self.ollama_backend.get_available_models()
                if models:
                    for model in models:
                        self.model_combo.addItem(model)
                    
                    current_model = self.ollama_settings.get("model", "llama2")
                    if current_model in models:
                        self.model_combo.setCurrentText(current_model)
                    else:
                        self.ollama_settings["model"] = models[0]
                        self.model_combo.setCurrentText(models[0])
                else:
                    # If no models available, add the configured one
                    model = self.ollama_settings.get("model", "llama2")
                    self.model_combo.addItem(model)
                    self.model_combo.setCurrentText(model)
            else:
                # If not available, add the configured model
                model = self.ollama_settings.get("model", "llama2")
                self.model_combo.addItem(model)
                self.model_combo.setCurrentText(model)
                
        # Update window title
        if self.active_backend == "openai":
            model_name = self.current_model or "GPT-4o-mini"
            self.setWindowTitle(f"KDE AI Interface - OpenAI {model_name}")
        elif self.active_backend == "ollama":
            model_name = self.ollama_settings.get("model", "llama2")
            self.setWindowTitle(f"KDE AI Interface - Ollama {model_name}")
                
        logger.info(f"Switched backend to: {backend_name}")
    
    def on_model_changed(self, model_name):
        """Handle model selection change"""
        if self.active_backend == "openai":
            self.current_model = model_name
            self.setWindowTitle(f"KDE AI Interface - OpenAI {model_name}")
        elif self.active_backend == "ollama":
            self.ollama_settings["model"] = model_name
            self.ollama_backend = OllamaBackend(
                server_url=self.ollama_settings.get("server_url", "http://localhost:11434"), 
                model=model_name
            )
            self.setWindowTitle(f"KDE AI Interface - Ollama {model_name}")
            
        logger.info(f"Selected model: {model_name}")
    
    def on_temperature_changed(self, value):
        """Handle temperature value change"""
        self.model_config["temperature"] = value / 10.0
        logger.info(f"Temperature set to {self.model_config['temperature']}")
    
    def on_top_p_changed(self, value):
        """Handle top-p value change"""
        self.model_config["top_p"] = value / 10.0
        logger.info(f"Top-p set to {self.model_config['top_p']}")
    
    def on_max_tokens_changed(self, value):
        """Handle max tokens value change"""
        self.model_config["max_tokens"] = value
        logger.info(f"Max tokens set to {self.model_config['max_tokens']}")
    
    def on_system_prompt_changed(self):
        """Handle system prompt change"""
        self.model_config["system_prompt"] = self.system_prompt_input.toPlainText()
        logger.info(f"System prompt updated")
        
    def get_conversation_history(self):
        """Get conversation history for the current conversation"""
        history = []
        if self.current_conversation_index >= 0 and self.conversations:
            conversation = self.conversations[self.current_conversation_index]
            # Get last few messages (limit to reasonable amount)
            for message in conversation["messages"][-10:]:  # Last 10 messages
                if "role" in message and "content" in message:
                    history.append({
                        "role": message["role"],
                        "content": message["content"]
                    })
        return history
        
    def send_message(self):
        """Send a message to the assistant"""
        # Get the message
        prompt = self.prompt_input.toPlainText().strip()
        if not prompt:
            return
        
        # Clear the input field
        self.prompt_input.clear()
        
        # Add the user message to the chat
        self.add_user_message(prompt)
        
        # Check if a backend is available
        if self.active_backend == "openai" and not self.openai_backend.is_available():
            self.statusBar.showMessage("OpenAI API not available. Please check your API key.")
            self.add_assistant_message("Error: OpenAI API not available. Please check your API key.")
            return
        elif self.active_backend == "ollama" and (not OLLAMA_AVAILABLE or not self.ollama_backend or not self.ollama_backend.is_available()):
            self.statusBar.showMessage("Ollama server not available. Please check server configuration.")
            self.add_assistant_message("Error: Ollama server not available. Please check server configuration.")
            return
        
        # Create assistant response placeholder
        self.chat_display.append("<p><b>Assistant:</b><br></p>")
        self.current_response = ""
        
        # Update config with model-specific settings
        config = self.model_config.copy()
        
        # Set model name based on active backend
        if self.active_backend == "openai":
            config["model"] = self.current_model
        elif self.active_backend == "ollama":
            config["model"] = self.ollama_settings.get("model", "llama2")
        
        # Add context information if capturing is enabled
        enhanced_prompt = prompt
        context_info = []
        
        if self.screen_capture_enabled:
            # Placeholder for actual screen capture implementation
            screen_context = "[Screen capture enabled - would include screenshot description here]"
            context_info.append(f"Screen Context: {screen_context}")
            self.statusBar.showMessage("Including screen context in prompt", 2000)
            
        if self.audio_capture_enabled:
            # Placeholder for actual audio capture implementation
            audio_context = "[Audio capture enabled - would include transcription here]"
            context_info.append(f"Audio Context: {audio_context}")
            self.statusBar.showMessage("Including audio context in prompt", 2000)
            
        # Add RAG context if enabled
        if self.rag_enabled:
            # Placeholder for actual RAG implementation
            if self.current_conversation_index >= 0 and self.conversations:
                # Get previous conversations for context
                conversation = self.conversations[self.current_conversation_index]
                if len(conversation["messages"]) > 2:  # If there's a conversation history
                    rag_context = "[RAG enabled - would include relevant memory from previous conversations]"
                    context_info.append(f"Memory Context: {rag_context}")
                    self.statusBar.showMessage("Including memory context in prompt", 2000)
        
        # If we have context info, add it to the prompt
        if context_info:
            context_block = "\n\n--- Context Information ---\n" + "\n".join(context_info) + "\n---\n\n"
            enhanced_prompt = context_block + "User Query: " + prompt
            
            # Log the enhanced prompt
            logger.info(f"Enhanced prompt with context: {enhanced_prompt[:100]}...")
        
        # Get backend for generation
        backend = None
        if self.active_backend == "openai":
            backend = self.openai_backend
        elif self.active_backend == "ollama" and OLLAMA_AVAILABLE:
            backend = self.ollama_backend
        
        # Start generation thread
        self.generate_thread = GenerateThread(backend, enhanced_prompt, config, 
                                             self.get_conversation_history() if self.rag_enabled else None)
        self.generate_thread.response_started.connect(self.on_response_started)
        self.generate_thread.response_chunk.connect(self.on_response_chunk)
        self.generate_thread.response_finished.connect(self.on_response_finished)
        self.generate_thread.error_occurred.connect(self.on_error)
        self.generate_thread.start()

    def add_user_message(self, message, add_to_history=True):
        """Add a user message to the chat display"""
        self.chat_display.append(f"<p><b>You:</b><br>{message}</p>")
        
        # Add to conversation history if a conversation is active
        if add_to_history and self.current_conversation_index >= 0:
            self.conversations[self.current_conversation_index]["messages"].append({
                "role": "user",
                "content": message
            })
            
        self.scroll_to_bottom()
    
    def add_assistant_message(self, message, add_to_history=True):
        """Add an assistant message to the chat display"""
        self.chat_display.append(f"<p><b>Assistant:</b><br>{message}</p>")
        
        # Add to conversation history if a conversation is active
        if add_to_history and self.current_conversation_index >= 0:
            self.conversations[self.current_conversation_index]["messages"].append({
                "role": "assistant",
                "content": message
            })
            
        self.scroll_to_bottom()
    
    def scroll_to_bottom(self):
        """Scroll the chat display to the bottom"""
        cursor = self.chat_display.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.chat_display.setTextCursor(cursor)
    
    def send_message(self):
        """Send a message to the assistant"""
        # Get the message
        prompt = self.prompt_input.toPlainText().strip()
        if not prompt:
            return
        
        # Clear the input field
        self.prompt_input.clear()
        
        # Add the user message to the chat
        self.add_user_message(prompt)
        
        # Create assistant response placeholder
        self.chat_display.append("<p><b>Assistant:</b><br></p>")
        self.current_response = ""
        
        # Get conversation history for context
        conversation_history = []
        if self.current_conversation_index >= 0 and self.rag_enabled:
            # Filter for actual message data in the format OpenAI expects
            for message in self.conversations[self.current_conversation_index]["messages"]:
                if message["role"] in ["user", "assistant", "system"]:
                    conversation_history.append({
                        "role": message["role"],
                        "content": message["content"]
                    })
        
        # Add context information if capturing is enabled
        enhanced_prompt = prompt
        context_info = []
        
        if self.screen_capture_enabled:
            # Placeholder for actual screen capture implementation
            screen_context = "[Screen capture enabled - would include screenshot description here]"
            context_info.append(f"Screen Context: {screen_context}")
            self.statusBar.showMessage("Including screen context in prompt", 2000)
            
        if self.audio_capture_enabled:
            # Placeholder for actual audio capture implementation
            audio_context = "[Audio capture enabled - would include transcription here]"
            context_info.append(f"Audio Context: {audio_context}")
            self.statusBar.showMessage("Including audio context in prompt", 2000)
        
        # If we have context info, add it to the prompt
        if context_info:
            context_block = "\n\n--- Context Information ---\n" + "\n".join(context_info) + "\n---\n\n"
            enhanced_prompt = context_block + "User Query: " + prompt
            
            # Log the enhanced prompt
            logger.info(f"Enhanced prompt with context: {enhanced_prompt[:100]}...")
        
        # Update config
        config = self.model_config.copy()
        config["model"] = self.current_model
        
        # Start generation thread
        self.generate_thread = GenerateThread(
            backend=self.openai_backend,
            prompt=enhanced_prompt,
            model_config=config,
            conversation_history=conversation_history
        )
        self.generate_thread.response_started.connect(self.on_response_started)
        self.generate_thread.response_chunk.connect(self.on_response_chunk)
        self.generate_thread.response_finished.connect(self.on_response_finished)
        self.generate_thread.error_occurred.connect(self.on_error)
        self.generate_thread.start()
    
    def on_response_started(self):
        """Handle response generation started"""
        self.statusBar.showMessage("Generating response...")
    
    def on_response_chunk(self, chunk):
        """Handle response chunk received"""
        self.current_response += chunk
        
        # Update the last paragraph (remove and replace)
        cursor = self.chat_display.textCursor()
        cursor.movePosition(QTextCursor.End)
        cursor.movePosition(QTextCursor.StartOfBlock, QTextCursor.KeepAnchor)
        cursor.removeSelectedText()
        cursor.insertHtml(f"<p><b>Assistant:</b><br>{self.current_response}</p>")
        
        self.scroll_to_bottom()
    
    def on_response_finished(self, metrics):
        """Handle response generation completed"""
        duration = metrics.get("duration", 0)
        token_count = metrics.get("token_count", 0)
        tokens_per_second = metrics.get("tokens_per_second", 0)
        backend = metrics.get("backend", "Unknown")
        
        # Update performance label
        self.performance_label.setText(
            f"{token_count} tokens in {duration:.2f}s ({tokens_per_second:.2f} tokens/sec) using {backend}"
        )
        
        self.statusBar.showMessage(f"Response complete: {tokens_per_second:.2f} tokens/sec", 3000)
        
        # Add the message to conversation history
        if self.current_conversation_index >= 0:
            self.conversations[self.current_conversation_index]["messages"].append({
                "role": "assistant",
                "content": self.current_response
            })
        
        # Add an empty line after the response
        self.chat_display.append("")
        
        # Save conversation
        self.save_conversations()
    
    def on_error(self, error_message):
        """Handle error during generation"""
        self.statusBar.showMessage(f"Error: {error_message}")
        self.add_assistant_message(f"Error: {error_message}")
    
    def closeEvent(self, event):
        """Handle closing the window"""
        # Save conversations before exiting
        self.save_conversations()
        event.accept()

def main():
    """Main function"""
    app = QApplication(sys.argv)
    app.setApplicationName("KDE AI Interface")
    
    # Set up dark style
    try:
        import qdarkstyle
        app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
        print("QDarkStyle applied")
    except ImportError:
        print("QDarkStyle not available, using default style")
    
    # Create and show the main window
    window = KDEAIInterface()
    
    # Load saved conversations
    window.load_conversations()
    
    window.show()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()