"""
System Status Overview
Shows the current state of the Sequential Query Handler system.
"""

import asyncio
import json
from datetime import datetime
from utils.r2_client import R2Client
from utils.logging import logger
from config import R2_CONFIG

class SystemStatus:
    """System status checker for Sequential Query Handler"""
    
    def __init__(self):
        self.r2_client = R2Client(config=R2_CONFIG)
        self.platforms = ["instagram", "twitter", "facebook"]
    
    async def check_system_status(self):
        """Check overall system status"""
        logger.info("🔍 SEQUENTIAL QUERY HANDLER - SYSTEM STATUS")
        logger.info("=" * 60)
        
        # Check generated_content files
        await self.check_generated_content()
        
        logger.info("")
        
        # Check next_posts output
        await self.check_next_posts_output()
        
        logger.info("")
        
        # Check processing status
        await self.check_processing_status()
    
    async def check_generated_content(self):
        """Check generated_content directory for pending posts"""
        logger.info("📂 GENERATED CONTENT STATUS")
        logger.info("-" * 40)
        
        total_campaigns = 0
        total_pending = 0
        total_processed = 0
        
        for platform in self.platforms:
            platform_prefix = f"generated_content/{platform}/"
            
            try:
                objects = await self.r2_client.list_objects(platform_prefix)
                posts_files = [obj["Key"] for obj in objects if obj["Key"].endswith("posts.json")]
                
                logger.info(f"📱 {platform.upper()}: {len(posts_files)} campaigns")
                
                for posts_file in posts_files:
                    username = posts_file.split('/')[2]  # Extract username
                    
                    try:
                        data = await self.r2_client.read_json(posts_file)
                        if data:
                            pending_posts = [
                                key for key, value in data.items() 
                                if key.startswith("Post_") and value.get("status") == "pending"
                            ]
                            processed_posts = [
                                key for key, value in data.items() 
                                if key.startswith("Post_") and value.get("status") == "processed"
                            ]
                            
                            total_campaigns += 1
                            total_pending += len(pending_posts)
                            total_processed += len(processed_posts)
                            
                            if pending_posts:
                                logger.info(f"  🔄 {username}: {len(pending_posts)} pending, {len(processed_posts)} processed")
                            else:
                                logger.info(f"  ✅ {username}: All {len(processed_posts)} posts processed")
                    
                    except Exception as e:
                        logger.warning(f"  ⚠️ {username}: Error reading file - {e}")
                        
            except Exception as e:
                logger.error(f"❌ Error checking {platform}: {e}")
        
        logger.info(f"\n📊 SUMMARY: {total_campaigns} campaigns, {total_pending} pending, {total_processed} processed")
    
    async def check_next_posts_output(self):
        """Check next_posts output directory"""
        logger.info("📤 NEXT_POSTS OUTPUT STATUS")
        logger.info("-" * 40)
        
        total_output_files = 0
        
        for platform in self.platforms:
            platform_prefix = f"next_posts/{platform}/"
            
            try:
                objects = await self.r2_client.list_objects(platform_prefix)
                
                # Group by username
                username_groups = {}
                for obj in objects:
                    parts = obj["Key"].split('/')
                    if len(parts) >= 4:
                        username = parts[2]
                        if username not in username_groups:
                            username_groups[username] = []
                        username_groups[username].append(obj["Key"])
                
                logger.info(f"📱 {platform.upper()}: {len(username_groups)} users with output")
                
                for username, files in username_groups.items():
                    post_files = [f for f in files if "post_" in f and f.endswith(".json")]
                    total_output_files += len(post_files)
                    logger.info(f"  📝 {username}: {len(post_files)} transformed posts")
                    
            except Exception as e:
                logger.error(f"❌ Error checking {platform} output: {e}")
        
        logger.info(f"\n📊 TOTAL OUTPUT FILES: {total_output_files}")
    
    async def check_processing_status(self):
        """Check recent processing activity"""
        logger.info("⚡ RECENT ACTIVITY")
        logger.info("-" * 40)
        
        try:
            # Check latest next_posts files across all platforms
            latest_files = []
            
            for platform in self.platforms:
                platform_prefix = f"next_posts/{platform}/"
                
                try:
                    objects = await self.r2_client.list_objects(platform_prefix)
                    for obj in objects:
                        if "post_" in obj["Key"] and obj["Key"].endswith(".json"):
                            latest_files.append(obj)
                except:
                    continue
            
            # Sort by last modified (if available) or by filename
            latest_files.sort(key=lambda x: x["Key"], reverse=True)
            
            if latest_files:
                logger.info("🕒 Latest processed posts:")
                
                for file_obj in latest_files[:5]:  # Show last 5
                    key = file_obj["Key"]
                    parts = key.split('/')
                    
                    if len(parts) >= 4:
                        platform = parts[1]
                        username = parts[2]
                        filename = parts[3]
                        
                        # Try to read the file to get timestamp
                        try:
                            data = await self.r2_client.read_json(key)
                            if data and "generated_at" in data:
                                timestamp = data["generated_at"]
                                logger.info(f"  📝 {platform}/{username}/{filename} - {timestamp}")
                            else:
                                logger.info(f"  📝 {platform}/{username}/{filename}")
                        except:
                            logger.info(f"  📝 {platform}/{username}/{filename}")
            else:
                logger.info("🔍 No recent activity found")
                
        except Exception as e:
            logger.error(f"❌ Error checking recent activity: {e}")
    
    async def show_sample_transformation(self):
        """Show a sample transformation to verify format"""
        logger.info("\n📄 SAMPLE TRANSFORMATION")
        logger.info("-" * 40)
        
        try:
            # Find a recent next_posts file
            objects = await self.r2_client.list_objects("next_posts/")
            
            if objects:
                sample_key = objects[-1]["Key"]  # Get latest
                sample_data = await self.r2_client.read_json(sample_key)
                
                if sample_data:
                    logger.info(f"File: {sample_key}")
                    logger.info(f"Module Type: {sample_data.get('module_type')}")
                    logger.info(f"Platform: {sample_data.get('platform')}")
                    logger.info(f"Username: {sample_data.get('username')}")
                    logger.info(f"Generated: {sample_data.get('generated_at')}")
                    
                    post_data = sample_data.get('post_data', {})
                    logger.info(f"Caption: {post_data.get('caption', '')[:60]}...")
                    logger.info(f"Hashtags: {len(post_data.get('hashtags', []))} tags")
                    logger.info(f"✅ Format is correct!")
                else:
                    logger.warning("⚠️ Could not read sample file")
            else:
                logger.info("📭 No output files found")
                
        except Exception as e:
            logger.error(f"❌ Error showing sample: {e}")

async def main():
    """Main status check"""
    status_checker = SystemStatus()
    
    await status_checker.check_system_status()
    await status_checker.show_sample_transformation()
    
    logger.info("\n🎯 SYSTEM STATUS CHECK COMPLETE")

if __name__ == "__main__":
    asyncio.run(main()) 