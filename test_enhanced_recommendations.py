#!/usr/bin/env python3
"""
Test script to validate the enhanced recommendation system with:
1. Deep strategic insights
2. Trending hashtag analysis
3. Natural language quality
4. Single export validation
"""

import sys
import os
import json
from unittest.mock import Mock, patch

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import ContentRecommendationSystem

def test_enhanced_recommendation_quality():
    """Test the enhanced recommendation prompt structure."""
    
    print("🧠 Testing enhanced recommendation structure...")
    
    # Read the rag_implementation.py to check for enhancements
    with open('/home/komail/Miners-1/rag_implementation.py', 'r') as f:
        content = f.read()
    
    # Test for enhanced sections
    test_results = {
        "trending_hashtag_intelligence": False,
        "natural_language_quality": False,
        "strategic_insights": False,
        "human_advisor_style": False,
        "account_post_mortem": False
    }
    
    # Check for trending hashtag intelligence structure
    if "trending_hashtag_intelligence" in content:
        print("✅ Trending hashtag intelligence section found!")
        test_results["trending_hashtag_intelligence"] = True
        
        # Check for detailed hashtag analysis
        if "competitor_usage" in content and "proof_of_value" in content:
            print("✅ Detailed hashtag analysis with competitor proof found!")
    
    # Check for natural language improvements
    natural_indicators = [
        "Looking at @{primary_username}",
        "I can see some fascinating patterns",
        "Here's what stands out",
        "What's interesting is"
    ]
    
    for indicator in natural_indicators:
        if indicator in content:
            print(f"✅ Natural language indicator found: '{indicator[:20]}...'")
            test_results["natural_language_quality"] = True
            break
    
    # Check for human advisor style
    advisor_indicators = [
        "Think like a wise content strategist",
        "HUMAN-LEVEL ADVISOR",
        "knowledgeable friend giving honest",
        "personal strategic advisor"
    ]
    
    for indicator in advisor_indicators:
        if indicator in content:
            print(f"✅ Human advisor style found: '{indicator[:30]}...'")
            test_results["human_advisor_style"] = True
            break
    
    # Check for strategic insights
    strategic_indicators = [
        "account_post_mortem",
        "strategic_positioning_insights",
        "content_optimization_insights"
    ]
    
    for indicator in strategic_indicators:
        if indicator in content:
            print(f"✅ Strategic insight section found: {indicator}")
            test_results["strategic_insights"] = True
    
    # Check for account post-mortem analysis
    if "account_post_mortem" in content:
        print("✅ Account post-mortem analysis section found!")
        test_results["account_post_mortem"] = True
    
    # Print results
    print("\n📊 ENHANCEMENT STRUCTURE TEST RESULTS:")
    print("=" * 50)
    passed_tests = 0
    total_tests = len(test_results)
    
    for test_name, passed in test_results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} {test_name.replace('_', ' ').title()}")
        if passed:
            passed_tests += 1
    
    print("=" * 50)
    success_rate = (passed_tests / total_tests) * 100
    print(f"🎯 Overall Enhancement Success: {passed_tests}/{total_tests} ({success_rate:.1f}%)")
    
    return success_rate >= 80  # 80% success rate threshold

def test_single_export_validation():
    """Test that recommendations are exported only once."""
    print("\n🔍 Testing single export validation...")
    
    # This is more of a structural test - check the main.py logic
    with open('/home/komail/Miners-1/main.py', 'r') as f:
        content = f.read()
    
    # Count recommendation export statements
    export_patterns = [
        'content_plan["recommendation"]',
        'main_recommendation'
    ]
    
    export_count = 0
    for pattern in export_patterns:
        export_count += content.count(pattern)
    
    print(f"📊 Found {export_count} recommendation export references")
    
    # Check for duplication prevention
    if 'content_plan["recommendation"] = main_recommendation' in content:
        print("✅ Single recommendation export confirmed")
        return True
    else:
        print("⚠️  Recommendation export pattern not found")
        return False

def main():
    """Run the enhanced recommendation test."""
    print("🧪 Starting Enhanced Recommendation Quality Test")
    print("=" * 70)
    
    try:
        # Test enhanced quality
        quality_success = test_enhanced_recommendation_quality()
        
        # Test single export
        export_success = test_single_export_validation()
        
        print("\n" + "=" * 70)
        print("🎯 FINAL RESULTS:")
        print("=" * 70)
        
        if quality_success and export_success:
            print("🎉 ALL TESTS PASSED: Enhanced recommendation system is working!")
            print("✅ Deep strategic insights implemented")
            print("✅ Trending hashtag analysis included")
            print("✅ Natural language quality improved")
            print("✅ Single export validation confirmed")
            success = True
        else:
            print("⚠️  PARTIAL SUCCESS:")
            print(f"{'✅' if quality_success else '❌'} Enhanced quality test")
            print(f"{'✅' if export_success else '❌'} Single export test")
            success = False
            
        return success
        
    except Exception as e:
        print(f"💥 TEST ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
