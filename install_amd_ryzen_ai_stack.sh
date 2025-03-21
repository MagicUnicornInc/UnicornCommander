#!/bin/bash
# install_amd_ryzen_ai_stack.sh
# This script installs the AMD Ryzen AI Software stack components, starting with ROCm.
# It will update your system, add the ROCm repository, and install rocm-dkms.
#
# NOTE: This needs to be run with sudo privileges.

set -e

echo "Starting system update..."
sudo apt update && sudo apt upgrade -y

echo "Adding ROCm repository key..."
wget -qO - http://repo.radeon.com/rocm/rocm.gpg.key | sudo apt-key add -

echo "Adding ROCm repository..."
# WARNING: This repository is for Ubuntu Xenial. Modify your sources.list according
# to your OS version. Check https://rocmdocs.amd.com/en/latest/Installation_Guide/Installation-Guide.html
echo 'deb [arch=amd64] http://repo.radeon.com/rocm/apt/debian/ jammy main' | sudo tee /etc/apt/sources.list.d/rocm.list

echo "Updating package lists..."
sudo apt update

echo "Installing ROCm components..."
sudo apt install -y rocm-dkms

echo "ROCm installation complete!"

cat << 'EOF2'

Next Steps:
1. To install developer tools like the AMD Radeon GPU Profiler (RGP) and ROCProfiler, please consult AMD's documentation:
   https://rocmdocs.amd.com/en/latest/index.html

2. To install the Vitis AI toolchain, follow the instructions at:
   https://www.xilinx.com/products/design-tools/vitis-ai.html

3. Install optimized math libraries like ZenDNN from AMD's site or your Linux distro's package manager.

4. Please ensure your BIOS/UEFI firmware is updated, and check for any AMD recommended patches for kernel or Mesa drivers.

Happy AI inference on AMD Ryzen!
EOF2

