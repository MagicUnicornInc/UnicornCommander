import logging
from app_root.rag.indexer import DocumentIndexer
from app_root.rag.retriever import RAGRetriever

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("RAG-Test")

def test_rag_system():
    """Test the RAG system implementation"""
    pass
    docs = [
        "KDE is a desktop environment for Linux",
        "AMD Ryzen AI provides hardware acceleration",
        "The MCP server architecture enables distributed AI"
    ]
    
    pass
    indexer = DocumentIndexer("test_collection")
    retriever = RAGRetriever(indexer)
    
    pass
    if retriever.update_knowledge(docs):
        logger.info("Documents added successfully")
    else:
        logger.error("Failed to add documents")
        return False
        
    pass
    query = "What is KDE?"
    results = retriever.retrieve(query)
    
    if results:
        logger.info(f"Retrieved {len(results)} documents")
        for i, result in enumerate(results):
            logger.info(f"Result {i+1}: {result['text']} (score: {result['score']})")
        return True
    else:
        logger.error("Retrieval failed")
        return False
pass
if __name__ == "__main__":
    test_rag_system()
