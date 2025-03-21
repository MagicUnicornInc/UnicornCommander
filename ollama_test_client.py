#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import asyncio
import aiohttp
import json
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("OllamaTest")

class OllamaClient:
    """Simple client for testing Ollama API"""
    
    def __init__(self, server_url="http://localhost:11434"):
        self.server_url = server_url
        self.session = None
        self.context = []
        
    async def _create_session(self):
        """Create an HTTP session if one doesn't exist"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
    
    async def close(self):
        """Close the HTTP session"""
        if self.session and not self.session.closed:
            await self.session.close()
            self.session = None
    
    async def get_models(self):
        """Get available models from Ollama"""
        try:
            await self._create_session()
            
            ollama_url = f"{self.server_url.rstrip('/')}/api/tags"
            logger.info(f"Getting models from {ollama_url}")
            
            async with self.session.get(ollama_url) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"Ollama Error: {response.status} - {error_text}")
                    return None
                
                data = await response.json()
                return data
                
        except Exception as e:
            logger.error(f"Error getting models: {str(e)}")
            return None
    
    async def send_message(self, message, model="llama3", stream=True):
        """Send a message to Ollama"""
        # Add user message to context
        self.context.append({"role": "user", "content": message})
        
        try:
            # Create session if needed
            await self._create_session()
            
            # Format messages in Ollama's expected format
            messages = []
            for msg in self.context:
                messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })
            
            # Use Ollama's API endpoint
            ollama_url = f"{self.server_url.rstrip('/')}/api/chat"
            
            # Build payload
            payload = {
                "model": model,
                "messages": messages,
                "stream": stream
            }
            
            logger.info(f"Sending request to Ollama at {ollama_url}")
            
            if stream:
                # Handle streaming response
                full_response = ""
                async with self.session.post(ollama_url, json=payload) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"Ollama Error: {response.status} - {error_text}")
                        return None
                    
                    # Process the streaming response
                    async for line in response.content:
                        if not line:
                            continue
                            
                        line_text = line.decode('utf-8').strip()
                        if not line_text:
                            continue
                            
                        try:
                            data = json.loads(line_text)
                            content = data.get("message", {}).get("content", "")
                            if content:
                                full_response += content
                                print(content, end='', flush=True)
                                
                            # Check if done
                            if data.get("done", False):
                                break
                                
                        except json.JSONDecodeError:
                            # Skip malformed JSON
                            continue
                
                # Add assistant response to context
                self.context.append({"role": "assistant", "content": full_response})
                print()  # Line break after complete response
                return full_response
            else:
                # Handle non-streaming response
                async with self.session.post(ollama_url, json=payload) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"Ollama Error: {response.status} - {error_text}")
                        return None
                    
                    data = await response.json()
                    response_text = data.get("message", {}).get("content", "")
                    
                    # Add assistant response to context
                    self.context.append({"role": "assistant", "content": response_text})
                    print(response_text)
                    return response_text
                    
        except Exception as e:
            logger.error(f"Error in send_message: {str(e)}", exc_info=True)
            return None

async def main():
    """Main function"""
    client = OllamaClient()
    
    try:
        # Get available models
        print("Getting available models...")
        models_data = await client.get_models()
        
        if models_data and "models" in models_data:
            print("Available models:")
            for model in models_data["models"]:
                print(f"- {model['name']}")
        else:
            print("Failed to get models")
            return
        
        # Interactive chat
        print("\nEnter your messages, type 'exit' to quit.\n")
        
        while True:
            user_input = input("> ")
            
            if user_input.lower() in ['exit', 'quit']:
                break
                
            if not user_input.strip():
                continue
                
            print("\nOllama: ", end='', flush=True)
            await client.send_message(user_input)
            print()
    
    finally:
        # Close the client session
        await client.close()

if __name__ == "__main__":
    asyncio.run(main())