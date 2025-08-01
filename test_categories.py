#!/usr/bin/env python3
"""
Test valid NewsData API categories
"""

import requests

api_key = 'pub_81555ab19b0046a7b3d947cddc59fe99c9146'
base_url = "https://newsdata.io/api/1/news"

# Valid NewsData categories according to their docs
valid_categories = [
    'top',  # This should be the default
    'business',
    'entertainment', 
    'environment',
    'food',
    'health',
    'politics',
    'science',
    'sports',
    'technology',
    'tourism',
    'world'
]

print("🔍 Testing valid NewsData API categories...")

for category in ['top', 'technology', 'business']:
    print(f"\nTesting category: {category}")
    
    params = {
        'apikey': api_key,
        'category': category,
        'language': 'en',
        'size': 3
    }
    
    response = requests.get(base_url, params=params, timeout=10)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        articles = data.get('results', [])
        print(f"✅ Got {len(articles)} articles")
        if articles:
            print(f"Sample: {articles[0].get('title', 'No title')[:60]}...")
    else:
        print(f"❌ Error: {response.text[:100]}...")
