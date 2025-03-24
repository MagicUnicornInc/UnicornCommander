import logging
from typing import List, Dict, Optional, Any, Callable
from .indexer import DocumentIndexer

# Set up logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("RAGRetriever")

class RAGRetriever:
    """Retrieval-Augmented Generation (RAG) system for enhancing LLM responses with context"""
    
    def __init__(self, indexer: DocumentIndexer, embedding_function: Optional[Callable] = None):
        """Initialize the RAG Retriever
        
        Args:
            indexer: Document indexer instance
            embedding_function: Function to generate embeddings from text
        """
        self.indexer = indexer
        self.embedding_function = embedding_function
        
    def set_embedding_function(self, embedding_function: Callable):
        """Set the embedding function
        
        Args:
            embedding_function: Function to generate embeddings from text
        """
        self.embedding_function = embedding_function
        
    def retrieve(self, query: str, n_docs: int = 3) -> List[Dict]:
        """Retrieve relevant documents for a query
        
        Args:
            query: The query text
            n_docs: Number of documents to retrieve
            
        Returns:
            List of dictionaries containing text and relevance score
        """
        try:
            if not self.embedding_function:
                logger.error("No embedding function set")
                return []
                
            # Generate embedding for the query
            query_embedding = self.embedding_function([query])[0]
            
            # Query the vector store
            results = self.indexer.query(query_embedding, n_results=n_docs)
            
            # Process results
            if results and "documents" in results and results["documents"]:
                documents = results["documents"][0]
                distances = results["distances"][0] if "distances" in results else [0.0] * len(documents)
                
                # Convert to list of dictionaries
                return [
                    {"text": doc, "score": score}
                    for doc, score in zip(documents, distances)
                ]
            return []
        except Exception as e:
            logger.error(f"Retrieval failed: {e}")
            return []
            
    def update_memory(self, 
                     texts: List[str], 
                     metadata: Optional[List[Dict]] = None,
                     ids: Optional[List[str]] = None) -> bool:
        """Add new documents to the memory store
        
        Args:
            texts: List of text documents to add
            metadata: List of metadata dictionaries (optional)
            ids: List of document IDs (optional)
            
        Returns:
            bool: True if successful
        """
        try:
            if not self.embedding_function:
                logger.error("No embedding function set")
                return False
                
            # Generate embeddings for the texts
            embeddings = self.embedding_function(texts)
            
            # Add to the vector store
            return self.indexer.add_documents(
                texts=texts,
                embeddings=embeddings,
                metadata=metadata,
                ids=ids
            )
        except Exception as e:
            logger.error(f"Failed to update memory: {e}")
            return False
            
    def format_for_context(self, retrieved_docs: List[Dict], max_length: int = 2000) -> str:
        """Format retrieved documents as context for the LLM
        
        Args:
            retrieved_docs: Documents retrieved from the vector store
            max_length: Maximum length of the context string
            
        Returns:
            str: Formatted context string
        """
        if not retrieved_docs:
            return ""
            
        # Format each document with its score
        context_parts = []
        current_length = 0
        
        for i, doc in enumerate(retrieved_docs):
            doc_text = doc["text"]
            doc_score = doc.get("score", 0.0)
            
            # Format document with relevance score
            formatted_doc = f"[Context {i+1} (Relevance: {doc_score:.2f})]\n{doc_text}\n"
            
            # Add to context if we have space
            if current_length + len(formatted_doc) <= max_length:
                context_parts.append(formatted_doc)
                current_length += len(formatted_doc)
            else:
                # Truncate the document to fit
                remaining_space = max_length - current_length
                if remaining_space > 50:  # Only add if we have reasonable space
                    truncated_doc = f"[Context {i+1} (Relevance: {doc_score:.2f})]\n{doc_text[:remaining_space-30]}...\n"
                    context_parts.append(truncated_doc)
                break
                
        # Join all context parts
        return "\n".join(context_parts)
        
    def get_memory_info(self) -> Dict[str, Any]:
        """Get information about the memory store
        
        Returns:
            dict: Memory store information
        """
        return self.indexer.get_collection_info()
        
    def clear_specific_memories(self, ids: List[str]) -> bool:
        """Delete specific memories by ID
        
        Args:
            ids: List of memory IDs to delete
            
        Returns:
            bool: True if successful
        """
        return self.indexer.delete(ids)