#!/usr/bin/env python3
"""Script to verify profile URL export fix is working properly."""

import logging
import json
import time
import os
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
            # Print URL with length
            url_length = len(str(value)) if value else 0
            print(f"{key}: URL length = {url_length}")
            if url_length > 0:
                print(f"  URL: {value[:80]}...")
        else:
            print(f"{key}: {value}")

def retrieve_exported_profile(username, bucket='tasks'):
    """Retrieve exported profile data."""
    client = boto3.client(
        's3',
        endpoint_url=R2_CONFIG['endpoint_url'],
        aws_access_key_id=R2_CONFIG['aws_access_key_id'],
        aws_secret_access_key=R2_CONFIG['aws_secret_access_key'],
        config=Config(signature_version='s3v4')
    )
    
    profile_key = f"ProfileInfo/{username}.json"
    
    try:
        response = client.get_object(
            Bucket=bucket,
            Key=profile_key
        )
        
        profile_json = json.loads(response['Body'].read().decode('utf-8'))
        return profile_json
    except Exception as e:
        logger.error(f"Error retrieving profile: {str(e)}")
        return None

def test_instagram_scraper_export():
    """Test profile URL export using InstagramScraper."""
    print("\n=== Testing InstagramScraper Profile URL Export ===")
    
    # Create a unique test username
    test_username = f"test_scraper_url_{int(time.time())}"
    
    # Create a test profile with URLs
    test_profile = {
        "username": test_username,
        "fullName": "Test Scraper URL Export",
        "biography": "Testing the scraper URL export fix",
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
    
    # Upload the profile
    result = scraper.upload_short_profile_to_tasks(test_profile)
    if not result:
        print("Failed to upload test profile via scraper")
        return False
    
    print(f"Successfully uploaded test profile: {test_username}")
    
    # Wait for consistency
    print("Waiting 3 seconds for R2 consistency...")
    time.sleep(3)
    
    # Retrieve the exported profile
    exported_profile = retrieve_exported_profile(test_username)
    if not exported_profile:
        print("Failed to retrieve exported profile")
        return False
    
    # Print the exported profile
    print_profile_data(exported_profile, "Exported Profile via InstagramScraper")
    
    # Check if profile URLs were preserved
    if (exported_profile.get("profilePicUrl") == test_profile["profilePicUrl"] and 
        exported_profile.get("profilePicUrlHD") == test_profile["profilePicUrlHD"]):
        print("SUCCESS: Profile URLs were preserved correctly")
        return True
    else:
        print("FAILURE: Profile URLs were not preserved correctly")
        return False

def test_cms_export():
    """Test profile URL export using ContentRecommendationSystem."""
    print("\n=== Testing ContentRecommendationSystem Profile URL Export ===")
    
    # Create a unique test username
    test_username = f"test_cms_url_{int(time.time())}"
    
    # Create a test profile with URLs
    test_profile = {
        "username": test_username,
        "fullName": "Test CMS URL Export",
        "biography": "Testing the CMS URL export fix",
        "followersCount": 5000,
        "followsCount": 500,
        "profilePicUrl": "https://example.com/cms_profile.jpg",
        "profilePicUrlHD": "https://example.com/cms_profile_hd.jpg",
        "private": False,
        "verified": True
    }
    
    # Create CMS instance
    cms = ContentRecommendationSystem()
    
    # Export the profile
    result = cms.export_profile_info(test_profile, test_username)
    if not result:
        print("Failed to export test profile via CMS")
        return False
    
    print(f"Successfully exported test profile: {test_username}")
    
    # Wait for consistency
    print("Waiting 3 seconds for R2 consistency...")
    time.sleep(3)
    
    # Retrieve the exported profile
    exported_profile = retrieve_exported_profile(test_username)
    if not exported_profile:
        print("Failed to retrieve exported profile")
        return False
    
    # Print the exported profile
    print_profile_data(exported_profile, "Exported Profile via CMS")
    
    # Check if profile URLs were preserved
    if (exported_profile.get("profilePicUrl") == test_profile["profilePicUrl"] and 
        exported_profile.get("profilePicUrlHD") == test_profile["profilePicUrlHD"]):
        print("SUCCESS: Profile URLs were preserved correctly")
        return True
    else:
        print("FAILURE: Profile URLs were not preserved correctly")
        return False

def test_actual_profile_export():
    """Test exporting a real Instagram profile."""
    print("\n=== Testing Real Instagram Profile Export ===")
    
    test_username = "maccosmetics"
    
    # Create scraper instance
    scraper = InstagramScraper()
    
    # Scrape the profile
    profile_data = scraper.scrape_profile(test_username, 1)
    if not profile_data:
        print(f"Failed to scrape profile for {test_username}")
        return False
    
    print(f"Successfully scraped profile for {test_username}")
    
    # Extract short profile info
    short_info = scraper.extract_short_profile_info(profile_data)
    if not short_info:
        print("Failed to extract short profile info")
        return False
    
    # Check if profile URLs exist
    if not short_info.get("profilePicUrl") or not short_info.get("profilePicUrlHD"):
        print("WARNING: Profile URLs missing from extracted info")
    
    # Create a unique test username to avoid redundancy check
    test_export_username = f"{test_username}_{int(time.time())}"
    
    # Create CMS instance
    cms = ContentRecommendationSystem()
    
    # Update the username but keep all other data
    short_info["username"] = test_export_username
    
    # Export the profile
    result = cms.export_profile_info(short_info, test_export_username)
    if not result:
        print("Failed to export profile via CMS")
        return False
    
    print(f"Successfully exported profile as: {test_export_username}")
    
    # Wait for consistency
    print("Waiting 3 seconds for R2 consistency...")
    time.sleep(3)
    
    # Retrieve the exported profile
    exported_profile = retrieve_exported_profile(test_export_username)
    if not exported_profile:
        print("Failed to retrieve exported profile")
        return False
    
    # Print the exported profile
    print_profile_data(exported_profile, "Exported Real Profile")
    
    # Check if profile URLs were preserved
    if (exported_profile.get("profilePicUrl") == short_info.get("profilePicUrl") and 
        exported_profile.get("profilePicUrlHD") == short_info.get("profilePicUrlHD")):
        print("SUCCESS: Profile URLs were preserved correctly")
        return True
    else:
        print("FAILURE: Profile URLs were not preserved correctly")
        return False

def verify_all_fixes():
    """Verify all profile URL export fixes."""
    print("=== Verifying Profile URL Export Fixes ===")
    
    # Test 1: Instagram Scraper Export
    scraper_result = test_instagram_scraper_export()
    
    # Test 2: CMS Export
    cms_result = test_cms_export()
    
    # Test 3: Real Profile Export
    real_result = test_actual_profile_export()
    
    # Print overall results
    print("\n=== Overall Results ===")
    print(f"InstagramScraper URL Export: {'Success' if scraper_result else 'Failure'}")
    print(f"ContentRecommendationSystem URL Export: {'Success' if cms_result else 'Failure'}")
    print(f"Real Profile URL Export: {'Success' if real_result else 'Failure'}")
    
    if scraper_result and cms_result and real_result:
        print("\nALL TESTS PASSED! The profile URL export fix is working correctly.")
        return True
    else:
        print("\nSome tests failed. The profile URL export fix may not be working correctly.")
        return False

if __name__ == "__main__":
    verify_all_fixes() 