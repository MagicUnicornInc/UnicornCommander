#!/bin/bash
# Launch script for optimized DeepSeek models on AMD Ryzen AI

# Activate environment
source quark_env/bin/activate
source quark_env.sh 2>/dev/null || echo "Environment file not found, using defaults"

# Check Quark availability
echo "Checking Quark availability..."
HAS_QUARK=0
python -c "import quark; print(f'Quark version: {quark.__version__}'); print(f'Available backends: {quark.get_available_backends()}')" && HAS_QUARK=1 || echo "❌ Quark not available - continuing with CPU fallback"

# Check for PyQt5
echo "Checking UI dependencies..."
python -c "import PyQt5; print('PyQt5 available')" || pip install PyQt5 QtPy qdarkstyle

# Launch the appropriate GUI
if [ $HAS_QUARK -eq 1 ]; then
    echo "Launching DeepSeek GUI with Quark acceleration..."
    python quark_deepseek_gui.py
else
    echo "Launching DeepSeek GUI in fallback mode..."
    # Run the fallback GUI version that doesn't require Quark
    if [ -f "run_without_quark.sh" ]; then
        bash ./run_without_quark.sh
    else
        echo "Creating fallback CPU-only interface..."
        # Check which GUI file exists
        if [ -f "test_quark_deepseek.py" ]; then
            python test_quark_deepseek.py --cpu-only
        else
            # Create a minimal fallback GUI
            cat > fallback_deepseek_gui.py << 'EOF'
#!/usr/bin/env python3
import sys
import os
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QTextEdit, QLineEdit, QPushButton, QLabel
from PyQt5.QtCore import Qt
import qdarkstyle
from transformers import AutoModelForCausalLM, AutoTokenizer

class FallbackDeepSeekGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DeepSeek Fallback Interface (CPU Mode)")
        self.resize(900, 700)
        
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Status label
        self.status_label = QLabel("Loading model in CPU-only mode (this may take a while)...")
        layout.addWidget(self.status_label)
        
        # Chat history display
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        layout.addWidget(self.chat_display)
        
        # Input area
        self.input_field = QTextEdit()
        self.input_field.setMaximumHeight(100)
        layout.addWidget(self.input_field)
        
        # Send button
        self.send_button = QPushButton("Send")
        self.send_button.clicked.connect(self.send_message)
        layout.addWidget(self.send_button)
        
        # Load model
        self.load_model()
        
    def load_model(self):
        try:
            # Check for available model
            models_dir = "models"
            if os.path.exists(os.path.join(models_dir, "deepseek-coder-1.3b-instruct")):
                model_path = os.path.join(models_dir, "deepseek-coder-1.3b-instruct")
                self.status_label.setText("Loading DeepSeek 1.3B model (smaller, faster)...")
            elif os.path.exists(os.path.join(models_dir, "deepseek-coder-6.7b-instruct")):
                model_path = os.path.join(models_dir, "deepseek-coder-6.7b-instruct")
                self.status_label.setText("Loading DeepSeek 6.7B model (larger, may be slow on CPU)...")
            else:
                self.status_label.setText("❌ No models found in 'models' directory!")
                return
                
            # Load tokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(model_path)
            
            # Load model in CPU mode
            self.model = AutoModelForCausalLM.from_pretrained(
                model_path,
                device_map="cpu",
                low_cpu_mem_usage=True,
            )
            self.status_label.setText(f"✅ Model loaded: {os.path.basename(model_path)} (CPU-only mode)")
        except Exception as e:
            self.status_label.setText(f"❌ Error loading model: {str(e)}")
    
    def send_message(self):
        user_message = self.input_field.toPlainText().strip()
        if not user_message:
            return
            
        # Clear input field
        self.input_field.clear()
        
        # Update chat display with user message
        self.chat_display.append(f"<b>You:</b> {user_message}")
        
        try:
            # Generate response
            self.status_label.setText("Generating response... (may take a while in CPU-only mode)")
            QApplication.processEvents()  # Update the UI
            
            # Prepare prompt
            prompt = f"<|im_start|>user\n{user_message}<|im_end|>\n<|im_start|>assistant\n"
            
            # Tokenize
            inputs = self.tokenizer(prompt, return_tensors="pt")
            
            # Generate
            outputs = self.model.generate(
                inputs["input_ids"],
                max_new_tokens=512,
                temperature=0.7,
                do_sample=True,
            )
            
            # Decode
            response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # Extract assistant's response
            try:
                response = response.split("<|im_start|>assistant\n")[-1].split("<|im_end|>")[0]
            except:
                pass  # Use the full response if the splitting fails
                
            # Update chat display with AI response
            self.chat_display.append(f"<b>Assistant:</b> {response}")
            self.status_label.setText("Ready")
        except Exception as e:
            self.chat_display.append(f"<b>System:</b> Error generating response: {str(e)}")
            self.status_label.setText("Error occurred")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
    window = FallbackDeepSeekGUI()
    window.show()
    sys.exit(app.exec_())
EOF
            python fallback_deepseek_gui.py
        fi
    fi
fi
