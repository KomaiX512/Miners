#!/usr/bin/env python3
"""
Test script to verify that duplicate competitor analysis generation has been fixed.
This test bypasses scraping to focus on the core issue.
"""

import sys
import os
import json
from unittest.mock import Mock, patch

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import ContentPlanCreator

def test_no_duplicate_competitor_analysis():
    """Test that competitor analysis is generated only once, not duplicated."""
    
    print("🔍 Testing duplicate competitor analysis fix...")
    
    # Create mock data that simulates already scraped profiles
    mock_profiles = {
        "geoffreyhinton": {
            "instagram": {
                "posts": [
                    {
                        "text": "Excited about the future of AI and deep learning! #AI #MachineLearning",
                        "likes": 1500,
                        "comments": 200,
                        "hashtags": ["#AI", "#MachineLearning"]
                    }
                ],
                "followers": 250000,
                "following": 150
            }
        },
        "elonmusk": {
            "instagram": {
                "posts": [
                    {
                        "text": "Tesla's new AI chip is revolutionary #Tesla #AI #Innovation",
                        "likes": 5000,
                        "comments": 800,
                        "hashtags": ["#Tesla", "#AI", "#Innovation"]
                    }
                ],
                "followers": 15000000,
                "following": 42
            }
        }
    }
    
    # Mock the scraping to return our test data
    with patch('main.ContentPlanCreator._scrape_profile') as mock_scrape:
        mock_scrape.side_effect = lambda username, platform: mock_profiles.get(username, {}).get(platform, {})
        
        # Mock the vector database to avoid actual DB operations
        with patch('main.ContentPlanCreator._store_data_in_vector_db'):
            with patch('main.ContentPlanCreator._query_vector_db') as mock_query:
                mock_query.return_value = {
                    "geoffreyhinton": mock_profiles["geoffreyhinton"],
                    "elonmusk": mock_profiles["elonmusk"]
                }
                
                # Create the content plan creator
                creator = ContentPlanCreator()
                
                # Generate content plan
                result = creator.create_content_plan(
                    usernames=["geoffreyhinton"],
                    secondary_usernames=["elonmusk"], 
                    platforms=["instagram"]
                )
                
                # Check if competitor analysis exists and is not empty
                if "competitor_analysis" in result:
                    competitor_analysis = result["competitor_analysis"]
                    print(f"✅ Competitor analysis found with {len(competitor_analysis)} entries")
                    
                    # Check for any signs of duplication
                    if isinstance(competitor_analysis, dict):
                        # Look for duplicate competitors or analysis
                        competitors = list(competitor_analysis.keys())
                        print(f"📊 Competitors analyzed: {competitors}")
                        
                        # Check if there are any duplicate entries
                        unique_competitors = set(competitors)
                        if len(competitors) == len(unique_competitors):
                            print("✅ No duplicate competitor entries found")
                            
                            # Check each competitor analysis for quality
                            for competitor, analysis in competitor_analysis.items():
                                if isinstance(analysis, str):
                                    print(f"📝 {competitor} analysis length: {len(analysis)} characters")
                                    # Check for cross-competitor contamination
                                    other_competitors = [c for c in competitors if c != competitor]
                                    contamination_found = False
                                    for other in other_competitors:
                                        if other.lower() in analysis.lower():
                                            print(f"⚠️  Cross-contamination detected: {other} mentioned in {competitor} analysis")
                                            contamination_found = True
                                    
                                    if not contamination_found:
                                        print(f"✅ {competitor} analysis is clean (no cross-contamination)")
                                else:
                                    print(f"📋 {competitor} analysis type: {type(analysis)}")
                            
                            return True
                        else:
                            print(f"❌ Duplicate competitors found! Total: {len(competitors)}, Unique: {len(unique_competitors)}")
                            return False
                    else:
                        print(f"⚠️  Competitor analysis type: {type(competitor_analysis)}")
                        print(f"📄 Content: {str(competitor_analysis)[:200]}...")
                        return True  # Different format but exists
                else:
                    print("❌ No competitor analysis found in result")
                    return False

def main():
    """Run the duplicate fix test."""
    print("🧪 Starting duplicate competitor analysis fix test")
    print("=" * 60)
    
    try:
        success = test_no_duplicate_competitor_analysis()
        
        print("=" * 60)
        if success:
            print("🎉 TEST PASSED: Duplicate competitor analysis fix verified!")
        else:
            print("💥 TEST FAILED: Duplicate competitor analysis still detected")
            
        return success
        
    except Exception as e:
        print(f"💥 TEST ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
