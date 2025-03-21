#!/usr/bin/env python3
"""
KDE AI Interface with AMD Quark and DeepSeek-R1 Distill models

This GUI application provides a KDE-compatible interface to DeepSeek-R1 models
using AMD's Quark framework for hardware acceleration on Ryzen AI processors.
"""

import os
import sys
import logging
import time
import threading
from pathlib import Path
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QTextEdit, QPushButton, QHBoxLayout, QLabel, 
                            QSystemTrayIcon, QMenu, QAction, QStatusBar,
                            QComboBox, QCheckBox, QSpinBox, QGroupBox, QGridLayout,
                            QSplitter, QListWidget, QListWidgetItem, QTreeWidget, QTreeWidgetItem,
                            QFrame, QSizePolicy, QScrollArea, QToolButton, QPushButton)
from PyQt5.QtCore import Qt, pyqtSignal, QThread, QTimer, QSize
from PyQt5.QtGui import QIcon, QTextCursor, QFont, QPixmap, QColor

# Set up logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("QuarkDeepSeekGUI")

# Check if Quark is installed
try:
    import quark
    QUARK_AVAILABLE = True
    logger.info(f"Quark version: {quark.__version__}")
except ImportError:
    QUARK_AVAILABLE = False
    logger.warning("Quark not available. AMD Quark requires Python 3.9-3.11, but found " + 
                 '.'.join(map(str, [sys.version_info.major, sys.version_info.minor, sys.version_info.micro])))

# Check for huggingface_hub
try:
    from huggingface_hub import snapshot_download
    HF_HUB_AVAILABLE = True
except ImportError:
    HF_HUB_AVAILABLE = False
    logger.warning("huggingface_hub not available, will use local models only")

# Default models to try - ordered by size (largest first)
DEFAULT_MODELS = [
    "deepseek-ai/deepseek-coder-6.7b-instruct",  # Large model, good for coding
    "deepseek-ai/deepseek-coder-1.3b-instruct",  # Smaller coding model
    "TheBloke/deepseek-coder-6.7B-instruct-GGUF",  # GGUF version for better compatibility
    "TheBloke/deepseek-coder-1.3B-instruct-GGUF"  # GGUF version, smaller model
]

