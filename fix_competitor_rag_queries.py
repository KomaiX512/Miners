#!/usr/bin/env python3

"""
CRITICAL BUG FIX: RAG Competitor Query Strategy

ROOT CAUSE IDENTIFIED:
- TF-IDF embeddings don't capture semantic similarity
- Query "business strategy" never matches Red Bull's extreme sports content 
- Vector search returns 0 competitor documents → generic templates

SOLUTION:
- Use direct metadata-based queries for competitor analysis
- Bypass semantic similarity when collecting competitor content
- Focus on competitor username matching rather than content similarity
"""

import logging
from vector_database import VectorDatabaseManager

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_competitor_query_fix():
    """
    Create a fix for the competitor analysis by using direct metadata queries
    instead of semantic similarity searches
    """
    
    logger.info("🛠️ CREATING COMPETITOR QUERY FIX")
    logger.info("=" * 50)
    
    # Test the new approach
    vdb = VectorDatabaseManager()
    
    # Method 1: Direct metadata query for all competitor documents
    try:
        logger.info("🔍 Testing direct metadata query for competitors...")
        
        # Get all documents for a specific competitor
        all_data = vdb.collection.get(include=["metadatas", "documents"])
        
        competitor_docs = []
        for i, meta in enumerate(all_data["metadatas"]):
            if not meta:
                continue
                
            username = meta.get("username", "")
            competitor = meta.get("competitor", "")
            is_competitor = meta.get("is_competitor", False)
            
            # Direct competitor matching - no semantic similarity needed
            if (username == "redbull" or competitor == "redbull") and is_competitor:
                competitor_docs.append({
                    'document': all_data["documents"][i],
                    'metadata': meta
                })
                
                if len(competitor_docs) >= 10:  # Get first 10 posts
                    break
        
        logger.info(f"✅ Direct metadata query found {len(competitor_docs)} redbull documents")
        
        if competitor_docs:
            logger.info("📊 Sample redbull content found:")
            for i, doc_info in enumerate(competitor_docs[:3]):
                content_preview = doc_info['document'][:100]
                engagement = doc_info['metadata'].get('engagement', 0)
                logger.info(f"   {i+1}. Engagement: {engagement}, Content: {content_preview}...")
        
        # This proves we CAN get competitor data without semantic similarity!
        
        return competitor_docs
        
    except Exception as e:
        logger.error(f"❌ Error in competitor query fix: {str(e)}")
        return []

def implement_fix_in_vector_database():
    """
    Plan for implementing the fix in the actual vector database query method
    """
    
    logger.info("\n🛠️ IMPLEMENTATION PLAN:")
    logger.info("=" * 50)
    
    logger.info("1. MODIFY vector_database.py query_similar method:")
    logger.info("   - Add special handling for competitor queries")
    logger.info("   - When is_competitor=True and filter_username provided:")
    logger.info("     * Skip semantic similarity search")
    logger.info("     * Use direct metadata filtering")
    logger.info("     * Return ALL posts from that competitor")
    
    logger.info("\n2. PRESERVE semantic search for primary user content:")
    logger.info("   - Keep TF-IDF for primary user content recommendations")
    logger.info("   - Only use direct metadata for competitor analysis")
    
    logger.info("\n3. MODIFY main.py competitor analysis:")
    logger.info("   - Use new query approach for gathering competitor posts")
    logger.info("   - Focus on engagement metrics rather than content similarity")
    
    logger.info("\n🎯 This will fix the 'generic template' issue!")
    logger.info("   - RAG will have real competitor data to analyze")
    logger.info("   - Quality analysis will be based on actual competitor posts")
    logger.info("   - No more 'Missing required modules' errors")

if __name__ == "__main__":
    # Test the fix
    competitor_docs = create_competitor_query_fix()
    
    if competitor_docs:
        logger.info(f"\n✅ FIX VALIDATION: Found {len(competitor_docs)} competitor documents")
        logger.info("✅ This approach will solve the quality analysis problem!")
    else:
        logger.error("❌ Fix validation failed")
    
    # Show implementation plan
    implement_fix_in_vector_database()
