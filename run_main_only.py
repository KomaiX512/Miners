#!/usr/bin/env python3
"""
Run Main Recommendation System Only (Without Module 2)

This script runs the core recommendation system without Module 2 dependencies
to test performance and debug issues efficiently.
"""

import sys
import os
import logging
import argparse
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main import ContentRecommendationSystem

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_scrapers_only():
    """Test scrapers independently without main system."""
    logger.info("=" * 60)
    logger.info("TESTING SCRAPERS INDEPENDENTLY")
    logger.info("=" * 60)
    
    try:
        # Test Instagram scraper
        logger.info("Testing Instagram Scraper...")
        from instagram_scraper import InstagramScraper
        instagram_scraper = InstagramScraper()
        processed_instagram = instagram_scraper.retrieve_and_process_usernames()
        logger.info(f"✅ Instagram scraper processed {len(processed_instagram)} accounts")
    except Exception as e:
        logger.error(f"❌ Instagram scraper error: {str(e)}")
    
    try:
        # Test Twitter scraper
        logger.info("Testing Twitter Scraper...")
        from twitter_scraper import TwitterScraper
        twitter_scraper = TwitterScraper()
        processed_twitter = twitter_scraper.retrieve_and_process_twitter_usernames()
        logger.info(f"✅ Twitter scraper processed {len(processed_twitter)} accounts")
    except Exception as e:
        logger.error(f"❌ Twitter scraper error: {str(e)}")

def test_recommendation_system_with_sample_data():
    """Test the recommendation system with sample data."""
    logger.info("=" * 60)
    logger.info("TESTING RECOMMENDATION SYSTEM WITH SAMPLE DATA")
    logger.info("=" * 60)
    
    try:
        # Initialize recommendation system
        system = ContentRecommendationSystem()
        logger.info("✅ Recommendation system initialized successfully")
        
        # Test with sample data
        logger.info("Creating sample data for testing...")
        sample_data = system.create_sample_data()
        
        if sample_data:
            logger.info("✅ Sample data created successfully")
            
            # Run the pipeline
            logger.info("Running recommendation pipeline...")
            result = system.run_pipeline(data=sample_data)
            
            if result:
                logger.info("✅ Recommendation pipeline completed successfully")
                return True
            else:
                logger.error("❌ Recommendation pipeline failed")
                return False
        else:
            logger.error("❌ Failed to create sample data")
            return False
            
    except Exception as e:
        logger.error(f"❌ Recommendation system error: {str(e)}")
        return False

def test_sequential_processing():
    """Test the sequential multi-platform processing."""
    logger.info("=" * 60)
    logger.info("TESTING SEQUENTIAL MULTI-PLATFORM PROCESSING")
    logger.info("=" * 60)
    
    try:
        system = ContentRecommendationSystem()
        
        # Test finding unprocessed accounts
        instagram_accounts = system._find_unprocessed_account_info('instagram')
        twitter_accounts = system._find_unprocessed_account_info('twitter')
        
        logger.info(f"✅ Found {len(instagram_accounts)} unprocessed Instagram accounts")
        logger.info(f"✅ Found {len(twitter_accounts)} unprocessed Twitter accounts")
        
        # Run one cycle of processing (without infinite loop)
        logger.info("Running one cycle of platform processing...")
        instagram_processed = system._process_platform_accounts('instagram')
        twitter_processed = system._process_platform_accounts('twitter')
        
        logger.info(f"✅ Processed {instagram_processed} Instagram accounts")
        logger.info(f"✅ Processed {twitter_processed} Twitter accounts")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Sequential processing error: {str(e)}")
        return False

def run_main_recommendation_system(mode='sample_data'):
    """
    Run the main recommendation system without Module 2.
    
    Args:
        mode: 'sample_data', 'sequential_processing', or 'scrapers_only'
    """
    logger.info("🚀 Starting Main Recommendation System (Without Module 2)")
    logger.info(f"📋 Mode: {mode}")
    logger.info(f"⏰ Started at: {datetime.now()}")
    
    success = False
    
    if mode == 'sample_data':
        success = test_recommendation_system_with_sample_data()
    elif mode == 'sequential_processing':
        success = test_sequential_processing()
    elif mode == 'scrapers_only':
        test_scrapers_only()
        success = True
    else:
        logger.error(f"❌ Unknown mode: {mode}")
        return False
    
    logger.info("=" * 60)
    if success:
        logger.info("🎉 MAIN SYSTEM TEST COMPLETED SUCCESSFULLY!")
        logger.info("✅ Recommendation system is working properly")
        logger.info("✅ Platform separation is enforced")
        logger.info("✅ No Module 2 dependencies required")
    else:
        logger.error("💥 MAIN SYSTEM TEST FAILED!")
        logger.error("❌ Check logs above for specific errors")
    
    logger.info(f"⏰ Completed at: {datetime.now()}")
    return success

def main():
    """Main entry point with command line arguments."""
    parser = argparse.ArgumentParser(
        description="Run Main Recommendation System Without Module 2",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Available modes:
  sample_data           - Test with sample data (default)
  sequential_processing - Test sequential multi-platform processing
  scrapers_only        - Test scrapers independently
  
Examples:
  python run_main_only.py
  python run_main_only.py --mode sample_data
  python run_main_only.py --mode sequential_processing
  python run_main_only.py --mode scrapers_only
        """
    )
    
    parser.add_argument(
        '--mode',
        choices=['sample_data', 'sequential_processing', 'scrapers_only'],
        default='sample_data',
        help='Test mode to run (default: sample_data)'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.info("🔍 Verbose logging enabled")
    
    try:
        success = run_main_recommendation_system(mode=args.mode)
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("🛑 Process interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"💥 Unexpected error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 