#!/usr/bin/env python3
"""
Test script for the Elite News For You Module
Tests the integration with the main system pipeline.
"""

import sys
import os
import json
import logging
from datetime import datetime
from typing import Dict, List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_news_module_integration():
    """Test the News For You module integration with main system."""
    try:
        logger.info("🧪 Starting News For You Module Integration Test")
        
        # Import the main system
        from main import ContentRecommendationSystem
        
        logger.info("✅ Successfully imported ContentRecommendationSystem")
        
        # Initialize the system
        logger.info("🚀 Initializing ContentRecommendationSystem...")
        manager = ContentRecommendationSystem()
        
        logger.info("✅ ContentRecommendationSystem initialized successfully")
        
        # Test with a tech influencer profile
        test_username = "elonmusk"
        test_platform = "twitter"
        test_account_type = "personal"
        test_posting_style = "casual"
        
        # Mock user posts (typical tech content)
        mock_user_posts = [
            {
                "tweet_text": "Exciting developments in AI and machine learning! #TechInnovation #AI",
                "engagement": 1500,
                "timestamp": "2024-01-15T10:30:00Z"
            },
            {
                "tweet_text": "The future of space exploration is here. Mars mission updates! #SpaceX #Mars",
                "engagement": 2200,
                "timestamp": "2024-01-15T08:15:00Z"
            },
            {
                "tweet_text": "Electric vehicles are revolutionizing transportation. #Tesla #EV #Innovation",
                "engagement": 1800,
                "timestamp": "2024-01-14T16:45:00Z"
            }
        ]
        
        logger.info(f"🎯 Testing News For You module for @{test_username}")
        
        # Test the news generation
        news_result = manager._generate_news_for_you_module(
            username=test_username,
            platform=test_platform,
            account_type=test_account_type,
            posting_style=test_posting_style,
            user_posts=mock_user_posts
        )
        
        if news_result:
            logger.info("✅ News For You module generated results successfully!")
            
            # Analyze the results
            domain_profile = news_result.get('domain_profile', {})
            curated_news = news_result.get('curated_news', [])
            premium_summary = news_result.get('premium_summary', {})
            metadata = news_result.get('curation_metadata', {})
            
            logger.info(f"📊 Domain Analysis:")
            logger.info(f"   - Primary Domain: {domain_profile.get('primary_domain', 'Unknown')}")
            logger.info(f"   - Confidence: {domain_profile.get('confidence', 0):.2f}")
            logger.info(f"   - Categories: {domain_profile.get('categories', [])}")
            logger.info(f"   - Keywords: {domain_profile.get('keywords', [])[:5]}")  # Show first 5
            
            logger.info(f"📰 News Curation Results:")
            logger.info(f"   - Total Fetched: {metadata.get('total_fetched', 0)}")
            logger.info(f"   - After Filtering: {metadata.get('after_filtering', 0)}")
            logger.info(f"   - Final Selection: {metadata.get('final_selection', 0)}")
            logger.info(f"   - Quality Score: {metadata.get('quality_score', 0):.2f}")
            
            logger.info(f"✨ Premium Summary:")
            daily_summary = premium_summary.get('daily_news_summary', [])
            logger.info(f"   - Total Stories: {len(daily_summary)}")
            logger.info(f"   - Curation Quality: {premium_summary.get('curation_quality', 'Unknown')}")
            
            # Show first news item as example
            if daily_summary:
                first_news = daily_summary[0]
                logger.info(f"   - Top Story: {first_news.get('title', 'N/A')}")
                logger.info(f"   - Summary: {first_news.get('summary', 'N/A')[:100]}...")
                logger.info(f"   - Relevance Score: {first_news.get('relevance_score', 0):.2f}")
            
            # Test R2 export
            logger.info("💾 Testing R2 export functionality...")
            export_result = manager._export_news_for_you_to_r2(news_result, test_username, test_platform)
            
            if export_result:
                logger.info("✅ R2 export completed successfully!")
                logger.info(f"   - Export Path: {export_result.get('r2_path', 'Unknown')}")
                logger.info(f"   - File Size: {export_result.get('file_size', 0)} bytes")
            else:
                logger.warning("⚠️ R2 export had issues (might be config-related)")
            
            # Save test results to file
            test_results = {
                'test_timestamp': datetime.now().isoformat(),
                'test_account': f"@{test_username}",
                'platform': test_platform,
                'news_module_results': news_result,
                'export_results': export_result,
                'test_status': 'SUCCESS',
                'summary': {
                    'domain_detected': domain_profile.get('primary_domain'),
                    'news_curated': len(curated_news),
                    'summaries_generated': len(daily_summary),
                    'quality_achieved': metadata.get('quality_score', 0)
                }
            }
            
            with open('news_module_test_results.json', 'w') as f:
                json.dump(test_results, f, indent=2)
            
            logger.info("📝 Test results saved to news_module_test_results.json")
            logger.info("🎉 News For You Module Integration Test PASSED!")
            
            return True
            
        else:
            logger.error("❌ News For You module returned no results")
            return False
            
    except ImportError as e:
        logger.error(f"❌ Import error: {str(e)}")
        logger.error("Make sure all dependencies are installed and main.py is accessible")
        return False
        
    except Exception as e:
        logger.error(f"❌ Test failed with error: {str(e)}")
        logger.exception("Full error traceback:")
        return False

