#!/usr/bin/env python3
"""Script to refresh empty profiles with complete data including URLs."""

import json
import logging
import boto3
import time
from botocore.client import Config
from instagram_scraper import InstagramScraper
from config import R2_CONFIG

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_empty_profiles():
    """Get profiles with empty URLs."""
    try:
        s3 = boto3.client(
            's3',
            endpoint_url=R2_CONFIG['endpoint_url'],
            aws_access_key_id=R2_CONFIG['aws_access_key_id'],
            aws_secret_access_key=R2_CONFIG['aws_secret_access_key'],
            config=Config(signature_version='s3v4')
        )
        
        # List all objects in ProfileInfo directory
        response = s3.list_objects_v2(
            Bucket=R2_CONFIG['bucket_name2'],
            Prefix='ProfileInfo/'
        )
        
        empty_profiles = []
        if 'Contents' in response:
            for obj in response['Contents']:
                if obj['Key'].endswith('.json'):
                    response = s3.get_object(Bucket=R2_CONFIG['bucket_name2'], Key=obj['Key'])
                    profile_data = json.loads(response['Body'].read().decode('utf-8'))
                    
                    # Check if profile URLs are empty
                    if not profile_data.get("profilePicUrl") and not profile_data.get("profilePicUrlHD"):
                        username = obj['Key'].replace('ProfileInfo/', '').replace('.json', '')
                        empty_profiles.append(username)
                        print(f"Found empty profile: {username}")
        
        return empty_profiles
    except Exception as e:
        logger.error(f"Error getting empty profiles: {e}")
        return []

def refresh_profiles(usernames):
    """Refresh profiles by scraping and uploading fresh data."""
    if not usernames:
        print("No empty profiles found")
        return []
        
    print(f"\nRefreshing {len(usernames)} profiles: {', '.join(usernames)}")
    
    scraper = InstagramScraper()
    refreshed = []
    
    for username in usernames:
        print(f"\nRefreshing profile for {username}...")
        
        # Scrape the profile
        profile_data = scraper.scrape_profile(username, 1)
        if not profile_data:
            print(f"Failed to scrape profile for {username}")
            continue
            
        # Extract profile info
        profile_info = scraper.extract_short_profile_info(profile_data)
        if not profile_info:
            print(f"Failed to extract profile info for {username}")
            continue
            
        # Check if profile URLs exist in extracted data
        has_profile_pic_url = bool(profile_info.get("profilePicUrl", ""))
        has_profile_pic_url_hd = bool(profile_info.get("profilePicUrlHD", ""))
        
        if not has_profile_pic_url and not has_profile_pic_url_hd:
            print(f"WARNING: Could not find profile URLs for {username}")
            print(f"Available fields: {', '.join(profile_data[0].keys())}")
            continue
            
        # Upload the profile info
        result = scraper.upload_short_profile_to_tasks(profile_info)
        if result:
            print(f"Successfully refreshed profile for {username}")
            print(f"profilePicUrl length: {len(profile_info.get('profilePicUrl', ''))}")
            print(f"profilePicUrlHD length: {len(profile_info.get('profilePicUrlHD', ''))}")
            refreshed.append(username)
        else:
            print(f"Failed to upload profile info for {username}")
    
    return refreshed

if __name__ == "__main__":
    # Get profiles with empty URLs
    empty_profiles = get_empty_profiles()
    
    # If no profiles specified, use default problematic ones
    if not empty_profiles:
        empty_profiles = ["maccosmetics", "fentybeauty", "urbandecaycosmetics", "toofaced"]
        print(f"Using default problematic profiles: {', '.join(empty_profiles)}")
    
    # Refresh the profiles
    refreshed = refresh_profiles(empty_profiles)
    
    # Print summary
    print(f"\nRefresh summary:")
    print(f"Total empty profiles: {len(empty_profiles)}")
    print(f"Successfully refreshed: {len(refreshed)}")
    print(f"Failed to refresh: {len(empty_profiles) - len(refreshed)}")
    
    if refreshed:
        print(f"Refreshed profiles: {', '.join(refreshed)}")
        
    if len(empty_profiles) - len(refreshed) > 0:
        failed = [u for u in empty_profiles if u not in refreshed]
        print(f"Failed profiles: {', '.join(failed)}") 