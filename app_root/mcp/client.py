#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import aiohttp
import asyncio
import logging
import sys

# Log debug information
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

try:
    # Try PyQt6 first (used in main app)
    from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot
    QT6 = True
except ImportError:
    # Fallback to PyQt5 if needed
    from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot
    QT6 = False


class MCPClient(QObject):
    """Client for interacting with MCP (Model Context Protocol) servers"""
    
    # Signals
    message_started = pyqtSignal()
    message_chunk = pyqtSignal(str)
    message_completed = pyqtSignal(str)
    message_error = pyqtSignal(str)
    
    def __init__(self, server_url=None, api_key=None, parent=None):
        super().__init__(parent)
        self.server_url = server_url
        self.api_key = api_key
        self.session = None
        self.context = []
        self.logger = logging.getLogger("MCPClient")
    
    def set_server(self, server_url, api_key=None):
        """Set the server URL and API key"""
        self.server_url = server_url
        self.api_key = api_key
    
    def set_context(self, context):
        """Set the conversation context"""
        self.context = context
    
    def clear_context(self):
        """Clear the conversation context"""
        self.context = []
    
    async def _create_session(self):
        """Create an HTTP session if one doesn't exist"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
            headers = {}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
            self.session.headers.update(headers)
    
    async def close(self):
        """Close the HTTP session"""
        if self.session and not self.session.closed:
            await self.session.close()
            self.session = None
    
    
    async def send_message(self, message, model_params=None, stream=True):
        # Add user message to context
        self.context.append({"role": "user", "content": message})
        
        # Prepare for streaming or non-streaming response
        self.message_started.emit()
        
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
            ollama_url = "http://localhost:11434/api/chat"
            if self.server_url and not self.server_url.isspace():
                # Custom Ollama server URL if provided
                base_url = self.server_url.rstrip('/')
                ollama_url = f"{base_url}/api/chat"
            
            # Build payload
            payload = {
                "model": model_params.get("model", "llama3"),  # Default to llama3 if not specified
                "messages": messages,
                "stream": stream
            }
            
            # Add any additional parameters from model_params
            if model_params:
                for key, value in model_params.items():
                    if key not in ["model"]:  # Skip already handled keys
                        payload[key] = value
            
            self.logger.info(f"Sending request to Ollama at {ollama_url}")
            
            if stream:
                # Handle streaming response
                full_response = ""
                async with self.session.post(ollama_url, json=payload) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        self.message_error.emit(f"Ollama Error: {response.status} - {error_text}")
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
                                self.message_chunk.emit(content)
                                
                            # Check if done
                            if data.get("done", False):
                                break
                                
                        except json.JSONDecodeError:
                            # Skip malformed JSON
                            continue
                
                # Add assistant response to context and emit completion signal
                self.context.append({"role": "assistant", "content": full_response})
                self.message_completed.emit(full_response)
                return full_response
            else:
                # Handle non-streaming response
                async with self.session.post(ollama_url, json=payload) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        self.message_error.emit(f"Ollama Error: {response.status} - {error_text}")
                        return None
                    
                    data = await response.json()
                    response_text = data.get("message", {}).get("content", "")
                    
                    # Add assistant response to context and emit completion signal
                    self.context.append({"role": "assistant", "content": response_text})
                    self.message_completed.emit(response_text)
                    return response_text
                    
        except aiohttp.ClientError as e:
            self.message_error.emit(f"Connection error: {str(e)}")
        except asyncio.TimeoutError:
            self.message_error.emit("Request timed out")
        except Exception as e:
            self.logger.error(f"Error in send_message: {str(e)}", exc_info=True)
            self.message_error.emit(f"Error: {str(e)}")
            
        return None

    def send_message_slot(self, message, model_params=None):
        """Qt slot for sending a message (creates an event loop if needed)"""
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            # No event loop exists in this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(self.send_message(message, model_params))


class MCPCoordinatorClient(QObject):
    """Client for interacting with the MCP Central Coordinator and its servers"""
    
    # Signals
    operation_started = pyqtSignal()
    operation_result = pyqtSignal(dict)
    operation_error = pyqtSignal(str)
    
    def __init__(self, coordinator_url=None, auth_token=None, parent=None):
        super().__init__(parent)
        self.coordinator_url = coordinator_url
        self.auth_token = auth_token
        self.session = None
        self.logger = logging.getLogger("MCPCoordinatorClient")
    
    def set_coordinator(self, coordinator_url, auth_token=None):
        """Set the coordinator URL and authentication token"""
        self.coordinator_url = coordinator_url
        self.auth_token = auth_token
    
    async def _create_session(self):
        """Create an HTTP session if one doesn't exist"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
            headers = {}
            if self.auth_token:
                headers["Authorization"] = f"Bearer {self.auth_token}"
            self.session.headers.update(headers)
    
    async def close(self):
        """Close the HTTP session"""
        if self.session and not self.session.closed:
            await self.session.close()
            self.session = None
    
    async def get_capabilities(self):
        """Get the capabilities of all MCP servers through the coordinator"""
        self.operation_started.emit()
        
        try:
            # Create session if needed
            await self._create_session()
            
            # Call the capabilities endpoint
            url = f"{self.coordinator_url}/api/capabilities"
            async with self.session.get(url) as response:
                if response.status != 200:
                    error_text = await response.text()
                    self.operation_error.emit(f"MCP Coordinator Error: {response.status} - {error_text}")
                    return None
                
                capabilities = await response.json()
                self.operation_result.emit(capabilities)
                return capabilities
                
        except aiohttp.ClientError as e:
            self.operation_error.emit(f"Connection error: {str(e)}")
        except asyncio.TimeoutError:
            self.operation_error.emit("Request timed out")
        except Exception as e:
            self.logger.error(f"Error in get_capabilities: {str(e)}", exc_info=True)
            self.operation_error.emit(f"Error: {str(e)}")
            
        return None
    
    async def execute_operation(self, server_id, endpoint, method="POST", data=None):
        """Execute an operation on a specific MCP server through the coordinator"""
        self.operation_started.emit()
        
        try:
            # Create session if needed
            await self._create_session()
            
            # Build the URL and request body
            url = f"{self.coordinator_url}/api/proxy/{server_id}{endpoint}"
            
            # Make the request
            kwargs = {"json": data} if data else {}
            async with self.session.request(method, url, **kwargs) as response:
                if response.status != 200:
                    error_text = await response.text()
                    self.operation_error.emit(f"MCP Server Error: {response.status} - {error_text}")
                    return None
                
                result = await response.json()
                self.operation_result.emit(result)
                return result
                
        except aiohttp.ClientError as e:
            self.operation_error.emit(f"Connection error: {str(e)}")
        except asyncio.TimeoutError:
            self.operation_error.emit("Request timed out")
        except Exception as e:
            self.logger.error(f"Error in execute_operation: {str(e)}", exc_info=True)
            self.operation_error.emit(f"Error: {str(e)}")
            
        return None
    
    # Convenience methods for specific MCP operations
    
    # KDE Desktop operations
    async def query_krunner(self, query):
        """Query KRunner for the given search term"""
        return await self.execute_operation("kde", "/api/krunner/query", "POST", {"query": query})
    
    async def list_directory(self, path):
        """List files and directories at the given path"""
        return await self.execute_operation("kde", "/api/fs/list", "POST", {"path": path})
    
    async def read_file(self, path):
        """Read the contents of a file"""
        return await self.execute_operation("kde", "/api/fs/read", "POST", {"path": path})
    
    async def send_notification(self, title, message):
        """Send a KDE notification"""
        return await self.execute_operation("kde", "/api/notifications/send", "POST", 
                                           {"title": title, "message": message})
    
    # Code Execution operations
    async def execute_code(self, code, language="python"):
        """Execute code in the specified language"""
        return await self.execute_operation("code", "/api/execute", "POST", 
                                           {"code": code, "language": language})
    
    # Data Processing operations
    async def analyze_data(self, data, analysis_type="summary"):
        """Analyze data with the specified analysis type"""
        return await self.execute_operation("data", "/api/analyze", "POST", 
                                           {"data": data, "type": analysis_type})
    
    # Network operations
    async def http_request(self, url, method="GET", headers=None, body=None):
        """Make an HTTP request to the specified URL"""
        return await self.execute_operation("network", "/api/http", "POST", 
                                           {"url": url, "method": method, 
                                            "headers": headers, "body": body})
    
    def execute_operation_slot(self, server_id, endpoint, method="POST", data=None):
        """Qt slot for executing an operation (creates an event loop if needed)"""
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            # No event loop exists in this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(self.execute_operation(server_id, endpoint, method, data))

    # Convenience slot methods
    def query_krunner_slot(self, query):
        """Qt slot for querying KRunner"""
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        return loop.run_until_complete(self.query_krunner(query))