#!/usr/bin/env python3
import os
import psutil
import logging

def set_ai_process_affinity(pid=None):
    """Set CPU affinity for AI processes"""
    try:
        process = psutil.Process(pid or os.getpid())
        cores = list(range(psutil.cpu_count() // 2))
        process.cpu_affinity(cores)
        return True
    except Exception as e:
        logging.error(f"Failed to set CPU affinity: {e}")
        return False
