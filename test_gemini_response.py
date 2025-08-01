#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main import ContentRecommendationSystem
import logging
import json

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_gemini_response_structure():
    """Check what Gemini is actually returning"""
    logger.info("🧪 TESTING GEMINI RESPONSE STRUCTURE")
    logger.info("="*50)
    
    try:
        # Initialize system
        system = ContentRecommendationSystem()
        
        # Test a single RAG query to see the raw response
        logger.info("🔍 Testing single RAG query to see raw Gemini response")
        
        # Get raw response from RAG
        rag = system.recommendation_generator.rag
        
        # Test with our exact scenario
        username = "Appleass"
        platform = "facebook"
        module_key = "FACEBOOK_PERSONAL"
        
        logger.info(f"📊 Testing {module_key} for {username}")
        
        # Get some competitor data first
        competitor_data = []
        for competitor in ['nike', 'redbull', 'netflix']:
            comp_data = system._scrape_competitor_data(competitor, platform, username)
            if comp_data:
                competitor_data.extend(comp_data[:2])  # Just take 2 posts each
                logger.info(f"✅ Got {len(comp_data)} posts from {competitor}")
        
        logger.info(f"📊 Total competitor data: {len(competitor_data)} posts")
        
        # Try to get a raw response to analyze structure
        instruction_config = rag.module_configs[module_key]
        logger.info(f"📋 Expected modules: {list(instruction_config['output_format'].keys())}")
        
        # Test RAG generation with debug
        test_prompt = f"Generate {module_key} content plan for {username} using competitor data"
        logger.info(f"🔍 Test prompt: {test_prompt}")
        
        # This should help us see what structure Gemini returns
        result = rag.generate_recommendation(
            username=username,
            platform=platform,
            module_key=module_key,
            is_branding=False,
            competitor_data=competitor_data[:5]  # Limited data for faster testing
        )
        
        if result:
            logger.info("✅ Generation successful!")
            logger.info(f"📊 Result keys: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}")
        else:
            logger.error("❌ Generation failed")
                
    except Exception as e:
        logger.error(f"💥 Test failed: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_gemini_response_structure()
