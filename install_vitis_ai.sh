#!/bin/bash
# install_vitis_ai.sh
# This script pulls the Vitis AI docker image, serving as a step to install the Vitis AI toolchain.
#
# NOTE: Ensure that Docker is installed and running.
# If you do not have Docker, install it first using:
#   curl -fsSL https://get.docker.com -o get-docker.sh && sh get-docker.sh

set -e

echo "Pulling the official Vitis AI docker image..."
docker pull xilinx/vitis-ai:latest

echo "Vitis AI docker image pulled successfully!"

cat << 'EOF2'
Next Steps:
1. Verify the docker image exists by running:
      docker images | grep vitis-ai
2. Follow the Vitis AI documentation for running compilation and optimization of ONNX models:
      https://www.xilinx.com/products/design-tools/vitis-ai.html

Happy AI inference on AMD Ryzen!
EOF2

