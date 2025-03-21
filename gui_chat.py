#!/usr/bin/env python3
import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QTextEdit, QLineEdit, QPushButton)
from PyQt6.QtCore import Qt
import qdarkstyle

class KDEAIWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()
        
    def initUI(self):
        self.setWindowTitle('KDE AI Assistant')
        self.setGeometry(100, 100, 600, 400)
        
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Chat display area
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        layout.addWidget(self.chat_display)
        
        # Input field
        self.input_field = QLineEdit()
        self.input_field.returnPressed.connect(self.send_message)
        layout.addWidget(self.input_field)
        
        # Send button
        self.send_button = QPushButton('Send')
        self.send_button.clicked.connect(self.send_message)
        layout.addWidget(self.send_button)
        
        # Add welcome message
        self.chat_display.append('KDE AI Assistant: Hello! How can I help you today?')
        
    def send_message(self):
        user_message = self.input_field.text().strip()
        if user_message:
            # Display user message
            self.chat_display.append(f'You: {user_message}')
            
            # Clear input field
            self.input_field.clear()
            
            # Simple response simulation
            response = "This is a demonstration of the KDE AI Assistant interface. In the full version, this would connect to an AI model."
            self.chat_display.append(f'Assistant: {response}\n')

def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(qdarkstyle.load_stylesheet(qt_api='pyqt6'))
    
    window = KDEAIWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
