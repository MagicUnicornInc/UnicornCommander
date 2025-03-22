# DeepSeek Quark Integration for Ryzen AI

This is the AMD Quark integration for the UnicornCommander project, optimized for Ryzen 9 8945HS with 780M iGPU and XDNA NPU.

## Overview

This package provides the necessary tools and scripts to run optimized DeepSeek models on AMD Ryzen AI hardware with NPU (Neural Processing Unit) acceleration. It integrates with the broader UnicornCommander KDE AI Interface project to provide highly efficient local LLM inference capabilities.

## Key Features

- **Hardware Acceleration**: Utilizes the XDNA NPU for efficient model inference
- **Optimized Models**: Support for DeepSeek Coder models quantized for performance
- **Hybrid Execution**: Efficiently splits workload across NPU, GPU, and CPU
- **Automatic Fallback**: CPU-only mode when hardware acceleration isn't available
- **Compatible with UnicornCommander**: Integrates into the broader AI interface

## Quick Start

1. **Run the setup script**:
   ```bash
   ./setup_ryzen_ai.sh
   ```

2. **Launch the optimized interface**:
   ```bash
   ./run_optimized_deepseek.sh
   ```

## Documentation

- [AMD_QUARK_SETUP.md](AMD_QUARK_SETUP.md) - Main setup guide
- [MANUAL_SETUP_GUIDE.md](MANUAL_SETUP_GUIDE.md) - Detailed manual setup instructions
- [RYZEN_AI_OPTIMIZATION.md](RYZEN_AI_OPTIMIZATION.md) - Performance optimization tips
- [AMD_QUARK_RECOMMENDED_MODELS.md](AMD_QUARK_RECOMMENDED_MODELS.md) - Model selection guide

## System Requirements

- **Processor**: AMD Ryzen AI processor with XDNA NPU (e.g., Ryzen 9 8945HS)
- **GPU**: AMD 780M integrated GPU or better
- **RAM**: 16GB minimum, 32GB recommended
- **Storage**: 10GB free space
- **Python**: 3.9-3.11 (for Quark), 3.12 works with CPU-only mode

## Files Included

- **setup_ryzen_ai.sh**: Automated setup script
- **run_optimized_deepseek.sh**: Launcher for accelerated interface
- **run_without_quark.sh**: CPU-only fallback mode
- **optimize_models.py**: Model quantization and optimization tool
- **quark_deepseek_gui.py**: Main GUI interface for DeepSeek models

## Performance Expectations

When properly configured on Ryzen 9 8945HS:

- **DeepSeek 6.7B**: 15-25 tokens/second with NPU acceleration
- **DeepSeek 1.3B**: 40-60 tokens/second with NPU acceleration
- **CPU-only mode**: 5-8 tokens/second for 6.7B model, 10-15 tokens/second for 1.3B

## Troubleshooting

For troubleshooting assistance, please refer to the Troubleshooting section in [AMD_QUARK_SETUP.md](AMD_QUARK_SETUP.md) or [MANUAL_SETUP_GUIDE.md](MANUAL_SETUP_GUIDE.md).

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- AMD for Quark and Ryzen AI technology
- DeepSeek AI for their high-quality open models
- The UnicornCommander project team