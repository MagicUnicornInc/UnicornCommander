# AMD Quark Recommended Models

This document outlines the recommended DeepSeek models for different AMD Ryzen AI hardware configurations.

## AMD Ryzen 9 8945HS (Your System)

The **AMD Ryzen 9 8945HS** with XDNA NPU is a high-performance mobile processor capable of running larger models efficiently:

| Recommended Model | Parameters | Format | Benefits |
|------------------|------------|--------|----------|
| **deepseek-ai/deepseek-coder-6.7b-instruct** | 6.7 billion | FP16/INT8 | Best quality for coding tasks |
| **TheBloke/deepseek-coder-6.7B-instruct-GGUF** | 6.7 billion | GGUF | Better compatibility |
| deepseek-ai/deepseek-coder-1.3b-instruct | 1.3 billion | FP16/INT8 | Faster responses for simple tasks |

**Why the 6.7B model?** Your Ryzen 9 8945HS has excellent NPU capabilities and can handle the 6.7B model well, providing significantly better code generation and reasoning quality than smaller models while maintaining good performance.

## Other Hardware Configurations

### Mid-Range (AMD Ryzen 7 8840HS, 8845HS)

| Recommended Model | Parameters | Format | Benefits |
|------------------|------------|--------|----------|
| **deepseek-ai/deepseek-coder-1.3b-instruct** | 1.3 billion | FP16/INT8 | Best balance for mid-range hardware |
| TheBloke/deepseek-coder-1.3B-instruct-GGUF | 1.3 billion | GGUF | Better compatibility |

### Entry-Level (AMD Ryzen 5 8640HS)

| Recommended Model | Parameters | Format | Benefits |
|------------------|------------|--------|----------|
| **deepseek-ai/deepseek-coder-1.3b-instruct** | 1.3 billion | FP16/INT8 | More efficient on entry-level NPUs |
| **phi-2** | 2.7 billion | FP16/INT8 | Alternative option |

## Model Formats Explained

- **GGUF**: Highly efficient format with good compatibility across hardware
- **INT4/INT8**: Quantized formats for efficient NPU acceleration
- **FP16**: Half-precision format with good balance of precision and efficiency
- **Hybrid**: Models using a mix of multiple formats for different parts of the network

## Performance Expectations

For the **deepseek-coder-6.7b-instruct** model on your Ryzen 9 8945HS:

- **Tokens per second**: 15-25 tokens/second
- **First token latency**: 150-250ms
- **Memory usage**: ~5GB

## Backend Selection

Quark automatically selects the best backend for your hardware:

1. **AMD_XDNA**: Uses the NPU for acceleration (preferred for best efficiency)
2. **AMD_ROCm**: Uses the integrated GPU (good alternative)
3. **CPU**: Fallback option (much slower)

## Model Download Location

Models will be downloaded to:
`/home/ucadmin/GIT-Projects/KDE AI Interface/quark-integration/models/`

Each model typically requires 2-4GB of disk space.