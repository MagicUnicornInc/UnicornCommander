# Manual AMD Ryzen AI Setup Guide

This guide provides detailed manual steps to set up AMD Ryzen AI environment for your Ryzen 9 8945HS with 780M iGPU and XDNA NPU.

## 1. System Requirements

- AMD Ryzen 9 8945HS processor with XDNA NPU
- Linux distribution (Ubuntu 22.04 or newer recommended)
- At least 16GB RAM (32GB recommended for larger models)
- At least 10GB free disk space

## 2. Install System Dependencies

```bash
# Install essential development tools
sudo apt update
sudo apt install -y build-essential cmake git

# Install libraries needed for GUI and ML
sudo apt install -y python3-dev python3-pip python3-venv
sudo apt install -y libopenblas-dev libomp-dev

# Install ROCm for GPU acceleration (if needed)
wget -q -O - https://repo.radeon.com/rocm/rocm.gpg.key | sudo apt-key add -
echo 'deb [arch=amd64] https://repo.radeon.com/rocm/apt/debian/ ubuntu main' | sudo tee /etc/apt/sources.list.d/rocm.list
sudo apt update
sudo apt install -y rocm-libs rocm-dev
```

## 3. Install XDNA Driver

The XDNA driver (`amdxdna`) must be loaded for NPU access:

```bash
# Check if amdxdna module is available
find /lib/modules/$(uname -r) -name "amdxdna.ko"

# Load the module
sudo modprobe amdxdna

# Verify it's loaded
lsmod | grep amdxdna

# Create device node if not present
if [ ! -e /dev/amdxdna0 ]; then
    sudo mknod -m 666 /dev/amdxdna0 c 235 0
fi

# Check device node
ls -la /dev/amdxdna*
```

## 4. Set Up Python Environment

Quark requires Python 3.9-3.11 (not 3.12):

```bash
# Install Python 3.11
sudo apt install -y python3.11 python3.11-venv python3.11-dev

# Create and activate a virtual environment
python3.11 -m venv quark_env_311
source quark_env_311/bin/activate
```

## 5. Install Quark and Dependencies

```bash
# Upgrade pip
pip install --upgrade pip

# Install PyTorch and dependencies
pip install torch==2.2.0 torchvision torchaudio

# Install ONNX dependencies
pip install onnx==1.16.0 onnxruntime==1.17.0 onnxruntime-extensions==0.4.2

# Install model and UI dependencies
pip install transformers==4.36.2 huggingface_hub
pip install PyQt5 QtPy qdarkstyle

# Install Quark (if you have the wheel file)
pip install /path/to/amd_quark-0.8rc3-py3-none-any.whl

# If you don't have the wheel, install common dependencies
pip install ninja numpy protobuf pandas rich scipy tqdm
```

## 6. Set Up Environment Variables

Create an environment file:

```bash
cat > quark_env.sh << 'EOF'
# AMD Quark environment variables
export QUARK_BACKENDS="AMD_XDNA,AMD_ROCm,CPU"
export QUARK_XDNA_OPTIMIZATION=1

# XRT and XDNA paths
export XRT_PATH="/opt/xilinx/xrt"
export XDNA_PATH="/opt/amd-xdna"

# Library paths
export LD_LIBRARY_PATH="$XRT_PATH/lib:$XDNA_PATH/lib:$LD_LIBRARY_PATH"

# CPU optimization (optional)
export OMP_NUM_THREADS=$(nproc)
export MKL_NUM_THREADS=$(nproc)
EOF

chmod +x quark_env.sh
```

## 7. Download Models

Download DeepSeek models using Hugging Face:

```bash
# Create directories
mkdir -p models

# Install git-lfs if needed
sudo apt install -y git-lfs
git lfs install

# Download DeepSeek Coder 1.3B (recommended for your hardware)
git clone https://huggingface.co/deepseek-ai/deepseek-coder-1.3b-instruct models/deepseek-coder-1.3b-instruct

# Download DeepSeek Coder 6.7B (optional, requires more memory)
git clone https://huggingface.co/deepseek-ai/deepseek-coder-6.7b-instruct models/deepseek-coder-6.7b-instruct
```

Alternatively, use the Hugging Face API:

```python
from huggingface_hub import snapshot_download

# Download models
snapshot_download(repo_id='deepseek-ai/deepseek-coder-1.3b-instruct', 
                  local_dir='models/deepseek-coder-1.3b-instruct')
```

## 8. System Optimization

For optimal performance:

```bash
# Set CPU governor to performance mode
sudo cpupower frequency-set -g performance

# Allocate huge pages for better memory performance
sudo bash -c "echo 512 > /proc/sys/vm/nr_hugepages"

# Reduce swappiness for better responsiveness
sudo sysctl vm.swappiness=10

# Set GPU clocks to optimal level (if using ROCm)
sudo rocm-smi --setperflevel high
```

## 9. Model Quantization

If Quark is installed, quantize models for faster inference:

```python
import quark
from quark.onnx import optimize_model

# Load and quantize model
model = optimize_model(
    "models/deepseek-coder-1.3b-instruct/model.onnx",
    quantization="int8",
    optimization_level=1,
    target="xdna"
)
model.save("models/deepseek-coder-1.3b-instruct/model_int8.onnx")
```

## 10. Run the Interface

Create a launch script:

```bash
cat > run_deepseek.sh << 'EOF'
#!/bin/bash
# Launch DeepSeek interface

# Set environment
source quark_env_311/bin/activate
source quark_env.sh

# Check Quark (optional)
python -c "import quark; print(f'Quark version: {quark.__version__}')" 2>/dev/null || echo "Quark not found, using CPU only"

# Launch interface
python path/to/deepseek_gui.py
EOF

chmod +x run_deepseek.sh
```

## Troubleshooting

### Driver Issues

If XDNA driver doesn't load:

```bash
# Check if driver exists
find /lib/modules/$(uname -r) -name "amdxdna.ko"

# Check kernel messages
dmesg | grep -i amdxdna

# Check for errors
sudo modprobe -v amdxdna
```

### Model Loading Issues

If models fail to load:

```bash
# Check model files
find models/ -type f -name "*.bin" | wc -l
find models/ -type f -name "*.safetensors" | wc -l

# Try converting from safetensors to bin (if needed)
python -c "from transformers import AutoModelForCausalLM; model = AutoModelForCausalLM.from_pretrained('models/deepseek-coder-1.3b-instruct', trust_remote_code=True); model.save_pretrained('models/deepseek-coder-1.3b-instruct')"
```

### Performance Optimization

For better performance:

```bash
# Monitor CPU/GPU usage
htop
sudo rocm-smi --showuse

# Set CPU affinity for LLM processes
taskset -c 4-15 python deepseek_gui.py  # Reserve 0-3 for system

# Check memory usage
free -h
```

## Additional Resources

- [AMD Ryzen AI Developer Page](https://www.amd.com/en/developer/tools/ryzen-ai.html)
- [DeepSeek Coder Models](https://huggingface.co/collections/deepseek-ai/deepseek-coder-models-67422868754a53f603d81c79)
- [HuggingFace Transformers Documentation](https://huggingface.co/docs/transformers/index)
- [PyTorch Documentation](https://pytorch.org/docs/stable/index.html)