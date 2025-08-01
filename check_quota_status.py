#!/usr/bin/env python3
"""
Quick script to check current quota status and configuration
"""

from config import GEMINI_CONFIG
from rag_implementation import AdaptiveRateLimiter
import json

def check_current_status():
    print("🔍 Current Gemini API Quota Management Status")
    print("=" * 50)
    
    # Check configuration
    print("📊 Configuration:")
    print(f"   Model: {GEMINI_CONFIG.get('model', 'unknown')}")
    print(f"   Max Tokens: {GEMINI_CONFIG.get('max_tokens', 'unknown')}")
    print(f"   API Key: {'✅ Set' if GEMINI_CONFIG.get('api_key') else '❌ Not Set'}")
    
    quota_config = GEMINI_CONFIG.get('quota_management', {})
    print(f"\n📈 Quota Management:")
    print(f"   Max Daily Requests: {quota_config.get('max_daily_requests', 'Not Set')}")
    print(f"   Max Hourly Requests: {quota_config.get('requests_per_hour', 'Not Set')}")
    print(f"   Caching Enabled: {quota_config.get('enable_caching', 'Not Set')}")
    print(f"   Fallback to Mock: {quota_config.get('fallback_to_mock', 'Not Set')}")
    
    # Initialize rate limiter to check current state
    rate_limiter = AdaptiveRateLimiter(quota_config=quota_config)
    print(f"\n🕒 Rate Limiter Status:")
    print(f"   Current Delay: {rate_limiter.current_delay:.1f}s")
    print(f"   Daily Requests: {rate_limiter.daily_requests}")
    print(f"   Hourly Requests: {rate_limiter.hourly_requests}")
    print(f"   Quota Exceeded: {rate_limiter.quota_exceeded}")
    
    # Check if system is ready
    can_proceed = rate_limiter._check_quota_limits()
    print(f"\n✅ System Status:")
    print(f"   Can Make Requests: {can_proceed}")
    print(f"   Quota Available: {'Yes' if can_proceed else 'No'}")
    
    if can_proceed:
        remaining_daily = quota_config.get('max_daily_requests', 45) - rate_limiter.daily_requests
        remaining_hourly = quota_config.get('requests_per_hour', 10) - rate_limiter.hourly_requests
        print(f"   Remaining Daily: {remaining_daily}")
        print(f"   Remaining Hourly: {remaining_hourly}")
    
    print("\n🎯 Recommendations:")
    if not can_proceed:
        print("   ⚠️  Quota limit reached - system will use mock mode")
    elif rate_limiter.daily_requests > 40:
        print("   ⚠️  Approaching daily limit - consider reducing usage")
    elif rate_limiter.hourly_requests > 8:
        print("   ⚠️  Approaching hourly limit - consider spacing requests")
    else:
        print("   ✅ Quota usage is healthy")
    
    print("\n📋 Next Steps:")
    print("   1. Monitor quota usage with: tail -f logs | grep 'Quota usage'")
    print("   2. Test system with: python3 test_quota_management.py")
    print("   3. Check cache effectiveness in logs")

if __name__ == "__main__":
    check_current_status() 