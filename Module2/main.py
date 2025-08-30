import asyncio
import os
import fcntl
from image_generator import ImageGenerator
from query_handler import SequentialQueryHandler
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
        
        # Log what goal objects we found
        for obj in goal_objects[:5]:  # Show first 5 for debugging
            logger.info(f"📁 Goal object: {obj['Key']}")
        
        # Check each platform specifically
        for platform in ["instagram", "twitter", "facebook"]:
            platform_goals = await tasks_client.list_objects(f"goal/{platform}/")
            logger.info(f"📁 {platform} goals: {len(platform_goals)} objects")
            for obj in platform_goals[:3]:  # Show first 3 for each platform
                logger.info(f"  📄 {platform} goal: {obj['Key']}")
        
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
                await asyncio.sleep(60)  # Check every 1 minute as requested
                await goal_handler.scan_existing_goals()
        finally:
            observer.stop()
            
    except Exception as e:
        logger.error(f"Error in Enhanced Goal Handler: {e}")
        if 'observer' in locals():
            observer.stop()
        raise

async def run_sequential_query_handler():
    """Run the Sequential Query Handler with 10-second retry loop"""
    try:
        logger.info("Starting Sequential Query Handler with 10-second retry...")
        query_handler = SequentialQueryHandler()
        
        # Run continuous processing with 10-second retry
        await query_handler.run_continuous_processing()
        
    except Exception as e:
        logger.error(f"Error in Sequential Query Handler: {e}")
        raise

async def main():
    """Main entry point for the enhanced pipeline (single-instance, sequential)."""
    logger.info("🚀 Starting Enhanced Content Generation Pipeline (SEQUENTIAL, SINGLE-INSTANCE)")
    logger.info("Platform-aware schema with Deep RAG Analysis")
    logger.info("Strictly sequential processing across modules")
    logger.info("=" * 60)

    # Single-instance file lock
    lock_file_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".module2.lock"))
    lock_file = open(lock_file_path, "w")
    try:
        fcntl.flock(lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
        lock_file.write(str(os.getpid()))
        lock_file.flush()
        logger.info(f"🔒 Acquired single-instance lock at {lock_file_path}")
    except BlockingIOError:
        logger.error("🚫 Another instance of Module2 is already running. Exiting.")
        return

    # Perform initial verification
    await check_buckets()

    # Initialize components
    image_generator = ImageGenerator()

    try:
        # Strict sequential scheduler loop
        while True:
            # 1) Goal handler single scan
            try:
                goal_handler = EnhancedGoalHandler()
                await goal_handler.scan_existing_goals()
            except Exception as e:
                logger.error(f"Goal handler step error: {e}")

            # 2) Query handler single pass
            try:
                handler = SequentialQueryHandler()
                # Scan each platform once; break early if any processed
                processed_any = False
                for platform in handler.platforms:
                    if await handler.scan_platform_for_pending_posts(platform):
                        processed_any = True
                        break
                if processed_any:
                    logger.info("✅ [Sequential] Processed pending posts in query handler")
            except Exception as e:
                logger.error(f"Query handler step error: {e}")

            # 3) Image generator single cycle (process at most one)
            try:
                await image_generator.process_single_cycle()
            except Exception as e:
                logger.error(f"Image generator step error: {e}")

            # Small interval to prevent busy loop
            await asyncio.sleep(5)

    except KeyboardInterrupt:
        logger.info("🛑 Shutting down Module2 sequential scheduler...")
    except Exception as e:
        logger.error(f"💥 Fatal error: {e}")
    finally:
        try:
            fcntl.flock(lock_file, fcntl.LOCK_UN)
            lock_file.close()
            logger.info("🔓 Released single-instance lock")
        except Exception:
            pass

if __name__ == "__main__":
    asyncio.run(main())
