#!/usr/bin/env python3
"""
Launcher for KDE AI Interface with Quark and DeepSeek-R1
This script detects the available components and launches the appropriate GUI
"""

import os
import sys
import logging
import subprocess
import importlib.util

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("QuarkLauncher")

def check_quark_availability():
    """Check if AMD Quark is available"""
    try:
        # Try to import quark
        spec = importlib.util.find_spec('quark')
        if spec is None:
            logger.warning("AMD Quark not found in Python environment")
            return False
            
        # Check if we can actually import it
        import quark
        logger.info(f"Quark version: {quark.__version__}")
        
        # Check for backends
        backends = quark.get_available_backends()
        logger.info(f"Available backends: {backends}")
        
        if not backends:
            logger.warning("No Quark backends available")
            return False
            
        # Check if we have any hardware acceleration
        has_acceleration = any(b != "CPU" for b in backends)
        if has_acceleration:
            logger.info("Hardware acceleration available")
        else:
            logger.info("Only CPU backend available")
            
        return True
        
    except ImportError as e:
        logger.warning(f"Error importing Quark: {e}")
        return False
    except Exception as e:
        logger.warning(f"Error checking Quark: {e}")
        return False

def check_xdna_driver():
    """Check if XDNA driver is loaded"""
    try:
        with open('/proc/modules', 'r') as f:
            modules = f.read()
            if 'amdxdna' in modules:
                logger.info("XDNA driver is loaded")
                return True
            else:
                logger.warning("XDNA driver is not loaded")
                return False
    except Exception as e:
        logger.warning(f"Could not check XDNA driver status: {e}")
        return False

def check_deepseek_models():
    """Check if DeepSeek models are available"""
    models_dir = os.path.join(os.path.expanduser("~"), "GIT-Projects/KDE AI Interface/quark-integration/models")
    if not os.path.exists(models_dir):
        logger.warning(f"Models directory not found: {models_dir}")
        return False
        
    # Look for model directories
    model_count = 0
    for item in os.listdir(models_dir):
        item_path = os.path.join(models_dir, item)
        if os.path.isdir(item_path):
            # Check if this looks like a model directory
            if os.path.exists(os.path.join(item_path, "tokenizer.json")):
                # Look for ONNX files
                for file in os.listdir(item_path):
                    if file.endswith(".onnx"):
                        logger.info(f"Found model: {item}")
                        model_count += 1
                        break
    
    logger.info(f"Found {model_count} DeepSeek models")
    return model_count > 0

def check_huggingface_hub():
    """Check if huggingface_hub is available for downloading models"""
    try:
        import huggingface_hub
        logger.info(f"huggingface_hub version: {huggingface_hub.__version__}")
        return True
    except ImportError:
        logger.warning("huggingface_hub not available")
        return False

def main():
    """Main function to launch the appropriate GUI"""
    logger.info("Starting KDE AI Interface with Quark/DeepSeek-R1...")
    
    # Check prerequisites
    has_quark = check_quark_availability()
    has_xdna = check_xdna_driver()
    has_models = check_deepseek_models()
    has_hf_hub = check_huggingface_hub()
    
    # Print status
    logger.info("Status Summary:")
    logger.info(f"  - AMD Quark: {'Available' if has_quark else 'Not Available'}")
    logger.info(f"  - XDNA Driver: {'Loaded' if has_xdna else 'Not Loaded'}")
    logger.info(f"  - DeepSeek Models: {'Found' if has_models else 'Not Found'}")
    logger.info(f"  - HuggingFace Hub: {'Available' if has_hf_hub else 'Not Available'}")
    
    # Determine what to launch
    if has_quark:
        if has_models:
            logger.info("Launching Quark DeepSeek GUI with existing models")
            try:
                subprocess.run([sys.executable, "quark_deepseek_gui.py"])
                return 0
            except Exception as e:
                logger.error(f"Error launching quark_deepseek_gui.py: {e}")
        elif has_hf_hub:
            logger.info("No models found, but HuggingFace Hub is available. Launching GUI to download models.")
            try:
                subprocess.run([sys.executable, "quark_deepseek_gui.py"])
                return 0
            except Exception as e:
                logger.error(f"Error launching quark_deepseek_gui.py: {e}")
        else:
            logger.warning("No models and no way to download them. Running test script.")
            print("No DeepSeek models found and HuggingFace Hub is not available.")
            print("Please install huggingface_hub to download models:")
            print("pip install huggingface_hub")
            try:
                subprocess.run([sys.executable, "test_quark_deepseek.py", "--prompt", "Testing Quark without models"])
                return 0
            except Exception as e:
                logger.error(f"Error launching test_quark_deepseek.py: {e}")
    else:
        logger.error("AMD Quark not available. Please install it to use this interface.")
        print("\nERROR: AMD Quark is not available. This application requires:")
        print("1. AMD Ryzen AI processor with XDNA NPU")
        print("2. AMD Quark runtime properly installed")
        print("3. Proper drivers for hardware acceleration")
        print("\nPlease download and install from: https://www.amd.com/en/developer/tools/ryzen-ai.html")
        print("Then ensure the XDNA driver is loaded with: lsmod | grep amdxdna")
        print("\nNo simulation mode is available - hardware acceleration is required.")
    
    # If we reach here, we couldn't launch any suitable application
    logger.error("Could not launch a suitable application")
    return 1

if __name__ == "__main__":
    sys.exit(main())