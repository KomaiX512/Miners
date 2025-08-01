#!/usr/bin/env python3
"""Test script to verify profile URL extraction and export."""

import json
import logging
import time
import boto3
import sys
from datetime import datetime
from botocore.client import Config
from config import R2_CONFIG

# Add the parent directory to sys.path to import InstagramScraper
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from instagram_scraper import InstagramScraper

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def print_profile_data(profile_data, title="Profile Data"):
    """Print profile data in a readable format."""
    print(f"\n--- {title} ---")
    for key, value in sorted(profile_data.items()):
        if key in ["profilePicUrl", "profilePicUrlHD"]:
            print(f"{key}: URL length = {len(str(value))}, empty = {value == ''}")
            if value and len(value) > 0:
                print(f"  URL preview: {value[:50]}...")
        else:
            print(f"{key}: {value}")

def retrieve_exported_profile(username):
    """Retrieve a profile from the tasks bucket."""
    try:
        s3 = boto3.client(
            's3',
            endpoint_url=R2_CONFIG['endpoint_url'],
            aws_access_key_id=R2_CONFIG['aws_access_key_id'],
            aws_secret_access_key=R2_CONFIG['aws_secret_access_key'],
            config=Config(signature_version='s3v4')
        )
        
        profile_key = f"ProfileInfo/{username}.json"
        response = s3.get_object(Bucket=R2_CONFIG['bucket_name2'], Key=profile_key)
        profile_data = json.loads(response['Body'].read().decode('utf-8'))
        return profile_data
    except Exception as e:
        logger.error(f"Error retrieving profile {username}: {str(e)}")
        return None

def test_url_extraction_and_export():
    """Test the profile URL extraction and export process."""
    print("=== Testing Profile URL Extraction and Export ===")
    
    # Test with a few different usernames to ensure consistency
    test_usernames = ["humansofny", "maccosmetics", "fentybeauty"]
    
    # Create scraper instance
    scraper = InstagramScraper()
    
    for username in test_usernames:
        print(f"\n\n>>> Testing username: {username} <<<")
        
        # 1. Scrape profile
        print(f"1. Scraping profile for {username}...")
        profile_data = scraper.scrape_profile(username, 1)
        
        if not profile_data:
            print(f"Failed to scrape profile for {username}, skipping to next username")
            continue
        
        raw_profile = profile_data[0]
        print(f"Successfully scraped profile for {username}")
        
        # 2. Check raw profile for URL fields
        print("\n2. Checking raw profile for URL fields:")
        profile_pic_url = raw_profile.get("profilePicUrl", "")
        profile_pic_url_hd = raw_profile.get("profilePicUrlHD", "")
        
        print(f"profilePicUrl in raw data: {'✓ PRESENT' if profile_pic_url else '❌ MISSING'}")
        if profile_pic_url:
            print(f"  Length: {len(profile_pic_url)}, Preview: {profile_pic_url[:50]}...")
            
        print(f"profilePicUrlHD in raw data: {'✓ PRESENT' if profile_pic_url_hd else '❌ MISSING'}")
        if profile_pic_url_hd:
            print(f"  Length: {len(profile_pic_url_hd)}, Preview: {profile_pic_url_hd[:50]}...")
        
        # 3. Test extract_short_profile_info
        print("\n3. Testing extract_short_profile_info method:")
        short_info = scraper.extract_short_profile_info(profile_data)
        
        if not short_info:
            print(f"Failed to extract short profile info for {username}")
            continue
            
        print(f"Extracted short profile info for {username}")
        print(f"profilePicUrl in extracted data: {'✓ PRESENT' if short_info.get('profilePicUrl') else '❌ MISSING'}")
        print(f"profilePicUrlHD in extracted data: {'✓ PRESENT' if short_info.get('profilePicUrlHD') else '❌ MISSING'}")
        
        # 4. Test upload_short_profile_to_tasks
        print("\n4. Testing upload_short_profile_to_tasks method:")
        # Add unique identifier to avoid conflicts
        test_upload_username = f"{username}_test_{int(time.time())}"
        short_info["username"] = test_upload_username
        
        upload_result = scraper.upload_short_profile_to_tasks(short_info)
        if not upload_result:
            print(f"Failed to upload profile info for {test_upload_username}")
            continue
            
        print(f"Successfully uploaded profile info for {test_upload_username}")
        
        # 5. Retrieve exported profile
        print("\n5. Retrieving exported profile:")
        # Wait a moment for consistency
        time.sleep(2)
        
        exported_profile = retrieve_exported_profile(test_upload_username)
        if not exported_profile:
            print(f"Failed to retrieve exported profile for {test_upload_username}")
            continue
            
        print(f"Successfully retrieved exported profile for {test_upload_username}")
        print(f"profilePicUrl in exported data: {'✓ PRESENT' if exported_profile.get('profilePicUrl') else '❌ MISSING'}")
        if exported_profile.get('profilePicUrl'):
            print(f"  Length: {len(exported_profile['profilePicUrl'])}")
            
        print(f"profilePicUrlHD in exported data: {'✓ PRESENT' if exported_profile.get('profilePicUrlHD') else '❌ MISSING'}")
        if exported_profile.get('profilePicUrlHD'):
            print(f"  Length: {len(exported_profile['profilePicUrlHD'])}")
        
        # Print full profile data
        print_profile_data(exported_profile, f"Exported Profile Data for {test_upload_username}")
        
    print("\n=== Test Complete ===")
    return True

if __name__ == "__main__":
    test_url_extraction_and_export() 