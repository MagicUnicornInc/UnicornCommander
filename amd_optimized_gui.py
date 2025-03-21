#!/usr/bin/env python3
import os
import sys
import logging
import time
import threading
import torch
from pathlib import Path
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QTextEdit, QPushButton, QHBoxLayout, QLabel, 
                            QSystemTrayIcon, QMenu, QAction, QStatusBar)
from PyQt5.QtCore import Qt, pyqtSignal, QThread
from PyQt5.QtGui import QIcon, QTextCursor

# Import AMD-specific libraries if available
try:
    from optimum.amd import AMDONNXModel
    from transformers import AutoTokenizer, TextIteratorStreamer
    AMD_SUPPORT = True
except ImportError:
    AMD_SUPPORT = False

# Set up logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("AMD-Ryzen-AI-Interface")

# Log system info
logger.info(f"PyTorch version: {torch.__version__}")
logger.info(f"CUDA available: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    logger.info(f"CUDA device: {torch.cuda.get_device_name(0)}")
logger.info(f"AMD Optimum support: {AMD_SUPPORT}")

class GenerateThread(QThread):
    """Thread for text generation"""
    response_started = pyqtSignal()
    response_chunk = pyqtSignal(str)
    response_finished = pyqtSignal()
    error_occurred = pyqtSignal(str)
    
    def __init__(self, model_path, prompt, max_length=200):
        super().__init__()
        self.model_path = model_path
        self.prompt = prompt
        self.max_length = max_length
        self.model = None
        self.tokenizer = None
    
    def run(self):
        """Run the generation thread"""
        try:
            self.response_started.emit()
            
            # Check if AMD support is available
            if not AMD_SUPPORT:
                logger.warning("AMD Optimum not available, using simulation mode")
                self.simulate_response()
                return
            
            # Load model and tokenizer
            try:
                # Find the parent model for tokenizer (strip the AMD customizations)
                model_id = Path(self.model_path).name
                if "Llama-3" in model_id:
                    tokenizer_id = "meta-llama/Llama-3-8B"
                elif "Llama-2" in model_id:
                    tokenizer_id = "meta-llama/Llama-2-7b-hf"
                elif "Mistral" in model_id:
                    tokenizer_id = "mistralai/Mistral-7B-v0.3"
                elif "Phi" in model_id:
                    tokenizer_id = "microsoft/phi-3-mini"
                elif "Qwen" in model_id:
                    tokenizer_id = "Qwen/Qwen1.5-7B"
                else:
                    # Generic fallback
                    tokenizer_id = "gpt2"
                    
                logger.info(f"Loading tokenizer from {tokenizer_id}")
                self.tokenizer = AutoTokenizer.from_pretrained(tokenizer_id)
                
                logger.info(f"Loading model from {self.model_path}")
                self.model = AMDONNXModel.from_pretrained(self.model_path)
                
                # Generate text
                self.generate_with_model()
            except Exception as e:
                logger.error(f"Error loading or running model: {str(e)}")
                self.simulate_response()
        except Exception as e:
            logger.error(f"Error in generation thread: {str(e)}")
            self.error_occurred.emit(str(e))
    
    def simulate_response(self):
        """Simulate a response when the model can't be loaded"""
        chunks = [
            "This is a simulated response. ",
            "The AMD-optimized model couldn't be loaded with hardware acceleration. ",
            "You need to install the full AMD Ryzen AI Software stack with NPU support. ",
            "The KDE Plasma desktop environment is highly customizable and feature-rich. ",
            "It includes a powerful panel system, widgets, virtual desktops, and extensive theming options."
        ]
        
        for chunk in chunks:
            time.sleep(0.3)
            self.response_chunk.emit(chunk)
        
        self.response_finished.emit()
    
    def generate_with_model(self):
        """Generate text using the model"""
        try:
            logger.info(f"Generating text for prompt: '{self.prompt}'")
            
            # Tokenize the prompt
            inputs = self.tokenizer(self.prompt, return_tensors="pt")
            
            # Set up the streamer
            streamer = TextIteratorStreamer(self.tokenizer, skip_special_tokens=True)
            
            # Set up generation kwargs
            generation_kwargs = {
                "input_ids": inputs["input_ids"],
                "attention_mask": inputs["attention_mask"],
                "max_length": self.max_length,
                "streamer": streamer,
            }
            
            # Start generation in a separate thread
            generation_thread = threading.Thread(
                target=self.model.generate, 
                kwargs=generation_kwargs
            )
            generation_thread.start()
            
            # Stream the output
            for text in streamer:
                self.response_chunk.emit(text)
                
            # Signal completion
            self.response_finished.emit()
            
        except Exception as e:
            logger.error(f"Error generating text: {str(e)}")
            self.error_occurred.emit(str(e))
            self.simulate_response()

class AMDRyzenAIInterface(QMainWindow):
    """Main window for the AMD Ryzen AI Interface"""
    def __init__(self):
        super().__init__()
        
        # Set model path
        self.model_path = os.path.join(os.getcwd(), "amd-model")
        
        # Initialize UI
        self.init_ui()
    
    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("KDE AI Interface - AMD Ryzen AI")
        self.setGeometry(100, 100, 800, 500)
        self.setWindowFlags(Qt.Window | Qt.WindowStaysOnTopHint)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Add header label
        header = QLabel("KDE AI Interface - AMD Ryzen AI Powered")
        header.setStyleSheet("font-size: 18px; font-weight: bold; margin-bottom: 10px;")
        header.setAlignment(Qt.AlignCenter)
        layout.addWidget(header)
        
        # Add hardware info label
        hardware_info = QLabel()
        if AMD_SUPPORT:
            hardware_info.setText("AMD Ryzen AI Support: Available")
            hardware_info.setStyleSheet("color: green;")
        else:
            hardware_info.setText("AMD Ryzen AI Support: Not Available (Simulation Mode)")
            hardware_info.setStyleSheet("color: red;")
        layout.addWidget(hardware_info)
        
        # Add chat display
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        layout.addWidget(self.chat_display)
        
        # Add input area
        input_layout = QHBoxLayout()
        
        self.prompt_input = QTextEdit()
        self.prompt_input.setPlaceholderText("Type your message here...")
        self.prompt_input.setMaximumHeight(100)
        input_layout.addWidget(self.prompt_input)
        
        send_button = QPushButton("Send")
        send_button.clicked.connect(self.send_message)
        input_layout.addWidget(send_button)
        
        layout.addLayout(input_layout)
        
        # Add status bar
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage("Ready")
        
        # Add system tray icon
        self.setup_tray()
        
        # Add welcome message
        self.add_assistant_message("Welcome to the KDE AI Interface powered by AMD Ryzen AI! How can I help you today?")
    
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
    
    def add_user_message(self, message):
        """Add a user message to the chat display"""
        self.chat_display.append(f"<p><b>You:</b><br>{message}</p>")
        self.scroll_to_bottom()
    
    def add_assistant_message(self, message):
        """Add an assistant message to the chat display"""
        self.chat_display.append(f"<p><b>Assistant:</b><br>{message}</p>")
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
        
        # Start generation thread
        self.generate_thread = GenerateThread(self.model_path, prompt)
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
    
    def on_response_finished(self):
        """Handle response generation completed"""
        self.statusBar.showMessage("Response complete", 3000)
        # Add an empty line after the response
        self.chat_display.append("")
    
    def on_error(self, error_message):
        """Handle error during generation"""
        self.statusBar.showMessage(f"Error: {error_message}")
        self.add_assistant_message(f"Error: {error_message}")

def main():
    """Main function"""
    app = QApplication(sys.argv)
    app.setApplicationName("AMD Ryzen AI Interface")
    
    # Set up dark style
    try:
        import qdarkstyle
        app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
        print("QDarkStyle applied")
    except ImportError:
        print("QDarkStyle not available, using default style")
    
    # Create and show the main window
    window = AMDRyzenAIInterface()
    window.show()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()