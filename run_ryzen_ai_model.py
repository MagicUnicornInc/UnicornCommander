#!/usr/bin/env python3
import os
import sys
import logging
import argparse
from pathlib import Path
import numpy as np
import onnx
import onnxruntime as ort
from transformers import AutoTokenizer, TextIteratorStreamer
from threading import Thread
from typing import Dict, List, Optional, Tuple, Union

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("RyzenAI-Interface")

def download_model(model_id: str, cache_dir: Optional[str] = None) -> Path:
    """Download model from Hugging Face Hub"""
    logger.info(f"Downloading model {model_id}")
    from huggingface_hub import snapshot_download
    
    model_dir = snapshot_download(repo_id=model_id, cache_dir=cache_dir)
    return Path(model_dir)

class RyzenAIModel:
    def __init__(self, model_id: str, cache_dir: Optional[str] = None):
        """Initialize the Ryzen AI model"""
        self.model_id = model_id
        self.cache_dir = cache_dir
        self.model_path = None
        self.session = None
        self.tokenizer = None
        self.input_names = None
        self.output_names = None
        
        # Load the model
        self.load_model()
    
    def load_model(self):
        """Load the ONNX model and tokenizer"""
        try:
            # Download or use cached model
            model_dir = download_model(self.model_id, self.cache_dir)
            
            # Find the ONNX model file
            onnx_files = list(model_dir.glob("*.onnx"))
            if not onnx_files:
                raise FileNotFoundError(f"No ONNX model found in {model_dir}")
            
            self.model_path = onnx_files[0]
            logger.info(f"Found ONNX model: {self.model_path}")
            
            # Load tokenizer from the ONNX model directory
            model_dir = Path(model_dir)
            logger.info(f"Loading tokenizer from {model_dir}")
            
            # Try to find tokenizer files in the model directory
            if (model_dir / "tokenizer.model").exists() or (model_dir / "tokenizer.json").exists():
                self.tokenizer = AutoTokenizer.from_pretrained(model_dir)
            else:
                # Fall back to a compatible tokenizer
                if "Llama-3" in self.model_id:
                    tokenizer_id = "meta-llama/Llama-3-8B"
                elif "Llama-2" in self.model_id:
                    tokenizer_id = "meta-llama/Llama-2-7b-hf"
                elif "Mistral" in self.model_id:
                    tokenizer_id = "mistralai/Mistral-7B-v0.3"
                elif "Phi" in self.model_id:
                    tokenizer_id = "microsoft/phi-3-mini"
                elif "Qwen" in self.model_id:
                    tokenizer_id = "Qwen/Qwen1.5-7B"
                else:
                    # Generic fallback
                    tokenizer_id = "gpt2"
                    
                logger.info(f"Using fallback tokenizer: {tokenizer_id}")
                self.tokenizer = AutoTokenizer.from_pretrained(tokenizer_id)
            
            # Check if Vitis AI EP is available
            providers = ort.get_available_providers()
            logger.info(f"Available ONNX Runtime providers: {providers}")
            
            # Configure session options
            sess_options = ort.SessionOptions()
            sess_options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
            sess_options.execution_mode = ort.ExecutionMode.ORT_SEQUENTIAL
            
            # Priority: VitisAI (NPU) > ROCm (GPU) > CPU
            preferred_providers = []
            if 'VitisAIExecutionProvider' in providers:
                preferred_providers.append('VitisAIExecutionProvider')
                logger.info("Using Vitis AI (NPU) for inference")
            elif 'ROCmExecutionProvider' in providers:
                preferred_providers.append('ROCmExecutionProvider')
                logger.info("Using ROCm (GPU) for inference")
            preferred_providers.append('CPUExecutionProvider')
            
            # Create ONNX Runtime session
            logger.info(f"Creating ONNX Runtime session with providers: {preferred_providers}")
            self.session = ort.InferenceSession(
                str(self.model_path), 
                sess_options=sess_options, 
                providers=preferred_providers
            )
            
            # Get input and output names
            self.input_names = [input.name for input in self.session.get_inputs()]
            self.output_names = [output.name for output in self.session.get_outputs()]
            logger.info(f"Model inputs: {self.input_names}")
            logger.info(f"Model outputs: {self.output_names}")
            
            logger.info("Model loaded successfully")
        except Exception as e:
            logger.error(f"Error loading model: {str(e)}")
            raise
    
    def generate(self, 
                 prompt: str, 
                 max_new_tokens: int = 512, 
                 temperature: float = 0.7,
                 top_p: float = 0.9,
                 stream: bool = True) -> Union[str, TextIteratorStreamer]:
        """Generate text based on the prompt"""
        try:
            # Prepare input
            tokenized_input = self.tokenizer(prompt, return_tensors="np")
            input_ids = tokenized_input["input_ids"]
            attention_mask = tokenized_input["attention_mask"]
            
            # Create input feed dictionary
            input_feed = {
                "input_ids": input_ids,
                "attention_mask": attention_mask,
            }
            
            # Add optional parameters if the model supports them
            if "temperature" in self.input_names:
                input_feed["temperature"] = np.array([temperature], dtype=np.float32)
            if "top_p" in self.input_names:
                input_feed["top_p"] = np.array([top_p], dtype=np.float32)
            if "max_new_tokens" in self.input_names:
                input_feed["max_new_tokens"] = np.array([max_new_tokens], dtype=np.int32)
            
            if stream:
                # Set up a streamer for incremental output
                streamer = TextIteratorStreamer(self.tokenizer, skip_special_tokens=True)
                
                # Run generation in a separate thread
                def generate_in_thread():
                    result = self.session.run(self.output_names, input_feed)
                    output_ids = result[0]
                    streamer.put(output_ids)
                
                thread = Thread(target=generate_in_thread)
                thread.start()
                
                return streamer
            else:
                # Run the model
                logger.info("Running inference...")
                result = self.session.run(self.output_names, input_feed)
                
                # Process the output
                output_ids = result[0]
                decoded_output = self.tokenizer.decode(output_ids[0], skip_special_tokens=True)
                
                return decoded_output
        except Exception as e:
            logger.error(f"Error during generation: {str(e)}")
            raise

def main():
    parser = argparse.ArgumentParser(description="Run a Ryzen AI optimized model")
    parser.add_argument("--model", type=str, default="amd/Llama-3.2-3B-Instruct-awq-g128-int4-asym-bf16-onnx-ryzen-strix", 
                        help="Model ID from Hugging Face")
    parser.add_argument("--cache-dir", type=str, default=None, 
                        help="Directory to cache the downloaded models")
    parser.add_argument("--prompt", type=str, 
                        default="What are the key features of the KDE desktop environment?",
                        help="Prompt to send to the model")
    args = parser.parse_args()
    
    # Initialize and run the model
    try:
        model = RyzenAIModel(args.model, args.cache_dir)
        
        print(f"\nPrompt: {args.prompt}\n")
        print("Generating response...\n")
        
        # Stream the output
        streamer = model.generate(args.prompt, stream=True)
        
        print("\nResponse:")
        for text in streamer:
            print(text, end="", flush=True)
        print("\n")
        
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()