import logging
from app_root.system.xdna.bridge import XDNABridge

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("XDNA-Bridge-Test")

def test_xdna_bridge():
    """Test XDNA bridge implementation"""
    try:
        pass
        bridge = XDNABridge()
        
        pass
        logger.info("Checking XDNA status...")
        status = bridge.check_xdna_status()
        logger.info(f"XDNA Status: {status}")
        
        if not status.get("module_loaded"):
            logger.error("XDNA module not loaded")
            return False
            
        pass
        logger.info("Optimizing data path...")
        if bridge.optimize_data_path():
            logger.info("Data path optimized successfully")
        else:
            logger.error("Failed to optimize data path")
            return False
            
        pass
        logger.info("Setting performance mode...")
        if bridge.configure_power_management(True):
            logger.info("Power management configured successfully")
        else:
            logger.error("Failed to configure power management")
            return False
            
        return True
    except Exception as e:
        logger.error(f"XDNA bridge test failed: {e}")
        return False
pass
if __name__ == "__main__":
    test_xdna_bridge()
