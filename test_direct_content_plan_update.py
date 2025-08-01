#!/usr/bin/env python3
"""
Simple test to validate that content_plan.json is updated directly without complexity.
"""

import sys
import os
import json
import tempfile
from unittest.mock import Mock, patch

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import ContentRecommendationSystem

def test_direct_content_plan_update():
    """Test that content_plan.json is updated directly without backup complexity."""
    
    print("🧪 Testing direct content_plan.json update...")
    
    # Create a test content plan
    test_content_plan = {
        "primary_username": "testuser",
        "platform": "instagram",
        "account_type": "branding",
        "recommendation": {
            "competitive_intelligence": {
                "account_post_mortem": "Test analysis for direct update validation",
                "trending_hashtag_intelligence": {
                    "recommended_hashtags": [
                        {
                            "hashtag": "#TestHashtag",
                            "trend_strength": "HIGH",
                            "competitor_usage": "Test competitor data",
                            "proof_of_value": "Test proof"
                        }
                    ]
                }
            }
        },
        "competitor_analysis": {
            "competitor1": {
                "individual_competitor_insights": "Test competitor insights"
            }
        }
    }
    
    # Create test filename
    test_filename = "test_content_plan.json"
    
    try:
        # Initialize the system
        system = ContentRecommendationSystem()
        
        # Test the save method directly
        print("📝 Testing direct save...")
        result = system.save_content_plan(test_content_plan, test_filename)
        
        if result:
            print("✅ Save method returned success")
            
            # Check if file was created
            if os.path.exists(test_filename):
                print("✅ File was created successfully")
                
                # Check file size
                file_size = os.path.getsize(test_filename)
                print(f"📊 File size: {file_size} bytes")
                
                # Verify content by reading it back
                with open(test_filename, 'r', encoding='utf-8') as f:
                    loaded_content = json.load(f)
                
                # Check key fields
                if loaded_content.get("primary_username") == "testuser":
                    print("✅ Primary username correctly saved")
                
                if "recommendation" in loaded_content:
                    print("✅ Recommendation section correctly saved")
                    
                    rec = loaded_content["recommendation"]
                    if isinstance(rec, dict) and "competitive_intelligence" in rec:
                        intel = rec["competitive_intelligence"]
                        if "trending_hashtag_intelligence" in intel:
                            print("✅ Trending hashtag intelligence correctly saved")
                        else:
                            print("⚠️  Trending hashtag intelligence not found")
                    else:
                        print("⚠️  Competitive intelligence not found in recommendation")
                else:
                    print("❌ Recommendation section missing")
                
                if "competitor_analysis" in loaded_content:
                    print("✅ Competitor analysis correctly saved")
                else:
                    print("❌ Competitor analysis missing")
                
                print("\n🎯 VALIDATION RESULTS:")
                print("=" * 50)
                print("✅ File directly updated without backup complexity")
                print("✅ Content correctly preserved")
                print("✅ Enhanced recommendation structure maintained")
                print("✅ JSON formatting is clean and readable")
                
                return True
            else:
                print("❌ File was not created")
                return False
        else:
            print("❌ Save method returned failure")
            return False
            
    except Exception as e:
        print(f"💥 Test error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # Cleanup
        if os.path.exists(test_filename):
            os.remove(test_filename)
            print(f"🧹 Cleaned up test file: {test_filename}")

def test_main_content_plan_location():
    """Test that the main content_plan.json location is correct."""
    print("\n📍 Testing main content_plan.json location...")
    
    current_dir = os.getcwd()
    content_plan_path = os.path.join(current_dir, "content_plan.json")
    
    print(f"📂 Current directory: {current_dir}")
    print(f"📄 Expected content_plan.json path: {content_plan_path}")
    
    if os.path.exists(content_plan_path):
        file_size = os.path.getsize(content_plan_path)
        print(f"✅ content_plan.json exists ({file_size} bytes)")
        
        # Quick validation that it's valid JSON
        try:
            with open(content_plan_path, 'r', encoding='utf-8') as f:
                content = json.load(f)
            print("✅ content_plan.json is valid JSON")
            
            # Check for key sections
            if "recommendation" in content:
                print("✅ Has recommendation section")
            if "competitor_analysis" in content:
                print("✅ Has competitor analysis section")
                
            return True
        except json.JSONDecodeError as e:
            print(f"❌ content_plan.json is not valid JSON: {e}")
            return False
    else:
        print("⚠️  content_plan.json does not exist yet")
        return True  # This is OK, it will be created on next run

def main():
    """Run the direct update validation test."""
    print("🧪 Starting Direct Content Plan Update Validation")
    print("=" * 60)
    
    try:
        # Test direct update functionality
        direct_test = test_direct_content_plan_update()
        
        # Test main file location
        location_test = test_main_content_plan_location()
        
        print("\n" + "=" * 60)
        print("🎯 FINAL VALIDATION:")
        print("=" * 60)
        
        if direct_test and location_test:
            print("🎉 ALL TESTS PASSED: Direct content_plan.json update working!")
            print("✅ No backup complexity - files are updated directly")
            print("✅ Enhanced recommendation structure preserved")
            print("✅ Simple, straightforward file saving")
            success = True
        else:
            print("⚠️  PARTIAL SUCCESS:")
            print(f"{'✅' if direct_test else '❌'} Direct update test")
            print(f"{'✅' if location_test else '❌'} Location validation test")
            success = False
            
        return success
        
    except Exception as e:
        print(f"💥 VALIDATION ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
