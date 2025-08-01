#!/usr/bin/env python3
import asyncio
import sys
from utils.r2_client import R2Client
from utils.logging import logger
from config import R2_CONFIG, STRUCTUREDB_R2_CONFIG

async def debug_r2_access(username=None):
    """Debug script to check R2 access and find files in buckets."""
    logger.info("===== R2 Bucket Access Debugging =====")
    
    # Check tasks bucket
    tasks_client = R2Client(config=R2_CONFIG)
    try:
        logger.info(f"Testing connection to tasks bucket: {R2_CONFIG['bucket_name']}")
        all_objects = await tasks_client.list_all_objects()
        logger.info(f"Successfully connected to tasks bucket. Found {len(all_objects)} objects.")
        
        # Print first 10 objects for verification
        if all_objects:
            logger.info("First 10 objects in tasks bucket:")
            for i, obj in enumerate(all_objects[:10]):
                logger.info(f"  {i+1}. {obj['Key']}")
        
        # If username provided, look for specific files
        if username:
            logger.info(f"Searching for files matching username '{username}' in tasks bucket...")
            
            # Look for rules files
            rules_files = await tasks_client.find_file_by_pattern(f"rules/{username}")
            logger.info(f"Found {len(rules_files)} rules files for {username}:")
            for file in rules_files:
                logger.info(f"  - {file}")
                
            # Look for query files
            query_files = await tasks_client.find_file_by_pattern(f"queries/{username}")
            logger.info(f"Found {len(query_files)} query files for {username}:")
            for file in query_files:
                logger.info(f"  - {file}")
    except Exception as e:
        logger.error(f"Failed to access tasks bucket: {e}")
    
    # Check structuredb bucket
    structuredb_client = R2Client(config=STRUCTUREDB_R2_CONFIG)
    try:
        logger.info(f"Testing connection to structuredb bucket: {STRUCTUREDB_R2_CONFIG['bucket_name']}")
        all_objects = await structuredb_client.list_all_objects()
        logger.info(f"Successfully connected to structuredb bucket. Found {len(all_objects)} objects.")
        
        # Print first 10 objects for verification
        if all_objects:
            logger.info("First 10 objects in structuredb bucket:")
            for i, obj in enumerate(all_objects[:10]):
                logger.info(f"  {i+1}. {obj['Key']}")
        
        # If username provided, look for profile files
        if username:
            logger.info(f"Searching for profile files matching username '{username}' in structuredb bucket...")
            profile_files = await structuredb_client.find_file_by_pattern(username)
            logger.info(f"Found {len(profile_files)} profile files for {username}:")
            for file in profile_files:
                logger.info(f"  - {file}")
                
            # Try to read one of these files to verify content access
            if profile_files:
                logger.info(f"Attempting to read file: {profile_files[0]}")
                data = await structuredb_client.read_json(profile_files[0])
                if data:
                    logger.info(f"Successfully read file {profile_files[0]}")
                else:
                    logger.error(f"Failed to read file {profile_files[0]}")
    except Exception as e:
        logger.error(f"Failed to access structuredb bucket: {e}")
    
    logger.info("===== R2 Bucket Access Debugging Complete =====")

if __name__ == "__main__":
    username = sys.argv[1] if len(sys.argv) > 1 else None
    if username:
        logger.info(f"Debug mode with username: {username}")
    else:
        logger.info("Debug mode with no username specified")
    
    asyncio.run(debug_r2_access(username)) 