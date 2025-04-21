#!/usr/bin/env python3
"""Script to test enhanced profile extraction and replacement functionality."""

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
        
    # Sort keys to put important fields first
    important_fields = ["username", "fullName", "biography", "followersCount", "followsCount", 
                        "postsCount", "externalUrl", "verified", "private"]
    all_keys = sorted(profile_data.keys(), key=lambda k: 
                     (0 if k in important_fields else 1, important_fields.index(k) if k in important_fields else 999))
    
    for key in all_keys:
        value = profile_data[key]
        if key in ["profilePicUrl", "profilePicUrlHD"]:
            # Print URL with length
            url_length = len(str(value)) if value else 0
            print(f"{key}: URL length = {url_length}")
            if url_length > 0:
                print(f"  URL snippet: {value[:80]}...")
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

def test_enhanced_extraction():
    """Test enhanced profile extraction with all fields."""
    print("\n=== Testing Enhanced Profile Extraction ===")
    
    test_username = "fentybeauty"
    
    # Create scraper instance
    scraper = InstagramScraper()
    
    # Scrape profile
    print(f"1. Scraping profile for {test_username}...")
    profile_data = scraper.scrape_profile(test_username, 1)
    if not profile_data:
        print(f"Failed to scrape profile for {test_username}")
        return False
    
    print(f"Successfully scraped profile for {test_username}")
    
    # Print raw data fields
    raw_profile = profile_data[0]
    print("\n2. Available fields in raw profile data:")
    for key in sorted(raw_profile.keys()):
        if key in ["profilePicUrl", "profilePicUrlHD"]:
            print(f"  {key}: [URL length: {len(raw_profile[key]) if raw_profile.get(key) else 0}]")
        else:
            value = raw_profile.get(key)
            if isinstance(value, (dict, list)):
                print(f"  {key}: {type(value).__name__} ({len(value)} items)")
            else:
                print(f"  {key}: {value}")
    
    # Extract short profile info
    print("\n3. Extracting short profile info...")
    short_info = scraper.extract_short_profile_info(profile_data)
    if not short_info:
        print("Failed to extract short profile info")
        return False
    
    # Print extracted profile data
    print_profile_data(short_info, "Extracted Profile Info")
    
    # Upload to tasks bucket
    print("\n4. Uploading profile to tasks bucket (first time)...")
    result = scraper.upload_short_profile_to_tasks(short_info)
    if not result:
        print("Failed to upload profile info")
        return False
    
    # Wait for consistency
    print("Waiting 3 seconds for R2 consistency...")
    time.sleep(3)
    
    # Verify uploaded profile
    print("\n5. Verifying uploaded profile...")
    exported_profile = retrieve_exported_profile(test_username)
    if not exported_profile:
        print("Failed to retrieve exported profile")
        return False
    
    print_profile_data(exported_profile, "Exported Profile (First Upload)")
    
    # Test profile replacement
    print("\n6. Testing profile replacement...")
    
    # Modify the profile data to test replacement
    short_info["biography"] = short_info.get("biography", "") + " [UPDATED]"
    short_info["extractedAt"] = time.strftime("%Y-%m-%dT%H:%M:%S.000000")
    
    # Upload modified profile
    replacement_result = scraper.upload_short_profile_to_tasks(short_info)
    if not replacement_result:
        print("Failed to replace profile info")
        return False
    
    # Wait for consistency
    print("Waiting 3 seconds for R2 consistency...")
    time.sleep(3)
    
    # Verify replaced profile
    replaced_profile = retrieve_exported_profile(test_username)
    if not replaced_profile:
        print("Failed to retrieve replaced profile")
        return False
    
    print_profile_data(replaced_profile, "Replaced Profile")
    
    # Verify replacement was successful
    if replaced_profile.get("biography") == short_info["biography"]:
        print("\nSUCCESS: Profile replacement worked correctly")
        return True
    else:
        print("\nFAILURE: Profile replacement did not work correctly")
        return False

