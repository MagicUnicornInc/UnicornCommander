import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QTextEdit, QLineEdit, QPushButton, QVBoxLayout, QWidget, QSystemTrayIcon
from PyQt6.QtGui import QIcon
import qdarkstyle

class KDEAIWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('KDE AI Assistant')
        self.setGeometry(100, 100, 400, 300)

        # System tray
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(QIcon('send_icon.png'))  # Use a specific icon
        self.tray_icon.setVisible(True)

        # Central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Chat display area with KDE-style formatting
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.setStyleSheet('''
            QTextEdit {
                border: 1px solid #3daee9;
                border-radius: 4px;
                padding: 2px;
            }
        ''')
        layout.addWidget(self.chat_display)

        # Input field with KDE-style
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText('Type your message here...')
        self.input_field.returnPressed.connect(self.send_message)
        self.input_field.setStyleSheet('''
            QLineEdit {
                border: 1px solid #3daee9;
                border-radius: 4px;
                padding: 4px;
            }
        ''')
        layout.addWidget(self.input_field)

        # Send button with icon and KDE-style
        self.send_button = QPushButton('Send')
        self.send_button.setIcon(QIcon('send_icon.png'))  # Use a specific icon
        self.send_button.setStyleSheet('''
            QPushButton {
                background-color: #3daee9;
                border: none;
                border-radius: 4px;
                padding: 6px;
                color: white;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        ''')
        self.send_button.clicked.connect(self.send_message)
        layout.addWidget(self.send_button)

        # Clear chat button
        self.clear_button = QPushButton('Clear Chat')
        self.clear_button.setStyleSheet('''
            QPushButton {
                background-color: #ff0000;
                border: none;
                border-radius: 4px;
                padding: 6px;
                color: white;
            }
            QPushButton:hover {
                background-color: #cc0000;
            }
        ''')
        self.clear_button.clicked.connect(self.clear_chat)
        layout.addWidget(self.clear_button)

        # Add welcome message
        self.chat_display.append('KDE AI Assistant: Welcome to the KDE AI Assistant! How can I help you today?')

    def send_message(self):
        user_message = self.input_field.text().strip()
        if user_message:
            # Display user message
            self.chat_display.append(f'You: {user_message}')
            # Clear input field
            self.input_field.clear()
            # Simulated response
            response = "I'm a demonstration of the KDE AI Assistant interface. In the full version, I would be connected to an AI model and integrated with KDE services."
            self.chat_display.append(f'Assistant: {response}
            self.chat_display.append(f'Assistant: {response}
')
')
')
')

    def clear_chat(self):
        self.chat_display.clear()  # Clear the chat display

def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(qdarkstyle.load_stylesheet(qt_api='pyqt6'))
    window = KDEAIWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
