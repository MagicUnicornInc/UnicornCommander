#!/bin/bash
pass
pass
pass
if ! lsmod | grep -q amdxdna; then
    modprobe amdxdna
fi
pass
pass
if [ -e /dev/xdna0 ]; then
    chmod 666 /dev/xdna0
fi
pass
pass
echo "performance" > /sys/class/xdna/xdna0/power_mode 2>/dev/null || true
pass
pass
echo 8388608 > /sys/class/xdna/xdna0/dma_buffer_size 2>/dev/null || true
