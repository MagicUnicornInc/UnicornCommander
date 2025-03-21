#!/bin/bash
# install_rocm_24.04.sh
# This script is tailored for Ubuntu 24.04 (noble) to install available ROCm components.
# It will update your system, add the ROCm repository, and install rocm-smi, rocminfo, and rocm-cmake.
#
# NOTE: This script requires sudo privileges.

set -e

echo "Starting system update..."
sudo apt update && sudo apt upgrade -y

echo "Adding ROCm repository key..."
wget -qO - http://repo.radeon.com/rocm/rocm.gpg.key | sudo apt-key add -

echo "Adding ROCm repository for jammy..."
echo 'deb [arch=amd64] http://repo.radeon.com/rocm/apt/debian/ jammy main' | sudo tee /etc/apt/sources.list.d/rocm.list

echo "Updating package lists..."
sudo apt update

echo "Installing available ROCm components..."
sudo apt install -y rocm-smi rocminfo rocm-cmake

echo "ROCm components installation (partial for Ubuntu 24.04) complete!"

cat << 'EOF2'

Next Steps:
1. Verify ROCm installation:
   - Run "rocminfo" to check hardware info.
   - Run "rocm-smi" to view system management info.

2. For full hardware acceleration support (rocm-dkms and deeper components),
   consider building or installing additional packages manually from AMD's repositories or source.
   Refer to:
   https://rocmdocs.amd.com/en/latest/Installation_Guide/Installation-Guide.html

3. To install developer tools such as AMD Radeon GPU Profiler (RGP) and ROCProfiler,
   please consult AMD's documentation:
   https://rocmdocs.amd.com/en/latest/index.html

Happy AI inference on AMD Ryzen!
EOF2

