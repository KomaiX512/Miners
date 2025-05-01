import asyncio
from image_generator import ImageGenerator
from query_handler import QueryHandler
from goal_rag_handler import GoalRAGHandler
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

async def run_goal_rag_handler():
    handler = GoalRAGHandler()
    # Start the main watcher loop in a thread
    from threading import Thread
    def start_watcher():
        handler_main = getattr(handler, "main", None)
        if handler_main:
            handler_main()
    t = Thread(target=start_watcher, daemon=True)
    t.start()
    logger.info("GoalRAGHandler watcher started in background thread.")
    while True:
        await asyncio.sleep(60)  # Keep the task alive

async def main():
    # Perform initial verification
    await check_buckets()
    
    image_generator = ImageGenerator()
    query_handler = QueryHandler()
    try:
        await asyncio.gather(
            image_generator.run(),
            query_handler.run(),
            run_goal_rag_handler()
        )
    except KeyboardInterrupt:
        logger.info("Shutting down all modules...")
    except Exception as e:
        logger.error(f"Fatal error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
