#!/usr/bin/env python3
"""
🎯 BULLETPROOF COMPATIBILITY TEST SUITE
Enhanced Image Generator & NextPost Module Integration Test

This test suite validates that the enhanced Image Generator can correctly handle
all possible NextPost module output formats and edge cases.
"""

import asyncio
import json
import tempfile
import os
from datetime import datetime
from image_generator import ImageGenerator
from utils.logging import logger

class CompatibilityTestSuite:
    """Comprehensive test suite for NextPost-ImageGenerator compatibility."""
    
    def __init__(self):
        self.image_gen = ImageGenerator()
        self.test_results = []
    
    def create_test_data(self):
        """Create comprehensive test data covering all possible formats."""
        return {
            # Test 1: Standard NextPost module format (most common)
            "nextpost_standard": {
                "module_type": "next_post_prediction",
                "platform": "instagram",
                "username": "fentybeauty",
                "post_data": {
                    "caption": "Okay baddies, let's talk LIPS 💋 What's your go-to Gloss Bomb shade?",
                    "hashtags": ["#FentyBeauty", "#GlossBomb", "#LipGloss"],
                    "call_to_action": "Drop your fave Gloss Bomb shade in the comments!",
                    "image_prompt": "🎨 **AUTHENTIC VISUAL DIRECTION**: Close-up shot of lips glistening with Gloss Bomb. Focus on the texture and shine."
                },
                "generated_at": datetime.now().isoformat(),
                "status": "pending"
            },
            
            # Test 2: Direct next_post_prediction format
            "nextpost_direct": {
                "next_post_prediction": {
                    "caption": "New collection dropping soon! ✨",
                    "hashtags": ["#NewCollection", "#ComingSoon"],
                    "call_to_action": "Stay tuned!",
                    "image_prompt": "High-quality product showcase with professional lighting"
                },
                "platform": "instagram",
                "username": "maccosmetics"
            },
            
            # Test 3: Twitter format
            "twitter_format": {
                "tweet_text": "Exciting AI developments happening! 🚀",
                "hashtags": ["#AI", "#Technology", "#Innovation"],
                "call_to_action": "What do you think about this?",
                "image_prompt": "Modern technology visual with AI elements",
                "platform": "twitter",
                "username": "ylecun"
            },
            
            # Test 4: Alternative field names
            "alternative_fields": {
                "post": {
                    "caption": "Beautiful sunset today! 🌅",
                    "hashtags": ["#Sunset", "#Nature", "#Photography"],
                    "call_to_action": "Share your sunset photos!",
                    "visual_prompt": "Stunning sunset photography with warm golden hour lighting"
                },
                "status": "pending"
            },
            
            # Test 5: Missing image prompt (should auto-generate)
            "missing_prompt": {
                "post": {
                    "caption": "Great workout session today! 💪",
                    "hashtags": ["#Fitness", "#Workout", "#Health"],
                    "call_to_action": "What's your favorite exercise?"
                },
                "platform": "instagram",
                "username": "fitnessinfluencer",
                "status": "pending"
            },
            
            # Test 6: Nested structure
            "nested_structure": {
                "content_plan": {
                    "next_post": {
                        "caption": "Delicious recipe coming up! 🍝",
                        "hashtags": ["#Recipe", "#Cooking", "#Food"],
                        "call_to_action": "Try this recipe and let me know!",
                        "image_prompt": "Appetizing food photography with beautiful plating"
                    }
                },
                "platform": "instagram",
                "username": "chef_marco"
            },
            
            # Test 7: Malformed data (should recover)
            "malformed_data": {
                "random_field": "some value",
                "another_field": {
                    "caption": "Travel adventures! ✈️",
                    "hashtags": "#Travel #Adventure #Explore",
                    "image_description": "Beautiful travel destination photography"
                },
                "platform": "instagram",
                "username": "traveler_jane"
            },
            
            # Test 8: Empty data (edge case)
            "empty_data": {},
            
            # Test 9: Complex NextPost wrapper
            "complex_wrapper": {
                "module_type": "next_post_prediction",
                "platform": "twitter",
                "username": "tech_startup",
                "post_data": {
                    "tweet_text": "Launching our new app! 📱",
                    "hashtags": ["#AppLaunch", "#Startup", "#Tech"],
                    "call_to_action": "Download now!",
                    "media_suggestion": "Clean app interface screenshot with modern design"
                },
                "generated_at": datetime.now().isoformat(),
                "status": "pending",
                "original_format": "nextpost_module"
            }
        }
    
    async def run_test(self, test_name, test_data):
        """Run a single test case."""
        logger.info(f"🧪 RUNNING TEST: {test_name}")
        
        try:
            # Create temporary file for testing
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
                json.dump(test_data, temp_file, indent=2)
                temp_path = temp_file.name
            
            # Test the fix_post_data method
            fixed_data = self.image_gen.fix_post_data(test_data, f"test_{test_name}")
            
            if fixed_data is None:
                result = {
                    "test_name": test_name,
                    "status": "FAILED",
                    "error": "fix_post_data returned None",
                    "input_keys": list(test_data.keys()) if isinstance(test_data, dict) else "NOT_DICT"
                }
            else:
                # Validate the fixed data structure
                validation_result = self._validate_fixed_data(fixed_data, test_name)
                
                result = {
                    "test_name": test_name,
                    "status": "PASSED" if validation_result["valid"] else "FAILED",
                    "input_keys": list(test_data.keys()) if isinstance(test_data, dict) else "NOT_DICT",
                    "output_structure": validation_result,
                    "image_prompt_found": validation_result.get("image_prompt_exists", False),
                    "image_prompt_length": validation_result.get("image_prompt_length", 0)
                }
            
            # Clean up temporary file
            os.unlink(temp_path)
            
            return result
            
        except Exception as e:
            return {
                "test_name": test_name,
                "status": "ERROR",
                "error": str(e),
                "input_keys": list(test_data.keys()) if isinstance(test_data, dict) else "NOT_DICT"
            }
    
    def _validate_fixed_data(self, fixed_data, test_name):
        """Validate that fixed data has the expected structure."""
        try:
            validation = {
                "valid": True,
                "errors": []
            }
            
            # Check basic structure
            if not isinstance(fixed_data, dict):
                validation["valid"] = False
                validation["errors"].append("Fixed data is not a dictionary")
                return validation
            
            # Check for required fields
            required_fields = ["post", "status"]
            for field in required_fields:
                if field not in fixed_data:
                    validation["valid"] = False
                    validation["errors"].append(f"Missing required field: {field}")
            
            # Check post structure
            if "post" in fixed_data:
                post = fixed_data["post"]
                if not isinstance(post, dict):
                    validation["valid"] = False
                    validation["errors"].append("'post' field is not a dictionary")
                else:
                    # Check for essential post fields
                    post_fields = ["caption", "hashtags", "call_to_action", "image_prompt"]
                    for field in post_fields:
                        if field not in post:
                            if field == "image_prompt":
                                # Check for alternative image prompt fields
                                alt_fields = ["visual_prompt", "media_suggestion"]
                                if not any(alt_field in post for alt_field in alt_fields):
                                    validation["valid"] = False
                                    validation["errors"].append(f"Missing image prompt (checked: {field}, {alt_fields})")
                            else:
                                validation["errors"].append(f"Missing post field: {field}")
                    
                    # Validate image prompt specifically
                    image_prompt = (post.get("image_prompt") or 
                                  post.get("visual_prompt") or 
                                  post.get("media_suggestion"))
                    
                    if image_prompt:
                        validation["image_prompt_exists"] = True
                        validation["image_prompt_length"] = len(str(image_prompt))
                        validation["image_prompt_preview"] = str(image_prompt)[:50]
                        
                        if len(str(image_prompt).strip()) < 10:
                            validation["errors"].append("Image prompt too short")
                    else:
                        validation["image_prompt_exists"] = False
                        validation["image_prompt_length"] = 0
            
            return validation
            
        except Exception as e:
            return {
                "valid": False,
                "errors": [f"Validation error: {str(e)}"]
            }
    
    async def run_full_test_suite(self):
        """Run the complete test suite."""
        logger.info("🚀 STARTING ENHANCED COMPATIBILITY TEST SUITE")
        logger.info("=" * 60)
        
        test_data = self.create_test_data()
        
        for test_name, data in test_data.items():
            result = await self.run_test(test_name, data)
            self.test_results.append(result)
            
            # Print immediate result
            status_emoji = "✅" if result["status"] == "PASSED" else "❌" if result["status"] == "FAILED" else "⚠️"
            logger.info(f"{status_emoji} {test_name}: {result['status']}")
            
            if result["status"] != "PASSED":
                if "error" in result:
                    logger.error(f"   Error: {result['error']}")
                if "output_structure" in result and "errors" in result["output_structure"]:
                    for error in result["output_structure"]["errors"]:
                        logger.error(f"   Validation: {error}")
        
        # Print summary
        self._print_test_summary()
    
    def _print_test_summary(self):
        """Print detailed test summary."""
        logger.info("=" * 60)
        logger.info("🎯 TEST SUITE SUMMARY")
        logger.info("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r["status"] == "PASSED"])
        failed_tests = len([r for r in self.test_results if r["status"] == "FAILED"])
        error_tests = len([r for r in self.test_results if r["status"] == "ERROR"])
        
        logger.info(f"📊 RESULTS: {passed_tests}/{total_tests} tests passed")
        logger.info(f"✅ Passed: {passed_tests}")
        logger.info(f"❌ Failed: {failed_tests}")
        logger.info(f"⚠️ Errors: {error_tests}")
        
        # Detailed results for failed/error tests
        if failed_tests > 0 or error_tests > 0:
            logger.info("\n📋 DETAILED FAILURE ANALYSIS:")
            for result in self.test_results:
                if result["status"] != "PASSED":
                    logger.info(f"\n🔍 {result['test_name']}:")
                    logger.info(f"   Status: {result['status']}")
                    logger.info(f"   Input keys: {result.get('input_keys', 'N/A')}")
                    
                    if "error" in result:
                        logger.info(f"   Error: {result['error']}")
                    
                    if "output_structure" in result:
                        structure = result["output_structure"]
                        if "errors" in structure:
                            for error in structure["errors"]:
                                logger.info(f"   Validation error: {error}")
                        
                        if "image_prompt_exists" in structure:
                            logger.info(f"   Image prompt found: {structure['image_prompt_exists']}")
                            if structure["image_prompt_exists"]:
                                logger.info(f"   Image prompt length: {structure['image_prompt_length']}")
        
        # Success analysis
        logger.info("\n🎉 SUCCESS ANALYSIS:")
        for result in self.test_results:
            if result["status"] == "PASSED":
                structure = result.get("output_structure", {})
                prompt_length = structure.get("image_prompt_length", 0)
                logger.info(f"✅ {result['test_name']}: Image prompt length = {prompt_length}")
        
        logger.info("=" * 60)
        
        if passed_tests == total_tests:
            logger.info("🎊 ALL TESTS PASSED! NextPost-ImageGenerator compatibility is BULLETPROOF!")
        else:
            logger.warning(f"⚠️ {failed_tests + error_tests} tests failed. Review and fix issues.")

async def main():
    """Run the compatibility test suite."""
    test_suite = CompatibilityTestSuite()
    await test_suite.run_full_test_suite()

if __name__ == "__main__":
    asyncio.run(main()) 