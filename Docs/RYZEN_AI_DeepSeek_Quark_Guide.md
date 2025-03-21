# Ryzen AI, DeepSeek-R1, and Quark Integration Guide

## Overview

The following guide provides an overview of the evolving AMD ecosystem:

- **Vitis AI Deprecation**: Vitis AI is being deprecated in favor of Quark, a lightweight framework optimized for Ryzen AI NPUs.
- **Recommended Pipeline**: Quark + ONNX + INT8 models.
- **DeepSeek-R1**: Optimized DeepSeek-R1 Distill models for hybrid execution (CPU, 780M iGPU, and XDNA NPU).

## Key Hardware & Software Details

- **Compatible Hardware**: Ryzen 9 8945HS and other supported Ryzen models.
- **Performance Metrics**: ~27 tokens/sec on Ryzen 7 8845HS using DeepSeek-R1.
- **Toolchain Notes**: Issues with ONNX conversion and sparse documentation exist; monitor for updates.

## Key URLs

1. [AMD Quark + DeepSeek Integration Tutorial](https://www.amd.com/en/developer/resources/technical-articles/deepseek-distilled-models-on-ryzen-ai-processors.html)
2. [Hugging Face – AMD Ryzen AI DeepSeek-R1 Collection](https://huggingface.co/collections/amd/amd-ryzenai-deepseek-r1-distill-hybrid-67a53471e9d5f14bece775d2)
3. [Community Thread: Quark Setup on Ryzen 8840](https://community.amd.com/t5/ai-discussions/compiling-model-for-ryzenai-8840-igpu-npu-using-quark/m-p/753302#M1008)
4. [AMD Blog: DeepSeek-R1 Distilled on Ryzen AI](https://community.amd.com/t5/ai/experience-the-deepseek-r1-distilled-reasoning-models-on-amd/ba-p/740593)
5. [Community Troubleshooting: Running LLMs on RyzenAI NPU](https://community.amd.com/t5/ai-discussions/issue-running-llms-on-amd-ryzenai-npu/m-p/733412)
6. [GitHub – AMD Quark Runtime](https://github.com/amd/Quark)
