#!/usr/bin/env python3
"""
Test script to verify vector database functionality after fixes.
"""

import logging
from vector_database import VectorDatabaseManager

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """Test the vector database functionality."""
    logger.info("Starting vector database test")
    
    # Initialize vector database
    db = VectorDatabaseManager()
    
    # Check if using fallback
    logger.info(f"Using fallback database: {db.use_fallback}")
    
    # Get document count
    count = db.get_count()
    logger.info(f"Vector database contains {count} documents")
    
    # Test normalizing usernames
    result = db.normalize_vector_database_usernames()
    logger.info(f"Username normalization result: {result}")
    
    # Test adding documents
    test_docs = [
        "This is a test document for vector database",
        "Another test document with different content"
    ]
    test_ids = ["test_1", "test_2"]
    test_meta = [
        {"username": "test_user", "primary_username": "test_user"},
        {"username": "test_user", "primary_username": "test_user"}
    ]
    
    db.add_documents(test_docs, test_ids, test_meta)
    
    # Test query
    query_result = db.query_similar("test document", n_results=2)
    logger.info(f"Query returned {len(query_result.get('documents', [[]])[0])} documents")
    
    # Test reinitialize
    reinit_result = db.clear_and_reinitialize(force=True)
    logger.info(f"Reinitialization result: {reinit_result}")
    
    # Check final count
    final_count = db.get_count()
    logger.info(f"Final document count: {final_count}")
    
    logger.info("Vector database test completed")

if __name__ == "__main__":
    main() 