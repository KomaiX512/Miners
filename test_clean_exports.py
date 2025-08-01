#!/usr/bin/env python3
"""
Test script to verify that exports are clean (no metadata).
"""

import sys
import os
import json
from unittest.mock import Mock, patch

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from export_content_plan import export_competitor_analysis, export_recommendation, export_next_post
except ImportError as e:
    print(f"Import error: {e}")
    sys.exit(1)

def test_clean_exports():
    """Test that all exports are clean without metadata."""
    
    print("🔍 Testing clean exports (no metadata)...")
    
    # Test data
    test_competitor_analysis = {
        "competitor1": "Analysis of competitor1 vs primary user...",
        "competitor2": "Analysis of competitor2 vs primary user..."
    }
    
    test_recommendation = {
        "content_strategy": "Post more AI content...",
        "hashtag_strategy": "#AI #MachineLearning",
        "posting_schedule": "3 times per week"
    }
    
    test_next_post = {
        "suggested_content": "Share your latest research...",
        "optimal_hashtags": ["#AI", "#Research"],
        "predicted_engagement": "High"
    }
    
    # Test competitor analysis export
    try:
        result = export_competitor_analysis(test_competitor_analysis)
        print(f"📊 Competitor analysis export type: {type(result)}")
        print(f"📊 Competitor analysis export keys: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}")
        
        # Check for unwanted metadata
        unwanted_keys = ['module_type', 'platform', 'timestamp']
        metadata_found = []
        if isinstance(result, dict):
            for key in unwanted_keys:
                if key in result:
                    metadata_found.append(key)
        
        if metadata_found:
            print(f"❌ Competitor analysis contains metadata: {metadata_found}")
        else:
            print("✅ Competitor analysis export is clean (no metadata)")
            
    except Exception as e:
        print(f"❌ Competitor analysis export error: {e}")
    
    # Test recommendation export
    try:
        result = export_recommendation(test_recommendation)
        print(f"📊 Recommendation export type: {type(result)}")
        print(f"📊 Recommendation export keys: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}")
        
        # Check for unwanted metadata
        metadata_found = []
        if isinstance(result, dict):
            for key in unwanted_keys:
                if key in result:
                    metadata_found.append(key)
        
        if metadata_found:
            print(f"❌ Recommendation contains metadata: {metadata_found}")
        else:
            print("✅ Recommendation export is clean (no metadata)")
            
    except Exception as e:
        print(f"❌ Recommendation export error: {e}")
    
    # Test next post export
    try:
        result = export_next_post(test_next_post)
        print(f"📊 Next post export type: {type(result)}")
        print(f"📊 Next post export keys: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}")
        
        # Check for unwanted metadata
        metadata_found = []
        if isinstance(result, dict):
            for key in unwanted_keys:
                if key in result:
                    metadata_found.append(key)
        
        if metadata_found:
            print(f"❌ Next post contains metadata: {metadata_found}")
        else:
            print("✅ Next post export is clean (no metadata)")
            
    except Exception as e:
        print(f"❌ Next post export error: {e}")
    
    return True

def main():
    """Run the clean exports test."""
    print("🧪 Starting clean exports test")
    print("=" * 60)
    
    try:
        success = test_clean_exports()
        
        print("=" * 60)
        if success:
            print("🎉 EXPORT TEST COMPLETED: Check results above")
        else:
            print("💥 EXPORT TEST FAILED")
            
        return success
        
    except Exception as e:
        print(f"💥 TEST ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
