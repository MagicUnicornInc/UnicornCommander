#!/usr/bin/env python3
import os
import sys
import subprocess
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("KDE-AI-Interface-Launcher")

def check_hardware_acceleration():
    """Check if hardware acceleration is available"""
    try:
        import onnxruntime as ort
        providers = ort.get_available_providers()
        logger.info(f"Available ONNX Runtime providers: {providers}")
        
        if 'VitisAIExecutionProvider' in providers:
            logger.info("Vitis AI Execution Provider is available")
            return True
        else:
            logger.warning("Vitis AI Execution Provider is not available")
            
        # Check if XDNA driver is loaded
        with open('/proc/modules', 'r') as f:
            modules = f.read()
            if 'amdxdna' in modules:
                logger.info("XDNA driver is loaded")
            else:
                logger.warning("XDNA driver is not loaded")
        
        # Check if XRT libraries are available
        import os
        if 'XILINX_XRT' in os.environ:
            logger.info(f"XILINX_XRT is set to {os.environ['XILINX_XRT']}")
        else:
            logger.warning("XILINX_XRT environment variable is not set")
            
        return False
    except Exception as e:
        logger.error(f"Error checking hardware acceleration: {e}")
        return False

def check_optimum_amd():
    """Check if optimum-amd is available"""
    try:
        import importlib.util
        spec = importlib.util.find_spec('optimum.amd')
        if spec is not None:
            logger.info("optimum-amd is available")
            return True
        else:
            logger.warning("optimum-amd is not available")
            return False
    except Exception as e:
        logger.error(f"Error checking optimum-amd: {e}")
        return False

def main():
    """Main function"""
    logger.info("Starting KDE AI Interface...")
    
    # Check if hardware acceleration is available
    has_hardware_accel = check_hardware_acceleration() and check_optimum_amd()
    
    # Launch the appropriate GUI
    if has_hardware_accel:
        logger.info("Launching with hardware acceleration")
        try:
            subprocess.run([sys.executable, "amd_optimized_gui.py"])
        except Exception as e:
            logger.error(f"Error launching hardware accelerated GUI: {e}")
            logger.info("Falling back to simulation mode")
            subprocess.run([sys.executable, "simulate_ryzen_ai_gui.py"])
    else:
        logger.info("Launching in simulation mode")
        logger.info("To enable hardware acceleration, follow the instructions in vitis_ai_ep/INSTALL_INSTRUCTIONS.md")
        subprocess.run([sys.executable, "simulate_ryzen_ai_gui.py"])

if __name__ == "__main__":
    main()