#!/usr/bin/env python3
"""
Quick News Module Test
"""

from news_for_you import NewsForYouModule
from config import R2_CONFIG

print("🧪 Quick News Module Test")

# Create news module
news_module = NewsForYouModule(
    config=R2_CONFIG,
    ai_domain_intel=None,
    rag_implementation=None,
    vector_db=None
)

# Test domain analysis
print("\n🔍 Testing domain analysis...")
domain = news_module._analyze_account_domain_sync(
    username="elonmusk",
    platform="twitter",
    account_type="personal",
    user_posts=[]
)
print(f"Domain: {domain}")

# Test news fetching 
print("\n📰 Testing news fetching...")
news = news_module._fetch_todays_trending_news_sync(domain)
print(f"Fetched {len(news)} news articles")

if news:
    print("Sample article:")
    print(f"- {news[0].get('title', 'No title')}")
    print("✅ SUCCESS!")
else:
    print("❌ No news fetched")
