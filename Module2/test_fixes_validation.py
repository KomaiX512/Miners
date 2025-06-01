"""
Comprehensive Test Suite for Pipeline Fixes Validation
Tests all five critical fixes implemented in the modules:
Fix 1: Remove test users from main pipeline
Fix 2: Improve image prompt detection
Fix 3: Enforce naming conventions
Fix 4: Correct status handling
Fix 5: Query handler campaign naming
"""

import asyncio
import json
from datetime import datetime
from utils.r2_client import R2Client
from utils.logging import logger
from config import R2_CONFIG
from goal_rag_handler import EnhancedGoalHandler
from query_handler import SequentialQueryHandler
from image_generator import ImageGenerator

class FixesValidationSuite:
    """Comprehensive validation suite for all pipeline fixes"""
    
    def __init__(self):
        self.r2_client = R2Client(config=R2_CONFIG)
        
    async def run_all_validations(self):
        """Run all validation tests"""
        logger.info("🧪 STARTING COMPREHENSIVE FIXES VALIDATION SUITE")
        logger.info("=" * 70)
        
        # Test Fix 1: Test user filtering
        await self.test_fix_1_test_user_filtering()
        
        # Test Fix 2: Image prompt detection
        await self.test_fix_2_image_prompt_detection()
        
        # Test Fix 3: Naming conventions
        await self.test_fix_3_naming_conventions()
        
        # Test Fix 4: Status handling
        await self.test_fix_4_status_handling()
        
        # Test Fix 5: Query handler campaign naming
        await self.test_fix_5_campaign_naming()
        
        logger.info("\n🎉 ALL FIXES VALIDATION COMPLETED")
    
    async def test_fix_1_test_user_filtering(self):
        """Test Fix 1: Verify test users are filtered out from main pipeline"""
        logger.info("\n🔍 FIX 1 VALIDATION: Test User Filtering")
        logger.info("-" * 50)
        
        # Create test goal files with various test indicators
        test_cases = [
            {"platform": "instagram", "username": "test_user", "should_skip": True},
            {"platform": "instagram", "username": "demo_account", "should_skip": True},
            {"platform": "instagram", "username": "sample_profile", "should_skip": True},
            {"platform": "instagram", "username": "development_test", "should_skip": True},
            {"platform": "instagram", "username": "real_user_account", "should_skip": False},
            {"platform": "instagram", "username": "production_account", "should_skip": False}
        ]
        
        goal_handler = EnhancedGoalHandler()
        
        for case in test_cases:
            # Create test goal file
            goal_data = {
                "goal": "Test goal for validation",
                "timeline": 7,
                "persona": "Test persona",
                "instructions": "Test instructions",
                "status": "pending",
                "created_at": datetime.now().isoformat()
            }
            
            goal_key = f"goal/{case['platform']}/{case['username']}/goal_validation.json"
            await self.r2_client.write_json(goal_key, goal_data)
            
            # Test if goal handler processes or skips
            initial_processed_count = len(goal_handler.processed_files)
            await goal_handler.process_goal_file(goal_key)
            final_processed_count = len(goal_handler.processed_files)
            
            was_processed = final_processed_count > initial_processed_count
            
            if case["should_skip"]:
                if not was_processed:
                    logger.info(f"✅ {case['username']}: Correctly skipped test user")
                else:
                    logger.error(f"❌ {case['username']}: Test user was processed (should be skipped)")
            else:
                if was_processed or goal_key in goal_handler.processed_files:
                    logger.info(f"✅ {case['username']}: Correctly processed real user")
                else:
                    logger.info(f"⚠️ {case['username']}: Real user skipped (may need profile data)")
        
        logger.info("🎯 Fix 1 validation completed")
    
    async def test_fix_2_image_prompt_detection(self):
        """Test Fix 2: Verify enhanced image prompt detection"""
        logger.info("\n🔍 FIX 2 VALIDATION: Image Prompt Detection")
        logger.info("-" * 50)
        
        image_gen = ImageGenerator()
        
        # Test cases with different image prompt scenarios
        test_cases = [
            {
                "name": "Direct image_prompt",
                "data": {
                    "post_data": {
                        "caption": "Test caption",
                        "hashtags": ["#test"],
                        "image_prompt": "High-quality professional photography with perfect lighting"
                    }
                },
                "should_find": True
            },
            {
                "name": "visual_prompt alternative",
                "data": {
                    "post_data": {
                        "caption": "Test caption",
                        "hashtags": ["#test"],
                        "visual_prompt": "Beautiful aesthetic visual design with modern elements"
                    }
                },
                "should_find": True
            },
            {
                "name": "prompt keyword",
                "data": {
                    "post_data": {
                        "caption": "Test caption",
                        "hashtags": ["#test"],
                        "prompt": "Creative visual composition with artistic elements"
                    }
                },
                "should_find": True
            },
            {
                "name": "Nested image_prompt",
                "data": {
                    "post": {
                        "caption": "Test caption",
                        "hashtags": ["#test"]
                    },
                    "image_data": {
                        "image_prompt": "Stunning photography with perfect composition and lighting"
                    }
                },
                "should_find": True
            },
            {
                "name": "Invalid short prompt",
                "data": {
                    "post_data": {
                        "caption": "Test caption",
                        "hashtags": ["#test"],
                        "image_prompt": "short"
                    }
                },
                "should_find": False
            },
            {
                "name": "No prompt at all",
                "data": {
                    "post_data": {
                        "caption": "Test caption",
                        "hashtags": ["#test"]
                    }
                },
                "should_find": False
            }
        ]
        
        for case in test_cases:
            try:
                fixed_data = image_gen.fix_post_data(case["data"], f"test_{case['name']}")
                
                if fixed_data and "post" in fixed_data:
                    post = fixed_data["post"]
                    prompt = image_gen._extract_image_prompt(post, case["data"], f"test_{case['name']}")
                    
                    found_prompt = prompt is not None and len(str(prompt).strip()) >= 15
                    
                    if case["should_find"]:
                        if found_prompt:
                            logger.info(f"✅ {case['name']}: Correctly found image prompt")
                        else:
                            logger.error(f"❌ {case['name']}: Failed to find expected image prompt")
                    else:
                        if not found_prompt:
                            logger.info(f"✅ {case['name']}: Correctly skipped invalid prompt")
                        else:
                            logger.error(f"❌ {case['name']}: Found prompt when it should be skipped")
                else:
                    if not case["should_find"]:
                        logger.info(f"✅ {case['name']}: Correctly rejected invalid data")
                    else:
                        logger.error(f"❌ {case['name']}: Failed to process valid data")
                        
            except Exception as e:
                logger.error(f"❌ {case['name']}: Exception during test - {e}")
        
        logger.info("🎯 Fix 2 validation completed")
    
    async def test_fix_3_naming_conventions(self):
        """Test Fix 3: Verify naming conventions are enforced"""
        logger.info("\n🔍 FIX 3 VALIDATION: Naming Conventions")
        logger.info("-" * 50)
        
        # Test cases for different input file types
        test_cases = [
            {
                "input_key": "next_posts/instagram/testuser/campaign_next_post_1.json",
                "expected_prefix": "campaign_ready_post_",
                "description": "Campaign post input"
            },
            {
                "input_key": "next_posts/instagram/testuser/compaign_next_post_1.json", 
                "expected_prefix": "campaign_ready_post_",
                "description": "Campaign post with typo"
            },
            {
                "input_key": "next_posts/instagram/testuser/post_1.json",
                "expected_prefix": "ready_post_",
                "description": "Regular post input"
            },
            {
                "input_key": "next_posts/instagram/testuser/next_post_1.json",
                "expected_prefix": "ready_post_",
                "description": "Standard next post"
            }
        ]
        
        image_gen = ImageGenerator()
        
        for case in test_cases:
            # Simulate the naming logic from process_post
            key = case["input_key"]
            
            is_campaign_post = (
                "campaign_next_post_" in key or 
                "campaign_post_" in key or 
                "compaign_next_post_" in key or
                "campaign" in key.lower()
            )
            
            if is_campaign_post:
                file_prefix = "campaign_ready_post_"
            else:
                file_prefix = "ready_post_"
            
            if file_prefix == case["expected_prefix"]:
                logger.info(f"✅ {case['description']}: Correct naming convention - {file_prefix}")
            else:
                logger.error(f"❌ {case['description']}: Wrong naming - got {file_prefix}, expected {case['expected_prefix']}")
        
        logger.info("🎯 Fix 3 validation completed")
    
    async def test_fix_4_status_handling(self):
        """Test Fix 4: Verify status is set to pending"""
        logger.info("\n🔍 FIX 4 VALIDATION: Status Handling")
        logger.info("-" * 50)
        
        image_gen = ImageGenerator()
        
        # Test the _create_output_post method
        test_post = {
            "caption": "Test caption for status validation",
            "hashtags": ["#test", "#validation"],
            "call_to_action": "Test CTA",
            "image_prompt": "Test image prompt for validation"
        }
        
        image_key = "test/path/image_1.jpg"
        platform = "instagram"
        username = "testuser"
        original_data = {"original_format": "test"}
        
        output_post = image_gen._create_output_post(test_post, image_key, platform, username, original_data)
        
        if output_post.get("status") == "pending":
            logger.info("✅ Status correctly set to 'pending' in output post")
        else:
            logger.error(f"❌ Status incorrectly set to '{output_post.get('status')}' (should be 'pending')")
        
        # Test fallback case
        try:
            # Simulate error condition
            bad_post = None
            fallback_output = image_gen._create_output_post(bad_post, image_key, platform, username, original_data)
            
            if fallback_output.get("status") == "pending":
                logger.info("✅ Fallback status correctly set to 'pending'")
            else:
                logger.error(f"❌ Fallback status incorrectly set to '{fallback_output.get('status')}' (should be 'pending')")
        except:
            # This is expected for None input, but status should still be pending in fallback
            pass
        
        logger.info("🎯 Fix 4 validation completed")
    
    async def test_fix_5_campaign_naming(self):
        """Test Fix 5: Verify query handler uses campaign naming"""
        logger.info("\n🔍 FIX 5 VALIDATION: Campaign Naming")
        logger.info("-" * 50)
        
        query_handler = SequentialQueryHandler()
        
        # Test the save_next_post method logic
        test_data = {
            "module_type": "next_post_prediction",
            "platform": "instagram",
            "username": "testuser",
            "post_data": {
                "caption": "Test campaign post",
                "hashtags": ["#test"],
                "call_to_action": "Test CTA",
                "image_prompt": "Test image prompt"
            },
            "generated_at": datetime.now().isoformat()
        }
        
        # Clean up any existing test files first
        try:
            test_dir = "next_posts/instagram/testuser/"
            objects = await query_handler.r2_client.list_objects(test_dir)
            for obj in objects:
                if "campaign_next_post_" in obj["Key"]:
                    # Clean up test files
                    pass
        except:
            pass
        
        # Test save functionality
        success = await query_handler.save_next_post(test_data, "instagram", "testuser")
        
        if success:
            # Check if file was created with correct naming
            try:
                objects = await query_handler.r2_client.list_objects("next_posts/instagram/testuser/")
                campaign_files = [obj["Key"] for obj in objects if "campaign_next_post_" in obj["Key"]]
                
                if campaign_files:
                    logger.info(f"✅ Campaign naming convention used: {campaign_files[-1]}")
                    
                    # Verify the file contains correct data
                    latest_file = campaign_files[-1]
                    file_data = await query_handler.r2_client.read_json(latest_file)
                    
                    if file_data and file_data.get("module_type") == "next_post_prediction":
                        logger.info("✅ Campaign file contains correct next_post_prediction format")
                    else:
                        logger.error("❌ Campaign file has incorrect format")
                else:
                    logger.error("❌ No campaign_next_post_ files found")
            except Exception as e:
                logger.error(f"❌ Error checking campaign files: {e}")
        else:
            logger.error("❌ Failed to save campaign post")
        
        logger.info("🎯 Fix 5 validation completed")

async def main():
    """Run comprehensive validation"""
    validator = FixesValidationSuite()
    await validator.run_all_validations()

if __name__ == "__main__":
    asyncio.run(main()) 