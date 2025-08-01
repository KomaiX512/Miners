#!/usr/bin/env python3
"""
Main data processing pipeline for the recommendation system.
This script coordinates the data flow and processing steps.
"""

import logging
import os
import sys
from datetime import datetime
from vector_database import VectorDatabaseManager
from main import ContentRecommendationSystem

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(name)s:%(funcName)s:%(lineno)d - %(message)s'
)
logger = logging.getLogger(__name__)

def run_pipeline(object_key=None, username=None, platform='instagram'):
    """
    Execute the recommendation pipeline for the given data.
    
    Args:
        object_key: The key of the object to process in storage
        username: The username to process if no object_key is provided
        platform: The platform (instagram or twitter) to process for
        
    Returns:
        bool: True if processing was successful, False otherwise
    """
    logger.info(f"Starting pipeline for {'object: ' + object_key if object_key else 'username: ' + username} on {platform}")
    
    try:
        # Initialize the content recommendation system
        system = ContentRecommendationSystem()
        
        # IMPROVED: Clear vector database before processing to prevent errors
        logger.info("🧹 Clearing vector database before starting pipeline run")
        vector_db = VectorDatabaseManager()
        clear_result = vector_db.clear_before_new_run()
        if clear_result:
            logger.info("✅ Vector database successfully cleared and reinitialized")
        else:
            logger.warning("⚠️ Vector database clear failed - attempting to continue with caution")
        
        # Process the data based on input type
        if object_key:
            result = system.run_pipeline(object_key=object_key)
        elif username:
            if platform.lower() == 'twitter':
                result = system.process_twitter_username(username)
            else:  # Default to Instagram
                result = system.process_instagram_username(username)
        else:
            logger.error("Either object_key or username must be provided")
            return False
        
        if result:
            logger.info(f"✅ Pipeline completed successfully for {'object: ' + object_key if object_key else 'username: ' + username}")
        else:
            logger.error(f"❌ Pipeline failed for {'object: ' + object_key if object_key else 'username: ' + username}")
        
        return result
    
    except Exception as e:
        logger.error(f"Error in pipeline: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def main():
    """Process command line arguments and run the pipeline."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Run the content recommendation pipeline')
    parser.add_argument('--object', help='Object key to process')
    parser.add_argument('--username', help='Username to process')
    parser.add_argument('--platform', default='instagram', choices=['instagram', 'twitter'], 
                        help='Platform to process (instagram or twitter)')
    
    args = parser.parse_args()
    
    if not args.object and not args.username:
        parser.error("Either --object or --username must be provided")
    
    success = run_pipeline(object_key=args.object, username=args.username, platform=args.platform)
    
    if success:
        logger.info("Pipeline execution completed successfully")
        return 0
    else:
        logger.error("Pipeline execution failed")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 