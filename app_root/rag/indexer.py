from typing import List, Dict, Optional, Any, Union
import logging
import os
from pathlib import Path
import numpy as np

# Try importing Qdrant client
try:
    from qdrant_client import QdrantClient
    from qdrant_client.http import models
    QDRANT_AVAILABLE = True
except ImportError:
    QDRANT_AVAILABLE = False
    print("Qdrant client not installed. Run: pip install qdrant_client")

# Fallback to Chroma if Qdrant is not available
try:
    import chromadb
    CHROMA_AVAILABLE = True
except ImportError:
    CHROMA_AVAILABLE = False
    print("ChromaDB not installed. Run: pip install chromadb")

# Set up logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("DocumentIndexer")

class DocumentIndexer:
    """Vector store indexer that supports both Qdrant and ChromaDB backends"""
    
    def __init__(self, collection_name: str = "kde_memory", 
                 vector_size: int = 1536,
                 qdrant_url: Optional[str] = None,
                 qdrant_api_key: Optional[str] = None,
                 use_qdrant: bool = True):
        """Initialize the document indexer
        
        Args:
            collection_name: Name of the collection
            vector_size: Dimension of embedding vectors
            qdrant_url: URL for Qdrant server (None for local)
            qdrant_api_key: API key for Qdrant cloud (if applicable)
            use_qdrant: Whether to prefer Qdrant over Chroma
        """
        self.collection_name = collection_name
        self.vector_size = vector_size
        self.use_qdrant = use_qdrant and QDRANT_AVAILABLE
        
        # Initialize the vector store
        if self.use_qdrant:
            logger.info(f"Using Qdrant for vector indexing with collection: {collection_name}")
            try:
                # Create Qdrant client
                if qdrant_url:
                    # Use remote Qdrant server
                    self.client = QdrantClient(
                        url=qdrant_url,
                        api_key=qdrant_api_key
                    )
                else:
                    # Use local Qdrant
                    data_path = Path.home() / ".local" / "share" / "kde-ai-interface" / "qdrant_data"
                    data_path.mkdir(parents=True, exist_ok=True)
                    self.client = QdrantClient(path=str(data_path))
                
                # Check if collection exists, create if not
                collections = self.client.get_collections().collections
                collection_names = [c.name for c in collections]
                
                if collection_name not in collection_names:
                    self.client.create_collection(
                        collection_name=collection_name,
                        vectors_config=models.VectorParams(
                            size=vector_size,
                            distance=models.Distance.COSINE
                        )
                    )
                logger.info(f"Qdrant collection '{collection_name}' is ready")
            except Exception as e:
                logger.error(f"Failed to initialize Qdrant: {e}")
                self.use_qdrant = False
        
        # Fall back to ChromaDB if Qdrant is not available or initialization failed
        if not self.use_qdrant:
            if CHROMA_AVAILABLE:
                logger.info(f"Using ChromaDB for vector indexing with collection: {collection_name}")
                try:
                    # Create ChromaDB client
                    data_path = Path.home() / ".local" / "share" / "kde-ai-interface" / "chroma_data"
                    data_path.mkdir(parents=True, exist_ok=True)
                    self.client = chromadb.PersistentClient(path=str(data_path))
                    self.collection = self.client.get_or_create_collection(collection_name)
                    logger.info(f"ChromaDB collection '{collection_name}' is ready")
                except Exception as e:
                    logger.error(f"Failed to initialize ChromaDB: {e}")
                    self.client = None
                    self.collection = None
            else:
                logger.error("Neither Qdrant nor ChromaDB is available")
                self.client = None
                self.collection = None
        
    def add_documents(self, texts: List[str], 
                      embeddings: Optional[List[List[float]]] = None,
                      metadata: Optional[List[Dict[str, Any]]] = None,
                      ids: Optional[List[str]] = None) -> bool:
        """Add documents to the vector store
        
        Args:
            texts: List of text documents
            embeddings: List of embedding vectors (optional)
            metadata: List of metadata dictionaries (optional)
            ids: List of IDs for the documents (optional)
            
        Returns:
            bool: True if successful
        """
        if not texts:
            logger.warning("No texts provided to add_documents")
            return False
            
        # Generate IDs if not provided
        if not ids:
            import uuid
            ids = [str(uuid.uuid4()) for _ in range(len(texts))]
        
        # Ensure metadata exists
        if not metadata:
            metadata = [{"source": "user_memory"} for _ in range(len(texts))]
        
        try:
            # Add documents using the appropriate client
            if self.use_qdrant:
                # Convert to Qdrant format
                if embeddings:
                    # Add points with provided embeddings
                    points = [
                        models.PointStruct(
                            id=point_id,
                            payload={"text": text, **(meta or {})},
                            vector=embedding
                        )
                        for point_id, text, meta, embedding in zip(ids, texts, metadata, embeddings)
                    ]
                    self.client.upload_points(
                        collection_name=self.collection_name,
                        points=points
                    )
                else:
                    logger.error("Embeddings must be provided when using Qdrant directly")
                    return False
            else:
                # Use ChromaDB
                if self.collection:
                    if embeddings:
                        self.collection.add(
                            documents=texts,
                            embeddings=embeddings,
                            metadatas=metadata,
                            ids=ids
                        )
                    else:
                        self.collection.add(
                            documents=texts,
                            metadatas=metadata,
                            ids=ids
                        )
                else:
                    logger.error("No collection available")
                    return False
                    
            return True
        except Exception as e:
            logger.error(f"Failed to add documents: {e}")
            return False
    
    def query(self, query_embedding: List[float], n_results: int = 5) -> dict:
        """Query the vector store with an embedding
        
        Args:
            query_embedding: The embedding vector of the query
            n_results: Number of results to return
            
        Returns:
            dict: Results containing documents, metadata, and distances
        """
        try:
            if self.use_qdrant:
                # Query using Qdrant
                search_result = self.client.search(
                    collection_name=self.collection_name,
                    query_vector=query_embedding,
                    limit=n_results
                )
                
                # Format results similar to ChromaDB
                documents = [point.payload.get("text") for point in search_result]
                metadatas = [{k: v for k, v in point.payload.items() if k != "text"} for point in search_result]
                distances = [point.score for point in search_result]
                ids = [point.id for point in search_result]
                
                return {
                    "documents": [documents],
                    "metadatas": [metadatas],
                    "distances": [distances],
                    "ids": [ids]
                }
            else:
                # Query using ChromaDB
                if self.collection:
                    results = self.collection.query(
                        query_embeddings=[query_embedding],
                        n_results=n_results
                    )
                    return results
                else:
                    logger.error("No collection available")
                    return {"documents": [], "metadatas": [], "distances": [], "ids": []}
        except Exception as e:
            logger.error(f"Query failed: {e}")
            return {"documents": [], "metadatas": [], "distances": [], "ids": []}
    
    def query_by_text(self, query_text: str, embedding_function: callable, n_results: int = 5) -> dict:
        """Query the vector store using a text query
        
        Args:
            query_text: The text query
            embedding_function: Function to convert text to embedding
            n_results: Number of results to return
            
        Returns:
            dict: Results containing documents, metadata, and distances
        """
        # Get embedding for the query text
        query_embedding = embedding_function([query_text])[0]
        
        # Use the embedding to query
        return self.query(query_embedding, n_results)
    
    def delete(self, ids: List[str]) -> bool:
        """Delete documents by ID
        
        Args:
            ids: List of document IDs to delete
            
        Returns:
            bool: True if successful
        """
        try:
            if self.use_qdrant:
                # Delete from Qdrant
                self.client.delete(
                    collection_name=self.collection_name,
                    points_selector=models.PointIdsList(
                        points=ids
                    )
                )
            else:
                # Delete from ChromaDB
                if self.collection:
                    self.collection.delete(ids=ids)
                else:
                    logger.error("No collection available")
                    return False
            return True
        except Exception as e:
            logger.error(f"Failed to delete documents: {e}")
            return False
    
    def get_collection_info(self) -> Dict[str, Any]:
        """Get information about the collection
        
        Returns:
            dict: Collection information
        """
        try:
            if self.use_qdrant:
                # Get Qdrant collection info
                info = self.client.get_collection(self.collection_name)
                return {
                    "name": info.name,
                    "vectors_count": info.vectors_count,
                    "status": "ready" if info.status == models.CollectionStatus.GREEN else "not_ready",
                    "vector_size": info.config.params.size
                }
            else:
                # Get ChromaDB collection info
                if self.collection:
                    return {
                        "name": self.collection.name,
                        "count": self.collection.count()
                    }
                else:
                    logger.error("No collection available")
                    return {}
        except Exception as e:
            logger.error(f"Failed to get collection info: {e}")
            return {}