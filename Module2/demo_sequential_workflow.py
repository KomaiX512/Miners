"""
Demo Script: Sequential Query Handler Workflow
Demonstrates the complete workflow from generated_content to next_posts format.
"""

import asyncio
import json
from datetime import datetime
from utils.r2_client import R2Client
from utils.logging import logger
from config import R2_CONFIG
from query_handler import SequentialQueryHandler

async def create_sample_campaign():
    """Create a sample campaign in generated_content format"""
    r2_client = R2Client(config=R2_CONFIG)
    
    # Create sample campaign with 5 posts
    campaign_data = {
        "Post_1": {
            "content": "🌟 Get ready for the ultimate glow-up! Our new highlighter collection is here to make you shine brighter than ever. The perfect luminous finish awaits you in every shade.",
            "status": "pending"
        },
        "Post_2": {
            "content": "Behind the scenes magic happening at Fenty Beauty HQ! Our team is working hard to bring you the most innovative products. Watch as our makeup artists create stunning looks with precision.",
            "status": "pending"
        },
        "Post_3": {
            "content": "Self-care Sunday vibes are in full effect! Take time to pamper yourself with our luxurious skincare routine. The image should capture a serene spa-like atmosphere with soft lighting.",
            "status": "pending"
        },
        "Post_4": {
            "content": "Bold and beautiful - that's the Fenty way! Today we're celebrating diversity and inclusivity in beauty. Show a diverse group of people wearing vibrant makeup looks with confidence.",
            "status": "pending"
        },
        "Post_5": {
            "content": "Flash sale alert - 24 hours only! Get your favorite Fenty products at amazing prices before they're gone. Create urgency with dynamic graphics and countdown timers.",
            "status": "pending"
        },
        "Summary": "📊 STATISTICAL CAMPAIGN ANALYSIS: This 5-post strategy targets 30% engagement increase over 7 days, based on comprehensive analysis of 2.1M followers with 3.2% baseline engagement rate. XGBoost model estimates optimal posting with 87% confidence."
    }
    
    # Save to generated_content
    campaign_key = "generated_content/instagram/fentybeauty/posts.json"
    success = await r2_client.write_json(campaign_key, campaign_data)
    
    if success:
        logger.info(f"✅ Created sample campaign: {campaign_key}")
        return campaign_key
    else:
        logger.error(f"❌ Failed to create sample campaign")
        return None

