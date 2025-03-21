import logging
from typing import List, Dict
from .indexer import DocumentIndexer

class RAGRetriever:
    def __init__(self, indexer: DocumentIndexer):
        self.indexer = indexer
        
    def retrieve(self, query: str, n_docs: int = 3) -> List[Dict]:
        """Retrieve relevant documents for a query"""
        try:
            results = self.indexer.query(query, n_results=n_docs)
            if results and results['documents']:
                return [
                    {"text": doc, "score": score}
                    for doc, score in zip(results['documents'][0], results['distances'][0])
                ]
            return []
        except Exception as e:
            logging.error(f"Retrieval failed: {e}")
            return []
            
    def update_knowledge(self, documents: List[str], metadata: List[Dict] = None):
        """Update the knowledge base"""
        return self.indexer.add_documents(documents, metadata)
