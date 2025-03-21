from typing import List, Dict, Optional
import chromadb
import logging

class DocumentIndexer:
    def __init__(self, collection_name: str = "kde_docs"):
        self.client = chromadb.Client()
        self.collection = self.client.get_or_create_collection(collection_name)
        
    def add_documents(self, texts: List[str], metadata: Optional[List[Dict]] = None):
        """Add documents to the vector store"""
        try:
            self.collection.add(
                documents=texts,
                metadatas=metadata if metadata else [{}] * len(texts),
                ids=[f"doc_{i}" for i in range(len(texts))]
            )
            return True
        except Exception as e:
            logging.error(f"Failed to add documents: {e}")
            return False
            
    def query(self, query: str, n_results: int = 5):
        """Query the vector store"""
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results
            )
            return results
        except Exception as e:
            logging.error(f"Query failed: {e}")
            return None
