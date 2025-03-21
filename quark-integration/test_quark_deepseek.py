#!/usr/bin/env python3
"""
Test script for AMD Quark with DeepSeek-R1 Distill models
This script tests the basic functionality of Quark inference with DeepSeek-R1 models
"""

import os
import sys
import logging
import time
import argparse
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("QuarkDeepSeek")

def check_environment():
    """Check if required environment components are installed"""
    try:
        import quark
        logger.info(f"Quark runtime found: {quark.__version__}")
        
        # Check AMD XDNA driver
        try:
            with open('/proc/modules', 'r') as f:
                modules = f.read()
                if 'amdxdna' in modules:
                    logger.info("XDNA driver is loaded")
                else:
                    logger.warning("XDNA driver is not loaded")
        except Exception as e:
            logger.warning(f"Could not check XDNA driver status: {e}")
        
        # Check if XRT runtime is available
        if 'XILINX_XRT' in os.environ:
            logger.info(f"XILINX_XRT is set to {os.environ['XILINX_XRT']}")
        else:
            logger.warning("XILINX_XRT environment variable is not set")
            
        return True
    except ImportError:
        logger.error("Quark runtime not found. Please install AMD Quark")
        return False

def download_model(model_name="deepseek-ai/deepseek-r1-distill-1b-hybrid"):
    """Download model files from Hugging Face if not available locally"""
    try:
        from huggingface_hub import snapshot_download
        
        # Check if model directory already exists
        model_dir = Path.home() / "GIT-Projects/KDE AI Interface/quark-integration/models" / model_name.split('/')[-1]
        if model_dir.exists():
            logger.info(f"Model already exists at {model_dir}")
            return str(model_dir)
        
        logger.info(f"Downloading model {model_name}...")
        model_path = snapshot_download(
            repo_id=model_name,
            local_dir=str(model_dir),
            ignore_patterns=["*.bin", "*.pt", "*.safetensors"],  # We only need the ONNX files
        )
        logger.info(f"Model downloaded to {model_path}")
        return model_path
    except Exception as e:
        logger.error(f"Error downloading model: {e}")
        return None

def setup_quark_model(model_path):
    """Set up Quark model for inference"""
    try:
        import quark
        
        # Look for required files
        model_dir = Path(model_path)
        model_file = None
        
        # Find ONNX model file - prefer quantized models
        for pattern in ["*int8*.onnx", "*int4*.onnx", "*.onnx"]:
            models = list(model_dir.glob(pattern))
            if models:
                model_file = str(models[0])
                break
        
        if not model_file:
            logger.error(f"No ONNX model file found in {model_path}")
            return None
            
        logger.info(f"Using model file: {model_file}")
        
        # Find tokenizer
        tokenizer_file = model_dir / "tokenizer.json"
        if not tokenizer_file.exists():
            logger.error(f"Tokenizer not found at {tokenizer_file}")
            return None
            
        # Create Quark model
        logger.info("Initializing Quark model...")
        
        # Get available backends
        backends = quark.get_available_backends()
        logger.info(f"Available Quark backends: {backends}")
        
        # Load model - try different backends in order of preference
        preferred_backends = ["AMD_XDNA", "AMD_ROCm", "CPU"]
        selected_backend = None
        
        for backend in preferred_backends:
            if backend in backends:
                selected_backend = backend
                break
                
        if not selected_backend:
            logger.warning(f"None of the preferred backends {preferred_backends} available, using default")
            selected_backend = backends[0] if backends else None
            
        logger.info(f"Using backend: {selected_backend}")
        
        # Configuration based on selected backend
        config = {
            "model_path": model_file,
            "backend": selected_backend if selected_backend else "CPU",
            "tokenizer_path": str(tokenizer_file),
            "temperature": 0.7,
            "top_p": 0.9
        }
        
        model = quark.Model(**config)
        return model
        
    except Exception as e:
        logger.error(f"Error setting up Quark model: {e}")
        return None

def generate_text(model, prompt, max_tokens=200):
    """Generate text using the model"""
    try:
        logger.info(f"Generating text for prompt: {prompt}")
        start_time = time.time()
        
        # Generate response
        response = model.generate(prompt, max_tokens=max_tokens)
        
        # Calculate stats
        end_time = time.time()
        duration = end_time - start_time
        tokens = len(response.split())
        tokens_per_second = tokens / duration
        
        logger.info(f"Generated {tokens} tokens in {duration:.2f} seconds ({tokens_per_second:.2f} tokens/sec)")
        return response
    except Exception as e:
        logger.error(f"Error generating text: {e}")
        return f"Error: {str(e)}"

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Test AMD Quark with DeepSeek-R1 models")
    parser.add_argument("--model", default="deepseek-ai/deepseek-r1-distill-1b-hybrid", 
                       help="Model name or path (default: deepseek-ai/deepseek-r1-distill-1b-hybrid)")
    parser.add_argument("--prompt", default="Explain quantum computing in simple terms", 
                       help="Prompt for text generation")
    parser.add_argument("--max_tokens", type=int, default=200, 
                       help="Maximum number of tokens to generate")
    
    args = parser.parse_args()
    
    # Check environment
    if not check_environment():
        logger.error("Environment check failed. Exiting.")
        return 1
    
    # Download model if needed
    model_path = download_model(args.model)
    if not model_path:
        logger.error("Failed to get model. Exiting.")
        return 1
    
    # Set up model
    model = setup_quark_model(model_path)
    if not model:
        logger.error("Failed to set up model. Exiting.")
        return 1
    
    # Generate text
    response = generate_text(model, args.prompt, args.max_tokens)
    print("\n=== Generated Response ===\n")
    print(response)
    print("\n=========================\n")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())