#!/usr/bin/env python3
"""Script to test profile URL extraction and export."""

import logging
import json
import os
import time
from instagram_scraper import InstagramScraper
from main import ContentRecommendationSystem
import boto3
from botocore.client import Config
from config import R2_CONFIG

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def print_profile_data(profile_data, label="Profile Data"):
    """Pretty print profile data."""
    print(f"\n=== {label} ===")
    if not profile_data:
        print("No profile data available")
        return
        
    for key, value in profile_data.items():
        if key in ["profilePicUrl", "profilePicUrlHD"]:
            # Print URL keys with special formatting
            print(f"{key}: '{value}'")
        else:
            print(f"{key}: {value}")

def verify_exported_profile(username, bucket='tasks'):
    """Verify profile data was exported correctly."""
    print(f"\n=== Verifying Exported Profile for {username} ===")
    
    # Create S3 client
    client = boto3.client(
        's3',
        endpoint_url=R2_CONFIG['endpoint_url'],
        aws_access_key_id=R2_CONFIG['aws_access_key_id'],
        aws_secret_access_key=R2_CONFIG['aws_secret_access_key'],
        config=Config(signature_version='s3v4')
    )
    
    profile_key = f"ProfileInfo/{username}.json"
    
    try:
        # Get object
        response = client.get_object(
            Bucket=bucket,
            Key=profile_key
        )
        
        # Read and parse the JSON content
        profile_json = json.loads(response['Body'].read().decode('utf-8'))
        
        # Print the exported profile
        print_profile_data(profile_json, f"Exported Profile from R2 ({profile_key})")
        
        # Check for profile picture URLs
        if not profile_json.get("profilePicUrl"):
            print("WARNING: profilePicUrl is empty in exported profile")
        if not profile_json.get("profilePicUrlHD"):
            print("WARNING: profilePicUrlHD is empty in exported profile")
            
        return profile_json
    except Exception as e:
        print(f"Error retrieving exported profile: {str(e)}")
        return None

def diagnose_export_issue():
    """Diagnose and fix profile URL export issue."""
    print("=== Starting Profile URL Export Diagnosis ===")
    
    # 1. Test scraping an actual Instagram profile
    print("\n1. Testing Instagram profile scraping:")
    test_username = "maccosmetics"
    
    # Create scraper instance
    scraper = InstagramScraper()
    
    # Scrape profile
    profile_data = scraper.scrape_profile(test_username, 1)
    
    if not profile_data:
        print(f"Failed to scrape profile for {test_username}")
        return
    
    # 2. Extract and print raw profile data
    print("\n2. Examining raw profile data:")
    raw_profile = profile_data[0]
    
    # Check if profile URLs exist in raw data
    print(f"Profile picture URL exists in raw data: {'profilePicUrl' in raw_profile}")
    print(f"HD profile picture URL exists in raw data: {'profilePicUrlHD' in raw_profile}")
    
    if 'profilePicUrl' in raw_profile:
        print(f"Raw profilePicUrl: '{raw_profile['profilePicUrl']}'")
    if 'profilePicUrlHD' in raw_profile:
        print(f"Raw profilePicUrlHD: '{raw_profile['profilePicUrlHD']}'")
    
    # 3. Test InstagramScraper extract_short_profile_info method
    print("\n3. Testing InstagramScraper.extract_short_profile_info:")
    short_info = scraper.extract_short_profile_info(profile_data)
    
    if short_info:
        print_profile_data(short_info, "Extracted Short Profile Info")
    else:
        print("Failed to extract short profile info")
        return
    
    # 4. Test InstagramScraper upload_short_profile_to_tasks method
    print("\n4. Testing InstagramScraper.upload_short_profile_to_tasks:")
    upload_result = scraper.upload_short_profile_to_tasks(short_info)
    
    if upload_result:
        print(f"Successfully uploaded short profile to tasks/ProfileInfo/{test_username}.json")
    else:
        print(f"Failed to upload short profile to tasks bucket")
        return
    
    # Wait for consistency
    print("Waiting 5 seconds for R2 consistency...")
    time.sleep(5)
    
    # 5. Verify the profile was exported with URLs
    exported_via_scraper = verify_exported_profile(test_username)
    
    # 6. Test ContentRecommendationSystem export_profile_info method
    print("\n6. Testing ContentRecommendationSystem.export_profile_info:")
    
    # Create CMS instance
    cms = ContentRecommendationSystem()
    
    # Create test profile with new username to avoid redundancy check
    test_cms_username = f"test_profile_url_{int(time.time())}"
    test_profile = {
        "username": test_cms_username,
        "fullName": "Test URL Export",
        "biography": "Testing profile URL export",
        "followersCount": 5000,
        "followsCount": 500,
        "profilePicUrl": "https://example.com/profile.jpg",
        "profilePicUrlHD": "https://example.com/profile_hd.jpg",
        "private": False,
        "verified": True
    }
    
    # Export profile via CMS
    cms_result = cms.export_profile_info(test_profile, test_cms_username)
    
    if cms_result:
        print(f"Successfully exported profile via CMS to tasks/ProfileInfo/{test_cms_username}.json")
    else:
        print("Failed to export profile via CMS")
        return
    
    # Wait for consistency
    print("Waiting 5 seconds for R2 consistency...")
    time.sleep(5)
    
    # 7. Verify CMS-exported profile
    exported_via_cms = verify_exported_profile(test_cms_username)
    
    # 8. Test redundancy check
    print("\n8. Testing redundancy check on a second export")
    updated_profile = test_profile.copy()
    updated_profile["profilePicUrl"] = "https://example.com/updated_profile.jpg"
    updated_profile["profilePicUrlHD"] = "https://example.com/updated_profile_hd.jpg"
    
    second_export = cms.export_profile_info(updated_profile, test_cms_username)
    print(f"Second export result (should be skipped): {'Success' if second_export else 'Failed'}")

if __name__ == "__main__":
    diagnose_export_issue() 