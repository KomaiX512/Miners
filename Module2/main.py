import asyncio
from image_generator import ImageGenerator
from query_handler import QueryHandler
from utils.r2_client import R2Client
from utils.logging import logger
from config import R2_CONFIG, STRUCTUREDB_R2_CONFIG

async def check_buckets():
    """Verify bucket access and check if files exist on startup."""
    logger.info("Performing initial bucket verification...")
    
    # Check tasks bucket
    tasks_client = R2Client(config=R2_CONFIG)
    try:
        logger.info(f"Testing connection to tasks bucket: {R2_CONFIG['bucket_name']}")
        objects = await tasks_client.list_all_objects(max_items=10)
        logger.info(f"Successfully connected to tasks bucket. Found {len(objects)} objects.")
        
        # Look for rules files
        rules_files = await tasks_client.find_file_by_pattern("rules/")
        logger.info(f"Found {len(rules_files)} rules files: {rules_files[:5] if rules_files else 'None'}")
    except Exception as e:
        logger.error(f"Failed to access tasks bucket: {e}")
    
    # Check structuredb bucket
    structuredb_client = R2Client(config=STRUCTUREDB_R2_CONFIG)
    try:
        logger.info(f"Testing connection to structuredb bucket: {STRUCTUREDB_R2_CONFIG['bucket_name']}")
        objects = await structuredb_client.list_all_objects(max_items=10)
        logger.info(f"Successfully connected to structuredb bucket. Found {len(objects)} objects.")
        
        # Look for profile files
        profile_files = [obj["Key"] for obj in objects if obj["Key"].endswith(".json")]
        logger.info(f"Found {len(profile_files)} profile files: {profile_files[:5] if profile_files else 'None'}")
    except Exception as e:
        logger.error(f"Failed to access structuredb bucket: {e}")

async def main():
    # Perform initial verification
    await check_buckets()
    
    image_generator = ImageGenerator()
    query_handler = QueryHandler()
    try:
        await asyncio.gather(
            image_generator.run(),
            query_handler.run()
        )
    except KeyboardInterrupt:
        logger.info("Shutting down both modules...")
    except Exception as e:
        logger.error(f"Fatal error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
