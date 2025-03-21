#!/usr/bin/env python3
"""
Ollama Backend for KDE AI Interface

This module provides integration with Ollama servers to use local LLM models
as a backend for the KDE AI Interface.
"""

import os
import logging
import json
import time
import requests
from typing import Dict, List, Optional, Any, Generator
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("OllamaBackend")

class OllamaBackend:
    """Provides access to Ollama models as a backend for the KDE AI Interface"""
    
    def __init__(self, server_url: str = "http://localhost:11434", model: str = "llama2"):
        """Initialize the Ollama backend
        
        Args:
            server_url: Ollama server URL, default is http://localhost:11434
            model: Model to use, default is llama2
        """
        self.server_url = server_url
        self.model = model
        self.api_base = f"{server_url}/api"
    
    def is_available(self) -> bool:
        """Check if the Ollama server is available
        
        Returns:
            bool: True if server is running and responding
        """
        try:
            response = requests.get(f"{self.api_base}/tags")
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Error checking Ollama server availability: {e}")
            return False
    
    def get_available_models(self) -> List[str]:
        """Get list of available models
        
        Returns:
            List[str]: List of available model names
        """
        if not self.is_available():
            return []
            
        try:
            response = requests.get(f"{self.api_base}/tags")
            data = response.json()
            # Extract model names from the response
            return [model["name"] for model in data.get("models", [])]
        except Exception as e:
            logger.error(f"Error getting available models: {e}")
            return []
    
    def generate(self, prompt: str, 
               system_prompt: str = "You are a helpful assistant.",
               temperature: float = 0.7, 
               max_tokens: int = 1000,
               streaming: bool = False,
               conversation_history: Optional[List[Dict]] = None) -> str:
        """Generate text using the Ollama API
        
        Args:
            prompt: User's input text
            system_prompt: System prompt to use
            temperature: Model temperature (0.0 to 1.0)
            max_tokens: Maximum tokens to generate
            streaming: Whether to stream the response (not used in this method)
            conversation_history: List of previous messages in the conversation
            
        Returns:
            str: Generated text response
        """
        if not self.is_available():
            return "Error: Ollama server not available. Please check the server status."
        
        try:
            # Prepare request data
            messages = []
            
            # Add system message if present
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            
            # Add conversation history if provided
            if conversation_history:
                for message in conversation_history:
                    # Only include messages with 'role' and 'content'
                    if "role" in message and "content" in message:
                        messages.append(message)
            
            # Add current prompt
            messages.append({"role": "user", "content": prompt})
            
            # Prepare request payload
            data = {
                "model": self.model,
                "messages": messages,
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens
                },
                "stream": False
            }
            
            # Make the API call
            response = requests.post(f"{self.api_base}/chat", json=data)
            
            if response.status_code != 200:
                logger.error(f"Error from Ollama API: {response.status_code}, {response.text}")
                return f"Error from Ollama: {response.text}"
            
            # Parse response
            result = response.json()
            return result.get("message", {}).get("content", "")
            
        except Exception as e:
            logger.error(f"Error generating text: {e}")
            return f"Error generating text: {str(e)}"
    
    def stream(self, prompt: str, 
             system_prompt: str = "You are a helpful assistant.",
             temperature: float = 0.7,
             max_tokens: int = 1000,
             conversation_history: Optional[List[Dict]] = None) -> Generator[str, None, None]:
        """Stream text generation using the Ollama API
        
        Args:
            prompt: User's input text
            system_prompt: System prompt to use
            temperature: Model temperature (0.0 to 1.0)
            max_tokens: Maximum tokens to generate
            conversation_history: List of previous messages in the conversation
            
        Yields:
            str: Generated text chunks as they become available
        """
        if not self.is_available():
            yield "Error: Ollama server not available. Please check the server status."
            return
        
        try:
            # Prepare request data
            messages = []
            
            # Add system message if present
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            
            # Add conversation history if provided
            if conversation_history:
                for message in conversation_history:
                    # Only include messages with 'role' and 'content'
                    if "role" in message and "content" in message:
                        messages.append(message)
            
            # Add current prompt
            messages.append({"role": "user", "content": prompt})
            
            # Prepare request payload
            data = {
                "model": self.model,
                "messages": messages,
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens
                },
                "stream": True
            }
            
            # Make the API call with streaming
            response = requests.post(f"{self.api_base}/chat", json=data, stream=True)
            
            if response.status_code != 200:
                logger.error(f"Error from Ollama API: {response.status_code}, {response.text}")
                yield f"Error from Ollama: {response.text}"
                return
            
            # Process streaming response
            for line in response.iter_lines():
                if line:
                    try:
                        chunk = json.loads(line)
                        if "message" in chunk and "content" in chunk["message"]:
                            content = chunk["message"]["content"]
                            if content:
                                yield content
                    except json.JSONDecodeError:
                        logger.error(f"Error decoding JSON from stream: {line}")
                        continue
                        
        except Exception as e:
            logger.error(f"Error streaming text: {e}")
            logger.error(f"Exception details: {type(e).__name__}")
            yield f"Error streaming text: {str(e)}"

    def test_connection(self) -> bool:
        """Test the connection to the Ollama API
        
        Returns:
            bool: True if connection is successful
        """
        try:
            response = requests.get(f"{self.api_base}/tags", timeout=5)
            if response.status_code == 200:
                logger.info("Ollama API connection test successful")
                return True
            else:
                logger.error(f"Ollama API connection test failed: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"Ollama API connection test failed: {e}")
            return False

# Example usage
if __name__ == "__main__":
    # Test the Ollama backend
    backend = OllamaBackend()
    
    if backend.is_available():
        print("Ollama server is available")
        
        # Get available models
        models = backend.get_available_models()
        print(f"Available models: {models}")
        
        # Generate text
        response = backend.generate("Hello, how are you today?")
        print(f"Generated text: {response}")
        
        # Stream text
        print("\nStreaming response:")
        for chunk in backend.stream("Tell me a short joke"):
            print(chunk, end="", flush=True)
        print("\nDone streaming.")
    else:
        print("Ollama server is not available. Please check the server status.")