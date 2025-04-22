#!/usr/bin/env python3
"""Test script to diagnose and fix profile URL extraction issues."""

import json
import logging
import time
import boto3
from botocore.client import Config
from datetime import datetime
from config import R2_CONFIG, LOGGING_CONFIG

# Import from the right module path
from instagram_scraper import InstagramScraper

# Set up logging
logging.basicConfig(
    level=LOGGING_CONFIG['level'],
    format=LOGGING_CONFIG['format']
)
logger = logging.getLogger(__name__)

def print_profile_data(profile_data, title="Profile Data"):
    """Print profile data in a readable format."""
    print(f"\n--- {title} ---")
    for key, value in profile_data.items():
        if key in ["profilePicUrl", "profilePicUrlHD"]:
            print(f"{key}: URL length = {len(str(value))}, empty = {value == ''}")
            if value and len(value) > 0:
                print(f"  URL preview: {value[:50]}...")
        else:
            print(f"{key}: {value}")

def test_profile_extraction():
    """Test profile extraction to diagnose URL issues."""
    test_username = "humansofny"  # Use the username that's having issues
    
    # Create scraper instance
    scraper = InstagramScraper()
    
    # 1. Scrape profile and dump raw data
    print(f"\n1. Scraping profile for {test_username}...")
    profile_data = scraper.scrape_profile(test_username, 1)
    
    if not profile_data:
        print(f"Failed to scrape profile for {test_username}")
        return False
    
    # Save raw data to file for inspection
    with open(f"{test_username}_raw.json", "w") as f:
        json.dump(profile_data, f, indent=2)
    print(f"Raw data saved to {test_username}_raw.json")
    
    # 2. Print available fields in raw data
    raw_profile = profile_data[0]
    print("\n2. Profile fields in raw data:")
    for key in sorted(raw_profile.keys()):
        if key in ["profilePicUrl", "profilePicUrlHD"]:
            url_value = raw_profile.get(key, "")
            print(f"  {key}: URL length = {len(url_value)}, empty = {url_value == ''}")
            if url_value and len(url_value) > 0:
                print(f"    URL preview: {url_value[:50]}...")
        else:
            value = raw_profile.get(key)
            if isinstance(value, (dict, list)):
                print(f"  {key}: {type(value).__name__} with {len(value)} items")
            else:
                print(f"  {key}: {value}")
    
    # 3. Test standard extraction
    print("\n3. Testing standard extraction...")
    standard_info = scraper.extract_short_profile_info(profile_data)
    if standard_info:
        print_profile_data(standard_info, "Standard Extraction")
    else:
        print("Failed to extract standard profile info")
    
    # 4. Test enhanced extraction with explicit field checking
    print("\n4. Testing enhanced extraction with explicit field checking...")
    try:
        profile = profile_data[0]
        
        # Log all available fields for debugging
        logger.info(f"Available fields: {', '.join(profile.keys())}")
        
        enhanced_info = {
            "username": profile.get("username", ""),
            "fullName": profile.get("fullName", ""),
            "biography": profile.get("biography", ""),
            "followersCount": profile.get("followersCount", 0),
            "followsCount": profile.get("followsCount", 0),
            "postsCount": profile.get("postsCount", 0),
            "externalUrl": profile.get("externalUrl", ""),
            "private": profile.get("private", False),
            "verified": profile.get("verified", False),
            "extractedAt": datetime.now().isoformat()
        }
        
        # Handle profile pic URLs with explicit logging
        profile_pic_url = profile.get("profilePicUrl", "")
        profile_pic_url_hd = profile.get("profilePicUrlHD", "")
        
        logger.info(f"Raw profilePicUrl: {profile_pic_url[:50]}..." if profile_pic_url else "Raw profilePicUrl: EMPTY")
        logger.info(f"Raw profilePicUrlHD: {profile_pic_url_hd[:50]}..." if profile_pic_url_hd else "Raw profilePicUrlHD: EMPTY")
        
        # Add profile pic URLs to enhanced info
        enhanced_info["profilePicUrl"] = profile_pic_url
        enhanced_info["profilePicUrlHD"] = profile_pic_url_hd
        
        print_profile_data(enhanced_info, "Enhanced Extraction")
        
        # Save enhanced extraction to file
        with open(f"{test_username}_enhanced.json", "w") as f:
            json.dump(enhanced_info, f, indent=2)
        print(f"Enhanced data saved to {test_username}_enhanced.json")
        
    except Exception as e:
        logger.error(f"Error in enhanced extraction: {str(e)}")
        print(f"Enhanced extraction failed: {str(e)}")
    
    return True

if __name__ == "__main__":
    test_profile_extraction() 