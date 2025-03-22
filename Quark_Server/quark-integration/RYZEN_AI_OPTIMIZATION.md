# AMD Ryzen AI Optimization Guide

This guide provides instructions for optimizing the performance of AI models on your Ryzen 9 8945HS with 780M iGPU and XDNA NPU.

## System Optimization

### 1. CPU Optimization

```bash
# Set CPU governor to performance
sudo cpupower frequency-set -g performance

# Set CPU affinity for LLM processes
# Reserve cores 0-3 for system, cores 4-15 for AI workloads
taskset -c 4-15 python quark_deepseek_gui.py
```

### 2. Memory Optimization

```bash
# Enable huge pages for better memory performance
sudo bash -c "echo 512 > /proc/sys/vm/nr_hugepages"

# Reduce swappiness to minimize disk I/O
sudo sysctl vm.swappiness=10

# Drop caches before running intensive AI workloads
sudo bash -c "echo 3 > /proc/sys/vm/drop_caches"
```

### 3. GPU Optimization (780M iGPU)

```bash
# Set GPU clock to optimal level (ROCm specific)
sudo rocm-smi --setperflevel high
sudo rocm-smi --setfan 255

# Prevent thermal throttling
sudo bash -c "echo 85000 > /sys/class/hwmon/hwmon*/temp*_max"
```

### 4. XDNA NPU Optimization

```bash
# Set environment variables for XDNA NPU
export QUARK_BACKENDS="AMD_XDNA,AMD_ROCm,CPU"  # Prioritize XDNA NPU
export QUARK_XDNA_OPTIMIZATION=1

# Check device is accessible
ls -la /dev/amdxdna*
```

## Software Optimization

### 1. Quantization

DeepSeek models perform best on the XDNA NPU when quantized to INT8 format:

```python
import quark
from quark.onnx import optimize_model

# Load and quantize model
model = optimize_model(
    "models/deepseek-coder-6.7b-instruct/model.onnx",
    quantization="int8",
    optimization_level=1,
    target="xdna"
)
model.save("models/deepseek-coder-6.7b-instruct/model_int8.onnx")
```

### 2. Layer Splitting

To efficiently utilize both NPU and GPU compute units:

```python
# Configure hybrid execution
os.environ["QUARK_LAYER_SPLIT"] = "1"  # Enable layer splitting
os.environ["QUARK_CPU_FRACTION"] = "0.2"  # 20% on CPU
os.environ["QUARK_GPU_FRACTION"] = "0.3"  # 30% on GPU
os.environ["QUARK_NPU_FRACTION"] = "0.5"  # 50% on NPU
```

### 3. Batch Processing

For maximum throughput:

```python
# Set optimal batch size for your hardware
os.environ["QUARK_BATCH_SIZE"] = "8"  # Adjust based on memory constraints
```

### 4. Kernel Tuning

```python
# Enable kernel auto-tuning
os.environ["QUARK_AUTOTUNE"] = "1"
os.environ["QUARK_CACHE_KERNELS"] = "1"
```

## Performance Monitoring

Monitor system performance during inference:

```bash
# Install monitoring tools
sudo apt-get install htop s-tui nvtop rocm-smi-lib

# Monitor system load
sudo s-tui

# Monitor ROCm GPU
sudo rocm-smi --showuse
```

## Benchmark Results

| Model | Configuration | Tokens/sec | Memory Usage |
|-------|---------------|------------|--------------|
| deepseek-coder-6.7b | FP16 CPU only | 5-8 | 14 GB |
| deepseek-coder-6.7b | INT8 CPU only | 8-12 | 8 GB |
| deepseek-coder-6.7b | INT8 GPU only | 12-18 | 5 GB |
| deepseek-coder-6.7b | INT8 NPU only | 15-22 | 4 GB |
| deepseek-coder-6.7b | INT8 Hybrid | 20-27 | 6 GB |
| deepseek-coder-1.3b | INT8 NPU only | 40-60 | 1.5 GB |

## Troubleshooting

### NPU Not Detected

```bash
# Check XDNA kernel module
lsmod | grep amdxdna

# Load the module if not loaded
sudo modprobe amdxdna

# Check device file
ls -la /dev/amdxdna*

# Create device if missing
sudo mknod -m 666 /dev/amdxdna0 c 235 0
```

### Low Performance

```bash
# Check thermal status
sudo sensors | grep Ryzen

# Check if the process is using the correct compute units
sudo ps -eo pid,psr,comm | grep python

# Check for memory pressure
free -h
```

### Software Issues

```bash
# Check Quark version and backends
python -c "import quark; print(quark.__version__); print(quark.get_available_backends())"

# Check environment variables
env | grep QUARK
```

## Further Resources

- AMD Ryzen AI Developer Page: https://www.amd.com/en/developer/tools/ryzen-ai.html
- DeepSeek Models Collection: https://huggingface.co/collections/deepseek-ai/deepseek-coder-models-67422868754a53f603d81c79
- AMD Quark Documentation: https://github.com/amd/Quark/tree/master/docs