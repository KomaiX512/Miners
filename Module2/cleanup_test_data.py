"""
Cleanup script to remove test data from buckets
"""

import asyncio
from utils.r2_client import R2Client
from utils.logging import logger
from config import R2_CONFIG, STRUCTUREDB_R2_CONFIG

async def cleanup_test_data():
    """Remove all test data from buckets"""
    r2_tasks = R2Client(config=R2_CONFIG)
    r2_structuredb = R2Client(config=STRUCTUREDB_R2_CONFIG)
    
    logger.info("🧹 Starting test data cleanup...")
    
    # Clean up test files from tasks bucket
    test_files = [
        'goal/instagram/test_campaign_user/goal_test_campaign.json',
        'generated_content/instagram/test_campaign_user/posts.json',
    ]
    
    # Clean campaign posts
    for i in range(1, 25):
        test_files.extend([
            f'next_posts/instagram/test_campaign_user/campaign_post_{i}.json',
            f'ready_post/instagram/test_campaign_user/campaign_ready_post_{i}.json'
        ])
    
    deleted_count = 0
    for file_key in test_files:
        try:
            await r2_tasks.delete_object(file_key)
            logger.info(f"Deleted: {file_key}")
            deleted_count += 1
        except Exception as e:
            logger.debug(f"Could not delete {file_key}: {e}")
    
    # Clean up test profile from structuredb
    try:
        await r2_structuredb.delete_object('instagram/test_campaign_user/test_campaign_user.json')
        logger.info("Deleted: test profile data")
        deleted_count += 1
    except Exception as e:
        logger.debug(f"Could not delete test profile: {e}")
    
    logger.info(f"✅ Test data cleanup complete - {deleted_count} files removed")

if __name__ == "__main__":
    asyncio.run(cleanup_test_data()) 