# AMD Ryzen AI Hardware Acceleration Setup

This guide explains what we've discovered about the AMD Ryzen AI hardware acceleration and what's needed to get it working.

## Current Status

✅ **Working Components:**
- XDNA kernel module (`amdxdna`) is loaded
- XRT (Xilinx Runtime) libraries are installed in `/opt/xilinx/xrt/lib`
- AMD-optimized Llama 3.2 1B model in ONNX format is downloaded
- The basic GUI application works in simulation mode

❌ **Missing Components:**
- ONNX Runtime with Vitis AI Execution Provider support
- Custom AMD operators for ONNX models (like `com.amd:AMDSimplifiedLayerNormalization`)
- Proper device nodes for the XDNA NPU

## Error Diagnosis

When trying to load the AMD-optimized model, we get the error:
```
Fatal error: com.amd:AMDSimplifiedLayerNormalization(-1) is not a registered function/op
```

This confirms that the custom AMD operators required by the model are not available in the standard ONNX Runtime.

## How to Fix

To enable hardware acceleration, you need to install the AMD Ryzen AI Software stack:

1. **Download the AMD Ryzen AI Software SDK** from AMD's official site:
   - https://www.amd.com/en/developer/tools/ryzen-ai.html

2. **Install the SDK components:**
   - ONNX Runtime with Vitis AI Execution Provider
   - Custom AMD operators for ONNX models
   - Configuration utilities for the XDNA NPU

3. **Verify the Installation:**
   - Check if the Vitis AI Execution Provider is available:
     ```python
     import onnxruntime as ort
     print(ort.get_available_providers())
     ```
   - You should see 'VitisAIExecutionProvider' in the list

4. **Run the Hardware-Accelerated GUI:**
   - Once the Vitis AI Execution Provider is available, run:
     ```bash
     python run_kde_ai_interface.py
     ```
   - This script will automatically use hardware acceleration if available

## Available Models

These AMD-optimized models should work once hardware acceleration is set up:

1. **meta-llama/Llama-3.2-1B-Instruct** (already downloaded)
   - INT4 quantized version optimized for XDNA NPU

2. Other models that can be downloaded from Hugging Face:
   - **amd/Llama-3.2-3B-Instruct-awq-g128-int4-asym-bf16-onnx-ryzen-strix**
   - **amd/Mistral-7B-Instruct-v0.3-onnx-ryzen-strix**
   - **amd/Phi-2-onnx-ryzen-strix**
   - **amd/Phi-3-mini-4k-instruct-onnx-ryzen-strix**

## Temporary Solution

Until the full AMD Ryzen AI stack is installed, you can run the simulation mode:

```bash
python simulate_ryzen_ai_gui.py
```

Or use the wrapper script that will automatically fall back to simulation mode:

```bash
python run_kde_ai_interface.py
```

## For More Information

Detailed installation instructions for the Vitis AI Execution Provider are available in:
`vitis_ai_ep/INSTALL_INSTRUCTIONS.md`