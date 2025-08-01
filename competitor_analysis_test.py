#!/usr/bin/env python3
"""
Full Pipeline Simulation for Competitor Analysis Validation
Primary: gdb
Competitors: ylecun, geoffreyhinton, sama
Platform: Twitter
"""

import sys
import os
import json
import logging
from datetime import datetime

# Add the main directory to path
sys.path.append('/home/komail/Miners-1')

# Import the main pipeline class
from main import ContentRecommendationSystem

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def simulate_full_pipeline():
    """
    Simulate full pipeline with existing data:
    Primary: gdb
    Competitors: ylecun, geoffreyhinton, sama
    Platform: Twitter
    """
    
    print("=" * 80)
    print("COMPETITOR ANALYSIS PIPELINE SIMULATION")
    print("=" * 80)
    print(f"Primary Username: gdb")
    print(f"Competitors: ylecun, geoffreyhinton, sama")
    print(f"Platform: Twitter")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print("=" * 80)
    
    try:
        # Initialize the system
        system = ContentRecommendationSystem()
        
        # Create mock processed data structure with competitors
        mock_processed_data = {
            'primary_username': 'gdb',
            'platform': 'twitter',
            'account_type': 'branding',
            'posting_style': 'technical_ai_research',
            'posts': [],  # We'll use existing vector database data
            'competitor_posts': [],  # We'll use existing vector database data
            'secondary_usernames': ['ylecun', 'geoffreyhinton', 'sama'],  # CRITICAL: This is what was missing!
            'competitors': ['ylecun', 'geoffreyhinton', 'sama']
        }
        
        # Simulate some posts data for the primary user
        for i in range(10):
            mock_processed_data['posts'].append({
                'id': f'gdb_post_{i}',
                'username': 'gdb',
                'caption': f'AI research update #{i}: Working on transformer architectures and their applications.',
                'hashtags': ['#AI', '#MachineLearning', '#Research'],
                'engagement': 100 + i * 50,
                'timestamp': datetime.now().isoformat()
            })
        
        # Simulate competitor posts
        competitors = ['ylecun', 'geoffreyhinton', 'sama']
        for competitor in competitors:
            for i in range(5):
                mock_processed_data['competitor_posts'].append({
                    'id': f'{competitor}_post_{i}',
                    'username': competitor,
                    'caption': f'AI insights from {competitor} #{i}: Deep learning progress continues.',
                    'hashtags': ['#DeepLearning', '#AI', '#NeuralNetworks'],
                    'engagement': 200 + i * 30,
                    'timestamp': datetime.now().isoformat(),
                    'is_competitor': True
                })
        
        print(f"📊 Mock Data Created:")
        print(f"   Primary posts: {len(mock_processed_data['posts'])}")
        print(f"   Competitor posts: {len(mock_processed_data['competitor_posts'])}")
        print(f"   Secondary usernames: {mock_processed_data['secondary_usernames']}")
        print("")
        
        # Test the content plan generation directly
        print("🚀 Starting Content Plan Generation...")
        
        # Call the public method that generates content plans
        content_plan = system.generate_content_plan(
            data=mock_processed_data,
            topics=None,
            n_recommendations=3
        )
        
        print("✅ Content Plan Generated!")
        print(f"Content Plan Keys: {list(content_plan.keys())}")
        
        # Check if competitor analysis was generated
        if 'competitor_analysis' in content_plan:
            competitor_analysis = content_plan['competitor_analysis']
            print(f"✅ COMPETITOR ANALYSIS FOUND!")
            print(f"   Competitors analyzed: {list(competitor_analysis.keys())}")
            
            # Validate each competitor
            for competitor in ['ylecun', 'geoffreyhinton', 'sama']:
                if competitor in competitor_analysis:
                    analysis = competitor_analysis[competitor]
                    print(f"   ✅ {competitor}: {len(analysis)} analysis fields")
                    print(f"      Overview: {analysis.get('overview', 'N/A')[:100]}...")
                else:
                    print(f"   ❌ {competitor}: MISSING")
        else:
            print("❌ COMPETITOR ANALYSIS MISSING!")
            print("Available keys:", list(content_plan.keys()))
        
        # Save the content plan for inspection
        with open('/home/komail/Miners-1/competitor_test_content_plan.json', 'w') as f:
            json.dump(content_plan, f, indent=2, default=str)
        
        print(f"📁 Content plan saved to: competitor_test_content_plan.json")
        
        # Test the export functionality
        print("\n🔄 Testing Export Functionality...")
        system.save_content_plan(content_plan)
        print("✅ Content plan saved successfully")
        
        return content_plan
        
    except Exception as e:
        logger.error(f"❌ Pipeline simulation failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    result = simulate_full_pipeline()
    
    if result:
        print("\n" + "=" * 80)
        print("SIMULATION COMPLETE - SUCCESS!")
        print("=" * 80)
        
        # Final validation
        if 'competitor_analysis' in result:
            print(f"✅ Competitor analysis generated for {len(result['competitor_analysis'])} competitors")
        else:
            print("❌ Competitor analysis was NOT generated")
            
        if 'next_post_prediction' in result:
            print("✅ Next post prediction generated")
        
        if 'improvement_recommendations' in result:
            print("✅ Improvement recommendations generated")
            
    else:
        print("\n" + "=" * 80)
        print("SIMULATION FAILED!")
        print("=" * 80)
