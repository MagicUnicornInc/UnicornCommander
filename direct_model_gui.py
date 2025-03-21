#!/usr/bin/env python3
import os
import sys
import time
import logging
import threading
import numpy as np
import onnxruntime as ort
from pathlib import Path
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                           QTextEdit, QPushButton, QHBoxLayout, QLabel, 
                           QSystemTrayIcon, QMenu, QAction)
from PyQt5.QtCore import Qt, pyqtSignal, QThread
from PyQt5.QtGui import QIcon, QTextCursor

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("Direct-Model-GUI")

# Print ONNX Runtime info
logger.info(f"ONNX Runtime version: {ort.__version__}")
providers = ort.get_available_providers()
logger.info(f"Available ONNX Runtime providers: {providers}")

class DirectModelThread(QThread):
    """Thread for text generation using the model directly without optimum-amd"""
    response_started = pyqtSignal()
    response_chunk = pyqtSignal(str)
    response_finished = pyqtSignal()
    error_occurred = pyqtSignal(str)
    
    def __init__(self, model_path, prompt, max_length=200):
        super().__init__()
        self.model_path = model_path
        self.prompt = prompt
        self.max_length = max_length
        
    def run(self):
        """Run the generation thread"""
        try:
            self.response_started.emit()
            logger.info(f"Attempting to load model from {self.model_path}")
            
            # Try direct ONNX inference
            try:
                self.direct_onnx_inference()
            except Exception as e:
                logger.error(f"Direct ONNX inference failed: {str(e)}")
                self.simulate_response()
                
        except Exception as e:
            logger.error(f"Error in generation thread: {str(e)}")
            self.error_occurred.emit(str(e))
    
    def direct_onnx_inference(self):
        """Try to directly use ONNX Runtime to run the model"""
        try:
            # First, check if tokenizer files are available
            model_dir = Path(self.model_path).parent
            tokenizer_path = model_dir / "tokenizer.json"
            
            if not tokenizer_path.exists():
                raise FileNotFoundError(f"Tokenizer not found at {tokenizer_path}")
            
            # Load tokenizer from the local directory
            from transformers import PreTrainedTokenizerFast
            logger.info(f"Loading tokenizer from {model_dir}")
            tokenizer = PreTrainedTokenizerFast(
                tokenizer_file=str(tokenizer_path),
                bos_token="<s>",
                eos_token="</s>",
                unk_token="<unk>",
                pad_token="</s>"
            )
            
            # Try to create a session with CPU provider
            logger.info("Creating ONNX Runtime session with CPU provider")
            sess_options = ort.SessionOptions()
            sess_options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
            
            try:
                session = ort.InferenceSession(
                    str(self.model_path), 
                    sess_options=sess_options,
                    providers=['CPUExecutionProvider']
                )
                
                # Log inputs and outputs
                inputs = session.get_inputs()
                outputs = session.get_outputs()
                logger.info(f"Model inputs: {[x.name for x in inputs]}")
                logger.info(f"Model outputs: {[x.name for x in outputs]}")
                
                # Tokenize the prompt
                logger.info(f"Tokenizing prompt: {self.prompt}")
                tokens = tokenizer(self.prompt, return_tensors="np")
                input_ids = tokens["input_ids"]
                attention_mask = tokens["attention_mask"]
                
                # Run inference (this likely won't work without custom ops)
                logger.info("Running inference...")
                outputs = session.run(
                    None, 
                    {
                        "input_ids": input_ids,
                        "attention_mask": attention_mask
                    }
                )
                
                # Process output
                logger.info("Processing outputs...")
                output_ids = outputs[0]
                response = tokenizer.decode(output_ids[0], skip_special_tokens=True)
                
                # Output response in chunks
                words = response.split()
                for word in words:
                    time.sleep(0.05)
                    self.response_chunk.emit(word + " ")
                
                self.response_finished.emit()
                return
                
            except Exception as e:
                logger.error(f"ONNX session run failed: {str(e)}")
                raise
                
        except Exception as e:
            logger.error(f"Error in direct_onnx_inference: {str(e)}")
            raise
    
    def simulate_response(self):
        """Simulate a response when the model can't be loaded"""
        logger.info("Using simulation mode")
        chunks = [
            "I'm currently running in simulation mode. ",
            "The Llama 3.2 model couldn't be loaded directly because it requires custom AMD operators. ",
            "To run this model on the NPU, you need to install the full AMD Ryzen AI Software stack with Vitis AI support. ",
            "This model is quantized to INT4 specifically for the XDNA NPU and contains special operators not available in standard ONNX Runtime."
        ]
        
        for chunk in chunks:
            time.sleep(0.5)
            self.response_chunk.emit(chunk)
        
        self.response_finished.emit()

