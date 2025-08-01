#!/usr/bin/env python3

import logging
from vector_database import VectorDatabaseManager

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def debug_filtering():
    """Debug the filtering logic step by step"""
    
    logger.info("🔍 DEBUGGING FILTERING LOGIC")
    logger.info("=" * 50)
    
    # Initialize vector database
    vdb = VectorDatabaseManager()
    
    # Get all redbull documents directly
    try:
        all_data = vdb.collection.get(include=["metadatas", "documents"])
        
        redbull_docs = []
        for i, meta in enumerate(all_data["metadatas"]):
            if not meta:
                continue
            username = meta.get("username", "")
            competitor = meta.get("competitor", "")
            is_competitor = meta.get("is_competitor", False)
            
            if username == "redbull" or competitor == "redbull":
                redbull_docs.append({
                    'index': i,
                    'username': username,
                    'competitor': competitor, 
                    'is_competitor': is_competitor,
                    'primary_username': meta.get("primary_username", ""),
                    'meta': meta,
                    'doc': all_data["documents"][i][:100] if i < len(all_data["documents"]) else ""
                })
        
        logger.info(f"📊 Found {len(redbull_docs)} redbull documents total")
        
        # Check each document against filtering logic
        filter_username = "redbull"
        is_competitor_query = True
        
        for i, doc_info in enumerate(redbull_docs[:3]):  # Just check first 3
            meta = doc_info['meta']
            logger.info(f"\n🔍 Document {i+1}:")
            logger.info(f"   Username: {meta.get('username', '')}")
            logger.info(f"   Competitor: {meta.get('competitor', '')}")
            logger.info(f"   Is Competitor: {meta.get('is_competitor', False)}")
            logger.info(f"   Primary Username: {meta.get('primary_username', '')}")
            logger.info(f"   Content: {doc_info['doc']}")
            
            # Apply the exact same filtering logic from query_similar
            match_found = False
            
            meta_username = meta.get('username', '').lower().strip()
            meta_competitor = meta.get('competitor', '').lower().strip()
            meta_primary_username = meta.get('primary_username', '').lower().strip()
            meta_is_competitor = meta.get('is_competitor', False)
            clean_username = filter_username.lower().strip()
            
            logger.info(f"   Normalized - username: '{meta_username}', competitor: '{meta_competitor}', primary: '{meta_primary_username}', is_competitor: {meta_is_competitor}")
            
            # COMPETITOR MATCHING LOGIC (exact copy from vector_database.py)
            if is_competitor_query:
                # Strategy 1: Direct competitor field match
                if meta_competitor and meta_competitor == clean_username:
                    match_found = True
                    logger.info(f"   ✅ Match via Strategy 1: competitor field")
                
                # Strategy 2: Username match with competitor flag
                elif meta_username and meta_username == clean_username and meta_is_competitor:
                    match_found = True
                    logger.info(f"   ✅ Match via Strategy 2: username+flag")
                
                # Strategy 3: Primary username match with competitor flag
                elif meta_primary_username and meta_primary_username == clean_username and meta_is_competitor:
                    match_found = True
                    logger.info(f"   ✅ Match via Strategy 3: primary_username+flag")
                
                # Strategy 4: Relaxed competitor name matching (partial matches)
                elif meta_is_competitor and (
                    (meta_username and clean_username in meta_username) or
                    (meta_competitor and clean_username in meta_competitor) or
                    (meta_username and meta_username in clean_username)
                ):
                    match_found = True
                    logger.info(f"   ✅ Match via Strategy 4: partial match")
                
                # Strategy 5: Handle username variations (underscores, etc.)
                elif meta_is_competitor and meta_username and (
                    meta_username.replace('_', '') == clean_username.replace('_', '') or
                    meta_username.replace('-', '') == clean_username.replace('-', '')
                ):
                    match_found = True
                    logger.info(f"   ✅ Match via Strategy 5: username variation")
            
            if not match_found:
                logger.error(f"   ❌ NO MATCH FOUND! This document should match but doesn't.")
                logger.error(f"   ❌ Check: meta_competitor='{meta_competitor}' == clean_username='{clean_username}' -> {meta_competitor == clean_username}")
                logger.error(f"   ❌ Check: meta_username='{meta_username}' == clean_username='{clean_username}' and meta_is_competitor={meta_is_competitor} -> {meta_username == clean_username and meta_is_competitor}")
    
    except Exception as e:
        logger.error(f"❌ Error in debug: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_filtering()
