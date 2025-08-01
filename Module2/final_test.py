#!/usr/bin/env python3
import asyncio
from query_handler import QueryHandler
from utils.logging import logger

async def test_document_loading():
    """Directly test the load_documents method in QueryHandler."""
    logger.info("==== TESTING DOCUMENT LOADING ====")
    
    # Create instance of QueryHandler
    handler = QueryHandler()
    
    # Test with Maccosmetics username
    username = "Maccosmetics"
    logger.info(f"Testing document loading for: {username}")
    
    # Attempt to load documents
    docs_loaded = await handler.load_documents(username)
    
    if docs_loaded:
        logger.info(f"SUCCESS: Documents successfully loaded for {username}")
        
        # Print loaded documents count
        doc_count = handler.collection.count()
        logger.info(f"Loaded {doc_count} documents")
    else:
        logger.error(f"FAILURE: Failed to load documents for {username}")
    
    logger.info("==== DOCUMENT LOADING TEST COMPLETE ====")

if __name__ == "__main__":
    asyncio.run(test_document_loading()) 