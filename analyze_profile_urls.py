#!/usr/bin/env python3
"""Script to analyze Instagram profile image URLs."""

import json
import os
import re

def analyze_profile_urls():
    """Analyze Instagram profile image URLs to understand their structure."""
    raw_data_path = os.path.join('temp', 'raw_insta_data.json')
    
    if not os.path.exists(raw_data_path):
        print(f"Error: Raw data file not found at {raw_data_path}")
        print("Please run test_save_raw.py first to generate the data file.")
        return
    
    # Load the raw data
    with open(raw_data_path, 'r') as f:
        data = json.load(f)
    
    if not data or not isinstance(data, list) or len(data) == 0:
        print("Error: Invalid data format in the raw data file.")
        return
    
    profile = data[0]
    
    # Extract profile image URLs
    profile_pic_url = profile.get('profilePicUrl', '')
    profile_pic_url_hd = profile.get('profilePicUrlHD', '')
    
    print(f"Username: {profile.get('username')}")
    print(f"Full Name: {profile.get('fullName')}")
    
    print("\n=== Profile Image URLs Analysis ===")
    
    # Analyze standard profile pic URL
    print("\nStandard Profile Pic URL:")
    print(profile_pic_url)
    
    # Parse URL components
    if profile_pic_url:
        analyze_url(profile_pic_url, "Standard")
    
    # Analyze HD profile pic URL
    print("\nHD Profile Pic URL:")
    print(profile_pic_url_hd)
    
    # Parse URL components
    if profile_pic_url_hd:
        analyze_url(profile_pic_url_hd, "HD")
    
    # Compare the two URLs
    if profile_pic_url and profile_pic_url_hd:
        print("\n=== Comparison of Standard and HD URLs ===")
        url_differences = compare_urls(profile_pic_url, profile_pic_url_hd)
        for diff in url_differences:
            print(f"- {diff}")

def analyze_url(url, url_type):
    """Analyze components of the profile image URL."""
    print(f"\n{url_type} URL Analysis:")
    
    # Extract base URL and parameters
    url_parts = url.split('?')
    base_url = url_parts[0]
    params = url_parts[1] if len(url_parts) > 1 else ""
    
    print(f"Base URL: {base_url}")
    
    # Extract file name and extension
    filename = os.path.basename(base_url)
    print(f"Filename: {filename}")
    
    # Analysis of parameters
    if params:
        print("\nParameters:")
        param_parts = params.split('&')
        for part in param_parts:
            if '=' in part:
                key, value = part.split('=', 1)
                print(f"  {key}: {value}")
    
    # Check for resolution indicators in URL
    resolution_patterns = {
        "s150x150": "150x150 pixels (thumbnail)",
        "s320x320": "320x320 pixels (medium)",
        "s640x640": "640x640 pixels (large)",
        "s1080x1080": "1080x1080 pixels (full HD)"
    }
    
    for pattern, description in resolution_patterns.items():
        if pattern in url:
            print(f"\nResolution: {description}")
            break

def compare_urls(url1, url2):
    """Compare two URLs to identify differences."""
    differences = []
    
    # Split URLs to compare base and parameters
    url1_parts = url1.split('?')
    url2_parts = url2.split('?')
    
    # Compare base URLs
    if url1_parts[0] != url2_parts[0]:
        differences.append(f"Different base URLs:\n  URL1: {url1_parts[0]}\n  URL2: {url2_parts[0]}")
    
    # Compare parameters
    if len(url1_parts) > 1 and len(url2_parts) > 1:
        params1 = {p.split('=')[0]: p.split('=')[1] for p in url1_parts[1].split('&') if '=' in p}
        params2 = {p.split('=')[0]: p.split('=')[1] for p in url2_parts[1].split('&') if '=' in p}
        
        # Find parameters in URL1 that differ from URL2
        for key, value in params1.items():
            if key in params2:
                if value != params2[key]:
                    differences.append(f"Parameter '{key}' differs:\n  URL1: {value}\n  URL2: {params2[key]}")
            else:
                differences.append(f"Parameter '{key}' only in URL1: {value}")
        
        # Find parameters only in URL2
        for key, value in params2.items():
            if key not in params1:
                differences.append(f"Parameter '{key}' only in URL2: {value}")
    
    # Look for resolution differences
    res1 = re.search(r's(\d+)x(\d+)', url1)
    res2 = re.search(r's(\d+)x(\d+)', url2)
    
    if res1 and res2:
        res1_str = f"{res1.group(1)}x{res1.group(2)}"
        res2_str = f"{res2.group(1)}x{res2.group(2)}"
        if res1_str != res2_str:
            differences.append(f"Different resolutions: URL1 is {res1_str}, URL2 is {res2_str}")
    
    return differences

if __name__ == "__main__":
    analyze_profile_urls() 