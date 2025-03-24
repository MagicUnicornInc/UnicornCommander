import logging
import json
from typing import List, Dict, Optional, Any, Callable
from datetime import datetime
import uuid
import os
from pathlib import Path

from .indexer import DocumentIndexer
from .retriever import RAGRetriever

# Set up logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("MemoryManager")

class MemoryManager:
    """Manages both short-term and long-term memory for the AI assistant"""
    
    def __init__(self, embedding_function: Optional[Callable] = None):
        """Initialize the memory manager
        
        Args:
            embedding_function: Function to generate embeddings from text
        """
        # Set up short-term memory (current conversation)
        self.short_term_memory = []
        
        # Set up long-term memory (persistent across conversations)
        self.long_term_indexer = DocumentIndexer(collection_name="long_term_memory")
        self.long_term_retriever = RAGRetriever(self.long_term_indexer, embedding_function)
        
        # Set up conversation memory (recent conversations)
        self.conversation_indexer = DocumentIndexer(collection_name="conversation_memory")
        self.conversation_retriever = RAGRetriever(self.conversation_indexer, embedding_function)
        
        # Set up screen memory (context from screen captures)
        self.screen_indexer = DocumentIndexer(collection_name="screen_memory")
        self.screen_retriever = RAGRetriever(self.screen_indexer, embedding_function)
        
        # Embedding function
        self.embedding_function = embedding_function
        
        # Create storage path for conversations
        self.storage_path = Path.home() / ".local" / "share" / "kde-ai-interface" / "conversations"
        self.storage_path.mkdir(parents=True, exist_ok=True)
    
    def set_embedding_function(self, embedding_function: Callable):
        """Set the embedding function for all retrievers
        
        Args:
            embedding_function: Function to generate embeddings from text
        """
        self.embedding_function = embedding_function
        self.long_term_retriever.set_embedding_function(embedding_function)
        self.conversation_retriever.set_embedding_function(embedding_function)
        self.screen_retriever.set_embedding_function(embedding_function)
    
    def add_to_short_term_memory(self, role: str, content: str):
        """Add a message to short-term memory (current conversation)
        
        Args:
            role: Role of the message sender (user, assistant, system)
            content: Content of the message
        """
        self.short_term_memory.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
    
    def clear_short_term_memory(self):
        """Clear short-term memory (current conversation)"""
        self.short_term_memory = []
    
    def get_short_term_memory(self) -> List[Dict]:
        """Get short-term memory
        
        Returns:
            List of message dictionaries in the current conversation
        """
        return self.short_term_memory
    
    def add_to_long_term_memory(self, text: str, metadata: Optional[Dict] = None) -> bool:
        """Add text to long-term memory
        
        Args:
            text: Text to add to long-term memory
            metadata: Additional metadata for the memory
            
        Returns:
            bool: True if successful
        """
        if not self.embedding_function:
            logger.error("No embedding function set")
            return False
            
        # Set default metadata if not provided
        if not metadata:
            metadata = {
                "source": "user_input",
                "timestamp": datetime.now().isoformat()
            }
        else:
            # Ensure timestamp is included in metadata
            if "timestamp" not in metadata:
                metadata["timestamp"] = datetime.now().isoformat()
        
        # Add to long-term memory
        return self.long_term_retriever.update_memory(
            texts=[text],
            metadata=[metadata]
        )
    
    def add_conversation_to_memory(self, save_to_file: bool = True) -> bool:
        """Add the current conversation to memory
        
        Args:
            save_to_file: Whether to save the conversation to a file
            
        Returns:
            bool: True if successful
        """
        if not self.short_term_memory:
            return False
            
        # Generate a summary of the conversation
        summary = self._generate_conversation_summary()
        
        # Add the conversation summary to conversation memory
        conversation_id = str(uuid.uuid4())
        metadata = {
            "conversation_id": conversation_id,
            "timestamp": datetime.now().isoformat(),
            "message_count": len(self.short_term_memory)
        }
        
        # Add to conversation memory
        success = self.conversation_retriever.update_memory(
            texts=[summary],
            metadata=[metadata],
            ids=[conversation_id]
        )
        
        # Save conversation to file if requested
        if save_to_file:
            self._save_conversation_to_file(conversation_id)
            
        return success
    
    def add_screen_context(self, text: str, metadata: Optional[Dict] = None) -> bool:
        """Add screen context to memory
        
        Args:
            text: Text extracted from screen capture
            metadata: Additional metadata for the memory
            
        Returns:
            bool: True if successful
        """
        if not metadata:
            metadata = {
                "source": "screen_capture",
                "timestamp": datetime.now().isoformat()
            }
        
        # Add to screen memory
        return self.screen_retriever.update_memory(
            texts=[text],
            metadata=[metadata]
        )
    
    def retrieve_relevant_context(self, query: str, use_long_term: bool = True, 
                                 use_conversations: bool = True,
                                 use_screen: bool = True,
                                 max_length: int = 2000) -> str:
        """Retrieve relevant context for a query
        
        Args:
            query: The query text
            use_long_term: Whether to include long-term memory
            use_conversations: Whether to include conversation memory
            use_screen: Whether to include screen memory
            max_length: Maximum length of the context string
            
        Returns:
            str: Formatted context string
        """
        if not self.embedding_function:
            logger.error("No embedding function set")
            return ""
            
        combined_context = []
        remaining_length = max_length
        
        # Retrieve from long-term memory if requested
        if use_long_term:
            long_term_docs = self.long_term_retriever.retrieve(query, n_docs=3)
            if long_term_docs:
                long_term_context = "### LONG-TERM MEMORY ###\n"
                long_term_context += self.long_term_retriever.format_for_context(
                    long_term_docs, max_length=remaining_length-50)
                combined_context.append(long_term_context)
                remaining_length -= len(long_term_context)
        
        # Retrieve from conversation memory if requested
        if use_conversations and remaining_length > 100:
            conv_docs = self.conversation_retriever.retrieve(query, n_docs=2)
            if conv_docs:
                conv_context = "### PREVIOUS CONVERSATIONS ###\n"
                conv_context += self.conversation_retriever.format_for_context(
                    conv_docs, max_length=remaining_length-50)
                combined_context.append(conv_context)
                remaining_length -= len(conv_context)
        
        # Retrieve from screen memory if requested
        if use_screen and remaining_length > 100:
            screen_docs = self.screen_retriever.retrieve(query, n_docs=1)
            if screen_docs:
                screen_context = "### SCREEN CONTEXT ###\n"
                screen_context += self.screen_retriever.format_for_context(
                    screen_docs, max_length=remaining_length-50)
                combined_context.append(screen_context)
        
        # Return combined context
        if combined_context:
            return "\n\n".join(combined_context)
        else:
            return ""
    
    def _generate_conversation_summary(self) -> str:
        """Generate a summary of the current conversation
        
        Returns:
            str: Summary of the conversation
        """
        # For now, we'll just concatenate all messages
        # In a real implementation, you might want to use an LLM to generate a summary
        summary_parts = []
        for message in self.short_term_memory:
            role = message["role"]
            content = message["content"]
            summary_parts.append(f"{role}: {content[:100]}...")
        
        return "\n".join(summary_parts)
    
    def _save_conversation_to_file(self, conversation_id: str) -> bool:
        """Save the current conversation to a file
        
        Args:
            conversation_id: ID of the conversation
            
        Returns:
            bool: True if successful
        """
        try:
            # Create filename based on timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"conversation_{timestamp}_{conversation_id[:8]}.json"
            filepath = self.storage_path / filename
            
            # Save to file
            with open(filepath, 'w') as f:
                json.dump({
                    "conversation_id": conversation_id,
                    "timestamp": datetime.now().isoformat(),
                    "messages": self.short_term_memory
                }, f, indent=2)
                
            logger.info(f"Saved conversation to {filepath}")
            return True
        except Exception as e:
            logger.error(f"Failed to save conversation: {e}")
            return False
    
    def load_conversation_from_file(self, file_path: str) -> bool:
        """Load a conversation from a file
        
        Args:
            file_path: Path to the conversation file
            
        Returns:
            bool: True if successful
        """
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
                
            # Clear current short-term memory
            self.clear_short_term_memory()
            
            # Add messages from file
            self.short_term_memory = data.get("messages", [])
            
            logger.info(f"Loaded conversation from {file_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to load conversation: {e}")
            return False
    
    def get_recent_conversations(self, limit: int = 10) -> List[Dict]:
        """Get a list of recent conversations
        
        Args:
            limit: Maximum number of conversations to return
            
        Returns:
            List of conversation dictionaries
        """
        try:
            # Get list of conversation files
            conversation_files = list(self.storage_path.glob("conversation_*.json"))
            
            # Sort by modification time (most recent first)
            conversation_files.sort(key=os.path.getmtime, reverse=True)
            
            # Limit the number of files
            conversation_files = conversation_files[:limit]
            
            # Load conversation metadata
            conversations = []
            for file_path in conversation_files:
                try:
                    with open(file_path, 'r') as f:
                        data = json.load(f)
                        
                    # Extract summary information
                    summary = ""
                    if "messages" in data and data["messages"]:
                        first_msg = data["messages"][0]["content"]
                        summary = first_msg[:100] + "..." if len(first_msg) > 100 else first_msg
                        
                    conversations.append({
                        "id": data.get("conversation_id", ""),
                        "timestamp": data.get("timestamp", ""),
                        "filename": file_path.name,
                        "path": str(file_path),
                        "message_count": len(data.get("messages", [])),
                        "summary": summary
                    })
                except Exception as e:
                    logger.error(f"Failed to load conversation metadata from {file_path}: {e}")
            
            return conversations
        except Exception as e:
            logger.error(f"Failed to get recent conversations: {e}")
            return []