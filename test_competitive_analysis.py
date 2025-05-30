#!/usr/bin/env python3
"""Test script to verify enhanced competitor analysis with vulnerabilities and counter strategies."""

import json
import logging
from main import ContentRecommendationSystem

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_competitor_analysis():
    """Test the enhanced competitor analysis functionality."""
    try:
        logger.info("🔬 TESTING ENHANCED COMPETITOR ANALYSIS")
        system = ContentRecommendationSystem()
        
        # Create test data with multiple competitors
        test_data = {
            'posts': [
                {
                    'id': '1',
                    'caption': 'Amazing breakthrough in AI technology! 🚀',
                    'hashtags': ['#AI', '#Technology'],
                    'engagement': 1500,
                    'likes': 1200,
                    'comments': 300,
                    'timestamp': '2025-01-15T10:00:00Z',
                    'username': 'gdb'
                },
                {
                    'id': '2', 
                    'caption': 'Building the future of human-AI collaboration',
                    'hashtags': ['#AI', '#Future'],
                    'engagement': 2200,
                    'likes': 1800,
                    'comments': 400,
                    'timestamp': '2025-01-16T14:00:00Z',
                    'username': 'gdb'
                }
            ],
            'engagement_history': [
                {'timestamp': '2025-01-15T10:00:00Z', 'engagement': 1500},
                {'timestamp': '2025-01-16T14:00:00Z', 'engagement': 2200}
            ],
            'profile': {
                'username': 'gdb',
                'fullName': 'Test User',
                'followersCount': 50000,
                'followsCount': 1000,
                'postsCount': 150,
                'biography': 'AI researcher and technology enthusiast',
                'verified': False,
                'private': False,
                'account_type': 'branding',
                'posting_style': 'posting about OPEN AI'
            },
            'account_type': 'branding',
            'posting_style': 'posting about OPEN AI',
            'primary_username': 'gdb',
            'secondary_usernames': ['elonmusk', 'sama', 'demishassabis'],
            'platform': 'twitter'
        }
        
        logger.info("📊 Running content plan generation with test data...")
        
        # Run the complete pipeline
        result = system.run_pipeline(data=test_data)
        
        if result and result.get('success'):
            logger.info("✅ Pipeline completed successfully")
            
            # Check if content plan was generated
            if 'content_plan' in result:
                content_plan = result['content_plan']
                
                # Check competitor analysis section
                if 'competitor_analysis' in content_plan:
                    competitor_analysis = content_plan['competitor_analysis']
                    logger.info(f"🔍 Found competitor analysis for {len(competitor_analysis)} competitors")
                    
                    # Check each competitor for vulnerabilities and counter strategies
                    for competitor_name, analysis in competitor_analysis.items():
                        logger.info(f"\n📊 COMPETITOR: {competitor_name}")
                        
                        vulnerabilities = analysis.get('exploitable_vulnerabilities', [])
                        counter_strategies = analysis.get('recommended_counter_strategies', [])
                        
                        logger.info(f"   Vulnerabilities: {len(vulnerabilities)} found")
                        for i, vuln in enumerate(vulnerabilities[:3], 1):
                            logger.info(f"     {i}. {vuln}")
                        
                        logger.info(f"   Counter Strategies: {len(counter_strategies)} found")
                        for i, strategy in enumerate(counter_strategies[:3], 1):
                            logger.info(f"     {i}. {strategy}")
                        
                        # Test if fields are properly populated
                        if not vulnerabilities:
                            logger.warning(f"❌ NO VULNERABILITIES found for {competitor_name}")
                        else:
                            logger.info(f"✅ Vulnerabilities properly populated for {competitor_name}")
                            
                        if not counter_strategies:
                            logger.warning(f"❌ NO COUNTER STRATEGIES found for {competitor_name}")
                        else:
                            logger.info(f"✅ Counter strategies properly populated for {competitor_name}")
                    
                    # Summary
                    total_competitors = len(competitor_analysis)
                    competitors_with_vulns = len([c for c in competitor_analysis.values() if c.get('exploitable_vulnerabilities')])
                    competitors_with_strategies = len([c for c in competitor_analysis.values() if c.get('recommended_counter_strategies')])
                    
                    logger.info(f"\n📈 COMPETITIVE ANALYSIS SUMMARY:")
                    logger.info(f"   Total competitors analyzed: {total_competitors}")
                    logger.info(f"   Competitors with vulnerabilities: {competitors_with_vulns}/{total_competitors}")
                    logger.info(f"   Competitors with counter strategies: {competitors_with_strategies}/{total_competitors}")
                    
                    if competitors_with_vulns == total_competitors and competitors_with_strategies == total_competitors:
                        logger.info("🎯 SUCCESS: All competitors have comprehensive competitive analysis!")
                        return True
                    else:
                        logger.error("❌ FAILURE: Some competitors missing vulnerability/strategy analysis")
                        return False
                        
                else:
                    logger.error("❌ No competitor_analysis section found in content plan")
                    return False
            else:
                logger.error("❌ No content_plan found in result")
                return False
        else:
            logger.error(f"❌ Pipeline failed: {result}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Test failed with error: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    print("🔬 ENHANCED COMPETITOR ANALYSIS TEST")
    print("="*50)
    
    success = test_competitor_analysis()
    
    print("\n" + "="*50)
    if success:
        print("🎉 TEST PASSED: Enhanced competitor analysis working correctly!")
        print("✅ Vulnerabilities and counter strategies are now properly populated")
    else:
        print("❌ TEST FAILED: Issues detected in competitor analysis")
        print("⚠️  Check the logs above for specific problems")
    
    print("="*50) 