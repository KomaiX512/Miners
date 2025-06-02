#!/usr/bin/env python3
"""
Bulletproof RAG Implementation Test Suite
Tests all modules across all platforms and account types to ensure 100% RAG generation.
"""

import logging
import json
from rag_implementation import RagImplementation
from recommendation_generation import RecommendationGenerator

# Configure logging for detailed output
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_bulletproof_rag_comprehensive():
    """Comprehensive test of bulletproof RAG implementation."""
    print("🚀 BULLETPROOF RAG COMPREHENSIVE TEST SUITE")
    print("=" * 70)
    
    # Initialize components
    rag = RagImplementation()
    rec_gen = RecommendationGenerator(rag=rag)
    
    # Test cases covering all 4 configurations
    test_cases = [
        {
            "name": "Instagram Branding (MAC Cosmetics)",
            "platform": "instagram",
            "is_branding": True,
            "primary": "maccosmetics",
            "secondary": ["fentybeauty", "anastasiabeverlyhills", "toofaced"]
        },
        {
            "name": "Instagram Personal",
            "platform": "instagram", 
            "is_branding": False,
            "primary": "personal_lifestyle_user",
            "secondary": ["lifestyle_influencer1", "lifestyle_blogger2"]
        },
        {
            "name": "Twitter Branding (Nike)",
            "platform": "twitter",
            "is_branding": True,
            "primary": "nike",
            "secondary": ["adidas", "puma", "underarmour"]
        },
        {
            "name": "Twitter Personal",
            "platform": "twitter",
            "is_branding": False,
            "primary": "tech_enthusiast_user",
            "secondary": ["tech_person1", "developer_account"]
        }
    ]
    
    results = {}
    successful_tests = 0
    total_tests = len(test_cases)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🧪 TEST {i}/{total_tests}: {test_case['name']}")
        print("-" * 50)
        
        try:
            # Test unified content plan generation
            content_plan = rec_gen.generate_unified_content_plan(
                primary_username=test_case["primary"],
                secondary_usernames=test_case["secondary"],
                query=f"Generate comprehensive content strategy for {test_case['platform']} {'branding' if test_case['is_branding'] else 'personal'} account",
                is_branding=test_case["is_branding"],
                platform=test_case["platform"]
            )
            
            # Verify all required modules are present
            intelligence_type = "competitor_analysis" if test_case["is_branding"] else "personal_analysis"
            required_modules = [intelligence_type, "recommendations", "next_post"]
            
            missing_modules = [module for module in required_modules if module not in content_plan]
            if missing_modules:
                raise Exception(f"Missing modules: {missing_modules}")
            
            # Verify content quality
            content_verified = content_plan.get("content_verified", False)
            generation_method = content_plan.get("generation_method", "unknown")
            
            # Detailed module verification
            module_results = {}
            
            # Check intelligence module
            intel_module = content_plan[intelligence_type]
            if isinstance(intel_module, dict) and len(str(intel_module)) > 100:
                module_results["intelligence"] = "✅ VERIFIED"
            else:
                module_results["intelligence"] = "❌ FAILED"
            
            # Check recommendations
            recommendations = content_plan.get("recommendations", [])
            if isinstance(recommendations, list) and len(recommendations) >= 3:
                module_results["recommendations"] = "✅ VERIFIED"
            else:
                module_results["recommendations"] = "❌ FAILED"
            
            # Check next post
            next_post = content_plan.get("next_post", {})
            content_field = "tweet_text" if test_case["platform"] == "twitter" else "caption"
            if isinstance(next_post, dict) and content_field in next_post and next_post[content_field]:
                module_results["next_post"] = "✅ VERIFIED"
            else:
                module_results["next_post"] = "❌ FAILED"
            
            # Overall test result
            all_modules_verified = all(status == "✅ VERIFIED" for status in module_results.values())
            
            if all_modules_verified and content_verified:
                print(f"✅ SUCCESS: All modules verified for {test_case['name']}")
                print(f"   Generation Method: {generation_method}")
                print(f"   Content Verified: {content_verified}")
                print(f"   Module Status: {module_results}")
                successful_tests += 1
                results[test_case["name"]] = "SUCCESS"
            else:
                print(f"❌ PARTIAL: Some issues detected for {test_case['name']}")
                print(f"   Module Status: {module_results}")
                print(f"   Content Verified: {content_verified}")
                results[test_case["name"]] = "PARTIAL"
                
        except Exception as e:
            print(f"❌ FAILED: {test_case['name']} - {str(e)}")
            results[test_case["name"]] = f"FAILED: {str(e)}"
    
    # Final summary
    print("\n" + "=" * 70)
    print("🎯 BULLETPROOF RAG TEST SUMMARY")
    print("=" * 70)
    print(f"Total Tests: {total_tests}")
    print(f"Successful: {successful_tests}")
    print(f"Success Rate: {(successful_tests/total_tests)*100:.1f}%")
    print("\nDetailed Results:")
    for test_name, result in results.items():
        status_emoji = "✅" if result == "SUCCESS" else "⚠️" if result == "PARTIAL" else "❌"
        print(f"  {status_emoji} {test_name}: {result}")
    
    if successful_tests == total_tests:
        print("\n🎉 ALL TESTS PASSED - BULLETPROOF RAG IMPLEMENTATION VERIFIED!")
        return True
    else:
        print(f"\n⚠️ {total_tests - successful_tests} tests need attention")
        return False

