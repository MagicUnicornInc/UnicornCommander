# Installation Guide

## Prerequisites

1. KDE Plasma 5 Desktop Environment
2. Python 3.8 or higher
3. pip (Python package manager)
4. Ollama installed and running locally
5. KDE Frameworks 5 development files

## System Dependencies

On Ubuntu/Debian:
```bash
sudo apt-get install python3-pyqt5 python3-pip python3-venv
sudo apt-get install kde-config-dev libkf5globalaccel-dev libkf5notifications-dev
```

On Fedora/RHEL:
```bash
sudo dnf install python3-qt5 python3-pip python3-virtualenv
sudo dnf install kf5-kglobalaccel-devel kf5-knotifications-devel
```

## Installation Steps

1. Create and activate a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate
```

2. Install Python dependencies:
```bash
pip install -r requirements.txt
```

3. Verify Ollama is running:
```bash
curl http://localhost:11434/api/models
```

4. Run the application:
```bash
python app_root/main.py
```

## Troubleshooting

1. If PyKF5 fails to import:
   - Verify KDE5 development files are installed
   - Check Python environment PATH includes KDE libraries

2. If Ollama connection fails:
   - Verify Ollama is running: `ps aux | grep ollama`
   - Check Ollama API is accessible: `curl http://localhost:11434/api/health`

3. If UI appears without proper theme:
   - Verify KDE5 Breeze theme is installed
   - Check QT_QPA_PLATFORMTHEME environment variable

## Development Setup

For development, additional tools are recommended:

```bash
pip install pylint black pytest
```

## Updating

To update to the latest version:

1. Pull latest changes:
```bash
git pull origin main
```

2. Update dependencies:
```bash
pip install -r requirements.txt --upgrade
```