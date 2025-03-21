#!/usr/bin/env python3
import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QTextEdit, QPushButton, QLineEdit, QLabel, QHBoxLayout,
                            QSystemTrayIcon, QMenu, QAction)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon

class SimpleKDEAIWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()
        
    def initUI(self):
        self.setWindowTitle('KDE AI Interface Demo')
        self.setGeometry(100, 100, 600, 500)
        self.setWindowFlags(Qt.Window | Qt.WindowStaysOnTopHint)
        
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Header label
        header = QLabel("KDE AI Interface Demo")
        header.setStyleSheet("font-size: 18px; font-weight: bold; margin-bottom: 10px;")
        header.setAlignment(Qt.AlignCenter)
        layout.addWidget(header)
        
        # Chat display area
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        layout.addWidget(self.chat_display)
        
        # Input area
        input_layout = QHBoxLayout()
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText('Type your message here...')
        self.input_field.returnPressed.connect(self.send_message)
        input_layout.addWidget(self.input_field)
        
        self.send_button = QPushButton('Send')
        self.send_button.clicked.connect(self.send_message)
        input_layout.addWidget(self.send_button)
        layout.addLayout(input_layout)
        
        # Add welcome message
        self.chat_display.append('<b>KDE AI Assistant:</b> Welcome to the KDE AI Interface demo! How can I help you today?')
        
        # Set up system tray icon
        self.setup_tray()
        
    def setup_tray(self):
        """Set up system tray icon and menu"""
        self.tray_icon = QSystemTrayIcon(self)
        
        # Use a standard icon or load from a file
        self.tray_icon.setIcon(QIcon.fromTheme("assistant", 
                                              QIcon.fromTheme("system-help")))
        
        # Create tray menu
        tray_menu = QMenu()
        
        # Show/Hide action
        show_action = QAction("Show/Hide", self)
        show_action.triggered.connect(self.toggle_visibility)
        tray_menu.addAction(show_action)
        
        # Exit action
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        tray_menu.addAction(exit_action)
        
        # Set the menu and show the tray icon
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self.tray_icon_activated)
        self.tray_icon.show()
        
    def tray_icon_activated(self, reason):
        """Handle tray icon activation (click)"""
        if reason == QSystemTrayIcon.Trigger:
            self.toggle_visibility()
            
    def toggle_visibility(self):
        """Toggle window visibility"""
        if self.isVisible():
            self.hide()
        else:
            self.show()
            self.raise_()
            self.activateWindow()
        
    def send_message(self):
        user_message = self.input_field.text().strip()
        if user_message:
            # Display user message
            self.chat_display.append(f'<b>You:</b> {user_message}')
            
            # Clear input field
            self.input_field.clear()
            
            # Simulate "thinking"
            QApplication.processEvents()
            
            # Simulated response - in real version, this would connect to an AI model
            response = "This is a demonstration of the KDE AI Interface. In the full version, I would connect to an AI model like Llama or respond to your queries in a more intelligent way."
            self.chat_display.append(f'<b>Assistant:</b> {response}')
            self.chat_display.append('') # Add empty line for spacing
            
def main():
    app = QApplication(sys.argv)
    
    # Try to apply QDarkStyle if available
    try:
        import qdarkstyle
        app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
        print("QDarkStyle applied")
    except ImportError:
        print("QDarkStyle not available, using default style")
        
    window = SimpleKDEAIWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()