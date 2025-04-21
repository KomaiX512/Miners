#!/usr/bin/env python3
"""Script to save raw Instagram profile data for analysis."""

import instagram_scraper
import json
import os

def save_raw_data():
    """Save raw Instagram profile data for analysis."""
    os.makedirs('temp', exist_ok=True)
    
    # Create scraper instance
    scraper = instagram_scraper.InstagramScraper()
    
    # Scrape profile
    username = "maccosmetics"
    data = scraper.scrape_profile(username, 1)
    
    if not data:
        print(f"Failed to scrape profile for {username}")
        return
    
    # Save raw data to file
    output_path = os.path.join('temp', 'raw_insta_data.json')
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2)
    
    print(f"Saved raw Instagram profile data to {output_path}")
    
    # Print profile image URLs for reference
    if data and isinstance(data, list) and len(data) > 0:
        profile = data[0]
        print("\nProfile image URLs:")
        print(f"profilePicUrl: {profile.get('profilePicUrl', 'Not found')}")
        print(f"profilePicUrlHD: {profile.get('profilePicUrlHD', 'Not found')}")
        
        # Print all keys in the profile object
        print("\nAll available keys in profile object:")
        for key in profile.keys():
            print(f"- {key}")

if __name__ == "__main__":
    save_raw_data() 