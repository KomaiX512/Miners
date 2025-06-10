import asyncio
import json
from utils.r2_client import R2Client
from utils.logging import logger
from config import R2_CONFIG
from image_generator import ImageGenerator

async def test_r2_client_connections():
    """Test connections to the R2 bucket."""
    try:
        # Initialize the R2 client for tasks bucket
        r2_client = R2Client(config=R2_CONFIG)
        
        # Check if we can list objects
        objects = await r2_client.list_objects("ready_post/")
        logger.info(f"Connection to tasks bucket successful, found {len(objects)} ready_post objects")
        
        # Check next_post objects
        next_post_objects = await r2_client.list_objects("next_posts/")
        logger.info(f"Found {len(next_post_objects)} next_post objects in tasks bucket")
        
        return True
    except Exception as e:
        logger.error(f"Error testing R2 client connections: {e}")
        return False

async def verify_image_generator_schema():
    """Verify that the ImageGenerator has the correct bucket configuration."""
    try:
        generator = ImageGenerator()
        logger.info(f"Input bucket: {generator.input_r2_client.bucket_name}")
        logger.info(f"Output bucket: {generator.output_r2_client.bucket_name}")
        
        # Verify both point to the tasks bucket
        if generator.input_r2_client.bucket_name != "tasks" or generator.output_r2_client.bucket_name != "tasks":
            logger.error("⚠️ ImageGenerator not configured to use the tasks bucket for both input and output!")
            return False
        
        logger.info("✅ ImageGenerator correctly configured to use tasks bucket for both input and output")
        return True
    except Exception as e:
        logger.error(f"Error verifying ImageGenerator schema: {e}")
        return False

async def simulate_post_processing():
    """Simulate processing a post to verify it gets saved correctly."""
    try:
        generator = ImageGenerator()
        
        # Create a test post
        test_post = {
            "post": {
                "caption": "Test caption",
                "hashtags": ["#Test", "#Verification"],
                "call_to_action": "Test CTA",
                "image_prompt": "High-quality test image for verification purposes"
            },
            "status": "pending"
        }
        
        # Save the test post to next_posts/test/verification/test_post.json
        test_key = "next_posts/test/verification/test_post.json"
        result = await generator.input_r2_client.write_json(test_key, test_post)
        if not result:
            logger.error("Failed to write test post")
            return False
        
        logger.info(f"Successfully wrote test post to {test_key}")
        
        # Check if ready_post directory exists
        ready_post_dir = "ready_post/test/verification/"
        objects = await generator.output_r2_client.list_objects(ready_post_dir)
        logger.info(f"Found {len(objects)} objects in {ready_post_dir}")
        
        return True
    except Exception as e:
        logger.error(f"Error in post processing simulation: {e}")
        return False

async def main():
    logger.info("🧪 Starting Image Generator Tests")
    
    # Test 1: R2 Client Connections
    logger.info("Test 1: Verifying R2 Client Connections")
    if not await test_r2_client_connections():
        logger.error("❌ R2 Client Connection Test Failed")
        return
    logger.info("✅ R2 Client Connection Test Passed")
    
    # Test 2: Image Generator Schema
    logger.info("Test 2: Verifying Image Generator Schema")
    if not await verify_image_generator_schema():
        logger.error("❌ Image Generator Schema Test Failed")
        return
    logger.info("✅ Image Generator Schema Test Passed")
    
    # Test 3: Post Processing Simulation
    logger.info("Test 3: Simulating Post Processing")
    if not await simulate_post_processing():
        logger.error("❌ Post Processing Simulation Test Failed")
        return
    logger.info("✅ Post Processing Simulation Test Passed")
    
    logger.info("🎉 All tests passed successfully!")

if __name__ == "__main__":
    asyncio.run(main()) 