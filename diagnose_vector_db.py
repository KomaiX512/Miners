#!/usr/bin/env python3

import logging
from vector_database import VectorDatabaseManager

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def diagnose_vector_db():
    """Diagnose what's actually in the vector database"""
    
    logger.info("🔍 VECTOR DATABASE DIAGNOSIS")
    logger.info("=" * 50)
    
    # Initialize vector database
    vdb = VectorDatabaseManager()
    
    # Check collection count
    count = vdb.get_count()
    logger.info(f"📊 Total documents in collection: {count}")
    
    # Get all documents with metadata
    try:
        all_data = vdb.collection.get(include=["metadatas"])
        
        if not all_data or "metadatas" not in all_data:
            logger.error("❌ Could not retrieve metadata")
            return
        
        metadatas = all_data["metadatas"]
        logger.info(f"📊 Retrieved metadata for {len(metadatas)} documents")
        
        # Analyze usernames
        usernames = set()
        competitor_usernames = set()
        primary_usernames = set()
        competitor_flags = []
        
        for meta in metadatas:
            if not meta:
                continue
                
            username = meta.get("username", "")
            primary_username = meta.get("primary_username", "")
            is_competitor = meta.get("is_competitor", False)
            competitor = meta.get("competitor", "")
            
            if username:
                usernames.add(username)
            if primary_username:
                primary_usernames.add(primary_username)
            if is_competitor:
                competitor_flags.append(True)
                if username:
                    competitor_usernames.add(username)
                if competitor:
                    competitor_usernames.add(competitor)
            else:
                competitor_flags.append(False)
        
        logger.info(f"📊 ANALYSIS:")
        logger.info(f"   Total unique usernames: {len(usernames)}")
        logger.info(f"   Total unique primary_usernames: {len(primary_usernames)}")
        logger.info(f"   Total unique competitor usernames: {len(competitor_usernames)}")
        logger.info(f"   Documents with is_competitor=True: {sum(competitor_flags)}")
        logger.info(f"   Documents with is_competitor=False: {len(competitor_flags) - sum(competitor_flags)}")
        
        logger.info(f"\n📊 USERNAMES FOUND:")
        for username in sorted(usernames):
            logger.info(f"   - {username}")
        
        logger.info(f"\n📊 PRIMARY USERNAMES FOUND:")
        for username in sorted(primary_usernames):
            logger.info(f"   - {username}")
        
        logger.info(f"\n📊 COMPETITOR USERNAMES FOUND:")
        for username in sorted(competitor_usernames):
            logger.info(f"   - {username}")
        
        # Check for redbull and netflix specifically
        logger.info(f"\n🎯 SPECIFIC CHECKS:")
        
        redbull_count = 0
        netflix_count = 0
        for meta in metadatas:
            if not meta:
                continue
            username = meta.get("username", "")
            competitor = meta.get("competitor", "")
            if username == "redbull" or competitor == "redbull":
                redbull_count += 1
            if username == "netflix" or competitor == "netflix":
                netflix_count += 1
        
        logger.info(f"   Documents with redbull: {redbull_count}")
        logger.info(f"   Documents with netflix: {netflix_count}")
        
        # Sample a few competitor documents
        logger.info(f"\n📊 SAMPLE COMPETITOR DOCUMENTS:")
        competitor_samples = []
        for i, meta in enumerate(metadatas):
            if not meta:
                continue
            if meta.get("is_competitor", False):
                competitor_samples.append({
                    'index': i,
                    'username': meta.get("username", ""),
                    'primary_username': meta.get("primary_username", ""),
                    'competitor': meta.get("competitor", ""),
                    'is_competitor': meta.get("is_competitor", False),
                    'platform': meta.get("platform", "")
                })
                if len(competitor_samples) >= 5:
                    break
        
        for sample in competitor_samples:
            logger.info(f"   Sample {sample['index']}: username={sample['username']}, competitor={sample['competitor']}, primary={sample['primary_username']}")
        
    except Exception as e:
        logger.error(f"❌ Error during diagnosis: {str(e)}")

if __name__ == "__main__":
    diagnose_vector_db()
