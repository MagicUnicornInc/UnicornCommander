#!/usr/bin/env python3

import sys
from PyQt5.QtWidgets import QApplication
import importlib.util

# Create a minimal QApplication as early as possible
app = QApplication(sys.argv)

# Dynamically import the main module
spec = importlib.util.spec_from_file_location("main", "app_root/main.py")
main = importlib.util.module_from_spec(spec)
spec.loader.exec_module(main)

# Call the main function to run the application
main.main()
