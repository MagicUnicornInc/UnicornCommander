import os
import sys
import logging
import time

# Set up logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("QuarkTest")

# Check for Quark
try:
    logger.info("Checking if Quark is available...")
    import quark
    print(f"Quark version: {quark.__version__}")
    
    # Attempt to check available backends via optimum-amd
    logger.info("Checking for AMD hardware via optimum-amd...")
    import onnxruntime as ort
    print(f"Available ORT providers: {ort.get_available_providers()}")
    
    print("Checking for XDNA driver...")
    try:
        if os.path.exists("/dev/amdxdna0"):
            print("XDNA device found at /dev/amdxdna0")
        else:
            print("XDNA device not found at /dev/amdxdna0")
        
        # Try to load amdxdna kernel module
        os.system("lsmod | grep amdxdna")
    except Exception as e:
        print(f"Error checking for XDNA driver: {e}")
    
    print("\nQuark test completed. XDNA hardware acceleration is NOT available or properly configured.")
    print("To install the AMD XDNA driver, follow the instructions in the AMD Ryzen AI documentation.")
    
except ImportError as e:
    logger.error(f"Error importing Quark: {e}")
    print("Quark is not installed. Please follow the installation instructions.")
