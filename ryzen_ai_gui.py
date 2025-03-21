#!/usr/bin/env python3
import sys
import os
import logging
import threading
from pathlib import Path
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QTextEdit, QPushButton, QLineEdit, QComboBox,
                            QHBoxLayout, QLabel, QSystemTrayIcon, QMenu, QAction,
                            QDialog, QFormLayout, QSlider, QSpinBox, QDoubleSpinBox,
                            QTabWidget, QSplitter, QStatusBar)
from PyQt5.QtCore import Qt, pyqtSignal, pyqtSlot, QThread, QSettings
from PyQt5.QtGui import QIcon, QTextCursor

# Import the Ryzen AI model
from run_ryzen_ai_model import RyzenAIModel

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("RyzenAI-KDE-Interface")

# List of available AMD Ryzen AI models
AVAILABLE_MODELS = [
    "amd/Llama-3.2-1B-Instruct-awq-g128-int4-asym-bf16-onnx-ryzen-strix",  # Start with smallest model first
    "amd/Llama-3.2-3B-Instruct-awq-g128-int4-asym-bf16-onnx-ryzen-strix",
    "amd/Phi-3-mini-4k-instruct-awq-g128-int4-asym-bf16-onnx-ryzen-strix",
    "amd/Phi-3.5-mini-instruct-awq-g128-int4-asym-bf16-onnx-ryzen-strix",
    "amd/Llama-3-8B-awq-g128-int4-asym-bf16-onnx-ryzen-strix",
    "amd/Llama-3.1-8B-awq-g128-int4-asym-bf16-onnx-ryzen-strix",
    "amd/Mistral-7B-Instruct-v0.3-awq-g128-int4-asym-bf16-onnx-ryzen-strix",
    "amd/Qwen1.5-7B-Chat-awq-g128-int4-asym-bf16-onnx-ryzen-strix"
]

class GenerateThread(QThread):
    """Thread to run the model generation without blocking the UI"""
    response_started = pyqtSignal()
    response_chunk = pyqtSignal(str)
    response_finished = pyqtSignal()
    error_occurred = pyqtSignal(str)
    
    def __init__(self, model, prompt, max_tokens=1024, temperature=0.7, top_p=0.9):
        super().__init__()
        self.model = model
        self.prompt = prompt
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.top_p = top_p
    
    def run(self):
        try:
            self.response_started.emit()
            
            # Generate text with streaming
            streamer = self.model.generate(
                self.prompt,
                max_new_tokens=self.max_tokens,
                temperature=self.temperature,
                top_p=self.top_p,
                stream=True
            )
            
            # Process the streaming response
            for text in streamer:
                self.response_chunk.emit(text)
            
            self.response_finished.emit()
            
        except Exception as e:
            logger.error(f"Error in generation thread: {str(e)}")
            self.error_occurred.emit(str(e))