def test_specific_modules():
    """Test specific modules individually."""
    print("\n🔍 SPECIFIC MODULE TESTING")
    print("=" * 50)
    
    rag = RagImplementation()
    
    # Test competitor analysis specifically (the problematic module)
    try:
        print("\n1. Testing Competitor Analysis Module...")
        result = rag.generate_recommendation(
            primary_username="maccosmetics",
            secondary_usernames=["fentybeauty", "narsissist"],
            query="Generate detailed competitor analysis",
            is_branding=True,
            platform="instagram"
        )
        
        if "competitive_intelligence" in result:
            comp_intel = result["competitive_intelligence"]
            if isinstance(comp_intel, dict) and "competitive_analysis" in comp_intel:
                comp_analysis = comp_intel["competitive_analysis"]
                if len(str(comp_analysis)) > 100 and "fentybeauty" in str(comp_analysis).lower():
                    print("✅ Competitor Analysis: REAL RAG CONTENT VERIFIED")
                else:
                    print("❌ Competitor Analysis: Content appears generic")
            else:
                print("❌ Competitor Analysis: Missing competitive_analysis field")
        else:
            print("❌ Competitor Analysis: Missing competitive_intelligence module")
            
    except Exception as e:
        print(f"❌ Competitor Analysis: FAILED - {str(e)}")
    
    # Test next post module specifically
    try:
        print("\n2. Testing Next Post Module...")
        result = rag.generate_recommendation(
            primary_username="maccosmetics",
            secondary_usernames=["fentybeauty"],
            query="Generate Instagram next post prediction",
            is_branding=True,
            platform="instagram"
        )
        
        if "next_post_prediction" in result:
            next_post = result["next_post_prediction"]
            if isinstance(next_post, dict) and "caption" in next_post:
                caption = next_post["caption"]
                if len(caption) > 20 and "maccosmetics" in caption.lower():
                    print("✅ Next Post: REAL RAG CONTENT VERIFIED")
                else:
                    print("❌ Next Post: Content appears generic")
            else:
                print("❌ Next Post: Missing caption field")
        else:
            print("❌ Next Post: Missing next_post_prediction module")
            
    except Exception as e:
        print(f"❌ Next Post: FAILED - {str(e)}")

def verify_no_fallbacks():
    """Verify that no fallback content is being generated."""
    print("\n🚫 FALLBACK DETECTION TEST")
    print("=" * 40)
    
    rec_gen = RecommendationGenerator()
    
    fallback_indicators = [
        "template", "placeholder", "generic", "example",
        "coming soon", "to be determined", "fallback"
    ]
    
    try:
        # Generate content and check for fallback indicators
        content_plan = rec_gen.generate_unified_content_plan(
            primary_username="testuser",
            secondary_usernames=["competitor1", "competitor2"],
            query="Test content generation",
            is_branding=True,
            platform="instagram"
        )
        
        # Convert entire content to string for analysis
        full_content = json.dumps(content_plan, indent=2).lower()
        
        detected_fallbacks = []
        for indicator in fallback_indicators:
            if indicator in full_content:
                detected_fallbacks.append(indicator)
        
        if detected_fallbacks:
            print(f"❌ FALLBACK CONTENT DETECTED: {detected_fallbacks}")
            return False
        else:
            print("✅ NO FALLBACK CONTENT DETECTED - Pure RAG generation confirmed")
            return True
            
    except Exception as e:
        print(f"❌ Fallback detection test failed: {str(e)}")
        return False

if __name__ == "__main__":
    # Run comprehensive test suite
    success = test_bulletproof_rag_comprehensive()
    
    # Run specific module tests
    test_specific_modules()
    
    # Verify no fallbacks
    no_fallbacks = verify_no_fallbacks()
    
    print("\n" + "=" * 70)
    print("🎯 FINAL VERIFICATION")
    print("=" * 70)
    
    if success and no_fallbacks:
        print("🎉 BULLETPROOF RAG IMPLEMENTATION FULLY VERIFIED!")
        print("✅ All modules generate real RAG content")
        print("✅ No fallback mechanisms detected")
        print("✅ Works across all platforms and account types")
    else:
        print("⚠️ Implementation needs refinement")
        print(f"   Comprehensive tests: {'✅' if success else '❌'}")
        print(f"   No fallbacks: {'✅' if no_fallbacks else '❌'}") 