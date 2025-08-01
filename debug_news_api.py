#!/usr/bin/env python3
"""
Simple News API test to debug the 422 error
"""

import requests
import json

# Test the NewsData API directly
api_key = 'pub_81555ab19b0046a7b3d947cddc59fe99c9146'
base_url = "https://newsdata.io/api/1/news"

print("🔍 Testing NewsData API directly...")

# Try a basic request first
params = {
    'apikey': api_key,
    'language': 'en',
    'size': 5
}

print(f"Request URL: {base_url}")
print(f"Parameters: {params}")

response = requests.get(base_url, params=params, timeout=10)

print(f"Response Status: {response.status_code}")
print(f"Response Headers: {dict(response.headers)}")

if response.status_code == 200:
    data = response.json()
    print(f"✅ Success! Got {len(data.get('results', []))} articles")
    print("Sample article titles:")
    for i, article in enumerate(data.get('results', [])[:3]):
        print(f"  {i+1}. {article.get('title', 'No title')}")
else:
    print(f"❌ Error Response: {response.text}")
    try:
        error_data = response.json()
        print(f"Error Details: {json.dumps(error_data, indent=2)}")
    except:
        print("Could not parse error as JSON")

# Test with category
print("\n🔍 Testing with category parameter...")

params_with_category = {
    'apikey': api_key,
    'category': 'business',
    'language': 'en',
    'size': 5
}

response2 = requests.get(base_url, params=params_with_category, timeout=10)
print(f"With category - Status: {response2.status_code}")

if response2.status_code != 200:
    print(f"Error with category: {response2.text}")
