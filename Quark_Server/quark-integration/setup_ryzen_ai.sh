#!/bin/bash
# Setup script for AMD Ryzen AI NPU with DeepSeek models
# This script installs dependencies, configures the environment, and downloads models

set -e
echo "===== AMD Ryzen AI NPU Setup Script ====="
echo "This script will set up your Ryzen 9 8945HS environment for optimal LLM inference"

# Create the base directory
BASEDIR="$(pwd)"
echo "Working in $BASEDIR"

# Check if XDNA driver is loaded
if lsmod | grep -q amdxdna; then
    echo "✅ XDNA driver is loaded"
else
    echo "⚠️ XDNA driver is not loaded, attempting to load it"
    sudo modprobe amdxdna
    if lsmod | grep -q amdxdna; then
        echo "✅ XDNA driver loaded successfully"
    else
        echo "❌ Failed to load XDNA driver - hardware acceleration may not be available"
    fi
fi

# Check for device files
if [ -e /dev/amdxdna0 ]; then
    echo "✅ XDNA device found at /dev/amdxdna0"
else
    echo "❌ XDNA device file not found - hardware acceleration may not be available"
    echo "Creating XDNA device file..."
    # The major number 235 is typical for XDNA devices
    sudo mknod -m 666 /dev/amdxdna0 c 235 0
    if [ -e /dev/amdxdna0 ]; then
        echo "✅ XDNA device file created successfully"
    else
        echo "❌ Failed to create XDNA device file"
    fi
fi

# Create Python virtual environment
echo "Creating Python virtual environment..."
python3 -m venv quark_env --clear
source quark_env/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install --upgrade pip
pip install PyQt5 QtPy QDarkStyle

# Install core dependencies needed for the GUI
pip install torch onnx onnxruntime huggingface_hub transformers

# Install AMD Quark manually since the wheel file has version constraints
echo "AMD Quark requires Python < 3.12. Using a fallback approach..."
pip install ninja numpy protobuf pandas rich scipy tqdm

# Install important UI dependencies
echo "Installing UI dependencies..."
pip install qdarkstyle coloredlogs

# Create models directory
MODELS_DIR="models"
mkdir -p "$MODELS_DIR"

# Download DeepSeek models using HuggingFace
echo "Downloading DeepSeek models (this may take a while)..."
if [ -d "$MODELS_DIR/deepseek-coder-6.7b-instruct" ]; then
    echo "✅ DeepSeek 6.7B model already downloaded"
else
    echo "Downloading deepseek-coder-6.7b-instruct (large model)..."
    python -c "from huggingface_hub import snapshot_download; snapshot_download(repo_id='deepseek-ai/deepseek-coder-6.7b-instruct', local_dir='models/deepseek-coder-6.7b-instruct', ignore_patterns=['*.bin', '*.onnx'])"
fi

if [ -d "$MODELS_DIR/deepseek-coder-1.3b-instruct" ]; then
    echo "✅ DeepSeek 1.3B model already downloaded"
else
    echo "Downloading deepseek-coder-1.3b-instruct (smaller model)..."
    python -c "from huggingface_hub import snapshot_download; snapshot_download(repo_id='deepseek-ai/deepseek-coder-1.3b-instruct', local_dir='models/deepseek-coder-1.3b-instruct')"
fi

# Set up environment variables
echo "Setting up environment variables..."
echo 'export QUARK_BACKENDS="CPU,AMD_XDNA,AMD_ROCm"' > quark_env.sh
echo 'export XRT_PATH="/opt/xilinx/xrt"' >> quark_env.sh
echo 'export XDNA_PATH="/opt/amd-xdna"' >> quark_env.sh
echo 'export LD_LIBRARY_PATH="$XRT_PATH/lib:$XDNA_PATH/lib:$LD_LIBRARY_PATH"' >> quark_env.sh
chmod +x quark_env.sh

# Create the launcher script
echo "Creating launcher script..."
cat > run_optimized_deepseek.sh << 'EOF'
#!/bin/bash
# Launch script for optimized DeepSeek models on AMD Ryzen AI

# Activate environment
source quark_env/bin/activate
source quark_env.sh

# Check Quark availability
echo "Checking Quark availability..."
python -c "import quark; print(f'Quark version: {quark.__version__}'); print(f'Available backends: {quark.get_available_backends()}')" || echo "❌ Quark not available"

# Launch the GUI
echo "Launching DeepSeek GUI..."
python quark_deepseek_gui.py
EOF
chmod +x run_optimized_deepseek.sh

echo "===== Setup Complete ====="
echo "To run the optimized DeepSeek model, use:"
echo "  ./run_optimized_deepseek.sh"
echo ""
echo "If you encounter issues, check:"
echo "1. XDNA driver is loaded (lsmod | grep amdxdna)"
echo "2. Device file exists (/dev/amdxdna0)"
echo "3. Environment variables are set correctly (see quark_env.sh)"
echo ""
echo "For optimal performance:"
echo "- Use the deepseek-coder-6.7b-instruct model for high-quality responses"
echo "- Use the deepseek-coder-1.3b-instruct model for faster responses"