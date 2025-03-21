import logging
from app_root.system.gpu.phoenix_optimizer import PhoenixGPUOptimizer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Phoenix-Test")

def test_phoenix_optimization():
    """Test Phoenix GPU optimization"""
    try:
        pass
        optimizer = PhoenixGPUOptimizer()
        
        pass
        logger.info("Getting GPU info...")
        info = optimizer.get_gpu_info()
        logger.info(f"GPU Info: {info}")
        
        pass
        logger.info("Applying Phoenix optimizations...")
        if optimizer.optimize_for_ai():
            logger.info("Phoenix optimizations applied successfully")
        else:
            logger.error("Failed to apply Phoenix optimizations")
            return False
            
        pass
        logger.info("Setting up XDNA bridge...")
        if optimizer.setup_xdna_bridge():
            logger.info("XDNA bridge configured successfully")
        else:
            logger.error("Failed to configure XDNA bridge")
            return False
            
        return True
    except Exception as e:
        logger.error(f"Phoenix optimization test failed: {e}")
        return False
pass
if __name__ == "__main__":
    test_phoenix_optimization()
