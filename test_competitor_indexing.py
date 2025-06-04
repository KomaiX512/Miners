#!/usr/bin/env python3
"""
Test script to verify competitor indexing in vector database after our fixes
"""

import sys
import logging
import datetime
from vector_database import VectorDatabaseManager

# Configure logging
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_competitor_indexing():
    """Test competitor indexing with the fixed approach"""
    logger.info("Starting comprehensive competitor indexing test...")
    
    # Initialize the vector database with a clean slate
    vdb = VectorDatabaseManager()
    vdb.clear_and_reinitialize(force=True)
    logger.info("Vector database reinitialized")
    
    # Create test data
    primary_username = "testprimary"
    competitor_username = "testcompetitor"
    second_competitor = "testcompetitor2"
    
    # Create primary user posts
    primary_posts = [
        {
            "caption": "This is a primary user post #test",
            "timestamp": datetime.datetime.now().isoformat(),
            "username": primary_username,
            "engagement": 100,
            "id": "p1"
        },
        {
            "caption": "Another primary post #engagement",
            "timestamp": datetime.datetime.now().isoformat(),
            "username": primary_username,
            "engagement": 200,
            "id": "p2"
        }
    ]
    
    # Create competitor posts
    competitor_posts = [
        {
            "caption": "This is a competitor post #competition",
            "timestamp": datetime.datetime.now().isoformat(),
            "username": competitor_username,
            "engagement": 150,
            "id": "c1"
        },
        {
            "caption": "Another competitor post #strategy",
            "timestamp": datetime.datetime.now().isoformat(),
            "username": competitor_username,
            "engagement": 250,
            "id": "c2"
        }
    ]
    
    # Create second competitor posts
    second_competitor_posts = [
        {
            "caption": "Second competitor post #marketing",
            "timestamp": datetime.datetime.now().isoformat(),
            "username": second_competitor,
            "engagement": 300,
            "id": "s1"
        }
    ]
    
    # Test 1: Add primary user posts
    logger.info("Test 1: Adding primary user posts")
    vdb.add_posts(primary_posts, primary_username, is_competitor=False)
    
    # Verify primary posts were added
    primary_query = vdb.query_similar("test post", n_results=10, filter_username=primary_username)
    primary_count = len(primary_query['documents'][0]) if primary_query['documents'][0] else 0
    logger.info(f"Found {primary_count} primary posts (expected: 2)")
    assert primary_count == 2, "Primary posts weren't properly indexed"
    
    # Test 2: Add competitor posts
    logger.info("Test 2: Adding competitor posts")
    vdb.add_posts(competitor_posts, primary_username, is_competitor=True)
    
    # Test 3: Query competitor posts by competitor name
    logger.info("Test 3: Querying competitor posts by competitor name")
    competitor_query = vdb.query_similar("competition", n_results=10, filter_username=competitor_username, is_competitor=True)
    competitor_count = len(competitor_query['documents'][0]) if competitor_query['documents'][0] else 0
    logger.info(f"Found {competitor_count} competitor posts by competitor name (expected: 2)")
    assert competitor_count == 2, "Competitor posts weren't properly indexed or couldn't be queried by competitor name"
    
    # Test 4: Add second competitor posts
    logger.info("Test 4: Adding second competitor posts")
    vdb.add_posts(second_competitor_posts, primary_username, is_competitor=True)
    
    # Test 5: Query second competitor posts
    logger.info("Test 5: Querying second competitor posts")
    second_query = vdb.query_similar("marketing", n_results=10, filter_username=second_competitor, is_competitor=True)
    second_count = len(second_query['documents'][0]) if second_query['documents'][0] else 0
    logger.info(f"Found {second_count} second competitor posts (expected: 1)")
    assert second_count == 1, "Second competitor posts weren't properly indexed"
    
    # Test 6: Verify primary user not found as competitor
    logger.info("Test 6: Verifying primary user is not found as competitor")
    primary_as_competitor = vdb.query_similar("test", n_results=10, filter_username=primary_username, is_competitor=True)
    primary_comp_count = len(primary_as_competitor['documents'][0]) if primary_as_competitor['documents'][0] else 0
    logger.info(f"Found {primary_comp_count} primary posts as competitor (expected: 0)")
    assert primary_comp_count == 0, "Primary posts were incorrectly indexed as competitor posts"
    
    # Test 7: Normalize competitor data and verify
    logger.info("Test 7: Testing normalization of competitor data")
    vdb.normalize_competitor_data()
    
    # Verify normalization didn't break querying
    after_norm_query = vdb.query_similar("competition", n_results=10, filter_username=competitor_username, is_competitor=True)
    after_norm_count = len(after_norm_query['documents'][0]) if after_norm_query['documents'][0] else 0
    logger.info(f"Found {after_norm_count} competitor posts after normalization (expected: 2)")
    assert after_norm_count == 2, "Normalization broke competitor querying"
    
    # Test 8: Verify total document count
    total_docs = vdb.get_count()
    logger.info(f"Total documents in vector DB: {total_docs} (expected: 5)")
    assert total_docs == 5, f"Expected 5 total documents, but got {total_docs}"
    
    logger.info("✅ All competitor indexing tests passed! The fix is working correctly.")
    return True

def run_all_tests():
    """Run all tests to verify fixes"""
    success = test_competitor_indexing()
    if success:
        logger.info("🎉 All tests passed successfully!")
        return True
    else:
        logger.error("❌ Tests failed!")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1) 