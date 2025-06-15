"""
Facebook Integration Validation for Module2
Validates Facebook platform compatibility across key components.
"""

import asyncio
from utils.logging import logger
from config import PLATFORM_CONFIG
from query_handler import SequentialQueryHandler
from goal_rag_handler import EnhancedGoalHandler, ContentGenerator, DeepRAGAnalyzer
from image_generator import ImageGenerator

async def validate_facebook_integration():
    """Validate Facebook integration across Module2 components"""
    logger.info("🧪 Validating Facebook Integration in Module2")
    logger.info("=" * 50)
    
    results = []
    
    # Test 1: Platform Configuration
    try:
        logger.info("1. Testing Platform Configuration...")
        supported = "facebook" in PLATFORM_CONFIG.get("supported_platforms", [])
        features = bool(PLATFORM_CONFIG.get("platform_features", {}).get("facebook"))
        results.append(("Config", supported and features))
        logger.info(f"   ✅ Facebook support: {supported and features}")
    except Exception as e:
        results.append(("Config", False))
        logger.error(f"   ❌ Config test failed: {e}")
    
    # Test 2: Query Handler
    try:
        logger.info("2. Testing Query Handler...")
        handler = SequentialQueryHandler()
        facebook_in_platforms = "facebook" in handler.platforms
        results.append(("Query Handler", facebook_in_platforms))
        logger.info(f"   ✅ Facebook in platforms: {facebook_in_platforms}")
    except Exception as e:
        results.append(("Query Handler", False))
        logger.error(f"   ❌ Query Handler test failed: {e}")
    
    # Test 3: Goal Handler
    try:
        logger.info("3. Testing Goal Handler...")
        goal_handler = EnhancedGoalHandler()
        facebook_in_goals = "facebook" in goal_handler.platforms
        results.append(("Goal Handler", facebook_in_goals))
        logger.info(f"   ✅ Facebook in goal platforms: {facebook_in_goals}")
    except Exception as e:
        results.append(("Goal Handler", False))
        logger.error(f"   ❌ Goal Handler test failed: {e}")
    
    # Test 4: Image Generator
    try:
        logger.info("4. Testing Image Generator...")
        img_gen = ImageGenerator()
        facebook_in_images = "facebook" in img_gen.platforms
        results.append(("Image Generator", facebook_in_images))
        logger.info(f"   ✅ Facebook in image platforms: {facebook_in_images}")
    except Exception as e:
        results.append(("Image Generator", False))
        logger.error(f"   ❌ Image Generator test failed: {e}")
    
    # Test 5: Content Generator
    try:
        logger.info("5. Testing Content Generator...")
        rag_analyzer = DeepRAGAnalyzer()
        content_gen = ContentGenerator(rag_analyzer)
        
        # Test Facebook hashtag generation
        fb_hashtags = content_gen._get_platform_hashtags("facebook", {})
        facebook_hashtags_work = "#Facebook" in fb_hashtags
        results.append(("Content Generator", facebook_hashtags_work))
        logger.info(f"   ✅ Facebook hashtags work: {facebook_hashtags_work}")
    except Exception as e:
        results.append(("Content Generator", False))
        logger.error(f"   ❌ Content Generator test failed: {e}")
    
    # Summary
    logger.info("\n" + "=" * 50)
    logger.info("📊 FACEBOOK INTEGRATION RESULTS")
    logger.info("=" * 50)
    
    passed = 0
    for component, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"{status} - {component}")
        if result:
            passed += 1
    
    total = len(results)
    logger.info("-" * 50)
    logger.info(f"📈 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 Facebook integration is COMPLETE!")
        logger.info("✅ Module2 fully supports Facebook platform")
    else:
        logger.warning("⚠️ Some Facebook integration issues found")
    
    logger.info("=" * 50)
    return passed == total

if __name__ == "__main__":
    success = asyncio.run(validate_facebook_integration())
    exit(0 if success else 1) 