class DirectModelGUI(QMainWindow):
    """Main window for the direct model GUI"""
    def __init__(self):
        super().__init__()
        
        # Set model path
        self.model_path = os.path.join(os.getcwd(), "amd-ryzen-ai", "amd-model", "model.onnx")
        # Verify if the path exists
        if not os.path.exists(self.model_path):
            logger.warning(f"Model not found at {self.model_path}, searching for it...")
            # Try to find the model
            from pathlib import Path
            for path in Path("/home/ucadmin").glob("**/model.onnx"):
                if "amd-ryzen-ai" in str(path) or "amd-model" in str(path):
                    logger.info(f"Found model at {path}")
                    self.model_path = str(path)
                    break
        
        # Initialize UI
        self.init_ui()
    
    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("KDE AI Interface - Direct Model Test")
        self.setGeometry(100, 100, 800, 500)
        self.setWindowFlags(Qt.Window | Qt.WindowStaysOnTopHint)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Add header label
        header = QLabel("KDE AI Interface - Llama 3.2 Direct Model Test")
        header.setStyleSheet("font-size: 18px; font-weight: bold; margin-bottom: 10px;")
        header.setAlignment(Qt.AlignCenter)
        layout.addWidget(header)
        
        # Add hardware info label
        self.status_label = QLabel()
        if os.path.exists(self.model_path):
            self.status_label.setText(f"Model found: {self.model_path}")
            self.status_label.setStyleSheet("color: green;")
        else:
            self.status_label.setText(f"Model not found at {self.model_path}")
            self.status_label.setStyleSheet("color: red;")
        layout.addWidget(self.status_label)
        
        # Add providers info
        providers_label = QLabel(f"ONNX Runtime providers: {', '.join(providers)}")
        layout.addWidget(providers_label)
        
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
        
        # Add system tray icon
        self.setup_tray()
        
        # Add welcome message
        self.add_assistant_message("Welcome to the KDE AI Interface direct model test. This interface attempts to use the Llama 3.2 model directly with ONNX Runtime.")
    
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
        self.generate_thread = DirectModelThread(self.model_path, prompt)
        self.generate_thread.response_started.connect(self.on_response_started)
        self.generate_thread.response_chunk.connect(self.on_response_chunk)
        self.generate_thread.response_finished.connect(self.on_response_finished)
        self.generate_thread.error_occurred.connect(self.on_error)
        self.generate_thread.start()
    
    def on_response_started(self):
        """Handle response generation started"""
        self.status_label.setText("Generating response...")
    
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
        self.status_label.setText("Response complete")
        # Add an empty line after the response
        self.chat_display.append("")
    
    def on_error(self, error_message):
        """Handle error during generation"""
        self.status_label.setText(f"Error: {error_message}")
        self.add_assistant_message(f"Error: {error_message}")

def main():
    """Main function"""
    app = QApplication(sys.argv)
    app.setApplicationName("KDE AI Direct Model Interface")
    
    # Set up dark style
    try:
        import qdarkstyle
        app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
        print("QDarkStyle applied")
    except ImportError:
        print("QDarkStyle not available, using default style")
    
    # Create and show the main window
    window = DirectModelGUI()
    window.show()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()