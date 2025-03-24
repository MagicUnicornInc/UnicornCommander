#!/bin/bash

# Script to run the Unified AI Interface with proper Python environment

# Ensure we're in the correct directory
cd "$(dirname "$0")"

# Check if venv exists and activate it
if [ -d "venv" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
else
    echo "Virtual environment not found. Please create it with:"
    echo "python -m venv venv"
    echo "venv/bin/pip install -r requirements.txt"
    exit 1
fi

# Check if OpenAI API key is set
if [ -z "$OPENAI_API_KEY" ]; then
    # Try to load from .env file if it exists
    if [ -f ".env" ]; then
        echo "Loading OpenAI API key from .env file..."
        export $(grep -v '^#' .env | xargs)
    else
        echo "Warning: OPENAI_API_KEY environment variable not set."
        echo "The OpenAI backend will not work without an API key."
        echo "You can set it in a .env file or directly in this terminal with:"
        echo "export OPENAI_API_KEY=your_api_key_here"
    fi
fi

# Launch the application
echo "Starting Unified AI Interface..."
python unified_ai_gui.py