def test_news_api_connectivity():
    """Test direct News API connectivity."""
    try:
        logger.info("🔌 Testing News API connectivity...")
        
        from news_for_you import NewsForYouModule
        from config import R2_CONFIG
        
        # Create a minimal news module instance
        news_module = NewsForYouModule(
            config=R2_CONFIG,
            ai_domain_intel=None,  # Will use fallback
            rag_implementation=None,  # Will use fallback
            vector_db=None  # Will use fallback
        )
        
        # Test basic domain profile creation
        test_domain = news_module._analyze_account_domain_sync(
            username="testuser",
            platform="twitter", 
            account_type="personal",
            user_posts=[]
        )
        
        logger.info(f"✅ Domain analysis working: {test_domain.get('primary_domain')}")
        
        # Test news fetching (this will test News API)
        raw_news = news_module._fetch_todays_trending_news_sync(test_domain)
        
        if raw_news:
            logger.info(f"✅ News API connectivity successful! Fetched {len(raw_news)} articles")
            return True
        else:
            logger.warning("⚠️ News API returned no results (might be API limit or network issue)")
            return False
            
    except Exception as e:
        logger.error(f"❌ News API connectivity test failed: {str(e)}")
        return False

if __name__ == "__main__":
    print("=" * 80)
    print("🚀 ELITE NEWS FOR YOU MODULE - INTEGRATION TEST")
    print("=" * 80)
    
    # Test 1: News API connectivity
    print("\n📡 TEST 1: News API Connectivity")
    print("-" * 40)
    api_test = test_news_api_connectivity()
    
    # Test 2: Full integration test
    print("\n🔧 TEST 2: Full Integration Test")
    print("-" * 40)
    integration_test = test_news_module_integration()
    
    # Final results
    print("\n" + "=" * 80)
    print("📊 FINAL TEST RESULTS")
    print("=" * 80)
    print(f"News API Connectivity: {'✅ PASS' if api_test else '❌ FAIL'}")
    print(f"Full Integration Test: {'✅ PASS' if integration_test else '❌ FAIL'}")
    
    if api_test and integration_test:
        print("\n🎉 ALL TESTS PASSED! News For You Module is ready for production!")
        print("✨ Fourth major module successfully integrated alongside:")
        print("   • Recommendation Module")
        print("   • Competitor Analysis Module") 
        print("   • Next Post Module")
        print("   • News For You Module (NEW!)")
        sys.exit(0)
    else:
        print("\n⚠️ Some tests failed. Check the logs above for details.")
        sys.exit(1)
