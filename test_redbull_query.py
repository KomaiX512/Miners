#!/usr/bin/env python3

import logging
from vector_database import VectorDatabaseManager

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_redbull_query():
    """Test querying for redbull specifically"""
    
    logger.info("🎯 TESTING REDBULL QUERY")
    logger.info("=" * 50)
    
    # Initialize vector database
    vdb = VectorDatabaseManager()
    
    # Try querying for redbull content
    logger.info("🔍 Testing query for redbull competitor content...")
    
    try:
        results = vdb.query_similar(
            query_text="Appleass business strategy corporate leadership",
            filter_username="redbull",
            is_competitor=True,
            n_results=5
        )
        
        if results and 'documents' in results and results['documents']:
            documents = results['documents'][0] if results['documents'] else []
            metadatas = results['metadatas'][0] if results['metadatas'] else []
            
            logger.info(f"✅ Found {len(documents)} documents for redbull")
            
            # Show first few results
            for i, (doc, meta) in enumerate(zip(documents[:3], metadatas[:3])):
                logger.info(f"   Result {i+1}:")
                logger.info(f"     Username: {meta.get('username', 'N/A')}")
                logger.info(f"     Competitor: {meta.get('competitor', 'N/A')}")
                logger.info(f"     Is Competitor: {meta.get('is_competitor', 'N/A')}")
                logger.info(f"     Content Preview: {doc[:100]}...")
        else:
            logger.error("❌ No results found for redbull")
            
            # Debug: check what's actually there
            logger.info("🔍 Checking what competitor data exists...")
            all_data = vdb.collection.get(include=["metadatas"])
            
            redbull_docs = []
            for i, meta in enumerate(all_data["metadatas"]):
                if not meta:
                    continue
                username = meta.get("username", "")
                competitor = meta.get("competitor", "")
                is_competitor = meta.get("is_competitor", False)
                
                if (username == "redbull" or competitor == "redbull") and is_competitor:
                    redbull_docs.append({
                        'index': i,
                        'username': username,
                        'competitor': competitor,
                        'is_competitor': is_competitor,
                        'primary_username': meta.get("primary_username", "")
                    })
                    
                if len(redbull_docs) >= 3:
                    break
            
            logger.info(f"📊 Found {len(redbull_docs)} redbull documents in metadata:")
            for doc in redbull_docs:
                logger.info(f"   - Index {doc['index']}: username={doc['username']}, competitor={doc['competitor']}, primary={doc['primary_username']}")
    
    except Exception as e:
        logger.error(f"❌ Error testing redbull query: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_redbull_query()
