#!/usr/bin/env python3
"""Script to update existing profiles with correct profile image URLs."""

import os
import json
import logging
import time
import boto3
from botocore.client import Config
from instagram_scraper import InstagramScraper
from config import R2_CONFIG

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_s3_client():
    """Create S3 client for R2 storage."""
    client = boto3.client(
        's3',
        endpoint_url=R2_CONFIG['endpoint_url'],
        aws_access_key_id=R2_CONFIG['aws_access_key_id'],
        aws_secret_access_key=R2_CONFIG['aws_secret_access_key'],
        config=Config(signature_version='s3v4')
    )
    return client

def list_existing_profiles(client, bucket='tasks'):
    """List all existing profiles in the ProfileInfo directory."""
    profiles = []
    try:
        response = client.list_objects_v2(
            Bucket=bucket,
            Prefix='ProfileInfo/'
        )
        
        if 'Contents' in response:
            for obj in response['Contents']:
                if obj['Key'].endswith('.json'):
                    username = os.path.basename(obj['Key']).replace('.json', '')
                    profiles.append(username)
                    
        logger.info(f"Found {len(profiles)} existing profiles")
        return profiles
    except Exception as e:
        logger.error(f"Error listing profiles: {str(e)}")
        return []

def get_profile_data(client, username, bucket='tasks'):
    """Get existing profile data from R2."""
    profile_key = f"ProfileInfo/{username}.json"
    try:
        response = client.get_object(
            Bucket=bucket,
            Key=profile_key
        )
        
        profile_json = json.loads(response['Body'].read().decode('utf-8'))
        logger.info(f"Retrieved profile data for {username}")
        return profile_json
    except Exception as e:
        logger.error(f"Error retrieving profile data for {username}: {str(e)}")
        return None

def update_profile_with_urls(client, username, bucket='tasks'):
    """Update a profile with correct profile image URLs."""
    logger.info(f"Updating profile for {username}")
    
    # Get existing profile
    profile_data = get_profile_data(client, username, bucket)
    if not profile_data:
        logger.error(f"Could not retrieve profile for {username}")
        return False
    
    # Check if URLs already exist and are not empty
    if profile_data.get('profilePicUrl') and profile_data.get('profilePicUrlHD'):
        logger.info(f"Profile URLs already exist for {username}")
        return True
    
    # Scrape fresh profile data to get URLs
    scraper = InstagramScraper()
    scraped_data = scraper.scrape_profile(username, 1)
    
    if not scraped_data or not isinstance(scraped_data, list) or len(scraped_data) == 0:
        logger.error(f"Failed to scrape profile for {username}")
        return False
    
    # Extract URLs from scraped data
    scraped_profile = scraped_data[0]
    profile_pic_url = scraped_profile.get('profilePicUrl', '')
    profile_pic_url_hd = scraped_profile.get('profilePicUrlHD', '')
    
    if not profile_pic_url and not profile_pic_url_hd:
        logger.warning(f"No profile URLs found in scraped data for {username}")
        return False
    
    # Update the profile data with new URLs
    profile_data['profilePicUrl'] = profile_pic_url
    profile_data['profilePicUrlHD'] = profile_pic_url_hd
    
    # Save the updated profile data
    profile_key = f"ProfileInfo/{username}.json"
    try:
        client.put_object(
            Bucket=bucket,
            Key=profile_key,
            Body=json.dumps(profile_data, indent=2),
            ContentType='application/json'
        )
        logger.info(f"Successfully updated profile URLs for {username}")
        return True
    except Exception as e:
        logger.error(f"Error updating profile for {username}: {str(e)}")
        return False

def fix_instagram_scraper_url_export():
    """Check and fix the URL export issue in the InstagramScraper class."""
    logger.info("Checking InstagramScraper upload_short_profile_to_tasks method")
    
    # Create a test profile with URLs
    test_profile = {
        "username": f"test_profile_{int(time.time())}",
        "fullName": "Test Profile",
        "biography": "Testing profile URL fix",
        "followersCount": 5000,
        "followsCount": 500,
        "profilePicUrl": "https://example.com/profile.jpg",
        "profilePicUrlHD": "https://example.com/profile_hd.jpg", 
        "private": False,
        "verified": True,
        "extractedAt": time.strftime("%Y-%m-%dT%H:%M:%S.000000")
    }
    
    # Create scraper instance
    scraper = InstagramScraper()
    
    # Upload profile
    result = scraper.upload_short_profile_to_tasks(test_profile)
    if not result:
        logger.error("Failed to upload test profile")
        return False
    
    # Wait for consistency
    time.sleep(3)
    
    # Verify upload
    client = create_s3_client()
    profile_key = f"ProfileInfo/{test_profile['username']}.json"
    try:
        response = client.get_object(
            Bucket=R2_CONFIG['bucket_name2'],
            Key=profile_key
        )
        
        uploaded_profile = json.loads(response['Body'].read().decode('utf-8'))
        
        if (uploaded_profile.get('profilePicUrl') == test_profile['profilePicUrl'] and 
            uploaded_profile.get('profilePicUrlHD') == test_profile['profilePicUrlHD']):
            logger.info("URL export is working correctly in InstagramScraper")
            return True
        else:
            logger.error("Profile URLs not preserved in upload")
            return False
    except Exception as e:
        logger.error(f"Error verifying upload: {str(e)}")
        return False

def update_all_profiles():
    """Update all existing profiles with correct profile image URLs."""
    logger.info("Starting profile URL update for all profiles")
    
    # First fix the Instagram scraper if needed
    fix_result = fix_instagram_scraper_url_export()
    if not fix_result:
        logger.warning("URL export issue may still exist in InstagramScraper")
    
    # Create S3 client
    client = create_s3_client()
    
    # List existing profiles
    profiles = list_existing_profiles(client)
    
    # Update each profile
    success_count = 0
    for username in profiles:
        if update_profile_with_urls(client, username):
            success_count += 1
        # Add a small delay to avoid rate limiting
        time.sleep(1)
    
    logger.info(f"Updated {success_count} out of {len(profiles)} profiles")
    return success_count

if __name__ == "__main__":
    update_all_profiles() 