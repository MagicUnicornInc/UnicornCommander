#!/bin/bash
# Optimize GPU settings for AI workloads

# Set high performance mode
echo "performance" | sudo tee /sys/class/drm/card0/device/power_dpm_force_performance_level

# Enable compute mode
echo "1" | sudo tee /sys/class/drm/card0/device/gpu_busy_percent

# Set optimal memory parameters
echo "3" | sudo tee /sys/class/drm/card0/device/pp_dpm_mclk
echo "3" | sudo tee /sys/class/drm/card0/device/pp_dpm_sclk

# Apply AMD-specific optimizations
rocm-smi --setperflevel high
rocm-smi --setfan 255
