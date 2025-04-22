#!/usr/bin/env python3
"""Test script to diagnose and fix profile URL extraction issues."""

import json
import logging
import time
import re
import sys
from datetime import datetime
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

def fix_profile_url_extraction():
    """Diagnose and fix profile URL extraction issues."""
    # Test with a specific username that had issues
    username = "humansofny"
    
    print(f"=== Testing Profile URL extraction for {username} ===")
    
    # Create scraper instance
    scraper = InstagramScraper()
    
    # 1. Scrape the profile
    print(f"\n1. Scraping profile for {username}...")
    profile_data = scraper.scrape_profile(username, 1)
    
    if not profile_data:
        print(f"Failed to scrape profile for {username}")
        return False
        
    print(f"Successfully scraped profile for {username}")
    
    # 2. Examine raw profile data
    raw_profile = profile_data[0]
    print("\n2. Examining raw profile data:")
    
    # Check for profile picture URLs in raw data
    profile_pic_url = raw_profile.get("profilePicUrl", "")
    profile_pic_url_hd = raw_profile.get("profilePicUrlHD", "")
    
    print(f"Profile picture URL exists: {'Yes' if profile_pic_url else 'No'}")
    if profile_pic_url:
        print(f"URL length: {len(profile_pic_url)}")
        print(f"URL preview: {profile_pic_url[:50]}...")
        
    print(f"HD Profile picture URL exists: {'Yes' if profile_pic_url_hd else 'No'}")
    if profile_pic_url_hd:
        print(f"URL length: {len(profile_pic_url_hd)}")
        print(f"URL preview: {profile_pic_url_hd[:50]}...")
    
    # 3. Test extraction with updated method
    print("\n3. Testing extraction with updated method:")
    extracted_info = scraper.extract_short_profile_info(profile_data)
    
    if not extracted_info:
        print("Extraction failed")
        return False
        
    print("Extraction successful")
    print(f"Profile picture URL in extracted data: {'Yes' if extracted_info.get('profilePicUrl') else 'No'}")
    print(f"HD Profile picture URL in extracted data: {'Yes' if extracted_info.get('profilePicUrlHD') else 'No'}")
    
    # 4. Upload to tasks bucket
    print("\n4. Uploading to tasks bucket:")
    test_username = f"{username}_test_{int(time.time())}"
    extracted_info["username"] = test_username
    
    upload_result = scraper.upload_short_profile_to_tasks(extracted_info)
    print(f"Upload result: {'Success' if upload_result else 'Failed'}")
    
    # Print the full extracted profile
    print_profile_data(extracted_info, "Extracted Profile")
    
    return True

if __name__ == "__main__":
    fix_profile_url_extraction() 