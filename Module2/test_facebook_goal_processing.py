#!/usr/bin/env python3
"""
Test script to verify Facebook goal processing functionality
"""

import asyncio
import json
import os
from datetime import datetime
from goal_rag_handler import EnhancedGoalHandler
from xgboost_post_estimator import XGBoostPostEstimator

async def test_facebook_goal_processing():
    """Test Facebook goal processing functionality"""
    print("🧪 Testing Facebook goal processing...")
    
    # Initialize handlers
    goal_handler = EnhancedGoalHandler()
    estimator = XGBoostPostEstimator()
    
    # Test 1: Verify platforms list includes Facebook
    print(f"✅ Platforms supported: {goal_handler.platforms}")
    assert 'facebook' in goal_handler.platforms, "Facebook not in supported platforms"
    
    # Test 2: Verify XGBoost estimator supports Facebook
    print(f"✅ Facebook hashtags available: {'facebook' in estimator.hashtag_database}")
    assert 'facebook' in estimator.hashtag_database, "Facebook not in hashtag database"
    
    # Test 3: Create a sample Facebook goal for testing
    sample_facebook_goal = {
        "username": "test_facebook_user",
        "platform": "facebook",
        "goal_type": "increase",
        "current_engagement": 0.05,
        "target_engagement": 0.08,
        "follower_count": 5000,
        "timeline_days": 30,
        "created_at": datetime.now().isoformat()
    }
    
    # Test 4: Test XGBoost estimation for Facebook goal
    try:
        profile_analysis = {
            "avg_posts_per_week": 3,
            "consistency_score": 0.7,
            "content_variety_score": 0.8,
            "peak_engagement_ratio": 1.5
        }
        
        posts_needed, confidence, details = estimator.estimate_posts(
            sample_facebook_goal, 
            profile_analysis
        )
        
        print(f"✅ Facebook goal estimation successful:")
        print(f"   Posts needed: {posts_needed}")
        print(f"   Confidence: {confidence}")
        print(f"   Details: {details}")
        
    except Exception as e:
        print(f"❌ Facebook goal estimation failed: {e}")
        return False
    
    # Test 5: Test hashtag recommendations for Facebook
    try:
        hashtags = estimator.get_hashtag_recommendations(
            content_themes=["business", "community"],
            platform="facebook",
            engagement_goal="increase",
            follower_count=5000
        )
        
        print(f"✅ Facebook hashtag recommendations: {hashtags[:5]}")
        
    except Exception as e:
        print(f"❌ Facebook hashtag recommendations failed: {e}")
        return False
    
    print("🎉 All Facebook goal processing tests passed!")
    return True

if __name__ == "__main__":
    asyncio.run(test_facebook_goal_processing()) 