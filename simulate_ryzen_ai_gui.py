#!/usr/bin/env python3
import sys
import os
import time
import threading
import random
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QTextEdit, QPushButton, QHBoxLayout, QLabel, 
                            QSystemTrayIcon, QMenu, QAction)
from PyQt5.QtCore import Qt, pyqtSignal, QThread
from PyQt5.QtGui import QIcon, QTextCursor

class GenerateThread(QThread):
    """Simulate AI response generation"""
    response_chunk = pyqtSignal(str)
    response_finished = pyqtSignal()
    
    def __init__(self, prompt):
        super().__init__()
        self.prompt = prompt
        
        # Simple response templates
        self.templates = [
            "The KDE Plasma desktop environment offers a customizable and feature-rich computing experience. It includes a panel with widgets, a powerful application launcher, virtual desktops, and extensive theming options.",
            "AMD's Ryzen AI technology integrates neural processing units (NPUs) into CPUs, enabling efficient AI acceleration for tasks like natural language processing and computer vision while using less power than traditional CPU or GPU computation.",
            "The Model Context Protocol (MCP) is designed as a standardized way for AI models to access various data sources and tools. It allows AI assistants to maintain context across different applications and services.",
            "Local large language models (LLMs) offer privacy advantages by processing all data on your device without sending information to external servers. This approach protects sensitive information and works offline.",
            "The XDNA architecture in AMD's Ryzen AI chips is designed specifically for AI workloads, offering high performance while consuming minimal power. It's optimized for INT4/INT8 quantized models."
        ]
    
    def run(self):
        """Simulate generating a response"""
        # Choose a template based on the prompt
        if "kde" in self.prompt.lower():
            response = self.templates[0]
        elif "amd" in self.prompt.lower() or "ryzen" in self.prompt.lower() or "xdna" in self.prompt.lower():
            response = self.templates[1]
        elif "mcp" in self.prompt.lower() or "context" in self.prompt.lower():
            response = self.templates[2]
        elif "local" in self.prompt.lower() or "privacy" in self.prompt.lower():
            response = self.templates[3]
        else:
            response = random.choice(self.templates)
        
        # Simulate thinking time
        time.sleep(1)
        
        # Stream the response word by word
        words = response.split()
        for word in words:
            self.response_chunk.emit(word + " ")
            # Random delay between words
            time.sleep(0.05 + random.random() * 0.1)
        
        self.response_finished.emit()

class KDEAISimulator(QMainWindow):
    """Main window for the KDE AI Interface Simulator"""
    def __init__(self):
        super().__init__()
        self.init_ui()
    
    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("KDE AI Interface - Ryzen AI Simulator")
        self.setGeometry(100, 100, 800, 500)
        self.setWindowFlags(Qt.Window | Qt.WindowStaysOnTopHint)
        
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Header label
        header = QLabel("KDE AI Interface - Ryzen AI Powered (Simulation)")
        header.setStyleSheet("font-size: 18px; font-weight: bold; margin-bottom: 10px;")
        header.setAlignment(Qt.AlignCenter)
        layout.addWidget(header)
        
        # Status label
        self.status_label = QLabel("Status: Ready - Using Ryzen AI Simulation Mode")
        self.status_label.setStyleSheet("color: green;")
        layout.addWidget(self.status_label)
        
        # Create chat display
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        layout.addWidget(self.chat_display)
        
        # Create input area
        input_layout = QHBoxLayout()
        
        self.prompt_input = QTextEdit()
        self.prompt_input.setPlaceholderText("Type your message here...")
        self.prompt_input.setMaximumHeight(100)
        input_layout.addWidget(self.prompt_input)
        
        send_button = QPushButton("Send")
        send_button.clicked.connect(self.send_message)
        input_layout.addWidget(send_button)
        
        layout.addLayout(input_layout)
        
        # Setup system tray
        self.setup_tray()
        
        # Add welcome message
        self.add_assistant_message("Welcome to the KDE AI Interface! This is a simulation of how the Ryzen AI-powered assistant would work. Ask me about KDE, AMD Ryzen AI, or the MCP integration.")
    
    def setup_tray(self):
        """Set up the system tray icon"""
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(QIcon.fromTheme("assistant", QIcon.fromTheme("dialog-information")))
        
        # Create menu
        tray_menu = QMenu()
        
        show_action = QAction("Show/Hide", self)
        show_action.triggered.connect(self.toggle_window)
        tray_menu.addAction(show_action)
        
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
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
        """Send a message and get a simulated response"""
        # Get the message
        message = self.prompt_input.toPlainText().strip()
        if not message:
            return
        
        # Clear the input field
        self.prompt_input.clear()
        
        # Add user message to chat
        self.add_user_message(message)
        
        # Create assistant response placeholder
        self.chat_display.append("<p><b>Assistant:</b><br></p>")
        self.current_response = ""
        
        # Simulate response generation
        self.generate_thread = GenerateThread(message)
        self.generate_thread.response_chunk.connect(self.on_response_chunk)
        self.generate_thread.response_finished.connect(self.on_response_finished)
        self.generate_thread.start()
        
        # Update status
        self.status_label.setText("Status: Generating response...")
    
    def on_response_chunk(self, chunk):
        """Handle response chunk"""
        self.current_response += chunk
        
        # Update the last paragraph
        cursor = self.chat_display.textCursor()
        cursor.movePosition(QTextCursor.End)
        cursor.movePosition(QTextCursor.StartOfBlock, QTextCursor.KeepAnchor)
        cursor.removeSelectedText()
        cursor.insertHtml(f"<p><b>Assistant:</b><br>{self.current_response}</p>")
        
        self.scroll_to_bottom()
    
    def on_response_finished(self):
        """Handle response finished"""
        self.status_label.setText("Status: Ready - Using Ryzen AI Simulation Mode")
        self.chat_display.append("")  # Add empty line after response

def main():
    """Main function"""
    app = QApplication(sys.argv)
    app.setApplicationName("KDE AI Interface Simulator")
    
    # Try to apply QDarkStyle if available
    try:
        import qdarkstyle
        app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
        print("QDarkStyle applied")
    except ImportError:
        print("QDarkStyle not available, using default style")
    
    # Create and show the main window
    window = KDEAISimulator()
    window.show()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()