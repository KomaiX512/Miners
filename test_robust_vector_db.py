#!/usr/bin/env python3
"""
Test script to verify the robust dual-database vector system works properly.
This specifically tests competitor queries which have been problematic.
"""

import logging
import time
import json
from vector_database import VectorDatabaseManager

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(name)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_competitor_queries():
    """Test competitor queries with the robust dual-database system."""
    logger.info("=" * 80)
    logger.info("TESTING ROBUST DUAL-DATABASE VECTOR SYSTEM")
    logger.info("=" * 80)
    
    # Initialize vector database
    vdb = VectorDatabaseManager()
    vdb.clear_before_new_run()
    
    # Create test data for a primary account and competitors
    primary_username = "toofaced"
    competitors = ["maccosmetics", "fentybeauty", "narsissist"]
    
    # Add primary account posts
    primary_posts = [
        {
            "id": "primary_1",
            "caption": "Check out our new Ribbon Wrapped Lash Extreme Tubing Mascara!",
            "engagement": 3500,
            "likes": 3000,
            "comments": 500,
            "timestamp": "2025-06-01T12:00:00Z",
            "username": primary_username
        },
        {
            "id": "primary_2",
            "caption": "Join our Friends & Family Sale for 30% off sitewide!",
            "engagement": 2800,
            "likes": 2500,
            "comments": 300,
            "timestamp": "2025-06-02T15:00:00Z",
            "username": primary_username
        },
        {
            "id": "primary_3",
            "caption": "Enter our #TooFacedWrappedMasterpiece contest for a chance to win!",
            "engagement": 8300,
            "likes": 7500,
            "comments": 800,
            "timestamp": "2025-06-03T10:00:00Z",
            "username": primary_username
        }
    ]
    
    # Add competitor posts
    competitor_posts = {
        "maccosmetics": [
            {
                "id": "mac_1",
                "caption": "Our new MAC Studio Fix foundation shades are here! Perfect for all skin tones.",
                "engagement": 4200,
                "likes": 3800,
                "comments": 400,
                "timestamp": "2025-06-01T14:00:00Z",
                "username": "maccosmetics"
            },
            {
                "id": "mac_2",
                "caption": "Introducing our limited-edition MAC x Artist collaboration lipsticks!",
                "engagement": 3100,
                "likes": 2800,
                "comments": 300,
                "timestamp": "2025-06-02T11:00:00Z",
                "username": "maccosmetics"
            }
        ],
        "fentybeauty": [
            {
                "id": "fenty_1",
                "caption": "Fenty Beauty's new highlighter collection is here to make you shine!",
                "engagement": 6500,
                "likes": 6000,
                "comments": 500,
                "timestamp": "2025-06-01T16:00:00Z",
                "username": "fentybeauty"
            },
            {
                "id": "fenty_2",
                "caption": "Our foundation range now includes 50 shades for all skin tones!",
                "engagement": 5800,
                "likes": 5300,
                "comments": 500,
                "timestamp": "2025-06-02T13:00:00Z",
                "username": "fentybeauty"
            }
        ],
        "narsissist": [
            {
                "id": "nars_1",
                "caption": "NARS new blush collection gives you that perfect flush of color!",
                "engagement": 3700,
                "likes": 3400,
                "comments": 300,
                "timestamp": "2025-06-01T15:00:00Z",
                "username": "narsissist"
            },
            {
                "id": "nars_2",
                "caption": "Our iconic Orgasm blush now comes in multiple formulations!",
                "engagement": 4100,
                "likes": 3700,
                "comments": 400,
                "timestamp": "2025-06-02T14:00:00Z",
                "username": "narsissist"
            }
        ]
    }
    
    # Test with both ChromaDB and fallback database
    for force_fallback in [False, True]:
        # Set database mode
        vdb.use_fallback = force_fallback
        db_type = "FALLBACK DATABASE" if force_fallback else "CHROMADB"
        
        logger.info("\n" + "=" * 80)
        logger.info(f"TESTING WITH {db_type}")
        logger.info("=" * 80)
        
        # Clear the database
        vdb.clear_collection()
        
        # Add primary account posts
        logger.info(f"Adding {len(primary_posts)} primary posts for {primary_username}")
        primary_count = vdb.add_posts(primary_posts, primary_username)
        logger.info(f"Added {primary_count} primary posts")
        
        # Add competitor posts
        for competitor in competitors:
            posts = competitor_posts[competitor]
            logger.info(f"Adding {len(posts)} posts for competitor {competitor}")
            competitor_count = vdb.add_posts(posts, primary_username, is_competitor=True)
            logger.info(f"Added {competitor_count} posts for competitor {competitor}")
        
        # Verify document count
        total_count = vdb.get_count()
        expected_count = len(primary_posts) + sum(len(posts) for posts in competitor_posts.values())
        logger.info(f"Total documents: {total_count} (expected: {expected_count})")
        
        # Test primary account queries
        logger.info("\nTesting primary account queries...")
        primary_results = vdb.query_similar("mascara", n_results=3, filter_username=primary_username)
        primary_docs = primary_results.get('documents', [[]])[0]
        logger.info(f"Primary query found {len(primary_docs)} documents")
        for doc in primary_docs:
            logger.info(f"  - {doc[:50]}...")
        
        # Test each competitor query
        logger.info("\nTesting competitor queries...")
        for competitor in competitors:
            logger.info(f"\nQuerying competitor: {competitor}")
            
            # Try different query terms
            for query in ["foundation", "collection", "beauty"]:
                competitor_results = vdb.query_similar(
                    query, 
                    n_results=3, 
                    filter_username=competitor, 
                    is_competitor=True
                )
                
                competitor_docs = competitor_results.get('documents', [[]])[0]
                competitor_metas = competitor_results.get('metadatas', [[]])[0]
                
                logger.info(f"Query '{query}' found {len(competitor_docs)} documents")
                
                if competitor_docs:
                    for i, doc in enumerate(competitor_docs):
                        meta = competitor_metas[i] if i < len(competitor_metas) else {}
                        username = meta.get('username', 'unknown')
                        engagement = meta.get('engagement', 0)
                        logger.info(f"  - [{username}] {doc[:50]}... (engagement: {engagement})")
                else:
                    logger.warning(f"No results found for {competitor} with query '{query}'")
    
    # Final test with forced ChromaDB failure
    logger.info("\n" + "=" * 80)
    logger.info("TESTING AUTOMATIC FALLBACK ON CHROMADB FAILURE")
    logger.info("=" * 80)
    
    # Reset and force ChromaDB initially
    vdb = VectorDatabaseManager()
    vdb.clear_before_new_run()
    vdb.use_fallback = False
    
    # Add some test data
    logger.info("Adding test data to ChromaDB")
    vdb.add_posts(primary_posts, primary_username)
    for competitor in competitors[:1]:  # Just add one competitor for this test
        vdb.add_posts(competitor_posts[competitor], primary_username, is_competitor=True)
    
    # Verify it's working
    results = vdb.query_similar("test", n_results=1)
    if results and results.get('documents', [[]])[0]:
        logger.info("ChromaDB is working for initial query")
    
    # Now simulate ChromaDB failure and verify automatic fallback
    logger.info("Simulating ChromaDB failure...")
    
    # Method 1: Corrupt the collection reference
    vdb.collection = None
    
    # Try a query - should automatically fall back
    logger.info("Attempting query after simulated failure...")
    try:
        results = vdb.query_similar("beauty", n_results=2)
        if results and results.get('documents', [[]])[0]:
            logger.info("✅ Query succeeded using automatic fallback mechanism!")
            logger.info(f"Found {len(results.get('documents', [[]])[0])} documents")
            
            # Verify we're now using fallback
            if vdb.use_fallback:
                logger.info("✅ System correctly switched to fallback database")
            else:
                logger.error("❌ System did not switch to fallback database")
        else:
            logger.error("❌ Query returned no results even with fallback")
    except Exception as e:
        logger.error(f"❌ Query failed even with fallback: {str(e)}")
    
    logger.info("\n" + "=" * 80)
    logger.info("ROBUST VECTOR DATABASE TEST COMPLETED")
    logger.info("=" * 80)
    
    # Return success if we got this far
    return True

if __name__ == "__main__":
    test_competitor_queries() 