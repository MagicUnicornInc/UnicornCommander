#!/bin/bash

# This script will run in simulation mode without hardware acceleration
# For full hardware acceleration, follow the instructions in ALTERNATIVE_PYTHON_INSTALL.md
# to install Python 3.11 and AMD Quark

echo "Running DeepSeek GUI in simulation mode..."
echo "For hardware acceleration, you need Python 3.9-3.11 with AMD Quark runtime installed."
echo "See ALTERNATIVE_PYTHON_INSTALL.md for installation instructions."
echo ""

# Set Python path
export PYTHONPATH="/home/ucadmin/GIT-Projects/KDE AI Interface/quark-integration:$PYTHONPATH"

# Run the GUI
cd "/home/ucadmin/GIT-Projects/KDE AI Interface/quark-integration"
python3 ./quark_deepseek_gui.py

# Exit with the same status code as the Python script
exit $?