import asyncio
from utils.r2_client import R2Client
from utils.logging import logger
from config import R2_CONFIG

async def check_ready_posts():
    """Check if ready_post files exist in the tasks bucket."""
    try:
        # Initialize the R2 client for tasks bucket
        r2_client = R2Client(config=R2_CONFIG)
        
        # Check ready_post objects
        ready_post_objects = await r2_client.list_objects("ready_post/")
        logger.info(f"Found {len(ready_post_objects)} ready_post objects in tasks bucket")
        
        # List the first 10 ready_post objects
        for i, obj in enumerate(ready_post_objects[:10]):
            logger.info(f"  {i+1}. {obj['Key']}")
        
        # Check if toofaced ready post exists
        toofaced_ready_posts = await r2_client.list_objects("ready_post/instagram/toofaced/")
        logger.info(f"Found {len(toofaced_ready_posts)} ready_post objects for toofaced")
        
        for obj in toofaced_ready_posts:
            logger.info(f"  - {obj['Key']}")
            
            # Read the content of the JSON file if it's a JSON
            if obj['Key'].endswith('.json'):
                json_content = await r2_client.read_json(obj['Key'])
                if json_content:
                    logger.info(f"  Status: {json_content.get('status', 'unknown')}")
                    
        return True
    except Exception as e:
        logger.error(f"Error checking ready posts: {e}")
        return False

async def main():
    logger.info("🔍 Checking ready_post files in tasks bucket")
    await check_ready_posts()

if __name__ == "__main__":
    asyncio.run(main()) 