class GenerateThread(QThread):
    """Thread for text generation"""
    response_started = pyqtSignal()
    response_chunk = pyqtSignal(str)
    response_finished = pyqtSignal(dict)  # Signal with performance metrics
    error_occurred = pyqtSignal(str)
    
    def __init__(self, model_path, prompt, model_config=None):
        super().__init__()
        self.model_path = model_path
        self.prompt = prompt
        self.model_config = model_config or {}
        self.model = None
        
    def run(self):
        """Run the generation thread"""
        try:
            self.response_started.emit()
            
            # Check if Quark is available - now simulation is handled in generate_with_quark
            if not QUARK_AVAILABLE:
                logger.info("Quark not available, running in simulation mode")
                # Proceed to generate_with_quark which will handle simulation
                self.generate_with_quark()
                return
            
            # Load model if needed (only executes when Quark is available)
            try:
                # Set up the model
                logger.info(f"Loading model from {self.model_path}")
                
                # Initialize the backend
                backends = quark.get_available_backends()
                logger.info(f"Available backends: {backends}")
                
                # Choose backend - prefer XDNA, then ROCm, then CPU
                preferred_backends = ["AMD_XDNA", "AMD_ROCm", "CPU"]
                selected_backend = None
                
                for backend in preferred_backends:
                    if backend in backends:
                        selected_backend = backend
                        break
                
                if not selected_backend and backends:
                    selected_backend = backends[0]
                
                # Find model file (ONNX or GGUF)
                model_dir = Path(self.model_path)
                model_file = None
                
                # Look for model files, in order of preference
                for pattern in ["*int4*.onnx", "*int8*.onnx", "*.onnx", "*.gguf", "*.bin"]:
                    files = list(model_dir.glob(pattern))
                    if files:
                        model_file = str(files[0])
                        logger.info(f"Found model file: {model_file}")
                        break
                
                if not model_file:
                    raise FileNotFoundError(f"No compatible model file found in {model_dir}")
                
                # Find tokenizer (might be tokenizer.json, tokenizer.model, or config.json)
                tokenizer_file = None
                for tokenizer_name in ["tokenizer.json", "tokenizer.model", "config.json"]:
                    potential_file = model_dir / tokenizer_name
                    if potential_file.exists():
                        tokenizer_file = str(potential_file)
                        logger.info(f"Found tokenizer file: {tokenizer_file}")
                        break
                
                if not tokenizer_file:
                    raise FileNotFoundError(f"No tokenizer file found in {model_dir}")
                
                # Set up configuration
                config = {
                    "model_path": model_file,
                    "tokenizer_path": str(tokenizer_file),
                    "temperature": self.model_config.get("temperature", 0.7),
                    "top_p": self.model_config.get("top_p", 0.9),
                }
                
                # Only add backend if it's available and we're using ONNX files
                if selected_backend and model_file.endswith(".onnx"):
                    config["backend"] = selected_backend
                    
                # Apply additional config parameters
                for key, value in self.model_config.items():
                    if key not in config:
                        config[key] = value
                
                logger.info(f"Using config: {config}")
                
                try:
                    # Initialize model
                    self.model = quark.Model(**config)
                    
                    # Generate text
                    self.generate_with_quark()
                except Exception as e:
                    logger.error(f"Model initialization error: {str(e)}")
                    # Try simplified config if first attempt fails
                    if "backend" in config:
                        simplified_config = config.copy()
                        simplified_config.pop("backend")
                        logger.info(f"Retrying with simplified config: {simplified_config}")
                        try:
                            self.model = quark.Model(**simplified_config)
                            self.generate_with_quark()
                        except Exception as e2:
                            raise Exception(f"Failed with both configurations: {str(e)} and then {str(e2)}")
                    else:
                        raise
                
            except Exception as e:
                logger.error(f"Error loading or running model: {str(e)}")
                self.show_error(f"Failed to load or run model: {str(e)}")
        except Exception as e:
            logger.error(f"Error in generation thread: {str(e)}")
            self.error_occurred.emit(str(e))
    
    def show_error(self, error_message):
        """Show error message instead of simulating a response"""
        error_text = f"ERROR: {error_message}\n\nPlease ensure AMD Quark is properly installed with hardware acceleration for your Ryzen AI processor."
        self.error_occurred.emit(error_text)
    
    def generate_with_quark(self):
        """Generate text using Quark"""
        try:
            logger.info(f"Generating text for prompt: '{self.prompt}'")
            
            # Import modules needed for simulation
            import random
            
            # Start timing
            start_time = time.time()
            total_tokens = 0
            
            if not QUARK_AVAILABLE:
                # Simulation mode for development/testing
                logger.warning("Quark not available, using simulation mode")
                
                # Example response for simulation
                responses = [
                    "I'm running in simulation mode since Quark is not installed.",
                    "This is a simulated response to demonstrate the interface functionality.",
                    "The DeepSeek Coder model would normally generate code or provide assistance here.",
                    f"Your prompt was: '{self.prompt}'",
                    "To get actual AI responses, you need to install AMD Quark runtime for Python 3.9-3.11.",
                    "Check AMD_QUARK_SETUP.md for detailed installation instructions.",
                ]
                
                # Stream tokens with realistic timing
                for response in responses:
                    words = response.split()
                    for word in words:
                        total_tokens += 1
                        self.response_chunk.emit(word + " ")
                        time.sleep(0.05 + random.random() * 0.1)  # Simulate typing speed
                
                # Add code block if the prompt seems to be asking for code
                if any(code_word in self.prompt.lower() for code_word in ["code", "function", "script", "program", "write"]):
                    self.response_chunk.emit("\n\n```python\n")
                    code_sample = [
                        "def hello_world():",
                        "    \"\"\"Example function to demonstrate code formatting\"\"\"",
                        "    print('Hello from DeepSeek Coder simulation!')",
                        "    return True",
                        "",
                        "# This is simulated code",
                        "# In an actual Quark environment, the AI would generate",
                        "# relevant code based on your prompt",
                        "",
                        "if __name__ == '__main__':",
                        "    hello_world()",
                    ]
                    
                    for line in code_sample:
                        total_tokens += len(line.split())
                        self.response_chunk.emit(line + "\n")
                        time.sleep(0.1 + random.random() * 0.2)
                        
                    self.response_chunk.emit("```")
            else:
                # Real Quark inference
                for token in self.model.stream(self.prompt):
                    total_tokens += 1
                    self.response_chunk.emit(token + " ")
            
            # End timing
            end_time = time.time()
            duration = end_time - start_time
            tokens_per_second = total_tokens / duration if duration > 0 else 0
            
            # Collect metrics
            metrics = {
                "duration": duration,
                "token_count": total_tokens,
                "tokens_per_second": tokens_per_second,
                "backend": self.model_config.get("backend", "Simulation")
            }
            
            logger.info(f"Generated {total_tokens} tokens in {duration:.2f}s ({tokens_per_second:.2f} tokens/sec)")
            
            # Signal completion with metrics
            self.response_finished.emit(metrics)
            
        except Exception as e:
            logger.error(f"Error generating text: {str(e)}")
            self.show_error(f"Error generating text: {str(e)}")

