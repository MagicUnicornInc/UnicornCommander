#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import asyncio
try:
    # Try PyQt6 first (used in main app)
    from PyQt6.QtCore import QObject, pyqtSignal
except ImportError:
    # Fallback to PyQt5 if needed
    from PyQt5.QtCore import QObject, pyqtSignal


class StreamingHandler(QObject):
    """Handler for streaming responses from MCP servers"""
    
    # Signals
    chunk_received = pyqtSignal(str)
    response_complete = pyqtSignal(str)
    streaming_error = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.buffer = ""
        self.is_streaming = False
    
    def start_streaming(self):
        """Prepare for streaming response"""
        self.buffer = ""
        self.is_streaming = True
    
    def handle_chunk(self, chunk):
        """Handle a chunk of streaming data"""
        if not self.is_streaming:
            return
            
        # Add chunk to buffer
        self.buffer += chunk
        
        # Emit signal for chunk
        self.chunk_received.emit(chunk)
    
    def complete_streaming(self):
        """Complete streaming and return full response"""
        self.is_streaming = False
        full_response = self.buffer
        
        # Emit signal for complete response
        self.response_complete.emit(full_response)
        
        return full_response
    
    async def process_stream(self, stream):
        """Process an async stream of data"""
        self.start_streaming()
        
        try:
            async for chunk in stream:
                if isinstance(chunk, bytes):
                    chunk = chunk.decode('utf-8')
                    
                # Handle SSE format
                if chunk.startswith('data: '):
                    chunk = chunk[6:].strip()  # Remove 'data: ' prefix
                    
                    # Check for end marker
                    if chunk == '[DONE]':
                        break
                        
                    try:
                        data = json.loads(chunk)
                        content = self.extract_content(data)
                        if content:
                            self.handle_chunk(content)
                    except json.JSONDecodeError:
                        # Not valid JSON, treat as raw content
                        self.handle_chunk(chunk)
                else:
                    # Not in SSE format, treat as raw content
                    self.handle_chunk(chunk)
                    
        except Exception as e:
            self.streaming_error.emit(f"Streaming error: {str(e)}")
            
        return self.complete_streaming()
    
    def extract_content(self, data):
        """Extract content from parsed JSON chunk data"""
        # Handle different MCP server response formats
        
        # OpenAI-style format
        if "choices" in data and data["choices"]:
            choice = data["choices"][0]
            
            # Chat completion format
            if "delta" in choice:
                return choice["delta"].get("content", "")
                
            # Regular completion format
            elif "text" in choice:
                return choice["text"]
        
        # Anthropic-style format
        elif "content" in data:
            return data["content"]
            
        # Generic format fallback
        elif "text" in data:
            return data["text"]
            
        # Unknown format
        return ""