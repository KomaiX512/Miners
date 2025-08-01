#!/usr/bin/env python3
"""
Test script to verify XGBoost Post Estimator fixes
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from xgboost_post_estimator import XGBoostPostEstimator
from utils.logging import logger

def test_xgboost_estimator():
    """Test the XGBoost post estimator with various scenarios"""
    
    print("🧪 Testing XGBoost Post Estimator...")
    
    # Initialize estimator
    estimator = XGBoostPostEstimator()
    
    # Get model info
    model_info = estimator.get_model_info()
    print(f"📊 Model Info: {model_info}")
    
    # Test scenarios
    test_scenarios = [
        {
            'name': 'Instagram Growth',
            'goal': {
                'goal': 'I want to increase engagement by 50%',
                'timeline': 7,
                'platform': 'instagram'
            },
            'profile_analysis': {
                'followers': 5000,
                'engagement_patterns': {
                    'avg_engagement_rate': 0.03,
                    'engagement_growth_trend': 'increasing'
                },
                'posting_frequency': {
                    'avg_posts_per_week': 5,
                    'consistency_score': 0.7
                }
            }
        },
        {
            'name': 'Twitter Double Engagement',
            'goal': {
                'goal': 'I want to double my engagement rate',
                'timeline': 14,
                'platform': 'twitter'
            },
            'profile_analysis': {
                'followers': 2000,
                'engagement_patterns': {
                    'avg_engagement_rate': 0.02,
                    'engagement_growth_trend': 'stable'
                },
                'posting_frequency': {
                    'avg_posts_per_week': 3,
                    'consistency_score': 0.5
                }
            }
        },
        {
            'name': 'High Engagement Account',
            'goal': {
                'goal': 'I want to increase engagement by 25%',
                'timeline': 5,
                'platform': 'instagram'
            },
            'profile_analysis': {
                'followers': 50000,
                'engagement_patterns': {
                    'avg_engagement_rate': 0.08,
                    'engagement_growth_trend': 'increasing'
                },
                'posting_frequency': {
                    'avg_posts_per_week': 8,
                    'consistency_score': 0.8
                }
            }
        }
    ]
    
    for scenario in test_scenarios:
        print(f"\n🎯 Testing: {scenario['name']}")
        
        try:
            estimated_posts, rationale, metrics = estimator.estimate_posts(
                scenario['goal'],
                scenario['profile_analysis']
            )
            
            print(f"✅ Estimated posts: {estimated_posts}")
            print(f"📝 Rationale: {rationale}")
            print(f"📊 Method: {metrics.get('method', 'unknown')}")
            print(f"🎯 Confidence: {metrics.get('confidence', 'unknown')}")
            
        except Exception as e:
            print(f"❌ Error in scenario '{scenario['name']}': {e}")
    
    # Test hashtag recommendations
    print(f"\n🏷️ Testing hashtag recommendations...")
    try:
        hashtags = estimator.get_hashtag_recommendations(
            content_themes=['beauty', 'lifestyle'],
            platform='instagram',
            engagement_goal='increase',
            follower_count=5000
        )
        print(f"✅ Recommended hashtags: {hashtags}")
    except Exception as e:
        print(f"❌ Error in hashtag recommendations: {e}")
    
    print("\n✅ XGBoost Post Estimator test completed!")

if __name__ == "__main__":
    test_xgboost_estimator() 