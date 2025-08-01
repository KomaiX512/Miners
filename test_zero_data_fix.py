#!/usr/bin/env python3
"""
Test script to reproduce and fix zero data handling issues.
"""

import logging
import json
from main import ContentRecommendationSystem

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_zero_data_handling():
    """Test zero data handling with typo primary username and correct competitors."""
    
    print("=" * 80)
    print("🧪 ZERO DATA HANDLING TEST")
    print("=" * 80)
    
    # Test Case 1: Typo primary username with correct competitors
    print("\n📋 TEST CASE 1: Typo primary username, correct competitors")
    print("Primary: wrongtypo (should have no data)")
    print("Competitors: gdb, geoffreyhinton (known to exist)")
    print("Platform: twitter (using known good data)")
    
    try:
        system = ContentRecommendationSystem()
        
        # Test the process_social_data method directly
        print("\n🔍 Testing process_social_data with typo username...")
        
        # This should trigger the zero data handler
        data_key = "twitter/wrongtypo/wrongtypo.json"  # Typo username that doesn't exist
        result = system.process_social_data(data_key)
        
        print(f"Result: {result}")
        
        if result is None:
            print("✅ EXPECTED: process_social_data returned None for non-existent data")
            
            # Now test the zero data pipeline directly
            print("\n🔧 Testing zero data pipeline directly...")
            
            zero_result = system._handle_zero_data_account_pipeline(
                username="wrongtypo",
                competitors=["gdb", "geoffreyhinton"],  # Known existing usernames
                platform="twitter",
                account_type="personal",
                posting_style="informative"
            )
            
            print(f"Zero data handler result: {json.dumps(zero_result, indent=2)}")
            
            if zero_result and zero_result.get('success'):
                print("✅ Zero data handler worked correctly")
                return True
            else:
                print("❌ Zero data handler failed")
                return False
        else:
            print(f"❌ UNEXPECTED: Got result for non-existent data: {type(result)}")
            return False
            
    except Exception as e:
        print(f"❌ Error in test: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_competitor_data_collection():
    """Test competitor data collection works with correct usernames."""
    
    print("\n" + "=" * 80)
    print("🧪 COMPETITOR DATA COLLECTION TEST")
    print("=" * 80)
    
    try:
        system = ContentRecommendationSystem()
        
        # Test competitor data collection
        print("\n🔍 Testing competitor data collection...")
        
        competitors = ["gdb", "geoffreyhinton"]  # Known existing usernames
        competitor_data = system._collect_available_competitor_data(competitors, "twitter")
        
        print(f"Competitor data collected: {len(competitor_data)} competitors")
        for comp, data in competitor_data.items():
            print(f"  - {comp}: {len(data.get('posts', []))} posts")
        
        if competitor_data:
            print("✅ Competitor data collection worked")
            return True
        else:
            print("❌ No competitor data collected")
            return False
            
    except Exception as e:
        print(f"❌ Error in competitor test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 Starting zero data handling tests...")
    
    # Test 1: Zero data handling
    test1_result = test_zero_data_handling()
    
    # Test 2: Competitor data collection
    test2_result = test_competitor_data_collection()
    
    print("\n" + "=" * 80)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 80)
    print(f"Test 1 (Zero Data Handling): {'✅ PASS' if test1_result else '❌ FAIL'}")
    print(f"Test 2 (Competitor Collection): {'✅ PASS' if test2_result else '❌ FAIL'}")
    
    if test1_result and test2_result:
        print("\n🎉 ALL TESTS PASSED!")
    else:
        print("\n⚠️ SOME TESTS FAILED - Need debugging")
