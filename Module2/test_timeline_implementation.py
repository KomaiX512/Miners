"""
Timeline Implementation Test Suite
Comprehensive testing to ensure Timeline field is always present in generated_content
with correct posting interval values from the ML-powered strategy analysis.
"""

import asyncio
import json
import math
from datetime import datetime
from utils.r2_client import R2Client
from utils.logging import logger
from config import R2_CONFIG
from goal_rag_handler import EnhancedGoalHandler, ContentGenerator, DeepRAGAnalyzer, StrategyCalculator

class TimelineImplementationTester:
    """Comprehensive testing of Timeline field implementation"""
    
    def __init__(self):
        self.r2_client = R2Client(config=R2_CONFIG)
        self.test_scenarios_created = []
        self.content_generator = ContentGenerator(DeepRAGAnalyzer())
        self.strategy_calculator = StrategyCalculator(DeepRAGAnalyzer())
        
    async def run_comprehensive_timeline_tests(self):
        """Run complete timeline implementation validation"""
        logger.info("🧪 COMPREHENSIVE TIMELINE IMPLEMENTATION TESTING")
        logger.info("=" * 60)
        
        # Test 1: Direct method testing
        await self.test_generate_post_content_method()
        
        # Test 2: Different posting interval scenarios
        await self.test_various_posting_intervals()
        
        # Test 3: Edge cases and error handling
        await self.test_edge_cases()
        
        # Test 4: End-to-end goal processing
        await self.test_end_to_end_goal_processing()
        
        # Test 5: Real-world scenario simulation
        await self.test_real_world_scenarios()
        
        # Cleanup
        await self.cleanup_test_scenarios()
        
        logger.info("\n🎉 TIMELINE IMPLEMENTATION TESTING COMPLETED")
    
    async def test_generate_post_content_method(self):
        """Test the generate_post_content method directly"""
        logger.info("\n🔍 TESTING generate_post_content METHOD DIRECTLY")
        logger.info("-" * 50)
        
        # Mock data for testing
        mock_goal = {
            "goal": "Increase engagement by 50%",
            "timeline": 7,
            "persona": "Professional brand",
            "instructions": "Maintain authenticity"
        }
        
        mock_profile_analysis = {
            "persona_traits": {
                "brand_voice": "professional",
                "tone": "engaging",
                "writing_style": "concise"
            },
            "content_themes": ["engagement", "quality", "brand"],
            "successful_post_characteristics": [
                {"caption_length": 120, "hashtag_count": 5, "has_cta": True}
            ]
        }
        
        mock_prediction_metrics = {
            "method": "xgboost",
            "confidence": 0.85
        }
        
        # Test various posting intervals
        test_intervals = [
            6.0,    # 6 hours
            12.5,   # 12.5 hours (should round to 13)
            24.0,   # 24 hours
            8.3,    # 8.3 hours (should round to 8)
            15.7,   # 15.7 hours (should round to 16)
            48.0,   # 48 hours
            3.2     # 3.2 hours (should round to 3)
        ]
        
        for interval in test_intervals:
            logger.info(f"Testing posting interval: {interval} hours")
            
            try:
                result = await self.content_generator.generate_post_content(
                    goal=mock_goal,
                    profile_analysis=mock_profile_analysis,
                    posts_needed=3,
                    username="test_timeline_user",
                    platform="instagram",
                    prediction_metrics=mock_prediction_metrics,
                    posting_interval=interval
                )
                
                # Verify Timeline field exists
                if "Timeline" not in result:
                    logger.error(f"❌ Timeline field MISSING for interval {interval}")
                    continue
                
                # Verify Timeline value is correct
                expected_timeline = str(int(round(interval)))
                actual_timeline = result["Timeline"]
                
                if actual_timeline == expected_timeline:
                    logger.info(f"✅ Timeline correct: {interval}h → {actual_timeline}")
                else:
                    logger.error(f"❌ Timeline incorrect: {interval}h → expected {expected_timeline}, got {actual_timeline}")
                
                # Verify other required fields
                required_fields = ["Summary"]
                for field in required_fields:
                    if field not in result:
                        logger.error(f"❌ Required field {field} missing")
                    else:
                        logger.debug(f"✅ {field} field present")
                
                # Verify post structure
                post_count = len([key for key in result.keys() if key.startswith("Post_")])
                if post_count == 3:
                    logger.debug(f"✅ Correct number of posts: {post_count}")
                else:
                    logger.error(f"❌ Incorrect post count: expected 3, got {post_count}")
                    
            except Exception as e:
                logger.error(f"❌ Error testing interval {interval}: {e}")
    
    async def test_various_posting_intervals(self):
        """Test Timeline field with various posting interval calculations"""
        logger.info("\n🔍 TESTING VARIOUS POSTING INTERVAL CALCULATIONS")
        logger.info("-" * 50)
        
        # Test different scenarios that would produce different intervals
        test_scenarios = [
            {"posts": 2, "timeline_days": 1, "expected_interval": 12.0},    # 24/2 = 12h
            {"posts": 3, "timeline_days": 1, "expected_interval": 8.0},     # 24/3 = 8h
            {"posts": 4, "timeline_days": 2, "expected_interval": 12.0},    # 48/4 = 12h
            {"posts": 8, "timeline_days": 7, "expected_interval": 21.0},    # 168/8 = 21h
            {"posts": 1, "timeline_days": 1, "expected_interval": 24.0},    # 24/1 = 24h
            {"posts": 12, "timeline_days": 7, "expected_interval": 14.0},   # 168/12 = 14h
            {"posts": 5, "timeline_days": 3, "expected_interval": 14.4},    # 72/5 = 14.4h (rounds to 14)
        ]
        
        for scenario in test_scenarios:
            posts_needed = scenario["posts"]
            timeline_days = scenario["timeline_days"]
            expected_interval = scenario["expected_interval"]
            
            # Calculate posting interval using the same logic as StrategyCalculator
            posting_interval = (timeline_days * 24) / posts_needed if posts_needed > 0 else 24
            
            logger.info(f"Scenario: {posts_needed} posts over {timeline_days} days = {posting_interval:.1f}h interval")
            
            # Verify calculation matches expected
            if abs(posting_interval - expected_interval) < 0.1:
                logger.info(f"✅ Calculation correct: {posting_interval:.1f}h")
            else:
                logger.error(f"❌ Calculation error: expected {expected_interval}h, got {posting_interval:.1f}h")
                continue
            
            # Test with ContentGenerator
            try:
                mock_data = self._create_mock_data()
                result = await self.content_generator.generate_post_content(
                    goal=mock_data["goal"],
                    profile_analysis=mock_data["profile_analysis"],
                    posts_needed=posts_needed,
                    username="timeline_test",
                    platform="instagram",
                    prediction_metrics=mock_data["prediction_metrics"],
                    posting_interval=posting_interval
                )
                
                expected_timeline_str = str(int(round(posting_interval)))
                actual_timeline = result.get("Timeline", "MISSING")
                
                if actual_timeline == expected_timeline_str:
                    logger.info(f"✅ Timeline field correct: {actual_timeline} hours")
                else:
                    logger.error(f"❌ Timeline field incorrect: expected {expected_timeline_str}, got {actual_timeline}")
                    
            except Exception as e:
                logger.error(f"❌ Error in scenario {scenario}: {e}")
    
    async def test_edge_cases(self):
        """Test edge cases and error handling"""
        logger.info("\n🔍 TESTING EDGE CASES AND ERROR HANDLING")
        logger.info("-" * 50)
        
        edge_cases = [
            {"interval": 0.5, "description": "Very small interval"},
            {"interval": 168.0, "description": "Weekly interval"},
            {"interval": 1.0, "description": "Hourly posts"},
            {"interval": 0.1, "description": "Extremely small interval"},
            {"interval": 999.9, "description": "Very large interval"},
        ]
        
        for case in edge_cases:
            interval = case["interval"]
            description = case["description"]
            
            logger.info(f"Testing: {description} ({interval}h)")
            
            try:
                mock_data = self._create_mock_data()
                result = await self.content_generator.generate_post_content(
                    goal=mock_data["goal"],
                    profile_analysis=mock_data["profile_analysis"],
                    posts_needed=2,
                    username="edge_case_test",
                    platform="twitter",
                    prediction_metrics=mock_data["prediction_metrics"],
                    posting_interval=interval
                )
                
                # Verify Timeline field exists and is reasonable
                if "Timeline" in result:
                    timeline_value = result["Timeline"]
                    try:
                        timeline_int = int(timeline_value)
                        if timeline_int >= 0:
                            logger.info(f"✅ {description}: Timeline = {timeline_value} hours")
                        else:
                            logger.error(f"❌ {description}: Negative timeline value {timeline_value}")
                    except ValueError:
                        logger.error(f"❌ {description}: Timeline not a valid integer: {timeline_value}")
                else:
                    logger.error(f"❌ {description}: Timeline field missing")
                    
            except Exception as e:
                logger.error(f"❌ {description}: Exception {e}")
    
    async def test_end_to_end_goal_processing(self):
        """Test end-to-end goal processing to ensure Timeline is included"""
        logger.info("\n🔍 TESTING END-TO-END GOAL PROCESSING")
        logger.info("-" * 50)
        
        # Create test goal file
        test_goal = {
            "goal": "Double engagement in 2 weeks",
            "timeline": 14,
            "persona": "Engaging brand voice",
            "instructions": "Post consistently",
            "status": "pending",
            "created_at": datetime.now().isoformat()
        }
        
        goal_key = "goal/instagram/timeline_test_user/goal_timeline_validation.json"
        
        try:
            # Save test goal
            success = await self.r2_client.write_json(goal_key, test_goal)
            if success:
                self.test_scenarios_created.append(goal_key)
                logger.info(f"📝 Created test goal: {goal_key}")
                
                # Process the goal (this would normally be done by the goal handler)
                # For testing, we'll simulate the key parts
                mock_profile_analysis = self._create_mock_profile_analysis()
                mock_prediction_metrics = {"method": "xgboost", "confidence": 0.8}
                
                # Simulate strategy calculation
                posts_needed = 8  # Example calculation
                timeline_days = test_goal["timeline"]
                posting_interval = (timeline_days * 24) / posts_needed
                
                logger.info(f"Simulated strategy: {posts_needed} posts over {timeline_days} days = {posting_interval:.1f}h intervals")
                
                # Test content generation
                result = await self.content_generator.generate_post_content(
                    goal=test_goal,
                    profile_analysis=mock_profile_analysis,
                    posts_needed=posts_needed,
                    username="timeline_test_user",
                    platform="instagram",
                    prediction_metrics=mock_prediction_metrics,
                    posting_interval=posting_interval
                )
                
                # Verify complete structure
                self._verify_complete_structure(result, posts_needed, posting_interval)
                
            else:
                logger.error("❌ Failed to create test goal file")
                
        except Exception as e:
            logger.error(f"❌ End-to-end test error: {e}")
    
    async def test_real_world_scenarios(self):
        """Test real-world posting scenarios"""
        logger.info("\n🔍 TESTING REAL-WORLD SCENARIOS")
        logger.info("-" * 50)
        
        real_scenarios = [
            {
                "name": "Daily posting for a week",
                "posts": 7,
                "timeline_days": 7,
                "expected_hours": 24
            },
            {
                "name": "Twice daily for 5 days",
                "posts": 10,
                "timeline_days": 5,
                "expected_hours": 12
            },
            {
                "name": "3 times daily for 3 days",
                "posts": 9,
                "timeline_days": 3,
                "expected_hours": 8
            },
            {
                "name": "Every 6 hours for 2 days",
                "posts": 8,
                "timeline_days": 2,
                "expected_hours": 6
            },
            {
                "name": "Weekly posts for a month",
                "posts": 4,
                "timeline_days": 28,
                "expected_hours": 168
            }
        ]
        
        for scenario in real_scenarios:
            name = scenario["name"]
            posts = scenario["posts"]
            timeline_days = scenario["timeline_days"]
            expected_hours = scenario["expected_hours"]
            
            logger.info(f"Testing: {name}")
            
            # Calculate actual interval
            posting_interval = (timeline_days * 24) / posts
            
            # Test with content generator
            mock_data = self._create_mock_data()
            result = await self.content_generator.generate_post_content(
                goal=mock_data["goal"],
                profile_analysis=mock_data["profile_analysis"],
                posts_needed=posts,
                username="real_world_test",
                platform="instagram",
                prediction_metrics=mock_data["prediction_metrics"],
                posting_interval=posting_interval
            )
            
            # Verify Timeline
            if "Timeline" in result:
                timeline_value = int(result["Timeline"])
                expected_timeline = int(round(posting_interval))
                
                if timeline_value == expected_timeline:
                    logger.info(f"✅ {name}: {timeline_value} hours (expected ~{expected_hours}h)")
                else:
                    logger.error(f"❌ {name}: got {timeline_value}h, expected {expected_timeline}h")
            else:
                logger.error(f"❌ {name}: Timeline field missing")
    
    def _create_mock_data(self):
        """Create mock data for testing"""
        return {
            "goal": {
                "goal": "Test engagement increase",
                "timeline": 7,
                "persona": "Test persona",
                "instructions": "Test instructions"
            },
            "profile_analysis": {
                "persona_traits": {
                    "brand_voice": "authentic",
                    "tone": "professional",
                    "writing_style": "concise"
                },
                "content_themes": ["test", "engagement", "quality"],
                "successful_post_characteristics": [
                    {"caption_length": 100, "hashtag_count": 5, "has_cta": True}
                ]
            },
            "prediction_metrics": {
                "method": "xgboost",
                "confidence": 0.8
            }
        }
    
    def _create_mock_profile_analysis(self):
        """Create comprehensive mock profile analysis"""
        return {
            "persona_traits": {
                "brand_voice": "professional",
                "tone": "engaging",
                "writing_style": "detailed",
                "personality": "inspirational"
            },
            "content_themes": ["engagement", "growth", "quality", "brand", "community"],
            "successful_post_characteristics": [
                {"caption_length": 150, "hashtag_count": 8, "has_cta": True, "engagement": 1200},
                {"caption_length": 120, "hashtag_count": 6, "has_cta": True, "engagement": 980},
                {"caption_length": 180, "hashtag_count": 10, "has_cta": False, "engagement": 1100}
            ],
            "followers": 50000,
            "engagement_patterns": {
                "avg_engagement_rate": 0.08,
                "peak_engagement_rate": 0.15,
                "engagement_growth_trend": "increasing"
            }
        }
    
    def _verify_complete_structure(self, result, expected_posts, posting_interval):
        """Verify the complete structure of generated content"""
        logger.info("Verifying complete generated content structure...")
        
        # Check Timeline field
        if "Timeline" not in result:
            logger.error("❌ Timeline field is MISSING from generated content")
            return False
        
        timeline_value = result["Timeline"]
        expected_timeline = str(int(round(posting_interval)))
        
        if timeline_value != expected_timeline:
            logger.error(f"❌ Timeline value incorrect: expected {expected_timeline}, got {timeline_value}")
            return False
        
        logger.info(f"✅ Timeline field correct: {timeline_value} hours")
        
        # Check other required fields
        if "Summary" not in result:
            logger.error("❌ Summary field missing")
            return False
        
        logger.info("✅ Summary field present")
        
        # Check posts
        post_count = len([key for key in result.keys() if key.startswith("Post_")])
        if post_count != expected_posts:
            logger.error(f"❌ Post count incorrect: expected {expected_posts}, got {post_count}")
            return False
        
        logger.info(f"✅ Correct number of posts: {post_count}")
        
        # Verify post structure
        for i in range(1, expected_posts + 1):
            post_key = f"Post_{i}"
            if post_key not in result:
                logger.error(f"❌ {post_key} missing")
                return False
            
            post = result[post_key]
            if not isinstance(post, dict):
                logger.error(f"❌ {post_key} is not a dictionary")
                return False
            
            if "content" not in post or "status" not in post:
                logger.error(f"❌ {post_key} missing required fields")
                return False
            
            if post["status"] != "pending":
                logger.error(f"❌ {post_key} status is not 'pending': {post['status']}")
                return False
        
        logger.info("✅ All post structures correct")
        
        logger.info("🎉 COMPLETE STRUCTURE VERIFICATION PASSED")
        return True
    
    async def cleanup_test_scenarios(self):
        """Clean up test scenarios"""
        logger.info("\n🧹 CLEANING UP TEST SCENARIOS")
        logger.info("-" * 40)
        
        for scenario_key in self.test_scenarios_created:
            try:
                success = await self.r2_client.delete_object(scenario_key)
                if success:
                    logger.info(f"🗑️ Cleaned up: {scenario_key}")
                else:
                    logger.warning(f"⚠️ Failed to clean: {scenario_key}")
            except Exception as e:
                logger.error(f"❌ Error cleaning {scenario_key}: {e}")

async def main():
    """Main test execution"""
    tester = TimelineImplementationTester()
    await tester.run_comprehensive_timeline_tests()

if __name__ == "__main__":
    asyncio.run(main()) 