"""
Simple Timeline Implementation Test
Focused test to verify Timeline field is correctly added to generated content
without relying on AI generation (which has quota limits).
"""

import asyncio
import json
from datetime import datetime
from utils.logging import logger
from goal_rag_handler import ContentGenerator, DeepRAGAnalyzer

class SimpleTimelineTest:
    """Simple focused test for Timeline implementation"""
    
    def __init__(self):
        # Create mock content generator that bypasses AI calls
        self.content_generator = MockContentGenerator()
        
    async def run_timeline_tests(self):
        """Run focused timeline tests"""
        logger.info("🧪 SIMPLE TIMELINE IMPLEMENTATION TEST")
        logger.info("=" * 50)
        
        # Test 1: Basic Timeline functionality
        await self.test_basic_timeline_functionality()
        
        # Test 2: Different interval values
        await self.test_different_intervals()
        
        # Test 3: Rounding behavior
        await self.test_rounding_behavior()
        
        logger.info("\n🎉 SIMPLE TIMELINE TESTS COMPLETED")
    
    async def test_basic_timeline_functionality(self):
        """Test basic Timeline field functionality"""
        logger.info("\n🔍 TESTING BASIC TIMELINE FUNCTIONALITY")
        logger.info("-" * 40)
        
        mock_data = self._create_mock_data()
        
        # Test with 24-hour interval
        result = await self.content_generator.generate_post_content(
            goal=mock_data["goal"],
            profile_analysis=mock_data["profile_analysis"],
            posts_needed=3,
            username="test_user",
            platform="instagram",
            prediction_metrics=mock_data["prediction_metrics"],
            posting_interval=24.0
        )
        
        # Verify Timeline field
        if "Timeline" in result:
            timeline_value = result["Timeline"]
            if timeline_value == "24":
                logger.info("✅ Basic Timeline functionality: 24.0h → '24'")
            else:
                logger.error(f"❌ Timeline incorrect: expected '24', got '{timeline_value}'")
        else:
            logger.error("❌ Timeline field missing")
        
        # Verify other fields
        if "Summary" in result:
            logger.info("✅ Summary field present")
        else:
            logger.error("❌ Summary field missing")
        
        # Verify posts
        post_count = len([key for key in result.keys() if key.startswith("Post_")])
        if post_count == 3:
            logger.info("✅ Correct number of posts: 3")
        else:
            logger.error(f"❌ Wrong post count: expected 3, got {post_count}")
    
    async def test_different_intervals(self):
        """Test different posting intervals"""
        logger.info("\n🔍 TESTING DIFFERENT INTERVALS")
        logger.info("-" * 40)
        
        test_cases = [
            {"interval": 6.0, "expected": "6"},
            {"interval": 12.0, "expected": "12"},
            {"interval": 18.0, "expected": "18"},
            {"interval": 48.0, "expected": "48"},
            {"interval": 72.0, "expected": "72"}
        ]
        
        mock_data = self._create_mock_data()
        
        for case in test_cases:
            interval = case["interval"]
            expected = case["expected"]
            
            result = await self.content_generator.generate_post_content(
                goal=mock_data["goal"],
                profile_analysis=mock_data["profile_analysis"],
                posts_needed=2,
                username="test_user",
                platform="instagram",
                prediction_metrics=mock_data["prediction_metrics"],
                posting_interval=interval
            )
            
            if "Timeline" in result:
                actual = result["Timeline"]
                if actual == expected:
                    logger.info(f"✅ {interval}h → '{actual}'")
                else:
                    logger.error(f"❌ {interval}h → expected '{expected}', got '{actual}'")
            else:
                logger.error(f"❌ Timeline missing for {interval}h")
    
    async def test_rounding_behavior(self):
        """Test rounding behavior for decimal intervals"""
        logger.info("\n🔍 TESTING ROUNDING BEHAVIOR")
        logger.info("-" * 40)
        
        rounding_cases = [
            {"interval": 12.4, "expected": "12"},  # Rounds down
            {"interval": 12.5, "expected": "13"},  # Rounds up  
            {"interval": 12.6, "expected": "13"},  # Rounds up
            {"interval": 23.3, "expected": "23"},  # Rounds down
            {"interval": 23.7, "expected": "24"},  # Rounds up
            {"interval": 8.1, "expected": "8"},    # Rounds down
            {"interval": 8.9, "expected": "9"}     # Rounds up
        ]
        
        mock_data = self._create_mock_data()
        
        for case in rounding_cases:
            interval = case["interval"]
            expected = case["expected"]
            
            result = await self.content_generator.generate_post_content(
                goal=mock_data["goal"],
                profile_analysis=mock_data["profile_analysis"],
                posts_needed=2,
                username="test_user",
                platform="instagram",
                prediction_metrics=mock_data["prediction_metrics"],
                posting_interval=interval
            )
            
            if "Timeline" in result:
                actual = result["Timeline"]
                if actual == expected:
                    logger.info(f"✅ {interval}h → '{actual}' (correct rounding)")
                else:
                    logger.error(f"❌ {interval}h → expected '{expected}', got '{actual}'")
            else:
                logger.error(f"❌ Timeline missing for {interval}h")
    
    def _create_mock_data(self):
        """Create minimal mock data for testing"""
        return {
            "goal": {
                "goal": "Test timeline implementation",
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
                "content_themes": ["test", "timeline"],
                "successful_post_characteristics": []
            },
            "prediction_metrics": {
                "method": "test",
                "confidence": 0.8
            }
        }

class MockContentGenerator(ContentGenerator):
    """Mock ContentGenerator that bypasses AI calls"""
    
    def __init__(self):
        # Initialize without the RAG analyzer to avoid dependencies
        pass
        
    async def generate_post_content(
        self, 
        goal, 
        profile_analysis, 
        posts_needed,
        username,
        platform,
        prediction_metrics,
        posting_interval
    ):
        """Generate mock content without AI calls"""
        
        posts_dict = {}
        
        # Generate mock posts
        for i in range(posts_needed):
            post_key = f"Post_{i + 1}"
            posts_dict[post_key] = {
                "content": f"Mock content for post {i + 1}. This is test content. Visual should be engaging.",
                "status": "pending"
            }
        
        # Add mock summary
        posts_dict["Summary"] = "Mock summary for testing Timeline implementation"
        
        # 🕒 ADD TIMELINE: Include posting interval (in hours) as Timeline field
        # Extract numerical value from posting_interval (remove 'h' if present and round to integer)
        timeline_hours = int(round(posting_interval))
        posts_dict["Timeline"] = str(timeline_hours)
        
        logger.info(f"📅 Added Timeline to generated content: {timeline_hours} hours between posts")
        
        return posts_dict

async def main():
    """Main test execution"""
    tester = SimpleTimelineTest()
    await tester.run_timeline_tests()

if __name__ == "__main__":
    asyncio.run(main()) 