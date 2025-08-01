#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main import ContentRecommendationSystem
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_data_structure_fix():
    """Test the data structure fix for competitor data retrieval"""
    logger.info("🧪 TESTING DATA STRUCTURE FIX")
    logger.info("="*50)
    
    try:
        # Initialize system
        system = ContentRecommendationSystem()
        
        # Test Schema 1 vs Schema 2 retrieval
        logger.info("🔍 Testing competitor data retrieval with different schemas")
        
        competitors = ['nike', 'redbull', 'netflix']
        primary_username = 'Appleass'
        platform = 'facebook'
        
        for competitor in competitors:
            logger.info(f"\n📊 Testing {competitor}:")
            
            # Test the _scrape_competitor_data method directly
            result = system._scrape_competitor_data(
                competitor_username=competitor,
                platform=platform, 
                primary_username=primary_username
            )
            
            if result:
                logger.info(f"✅ {competitor}: Data found! {len(result)} posts")
                # Show sample
                if isinstance(result, list) and len(result) > 0:
                    sample = result[0]
                    text = sample.get('text', 'No text')[:80]
                    engagement = sample.get('engagement', 'No engagement')
                    logger.info(f"📝 Sample: {text}...")
                    logger.info(f"💰 Engagement: {engagement}")
            else:
                logger.error(f"❌ {competitor}: No data found")
        
        logger.info("\n" + "="*50)
        logger.info("🎯 DATA STRUCTURE FIX TEST COMPLETE")
                
    except Exception as e:
        logger.error(f"💥 Test failed: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_data_structure_fix()