class ModelDownloadThread(QThread):
    """Thread for downloading models"""
    download_started = pyqtSignal(str)
    download_progress = pyqtSignal(int, int)  # current, total
    download_finished = pyqtSignal(str)  # path
    download_error = pyqtSignal(str)  # error message
    
    def __init__(self, model_name):
        super().__init__()
        self.model_name = model_name
    
    def run(self):
        """Run the download thread"""
        try:
            self.download_started.emit(f"Downloading {self.model_name}...")
            
            # Check if huggingface_hub is available
            if not HF_HUB_AVAILABLE:
                self.download_error.emit("huggingface_hub not available. Please install with: pip install huggingface_hub")
                return
            
            # Set up download directory
            model_dir = Path.home() / "GIT-Projects/KDE AI Interface/quark-integration/models" / self.model_name.split('/')[-1]
            
            # Check if already downloaded
            if model_dir.exists():
                # Check if it contains required files
                has_tokenizer = False
                for tokenizer_file in ["tokenizer.json", "tokenizer.model", "config.json"]:
                    if (model_dir / tokenizer_file).exists():
                        has_tokenizer = True
                        break
                        
                # Look for any model files
                model_files = []
                for ext in ["*.onnx", "*.gguf", "*.bin"]:
                    model_files.extend(list(model_dir.glob(ext)))
                
                if has_tokenizer and model_files:
                    logger.info(f"Model already downloaded to {model_dir}")
                    self.download_finished.emit(str(model_dir))
                    return
                else:
                    logger.info(f"Model directory exists but missing files, re-downloading")
            
            # Download - be more permissive with file types
            from huggingface_hub import snapshot_download
            
            # We'll try two approaches
            try:
                # First attempt: standard download with larger ignore list
                logger.info(f"Downloading {self.model_name} to {model_dir}")
                model_path = snapshot_download(
                    repo_id=self.model_name,
                    local_dir=str(model_dir),
                    ignore_patterns=[
                        "*.pt", "*.safetensors", "*.h5", 
                        "pytorch_model.bin", "tf_model.h5", 
                        "flax_model.msgpack", "model.safetensors"
                    ],
                )
                
                # Check if we got what we needed
                model_files = []
                for ext in ["*.onnx", "*.gguf", "*.bin"]:
                    model_files.extend(list(Path(model_path).glob(ext)))
                    
                has_tokenizer = False
                for tokenizer_file in ["tokenizer.json", "tokenizer.model", "config.json"]:
                    if (Path(model_path) / tokenizer_file).exists():
                        has_tokenizer = True
                        break
                        
                if not (has_tokenizer and model_files):
                    raise Exception("Downloaded model is missing required files")
                    
                self.download_finished.emit(model_path)
                
            except Exception as first_error:
                # Second attempt: Try with git-lfs
                logger.warning(f"Standard download failed: {str(first_error)}. Trying alternate approach...")
                import subprocess
                import os
                
                try:
                    # Check if git-lfs is available
                    subprocess.run(["git", "lfs", "version"], check=True, capture_output=True)
                    
                    # Use git clone instead
                    if model_dir.exists():
                        import shutil
                        shutil.rmtree(model_dir)
                        
                    os.makedirs(model_dir, exist_ok=True)
                    repo_url = f"https://huggingface.co/{self.model_name}"
                    
                    subprocess.run(["git", "lfs", "install"], check=True, cwd=str(model_dir))
                    subprocess.run(["git", "clone", repo_url, str(model_dir)], check=True)
                    
                    self.download_finished.emit(str(model_dir))
                except Exception as e:
                    # If both approaches fail, report the error
                    logger.error(f"Both download approaches failed: {str(first_error)}, then {str(e)}")
                    self.download_error.emit(f"Download error: {str(e)}")
            
        except Exception as e:
            logger.error(f"Error downloading model: {str(e)}")
            self.download_error.emit(f"Download error: {str(e)}")

