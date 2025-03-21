import os
import logging
from typing import Optional

class GPUScheduler:
    def __init__(self):
        self.logger = logging.getLogger("GPU-Scheduler")
        
    def set_gpu_scheduling_mode(self, mode: str = "compute"):
        """Set GPU scheduling mode for optimal AI workload"""
        try:
            if mode == "compute":
                os.system("rocm-smi --setperflevel high")
                os.system("rocm-smi --setfan 255")
            return True
        except Exception as e:
            self.logger.error(f"Failed to set GPU mode: {e}")
            return False
            
    def optimize_memory_pool(self, size_mb: Optional[int] = None):
        """Optimize GPU memory pool size"""
        try:
            if size_mb:
                os.environ["HSA_ENABLE_SDMA"] = "0"
                os.environ["GPU_MAX_HEAP_SIZE"] = str(size_mb)
            return True
        except Exception as e:
            self.logger.error(f"Failed to optimize memory: {e}")
            return False
