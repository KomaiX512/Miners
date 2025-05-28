#!/usr/bin/env python3
"""Test script to validate Twitter and Instagram conditional processing functionality."""

import sys
import logging
import argparse
import json
import os
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_instagram_conditional():
    """Test Instagram conditional scraping."""
    from instagram_scraper import InstagramScraper
    from main import ContentRecommendationSystem
    
    logger.info("Testing Instagram conditional scraping...")
    
    # Test username
    username = "maccosmetics"
    
    try:
        # First, try direct scraping
        scraper = InstagramScraper()
        scrape_result = scraper.scrape_and_upload(username, results_limit=5)
        
        if not scrape_result.get("success", False):
            logger.error(f"❌ Instagram scraping failed: {scrape_result.get('message', 'Unknown error')}")
            return False
        
        logger.info(f"✅ Instagram scraping successful for {username}")
        
        # Now test the processing pipeline
        system = ContentRecommendationSystem()
        result = system.process_instagram_username(username)
        
        if not result.get("success", False):
            logger.error(f"❌ Instagram processing failed: {result.get('message', 'Unknown error')}")
            return False
        
        logger.info(f"✅ Instagram processing successful for {username}")
        logger.info(f"📊 Posts analyzed: {result.get('details', {}).get('posts_analyzed', 'N/A')}")
        logger.info(f"💡 Recommendations count: {result.get('details', {}).get('recommendations_count', 'N/A')}")
        
        return True
    except Exception as e:
        logger.error(f"❌ Error in Instagram conditional test: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def test_twitter_conditional_local():
    """Test Twitter conditional scraping using local files without R2 storage."""
    try:
        from twitter_scraper import TwitterScraper
        from main import ContentRecommendationSystem
        
        logger.info("Testing Twitter conditional scraping (local mode)...")
        
        # Test username
        username = "elonmusk"
        
        # First, try direct scraping with test_local=True to bypass R2 operations
        scraper = TwitterScraper(test_local=True)
        raw_data = scraper.scrape_profile(username, results_limit=5)
        
        if not raw_data:
            logger.error(f"❌ Twitter scraping failed for {username}")
            return False
        
        # Save data to local test file
        test_dir = "temp/test_twitter"
        os.makedirs(test_dir, exist_ok=True)
        test_file = f"{test_dir}/{username}.json"
        
        with open(test_file, 'w') as f:
            json.dump(raw_data, f)
            
        logger.info(f"✅ Twitter scraping successful for {username}, saved to {test_file}")
        
        # Extract profile info
        profile_info = scraper.extract_short_profile_info(raw_data)
        
        if not profile_info:
            logger.error(f"❌ Failed to extract profile info for {username}")
            return False
            
        logger.info(f"✅ Successfully extracted Twitter profile info:")
        logger.info(f"👤 Username: {profile_info.get('username')}")
        logger.info(f"📊 Follower count: {profile_info.get('follower_count')}")
        logger.info(f"💬 Tweet count: {profile_info.get('tweet_count')}")
        
        # Test tweet processing
        from main import ContentRecommendationSystem
        system = ContentRecommendationSystem()
        processed_data = system.process_twitter_data(raw_data)
        
        if not processed_data:
            logger.error(f"❌ Failed to process Twitter data")
            return False
            
        logger.info(f"✅ Successfully processed Twitter data:")
        logger.info(f"📊 Processed {len(processed_data.get('posts', []))} tweets")
        
        return True
    except ImportError:
        logger.error("❌ Twitter scraper not available")
        return False
    except Exception as e:
        logger.error(f"❌ Error in Twitter conditional test: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def test_twitter_scraper_new_actor():
    """Test the new Twitter actor specifically."""
    try:
        from twitter_scraper import TwitterScraper
        
        logger.info("Testing Twitter scraper with new actor...")
        
        # Test username
        username = "elonmusk"
        
        # Create scraper instance with test_local=True to bypass R2 operations
        scraper = TwitterScraper(test_local=True)
        
        # Test scrape_profile function
        logger.info(f"Scraping Twitter profile: {username}")
        raw_data = scraper.scrape_profile(username, results_limit=5)
        
        if not raw_data:
            logger.error(f"❌ Twitter actor failed to scrape {username}")
            return False
        
        logger.info(f"✅ Twitter actor successfully scraped {username}, got {len(raw_data)} items")
        
        # Test profile info extraction
        profile_info = scraper.extract_short_profile_info(raw_data)
        
        if not profile_info:
            logger.error(f"❌ Failed to extract Twitter profile info for {username}")
            return False
        
        logger.info(f"✅ Successfully extracted Twitter profile info for {profile_info.get('username', 'unknown')}")
        logger.info(f"📊 Follower count: {profile_info.get('follower_count', 0)}")
        logger.info(f"📊 Recent posts: {len(profile_info.get('recent_posts', []))}")
        
        return True
    except ImportError:
        logger.error("❌ Twitter scraper not available")
        return False
    except Exception as e:
        logger.error(f"❌ Error in Twitter scraper test: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def main():
    """Main test function."""
    parser = argparse.ArgumentParser(description="Test conditional scraping functionality")
    parser.add_argument('--platform', type=str, choices=['instagram', 'twitter', 'all'], default='all',
                        help="Platform to test (instagram, twitter, or all)")
    parser.add_argument('--local', action='store_true', help="Run in local-only mode (bypass R2 storage)")
    
    args = parser.parse_args()
    
    start_time = datetime.now()
    logger.info(f"Starting conditional scraping tests at {start_time} for platform: {args.platform}")
    
    results = {}
    
    if args.platform in ['instagram', 'all'] and not args.local:
        instagram_result = test_instagram_conditional()
        results['instagram'] = instagram_result
        logger.info(f"Instagram test {'passed' if instagram_result else 'failed'}")
    
    if args.platform in ['twitter', 'all']:
        if args.local:
            twitter_result = test_twitter_conditional_local()
            results['twitter_local'] = twitter_result
            logger.info(f"Twitter local test {'passed' if twitter_result else 'failed'}")
        else:
            twitter_result = test_twitter_conditional()
            results['twitter'] = twitter_result
            logger.info(f"Twitter test {'passed' if twitter_result else 'failed'}")
        
        twitter_actor_result = test_twitter_scraper_new_actor()
        results['twitter_actor'] = twitter_actor_result
        logger.info(f"Twitter actor test {'passed' if twitter_actor_result else 'failed'}")
    
    end_time = datetime.now()
    duration = end_time - start_time
    logger.info(f"All tests completed in {duration.total_seconds():.2f} seconds")
    
    # Print summary
    print("\n===== TEST SUMMARY =====")
    for test_name, result in results.items():
        print(f"{test_name}: {'✅ PASS' if result else '❌ FAIL'}")
    print("=======================")
    
    # Return success only if all tests passed
    return all(results.values())

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 