#!/usr/bin/env python3
import sys
import json
import requests
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                            QTextEdit, QPushButton, QHBoxLayout, QScrollArea,
                            QSystemTrayIcon, QMenu, QAction)
from PyQt5.QtGui import QIcon, QKeySequence
from PyQt5.QtCore import Qt, pyqtSignal, QThread

try:
    from PyKF5.kglobalaccel import KGlobalAccel
    from PyKF5.knotifications import KNotification
    KDE_AVAILABLE = True
except ImportError:
    KDE_AVAILABLE = False
    print("KDE integration not available - some features disabled")

class OllamaThread(QThread):
    response_received = pyqtSignal(str)
    
    def __init__(self, prompt):
        super().__init__()
        self.prompt = prompt
        
    def run(self):
        try:
            response = requests.post('http://localhost:11434/api/generate',
                                   json={'model': 'llama2', 'prompt': self.prompt,
                                        'stream': False})
            if response.status_code == 200:
                result = response.json()
                self.response_received.emit(result['response'])
        except Exception as e:
            self.response_received.emit(f"Error: {str(e)}")

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("KDE AI Assistant")
        self.setWindowFlags(Qt.Dialog | Qt.WindowStaysOnTopHint)
        
        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        
        # Chat history scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_widget = QWidget()
        self.chat_layout = QVBoxLayout(scroll_widget)
        self.chat_layout.addStretch()
        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)
        
        # Input area
        input_layout = QHBoxLayout()
        self.input_field = QTextEdit()
        self.input_field.setFixedHeight(50)
        self.input_field.setPlaceholderText("Type your message here...")
        input_layout.addWidget(self.input_field)
        
        send_button = QPushButton("Send")
        send_button.clicked.connect(self.send_message)
        send_button.setDefault(True)
        input_layout.addWidget(send_button)
        layout.addLayout(input_layout)
        
        # Size and position
        self.resize(600, 400)
        self.center()
        
        # System tray
        self.setup_tray()
        
        # Global shortcut
        if KDE_AVAILABLE:
            self.setup_global_shortcut()
        
    def setup_tray(self):
        self.tray = QSystemTrayIcon(self)
        self.tray.setIcon(QIcon.fromTheme("assistant"))
        
        menu = QMenu()
        show_action = QAction("Show/Hide", self)
        show_action.triggered.connect(self.toggle_window)
        menu.addAction(show_action)
        
        quit_action = QAction("Quit", self)
        quit_action.triggered.connect(app.quit)
        menu.addAction(quit_action)
        
        self.tray.setContextMenu(menu)
        self.tray.show()
        self.tray.activated.connect(self.on_tray_activated)
    
    def on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.Trigger:
            self.toggle_window()
    
    def setup_global_shortcut(self):
        try:
            shortcut = QKeySequence("Alt+Space")
            KGlobalAccel.self().setGlobalShortcut(
                self,
                shortcut,
                shortcut,
                "Show/Hide KDE AI Assistant",
                "Toggle the AI Assistant window"
            )
        except Exception as e:
            print(f"Could not set up global shortcut: {e}")
    
    def toggle_window(self, reason=None):
        if self.isVisible():
            self.hide()
        else:
            self.show()
            self.raise_()
            self.activateWindow()
    
    def center(self):
        qr = self.frameGeometry()
        cp = app.primaryScreen().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())
        
    def create_message_widget(self, text, is_user=True):
        msg = QTextEdit()
        msg.setReadOnly(True)
        msg.setStyleSheet("""
            QTextEdit {
                background-color: %s;
                border: 1px solid #ccc;
                border-radius: 5px;
                padding: 8px;
            }
        """ % ("#e0e0e0" if is_user else "#f0f0f0"))
        
        role = "You" if is_user else "Assistant"
        msg.setHtml(f"<b>{role}:</b><br>{text}")
        
        # Calculate appropriate height
        height = msg.document().size().toSize().height() + 20
        msg.setFixedHeight(int(height))
        
        return msg
        
    def send_message(self):
        message = self.input_field.toPlainText().strip()
        if message:
            # Add user message to chat
            user_msg = self.create_message_widget(message, True)
            self.chat_layout.addWidget(user_msg)
            
            # Clear input field
            self.input_field.clear()
            
            # Create response widget early
            self.response_widget = self.create_message_widget("Thinking...", False)
            self.chat_layout.addWidget(self.response_widget)
            
            # Send to Ollama in a thread
            self.ollama_thread = OllamaThread(message)
            self.ollama_thread.response_received.connect(self.handle_response)
            self.ollama_thread.start()
    
    def handle_response(self, response):
        # Update response widget with actual response
        self.response_widget.setHtml(f"<b>Assistant:</b><br>{response}")
        height = self.response_widget.document().size().toSize().height() + 20
        self.response_widget.setFixedHeight(int(height))
        
        # Notify if window is hidden
        if not self.isVisible() and KDE_AVAILABLE:
            try:
                KNotification.event(
                    "message",
                    "AI Assistant Response",
                    "New response received",
                    "assistant"
                )
            except Exception as e:
                print(f"Could not send notification: {e}")

# Create application
app = QApplication(sys.argv)
app.setApplicationName("KDE AI Assistant")
app.setStyle("Breeze")  # Use KDE's Breeze theme

# Create and show window
window = MainWindow()
window.show()

# Start event loop
sys.exit(app.exec_())
