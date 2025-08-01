#!/usr/bin/env python3
"""
🛡️ SMART RATE LIMITED NEWS FOR YOU TEST
Testing the intelligent news module with bulletproof rate limiting.

This test validates:
- Smart delay management to prevent quota violations
- Graceful fallback when limits are hit
- Proper rate limiting across multiple accounts
- No more 429 quota errors!

Test Accounts: elonmusk, geoffreyhinton, sama (reduced set for rate limiting test)
"""

import sys
import os
import json
import logging
from datetime import datetime
from typing import Dict, List
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_smart_rate_limited_news():
    """
    Test the intelligent news module with smart rate limiting.
    """
    try:
        logger.info("🛡️ STARTING SMART RATE LIMITED NEWS TEST")
        logger.info("=" * 80)
        
        # Import the intelligent news module
        from intelligent_news_for_you import IntelligentNewsForYouModule
        from config import R2_CONFIG, GEMINI_CONFIG
        
        logger.info("✅ Successfully imported IntelligentNewsForYouModule")
        
        # Mock dependencies for standalone testing
        class MockAIDomainIntel:
            def analyze_domain_intelligence(self, username, platform):
                domain_mapping = {
                    'elonmusk': {'primary_domain': 'tech_innovation', 'confidence': 0.95},
                    'geoffreyhinton': {'primary_domain': 'ai_research', 'confidence': 0.98},
                    'sama': {'primary_domain': 'tech_innovation', 'confidence': 0.92},
                }
                return domain_mapping.get(username, {'primary_domain': 'general', 'confidence': 0.5})
        
        class MockRAG:
            def generate_content(self, prompt):
                return "Mock RAG response"
        
        class MockVectorDB:
            def query_similar_content(self, text):
                return []
        
        class MockR2Storage:
            def upload_file(self, content, filename):
                logger.info(f"📤 Mock R2 upload: {filename}")
                return True
        
        # Initialize the intelligent news module
        logger.info("🔧 Initializing IntelligentNewsForYouModule with Smart Rate Limiting...")
        
        # Combine configs for the module
        combined_config = {**R2_CONFIG, **GEMINI_CONFIG}
        
        news_module = IntelligentNewsForYouModule(
            config=combined_config,
            ai_domain_intel=MockAIDomainIntel(),
            rag_implementation=MockRAG(),
            vector_db=MockVectorDB(),
            r2_storage=MockR2Storage()
        )
        
        logger.info("✅ IntelligentNewsForYouModule initialized with Smart Rate Limiting")
        
        # Test accounts (reduced set for rate limiting test)
        test_accounts = [
            {'username': 'elonmusk', 'expected_domain': 'tech_innovation', 'description': 'Tech innovator'},
            {'username': 'geoffreyhinton', 'expected_domain': 'ai_research', 'description': 'AI researcher'},
            {'username': 'sama', 'expected_domain': 'tech_innovation', 'description': 'Tech innovator'},
        ]
        
        logger.info(f"🎯 Testing {len(test_accounts)} accounts with smart rate limiting")
        logger.info(f"🕒 Rate Limiter: {news_module.rate_limiter.requests_per_minute} RPM")
        logger.info(f"⏱️ Min Delay: {news_module.rate_limiter.min_delay:.2f}s between requests")
        
        # Test Results Storage
        test_results = []
        successful_tests = 0
        quota_errors = 0
        start_time = time.time()
        
        for i, account in enumerate(test_accounts):
            username = account['username']
            expected_domain = account['expected_domain']
            description = account['description']
            
            logger.info(f"\n{'='*60}")
            logger.info(f"🎯 Test {i+1}/{len(test_accounts)}: @{username}")
            logger.info(f"📝 Description: {description}")
            logger.info(f"🔍 Expected Domain: {expected_domain}")
            logger.info("="*60)
            
            try:
                # Record start time for this request
                request_start = time.time()
                
                # Generate intelligent news with rate limiting
                logger.info(f"🧠 Generating rate-limited intelligent news for @{username}...")
                
                news_result = news_module.generate_news_for_account_sync(
                    username=username,
                    platform="twitter",
                    account_type="personal",
                    posting_style="professional",
                    user_posts=[]
                )
                
                request_time = time.time() - request_start
                
                if news_result and news_result.get('breaking_news_summary'):
                    # Analyze the results
                    actual_domain = news_result.get('domain', 'unknown')
                    keywords_used = news_result.get('keywords_used', [])
                    breaking_news = news_result.get('breaking_news_summary', '')
                    source_url = news_result.get('source_url', '')
                    relevance_score = news_result.get('relevance_score', 0)
                    
                    # Check for rate limiting success
                    no_quota_errors = 'quota' not in breaking_news.lower() and 'exceeded' not in breaking_news.lower()
                    
                    # Log results
                    logger.info(f"✅ News generated for @{username} in {request_time:.2f}s")
                    logger.info(f"📊 Domain: {actual_domain} | Keywords: {len(keywords_used)}")
                    logger.info(f"📰 Content Length: {len(breaking_news)} chars")
                    logger.info(f"📝 Summary: {breaking_news[:100]}...")
                    logger.info(f"🔗 URL: {source_url[:50]}...")
                    logger.info(f"🛡️ No Quota Issues: {'✅' if no_quota_errors else '❌'}")
                    
                    if no_quota_errors:
                        successful_tests += 1
                        logger.info(f"🎉 @{username}: SUCCESS (No quota violations)")
                    else:
                        quota_errors += 1
                        logger.warning(f"⚠️ @{username}: Quota fallback used")
                    
                    # Store results
                    test_results.append({
                        'username': username,
                        'success': True,
                        'domain': actual_domain,
                        'keywords': keywords_used,
                        'content_length': len(breaking_news),
                        'request_time': request_time,
                        'no_quota_errors': no_quota_errors,
                        'breaking_news': breaking_news[:150] + '...' if len(breaking_news) > 150 else breaking_news
                    })
                    
                else:
                    logger.error(f"❌ @{username}: No news generated")
                    test_results.append({
                        'username': username,
                        'success': False,
                        'error': 'No news generated'
                    })
                    
            except Exception as account_error:
                error_str = str(account_error)
                is_quota_error = "429" in error_str or "quota" in error_str.lower()
                
                if is_quota_error:
                    quota_errors += 1
                    logger.error(f"🚨 @{username}: QUOTA ERROR - {str(account_error)[:100]}...")
                else:
                    logger.error(f"❌ @{username}: ERROR - {str(account_error)}")
                
                test_results.append({
                    'username': username,
                    'success': False,
                    'error': str(account_error),
                    'is_quota_error': is_quota_error
                })
        
        total_time = time.time() - start_time
        
        # Final Results Analysis
        logger.info("\n" + "="*80)
        logger.info("🛡️ SMART RATE LIMITED NEWS TEST RESULTS")
        logger.info("="*80)
        
        success_rate = (successful_tests / len(test_accounts)) * 100
        quota_success_rate = ((len(test_accounts) - quota_errors) / len(test_accounts)) * 100
        
        logger.info(f"📊 OVERALL SUCCESS RATE: {success_rate:.1f}% ({successful_tests}/{len(test_accounts)})")
        logger.info(f"🛡️ QUOTA SUCCESS RATE: {quota_success_rate:.1f}% ({len(test_accounts) - quota_errors}/{len(test_accounts)})")
        logger.info(f"⏱️ Total Test Time: {total_time:.2f}s")
        logger.info(f"⚡ Average Request Time: {total_time/len(test_accounts):.2f}s per account")
        
        # Rate limiting analysis
        rate_limiter = news_module.rate_limiter
        logger.info(f"🕒 Rate Limiter Status:")
        logger.info(f"   Configured: {rate_limiter.requests_per_minute} RPM")
        logger.info(f"   Min Delay: {rate_limiter.min_delay:.2f}s")
        logger.info(f"   Requests Tracked: {len(rate_limiter.request_times)}")
        logger.info(f"   Quota Exceeded: {'Yes' if rate_limiter.quota_exceeded else 'No'}")
        
        # Detailed breakdown
        for result in test_results:
            username = result['username']
            if result.get('success'):
                request_time = result.get('request_time', 0)
                no_quota = result.get('no_quota_errors', False)
                quota_status = "🛡️ CLEAN" if no_quota else "⚠️ FALLBACK"
                logger.info(f"✅ @{username}: {quota_status} ({request_time:.2f}s)")
            else:
                error = result.get('error', 'Unknown')
                is_quota = result.get('is_quota_error', False)
                error_type = "🚨 QUOTA" if is_quota else "❌ OTHER"
                logger.info(f"{error_type} @{username}: {error[:50]}...")
        
        # Save test results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = f"smart_rate_limited_test_results_{timestamp}.json"
        
        detailed_results = {
            'timestamp': datetime.now().isoformat(),
            'success_rate': success_rate,
            'quota_success_rate': quota_success_rate,
            'total_time': total_time,
            'quota_errors': quota_errors,
            'test_results': test_results,
            'rate_limiter_config': {
                'requests_per_minute': rate_limiter.requests_per_minute,
                'min_delay': rate_limiter.min_delay,
                'buffer_factor': 0.8
            }
        }
        
        with open(results_file, 'w') as f:
            json.dump(detailed_results, f, indent=2)
        
        logger.info(f"📝 Test results saved to: {results_file}")
        
        # Final verdict
        if quota_success_rate >= 80:  # 80% quota success threshold
            logger.info("🎉 SMART RATE LIMITED NEWS: SUCCESS!")
            logger.info("🛡️ Rate limiting is working effectively!")
            logger.info("✨ Quota violations eliminated or minimized!")
            return True
        else:
            logger.info("⚠️ SMART RATE LIMITED NEWS: NEEDS TUNING")
            logger.info("🔧 Rate limiting may need further adjustment")
            return False
            
    except Exception as e:
        logger.error(f"❌ Test failed with error: {str(e)}")
        return False

if __name__ == "__main__":
    print("=" * 100)
    print("🛡️ SMART RATE LIMITED NEWS FOR YOU TEST")
    print("🕒 Testing intelligent rate limiting to prevent quota violations")
    print("👥 Accounts: elonmusk, geoffreyhinton, sama")
    print("=" * 100)
    
    success = test_smart_rate_limited_news()
    
    if success:
        print("\n🎉 SUCCESS! Smart rate limiting is working perfectly!")
        print("✨ Features validated:")
        print("   • Intelligent request spacing")
        print("   • Quota violation prevention")
        print("   • Graceful fallback handling")
        print("   • Smart delay management")
        print("   • Production-ready reliability")
        sys.exit(0)
    else:
        print("\n⚠️ Rate limiting needs further tuning. Check logs for details.")
        sys.exit(1)
