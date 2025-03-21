#!/usr/bin/env python3
import os
import sys
import logging
import argparse
from pathlib import Path
import time
import torch
from transformers import AutoTokenizer, TextIteratorStreamer
from optimum.amd import AMDONNXModel
from threading import Thread

# Set up logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("AMD-Ryzen-AI-Demo")

# Check if we have GPU/NPU support
logger.info(f"PyTorch version: {torch.__version__}")
logger.info(f"CUDA available: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    logger.info(f"CUDA device: {torch.cuda.get_device_name(0)}")

def load_model(model_path):
    """Load a model from the specified path"""
    try:
        # Load the model using AMD's optimum-amd
        logger.info(f"Loading model from {model_path}")
        
        # Find the parent model for tokenizer (strip the AMD customizations)
        model_id = Path(model_path).name
        if "Llama-3" in model_id:
            tokenizer_id = "meta-llama/Llama-3-8B"
        elif "Llama-2" in model_id:
            tokenizer_id = "meta-llama/Llama-2-7b-hf"
        elif "Mistral" in model_id:
            tokenizer_id = "mistralai/Mistral-7B-v0.3"
        elif "Phi" in model_id:
            tokenizer_id = "microsoft/phi-3-mini"
        elif "Qwen" in model_id:
            tokenizer_id = "Qwen/Qwen1.5-7B"
        else:
            # Generic fallback
            tokenizer_id = "gpt2"
            
        logger.info(f"Loading tokenizer from {tokenizer_id}")
        tokenizer = AutoTokenizer.from_pretrained(tokenizer_id)
        
        # Try to load model with AMD optimum
        try:
            logger.info("Attempting to load model with optimum-amd...")
            model = AMDONNXModel.from_pretrained(model_path)
            logger.info("Model loaded successfully with optimum-amd")
            return model, tokenizer
        except Exception as e:
            logger.error(f"Failed to load with optimum-amd: {str(e)}")
            logger.info("Falling back to simulate model for demo purposes")
            return None, tokenizer
            
    except Exception as e:
        logger.error(f"Error loading model: {str(e)}")
        raise

def generate_text(model, tokenizer, prompt, max_length=100, streaming=True):
    """Generate text using the model"""
    if model is None:
        # Simulate response if model couldn't be loaded with hardware acceleration
        logger.info("Using simulated response (model not loaded)")
        
        if streaming:
            for i in range(10):
                time.sleep(0.3)
                yield f"This is a simulated response chunk {i+1}. "
            yield "The AMD-optimized model couldn't be loaded with hardware acceleration. "
            yield "You need to install the full AMD Ryzen AI Software stack with NPU support."
        else:
            time.sleep(3)
            return "This is a simulated response. The AMD-optimized model couldn't be loaded with hardware acceleration. You need to install the full AMD Ryzen AI Software stack with NPU support."
    else:
        # Real model generation
        logger.info(f"Generating text for prompt: '{prompt}'")
        
        # Tokenize the prompt
        inputs = tokenizer(prompt, return_tensors="pt")
        
        # Generate
        if streaming:
            streamer = TextIteratorStreamer(tokenizer, skip_special_tokens=True)
            generation_kwargs = {
                "input_ids": inputs["input_ids"],
                "attention_mask": inputs["attention_mask"],
                "max_length": max_length,
                "streamer": streamer,
            }
            
            # Start generation in a separate thread
            thread = Thread(target=model.generate, kwargs=generation_kwargs)
            thread.start()
            
            # Yield from the streamer
            for text in streamer:
                yield text
        else:
            # Generate without streaming
            outputs = model.generate(
                **inputs,
                max_length=max_length,
            )
            
            # Decode the output
            generated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
            return generated_text[len(prompt):]

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="AMD Ryzen AI Demo")
    parser.add_argument("--model", type=str, default="amd-model",
                        help="Path to the model directory")
    parser.add_argument("--prompt", type=str, 
                        default="What are the key features of the KDE Plasma desktop environment?",
                        help="Prompt to generate text from")
    parser.add_argument("--max-length", type=int, default=200,
                        help="Maximum length of generated text")
    parser.add_argument("--no-stream", action="store_true",
                        help="Disable streaming generation")
    
    args = parser.parse_args()
    
    # Load the model
    model, tokenizer = load_model(args.model)
    
    # Generate text
    if args.no_stream:
        # Generate without streaming
        result = generate_text(model, tokenizer, args.prompt, args.max_length, 
                               streaming=False)
        print(f"\nPrompt: {args.prompt}")
        print(f"\nGenerated text: {result}")
    else:
        # Generate with streaming
        print(f"\nPrompt: {args.prompt}")
        print("\nGenerated text: ", end="", flush=True)
        
        for chunk in generate_text(model, tokenizer, args.prompt, args.max_length, 
                                  streaming=True):
            print(chunk, end="", flush=True)
        
        print("\n")

if __name__ == "__main__":
    main()