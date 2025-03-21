#!/bin/bash

# Run the KDE AI Interface with multiple backends (OpenAI, Ollama)

# Ensure we're in the right directory
cd "$(dirname "$0")"

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
elif [ -d "quark_env" ]; then
    source quark_env/bin/activate
fi

# Check if OpenAI package is installed, install if not
python -c "import openai" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "OpenAI package not found. Installing..."
    pip install openai
fi

# Check if requests package is installed, install if not
python -c "import requests" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "Requests package not found. Installing..."
    pip install requests
fi

# Run the KDE AI Interface
python openai_deepseek_gui.py

# Deactivate virtual environment
deactivate 2>/dev/null