def test_cms_export_replacement():
    """Test ContentRecommendationSystem profile export replacement."""
    print("\n=== Testing CMS Profile Export Replacement ===")
    
    # Create CMS instance
    cms = ContentRecommendationSystem()
    
    # Create unique test username
    test_username = f"test_enhanced_cms_{int(time.time())}"
    
    # Create initial test profile
    initial_profile = {
        "username": test_username,
        "fullName": "Test Enhanced CMS",
        "biography": "Testing enhanced profile extraction and replacement",
        "followersCount": 50000,
        "followsCount": 500,
        "postsCount": 300,
        "externalUrl": "https://example.com",
        "profilePicUrl": "https://example.com/profile.jpg",
        "profilePicUrlHD": "https://example.com/profile_hd.jpg",
        "private": False,
        "verified": True
    }
    
    # Export initial profile
    print("1. Exporting initial profile...")
    result = cms.export_profile_info(initial_profile, test_username)
    if not result:
        print("Failed to export initial profile")
        return False
    
    # Wait for consistency
    print("Waiting 3 seconds for R2 consistency...")
    time.sleep(3)
    
    # Verify initial profile
    print("2. Verifying initial profile...")
    initial_exported = retrieve_exported_profile(test_username)
    if not initial_exported:
        print("Failed to retrieve initial exported profile")
        return False
    
    print_profile_data(initial_exported, "Initial Exported Profile")
    
    # Create updated profile
    updated_profile = initial_profile.copy()
    updated_profile["fullName"] = "Test Enhanced CMS [UPDATED]"
    updated_profile["biography"] = "Testing profile replacement in CMS"
    updated_profile["followersCount"] = 55000
    updated_profile["externalUrl"] = "https://example.com/updated"
    
    # Export updated profile
    print("\n3. Exporting updated profile (replacement)...")
    replacement_result = cms.export_profile_info(updated_profile, test_username)
    if not replacement_result:
        print("Failed to export updated profile")
        return False
    
    # Wait for consistency
    print("Waiting 3 seconds for R2 consistency...")
    time.sleep(3)
    
    # Verify updated profile
    print("4. Verifying updated profile...")
    updated_exported = retrieve_exported_profile(test_username)
    if not updated_exported:
        print("Failed to retrieve updated exported profile")
        return False
    
    print_profile_data(updated_exported, "Updated Exported Profile")
    
    # Verify replacement was successful
    if (updated_exported.get("fullName") == updated_profile["fullName"] and
        updated_exported.get("biography") == updated_profile["biography"] and
        updated_exported.get("followersCount") == updated_profile["followersCount"]):
        print("\nSUCCESS: CMS profile replacement worked correctly")
        return True
    else:
        print("\nFAILURE: CMS profile replacement did not work correctly")
        return False

def test_full_profile_extraction():
    """Test actual Instagram profile extraction with all fields."""
    print("\n=== Testing Full Instagram Profile Extraction ===")
    
    test_username = "maccosmetics"
    
    # Create scraper instance
    scraper = InstagramScraper()
    
    # Scrape profile
    print(f"1. Scraping profile for {test_username}...")
    profile_data = scraper.scrape_profile(test_username, 1)
    if not profile_data:
        print(f"Failed to scrape profile for {test_username}")
        return False
    
    # Extract short profile info 
    short_info = scraper.extract_short_profile_info(profile_data)
    if not short_info:
        print("Failed to extract short profile info")
        return False
    
    # Print extracted profile data with all fields
    print_profile_data(short_info, "Complete Profile Info")
    
    # Test if all expected fields are present and non-empty
    expected_fields = ["username", "fullName", "biography", "followersCount", "followsCount", 
                      "profilePicUrl", "profilePicUrlHD", "postsCount", "verified"]
    
    missing_fields = [field for field in expected_fields if field not in short_info or not short_info.get(field)]
    
    if missing_fields:
        print(f"\nWARNING: The following fields are missing or empty: {', '.join(missing_fields)}")
        return False
    else:
        print("\nSUCCESS: All expected fields are present and non-empty")
        return True

if __name__ == "__main__":
    print("=== Testing Enhanced Profile Extraction and Replacement ===")
    
    # Run all tests
    extraction_result = test_enhanced_extraction()
    cms_result = test_cms_export_replacement()
    full_profile_result = test_full_profile_extraction()
    
    # Print overall results
    print("\n=== Overall Test Results ===")
    print(f"Enhanced Profile Extraction Test: {'Success' if extraction_result else 'Failure'}")
    print(f"CMS Profile Replacement Test: {'Success' if cms_result else 'Failure'}")
    print(f"Full Profile Extraction Test: {'Success' if full_profile_result else 'Failure'}")
    
    if extraction_result and cms_result and full_profile_result:
        print("\nALL TESTS PASSED! The enhanced profile extraction and replacement is working correctly.")
    else:
        print("\nSome tests failed. Please check the output for details.") 