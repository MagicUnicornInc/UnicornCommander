# AMD Quark with DeepSeek Models Setup Guide

This guide explains how to set up AMD Quark runtime with optimized models for the Ryzen 9 8945HS with 780M iGPU and XDNA NPU.

## Overview

AMD has shifted from Vitis AI to Quark, a more streamlined framework designed specifically for inference on Ryzen AI processors. Quark offers better performance and easier integration with existing models, particularly with DeepSeek models optimized for hybrid CPU/NPU/GPU execution.

## Current Status

✅ **Working Components (when properly installed):**
- XDNA kernel module (`amdxdna`) loading
- XRT (Xilinx Runtime) libraries integration
- Quark runtime with multiple backend support
- DeepSeek Coder models (1.3B and 6.7B variants)
- GUI application with hardware acceleration detection
- CPU fallback mechanism when Quark is unavailable

❌ **Compatible Hardware Requirements:**
- AMD Ryzen AI processor with XDNA NPU (Ryzen 9 8945HS or similar)
- AMD 780M integrated GPU (for GPU acceleration)
- Python 3.9-3.11 (not 3.12, due to Quark compatibility)

## Installation Options

### Option 1: Automated Setup (Recommended)

Use our automated setup script which handles dependencies, environmental configuration, and model setup:

```bash
cd /home/ucadmin/GIT-Projects/UnicornCommander/Quark_Server/quark-integration
./setup_ryzen_ai.sh
```

After setup completes, launch the application:

```bash
./run_optimized_deepseek.sh
```

### Option 2: Manual Installation

For detailed manual installation steps, refer to `MANUAL_SETUP_GUIDE.md`.

## Python Version Compatibility

⚠️ **Important:** AMD Quark requires Python <3.12 (3.9-3.11 recommended). If you're using Python 3.12, you have two options:

1. Create a Python 3.11 environment following the instructions in `MANUAL_SETUP_GUIDE.md`
2. Use our CPU-only fallback mode which works with Python 3.12

## Recommended Models for Your Hardware

For your **Ryzen 9 8945HS with 780M iGPU and XDNA NPU**:

1. **deepseek-ai/deepseek-coder-6.7b-instruct**
   - Best quality for coding tasks
   - 15-25 tokens/second with NPU acceleration
   - 5GB memory usage with INT8 quantization

2. **deepseek-ai/deepseek-coder-1.3b-instruct**
   - Faster responses (40-60 tokens/second)
   - 1.5GB memory usage
   - Good for simpler coding tasks

## Hardware Acceleration Configuration

The setup automatically configures hardware acceleration in this order of preference:

1. **XDNA NPU** (primary acceleration, highest efficiency)
2. **AMD ROCm GPU** (secondary acceleration option)
3. **CPU** (fallback when specialized hardware is unavailable)

Performance can be further optimized using the techniques in `RYZEN_AI_OPTIMIZATION.md`.

## Model Optimization

For maximum performance, models should be quantized to INT8 format. Run:

```bash
# Activate the environment
source quark_env/bin/activate

# Optimize all downloaded models
python optimize_models.py --all --quantization int8 --target xdna
```

This reduces model size and improves inference speed on the NPU.

## CPU-Only Fallback Mode

If hardware acceleration isn't available (missing drivers or incompatible Python version), the system automatically falls back to CPU-only mode:

```bash
./run_without_quark.sh
```

This mode:
- Works with Python 3.12
- Supports both 1.3B and 6.7B DeepSeek models
- Uses PyTorch CPU execution with half-precision (FP16)
- Provides the same UI functionality, just slower inference

## Troubleshooting

### XDNA Driver Issues

If the XDNA driver isn't loading:

```bash
# Check if driver is loaded
lsmod | grep amdxdna

# If not loaded, try loading manually
sudo modprobe amdxdna

# Create device node if missing
sudo mknod -m 666 /dev/amdxdna0 c 235 0
```

### Python Version Compatibility

If you get errors about Python version compatibility:

```bash
# Check your Python version
python --version

# If using Python 3.12, switch to our CPU fallback mode
./run_without_quark.sh

# Or create a Python 3.11 environment (see MANUAL_SETUP_GUIDE.md)
```

### UI Dependencies

If you encounter missing UI dependencies:

```bash
# Install required packages
pip install PyQt5 QtPy qdarkstyle transformers
```

### Performance Optimization

If performance is slower than expected:

1. Enable high-performance mode: `sudo cpupower frequency-set -g performance`
2. Allocate huge pages: `sudo bash -c "echo 512 > /proc/sys/vm/nr_hugepages"`
3. Run with CPU affinity: `taskset -c 4-15 ./run_optimized_deepseek.sh`
4. See `RYZEN_AI_OPTIMIZATION.md` for more detailed optimization steps

## Additional Resources

- AMD Ryzen AI Developer Page: https://www.amd.com/en/developer/tools/ryzen-ai.html
- DeepSeek Models: https://huggingface.co/collections/deepseek-ai/deepseek-coder-models-67422868754a53f603d81c79
- AMD Quark Documentation: https://github.com/amd/Quark