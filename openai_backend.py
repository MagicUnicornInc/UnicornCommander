#!/usr/bin/env python3
"""
OpenAI Backend for KDE AI Interface

This module provides integration with OpenAI API to use models like GPT-4o-mini 
as a backend for the KDE AI Interface.
"""

import os
import logging
import json
import time
import asyncio
from typing import Dict, List, Optional, Any, Generator
from pathlib import Path

try:
    from openai import OpenAI, AsyncOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    print("OpenAI SDK not installed. Run: pip install openai")

# Set up logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("OpenAIBackend")

class OpenAIBackend:
    """Provides access to OpenAI models as a backend for the KDE AI Interface"""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o-mini"):
        """Initialize the OpenAI backend
        
        Args:
            api_key: OpenAI API key. If None, will try to get from environment variable
            model: Model to use, default is gpt-4o-mini
        """
        self.model = model
        
        # API Key handling - prefer explicit key, then environment, then config file
        self.api_key = api_key
        
        if not self.api_key:
            # Try to get from environment variable
            self.api_key = os.environ.get("OPENAI_API_KEY")
            
        if not self.api_key:
            # Try to load from config file
            config_path = Path.home() / ".config" / "kde-ai-interface" / "openai_config.json"
            if config_path.exists():
                try:
                    with open(config_path, 'r') as f:
                        config = json.load(f)
                        self.api_key = config.get("api_key")
                except Exception as e:
                    logger.error(f"Error loading config file: {e}")
        
        # Initialize client if API key is available
        if self.api_key and OPENAI_AVAILABLE:
            self.client = OpenAI(
                api_key=self.api_key,
                base_url="https://api.openai.com/v1"  # Explicitly set API base URL
            )
            self.async_client = AsyncOpenAI(
                api_key=self.api_key,
                base_url="https://api.openai.com/v1"  # Explicitly set API base URL
            )
            logger.info(f"OpenAI backend initialized with model: {self.model}")
        else:
            self.client = None
            self.async_client = None
            missing = []
            if not self.api_key:
                missing.append("API key")
            if not OPENAI_AVAILABLE:
                missing.append("OpenAI SDK")
            logger.warning(f"OpenAI backend not fully initialized. Missing: {', '.join(missing)}")
    
    def save_api_key(self, api_key: str):
        """Save API key to config file
        
        Args:
            api_key: OpenAI API key to save
        """
        # Create config directory if it doesn't exist
        config_dir = Path.home() / ".config" / "kde-ai-interface"
        config_dir.mkdir(parents=True, exist_ok=True)
        
        # Save API key to config file (securely)
        config_path = config_dir / "openai_config.json"
        try:
            # Check if file exists and load existing config
            if config_path.exists():
                with open(config_path, 'r') as f:
                    config = json.load(f)
            else:
                config = {}
                
            config["api_key"] = api_key
                
            with open(config_path, 'w') as f:
                json.dump(config, f)
                
            # Update current instance
            self.api_key = api_key
            if OPENAI_AVAILABLE:
                self.client = OpenAI(
                    api_key=self.api_key,
                    base_url="https://api.openai.com/v1"  # Explicitly set API base URL
                )
                self.async_client = AsyncOpenAI(
                    api_key=self.api_key,
                    base_url="https://api.openai.com/v1"  # Explicitly set API base URL
                )
                
            logger.info("API key saved to config file")
            return True
        except Exception as e:
            logger.error(f"Error saving API key: {e}")
            return False
    
    def is_available(self) -> bool:
        """Check if the OpenAI backend is available
        
        Returns:
            bool: True if OpenAI SDK is available and API key is set
        """
        return OPENAI_AVAILABLE and self.api_key is not None and self.client is not None
    
    def get_available_models(self) -> List[str]:
        """Get list of available models
        
        Returns:
            List[str]: List of available model IDs
        """
        if not self.is_available():
            return []
            
        try:
            response = self.client.models.list()
            return [model.id for model in response.data]
        except Exception as e:
            logger.error(f"Error getting available models: {e}")
            return []
    
    def generate(self, prompt: str, 
               system_prompt: str = "You are a helpful assistant.",
               temperature: float = 0.7, 
               max_tokens: int = 1000,
               streaming: bool = False,
               conversation_history: Optional[List[Dict]] = None) -> str:
        """Generate text using the OpenAI API
        
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
            return "Error: OpenAI backend not available. Please check API key and SDK installation."
        
        try:
            # Prepare messages
            messages = []
            
            # Add system prompt
            messages.append({"role": "system", "content": system_prompt})
            
            # Add conversation history if provided
            if conversation_history:
                for message in conversation_history:
                    messages.append(message)
            
            # Add current prompt
            messages.append({"role": "user", "content": prompt})
            
            # Make the API call
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            # Extract and return the text
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Error generating text: {e}")
            return f"Error generating text: {str(e)}"
    
    def stream(self, prompt: str, 
             system_prompt: str = "You are a helpful assistant.",
             temperature: float = 0.7,
             max_tokens: int = 1000,
             conversation_history: Optional[List[Dict]] = None) -> Generator[str, None, None]:
        """Stream text generation using the OpenAI API
        
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
            yield "Error: OpenAI backend not available. Please check API key and SDK installation."
            return
        
        try:
            # Prepare messages
            messages = []
            
            # Add system prompt
            messages.append({"role": "system", "content": system_prompt})
            
            # Add conversation history if provided
            if conversation_history:
                for message in conversation_history:
                    messages.append(message)
            
            # Add current prompt
            messages.append({"role": "user", "content": prompt})
            
            # Make the streaming API call
            stream = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True
            )
            
            # Process the streaming response
            for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    yield chunk.choices[0].delta.content
                    
        except Exception as e:
            logger.error(f"Error streaming text: {e}")
            logger.error(f"Exception details: {type(e).__name__}")
            # Try to get more details if it's an API error
            try:
                if hasattr(e, 'status_code'):
                    logger.error(f"Status code: {e.status_code}")
                if hasattr(e, 'response'):
                    logger.error(f"Response: {e.response}")
            except:
                pass
            yield f"Error streaming text: {str(e)}"

    async def generate_async(self, prompt: str,
                           system_prompt: str = "You are a helpful assistant.",
                           temperature: float = 0.7,
                           max_tokens: int = 1000,
                           conversation_history: Optional[List[Dict]] = None) -> str:
        """Generate text asynchronously using the OpenAI API
        
        Args:
            prompt: User's input text
            system_prompt: System prompt to use
            temperature: Model temperature (0.0 to 1.0)
            max_tokens: Maximum tokens to generate
            conversation_history: List of previous messages in the conversation
            
        Returns:
            str: Generated text response
        """
        if not self.is_available():
            return "Error: OpenAI backend not available. Please check API key and SDK installation."
        
        try:
            # Prepare messages
            messages = []
            
            # Add system prompt
            messages.append({"role": "system", "content": system_prompt})
            
            # Add conversation history if provided
            if conversation_history:
                for message in conversation_history:
                    messages.append(message)
            
            # Add current prompt
            messages.append({"role": "user", "content": prompt})
            
            # Make the API call
            response = await self.async_client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            # Extract and return the text
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Error generating text asynchronously: {e}")
            return f"Error generating text: {str(e)}"

    def test_connection(self) -> bool:
        """Test the connection to the OpenAI API
        
        Returns:
            bool: True if connection is successful
        """
        if not self.is_available():
            logger.error("Cannot test connection: OpenAI backend not available")
            return False
            
        try:
            # Try to list models as a simple API test
            self.client.models.list()
            logger.info("OpenAI API connection test successful")
            return True
        except Exception as e:
            logger.error(f"OpenAI API connection test failed: {e}")
            # Get detailed error information
            logger.error(f"Exception type: {type(e).__name__}")
            try:
                if hasattr(e, 'status_code'):
                    logger.error(f"Status code: {e.status_code}")
                if hasattr(e, 'response'):
                    logger.error(f"Response: {e.response}")
            except:
                pass
            return False

# Example usage
if __name__ == "__main__":
    # Test the OpenAI backend
    backend = OpenAIBackend()
    
    if backend.is_available():
        print("OpenAI backend is available")
        
        # Test connection
        if backend.test_connection():
            print("Connection to OpenAI API successful")
            
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
            print("Failed to connect to OpenAI API. Check your API key and internet connection.")
    else:
        print("OpenAI backend is not available. Please check API key and SDK installation.")