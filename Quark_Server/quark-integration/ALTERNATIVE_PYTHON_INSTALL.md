# Installing Python 3.11 for AMD Quark

Since AMD Quark requires Python 3.9-3.11 (and doesn't support Python 3.12), you'll need to install a compatible Python version.

## Option 1: Using System Package Manager (recommended)

If you're running Ubuntu/Debian:

```bash
# Update package lists
sudo apt update

# Install Python 3.11 and development tools
sudo apt install python3.11 python3.11-venv python3.11-dev

# Create a virtual environment with Python 3.11
python3.11 -m venv quark_py311_env

# Activate the environment
source quark_py311_env/bin/activate

# Install required packages
pip install pyqt5 qdarkstyle huggingface_hub
```

If you're running Fedora/RHEL/CentOS:

```bash
# Install Python 3.11
sudo dnf install python3.11 python3.11-devel

# Create a virtual environment
python3.11 -m venv quark_py311_env

# Activate the environment
source quark_py311_env/bin/activate

# Install required packages
pip install pyqt5 qdarkstyle huggingface_hub
```

## Option 2: Using PyEnv

PyEnv is a great tool for managing multiple Python versions:

```bash
# Install pyenv prerequisites
sudo apt install -y build-essential libssl-dev zlib1g-dev libbz2-dev \
  libreadline-dev libsqlite3-dev wget curl llvm libncurses5-dev libncursesw5-dev \
  xz-utils tk-dev libffi-dev liblzma-dev python-openssl git

# Install pyenv
curl https://pyenv.run | bash

# Add to your shell configuration
echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.bashrc
echo 'command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.bashrc
echo 'eval "$(pyenv init -)"' >> ~/.bashrc
source ~/.bashrc

# Install Python 3.11
pyenv install 3.11.8

# Use Python 3.11 in this directory
cd "/home/ucadmin/GIT-Projects/KDE AI Interface/quark-integration"
pyenv local 3.11.8

# Create a virtual environment
python -m venv quark_env
source quark_env/bin/activate

# Install required packages
pip install pyqt5 qdarkstyle huggingface_hub
```

## Option 3: Using Miniconda/Anaconda

If you have Miniconda or Anaconda installed:

```bash
# Create a new environment with Python 3.11
conda create -n quark_env python=3.11

# Activate the environment
conda activate quark_env

# Install required packages
pip install pyqt5 qdarkstyle huggingface_hub
```

## Installing AMD Quark

After setting up a compatible Python environment:

1. Extract the AMD Quark package:
   ```bash
   cd "/home/ucadmin/GIT-Projects/KDE AI Interface" 
   mkdir -p quark_install 
   unzip amd_quark-0.8rc3.zip -d quark_install
   ```

2. Install the wheel file:
   ```bash
   # Make sure you're in your Python 3.11 environment
   pip install quark_install/amd_quark-0.8rc3/amd_quark-0.8rc3-py3-none-any.whl
   ```

3. Test the installation:
   ```python
   python -c "import quark; print(quark.__version__); print(quark.get_available_backends())"
   ```

4. Launch the application:
   ```bash
   python quark_deepseek_gui.py
   ```