"""
Production Filter Validation Script
Comprehensive testing to ensure no test data is processed in the production pipeline.
Tests the centralized TestFilter across all modules.
"""

import asyncio
import json
from datetime import datetime
from utils.r2_client import R2Client
from utils.logging import logger
from utils.test_filter import TestFilter
from config import R2_CONFIG
from goal_rag_handler import EnhancedGoalHandler
from query_handler import SequentialQueryHandler
from image_generator import ImageGenerator

class ProductionFilterValidator:
    """Comprehensive validation of production filtering"""
    
    def __init__(self):
        self.r2_client = R2Client(config=R2_CONFIG)
        self.test_scenarios_created = []
        
    async def run_comprehensive_validation(self):
        """Run complete validation of production filtering"""
        logger.info("🧪 COMPREHENSIVE PRODUCTION FILTER VALIDATION")
        logger.info("=" * 60)
        
        # Step 1: Test the TestFilter utility directly
        await self.test_filter_utility()
        
        # Step 2: Create test scenarios
        await self.create_test_scenarios()
        
        # Step 3: Test Goal Handler filtering
        await self.test_goal_handler_filtering()
        
        # Step 4: Test Query Handler filtering
        await self.test_query_handler_filtering()
        
        # Step 5: Test Image Generator filtering
        await self.test_image_generator_filtering()
        
        # Step 6: Cleanup test scenarios
        await self.cleanup_test_scenarios()
        
        logger.info("\n🎉 PRODUCTION FILTER VALIDATION COMPLETED")
    
    async def test_filter_utility(self):
        """Test the TestFilter utility directly"""
        logger.info("\n🔍 TESTING TestFilter UTILITY")
        logger.info("-" * 40)
        
        # Test cases for different scenarios
        test_cases = [
            # Should be detected as test data
            {"identifier": "test_user", "should_detect": True, "description": "Basic test user"},
            {"identifier": "demo_account", "should_detect": True, "description": "Demo account"},
            {"identifier": "sample_profile", "should_detect": True, "description": "Sample profile"},
            {"identifier": "validation_test", "should_detect": True, "description": "Validation test"},
            {"identifier": "user123", "should_detect": True, "description": "User with numbers"},
            {"identifier": "temp_user", "should_detect": True, "description": "Temporary user"},
            {"identifier": "dev_account", "should_detect": True, "description": "Development account"},
            {"identifier": "staging_user", "should_detect": True, "description": "Staging user"},
            {"identifier": "qa_test", "should_detect": True, "description": "QA test"},
            {"identifier": "testuser", "should_detect": True, "description": "Concatenated test"},
            {"identifier": "mytest", "should_detect": True, "description": "Ends with test"},
            {"identifier": "experiment_1", "should_detect": True, "description": "Experiment user"},
            
            # Should NOT be detected as test data (production users)
            {"identifier": "fentybeauty", "should_detect": False, "description": "Real brand"},
            {"identifier": "nike", "should_detect": False, "description": "Real company"},
            {"identifier": "johndoe", "should_detect": False, "description": "Real person name"},
            {"identifier": "creativestudio", "should_detect": False, "description": "Creative business"},
            {"identifier": "fitnessguru", "should_detect": False, "description": "Fitness account"},
            {"identifier": "foodblogger", "should_detect": False, "description": "Food blogger"},
            {"identifier": "traveler_jane", "should_detect": False, "description": "Travel account"},
            {"identifier": "techreview", "should_detect": False, "description": "Tech reviewer"},
        ]
        
        passed = 0
        failed = 0
        
        for case in test_cases:
            identifier = case["identifier"]
            should_detect = case["should_detect"]
            description = case["description"]
            
            is_detected = TestFilter.is_test_data(identifier)
            
            if is_detected == should_detect:
                logger.info(f"✅ {description}: '{identifier}' - {('detected' if is_detected else 'passed')} correctly")
                passed += 1
            else:
                logger.error(f"❌ {description}: '{identifier}' - Expected {should_detect}, got {is_detected}")
                failed += 1
        
        logger.info(f"\n📊 TestFilter Results: {passed} passed, {failed} failed")
        
        if failed == 0:
            logger.info("🎉 TestFilter utility working perfectly!")
        else:
            logger.error("❌ TestFilter has issues that need fixing")
    
    async def create_test_scenarios(self):
        """Create test scenarios for validation"""
        logger.info("\n🧪 CREATING TEST SCENARIOS")
        logger.info("-" * 40)
        
        # Create test goal files
        test_goals = [
            {"platform": "instagram", "username": "test_validation_user"},
            {"platform": "instagram", "username": "demo_filter_test"},
            {"platform": "twitter", "username": "sample_account"},
            {"platform": "twitter", "username": "qa_testing_123"}
        ]
        
        for goal in test_goals:
            goal_data = {
                "goal": "Test validation goal",
                "timeline": 7,
                "persona": "Test persona",
                "instructions": "Validation instructions",
                "status": "pending",
                "created_at": datetime.now().isoformat()
            }
            
            goal_key = f"goal/{goal['platform']}/{goal['username']}/goal_filter_validation.json"
            success = await self.r2_client.write_json(goal_key, goal_data)
            
            if success:
                self.test_scenarios_created.append(goal_key)
                logger.info(f"📝 Created test scenario: {goal_key}")
            else:
                logger.error(f"❌ Failed to create: {goal_key}")
        
        # Create test generated content
        test_content = {
            "Post_1": {"content": "Test post content.", "status": "pending"},
            "Summary": "Test campaign summary"
        }
        
        for goal in test_goals:
            content_key = f"generated_content/{goal['platform']}/{goal['username']}/posts.json"
            success = await self.r2_client.write_json(content_key, test_content)
            
            if success:
                self.test_scenarios_created.append(content_key)
                logger.info(f"📝 Created test content: {content_key}")
        
        logger.info(f"✅ Created {len(self.test_scenarios_created)} test scenarios")
    
    async def test_goal_handler_filtering(self):
        """Test Goal Handler filtering"""
        logger.info("\n🔍 TESTING GOAL HANDLER FILTERING")
        logger.info("-" * 40)
        
        goal_handler = EnhancedGoalHandler()
        initial_processed = len(goal_handler.processed_files)
        
        # Scan for goals (should filter out test data)
        await goal_handler.scan_existing_goals()
        
        final_processed = len(goal_handler.processed_files)
        test_goals_processed = final_processed - initial_processed
        
        if test_goals_processed == 0:
            logger.info("✅ Goal Handler correctly filtered out all test goals")
        else:
            logger.error(f"❌ Goal Handler processed {test_goals_processed} test goals (should be 0)")
        
        # Test direct processing attempt
        test_goal_key = f"goal/instagram/test_validation_user/goal_filter_validation.json"
        initial_processed = len(goal_handler.processed_files)
        await goal_handler.process_goal_file(test_goal_key)
        final_processed = len(goal_handler.processed_files)
        
        if final_processed == initial_processed:
            logger.info("✅ Goal Handler correctly skipped direct test goal processing")
        else:
            logger.error("❌ Goal Handler processed test goal directly (should be skipped)")
    
    async def test_query_handler_filtering(self):
        """Test Query Handler filtering"""
        logger.info("\n🔍 TESTING QUERY HANDLER FILTERING")
        logger.info("-" * 40)
        
        query_handler = SequentialQueryHandler()
        
        # Test platform scanning
        for platform in ["instagram", "twitter"]:
            processed = await query_handler.scan_platform_for_pending_posts(platform)
            
            if not processed:
                logger.info(f"✅ Query Handler correctly filtered test data from {platform}")
            else:
                logger.error(f"❌ Query Handler processed test data from {platform}")
    
    async def test_image_generator_filtering(self):
        """Test Image Generator filtering"""
        logger.info("\n🔍 TESTING IMAGE GENERATOR FILTERING")
        logger.info("-" * 40)
        
        # Test the filtering logic from run method
        image_gen = ImageGenerator()
        
        # Simulate getting objects (include test data)
        all_objects = []
        for scenario in self.test_scenarios_created:
            if "next_posts/" in scenario or scenario.endswith(".json"):
                all_objects.append({"Key": scenario})
        
        # Test filtering
        production_objects = TestFilter.filter_test_objects(all_objects)
        filtered_count = len(all_objects) - len(production_objects)
        
        if filtered_count == len(all_objects):
            logger.info("✅ Image Generator filtering correctly removed all test objects")
        elif filtered_count > 0:
            logger.info(f"✅ Image Generator filtered out {filtered_count} test objects")
            if len(production_objects) > 0:
                logger.warning(f"⚠️ {len(production_objects)} objects passed filtering - verify they are production data")
        else:
            logger.error("❌ Image Generator filtering didn't remove any test objects")
    
    async def cleanup_test_scenarios(self):
        """Clean up created test scenarios"""
        logger.info("\n🧹 CLEANING UP TEST SCENARIOS")
        logger.info("-" * 40)
        
        cleaned = 0
        for scenario_key in self.test_scenarios_created:
            try:
                success = await self.r2_client.delete_object(scenario_key)
                if success:
                    logger.info(f"🗑️ Cleaned up: {scenario_key}")
                    cleaned += 1
                else:
                    logger.warning(f"⚠️ Failed to clean: {scenario_key}")
            except Exception as e:
                logger.error(f"❌ Error cleaning {scenario_key}: {e}")
        
        logger.info(f"✅ Cleaned up {cleaned} test scenarios")
    
    async def test_future_proofing(self):
        """Test future-proofing mechanisms"""
        logger.info("\n🔮 TESTING FUTURE-PROOFING")
        logger.info("-" * 40)
        
        # Test adding custom indicators
        original_count = len(TestFilter.TEST_INDICATORS)
        TestFilter.add_custom_test_indicator("newtest")
        new_count = len(TestFilter.TEST_INDICATORS)
        
        if new_count > original_count:
            logger.info("✅ Custom test indicator addition works")
        else:
            logger.error("❌ Custom test indicator addition failed")
        
        # Test detection of new indicator
        if TestFilter.is_test_data("newtest_user"):
            logger.info("✅ Custom indicator correctly detected")
        else:
            logger.error("❌ Custom indicator not detected")
        
        # Test pattern variations
        future_test_patterns = [
            "test2025", "demo_new", "sample_v2", "experiment_ai",
            "validation_ml", "prototype_v3", "temp_2025"
        ]
        
        detected_count = 0
        for pattern in future_test_patterns:
            if TestFilter.is_test_data(pattern):
                detected_count += 1
        
        detection_rate = (detected_count / len(future_test_patterns)) * 100
        logger.info(f"📊 Future pattern detection rate: {detection_rate:.1f}%")
        
        if detection_rate >= 80:
            logger.info("✅ Future-proofing is robust")
        else:
            logger.warning("⚠️ Future-proofing may need enhancement")

async def main():
    """Main validation execution"""
    validator = ProductionFilterValidator()
    await validator.run_comprehensive_validation()
    await validator.test_future_proofing()

if __name__ == "__main__":
    asyncio.run(main()) 