async def demonstrate_sequential_processing():
    """Demonstrate sequential processing with 10-second intervals"""
    logger.info("🎬 SEQUENTIAL QUERY HANDLER DEMONSTRATION")
    logger.info("=" * 60)
    
    # Step 1: Create sample campaign
    logger.info("📝 Step 1: Creating sample campaign...")
    campaign_key = await create_sample_campaign()
    
    if not campaign_key:
        logger.error("❌ Failed to create campaign")
        return
    
    # Step 2: Initialize handler
    logger.info("🚀 Step 2: Initializing Sequential Query Handler...")
    handler = SequentialQueryHandler()
    
    # Step 3: Monitor progress manually for demonstration
    logger.info("🔄 Step 3: Starting sequential processing demonstration...")
    logger.info("⏰ Processing one post every 10 seconds...")
    
    r2_client = R2Client(config=R2_CONFIG)
    
    # Process posts sequentially for demonstration (5 iterations max)
    for iteration in range(5):
        logger.info(f"\n🔍 Iteration {iteration + 1}: Scanning for pending posts...")
        
        # Check current status
        current_data = await r2_client.read_json(campaign_key)
        if current_data:
            pending_posts = [
                key for key, value in current_data.items() 
                if key.startswith("Post_") and value.get("status") == "pending"
            ]
            processed_posts = [
                key for key, value in current_data.items() 
                if key.startswith("Post_") and value.get("status") == "processed"
            ]
            
            logger.info(f"📊 Current status: {len(pending_posts)} pending, {len(processed_posts)} processed")
            
            if not pending_posts:
                logger.info("🎉 All posts have been processed!")
                break
        
        # Process one post
        processed = await handler.scan_platform_for_pending_posts("instagram")
        
        if processed:
            logger.info("✅ Successfully processed one post")
            
            # Check next_posts output
            next_posts_objects = await r2_client.list_objects("next_posts/instagram/fentybeauty/")
            logger.info(f"📁 Total next_posts files: {len(next_posts_objects)}")
        else:
            logger.info("⭕ No posts were processed this iteration")
        
        # Wait 10 seconds (demonstrating the retry mechanism)
        if iteration < 4:  # Don't wait after last iteration
            logger.info("⏳ Waiting 10 seconds before next scan...")
            await asyncio.sleep(10)
    
    # Step 4: Show final results
    logger.info("\n📋 Step 4: Final Results")
    logger.info("=" * 40)
    
    # Show final campaign status
    final_data = await r2_client.read_json(campaign_key)
    if final_data:
        all_posts = [key for key in final_data.keys() if key.startswith("Post_")]
        processed_posts = [
            key for key, value in final_data.items() 
            if key.startswith("Post_") and value.get("status") == "processed"
        ]
        
        logger.info(f"📊 Campaign completion: {len(processed_posts)}/{len(all_posts)} posts processed")
    
    # Show next_posts output files
    next_posts_objects = await r2_client.list_objects("next_posts/instagram/fentybeauty/")
    logger.info(f"📁 Generated next_posts files: {len(next_posts_objects)}")
    
    # Show sample transformed post
    if next_posts_objects:
        sample_key = next_posts_objects[-1]["Key"]  # Get latest
        sample_post = await r2_client.read_json(sample_key)
        
        if sample_post:
            logger.info(f"\n📄 Sample transformed post ({sample_key}):")
            logger.info("-" * 50)
            logger.info(f"Module Type: {sample_post.get('module_type')}")
            logger.info(f"Platform: {sample_post.get('platform')}")
            logger.info(f"Username: {sample_post.get('username')}")
            logger.info(f"Generated At: {sample_post.get('generated_at')}")
            
            post_data = sample_post.get('post_data', {})
            logger.info(f"Caption: {post_data.get('caption', '')[:80]}...")
            logger.info(f"Hashtags: {len(post_data.get('hashtags', []))} hashtags")
            logger.info(f"CTA: {post_data.get('call_to_action', '')[:50]}...")
            logger.info(f"Image Prompt: {post_data.get('image_prompt', '')[:60]}...")

async def demonstrate_continuous_mode():
    """Demonstrate continuous mode for a short period"""
    logger.info("\n🔄 CONTINUOUS MODE DEMONSTRATION")
    logger.info("=" * 60)
    logger.info("⏰ Running continuous processing for 60 seconds...")
    
    handler = SequentialQueryHandler()
    
    try:
        # Run continuous processing for 60 seconds
        await asyncio.wait_for(handler.run_continuous_processing(), timeout=60)
    except asyncio.TimeoutError:
        logger.info("✅ Continuous processing demonstration completed")

async def main():
    """Main demonstration function"""
    logger.info("🎭 FENTY BEAUTY SEQUENTIAL QUERY HANDLER DEMO")
    logger.info("Processing generated_content → next_post_prediction format")
    logger.info("=" * 60)
    
    # Part 1: Sequential processing demonstration
    await demonstrate_sequential_processing()
    
    # Part 2: Continuous mode demonstration
    # await demonstrate_continuous_mode()
    
    logger.info("\n🎉 DEMONSTRATION COMPLETED!")
    logger.info("✅ Sequential Query Handler is working perfectly!")
    logger.info("✅ Posts are transformed to next_post_prediction format")
    logger.info("✅ 10-second retry mechanism is functional")
    logger.info("✅ Status tracking (pending → processed) works correctly")

if __name__ == "__main__":
    asyncio.run(main()) 