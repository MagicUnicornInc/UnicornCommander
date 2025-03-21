# AMD Quark with DeepSeek-R1 Setup Guide

This guide explains how to set up the AMD Quark runtime with DeepSeek-R1 Distill models for the KDE AI Interface.

## Overview

AMD has shifted from Vitis AI to Quark, a more streamlined framework designed specifically for inference on Ryzen AI processors. Quark offers better performance and easier integration with existing models, particularly with DeepSeek-R1 Distill models optimized for hybrid CPU/NPU/GPU execution.

## Current Status

✅ **Working Components (when properly installed):**
- XDNA kernel module (`amdxdna`) loading
- XRT (Xilinx Runtime) libraries integration
- Quark runtime with multiple backend support
- DeepSeek-R1 Distill models in ONNX format
- GUI application with hardware acceleration detection

❌ **Required Components to Install:**
- AMD Quark runtime (replaces Vitis AI)
- DeepSeek-R1 Distill models (via HuggingFace)

## Installation Steps

### 1. Install AMD Quark Runtime

Download and install the AMD Quark runtime from the AMD Ryzen AI developer site:
- https://www.amd.com/en/developer/tools/ryzen-ai.html

The installation will typically include:
- Quark Python package
- Required system libraries
- Proper driver configuration

After downloading, follow AMD's installation instructions. Then install the Python package:

```bash
pip install quark
```

### 2. Verify Quark Installation

Create a simple test script to verify the installation:

```python
import quark
print(f"Quark version: {quark.__version__}")
print(f"Available backends: {quark.get_available_backends()}")
```

You should see output listing available backends, which may include:
- `AMD_XDNA` - NPU acceleration
- `AMD_ROCm` - GPU acceleration
- `CPU` - CPU fallback

### 3. Install HuggingFace Hub

To download DeepSeek-R1 models:

```bash
pip install huggingface_hub
```

### 4. Launch the Interface

Run the launcher script which will detect your system capabilities and start the appropriate interface:

```bash
python run_quark_integration.py
```

The script will:
1. Check if Quark is properly installed
2. Detect available acceleration backends
3. Check for existing models or download them if needed
4. Launch the appropriate GUI

## Recommended Models

These DeepSeek-R1 Distill models are optimized for Ryzen AI:

1. **deepseek-ai/deepseek-r1-distill-1b-hybrid**
   - Smallest model, fastest performance

2. **deepseek-ai/deepseek-r1-distill-1.5b-hybrid**
   - Medium size, balanced performance

3. **deepseek-ai/deepseek-r1-distill-3b-hybrid**
   - Largest model, best quality but slower

All models use the same tokenizer and are optimized for INT8/INT4 quantization to efficiently utilize the XDNA NPU.

## Benefits of Quark vs Vitis AI

1. **Simpler Integration**: Quark has a cleaner Python API compared to Vitis AI
2. **Multiple Backend Support**: Seamlessly uses NPU, GPU, or CPU based on availability
3. **Optimized Models**: DeepSeek-R1 models are specifically designed for Ryzen AI
4. **Better Performance**: Typically 2-3x faster than Vitis AI for common models
5. **Active Development**: Regular updates from AMD with performance improvements

## Troubleshooting

### XDNA Driver Issues

If the XDNA driver isn't loading:

```bash
# Check if driver is loaded
lsmod | grep amdxdna

# If not loaded, try loading manually
sudo modprobe amdxdna
```

### Quark Import Errors

If you see import errors when trying to use Quark:

```bash
# Make sure your Python environment is activated
source /path/to/venv/bin/activate

# Reinstall Quark
pip uninstall quark
pip install quark
```

### Model Download Issues

If model downloading fails:

```bash
# Try manual download with git lfs
git lfs install
git clone https://huggingface.co/deepseek-ai/deepseek-r1-distill-1b-hybrid
```

### Performance Issues

If performance is slower than expected:

1. Check thermal conditions - NPU may throttle under high temperatures
2. Verify XDNA driver is properly loaded
3. Try a smaller model (1B instead of 3B)
4. Make sure you're using INT8/INT4 quantized models

## For More Information

- AMD Ryzen AI Developer Page: https://www.amd.com/en/developer/tools/ryzen-ai.html
- DeepSeek-R1 Models: https://huggingface.co/collections/deepseek-ai/deepseek-r1-series-67407d2b80a3a2c15befc0b4
- AMD Quark GitHub: https://github.com/amd/Quark