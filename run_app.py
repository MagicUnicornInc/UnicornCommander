#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QSettings

# Import necessary modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Create application
app = QApplication(sys.argv)
app.setApplicationName("KDE AI Interface")
app.setApplicationDisplayName("KDE AI Assistant")
app.setOrganizationName("KDE")
app.setOrganizationDomain("kde.org")

# Import after application is created (using our patched code with Qt compatibility)
from app_root.config.settings import SettingsManager
from app_root.ui.main_window import MainWindow

def main():
    """Main entry point for the KDE AI Interface application"""
    # Initialize settings
    settings = SettingsManager()
    
    # Create and show main window
    main_window = MainWindow(settings)
    main_window.show()
    
    # Set application icon
    app.setWindowIcon(QIcon.fromTheme("assistant"))
    
    # Run the application
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()