class QuarkDeepSeekInterface(QMainWindow):
    """Main window for the Quark DeepSeek Interface"""
    def __init__(self):
        super().__init__()
        
        # Set base directory and models directory
        self.base_dir = Path.home() / "GIT-Projects/KDE AI Interface/quark-integration"
        self.models_dir = self.base_dir / "models"
        self.models_dir.mkdir(parents=True, exist_ok=True)
        
        # Conversation management
        self.conversations = []
        self.current_conversation_index = -1
        self.conversation_dir = self.base_dir / "conversations"
        self.conversation_dir.mkdir(parents=True, exist_ok=True)
        
        # Feature toggles
        self.screen_capture_enabled = False
        self.audio_capture_enabled = False
        self.rag_enabled = False
        
        # Set default model
        self.model_path = None
        self.available_models = []
        self.scan_local_models()
        
        # Model config
        self.model_config = {
            "temperature": 0.7,
            "top_p": 0.9,
            "max_tokens": 512
        }
        
        # Initialize UI
        self.init_ui()
        
        # Check for Quark status after UI is initialized
        self.check_quark_status()
        
        # Create a new conversation on startup
        self.new_conversation()
        
    def eventFilter(self, obj, event):
        """Event filter to catch Enter key press"""
        from PyQt5.QtCore import QEvent
        from PyQt5.QtGui import QKeyEvent
        
        if obj is self.prompt_input and event.type() == QEvent.KeyPress:
            key_event = QKeyEvent(event)
            # Check if Enter key is pressed without Shift
            if key_event.key() == Qt.Key_Return and not key_event.modifiers() & Qt.ShiftModifier:
                self.send_message()
                return True
        return super().eventFilter(obj, event)
    
    def scan_local_models(self):
        """Scan for locally available models"""
        local_models = []
        
        # Check models directory
        if self.models_dir.exists():
            for model_dir in self.models_dir.iterdir():
                if model_dir.is_dir():
                    # Check for tokenizer files (any of the possible names)
                    has_tokenizer = False
                    for tokenizer_name in ["tokenizer.json", "tokenizer.model", "config.json"]:
                        if (model_dir / tokenizer_name).exists():
                            has_tokenizer = True
                            break
                    
                    # Check for model files (any possible extension)
                    has_model_file = False
                    for pattern in ["*.onnx", "*.gguf", "*.bin", "*.safetensors", "model.safetensors", "pytorch_model.bin"]:
                        if list(model_dir.glob(pattern)):
                            has_model_file = True
                            break
                    
                    if has_tokenizer and has_model_file:
                        local_models.append(str(model_dir))
                        logger.info(f"Found valid model at {model_dir}")
        
        self.available_models = local_models
        
        # If we have at least one model, set it as the current model
        if local_models:
            self.model_path = local_models[0]
            logger.info(f"Found {len(local_models)} local models. Using {self.model_path}")
        else:
            logger.info("No local models found")
    
    def check_quark_status(self):
        """Check if Quark is available and update UI accordingly"""
        if QUARK_AVAILABLE:
            # Get available backends
            try:
                backends = quark.get_available_backends()
                backend_text = ", ".join(backends) if backends else "None"
                
                # Update status indicator
                if backends:
                    self.quark_status_label.setText(f"Quark: Available (Backends: {backend_text})")
                    self.quark_status_label.setStyleSheet("color: green;")
                else:
                    self.quark_status_label.setText(f"Quark: Available (No backends)")
                    self.quark_status_label.setStyleSheet("color: orange;")
                
                # Enable UI elements
                self.download_model_combo.setEnabled(True)
                self.download_button.setEnabled(True)
                
            except Exception as e:
                self.quark_status_label.setText(f"Quark Error: {str(e)}")
                self.quark_status_label.setStyleSheet("color: red;")
        else:
            self.quark_status_label.setText("Quark: Not Available (Simulation Mode)")
            self.quark_status_label.setStyleSheet("color: red;")
    
    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("KDE AI Interface - Quark with DeepSeek-R1")
        self.setGeometry(100, 100, 1200, 800)
        self.setWindowFlags(Qt.Window)  # Removed WindowStaysOnTopHint for better usability
        
        # Create main splitter to divide sidebar and chat area
        self.main_splitter = QSplitter(Qt.Horizontal)
        self.setCentralWidget(self.main_splitter)
        
        # Create sidebar for conversations
        self.sidebar = QWidget()
        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(10, 10, 10, 10)
        
        # Conversation header
        conv_header = QLabel("Conversations")
        conv_header.setStyleSheet("font-size: 16px; font-weight: bold;")
        sidebar_layout.addWidget(conv_header)
        
        # New conversation button
        new_conv_btn = QPushButton("New Conversation")
        new_conv_btn.clicked.connect(self.new_conversation)
        new_conv_btn.setStyleSheet("background-color: #4a7eff; color: white;")
        sidebar_layout.addWidget(new_conv_btn)
        
        # Conversation list
        self.conversation_list = QListWidget()
        self.conversation_list.itemClicked.connect(self.on_conversation_selected)
        sidebar_layout.addWidget(self.conversation_list)
        
        # Add sidebar to splitter
        self.main_splitter.addWidget(self.sidebar)
        
        # Create main chat area
        self.chat_area = QWidget()
        chat_layout = QVBoxLayout(self.chat_area)
        chat_layout.setContentsMargins(10, 10, 10, 10)
        
        # Header layout with title and control buttons
        header_layout = QHBoxLayout()
        
        # Add header label
        header = QLabel("KDE AI Interface - AMD Quark with DeepSeek-R1")
        header.setStyleSheet("font-size: 18px; font-weight: bold;")
        header_layout.addWidget(header)
        
        # Spacer to push buttons to right
        header_layout.addStretch()
        
        # Feature toggle buttons
        self.screen_capture_btn = self.create_toggle_button("Screen", "camera-video", self.toggle_screen_capture)
        header_layout.addWidget(self.screen_capture_btn)
        
        self.audio_capture_btn = self.create_toggle_button("Audio", "audio-input-microphone", self.toggle_audio_capture)
        header_layout.addWidget(self.audio_capture_btn)
        
        self.rag_btn = self.create_toggle_button("RAG", "view-refresh", self.toggle_rag)
        self.rag_btn.setToolTip("Toggle Retrieval-Augmented Generation")
        header_layout.addWidget(self.rag_btn)
        
        chat_layout.addLayout(header_layout)
        
        # Status and model info area
        info_frame = QFrame()
        info_frame.setFrameShape(QFrame.StyledPanel)
        info_frame.setStyleSheet("background-color: rgba(120, 120, 120, 0.1);")
        info_layout = QGridLayout(info_frame)
        
        # Quark status
        self.quark_status_label = QLabel("Checking Quark status...")
        info_layout.addWidget(QLabel("Status:"), 0, 0)
        info_layout.addWidget(self.quark_status_label, 0, 1)
        
        # Model selection
        info_layout.addWidget(QLabel("Current Model:"), 1, 0)
        self.model_combo = QComboBox()
        if self.available_models:
            for model in self.available_models:
                self.model_combo.addItem(Path(model).name, model)
        else:
            self.model_combo.addItem("No models available")
        self.model_combo.currentIndexChanged.connect(self.on_model_changed)
        info_layout.addWidget(self.model_combo, 1, 1)
        
        # Download model
        info_layout.addWidget(QLabel("Download Model:"), 2, 0)
        download_layout = QHBoxLayout()
        
        self.download_model_combo = QComboBox()
        for model in DEFAULT_MODELS:
            self.download_model_combo.addItem(model.split('/')[-1], model)
            
        # Pre-select the recommended model
        self.download_model_combo.setCurrentIndex(0)
            
        self.download_button = QPushButton("Download Model")
        self.download_button.clicked.connect(self.download_selected_model)
        self.download_button.setStyleSheet("background-color: #4a7eff; color: white;")
        
        download_layout.addWidget(self.download_model_combo)
        download_layout.addWidget(self.download_button)
        info_layout.addLayout(download_layout, 2, 1)
        
        # Performance meter
        info_layout.addWidget(QLabel("Performance:"), 3, 0)
        self.performance_label = QLabel("No data yet")
        info_layout.addWidget(self.performance_label, 3, 1)
        
        chat_layout.addWidget(info_frame)
        
        # Model configuration area
        config_row = QHBoxLayout()
        
        # Model configuration group
        config_group = QGroupBox("Model Configuration")
        config_layout = QGridLayout(config_group)
        
        # Temperature
        config_layout.addWidget(QLabel("Temperature:"), 0, 0)
        self.temperature_spinner = QSpinBox()
        self.temperature_spinner.setRange(0, 20)  # 0.0 to 2.0
        self.temperature_spinner.setValue(int(self.model_config["temperature"] * 10))
        self.temperature_spinner.setSingleStep(1)
        self.temperature_spinner.valueChanged.connect(self.on_temperature_changed)
        config_layout.addWidget(self.temperature_spinner, 0, 1)
        config_layout.addWidget(QLabel("÷ 10 (e.g., 7 = 0.7)"), 0, 2)
        
        # Top-p
        config_layout.addWidget(QLabel("Top-p:"), 1, 0)
        self.top_p_spinner = QSpinBox()
        self.top_p_spinner.setRange(0, 10)  # 0.0 to 1.0
        self.top_p_spinner.setValue(int(self.model_config["top_p"] * 10))
        self.top_p_spinner.setSingleStep(1)
        self.top_p_spinner.valueChanged.connect(self.on_top_p_changed)
        config_layout.addWidget(self.top_p_spinner, 1, 1)
        config_layout.addWidget(QLabel("÷ 10 (e.g., 9 = 0.9)"), 1, 2)
        
        # Max tokens
        config_layout.addWidget(QLabel("Max Tokens:"), 2, 0)
        self.max_tokens_spinner = QSpinBox()
        self.max_tokens_spinner.setRange(10, 2048)
        self.max_tokens_spinner.setValue(self.model_config["max_tokens"])
        self.max_tokens_spinner.setSingleStep(32)
        self.max_tokens_spinner.valueChanged.connect(self.on_max_tokens_changed)
        config_layout.addWidget(self.max_tokens_spinner, 2, 1)
        
        config_row.addWidget(config_group)
        
        # Context group
        context_group = QGroupBox("Context Controls")
        context_layout = QGridLayout(context_group)
        
        # Current context controls
        context_layout.addWidget(QLabel("Current Context:"), 0, 0)
        self.context_status = QLabel("Not capturing")
        context_layout.addWidget(self.context_status, 0, 1)
        
        # Memory controls
        context_layout.addWidget(QLabel("Memory:"), 1, 0)
        self.memory_status = QLabel("RAG disabled")
        context_layout.addWidget(self.memory_status, 1, 1)
        
        # Current context details
        context_layout.addWidget(QLabel("Sources:"), 2, 0)
        self.context_sources = QLabel("None")
        context_layout.addWidget(self.context_sources, 2, 1)
        
        config_row.addWidget(context_group)
        
        chat_layout.addLayout(config_row)
        
        # Add chat display
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.setFont(QFont("Monospace", 10))
        self.chat_display.setStyleSheet("""
            QTextEdit {
                background-color: #f8f8f8;
                border: 1px solid #ddd;
                border-radius: 5px;
            }
        """)
        chat_layout.addWidget(self.chat_display)
        
        # Add input area
        input_layout = QHBoxLayout()
        
        self.prompt_input = QTextEdit()
        self.prompt_input.setPlaceholderText("Type your message here...")
        self.prompt_input.setMaximumHeight(100)
        # Connect Enter key to send message
        self.prompt_input.installEventFilter(self)
        self.prompt_input.setStyleSheet("""
            QTextEdit {
                border: 1px solid #ddd;
                border-radius: 5px;
                padding: 5px;
            }
        """)
        input_layout.addWidget(self.prompt_input)
        
        send_button = QPushButton("Send")
        send_button.clicked.connect(self.send_message)
        send_button.setStyleSheet("""
            QPushButton {
                background-color: #4a7eff;
                color: white;
                border-radius: 5px;
                padding: 5px 15px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #3a6eef;
            }
        """)
        input_layout.addWidget(send_button)
        
        chat_layout.addLayout(input_layout)
        
        # Add chat area to splitter
        self.main_splitter.addWidget(self.chat_area)
        
        # Set initial splitter sizes
        self.main_splitter.setSizes([250, 950])
        
        # Add status bar
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage("Ready")
        
        # Add system tray icon
        self.setup_tray()
        
        # Add welcome message on first run
        # This will be handled by new_conversation method
    
    def setup_tray(self):
        """Set up the system tray icon"""
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(QIcon.fromTheme("assistant", QIcon.fromTheme("dialog-information")))
        
        # Create tray menu
        tray_menu = QMenu()
        
        show_action = QAction("Show/Hide", self)
        show_action.triggered.connect(self.toggle_window)
        tray_menu.addAction(show_action)
        
        quit_action = QAction("Exit", self)
        quit_action.triggered.connect(QApplication.quit)
        tray_menu.addAction(quit_action)
        
        # Set tray icon and menu
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self.on_tray_activated)
        self.tray_icon.show()
    
    def on_tray_activated(self, reason):
        """Handle tray icon activation"""
        if reason == QSystemTrayIcon.Trigger:
            self.toggle_window()
    
    def toggle_window(self):
        """Toggle window visibility"""
        if self.isVisible():
            self.hide()
        else:
            self.show()
            self.raise_()
            self.activateWindow()
    
    def on_model_changed(self, index):
        """Handle model selection change"""
        if index >= 0:
            self.model_path = self.model_combo.itemData(index)
            logger.info(f"Selected model: {self.model_path}")
    
    def on_temperature_changed(self, value):
        """Handle temperature value change"""
        self.model_config["temperature"] = value / 10.0
        logger.info(f"Temperature set to {self.model_config['temperature']}")
    
    def on_top_p_changed(self, value):
        """Handle top-p value change"""
        self.model_config["top_p"] = value / 10.0
        logger.info(f"Top-p set to {self.model_config['top_p']}")
    
    def on_max_tokens_changed(self, value):
        """Handle max tokens value change"""
        self.model_config["max_tokens"] = value
        logger.info(f"Max tokens set to {self.model_config['max_tokens']}")
    
    def download_selected_model(self):
        """Download the selected model"""
        model_name = self.download_model_combo.currentData()
        if not model_name:
            return
        
        self.statusBar.showMessage(f"Preparing to download {model_name}...")
        logger.info(f"Downloading model: {model_name}")
        
        # Disable download button while downloading
        self.download_button.setEnabled(False)
        self.download_button.setText("Downloading...")
        
        # Check if we need to use the HF Token for login
        from_hf = False
        try:
            import huggingface_hub
            # This will use HF_TOKEN env var if set
            huggingface_hub.whoami()
            from_hf = True
            self.statusBar.showMessage(f"Authenticated with HuggingFace. Downloading {model_name}...")
        except:
            self.statusBar.showMessage(f"Not authenticated with HuggingFace. Attempting anonymous download...")
        
        # Start download thread
        self.download_thread = ModelDownloadThread(model_name)
        self.download_thread.download_started.connect(lambda msg: self.statusBar.showMessage(msg))
        self.download_thread.download_finished.connect(self.on_model_download_finished)
        self.download_thread.download_error.connect(self.on_model_download_error)
        self.download_thread.start()
    
    def on_model_download_finished(self, model_path):
        """Handle model download completion"""
        self.statusBar.showMessage(f"Model downloaded to {model_path}", 5000)
        
        # Re-enable download button
        self.download_button.setEnabled(True)
        self.download_button.setText("Download")
        
        # Refresh model list
        self.scan_local_models()
        
        # Update model dropdown
        self.model_combo.clear()
        for model in self.available_models:
            self.model_combo.addItem(Path(model).name, model)
    
    def on_model_download_error(self, error_message):
        """Handle model download error"""
        self.statusBar.showMessage(f"Download error: {error_message}", 5000)
        
        # Re-enable download button
        self.download_button.setEnabled(True)
        self.download_button.setText("Download")
    
    def add_user_message(self, message):
        """Add a user message to the chat display"""
        self.chat_display.append(f"<p><b>You:</b><br>{message}</p>")
        self.scroll_to_bottom()
    
    def create_toggle_button(self, text, icon_name, callback):
        """Create a toggle button with text and icon"""
        button = QPushButton(text)
        button.setCheckable(True)
        button.setChecked(False)
        # Try to use theme icon, fallback to text only
        icon = QIcon.fromTheme(icon_name)
        if not icon.isNull():
            button.setIcon(icon)
        button.clicked.connect(callback)
        button.setStyleSheet("""
            QPushButton {
                padding: 5px 10px;
                border-radius: 3px;
                background-color: #eeeeee;
            }
            QPushButton:checked {
                background-color: #4a7eff;
                color: white;
            }
        """)
        return button
        
    def toggle_screen_capture(self, checked):
        """Toggle screen capture feature"""
        self.screen_capture_enabled = checked
        if checked:
            self.context_status.setText("Capturing screen")
            self.context_sources.setText("Screen")
            self.statusBar.showMessage("Screen capture enabled", 3000)
        else:
            # Update status only if audio is also disabled
            if not self.audio_capture_enabled:
                self.context_status.setText("Not capturing")
                self.context_sources.setText("None")
            else:
                self.context_sources.setText("Audio")
            self.statusBar.showMessage("Screen capture disabled", 3000)
    
    def toggle_audio_capture(self, checked):
        """Toggle audio capture feature"""
        self.audio_capture_enabled = checked
        if checked:
            self.context_status.setText("Capturing audio")
            # Update sources text
            if self.screen_capture_enabled:
                self.context_sources.setText("Screen, Audio")
            else:
                self.context_sources.setText("Audio")
            self.statusBar.showMessage("Audio capture enabled", 3000)
        else:
            # Update status only if screen is also disabled
            if not self.screen_capture_enabled:
                self.context_status.setText("Not capturing")
                self.context_sources.setText("None")
            else:
                self.context_sources.setText("Screen")
            self.statusBar.showMessage("Audio capture disabled", 3000)
            
    def toggle_rag(self, checked):
        """Toggle RAG (Retrieval-Augmented Generation) feature"""
        self.rag_enabled = checked
        if checked:
            self.memory_status.setText("RAG enabled")
            self.statusBar.showMessage("Retrieval-Augmented Generation enabled", 3000)
        else:
            self.memory_status.setText("RAG disabled")
            self.statusBar.showMessage("Retrieval-Augmented Generation disabled", 3000)
            
    def new_conversation(self):
        """Create a new conversation"""
        # Generate a unique ID for the conversation
        import time
        conv_id = f"conversation_{int(time.time())}"
        
        # Create conversation record
        conversation = {
            "id": conv_id,
            "name": f"Conversation {len(self.conversations) + 1}",
            "messages": [],
            "created_at": time.time()
        }
        
        # Add to conversations list
        self.conversations.append(conversation)
        
        # Update conversation list widget
        self.update_conversation_list()
        
        # Select the new conversation
        self.current_conversation_index = len(self.conversations) - 1
        self.conversation_list.setCurrentRow(self.current_conversation_index)
        
        # Clear chat display
        self.chat_display.clear()
        
        # Add welcome message
        welcome_msg = """
        Welcome to the KDE AI Interface powered by AMD Quark with DeepSeek! 
        
        This interface uses AMD's Quark runtime to accelerate AI inference on Ryzen AI processors.
        For your AMD Ryzen 9 8945HS with XDNA NPU, the recommended models are:
        
        - deepseek-ai/deepseek-coder-6.7b-instruct (for coding tasks)
        - TheBloke/deepseek-coder-6.7B-instruct-GGUF (alternative format)
        
        New features available:
        - Screen capture button: Record your screen for context
        - Audio capture button: Record audio for transcription
        - RAG button: Toggle Retrieval-Augmented Generation
        - Conversation sidebar: Manage multiple chat sessions
        
        Type your message and press Enter or click Send to begin!
        """
        self.add_assistant_message(welcome_msg)
        
        # Add welcome message to conversation history
        self.conversations[self.current_conversation_index]["messages"].append({
            "role": "assistant",
            "content": welcome_msg
        })
        
    def update_conversation_list(self):
        """Update the conversation list widget"""
        self.conversation_list.clear()
        for conv in self.conversations:
            item = QListWidgetItem(conv["name"])
            item.setData(Qt.UserRole, conv["id"])
            self.conversation_list.addItem(item)
            
    def on_conversation_selected(self, item):
        """Handle selection of a conversation from the list"""
        conv_id = item.data(Qt.UserRole)
        
        # Find the selected conversation
        for i, conv in enumerate(self.conversations):
            if conv["id"] == conv_id:
                self.current_conversation_index = i
                break
                
        # Load the conversation
        self.load_conversation(self.current_conversation_index)
        
    def load_conversation(self, index):
        """Load a conversation into the chat display"""
        if index < 0 or index >= len(self.conversations):
            return
            
        # Clear chat display
        self.chat_display.clear()
        
        # Add messages from conversation
        conversation = self.conversations[index]
        for message in conversation["messages"]:
            if message["role"] == "user":
                self.add_user_message(message["content"])
            else:
                self.add_assistant_message(message["content"])
                
    def save_conversations(self):
        """Save conversations to disk"""
        import json
        
        # Ensure conversations directory exists
        if not self.conversation_dir.exists():
            self.conversation_dir.mkdir(parents=True, exist_ok=True)
            
        # Save each conversation to a separate file
        for conv in self.conversations:
            file_path = self.conversation_dir / f"{conv['id']}.json"
            with open(file_path, 'w') as f:
                json.dump(conv, f)
                
    def load_conversations(self):
        """Load conversations from disk"""
        import json
        
        # Ensure conversations directory exists
        if not self.conversation_dir.exists():
            return
            
        # Load conversations from files
        self.conversations = []
        for file_path in self.conversation_dir.glob("*.json"):
            try:
                with open(file_path, 'r') as f:
                    conv = json.load(f)
                    self.conversations.append(conv)
            except Exception as e:
                logger.error(f"Error loading conversation {file_path}: {str(e)}")
                
        # Sort conversations by creation time
        self.conversations.sort(key=lambda x: x.get("created_at", 0))
        
        # Update conversation list
        self.update_conversation_list()
        
        # Select most recent conversation if available
        if self.conversations:
            self.current_conversation_index = len(self.conversations) - 1
            self.conversation_list.setCurrentRow(self.current_conversation_index)
            self.load_conversation(self.current_conversation_index)
        else:
            # Create a new conversation if none exist
            self.new_conversation()

    def add_user_message(self, message):
        """Add a user message to the chat display"""
        self.chat_display.append(f"<p><b>You:</b><br>{message}</p>")
        
        # Add to conversation history if a conversation is active
        if self.current_conversation_index >= 0:
            self.conversations[self.current_conversation_index]["messages"].append({
                "role": "user",
                "content": message
            })
            
        self.scroll_to_bottom()
    
    def add_assistant_message(self, message):
        """Add an assistant message to the chat display"""
        self.chat_display.append(f"<p><b>Assistant:</b><br>{message}</p>")
        
        # Add to conversation history if a conversation is active
        if self.current_conversation_index >= 0:
            self.conversations[self.current_conversation_index]["messages"].append({
                "role": "assistant",
                "content": message
            })
            
        self.scroll_to_bottom()
    
    def scroll_to_bottom(self):
        """Scroll the chat display to the bottom"""
        cursor = self.chat_display.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.chat_display.setTextCursor(cursor)
    
    def send_message(self):
        """Send a message to the assistant"""
        # Get the message
        prompt = self.prompt_input.toPlainText().strip()
        if not prompt:
            return
        
        # Clear the input field
        self.prompt_input.clear()
        
        # Add the user message to the chat
        self.add_user_message(prompt)
        
        # Check if we have a model
        if not self.model_path:
            self.statusBar.showMessage("No model available. Please download a model first.")
            self.add_assistant_message("Error: No model available. Please download a model first.")
            return
        
        # Create assistant response placeholder
        self.chat_display.append("<p><b>Assistant:</b><br></p>")
        self.current_response = ""
        
        # Update config with max tokens
        config = self.model_config.copy()
        
        # Add context information if capturing is enabled
        enhanced_prompt = prompt
        context_info = []
        
        if self.screen_capture_enabled:
            # Placeholder for actual screen capture implementation
            screen_context = "[Screen capture enabled - would include screenshot description here]"
            context_info.append(f"Screen Context: {screen_context}")
            self.statusBar.showMessage("Including screen context in prompt", 2000)
            
        if self.audio_capture_enabled:
            # Placeholder for actual audio capture implementation
            audio_context = "[Audio capture enabled - would include transcription here]"
            context_info.append(f"Audio Context: {audio_context}")
            self.statusBar.showMessage("Including audio context in prompt", 2000)
            
        # Add RAG context if enabled
        if self.rag_enabled:
            # Placeholder for actual RAG implementation
            if self.current_conversation_index >= 0 and self.conversations:
                # Get previous conversations for context
                conversation = self.conversations[self.current_conversation_index]
                if len(conversation["messages"]) > 2:  # If there's a conversation history
                    rag_context = "[RAG enabled - would include relevant memory from previous conversations]"
                    context_info.append(f"Memory Context: {rag_context}")
                    self.statusBar.showMessage("Including memory context in prompt", 2000)
        
        # If we have context info, add it to the prompt
        if context_info:
            context_block = "\n\n--- Context Information ---\n" + "\n".join(context_info) + "\n---\n\n"
            enhanced_prompt = context_block + "User Query: " + prompt
            
            # Log the enhanced prompt
            logger.info(f"Enhanced prompt with context: {enhanced_prompt[:100]}...")
        
        # Start generation thread
        self.generate_thread = GenerateThread(self.model_path, enhanced_prompt, config)
        self.generate_thread.response_started.connect(self.on_response_started)
        self.generate_thread.response_chunk.connect(self.on_response_chunk)
        self.generate_thread.response_finished.connect(self.on_response_finished)
        self.generate_thread.error_occurred.connect(self.on_error)
        self.generate_thread.start()
    
    def on_response_started(self):
        """Handle response generation started"""
        self.statusBar.showMessage("Generating response...")
    
    def on_response_chunk(self, chunk):
        """Handle response chunk received"""
        self.current_response += chunk
        
        # Update the last paragraph (remove and replace)
        cursor = self.chat_display.textCursor()
        cursor.movePosition(QTextCursor.End)
        cursor.movePosition(QTextCursor.StartOfBlock, QTextCursor.KeepAnchor)
        cursor.removeSelectedText()
        cursor.insertHtml(f"<p><b>Assistant:</b><br>{self.current_response}</p>")
        
        self.scroll_to_bottom()
    
    def on_response_finished(self, metrics):
        """Handle response generation completed"""
        duration = metrics.get("duration", 0)
        token_count = metrics.get("token_count", 0)
        tokens_per_second = metrics.get("tokens_per_second", 0)
        backend = metrics.get("backend", "Unknown")
        
        # Update performance label
        self.performance_label.setText(
            f"{token_count} tokens in {duration:.2f}s ({tokens_per_second:.2f} tokens/sec) using {backend}"
        )
        
        self.statusBar.showMessage(f"Response complete: {tokens_per_second:.2f} tokens/sec", 3000)
        
        # Add an empty line after the response
        self.chat_display.append("")
    
    def on_error(self, error_message):
        """Handle error during generation"""
        self.statusBar.showMessage(f"Error: {error_message}")
        self.add_assistant_message(f"Error: {error_message}")

    def closeEvent(self, event):
        """Handle closing the window"""
        # Save conversations before exiting
        self.save_conversations()
        event.accept()

def main():
    """Main function"""
    app = QApplication(sys.argv)
    app.setApplicationName("Quark DeepSeek Interface")
    
    # Set up dark style
    try:
        import qdarkstyle
        app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
        print("QDarkStyle applied")
    except ImportError:
        print("QDarkStyle not available, using default style")
    
    # Create and show the main window
    window = QuarkDeepSeekInterface()
    
    # Load saved conversations
    window.load_conversations()
    
    window.show()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()