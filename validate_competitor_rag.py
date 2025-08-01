#!/usr/bin/env python3
"""
Focused validation test for competitor RAG functionality.
Tests the exact scenario that was failing: zero-post handler with competitor analysis.
"""

import logging
import sys
import os
import asyncio
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_competitor_rag_zero_post_scenario():
    """Test the exact scenario that was failing: competitor analysis for zero-post accounts."""
    try:
        from vector_database import VectorDatabaseManager
        from zero_data_handler import ZeroDataHandler
        
        logger.info("🚀 Starting focused competitor RAG validation test...")
        
        # Initialize vector database
        logger.info("1️⃣ Initializing vector database...")
        vector_db = VectorDatabaseManager()
        await vector_db.initialize()
        
        # Test competitor data query specifically - this was the core issue
        logger.info("2️⃣ Testing competitor data query (this was failing before)...")
        
        # Test different competitor queries to validate the fix
        test_queries = [
            ("beauty makeup trends", "fentybeauty"),
            ("makeup products", "toofaced"),
            ("cosmetics beauty", "maccosmetics")
        ]
        
        total_results = 0
        for query, username in test_queries:
            competitor_results = vector_db.query_similar(
                query,
                username=username,
                is_competitor=True,
                n_results=3
            )
            
            logger.info(f"📊 Query '{query}' for {username}: {len(competitor_results)} results")
            total_results += len(competitor_results)
            
            if competitor_results:
                for i, result in enumerate(competitor_results[:1]):
                    logger.info(f"   Sample: {result[:80]}...")
        
        if total_results == 0:
            logger.error("❌ COMPETITOR QUERY FAILED - No results found across all queries!")
            logger.error("🚨 The vector database filtering fix did not work")
            return False
        
        logger.info(f"✅ Found {total_results} total competitor results across queries")
        
        # Test direct vector database state
        logger.info("3️⃣ Checking vector database competitor data state...")
        try:
            # Get collection info
            collection_info = vector_db.collection.get()
            total_docs = len(collection_info['ids']) if collection_info['ids'] else 0
            
            # Count competitor documents
            competitor_docs = 0
            if collection_info['metadatas']:
                for metadata in collection_info['metadatas']:
                    if metadata and metadata.get('is_competitor'):
                        competitor_docs += 1
            
            logger.info(f"� Vector DB state: {total_docs} total docs, {competitor_docs} competitor docs")
            
            if competitor_docs == 0:
                logger.error("❌ No competitor documents found in vector database!")
                return False
                
        except Exception as e:
            logger.warning(f"⚠️ Could not check vector DB state: {e}")
        
        # Test zero data handler with a simple competitor check
        logger.info("4️⃣ Testing zero data handler competitor functionality...")
        zero_handler = ZeroDataHandler()
        
        # Test the competitor checking method that was failing
        competitor_usernames = ['fentybeauty', 'toofaced', 'maccosmetics']
        found_competitors = zero_handler._exhaustive_vector_competitor_check(
            competitor_usernames, 'instagram'
        )
        
        logger.info(f"📊 Zero handler found competitors: {found_competitors}")
        
        if not found_competitors:
            logger.error("❌ Zero data handler cannot find competitors in vector database!")
            logger.error("🚨 The integration between zero handler and vector DB is broken")
            return False
            
        logger.info("✅ Zero data handler successfully found competitor data")
        return True
            
    except Exception as e:
        logger.error(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Main test execution."""
    logger.info("🔍 COMPETITOR RAG VALIDATION TEST")
    logger.info("=" * 50)
    
    success = await test_competitor_rag_zero_post_scenario()
    
    if success:
        logger.info("✅ COMPETITOR RAG VALIDATION: SUCCESS")
        logger.info("🎯 Zero-post accounts should now receive real competitor analysis")
    else:
        logger.error("❌ COMPETITOR RAG VALIDATION: FAILED")
        logger.error("🚨 Issue still exists - further debugging needed")
    
    return success

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
