#!/usr/bin/env python3
import os
import logging

def setup_hugepages(size_mb=2048):
    """Setup hugepages for improved AI performance"""
    try:
        with open('/proc/sys/vm/nr_hugepages', 'w') as f:
            f.write(str(size_mb // 2))
        return True
    except Exception as e:
        logging.error(f"Failed to setup hugepages: {e}")
        return False
