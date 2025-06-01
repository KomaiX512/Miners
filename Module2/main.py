import asyncio
from image_generator import ImageGenerator
from query_handler import EnhancedQueryHandler
from goal_rag_handler import EnhancedGoalHandler
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
        objects = await tasks_client.list_objects("")
        logger.info(f"Successfully connected to tasks bucket. Found {len(objects)} objects.")
        
        # Look for goal files in new schema
        goal_objects = await tasks_client.list_objects("goal/")
        logger.info(f"Found {len(goal_objects)} goal-related objects")
        
        # Look for rules files
        rules_objects = await tasks_client.list_objects("rules/")
        logger.info(f"Found {len(rules_objects)} rules objects")
    except Exception as e:
        logger.error(f"Failed to access tasks bucket: {e}")
    
    # Check structuredb bucket
    structuredb_client = R2Client(config=STRUCTUREDB_R2_CONFIG)
    try:
        logger.info(f"Testing connection to structuredb bucket: {STRUCTUREDB_R2_CONFIG['bucket_name']}")
        objects = await structuredb_client.list_objects("")
        logger.info(f"Successfully connected to structuredb bucket. Found {len(objects)} objects.")
        
        # Look for profile files in new schema
        profile_objects = [obj for obj in objects if obj["Key"].endswith(".json")]
        logger.info(f"Found {len(profile_objects)} profile files")
    except Exception as e:
        logger.error(f"Failed to access structuredb bucket: {e}")

async def run_enhanced_goal_handler():
    """Run the Enhanced Goal Handler"""
    try:
        logger.info("Starting Enhanced Goal Handler...")
        goal_handler = EnhancedGoalHandler()
        
        # Scan for existing goal files
        await goal_handler.scan_existing_goals()
        
        # Start file system monitoring in background
        import os
        from watchdog.observers import Observer
        from goal_rag_handler import GoalFileEventHandler
        
        event_handler = GoalFileEventHandler(goal_handler)
        observer = Observer()
        watch_dir = os.path.join("goal")
        os.makedirs(watch_dir, exist_ok=True)
        observer.schedule(event_handler, watch_dir, recursive=True)
        observer.start()
        
        logger.info(f"Enhanced Goal Handler monitoring: {watch_dir}")
        
        # Keep running and periodically scan for new files
        try:
            while True:
                await asyncio.sleep(300)  # Check every 5 minutes instead of 1 minute
                await goal_handler.scan_existing_goals()
        finally:
            observer.stop()
            
    except Exception as e:
        logger.error(f"Error in Enhanced Goal Handler: {e}")
        if 'observer' in locals():
            observer.stop()
        raise

async def run_enhanced_query_handler():
    """Run the Enhanced Query Handler"""
    try:
        logger.info("Starting Enhanced Query Handler...")
        query_handler = EnhancedQueryHandler()
        
        # Run the enhanced query handler (includes FastAPI server)
        await query_handler.run(host="0.0.0.0", port=8001)
        
    except Exception as e:
        logger.error(f"Error in Enhanced Query Handler: {e}")
        raise

async def main():
    """Main entry point for the enhanced pipeline"""
    logger.info("🚀 Starting Enhanced Content Generation Pipeline")
    logger.info("Platform-aware schema with Deep RAG Analysis")
    logger.info("=" * 60)
    
    # Perform initial verification
    await check_buckets()
    
    # Initialize components
    image_generator = ImageGenerator()
    
    try:
        # Run all components concurrently
        await asyncio.gather(
            image_generator.run(),
            run_enhanced_query_handler(),
            run_enhanced_goal_handler(),
            return_exceptions=True
        )
    except KeyboardInterrupt:
        logger.info("🛑 Shutting down all modules...")
    except Exception as e:
        logger.error(f"💥 Fatal error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
