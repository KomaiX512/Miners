#!/usr/bin/env python3
import json
import logging
from main import ContentRecommendationSystem
from data_retrieval import DataRetrieval

logging.basicConfig(level=logging.INFO)


def simulate(platform, username, competitors):
    """
    Simulate a full pipeline run for a given platform and user, starting from data retrieval
    (skipping scraping stage), and verify content_plan output.
    """
    logger = logging.getLogger(__name__)
    logger.info(f"\n=== Simulating {platform.upper()} pipeline for '{username}' with competitors {competitors} ===")

    # Initialize systems
    crs = ContentRecommendationSystem()
    dr = DataRetrieval()

    # Step 1: Retrieve raw data (assumes data already scraped and stored)
    raw_data = dr.get_social_media_data(username, platform=platform)
    if not raw_data:
        logger.error(f"No raw data found for {username} on {platform}. Ensure data retrieval files exist.")
        return

    # Step 2: Prepare account_info with competitors
    account_info = {
        'username': username,
        'accountType': 'branding',      # adjust as needed
        'postingStyle': 'default',       # adjust as needed
        'competitors': competitors,
        'platform': platform
    }

    # Step 3: Process data (skip scraping, directly use raw_data)
    if platform == 'twitter':
        processed = crs.process_twitter_data(raw_data, account_info, authoritative_primary_username=username)
    elif platform == 'instagram':
        processed = crs.process_instagram_data(raw_data, account_info, authoritative_primary_username=username)
    elif platform == 'facebook':
        processed = crs.process_facebook_data(raw_data, account_info, authoritative_primary_username=username)
    else:
        logger.error(f"Unsupported platform: {platform}")
        return

    if not processed or not processed.get('posts'):
        logger.error(f"Processed data invalid or empty for {username} on {platform}.")
        return

    # Step 4: Run full recommendation pipeline
    success = crs.run_pipeline(data=processed)
    if not success:
        logger.error(f"Pipeline failed for {username} on {platform}.")
        return

    # Step 5: Load and display content_plan.json
    content_plan_file = 'content_plan.json'
    try:
        with open(content_plan_file, 'r') as f:
            cp = json.load(f)
    except Exception as e:
        logger.error(f"Failed to load content_plan.json: {e}")
        return

    # Verify modules
    modules = []
    if 'next_post_prediction' in cp:
        modules.append('next_post_prediction')
    if 'recommendation' in cp or 'recommendations' in cp:
        modules.append('recommendation')
    if 'competitor_analysis' in cp:
        modules.append('competitor_analysis')

    logger.info(f"Modules present in content_plan for {username} on {platform}: {modules}")
    logger.info(f"Endpoints check complete.\n")


if __name__ == '__main__':
    simulate('twitter', 'geoffreyhinton', ['elonmusk', 'ylecun', 'sama'])
    simulate('instagram', 'fentybeauty', ['toofaced', 'narsissist', 'maccosmetics'])
    simulate('facebook', 'netflix', ['cocacola', 'redbull', 'nike'])
