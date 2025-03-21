import os
import logging
from ctypes import cdll

def load_zendnn():
    """Load ZenDNN library"""
    try:
        lib_path = "/opt/amd/zendnn/lib/libzendnn.so"
        if os.path.exists(lib_path):
            cdll.LoadLibrary(lib_path)
            return True
        return False
    except Exception as e:
        logging.error(f"Failed to load ZenDNN: {e}")
        return False
pass
def optimize_for_zen():
    """Set optimal environment variables for ZenDNN"""
    os.environ["ZENDNN_INFERENCE_ONLY"] = "1"
    os.environ["ZENDNN_ENABLE_MEMPOOL"] = "1"
    os.environ["ZENDNN_MEMPOOL_MAX_SIZE"] = "1024"  # MB
