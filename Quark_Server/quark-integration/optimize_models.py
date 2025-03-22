#!/usr/bin/env python3
"""
Model optimizer for AMD Ryzen AI NPU
This script quantizes and optimizes models for the XDNA NPU
"""

import os
import sys
import argparse
import logging
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("ModelOptimizer")

def check_quark_availability():
    """Check if Quark is available and which backends are supported"""
    try:
        import quark
        logger.info(f"Quark version: {quark.__version__}")
        backends = quark.get_available_backends()
        logger.info(f"Available backends: {backends}")
        return True, backends
    except ImportError:
        logger.error("Quark is not installed. Please install it first.")
        return False, []
    except Exception as e:
        logger.error(f"Error checking Quark: {e}")
        return False, []

def optimize_model(model_path, output_path=None, quantization="int8", optimization_level=1, target="xdna"):
    """Optimize a model using Quark"""
    try:
        # Import here to handle potential import errors
        import quark
        from quark.onnx import optimize_model as quark_optimize

        # Default output path
        if output_path is None:
            model_dir = os.path.dirname(model_path)
            model_name = os.path.basename(model_path)
            base_name, ext = os.path.splitext(model_name)
            output_path = os.path.join(model_dir, f"{base_name}_{quantization}{ext}")
        
        logger.info(f"Optimizing model {model_path}")
        logger.info(f"Quantization: {quantization}")
        logger.info(f"Optimization level: {optimization_level}")
        logger.info(f"Target: {target}")
        logger.info(f"Output path: {output_path}")
        
        # Perform the optimization
        optimized_model = quark_optimize(
            model_path,
            quantization=quantization,
            optimization_level=optimization_level,
            target=target
        )
        
        # Save the optimized model
        optimized_model.save(output_path)
        logger.info(f"Optimization complete. Model saved to {output_path}")
        return True
    except Exception as e:
        logger.error(f"Error optimizing model: {e}")
        return False

def scan_for_models(models_dir):
    """Scan for models in the specified directory"""
    models = []
    try:
        for root, dirs, files in os.walk(models_dir):
            for file in files:
                if file.endswith(".onnx"):
                    model_path = os.path.join(root, file)
                    models.append(model_path)
        return models
    except Exception as e:
        logger.error(f"Error scanning for models: {e}")
        return []

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Optimize models for AMD Ryzen AI")
    parser.add_argument("--model", type=str, help="Path to the model file")
    parser.add_argument("--output", type=str, help="Path to save the optimized model")
    parser.add_argument("--models-dir", type=str, default="models", 
                        help="Directory to scan for models")
    parser.add_argument("--quantization", type=str, default="int8",
                        choices=["fp16", "int8", "int4"],
                        help="Quantization format (fp16, int8, int4)")
    parser.add_argument("--optimization-level", type=int, default=1,
                        choices=[0, 1, 2, 3],
                        help="Optimization level (0-3)")
    parser.add_argument("--target", type=str, default="xdna",
                        choices=["cpu", "gpu", "xdna", "auto"],
                        help="Optimization target (cpu, gpu, xdna, auto)")
    parser.add_argument("--all", action="store_true",
                        help="Optimize all models in the models directory")
    args = parser.parse_args()
    
    # Check if Quark is available
    has_quark, backends = check_quark_availability()
    if not has_quark:
        logger.error("Quark is required for model optimization")
        return 1
    
    # Check if the target backend is available
    if args.target != "auto":
        if args.target.upper() not in [backend.upper() for backend in backends]:
            logger.warning(f"Target backend {args.target} is not available in {backends}")
            logger.warning("Optimization may not be optimal for your hardware")
    
    # Optimize a specific model
    if args.model:
        if not os.path.exists(args.model):
            logger.error(f"Model file not found: {args.model}")
            return 1
        
        success = optimize_model(
            args.model,
            args.output,
            args.quantization,
            args.optimization_level,
            args.target
        )
        
        return 0 if success else 1
    
    # Optimize all models in the directory
    if args.all:
        if not os.path.exists(args.models_dir):
            logger.error(f"Models directory not found: {args.models_dir}")
            return 1
        
        models = scan_for_models(args.models_dir)
        if not models:
            logger.warning(f"No models found in {args.models_dir}")
            return 0
        
        logger.info(f"Found {len(models)} models to optimize")
        
        success_count = 0
        for model_path in models:
            logger.info(f"Processing model: {model_path}")
            success = optimize_model(
                model_path,
                None,  # Auto-generate output path
                args.quantization,
                args.optimization_level,
                args.target
            )
            if success:
                success_count += 1
        
        logger.info(f"Optimized {success_count} out of {len(models)} models")
        return 0
    
    # If no model specified and not optimizing all, show help
    parser.print_help()
    return 0

if __name__ == "__main__":
    sys.exit(main())