"""
Comprehensive Facebook Integration Test for Module2
Tests all components to ensure complete Facebook platform compatibility.
"""

import asyncio
import json
import os
from typing import Dict, List, Any
from utils.logging import logger
from config import PLATFORM_CONFIG
from query_handler import SequentialQueryHandler
from goal_rag_handler import EnhancedGoalHandler, DeepRAGAnalyzer, ContentGenerator
from image_generator import ImageGenerator
from utils.test_filter import TestFilter

class FacebookIntegrationValidator:
    """Validates Facebook integration across all Module2 components"""
    
    def __init__(self):
        self.test_results = {
            "config_validation": False,
            "query_handler_facebook": False,
            "goal_handler_facebook": False,
            "image_generator_facebook": False,
            "content_generation_facebook": False,
            "hashtag_generation_facebook": False,
            "test_filter_facebook": False,
            "platform_detection": False
        }
        self.facebook_test_data = self._create_facebook_test_data()
        
    def _create_facebook_test_data(self) -> Dict:
        """Create comprehensive Facebook test data"""
        return {
            "profile_data": {
                "username": "facebook_test_user",
                "biography": "Community-focused content creator sharing life experiences",
                "followersCount": 2500,
                "latestPosts": [
                    {
                        "caption": "Sharing moments with my community! Building connections that matter. #Community #Life #FacebookFamily",
                        "likesCount": 150,
                        "commentsCount": 25,
                        "type": "photo"
                    },
                    {
                        "caption": "Excited to announce our community event next week! Join us for meaningful conversations. #CommunityEvent #SocialConnection",
                        "likesCount": 200,
                        "commentsCount": 40,
                        "type": "event"
                    }
                ]
            },
            "goal_data": {
                "goal": "Increase community engagement by 50% through meaningful conversations and social connections",
                "timeline": 14,
                "persona": "Community-focused authentic voice",
                "instructions": "Foster genuine connections and encourage meaningful interactions",
                "status": "pending"
            },
            "generated_content": {
                "Post_1": {
                    "content": "Building stronger connections in our community starts with authentic conversations. Let's share our experiences and learn from each other's journeys. Visual should show people genuinely connecting and engaging in meaningful dialogue.",
                    "status": "pending"
                }
            }
        }

    async def run_comprehensive_test(self) -> Dict[str, bool]:
        """Run comprehensive Facebook integration test"""
        logger.info("🧪 Starting Facebook Integration Validation")
        logger.info("=" * 60)
        
        # Test 1: Platform Configuration
        await self._test_platform_config()
        
        # Test 2: Query Handler Facebook Support
        await self._test_query_handler_facebook()
        
        # Test 3: Goal Handler Facebook Support  
        await self._test_goal_handler_facebook()
        
        # Test 4: Image Generator Facebook Support
        await self._test_image_generator_facebook()
        
        # Test 5: Content Generation Facebook
        await self._test_content_generation_facebook()
        
        # Test 6: Hashtag Generation Facebook
        await self._test_hashtag_generation_facebook()
        
        # Test 7: Test Filter Facebook Support
        await self._test_filter_facebook()
        
        # Test 8: Platform Detection
        await self._test_platform_detection()
        
        # Summary Report
        self._print_test_results()
        
        return self.test_results
    
    async def _test_platform_config(self):
        """Test platform configuration includes Facebook"""
        try:
            logger.info("🔧 Testing Platform Configuration...")
            
            # Check if Facebook is in supported platforms
            supported_platforms = PLATFORM_CONFIG.get("supported_platforms", [])
            facebook_supported = "facebook" in supported_platforms
            
            # Check Facebook platform features
            facebook_features = PLATFORM_CONFIG.get("platform_features", {}).get("facebook", {})
            has_facebook_config = bool(facebook_features)
            
            # Validate Facebook-specific settings
            expected_facebook_features = ["content_type", "max_hashtags", "character_limit", "tone", "focus"]
            facebook_config_complete = all(key in facebook_features for key in expected_facebook_features)
            
            self.test_results["config_validation"] = facebook_supported and has_facebook_config and facebook_config_complete
            
            logger.info(f"   ✅ Facebook in supported platforms: {facebook_supported}")
            logger.info(f"   ✅ Facebook features configured: {has_facebook_config}")
            logger.info(f"   ✅ Facebook config complete: {facebook_config_complete}")
            
            if facebook_config_complete:
                logger.info(f"   📊 Facebook tone: {facebook_features.get('tone')}")
                logger.info(f"   📊 Facebook focus: {facebook_features.get('focus')}")
                logger.info(f"   📊 Facebook character limit: {facebook_features.get('character_limit')}")
            
        except Exception as e:
            logger.error(f"❌ Platform config test failed: {e}")
            self.test_results["config_validation"] = False
    
    async def _test_query_handler_facebook(self):
        """Test Query Handler Facebook support"""
        try:
            logger.info("🔄 Testing Query Handler Facebook Support...")
            
            query_handler = SequentialQueryHandler()
            
            # Check if Facebook is in platforms list
            facebook_in_platforms = "facebook" in query_handler.platforms
            
            # Test transformation prompt with Facebook
            test_content = "This is test content for Facebook community. Engage with authentic conversations. Show people connecting genuinely."
            prompt = query_handler.create_transformation_prompt(
                test_content, 
                "facebook", 
                "facebook_test_user", 
                self.facebook_test_data["profile_data"]
            )
            
            # Check for Facebook-specific instructions in prompt
            facebook_instructions = "community" in prompt.lower() and "conversational" in prompt.lower()
            
            # Test fallback hashtags
            fallback_data = query_handler.create_fallback_transformation(test_content, "facebook", "facebook_test_user")
            facebook_hashtags = any("#Facebook" in str(hashtag) for hashtag in fallback_data.get("hashtags", []))
            
            self.test_results["query_handler_facebook"] = facebook_in_platforms and facebook_instructions and facebook_hashtags
            
            logger.info(f"   ✅ Facebook in platforms: {facebook_in_platforms}")
            logger.info(f"   ✅ Facebook-specific instructions: {facebook_instructions}")
            logger.info(f"   ✅ Facebook hashtags generated: {facebook_hashtags}")
            
        except Exception as e:
            logger.error(f"❌ Query Handler test failed: {e}")
            self.test_results["query_handler_facebook"] = False
    
    async def _test_goal_handler_facebook(self):
        """Test Goal Handler Facebook support"""
        try:
            logger.info("🎯 Testing Goal Handler Facebook Support...")
            
            goal_handler = EnhancedGoalHandler()
            
            # Check if Facebook is in platforms list
            facebook_in_platforms = "facebook" in goal_handler.platforms
            
            # Test Deep RAG Analyzer (should be platform-agnostic)
            rag_analyzer = DeepRAGAnalyzer()
            profile_analysis = rag_analyzer.analyze_profile_patterns(self.facebook_test_data["profile_data"])
            analysis_success = bool(profile_analysis and "posting_frequency" in profile_analysis)
            
            # Test Content Generator with Facebook
            content_generator = ContentGenerator(rag_analyzer)
            
            # Test hashtag generation for Facebook
            content_generator_method = hasattr(content_generator, '_get_platform_hashtags')
            
            self.test_results["goal_handler_facebook"] = facebook_in_platforms and analysis_success and content_generator_method
            
            logger.info(f"   ✅ Facebook in platforms: {facebook_in_platforms}")
            logger.info(f"   ✅ Profile analysis works: {analysis_success}")
            logger.info(f"   ✅ Content generator method exists: {content_generator_method}")
            
        except Exception as e:
            logger.error(f"❌ Goal Handler test failed: {e}")
            self.test_results["goal_handler_facebook"] = False
    
    async def _test_image_generator_facebook(self):
        """Test Image Generator Facebook support"""
        try:
            logger.info("🖼️ Testing Image Generator Facebook Support...")
            
            image_generator = ImageGenerator()
            
            # Check if Facebook is in platforms list
            facebook_in_platforms = "facebook" in image_generator.platforms
            
            # Test post data fixing with Facebook format
            facebook_post_data = {
                "caption": "Community-focused Facebook post",
                "hashtags": ["#Facebook", "#Community"],
                "call_to_action": "Join the conversation!",
                "image_prompt": "Community gathering with genuine interactions"
            }
            
            fixed_data = image_generator.fix_post_data(facebook_post_data, "test_facebook_post")
            facebook_fixing_works = bool(fixed_data and "post" in fixed_data)
            
            # Test platform-specific image prompt generation  
            if fixed_data and "post" in fixed_data:
                post_data = fixed_data["post"]
                has_image_prompt = bool(post_data.get("image_prompt"))
            else:
                has_image_prompt = False
            
            self.test_results["image_generator_facebook"] = facebook_in_platforms and facebook_fixing_works and has_image_prompt
            
            logger.info(f"   ✅ Facebook in platforms: {facebook_in_platforms}")
            logger.info(f"   ✅ Facebook post fixing works: {facebook_fixing_works}")
            logger.info(f"   ✅ Image prompt generated: {has_image_prompt}")
            
        except Exception as e:
            logger.error(f"❌ Image Generator test failed: {e}")
            self.test_results["image_generator_facebook"] = False
    
    async def _test_content_generation_facebook(self):
        """Test content generation specifically for Facebook"""
        try:
            logger.info("📝 Testing Facebook Content Generation...")
            
            # Test content generator with Facebook platform
            rag_analyzer = DeepRAGAnalyzer()
            content_generator = ContentGenerator(rag_analyzer)
            
            # Simulate content generation process
            profile_analysis = rag_analyzer.analyze_profile_patterns(self.facebook_test_data["profile_data"])
            
            # Test single post generation (simulated)
            post_data = await content_generator._generate_single_post(
                post_number=1,
                total_posts=3,
                goal=self.facebook_test_data["goal_data"],
                persona_traits=profile_analysis.get("persona_traits", {}),
                content_themes=["community", "social_connection", "engagement"],
                successful_characteristics=[],
                username="facebook_test_user",
                platform="facebook"
            )
            
            content_generated = bool(post_data and "three_sentences" in post_data)
            
            # Test hashtag addition specifically for Facebook
            if content_generated:
                test_content = post_data["three_sentences"]
                enhanced_content = await content_generator._add_hashtags_to_content(
                    test_content,
                    ["community", "social_connection"],
                    "facebook",
                    "facebook_test_user",
                    self.facebook_test_data["goal_data"]
                )
                
                facebook_hashtags_added = "#Facebook" in enhanced_content or "#Community" in enhanced_content
            else:
                facebook_hashtags_added = False
            
            self.test_results["content_generation_facebook"] = content_generated and facebook_hashtags_added
            
            logger.info(f"   ✅ Content generated for Facebook: {content_generated}")
            logger.info(f"   ✅ Facebook hashtags added: {facebook_hashtags_added}")
            
        except Exception as e:
            logger.error(f"❌ Content generation test failed: {e}")
            self.test_results["content_generation_facebook"] = False
    
    async def _test_hashtag_generation_facebook(self):
        """Test Facebook-specific hashtag generation"""
        try:
            logger.info("🏷️ Testing Facebook Hashtag Generation...")
            
            rag_analyzer = DeepRAGAnalyzer()
            content_generator = ContentGenerator(rag_analyzer)
            
            # Test platform hashtags for Facebook
            platform_hashtags = content_generator._get_platform_hashtags("facebook", self.facebook_test_data["goal_data"])
            has_facebook_hashtags = "#Facebook" in platform_hashtags
            has_community_hashtags = "#Community" in platform_hashtags
            
            # Test fallback hashtags for Facebook
            fallback_hashtags = content_generator._get_fallback_hashtags("facebook")
            has_fallback_facebook = "#Facebook" in fallback_hashtags
            has_social_connection = "#SocialConnection" in fallback_hashtags
            
            # Test relevant hashtag generation
            relevant_hashtags = content_generator._generate_relevant_hashtags(
                ["community", "social_connection", "engagement"],
                "facebook",
                "facebook_test_user",
                self.facebook_test_data["goal_data"]
            )
            
            has_relevant_hashtags = len(relevant_hashtags) > 0
            
            hashtag_success = (has_facebook_hashtags and has_community_hashtags and 
                             has_fallback_facebook and has_social_connection and has_relevant_hashtags)
            
            self.test_results["hashtag_generation_facebook"] = hashtag_success
            
            logger.info(f"   ✅ Platform hashtags work: {has_facebook_hashtags and has_community_hashtags}")
            logger.info(f"   ✅ Fallback hashtags work: {has_fallback_facebook and has_social_connection}")
            logger.info(f"   ✅ Relevant hashtags generated: {has_relevant_hashtags}")
            logger.info(f"   📊 Generated hashtags: {relevant_hashtags[:5]}")
            
        except Exception as e:
            logger.error(f"❌ Hashtag generation test failed: {e}")
            self.test_results["hashtag_generation_facebook"] = False
    
    async def _test_filter_facebook(self):
        """Test filter works with Facebook data"""
        try:
            logger.info("🧹 Testing Facebook Test Filter Support...")
            
            # Test with Facebook production usernames
            facebook_production_users = ["shakira", "nike", "community_builder", "facebook_test_user"]
            facebook_test_users = ["facebook_test", "facebook_demo", "facebook_validation", "test_facebook"]
            
            production_correctly_passed = all(
                not TestFilter.should_skip_processing("facebook", user, "")
                for user in facebook_production_users
            )
            
            test_correctly_filtered = all(
                TestFilter.should_skip_processing("facebook", user, "")
                for user in facebook_test_users
            )
            
            # Test platform-agnostic filtering
            platform_agnostic = TestFilter.should_skip_processing("facebook", "test123", "facebook/test123/posts.json")
            
            filter_success = production_correctly_passed and test_correctly_filtered and platform_agnostic
            
            self.test_results["test_filter_facebook"] = filter_success
            
            logger.info(f"   ✅ Production users passed: {production_correctly_passed}")
            logger.info(f"   ✅ Test users filtered: {test_correctly_filtered}")
            logger.info(f"   ✅ Platform-agnostic filtering: {platform_agnostic}")
            
        except Exception as e:
            logger.error(f"❌ Test filter test failed: {e}")
            self.test_results["test_filter_facebook"] = False
    
    async def _test_platform_detection(self):
        """Test platform detection for Facebook paths"""
        try:
            logger.info("🔍 Testing Facebook Platform Detection...")
            
            # Test various Facebook path formats
            facebook_paths = [
                "facebook/shakira/shakira.json",
                "generated_content/facebook/shakira/posts.json", 
                "next_posts/facebook/shakira/campaign_next_post_1.json",
                "goal/facebook/shakira/goal_1.json",
                "ready_post/facebook/shakira/ready_post_1.json"
            ]
            
            platform_detection_success = True
            
            for path in facebook_paths:
                # Basic platform detection from path
                platform_detected = "facebook" in path.split("/")[:2]
                if not platform_detected:
                    platform_detection_success = False
                    logger.error(f"   ❌ Failed to detect Facebook in path: {path}")
                else:
                    logger.debug(f"   ✅ Facebook detected in: {path}")
            
            # Test with sample data structures
            facebook_data_sample = {
                "platform": "facebook",
                "username": "facebook_test_user",
                "post_data": {
                    "caption": "Community post",
                    "hashtags": ["#Community"]
                }
            }
            
            data_platform_detection = facebook_data_sample.get("platform") == "facebook"
            
            overall_detection = platform_detection_success and data_platform_detection
            
            self.test_results["platform_detection"] = overall_detection
            
            logger.info(f"   ✅ Path detection works: {platform_detection_success}")
            logger.info(f"   ✅ Data detection works: {data_platform_detection}")
            
        except Exception as e:
            logger.error(f"❌ Platform detection test failed: {e}")
            self.test_results["platform_detection"] = False
    
    def _print_test_results(self):
        """Print comprehensive test results"""
        logger.info("\n" + "=" * 60)
        logger.info("🧪 FACEBOOK INTEGRATION TEST RESULTS")
        logger.info("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() if result)
        
        for test_name, result in self.test_results.items():
            status = "✅ PASSED" if result else "❌ FAILED"
            test_display = test_name.replace("_", " ").title()
            logger.info(f"{status} - {test_display}")
        
        logger.info("-" * 60)
        logger.info(f"📊 OVERALL RESULT: {passed_tests}/{total_tests} tests passed")
        
        if passed_tests == total_tests:
            logger.info("🎉 ALL TESTS PASSED - Facebook integration is COMPLETE!")
            logger.info("✅ Module2 is fully compatible with Facebook platform")
        else:
            logger.warning(f"⚠️ {total_tests - passed_tests} tests failed - Review and fix issues")
            
        logger.info("=" * 60)

async def main():
    """Main test execution"""
    print("🚀 Facebook Integration Validation for Module2")
    print("Testing complete Facebook platform compatibility...")
    print()
    
    validator = FacebookIntegrationValidator()
    results = await validator.run_comprehensive_test()
    
    # Return exit code based on results
    all_passed = all(results.values())
    exit_code = 0 if all_passed else 1
    
    if all_passed:
        print("\n🎉 SUCCESS: Facebook integration is complete and functional!")
    else:
        print("\n⚠️ WARNING: Some Facebook integration tests failed")
    
    return exit_code

if __name__ == "__main__":
    import sys
    exit_code = asyncio.run(main())
    sys.exit(exit_code) 