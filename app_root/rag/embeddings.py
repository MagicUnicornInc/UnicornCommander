import logging
import numpy as np
from typing import List, Dict, Optional, Any, Callable, Union
import requests
import os
import time
from pathlib import Path
import json

# Set up logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("EmbeddingsProvider")

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logger.warning("OpenAI SDK not installed. OpenAI embeddings will not be available.")

class EmbeddingsProvider:
    """Provides embeddings for text using various embedding models"""
    
    def __init__(self, provider: str = "openai", api_key: Optional[str] = None, model: Optional[str] = None):
        """Initialize the embeddings provider
        
        Args:
            provider: Provider for embeddings (openai, local, etc.)
            api_key: API key for the provider
            model: Model to use for embeddings
        """
        self.provider = provider.lower()
        self.api_key = api_key
        
        # Set the embedding model based on provider
        if self.provider == "openai":
            self.model = model or "text-embedding-3-small"
            
            # Get API key if not provided
            if not self.api_key:
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
            
            # Initialize OpenAI client if API key is available
            if self.api_key and OPENAI_AVAILABLE:
                self.client = OpenAI(
                    api_key=self.api_key,
                    base_url="https://api.openai.com/v1"
                )
                logger.info(f"Using OpenAI for embeddings with model: {self.model}")
            else:
                self.client = None
                missing = []
                if not self.api_key:
                    missing.append("API key")
                if not OPENAI_AVAILABLE:
                    missing.append("OpenAI SDK")
                logger.warning(f"OpenAI embeddings not fully initialized. Missing: {', '.join(missing)}")
                
        elif self.provider == "local":
            # For local embedding models
            self.model = model or "all-MiniLM-L6-v2"
            try:
                from sentence_transformers import SentenceTransformer
                self.client = SentenceTransformer(self.model)
                logger.info(f"Using local SentenceTransformer for embeddings with model: {self.model}")
            except ImportError:
                logger.warning("SentenceTransformers not installed. Run: pip install sentence-transformers")
                self.client = None
                
        else:
            logger.error(f"Unsupported embeddings provider: {provider}")
            self.model = None
            self.client = None
    
    def is_available(self) -> bool:
        """Check if the embeddings provider is available
        
        Returns:
            bool: True if available
        """
        return self.client is not None
    
    def get_embeddings(self, texts: List[str], batch_size: int = 8) -> Optional[List[List[float]]]:
        """Get embeddings for a list of texts
        
        Args:
            texts: List of texts to embed
            batch_size: Number of texts to process at once
            
        Returns:
            List of embedding vectors, or None if failed
        """
        if not self.is_available():
            logger.error("Embeddings provider not available")
            return None
            
        if not texts:
            logger.warning("No texts provided for embedding")
            return []
            
        try:
            if self.provider == "openai":
                return self._get_openai_embeddings(texts, batch_size)
            elif self.provider == "local":
                return self._get_local_embeddings(texts, batch_size)
            else:
                logger.error(f"Unsupported embeddings provider: {self.provider}")
                return None
        except Exception as e:
            logger.error(f"Failed to get embeddings: {e}")
            return None
    
    def _get_openai_embeddings(self, texts: List[str], batch_size: int = 8) -> List[List[float]]:
        """Get embeddings using OpenAI API
        
        Args:
            texts: List of texts to embed
            batch_size: Number of texts to process at once
            
        Returns:
            List of embedding vectors
        """
        all_embeddings = []
        
        # Process in batches to avoid rate limits
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i+batch_size]
            
            try:
                # Call OpenAI API
                response = self.client.embeddings.create(
                    model=self.model,
                    input=batch
                )
                
                # Extract embeddings
                batch_embeddings = [item.embedding for item in response.data]
                all_embeddings.extend(batch_embeddings)
                
                # Sleep to avoid rate limits if we have more batches
                if i + batch_size < len(texts):
                    time.sleep(0.5)
                    
            except Exception as e:
                logger.error(f"Error getting OpenAI embeddings for batch {i//batch_size+1}: {e}")
                # Return empty embeddings for failed texts
                empty_embeddings = [[0.0] * 1536] * len(batch)  # default to 1536-dim for OpenAI embeddings
                all_embeddings.extend(empty_embeddings)
        
        return all_embeddings
    
    def _get_local_embeddings(self, texts: List[str], batch_size: int = 32) -> List[List[float]]:
        """Get embeddings using local SentenceTransformer model
        
        Args:
            texts: List of texts to embed
            batch_size: Number of texts to process at once
            
        Returns:
            List of embedding vectors
        """
        # Encode all texts at once (SentenceTransformer handles batching internally)
        embeddings = self.client.encode(texts, batch_size=batch_size, show_progress_bar=False)
        
        # Convert NumPy arrays to lists
        return embeddings.tolist()
    
    def get_embedding_function(self) -> Callable:
        """Get a function that can be used to get embeddings for texts
        
        Returns:
            Callable: Function that takes a list of texts and returns embeddings
        """
        return self.get_embeddings