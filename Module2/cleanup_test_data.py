"""
Test Data Cleanup Utility
Comprehensive cleanup of all test data from the production pipeline.
Removes test files, test users, and test campaigns from all buckets.
"""

import asyncio
import json
from typing import List, Dict, Any
from utils.r2_client import R2Client
from utils.logging import logger
from utils.test_filter import TestFilter
from config import R2_CONFIG, STRUCTUREDB_R2_CONFIG

class TestDataCleanup:
    """Comprehensive test data cleanup utility"""
    
    def __init__(self):
        self.r2_tasks = R2Client(config=R2_CONFIG)
        self.r2_structuredb = R2Client(config=STRUCTUREDB_R2_CONFIG)
        self.cleanup_stats = {
            "goal_files": 0,
            "generated_content": 0,
            "next_posts": 0,
            "ready_posts": 0,
            "test_profiles": 0,
            "total_cleaned": 0
        }
    
    async def cleanup_all_test_data(self):
        """Perform comprehensive cleanup of all test data"""
        logger.info("🧹 STARTING COMPREHENSIVE TEST DATA CLEANUP")
        logger.info("=" * 60)
        
        # Cleanup from tasks bucket
        await self.cleanup_goal_files()
        await self.cleanup_generated_content()
        await self.cleanup_next_posts()
        await self.cleanup_ready_posts()
        
        # Cleanup from structuredb bucket
        await self.cleanup_test_profiles()
        
        # Report statistics
        self.report_cleanup_statistics()
        
        logger.info("🎉 TEST DATA CLEANUP COMPLETED")
    
    async def cleanup_goal_files(self):
        """Clean up test goal files"""
        logger.info("\n🔍 Cleaning up test goal files...")
        
        prefixes = ["goal/instagram/", "goal/twitter/"]
        
        for prefix in prefixes:
            try:
                objects = await self.r2_tasks.list_objects(prefix)
                test_objects = []
                
                for obj in objects:
                    key = obj["Key"]
                    if TestFilter.is_test_data(key, "goal_file"):
                        test_objects.append(obj)
                
                logger.info(f"📁 Found {len(test_objects)} test goal files in {prefix}")
                
                for obj in test_objects:
                    key = obj["Key"]
                    try:
                        success = await self.r2_tasks.delete_object(key)
                        if success:
                            logger.info(f"🗑️ Deleted test goal file: {key}")
                            self.cleanup_stats["goal_files"] += 1
                        else:
                            logger.warning(f"⚠️ Failed to delete: {key}")
                    except Exception as e:
                        logger.error(f"❌ Error deleting {key}: {e}")
                        
            except Exception as e:
                logger.error(f"❌ Error cleaning {prefix}: {e}")
    
    async def cleanup_generated_content(self):
        """Clean up test generated content"""
        logger.info("\n🔍 Cleaning up test generated content...")
        
        prefixes = ["generated_content/instagram/", "generated_content/twitter/"]
        
        for prefix in prefixes:
            try:
                objects = await self.r2_tasks.list_objects(prefix)
                test_objects = []
                
                for obj in objects:
                    key = obj["Key"]
                    if TestFilter.is_test_data(key, "generated_content"):
                        test_objects.append(obj)
                
                logger.info(f"📁 Found {len(test_objects)} test generated content files in {prefix}")
                
                for obj in test_objects:
                    key = obj["Key"]
                    try:
                        success = await self.r2_tasks.delete_object(key)
                        if success:
                            logger.info(f"🗑️ Deleted test content: {key}")
                            self.cleanup_stats["generated_content"] += 1
                        else:
                            logger.warning(f"⚠️ Failed to delete: {key}")
                    except Exception as e:
                        logger.error(f"❌ Error deleting {key}: {e}")
                        
            except Exception as e:
                logger.error(f"❌ Error cleaning {prefix}: {e}")
    
    async def cleanup_next_posts(self):
        """Clean up test next_posts"""
        logger.info("\n🔍 Cleaning up test next_posts...")
        
        prefixes = ["next_posts/instagram/", "next_posts/twitter/"]
        
        for prefix in prefixes:
            try:
                objects = await self.r2_tasks.list_objects(prefix)
                test_objects = []
                
                for obj in objects:
                    key = obj["Key"]
                    if TestFilter.is_test_data(key, "next_posts"):
                        test_objects.append(obj)
                
                logger.info(f"📁 Found {len(test_objects)} test next_posts in {prefix}")
                
                for obj in test_objects:
                    key = obj["Key"]
                    try:
                        success = await self.r2_tasks.delete_object(key)
                        if success:
                            logger.info(f"🗑️ Deleted test next_post: {key}")
                            self.cleanup_stats["next_posts"] += 1
                        else:
                            logger.warning(f"⚠️ Failed to delete: {key}")
                    except Exception as e:
                        logger.error(f"❌ Error deleting {key}: {e}")
                        
            except Exception as e:
                logger.error(f"❌ Error cleaning {prefix}: {e}")
    
    async def cleanup_ready_posts(self):
        """Clean up test ready_posts from structuredb"""
        logger.info("\n🔍 Cleaning up test ready_posts...")
        
        prefixes = ["ready_post/instagram/", "ready_post/twitter/"]
        
        for prefix in prefixes:
            try:
                objects = await self.r2_structuredb.list_objects(prefix)
                test_objects = []
                
                for obj in objects:
                    key = obj["Key"]
                    if TestFilter.is_test_data(key, "ready_posts"):
                        test_objects.append(obj)
                
                logger.info(f"📁 Found {len(test_objects)} test ready_posts in {prefix}")
                
                for obj in test_objects:
                    key = obj["Key"]
                    try:
                        success = await self.r2_structuredb.delete_object(key)
                        if success:
                            logger.info(f"🗑️ Deleted test ready_post: {key}")
                            self.cleanup_stats["ready_posts"] += 1
                        else:
                            logger.warning(f"⚠️ Failed to delete: {key}")
                    except Exception as e:
                        logger.error(f"❌ Error deleting {key}: {e}")
                        
            except Exception as e:
                logger.error(f"❌ Error cleaning {prefix}: {e}")
    
    async def cleanup_test_profiles(self):
        """Clean up test profiles from structuredb"""
        logger.info("\n🔍 Cleaning up test profiles...")
        
        prefixes = ["instagram/", "twitter/"]
        
        for prefix in prefixes:
            try:
                objects = await self.r2_structuredb.list_objects(prefix)
                test_objects = []
                
                for obj in objects:
                    key = obj["Key"]
                    if TestFilter.is_test_data(key, "profile"):
                        test_objects.append(obj)
                
                logger.info(f"📁 Found {len(test_objects)} test profiles in {prefix}")
                
                for obj in test_objects:
                    key = obj["Key"]
                    try:
                        success = await self.r2_structuredb.delete_object(key)
                        if success:
                            logger.info(f"🗑️ Deleted test profile: {key}")
                            self.cleanup_stats["test_profiles"] += 1
                        else:
                            logger.warning(f"⚠️ Failed to delete: {key}")
                    except Exception as e:
                        logger.error(f"❌ Error deleting {key}: {e}")
                        
            except Exception as e:
                logger.error(f"❌ Error cleaning {prefix}: {e}")
    
    async def preview_cleanup(self):
        """Preview what would be cleaned up without actually deleting"""
        logger.info("🔍 PREVIEW MODE: Scanning for test data...")
        logger.info("=" * 50)
        
        # Preview from tasks bucket
        await self.preview_bucket_cleanup(self.r2_tasks, [
            "goal/instagram/", "goal/twitter/",
            "generated_content/instagram/", "generated_content/twitter/",
            "next_posts/instagram/", "next_posts/twitter/"
        ])
        
        # Preview from structuredb bucket
        await self.preview_bucket_cleanup(self.r2_structuredb, [
            "ready_post/instagram/", "ready_post/twitter/",
            "instagram/", "twitter/"
        ])
    
    async def preview_bucket_cleanup(self, r2_client: R2Client, prefixes: List[str]):
        """Preview cleanup for a specific bucket"""
        for prefix in prefixes:
            try:
                objects = await r2_client.list_objects(prefix)
                test_objects = [obj for obj in objects if TestFilter.is_test_data(obj["Key"])]
                
                logger.info(f"📁 {prefix}: {len(test_objects)} test files would be deleted")
                
                for obj in test_objects[:5]:  # Show first 5 examples
                    logger.info(f"   - {obj['Key']}")
                if len(test_objects) > 5:
                    logger.info(f"   ... and {len(test_objects) - 5} more")
                    
            except Exception as e:
                logger.error(f"❌ Error previewing {prefix}: {e}")
    
    def report_cleanup_statistics(self):
        """Report cleanup statistics"""
        logger.info("\n📊 CLEANUP STATISTICS")
        logger.info("=" * 40)
        
        total = sum(self.cleanup_stats.values())
        
        for category, count in self.cleanup_stats.items():
            if category != "total_cleaned" and count > 0:
                logger.info(f"🗑️ {category.replace('_', ' ').title()}: {count} files")
        
        logger.info(f"✅ Total test files cleaned: {total}")
        
        if total == 0:
            logger.info("🎉 No test data found - pipeline is clean!")
        else:
            logger.info("🎉 Pipeline successfully cleaned of test data!")

async def main():
    """Main cleanup execution"""
    cleanup = TestDataCleanup()
    
    # Preview mode first
    logger.info("Starting in preview mode...")
    await cleanup.preview_cleanup()
    
    # Ask for confirmation (in actual use, you might want user input)
    logger.info("\nStarting actual cleanup...")
    await cleanup.cleanup_all_test_data()

if __name__ == "__main__":
    asyncio.run(main()) 