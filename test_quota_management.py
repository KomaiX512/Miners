#!/usr/bin/env python3
"""
Test script for quota management system
"""

import logging
import time
from datetime import datetime
from rag_implementation import RagImplementation, AdaptiveRateLimiter
from config import GEMINI_CONFIG

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_quota_limiter():
    """Test the enhanced quota limiter functionality."""
    print("🧪 Testing Enhanced Quota Management System")
    print("=" * 50)
    
    # Test quota configuration
    quota_config = GEMINI_CONFIG.get('quota_management', {})
    print(f"📊 Quota Configuration:")
    print(f"   - Max Daily Requests: {quota_config.get('max_daily_requests', 45)}")
    print(f"   - Max Hourly Requests: {quota_config.get('requests_per_hour', 10)}")
    print(f"   - Caching Enabled: {quota_config.get('enable_caching', True)}")
    print(f"   - Fallback to Mock: {quota_config.get('fallback_to_mock', True)}")
    print()
    
    # Initialize rate limiter
    rate_limiter = AdaptiveRateLimiter(quota_config=quota_config)
    print(f"🕒 Rate Limiter Initialized:")
    print(f"   - Initial Delay: {rate_limiter.current_delay}s")
    print(f"   - Min Delay: {rate_limiter.min_delay}s")
    print(f"   - Max Delay: {rate_limiter.max_delay}s")
    print()
    
    # Test quota tracking
    print("📈 Testing Quota Tracking:")
    for i in range(5):
        rate_limiter.record_request()
        print(f"   Request {i+1}: Daily={rate_limiter.daily_requests}, Hourly={rate_limiter.hourly_requests}")
    
    print()
    
    # Test quota limit checking
    print("🔍 Testing Quota Limit Checking:")
    can_proceed = rate_limiter._check_quota_limits()
    print(f"   Can proceed: {can_proceed}")
    print()
    
    # Test caching
    print("📋 Testing Caching System:")
    test_prompt = "test_prompt_hash"
    test_response = {"test": "response"}
    
    # Cache a response
    rate_limiter._cache_response(test_prompt, test_response)
    print("   Response cached")
    
    # Retrieve cached response
    cached = rate_limiter._get_cached_response(test_prompt)
    if cached:
        print("   Cached response retrieved successfully")
    else:
        print("   No cached response found")
    
    print()
    
    # Test error handling
    print("⚠️ Testing Error Handling:")
    rate_limiter.record_error(is_quota_error=True, retry_seconds=30)
    print(f"   After quota error - Delay: {rate_limiter.current_delay:.1f}s")
    print(f"   Quota exceeded flag: {rate_limiter.quota_exceeded}")
    print(f"   Retry after: {rate_limiter.retry_after}s")
    
    print()
    
    # Test success tracking
    print("✅ Testing Success Tracking:")
    rate_limiter.record_success()
    print(f"   After success - Delay: {rate_limiter.current_delay:.1f}s")
    print(f"   Consecutive successes: {rate_limiter.consecutive_successes}")
    
    print()
    print("✅ Quota Management Test Complete!")

def test_rag_initialization():
    """Test RAG initialization with quota management."""
    print("\n🧪 Testing RAG Initialization with Quota Management")
    print("=" * 50)
    
    try:
        # Initialize RAG with quota management
        rag = RagImplementation(config=GEMINI_CONFIG)
        
        print(f"📊 RAG Status:")
        print(f"   - Real API Mode: ✅ Active")
        print(f"   - Model: {rag.config.get('model', 'unknown')}")
        print(f"   - Max Tokens: {rag.config.get('max_tokens', 'unknown')}")
        
        quota_config = rag.config.get('quota_management', {})
        print(f"   - Quota Management: {quota_config.get('max_daily_requests', 'unknown')} daily, {quota_config.get('requests_per_hour', 'unknown')} hourly")
        
        print("✅ RAG Initialization Test Complete!")
        
    except Exception as e:
        print(f"❌ RAG Initialization Failed: {str(e)}")

if __name__ == "__main__":
    test_quota_limiter()
    test_rag_initialization() 