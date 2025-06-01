"""
Test Script for Sequential Query Handler
Validates the new processing workflow for generated_content posts.
"""

import asyncio
import json
from datetime import datetime
from utils.r2_client import R2Client
from utils.logging import logger
from config import R2_CONFIG
from query_handler import SequentialQueryHandler

async def create_test_generated_content():
    """Create test generated_content file"""
    r2_client = R2Client(config=R2_CONFIG)
    
    # Create test content in the expected format
    test_content = {
        "Post_1": {
            "content": "This is an exciting announcement about our latest product launch. We're thrilled to share this innovation with our community. The visual should show a sleek product shot with modern lighting and clean background.",
            "status": "pending"
        },
        "Post_2": {
            "content": "Here's a behind-the-scenes look at our creative process. Our team works tirelessly to bring you quality content. The image should capture our team in action with warm, collaborative lighting.",
            "status": "pending"
        },
        "Post_3": {
            "content": "Thank you to our amazing community for your continued support. Your engagement means everything to us. The visual should be a heartwarming community collage with vibrant colors.",
            "status": "pending"
        },
        "Summary": "📊 STATISTICAL CAMPAIGN ANALYSIS: This 3-post strategy targets moderate engagement increase over 7 days, based on comprehensive data analysis. ML prediction with 85% confidence based on engagement factors."
    }
    
    # Save to generated_content directory
    test_key = "generated_content/instagram/testuser/posts.json"
    success = await r2_client.write_json(test_key, test_content)
    
    if success:
        logger.info(f"✅ Created test generated_content file: {test_key}")
        return test_key
    else:
        logger.error(f"❌ Failed to create test file")
        return None

async def test_sequential_processing():
    """Test the sequential processing functionality"""
    logger.info("🧪 Starting Sequential Query Handler Test")
    
    # Create test content
    test_key = await create_test_generated_content()
    if not test_key:
        logger.error("❌ Failed to create test content")
        return
    
    # Initialize handler
    handler = SequentialQueryHandler()
    
    # Test processing one post at a time
    for i in range(3):
        logger.info(f"🔄 Test iteration {i + 1}: Processing one pending post")
        
        # Process one pending post
        processed = await handler.scan_platform_for_pending_posts("instagram")
        
        if processed:
            logger.info(f"✅ Successfully processed a post in iteration {i + 1}")
            
            # Check the updated file
            r2_client = R2Client(config=R2_CONFIG)
            updated_content = await r2_client.read_json(test_key)
            
            if updated_content:
                pending_count = sum(
                    1 for key, value in updated_content.items() 
                    if key.startswith("Post_") and value.get("status") == "pending"
                )
                processed_count = sum(
                    1 for key, value in updated_content.items() 
                    if key.startswith("Post_") and value.get("status") == "processed"
                )
                
                logger.info(f"📊 Status: {pending_count} pending, {processed_count} processed")
            
            # Small delay between iterations
            await asyncio.sleep(2)
        else:
            logger.info(f"✅ No more pending posts found after iteration {i + 1}")
            break
    
    # Verify final state
    r2_client = R2Client(config=R2_CONFIG)
    final_content = await r2_client.read_json(test_key)
    
    if final_content:
        all_processed = all(
            value.get("status") == "processed" 
            for key, value in final_content.items() 
            if key.startswith("Post_")
        )
        
        if all_processed:
            logger.info("🎉 ALL POSTS SUCCESSFULLY PROCESSED!")
        else:
            logger.warning("⚠️ Some posts still pending")
    
    # Check next_posts output
    next_posts_objects = await r2_client.list_objects("next_posts/instagram/testuser/")
    logger.info(f"📁 Generated {len(next_posts_objects)} next_posts files")
    
    # Show sample output
    if next_posts_objects:
        sample_key = next_posts_objects[0]["Key"]
        sample_post = await r2_client.read_json(sample_key)
        
        if sample_post:
            logger.info("📄 Sample next_post output:")
            logger.info(f"Module Type: {sample_post.get('module_type')}")
            logger.info(f"Platform: {sample_post.get('platform')}")
            logger.info(f"Username: {sample_post.get('username')}")
            
            post_data = sample_post.get('post_data', {})
            logger.info(f"Caption: {post_data.get('caption', '')[:50]}...")
            logger.info(f"Hashtags: {post_data.get('hashtags', [])}")
            logger.info(f"CTA: {post_data.get('call_to_action', '')[:30]}...")

async def test_continuous_mode():
    """Test continuous processing mode for a short duration"""
    logger.info("🔄 Testing continuous processing mode for 30 seconds")
    
    handler = SequentialQueryHandler()
    
    # Run continuous processing for 30 seconds
    try:
        await asyncio.wait_for(handler.run_continuous_processing(), timeout=30)
    except asyncio.TimeoutError:
        logger.info("✅ Continuous processing test completed (30 seconds)")

async def main():
    """Run all tests"""
    logger.info("🚀 SEQUENTIAL QUERY HANDLER VALIDATION")
    
    # Test 1: Sequential processing
    await test_sequential_processing()
    
    logger.info("\n" + "="*50)
    
    # Test 2: Continuous mode (short test)
    await test_continuous_mode()
    
    logger.info("🎉 ALL TESTS COMPLETED")

if __name__ == "__main__":
    asyncio.run(main()) 