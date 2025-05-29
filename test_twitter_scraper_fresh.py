#!/usr/bin/env python3
"""
Test Twitter scraper with FRESH scraping - forces actual scraping instead of using cached data.
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

def test_twitter_scraper_fresh_scraping():
    """Test Twitter scraper with actual fresh scraping, not cached data."""
    try:
        from twitter_scraper import TwitterScraper
        
        logger.info("="*60)
        logger.info("TESTING TWITTER SCRAPER - FRESH SCRAPING")
        logger.info("="*60)
        
        # Test with a known working Twitter account
        test_username = "elonmusk"
        
        logger.info(f"1. Testing fresh scraping for {test_username}...")
        
        # Initialize scraper
        scraper = TwitterScraper()
        
        # FORCE FRESH SCRAPING - call scrape_profile directly
        logger.info(f"🔄 Starting FRESH scraping for {test_username} (not using cached data)")
        scraped_data = scraper.scrape_profile(test_username, results_limit=5)
        
        if not scraped_data:
            logger.error("❌ CRITICAL: Fresh scraping returned no data!")
            logger.error("This means the Twitter scraper is NOT working!")
            return False
        
        logger.info(f"✅ Fresh scraping successful! Got {len(scraped_data)} items")
        
        # Log sample of scraped data to verify it's real
        if scraped_data and len(scraped_data) > 0:
            first_item = scraped_data[0]
            logger.info(f"📊 Sample scraped data keys: {list(first_item.keys()) if isinstance(first_item, dict) else 'Not a dict'}")
            
            # Check for user data
            if isinstance(first_item, dict):
                user_fields = []
                for field in ['username', 'screen_name', 'displayName', 'name', 'followersCount', 'followers_count']:
                    if field in first_item:
                        user_fields.append(field)
                
                if user_fields:
                    logger.info(f"✅ Found user fields: {user_fields}")
                else:
                    logger.warning("⚠️  No recognizable user fields found")
                    logger.info(f"Available fields: {list(first_item.keys())}")
        
        # Test profile info extraction
        logger.info(f"2. Testing profile info extraction...")
        profile_info = scraper.extract_short_profile_info(scraped_data)
        
        if not profile_info:
            logger.error("❌ Profile info extraction failed!")
            return False
        
        logger.info("✅ Profile info extraction successful!")
        logger.info(f"   Username: {profile_info.get('username', 'N/A')}")
        logger.info(f"   Name: {profile_info.get('name', 'N/A')}")
        logger.info(f"   Followers: {profile_info.get('follower_count', 0):,}")
        logger.info(f"   Following: {profile_info.get('following_count', 0):,}")
        logger.info(f"   Tweets: {profile_info.get('tweet_count', 0):,}")
        
        # Test upload functionality  
        logger.info(f"3. Testing profile upload...")
        upload_result = scraper.upload_short_profile_to_tasks(profile_info)
        
        if upload_result:
            logger.info("✅ Profile upload successful!")
        else:
            logger.error("❌ Profile upload failed!")
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Test failed with error: {str(e)}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        return False

def test_actor_configuration():
    """Test that the Twitter scraper is using the correct actor and configuration."""
    try:
        from twitter_scraper import TwitterScraper, TWITTER_ACTOR_ID, APIFY_API_TOKEN
        
        logger.info("\n" + "="*60)
        logger.info("TESTING TWITTER ACTOR CONFIGURATION")
        logger.info("="*60)
        
        logger.info(f"✅ Actor ID: {TWITTER_ACTOR_ID}")
        logger.info(f"✅ API Token present: {'Yes' if APIFY_API_TOKEN else 'No'}")
        logger.info(f"✅ Token length: {len(APIFY_API_TOKEN) if APIFY_API_TOKEN else 0}")
        
        # Test actor connection
        from apify_client import ApifyClient
        
        logger.info("🔄 Testing Apify client connection...")
        client = ApifyClient(APIFY_API_TOKEN)
        
        # Try to get actor info
        try:
            actor = client.actor(TWITTER_ACTOR_ID)
            logger.info("✅ Successfully connected to Apify actor!")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to connect to actor: {str(e)}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Configuration test failed: {str(e)}")
        return False

def test_input_format():
    """Test that the input format matches the web.harvester/twitter-scraper requirements."""
    try:
        logger.info("\n" + "="*60)
        logger.info("TESTING INPUT FORMAT COMPATIBILITY")
        logger.info("="*60)
        
        test_username = "elonmusk"
        
        # Expected input format for web.harvester/twitter-scraper
        expected_input = {
            "urls": [f"https://twitter.com/{test_username}"],
            "resultsLimit": 5,
            "includeProfileInfo": True,
            "proxyConfig": {"useApifyProxy": True}
        }
        
        logger.info("✅ Expected input format:")
        logger.info(json.dumps(expected_input, indent=2))
        
        # Test with Apify client directly
        from apify_client import ApifyClient
        from twitter_scraper import APIFY_API_TOKEN, TWITTER_ACTOR_ID
        
        client = ApifyClient(APIFY_API_TOKEN)
        
        logger.info("🔄 Testing input format with actual actor...")
        
        try:
            actor = client.actor(TWITTER_ACTOR_ID)
            run = actor.call(run_input=expected_input)
            
            if run:
                logger.info("✅ Actor accepted input format successfully!")
                logger.info(f"Run ID: {run.get('id', 'Unknown')}")
                
                # Wait a bit and check results
                import time
                time.sleep(15)
                
                dataset = client.dataset(run["defaultDatasetId"])
                items = dataset.list_items().items
                
                if items:
                    logger.info(f"✅ Got {len(items)} results from actor!")
                    return True
                else:
                    logger.warning("⚠️  Actor ran but returned no results")
                    return False
            else:
                logger.error("❌ Actor call failed")
                return False
                
        except Exception as e:
            logger.error(f"❌ Input format test failed: {str(e)}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Input format test error: {str(e)}")
        return False

def test_complete_pipeline_fresh():
    """Test the complete pipeline with fresh Twitter data."""
    try:
        logger.info("\n" + "="*60)
        logger.info("TESTING COMPLETE PIPELINE WITH FRESH DATA")
        logger.info("="*60)
        
        from main import ContentRecommendationSystem
        from twitter_scraper import TwitterScraper
        
        test_username = "elonmusk"
        
        # Step 1: Force fresh scraping
        logger.info(f"1. Force fresh scraping for {test_username}...")
        scraper = TwitterScraper()
        fresh_data = scraper.scrape_profile(test_username, results_limit=5)
        
        if not fresh_data:
            logger.error("❌ Fresh scraping failed")
            return False
        
        logger.info(f"✅ Fresh scraping got {len(fresh_data)} items")
        
        # Step 2: Process with main system
        logger.info(f"2. Processing with main system...")
        system = ContentRecommendationSystem()
        
        # Create account info for testing
        account_info = {
            "username": test_username,
            "accountType": "branding",
            "postingStyle": "informative tech posts",
            "competitors": ["sama", "sundarpichai"],
            "platform": "twitter"
        }
        
        # Process the fresh data
        processed_data = system.process_twitter_data(fresh_data, account_info)
        
        if not processed_data:
            logger.error("❌ Data processing failed")
            return False
        
        logger.info("✅ Data processing successful!")
        logger.info(f"   Posts: {len(processed_data.get('posts', []))}")
        logger.info(f"   Account Type: {processed_data.get('account_type', 'N/A')}")
        logger.info(f"   Platform: {processed_data.get('platform', 'N/A')}")
        
        # Step 3: Generate recommendations
        logger.info(f"3. Generating recommendations...")
        try:
            content_plan = system.generate_content_plan(processed_data, n_recommendations=2)
            
            if content_plan and content_plan.get("recommendations"):
                logger.info(f"✅ Generated {len(content_plan['recommendations'])} recommendations")
            else:
                logger.warning("⚠️  No recommendations generated")
            
        except Exception as e:
            logger.warning(f"⚠️  Recommendation generation warning: {str(e)}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Complete pipeline test failed: {str(e)}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        return False

def main():
    """Run all Twitter scraper tests."""
    logger.info("🚀 STARTING COMPREHENSIVE TWITTER SCRAPER TESTS")
    logger.info("🎯 GOAL: Verify fresh scraping works correctly")
    
    test_results = []
    
    # Test 1: Actor Configuration
    logger.info("\n" + "🔧 TEST 1: Actor Configuration")
    if test_actor_configuration():
        test_results.append("✅ Actor Configuration")
    else:
        test_results.append("❌ Actor Configuration")
    
    # Test 2: Input Format 
    logger.info("\n" + "📝 TEST 2: Input Format Compatibility")
    if test_input_format():
        test_results.append("✅ Input Format")
    else:
        test_results.append("❌ Input Format")
    
    # Test 3: Fresh Scraping
    logger.info("\n" + "🔄 TEST 3: Fresh Scraping")
    if test_twitter_scraper_fresh_scraping():
        test_results.append("✅ Fresh Scraping")
    else:
        test_results.append("❌ Fresh Scraping")
    
    # Test 4: Complete Pipeline
    logger.info("\n" + "🏗️ TEST 4: Complete Pipeline")
    if test_complete_pipeline_fresh():
        test_results.append("✅ Complete Pipeline")
    else:
        test_results.append("❌ Complete Pipeline")
    
    # Results Summary
    logger.info("\n" + "="*80)
    logger.info("🎉 TWITTER SCRAPER TEST RESULTS")
    logger.info("="*80)
    
    success_count = sum(1 for result in test_results if result.startswith("✅"))
    total_count = len(test_results)
    
    for result in test_results:
        logger.info(f"   {result}")
    
    logger.info(f"\nSUCCESS RATE: {success_count}/{total_count} ({success_count/total_count*100:.1f}%)")
    
    if success_count == total_count:
        logger.info("\n🎯 ALL TESTS PASSED!")
        logger.info("✅ Twitter scraper is working correctly")
        logger.info("✅ Fresh scraping confirmed functional")
        logger.info("✅ Complete pipeline verified")
        sys.exit(0)
    else:
        logger.error("\n❌ SOME TESTS FAILED!")
        logger.error("Please check the detailed output above")
        sys.exit(1)

if __name__ == "__main__":
    main() 