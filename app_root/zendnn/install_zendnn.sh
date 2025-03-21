#!/bin/bash
# Install ZenDNN dependencies
sudo apt-get update
sudo apt-get install -y build-essential cmake git

# Clone ZenDNN
git clone https://github.com/amd/ZenDNN.git
cd ZenDNN

# Build and install
./scripts/zendnn_build.sh
sudo ./scripts/zendnn_install.sh
