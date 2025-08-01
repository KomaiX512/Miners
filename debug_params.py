#!/usr/bin/env python3
"""
Debug NewsData API parameters
"""

import requests

api_key = 'pub_81555ab19b0046a7b3d947cddc59fe99c9146'
base_url = "https://newsdata.io/api/1/news"

print("🔍 Testing different parameter combinations...")

# Test 1: Basic working version
print("\n1. Basic working version:")
params1 = {
    'apikey': api_key,
    'category': 'top',
    'language': 'en',
    'size': 3
}
response1 = requests.get(base_url, params=params1)
print(f"Status: {response1.status_code}")

# Test 2: With keywords using OR
print("\n2. With keywords using OR:")
params2 = {
    'apikey': api_key,
    'category': 'top',
    'language': 'en',
    'size': 3,
    'q': 'trending OR elonmusk OR news'
}
response2 = requests.get(base_url, params=params2)
print(f"Status: {response2.status_code}")
if response2.status_code != 200:
    print(f"Error: {response2.text}")

# Test 3: With keywords using spaces
print("\n3. With keywords using spaces:")
params3 = {
    'apikey': api_key,
    'category': 'top',
    'language': 'en',
    'size': 3,
    'q': 'trending news'
}
response3 = requests.get(base_url, params=params3)
print(f"Status: {response3.status_code}")
if response3.status_code != 200:
    print(f"Error: {response3.text}")

# Test 4: Business category only
print("\n4. Business category only:")
params4 = {
    'apikey': api_key,
    'category': 'business',
    'language': 'en',
    'size': 3
}
response4 = requests.get(base_url, params=params4)
print(f"Status: {response4.status_code}")
if response4.status_code != 200:
    print(f"Error: {response4.text}")
