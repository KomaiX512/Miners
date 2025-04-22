#!/usr/bin/env python3
"""Test script to verify profile URL preservation when exporting profile info."""

import json
import logging
import time
import boto3
from botocore.client import Config
from datetime import datetime
from config import R2_CONFIG
from main import ContentRecommendationSystem
from instagram_scraper import InstagramScraper

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
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

def retrieve_profile(username):
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

def test_profile_preservation():
    """Test that profile URLs are preserved when exporting profile info."""
    print("=== Testing Profile URL Preservation ===")
    
    # Test with a specific username 
    test_username = "urbandecaycosmetics"
    
    # Create instances
    scraper = InstagramScraper()
    cms = ContentRecommendationSystem()
    
    # Step 1: Create fresh profile with URLs by scraping
    print(f"1. Creating fresh profile for {test_username} with URLs...")
    # Scrape and upload profile to ensure it has URLs
    profile_data = scraper.scrape_profile(test_username, 1)
    if not profile_data:
        print(f"Failed to scrape profile for {test_username}")
        return False
        
    # Verify URLs are in the raw data
    raw_profile = profile_data[0]
    has_raw_profile_pic_url = "profilePicUrl" in raw_profile and raw_profile["profilePicUrl"]
    has_raw_profile_pic_url_hd = "profilePicUrlHD" in raw_profile and raw_profile["profilePicUrlHD"]
    
    print(f"Raw data has profilePicUrl: {has_raw_profile_pic_url}")
    print(f"Raw data has profilePicUrlHD: {has_raw_profile_pic_url_hd}")
    
    if not has_raw_profile_pic_url and not has_raw_profile_pic_url_hd:
        print("ERROR: Raw data doesn't contain profile URLs. Test cannot proceed.")
        return False
    
    # Extract profile info
    profile_info = scraper.extract_short_profile_info(profile_data)
    if not profile_info:
        print(f"Failed to extract profile info for {test_username}")
        return False
    
    # Upload profile with URLs
    upload_result = scraper.upload_short_profile_to_tasks(profile_info)
    if not upload_result:
        print(f"Failed to upload profile info for {test_username}")
        return False
    
    print(f"Successfully created fresh profile for {test_username} with URLs")
    
    # Wait for consistency
    print("Waiting 5 seconds for consistency...")
    time.sleep(5)
    
    # Step 2: Retrieve the profile to verify URLs are there
    print(f"\n2. Retrieving profile to verify URLs...")
    current_profile = retrieve_profile(test_username)
    if not current_profile:
        print(f"Failed to retrieve profile for {test_username}")
        return False
    
    # Print current profile data
    print_profile_data(current_profile, f"Current Profile for {test_username}")
    
    # Check if profile URLs exist
    has_profile_pic_url = bool(current_profile.get("profilePicUrl", ""))
    has_profile_pic_url_hd = bool(current_profile.get("profilePicUrlHD", ""))
    
    print(f"Profile has profilePicUrl: {has_profile_pic_url}")
    print(f"Profile has profilePicUrlHD: {has_profile_pic_url_hd}")
    
    if not has_profile_pic_url and not has_profile_pic_url_hd:
        print("ERROR: Profile doesn't have URLs after upload. Test cannot proceed.")
        return False
    
    # Store URL values for comparison later
    original_profile_pic_url = current_profile.get("profilePicUrl", "")
    original_profile_pic_url_hd = current_profile.get("profilePicUrlHD", "")
    
    # Step 3: Create a new partial profile without URLs
    print("\n3. Creating a new partial profile without URLs...")
    partial_profile = {
        "username": test_username,
        "fullName": current_profile.get("fullName", "Test Name"),
        "biography": current_profile.get("biography", "Test Biography"),
        "followersCount": current_profile.get("followersCount", 1000),
        "followsCount": current_profile.get("followsCount", 500),
        # Deliberately omitting profilePicUrl and profilePicUrlHD
    }
    
    # Step 4: Export the partial profile
    print("\n4. Exporting the partial profile...")
    result = cms.export_profile_info(partial_profile, test_username)
    
    if not result:
        print("Failed to export profile info")
        return False
    
    print("Successfully exported profile info")
    
    # Step 5: Retrieve the updated profile
    print("\n5. Retrieving the updated profile...")
    # Wait for consistency
    print("Waiting 5 seconds for consistency...")
    time.sleep(5)
    
    updated_profile = retrieve_profile(test_username)
    if not updated_profile:
        print(f"Failed to retrieve updated profile for {test_username}")
        return False
    
    # Print updated profile data
    print_profile_data(updated_profile, f"Updated Profile for {test_username}")
    
    # Step 6: Verify that profile URLs were preserved
    print("\n6. Verifying that profile URLs were preserved...")
    updated_profile_pic_url = updated_profile.get("profilePicUrl", "")
    updated_profile_pic_url_hd = updated_profile.get("profilePicUrlHD", "")
    
    urls_preserved = (original_profile_pic_url == updated_profile_pic_url) and (original_profile_pic_url_hd == updated_profile_pic_url_hd)
    
    print(f"Original profilePicUrl length: {len(original_profile_pic_url)}")
    print(f"Updated profilePicUrl length: {len(updated_profile_pic_url)}")
    print(f"Original profilePicUrlHD length: {len(original_profile_pic_url_hd)}")
    print(f"Updated profilePicUrlHD length: {len(updated_profile_pic_url_hd)}")
    
    if urls_preserved:
        print("SUCCESS: Profile URLs were preserved exactly!")
    else:
        print("FAILURE: Profile URLs were not preserved correctly.")
    
    return urls_preserved

if __name__ == "__main__":
    result = test_profile_preservation()
    print(f"\n=== Test {'PASSED' if result else 'FAILED'} ===")
    exit(0 if result else 1) 