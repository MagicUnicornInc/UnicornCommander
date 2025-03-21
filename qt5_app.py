#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import logging

# Force PyQt5 mode by making PyQt6 import fail
sys.modules['PyQt6'] = None

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("KDE-AI-Interface")

# Import PyQt5 (what we have installed)
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QSettings

# Add project root to sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def main():
    """Main entry point for the KDE AI Interface application"""
    logger.info("Starting KDE AI Interface")
    
    # Create application
    app = QApplication(sys.argv)
    app.setApplicationName("KDE AI Interface")
    app.setApplicationDisplayName("KDE AI Assistant")
    app.setOrganizationName("KDE")
    app.setOrganizationDomain("kde.org")
    
    # Import after application is created (using our patched code with Qt compatibility)
    from app_root.config.settings import SettingsManager
    
    try:
        # Import main window class
        logger.info("Importing MainWindow...")
        from app_root.ui.main_window import MainWindow
        
        # Initialize settings
        settings = SettingsManager()
        logger.info("Settings initialized")
        
        # Create and show main window
        main_window = MainWindow(settings)
        main_window.show()
        logger.info("Main window created and shown")
        
        # Set application icon
        app.setWindowIcon(QIcon.fromTheme("assistant"))
        
        # Run the application
        return app.exec_()
        
    except ImportError as e:
        logger.error(f"Import error: {e}")
        from PyQt5.QtWidgets import QMessageBox
        QMessageBox.critical(None, "Error", 
                           f"Failed to initialize application: {str(e)}\n\n"
                           "This may be due to a PyQt version mismatch. "
                           "Please check your installation.")
        return 1
    except Exception as e:
        logger.error(f"Initialization error: {e}", exc_info=True)
        from PyQt5.QtWidgets import QMessageBox
        QMessageBox.critical(None, "Error", 
                           f"Failed to initialize application: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())