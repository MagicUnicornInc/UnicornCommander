import logging
import os
import json
from pathlib import Path
from typing import List, Dict, Optional, Any, Callable

# Import RAG components
from ..rag.memory_manager import MemoryManager
from ..rag.embeddings import EmbeddingsProvider

# Set up logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("MemoryIntegration")

class MemoryIntegration:
    """Integration of memory features into the KDE AI Interface"""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize memory integration
        
        Args:
            api_key: OpenAI API key for embeddings
        """
        # Initialize embeddings provider
        self.embeddings_provider = EmbeddingsProvider(
            provider="openai",  # Could be configurable in the future
            api_key=api_key,
            model="text-embedding-3-small"  # Most cost-effective OpenAI embedding model
        )
        
        # Check if embeddings are available
        if not self.embeddings_provider.is_available():
            logger.warning("Embeddings provider not available. Memory features will be limited.")
        
        # Initialize memory manager
        self.memory_manager = MemoryManager(
            embedding_function=self.embeddings_provider.get_embedding_function()
        )
        
        # Settings
        self.use_long_term_memory = True
        self.use_conversation_memory = True
        self.use_screen_memory = False  # Off by default until screen capture is implemented
    
    def set_api_key(self, api_key: str):
        """Set the API key for the embeddings provider
        
        Args:
            api_key: OpenAI API key
        """
        # Reinitialize embeddings provider with new API key
        self.embeddings_provider = EmbeddingsProvider(
            provider="openai",
            api_key=api_key,
            model="text-embedding-3-small"
        )
        
        # Update embedding function in memory manager
        self.memory_manager.set_embedding_function(
            self.embeddings_provider.get_embedding_function()
        )
    
    def add_message_to_memory(self, role: str, content: str):
        """Add a message to short-term memory
        
        Args:
            role: Role of the message sender (user, assistant, system)
            content: Content of the message
        """
        # Add to short-term memory
        self.memory_manager.add_to_short_term_memory(role, content)
        
        # For user messages, also add to long-term memory
        if role == "user" and self.use_long_term_memory:
            self.memory_manager.add_to_long_term_memory(
                text=content,
                metadata={
                    "source": "user_message",
                    "type": "question"
                }
            )
        
        # For assistant messages, selectively add important information
        # This is simplified; in a real system, you might use an LLM to determine importance
        if role == "assistant" and self.use_long_term_memory and len(content) > 200:
            self.memory_manager.add_to_long_term_memory(
                text=content,
                metadata={
                    "source": "assistant_message",
                    "type": "answer"
                }
            )
    
    def get_conversation_history(self) -> List[Dict]:
        """Get the current conversation history
        
        Returns:
            List of message dictionaries
        """
        return self.memory_manager.get_short_term_memory()
    
    def clear_conversation(self):
        """Clear the current conversation"""
        # Add current conversation to memory before clearing
        if self.use_conversation_memory:
            self.memory_manager.add_conversation_to_memory(save_to_file=True)
        
        # Clear short-term memory
        self.memory_manager.clear_short_term_memory()
    
    def enhance_prompt_with_memory(self, prompt: str) -> str:
        """Enhance a prompt with relevant memory context
        
        Args:
            prompt: Original user prompt
            
        Returns:
            Enhanced prompt with context
        """
        if not self.embeddings_provider.is_available():
            return prompt
            
        # Retrieve relevant context
        context = self.memory_manager.retrieve_relevant_context(
            query=prompt,
            use_long_term=self.use_long_term_memory,
            use_conversations=self.use_conversation_memory,
            use_screen=self.use_screen_memory
        )
        
        # If no context found, return original prompt
        if not context:
            return prompt
            
        # Combine context with prompt
        enhanced_prompt = (
            f"{context}\n\n"
            f"Please use the above context to inform your response to the following question:\n"
            f"{prompt}"
        )
        
        return enhanced_prompt
    
    def format_messages_for_api(self, system_prompt: str = "You are a helpful assistant.") -> List[Dict]:
        """Format messages for API calls
        
        Args:
            system_prompt: System prompt to use
            
        Returns:
            List of message dictionaries
        """
        messages = []
        
        # Add system prompt
        messages.append({"role": "system", "content": system_prompt})
        
        # Add conversation history
        for message in self.memory_manager.get_short_term_memory():
            messages.append({
                "role": message["role"],
                "content": message["content"]
            })
        
        return messages
    
    def save_current_conversation(self) -> bool:
        """Save the current conversation
        
        Returns:
            bool: True if successful
        """
        return self.memory_manager.add_conversation_to_memory(save_to_file=True)
    
    def load_conversation(self, file_path: str) -> bool:
        """Load a conversation from a file
        
        Args:
            file_path: Path to the conversation file
            
        Returns:
            bool: True if successful
        """
        return self.memory_manager.load_conversation_from_file(file_path)
    
    def get_recent_conversations(self, limit: int = 10) -> List[Dict]:
        """Get a list of recent conversations
        
        Args:
            limit: Maximum number of conversations to return
            
        Returns:
            List of conversation dictionaries
        """
        return self.memory_manager.get_recent_conversations(limit)
    
    def add_screen_context(self, text: str) -> bool:
        """Add screen context to memory
        
        Args:
            text: Text extracted from screen capture
            
        Returns:
            bool: True if successful
        """
        return self.memory_manager.add_screen_context(text)
    
    def toggle_long_term_memory(self, enabled: bool):
        """Toggle long-term memory
        
        Args:
            enabled: Whether long-term memory should be enabled
        """
        self.use_long_term_memory = enabled
    
    def toggle_conversation_memory(self, enabled: bool):
        """Toggle conversation memory
        
        Args:
            enabled: Whether conversation memory should be enabled
        """
        self.use_conversation_memory = enabled
    
    def toggle_screen_memory(self, enabled: bool):
        """Toggle screen memory
        
        Args:
            enabled: Whether screen memory should be enabled
        """
        self.use_screen_memory = enabled
    
    def get_memory_status(self) -> Dict[str, Any]:
        """Get status information about the memory system
        
        Returns:
            Dict containing memory status information
        """
        # Get collection info for each memory type
        long_term_info = self.memory_manager.long_term_indexer.get_collection_info()
        conversation_info = self.memory_manager.conversation_indexer.get_collection_info()
        screen_info = self.memory_manager.screen_indexer.get_collection_info()
        
        # Format status info
        return {
            "long_term_enabled": self.use_long_term_memory,
            "conversation_enabled": self.use_conversation_memory,
            "screen_enabled": self.use_screen_memory,
            "long_term_count": long_term_info.get("vectors_count", 0) if "vectors_count" in long_term_info else long_term_info.get("count", 0),
            "conversation_count": conversation_info.get("vectors_count", 0) if "vectors_count" in conversation_info else conversation_info.get("count", 0),
            "screen_count": screen_info.get("vectors_count", 0) if "vectors_count" in screen_info else screen_info.get("count", 0),
            "embeddings_available": self.embeddings_provider.is_available(),
            "current_conversation_length": len(self.memory_manager.get_short_term_memory())
        }