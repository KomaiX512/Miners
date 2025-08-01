#!/usr/bin/env python3
"""
CACHE CLEARER AND FRESH VALIDATION
Clears RAG cache and forces fresh content generation to eliminate template responses.
"""

import sys
import os
import json
import logging
from datetime import datetime

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the main system
from main import ContentRecommendationSystem

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def clear_rag_cache():
    """Clear RAG cache to force fresh content generation."""
    logger.info("🧹 CLEARING RAG CACHE to eliminate template responses")
    
    try:
        # Initialize system to access RAG
        system = ContentRecommendationSystem()
        
        # Clear caches in rate limiter
        if hasattr(system.rag, 'rate_limiter') and hasattr(system.rag.rate_limiter, 'request_cache'):
            cache_size = len(system.rag.rate_limiter.request_cache)
            system.rag.rate_limiter.request_cache.clear()
            logger.info(f"✅ Cleared rate limiter cache: {cache_size} entries")
        
        # Clear caches in RAG implementation
        if hasattr(system.rag, 'request_cache'):
            cache_size = len(system.rag.request_cache)
            system.rag.request_cache.clear()
            logger.info(f"✅ Cleared RAG implementation cache: {cache_size} entries")
            
        # Clear any recommendation generation caches
        if hasattr(system.recommendation_generator, 'rag') and hasattr(system.recommendation_generator.rag, 'request_cache'):
            cache_size = len(system.recommendation_generator.rag.request_cache)
            system.recommendation_generator.rag.request_cache.clear()
            logger.info(f"✅ Cleared recommendation generator cache: {cache_size} entries")
            
        logger.info("🎯 ALL CACHES CLEARED - Fresh content generation guaranteed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error clearing cache: {str(e)}")
        return False

def test_single_platform_fresh():
    """Test one platform with fresh content generation."""
    logger.info("🔥 TESTING FRESH CONTENT GENERATION - TWITTER")
    
    try:
        # Create mock account info
        account_info = {
            'username': 'geoffreyhinton',
            'accountType': 'branding',
            'postingStyle': 'professional',
            'competitors': ['elonmusk', 'ylecun', 'sama'],
            'platform': 'twitter'
        }
        
        system = ContentRecommendationSystem()
        
        # Get data
        raw_data = system.data_retriever.get_twitter_data('geoffreyhinton')
        if not raw_data:
            logger.error("❌ No data found")
            return False
            
        processed_data = system.process_twitter_data(
            raw_data=raw_data,
            account_info=account_info,
            authoritative_primary_username='geoffreyhinton'
        )
        
        if not processed_data:
            logger.error("❌ Data processing failed")
            return False
        
        # Ensure correct data
        processed_data['platform'] = 'twitter'
        processed_data['primary_username'] = 'geoffreyhinton'
        
        logger.info(f"✅ Data processed: {len(processed_data.get('posts', []))} posts")
        
        # Run pipeline
        result = system.run_pipeline(data=processed_data)
        
        if not result:
            logger.error("❌ Pipeline failed")
            return False
        
        # Read and validate content_plan.json
        try:
            with open('content_plan.json', 'r') as f:
                content_plan = json.load(f)
        except Exception as e:
            logger.error(f"❌ Failed to read content_plan.json: {str(e)}")
            return False
        
        # Check for template patterns
        improvements = content_plan.get('improvement_recommendations', {})
        recommendations = improvements.get('recommendations', [])
        
        template_patterns = [
            "see some fascinating",
            "outshine them by",
            "become the leading voice"
        ]
        
        template_found = False
        for i, rec in enumerate(recommendations):
            for pattern in template_patterns:
                if pattern in rec.lower():
                    logger.error(f"❌ TEMPLATE PATTERN FOUND #{i+1}: {pattern} in {rec[:50]}...")
                    template_found = True
        
        if template_found:
            logger.error("💥 TEMPLATE PATTERNS STILL PRESENT - Cache clear failed")
            return False
        else:
            logger.info("🎉 SUCCESS: No template patterns found - Fresh content generated!")
            
            # Show sample recommendations
            logger.info("📋 SAMPLE FRESH RECOMMENDATIONS:")
            for i, rec in enumerate(recommendations[:3], 1):
                logger.info(f"   {i}. {rec[:80]}...")
                
            return True
        
    except Exception as e:
        logger.error(f"❌ Error in fresh test: {str(e)}")
        return False

def main():
    """Main function."""
    logger.info("🔥 CACHE CLEARER AND FRESH VALIDATION")
    logger.info("🎯 Goal: Eliminate template responses and generate fresh content")
    logger.info("=" * 80)
    
    # Step 1: Clear cache
    if not clear_rag_cache():
        logger.error("💥 Failed to clear cache")
        return False
    
    # Step 2: Test fresh generation
    if not test_single_platform_fresh():
        logger.error("💥 Fresh generation test failed")
        return False
    
    logger.info("🎉🎉🎉 SUCCESS: Cache cleared and fresh content generated!")
    return True

if __name__ == "__main__":
    main()
