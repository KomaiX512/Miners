#!/usr/bin/env python3

import logging
from vector_database import VectorDatabaseManager

# Set up logging for detailed vector database operations
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def debug_chromadb_query():
    """Debug what ChromaDB returns before any filtering"""
    
    logger.info("🔍 DEBUGGING CHROMADB QUERY BEFORE FILTERING")
    logger.info("=" * 60)
    
    # Initialize vector database
    vdb = VectorDatabaseManager()
    
    # Manually simulate the exact query from query_similar
    query_text = "Appleass business strategy corporate leadership"
    n_results = 5
    
    try:
        # Generate embedding just like query_similar does
        logger.info(f"🔍 Generating embedding for: '{query_text}'")
        query_embedding = vdb._get_embeddings([query_text])
        if not query_embedding or len(query_embedding) == 0:
            logger.error("❌ Failed to generate embedding")
            return
            
        query_vector = query_embedding[0]
        logger.info(f"✅ Generated embedding with shape: {len(query_vector)}")
        
        # Get collection size
        collection_size = vdb.get_count()
        safe_n_results = min(n_results, collection_size, 20)
        logger.info(f"📊 Collection size: {collection_size}, using n_results: {safe_n_results}")
        
        # Execute the exact same ChromaDB query
        query_params = {
            'query_embeddings': [query_vector],
            'n_results': safe_n_results,
            'include': ['documents', 'metadatas', 'distances']
        }
        
        logger.info("🚀 Executing ChromaDB query...")
        results = vdb.collection.query(**query_params)
        
        logger.info("✅ ChromaDB query completed")
        
        # Check what ChromaDB returned
        if not results:
            logger.error("❌ ChromaDB returned None")
            return
            
        documents = results.get('documents', [[]])[0] if results.get('documents') else []
        metadatas = results.get('metadatas', [[]])[0] if results.get('metadatas') else []
        distances = results.get('distances', [[]])[0] if results.get('distances') else []
        
        logger.info(f"📊 ChromaDB returned {len(documents)} documents BEFORE filtering")
        
        # Analyze what ChromaDB returned
        redbull_count = 0
        netflix_count = 0
        competitor_count = 0
        
        for i, (doc, meta) in enumerate(zip(documents, metadatas)):
            username = meta.get('username', '') if meta else ''
            competitor = meta.get('competitor', '') if meta else ''
            is_competitor = meta.get('is_competitor', False) if meta else False
            distance = distances[i] if i < len(distances) else 'N/A'
            
            logger.info(f"   Document {i+1}: username='{username}', competitor='{competitor}', is_competitor={is_competitor}, distance={distance}")
            logger.info(f"      Content: {doc[:100]}...")
            
            if username == 'redbull' or competitor == 'redbull':
                redbull_count += 1
            if username == 'netflix' or competitor == 'netflix':
                netflix_count += 1
            if is_competitor:
                competitor_count += 1
        
        logger.info(f"\n📊 CHROMADB QUERY RESULTS SUMMARY:")
        logger.info(f"   Total documents returned: {len(documents)}")
        logger.info(f"   Redbull documents: {redbull_count}")
        logger.info(f"   Netflix documents: {netflix_count}")
        logger.info(f"   Competitor documents: {competitor_count}")
        
        if redbull_count == 0:
            logger.error(f"❌ PROBLEM FOUND: ChromaDB query didn't return ANY redbull documents!")
            logger.error(f"❌ This means the vector similarity search isn't finding redbull content")
            logger.error(f"❌ The issue is in the embedding/similarity matching, not the filtering!")
        else:
            logger.info(f"✅ ChromaDB found redbull documents, so filtering must be the issue")
    
    except Exception as e:
        logger.error(f"❌ Error in ChromaDB debug: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_chromadb_query()
