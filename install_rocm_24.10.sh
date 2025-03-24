#!/bin/bash
# install_rocm_24.10.sh
# This script is tailored for Ubuntu 24.10 (noble) to install available ROCm components.
# It will update your system, add the ROCm repository, and install rocm-smi, rocminfo, rocm-cmake, and amdxdna-dkms.
#
# NOTE: This script requires sudo privileges.

set -e

echo "Starting system update..."
sudo apt update && sudo apt upgrade -y

echo "Adding ROCm repository key..."
wget -qO - http://repo.radeon.com/rocm/rocm.gpg.key | sudo apt-key add -

echo "Adding ROCm repository for noble..."
echo 'deb [arch=amd64] http://repo.radeon.com/rocm/apt/debian/ noble main' | sudo tee /etc/apt/sources.list.d/rocm.list

echo "Updating package lists..."
sudo apt update

echo "Installing available ROCm components..."
sudo apt install -y rocm-smi rocminfo rocm-cmake 

echo "Installing XDNA driver for AMD Ryzen AI..."
sudo apt install -y amdxdna-dkms
sudo modprobe amdxdna

echo "Installing XRT (Xilinx Runtime)..."
sudo apt install -y xrt
echo 'export XILINX_XRT=/opt/xilinx/xrt' | sudo tee -a /etc/environment

echo "ROCm components installation for Ubuntu 24.10 complete!"
echo "Checking for XDNA device..."
ls -la /dev/amdxdna* || echo "No XDNA device found. Please check your hardware or kernel configuration."

echo "Running rocminfo..."
rocminfo || echo "rocminfo command failed. ROCm installation may be incomplete."

cat << 'EOF2'

Next Steps:
1. Verify ROCm and XDNA installation:
   - Run "rocminfo" to check hardware info
   - Run "rocm-smi" to view system management info
   - Check for XDNA device: "ls -la /dev/amdxdna*"

2. Download and install AMD Ryzen AI Software Stack from AMD's official site:
   https://www.amd.com/en/developer/tools/ryzen-ai.html

3. Install Python dependencies for ONNX Runtime and AI acceleration:
   pip install onnxruntime numpy

4. Verify Vitis AI Execution Provider:
   python -c "import onnxruntime as ort; print(ort.get_available_providers())"
   # This should show 'VitisAIExecutionProvider' if properly installed

5. For optimal performance with KDE Plasma 6 on Wayland, consider using:
   - KDE System Settings > Display and Monitor > Compositor > Latency
   - Set to "Force smoothest animations" for better window management

6. To install additional developer tools:
   sudo apt install -y rocm-developer
   
Happy AI inference on AMD Ryzen with Ubuntu 24.10 and KDE Plasma 6!
EOF2

