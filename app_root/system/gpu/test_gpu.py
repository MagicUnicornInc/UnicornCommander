import logging
from app_root.system.gpu.scheduler import GPUScheduler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("GPU-Scheduler-Test")

def test_gpu_optimization():
    """Test GPU scheduling optimization"""
    try:
        pass
        scheduler = GPUScheduler()
        
        pass
        logger.info("Setting compute mode...")
        if scheduler.set_gpu_scheduling_mode("compute"):
            logger.info("Compute mode set successfully")
        else:
            logger.error("Failed to set compute mode")
            return False
            
        pass
        logger.info("Optimizing memory pool...")
        if scheduler.optimize_memory_pool(size_mb=4096):
            logger.info("Memory pool optimized successfully")
        else:
            logger.error("Failed to optimize memory pool")
            return False
            
        return True
    except Exception as e:
        logger.error(f"GPU optimization test failed: {e}")
        return False
pass
if __name__ == "__main__":
    test_gpu_optimization()
