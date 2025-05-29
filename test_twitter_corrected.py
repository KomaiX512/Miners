#!/usr/bin/env python3
"""
FINAL TEST: Twitter scraper with CORRECTED input format for web.harvester/twitter-scraper
"""

import json
import logging
import sys
import os
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_corrected_twitter_scraper():
    """Test Twitter scraper with the CORRECTED input format."""
    try:
        from twitter_scraper import TwitterScraper
        
        logger.info("="*60)
        logger.info("TESTING CORRECTED TWITTER SCRAPER")
        logger.info("="*60)
        
        # Test with corrected format
        username = "elonmusk"
        
        logger.info(f"1. Testing corrected scraping for {username}...")
        scraper = TwitterScraper()
        
        # This should now use the CORRECT format:
        # {
        #     "startUrls": ["https://x.com/elonmusk"],
        #     "tweetsDesired": 5,
        #     "withReplies": false,
        #     "includeUserInfo": true
        # }
        
        scraped_data = scraper.scrape_profile(username, results_limit=5)
        
        if scraped_data and len(scraped_data) > 0:
            logger.info(f"✅ CORRECTED SCRAPING SUCCESSFUL!")
            logger.info(f"   - Got {len(scraped_data)} items")
            logger.info(f"   - Data type: {type(scraped_data)}")
            
            # Log first item structure
            if len(scraped_data) > 0:
                first_item = scraped_data[0]
                logger.info(f"   - First item keys: {list(first_item.keys()) if isinstance(first_item, dict) else 'Not a dict'}")
            
            # Test profile extraction
            logger.info(f"2. Testing profile extraction...")
            profile_info = scraper.extract_short_profile_info(scraped_data)
            
            if profile_info:
                logger.info(f"✅ PROFILE EXTRACTION SUCCESSFUL!")
                logger.info(f"   - Username: {profile_info.get('username', 'N/A')}")
                logger.info(f"   - Followers: {profile_info.get('follower_count', 'N/A')}")
                logger.info(f"   - Posts: {len(profile_info.get('recent_posts', []))}")
                
                # Test complete pipeline
                logger.info(f"3. Testing complete pipeline...")
                from main import ContentRecommendationSystem
                
                system = ContentRecommendationSystem()
                
                # Create proper account info
                account_info = {
                    "username": username,
                    "account_type": "business", 
                    "posting_style": "informative",
                    "competitors": ["sundarpichai", "sama", "naval"],
                    "platform": "twitter"
                }
                
                processed_data = system.process_twitter_data(scraped_data, account_info)
                
                if processed_data:
                    logger.info(f"✅ PIPELINE PROCESSING SUCCESSFUL!")
                    logger.info(f"   - Account type: {processed_data.get('account_type', 'N/A')}")
                    logger.info(f"   - Posts count: {len(processed_data.get('posts', []))}")
                    logger.info(f"   - Platform: {processed_data.get('platform', 'N/A')}")
                    
                    print(f"\n{'='*60}")
                    print(f"🎉 TWITTER SCRAPER FULLY FUNCTIONAL!")
                    print(f"{'='*60}")
                    print(f"✅ Input format: CORRECTED")
                    print(f"✅ Scraping: WORKING")
                    print(f"✅ Extraction: WORKING") 
                    print(f"✅ Pipeline: WORKING")
                    print(f"✅ Schema: COMPATIBLE")
                    print(f"")
                    print(f"Ready for production use!")
                    return True
                else:
                    logger.error(f"❌ Pipeline processing failed")
                    return False
            else:
                logger.error(f"❌ Profile extraction failed")
                return False
        else:
            logger.error(f"❌ CORRECTED SCRAPING FAILED - No data returned")
            logger.error(f"   This indicates the input format or actor configuration is still incorrect")
            return False
            
    except Exception as e:
        logger.error(f"❌ Test failed with error: {str(e)}")
        import traceback
        logger.error(f"   Traceback: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    success = test_corrected_twitter_scraper()
    if success:
        print(f"\n🎉 ALL TESTS PASSED! Twitter scraper is ready!")
        sys.exit(0)
    else:
        print(f"\n❌ TESTS FAILED! Check logs for details.")
        sys.exit(1) 