class SettingsDialog(QDialog):
    """Dialog for model settings"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("KDE AI Interface Settings")
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.setMinimumWidth(400)
        
        self.settings = QSettings("KDE", "AIInterface")
        
        # Main layout
        layout = QVBoxLayout(self)
        
        # Settings form
        form_layout = QFormLayout()
        
        # Model selection
        self.model_combo = QComboBox()
        self.model_combo.addItems(AVAILABLE_MODELS)
        current_model = self.settings.value("model", AVAILABLE_MODELS[0])
        index = self.model_combo.findText(current_model)
        self.model_combo.setCurrentIndex(max(0, index))
        form_layout.addRow("Model:", self.model_combo)
        
        # Temperature
        self.temperature_spin = QDoubleSpinBox()
        self.temperature_spin.setRange(0.0, 2.0)
        self.temperature_spin.setSingleStep(0.1)
        self.temperature_spin.setValue(float(self.settings.value("temperature", 0.7)))
        form_layout.addRow("Temperature:", self.temperature_spin)
        
        # Top-p
        self.top_p_spin = QDoubleSpinBox()
        self.top_p_spin.setRange(0.0, 1.0)
        self.top_p_spin.setSingleStep(0.05)
        self.top_p_spin.setValue(float(self.settings.value("top_p", 0.9)))
        form_layout.addRow("Top-p:", self.top_p_spin)
        
        # Max tokens
        self.max_tokens_spin = QSpinBox()
        self.max_tokens_spin.setRange(1, 4096)
        self.max_tokens_spin.setSingleStep(128)
        self.max_tokens_spin.setValue(int(self.settings.value("max_tokens", 1024)))
        form_layout.addRow("Max Tokens:", self.max_tokens_spin)
        
        layout.addLayout(form_layout)
        
        # Buttons
        buttons_layout = QHBoxLayout()
        
        save_button = QPushButton("Save")
        save_button.clicked.connect(self.accept)
        buttons_layout.addWidget(save_button)
        
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_button)
        
        layout.addLayout(buttons_layout)
    
    def get_settings(self):
        """Return the current settings"""
        return {
            "model": self.model_combo.currentText(),
            "temperature": self.temperature_spin.value(),
            "top_p": self.top_p_spin.value(),
            "max_tokens": self.max_tokens_spin.value()
        }
    
    def save_settings(self):
        """Save settings to persistent storage"""
        settings = self.get_settings()
        for key, value in settings.items():
            self.settings.setValue(key, value)
        self.settings.sync()

class KDEAIWindow(QMainWindow):
    """Main window for the KDE AI Interface"""
    def __init__(self):
        super().__init__()
        
        # Initialize settings
        self.settings = QSettings("KDE", "AIInterface")
        self.load_settings()
        
        # Initialize the UI
        self.init_ui()
        
        # Initialize the model (in a background thread)
        self.model = None
        self.model_thread = None
        self.init_model()
    
    def load_settings(self):
        """Load settings"""
        self.model_id = self.settings.value("model", AVAILABLE_MODELS[0])
        self.temperature = float(self.settings.value("temperature", 0.7))
        self.top_p = float(self.settings.value("top_p", 0.9))
        self.max_tokens = int(self.settings.value("max_tokens", 1024))
        self.window_geometry = self.settings.value("window_geometry")
    
    def save_settings(self):
        """Save settings"""
        self.settings.setValue("window_geometry", self.saveGeometry())
        self.settings.sync()
    
    def init_model(self):
        """Initialize the model in a background thread"""
        def load_model_thread():
            try:
                self.statusBar().showMessage("Loading model, please wait...")
                self.model = RyzenAIModel(self.model_id)
                self.statusBar().showMessage("Model loaded successfully", 3000)
            except Exception as e:
                logger.error(f"Error loading model: {str(e)}")
                self.statusBar().showMessage(f"Error loading model: {str(e)}")
        
        self.model_thread = threading.Thread(target=load_model_thread)
        self.model_thread.daemon = True
        self.model_thread.start()
    
    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("KDE AI Interface - Ryzen AI Powered")
        self.setGeometry(100, 100, 800, 600)
        
        # Restore saved geometry if available
        if self.window_geometry:
            self.restoreGeometry(self.window_geometry)
        
        # Main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)
        
        # Create chat display
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        
        # Create input area
        input_layout = QHBoxLayout()
        
        self.prompt_input = QTextEdit()
        self.prompt_input.setPlaceholderText("Type your message here...")
        self.prompt_input.setMaximumHeight(100)
        input_layout.addWidget(self.prompt_input)
        
        send_button = QPushButton("Send")
        send_button.clicked.connect(self.send_message)
        input_layout.addWidget(send_button)
        
        # Add widgets to main layout
        main_layout.addWidget(self.chat_display)
        main_layout.addLayout(input_layout)
        
        # Status bar
        self.statusBar().showMessage("Ready")
        
        # Create menu bar
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("File")
        
        settings_action = QAction("Settings", self)
        settings_action.triggered.connect(self.open_settings)
        file_menu.addAction(settings_action)
        
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Setup system tray
        self.setup_tray()
        
        # Add welcome message
        self.add_assistant_message("Welcome to the KDE AI Interface powered by AMD Ryzen AI! How can I help you today?")
    
    def setup_tray(self):
        """Set up the system tray icon"""
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(QIcon.fromTheme("assistant", QIcon.fromTheme("system-help")))
        
        # Create menu
        tray_menu = QMenu()
        
        show_action = QAction("Show/Hide", self)
        show_action.triggered.connect(self.toggle_window)
        tray_menu.addAction(show_action)
        
        settings_action = QAction("Settings", self)
        settings_action.triggered.connect(self.open_settings)
        tray_menu.addAction(settings_action)
        
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(QApplication.quit)
        tray_menu.addAction(exit_action)
        
        # Set menu and activate
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
    
    def open_settings(self):
        """Open the settings dialog"""
        dialog = SettingsDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            # Save the settings
            dialog.save_settings()
            
            # Update current settings
            settings = dialog.get_settings()
            
            old_model = self.model_id
            self.model_id = settings["model"]
            self.temperature = settings["temperature"]
            self.top_p = settings["top_p"]
            self.max_tokens = settings["max_tokens"]
            
            # Reload model if changed
            if old_model != self.model_id:
                self.add_system_message(f"Switching to model: {self.model_id}")
                self.init_model()
    
    def add_user_message(self, message):
        """Add a user message to the chat display"""
        self.chat_display.append(f"<p><b>You:</b><br>{message}</p>")
        self.scroll_to_bottom()
    
    def add_assistant_message(self, message):
        """Add an assistant message to the chat display"""
        self.chat_display.append(f"<p><b>Assistant:</b><br>{message}</p>")
        self.scroll_to_bottom()
    
    def add_system_message(self, message):
        """Add a system message to the chat display"""
        self.chat_display.append(f"<p><i>System: {message}</i></p>")
        self.scroll_to_bottom()
    
    def scroll_to_bottom(self):
        """Scroll the chat display to the bottom"""
        cursor = self.chat_display.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.chat_display.setTextCursor(cursor)
    
    def send_message(self):
        """Send a message to the model"""
        prompt = self.prompt_input.toPlainText().strip()
        if not prompt:
            return
        
        # Clear the input
        self.prompt_input.clear()
        
        # Display the user message
        self.add_user_message(prompt)
        
        # Check if the model is loaded
        if self.model is None:
            self.add_system_message("Model is still loading. Please wait...")
            return
        
        # Create and start the generation thread
        self.current_response = ""
        self.generate_thread = GenerateThread(
            self.model,
            prompt,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            top_p=self.top_p
        )
        
        # Connect signals
        self.generate_thread.response_started.connect(self.on_response_started)
        self.generate_thread.response_chunk.connect(self.on_response_chunk)
        self.generate_thread.response_finished.connect(self.on_response_finished)
        self.generate_thread.error_occurred.connect(self.on_error)
        
        # Start generation
        self.generate_thread.start()
    
    @pyqtSlot()
    def on_response_started(self):
        """Handle response generation started"""
        self.statusBar().showMessage("Generating response...")
        self.chat_display.append("<p><b>Assistant:</b><br></p>")
        self.current_response = ""
    
    @pyqtSlot(str)
    def on_response_chunk(self, chunk):
        """Handle response chunk received"""
        self.current_response += chunk
        
        # Update the last paragraph with the current response
        cursor = self.chat_display.textCursor()
        cursor.movePosition(QTextCursor.End)
        cursor.movePosition(QTextCursor.StartOfBlock, QTextCursor.KeepAnchor)
        cursor.removeSelectedText()
        cursor.insertHtml(f"<p><b>Assistant:</b><br>{self.current_response}</p>")
        
        self.scroll_to_bottom()
    
    @pyqtSlot()
    def on_response_finished(self):
        """Handle response generation completed"""
        self.statusBar().showMessage("Response complete", 3000)
    
    @pyqtSlot(str)
    def on_error(self, error_message):
        """Handle error during generation"""
        self.add_system_message(f"Error: {error_message}")
        self.statusBar().showMessage(f"Error: {error_message}")
    
    def closeEvent(self, event):
        """Handle window close event"""
        self.save_settings()
        if self.model_thread and self.model_thread.is_alive():
            self.model_thread.join(0.1)
        event.accept()

def main():
    """Main function"""
    # Create the application
    app = QApplication(sys.argv)
    app.setApplicationName("KDE AI Interface")
    
    # Set up dark style
    try:
        import qdarkstyle
        app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
    except ImportError:
        logger.warning("QDarkStyle not available, using default style")
    
    # Create and show the main window
    window = KDEAIWindow()
    window.show()
    
    # Run the application
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()