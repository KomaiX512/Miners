#!/usr/bin/env python3
import asyncio
import json
import time
from utils.r2_client import R2Client
from utils.logging import logger
from config import R2_CONFIG

async def create_test_query():
    """Create a test query file for Maccosmetics and check if it's processed."""
    logger.info("Creating test query for Maccosmetics...")
    
    # Create R2 client
    r2_client = R2Client(config=R2_CONFIG)
    
    # Create test query
    query_data = {
        "query": "What are your most popular products?",
        "status": "pending"
    }
    
    # Define query path
    query_path = "queries/Maccosmetics/test_query.json"
    
    # Save test query
    result = await r2_client.write_json(query_path, query_data)
    if result:
        logger.info(f"Successfully created test query at {query_path}")
    else:
        logger.error(f"Failed to create test query at {query_path}")
        return
    
    # Monitor query status
    for i in range(10):  # Check for 10 iterations
        logger.info(f"Checking query status ({i+1}/10)...")
        time.sleep(5)  # Wait 5 seconds between checks
        
        # Read query file
        data = await r2_client.read_json(query_path)
        if data and data.get("status") == "processed":
            logger.info("Success! Query was processed!")
            return
        
        # Look for response file
        objects = await r2_client.list_objects("queries/Maccosmetics/")
        response_files = [o["Key"] for o in objects if "response_" in o["Key"]]
        logger.info(f"Found {len(response_files)} response files")
        
    logger.warning("Test completed. Check logs to see if query was processed.")

if __name__ == "__main__":
    asyncio.run(create_test_query()) 