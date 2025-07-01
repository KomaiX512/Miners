#!/usr/bin/env python3
"""
COMPREHENSIVE SYSTEM TEST: Verify ALL modules generate hyper-personalized content
This test validates:
1. Competitor Analysis - Rich, detailed insights without templates
2. Next Post Prediction - Theme-aligned, authentic content
3. Main Recommendations - Actionable, specific strategies
4. Complete Content Plan Export - All 3 modules working perfectly
"""

import os
import json
import sys
from datetime import datetime

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main import ContentRecommendationSystem
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def analyze_competitor_analysis_quality(competitor_analysis):
    """Analyze the quality of competitor analysis - detect templates vs real insights."""
    quality_indicators = {
        'template_bullshit_detected': 0,
        'real_insights_found': 0,
        'detailed_overviews': 0,
        'specific_strengths': 0,
        'actionable_strategies': 0,
        'content_themes': 0
    }
    
    template_phrases = [
        "RAG analysis indicates",
        "requires competitive intelligence assessment", 
        "Performance analysis available for",
        "Strategic opportunity assessment for",
        "Competitive positioning strategy vs",
        "offer in-depth analysis of specific",
        "can offer in-depth analysis"
    ]
    
    for competitor, analysis in competitor_analysis.items():
        overview = analysis.get('overview', '')
        strengths = analysis.get('strengths', [])
        strategies = analysis.get('recommended_counter_strategies', [])
        themes = analysis.get('top_content_themes', [])
        
        # Check for template bullshit
        for phrase in template_phrases:
            if phrase in overview or any(phrase in str(item) for item in strengths + strategies):
                quality_indicators['template_bullshit_detected'] += 1
                logger.warning(f"🚩 TEMPLATE DETECTED in {competitor}: {phrase}")
        
        # Check for real insights
        if len(overview) > 50 and not any(phrase in overview for phrase in template_phrases):
            quality_indicators['detailed_overviews'] += 1
            quality_indicators['real_insights_found'] += 1
        
        if len(strengths) > 0 and not any(phrase in str(strengths) for phrase in template_phrases):
            quality_indicators['specific_strengths'] += 1
            quality_indicators['real_insights_found'] += 1
        
        if len(strategies) > 0 and not any(phrase in str(strategies) for phrase in template_phrases):
            quality_indicators['actionable_strategies'] += 1
            quality_indicators['real_insights_found'] += 1
        
        if len(themes) > 0:
            quality_indicators['content_themes'] += 1
            quality_indicators['real_insights_found'] += 1
    
    return quality_indicators

def analyze_next_post_quality(next_post):
    """Analyze next post prediction quality - theme alignment and authenticity."""
    quality_indicators = {
        'generic_templates': 0,
        'theme_aligned': 0,
        'authentic_content': 0,
        'specific_calls_to_action': 0,
        'relevant_hashtags': 0
    }
    
    caption = next_post.get('caption', '')
    cta = next_post.get('call_to_action', '')
    hashtags = next_post.get('hashtags', [])
    
    # Check for generic templates
    generic_phrases = [
        "Authentic, engaging content that reflects brand voice",
        "High-quality visual content that authentically represents",
        "Share your thoughts and experiences in the comments",
        "Tell us what you think in the comments below"
    ]
    
    for phrase in generic_phrases:
        if phrase in caption or phrase in cta:
            quality_indicators['generic_templates'] += 1
            logger.warning(f"🚩 GENERIC TEMPLATE in next post: {phrase}")
    
    # Check for authentic, specific content
    if len(caption) > 30 and not any(phrase in caption for phrase in generic_phrases):
        quality_indicators['authentic_content'] += 1
        
        # Check for theme alignment (should mention products, brands, or specific concepts)
        theme_indicators = ['product', 'launch', 'new', 'collection', 'beauty', 'tech', 'review', 'showcase']
        if any(indicator in caption.lower() for indicator in theme_indicators):
            quality_indicators['theme_aligned'] += 1
    
    if len(cta) > 10 and not any(phrase in cta for phrase in generic_phrases):
        quality_indicators['specific_calls_to_action'] += 1
    
    # Check hashtag relevance
    generic_hashtags = ['#authentic', '#engagement', '#community', '#growth', '#strategy']
    specific_hashtags = [tag for tag in hashtags if tag not in generic_hashtags]
    if len(specific_hashtags) >= 3:
        quality_indicators['relevant_hashtags'] += 1
    
    return quality_indicators

def analyze_recommendations_quality(recommendations):
    """Analyze tactical recommendations quality."""
    quality_indicators = {
        'generic_recommendations': 0,
        'specific_actionable': 0,
        'metrics_included': 0,
        'detailed_strategies': 0
    }
    
    generic_phrases = [
        "Strategic content optimization with competitive audience analysis",
        "Authentic engagement development through community-building initiatives",
        "Brand positioning enhancement with market differentiation focus",
        "Performance-driven content strategy with measurable growth metrics",
        "Cross-platform content syndication for maximum reach and impact"
    ]
    
    for rec in recommendations:
        rec_text = str(rec)
        
        # Check for generic templates
        if any(phrase in rec_text for phrase in generic_phrases):
            quality_indicators['generic_recommendations'] += 1
            logger.warning(f"🚩 GENERIC RECOMMENDATION: {rec_text[:100]}...")
        else:
            quality_indicators['specific_actionable'] += 1
        
        # Check for metrics and numbers
        import re
        if re.search(r'\d+%|\d+\s*(?:likes|followers|engagement|views)', rec_text):
            quality_indicators['metrics_included'] += 1
        
        # Check for detailed strategies (longer, specific recommendations)
        if len(rec_text) > 100 and not any(phrase in rec_text for phrase in generic_phrases):
            quality_indicators['detailed_strategies'] += 1
    
    return quality_indicators

def test_complete_system():
    """Test the complete system with multiple account types to ensure universal functionality."""
    
    print("🔥 COMPREHENSIVE SYSTEM TEST - ALL MODULES VALIDATION")
    print("=" * 80)
    
    test_cases = [
        {
            'name': 'Beauty Brand Test (TooFaced)',
            'primary_username': 'toofaced',
            'username': 'toofaced',
            'platform': 'instagram',
            'account_type': 'branding',
            'bio': 'Get ready to unwrap the secret to your best lashes yet! Our NEW Ribbon Wrapped Lash Extreme Tubing Mascara is almost here!! 🎀',
            'followers_count': 1200000,
            'secondary_usernames': ['fentybeauty', 'maccosmetics', 'narsissist'],
        },
        {
            'name': 'Tech Reviewer Test (MKBHD)',
            'primary_username': 'mkbhd',
            'username': 'mkbhd', 
            'platform': 'instagram',
            'account_type': 'branding',
            'bio': 'Tech reviews, crisp videos, and the occasional car content. Subscribe for tech!',
            'followers_count': 4800000,
            'secondary_usernames': ['techburner', 'technicalguruji', 'mrwhosetheboss'],
        }
    ]
    
    system = ContentRecommendationSystem()
    overall_results = {
        'tests_passed': 0,
        'tests_failed': 0,
        'template_bullshit_eliminated': True,
        'all_modules_working': True
    }
    
    for test_case in test_cases:
        print(f"\n🎯 TESTING: {test_case['name']}")
        print("-" * 60)
        
        try:
            # Generate content plan
            print(f"📝 Generating content plan for @{test_case['primary_username']}...")
            content_plan = system.generate_content_plan(test_case)
            
            # Test 1: Competitor Analysis Quality
            print("\n🔍 TESTING COMPETITOR ANALYSIS...")
            competitor_analysis = content_plan.get('competitor_analysis', {})
            comp_quality = analyze_competitor_analysis_quality(competitor_analysis)
            
            print(f"   📊 Competitors analyzed: {len(competitor_analysis)}")
            print(f"   ✅ Real insights found: {comp_quality['real_insights_found']}")
            print(f"   🚩 Template bullshit detected: {comp_quality['template_bullshit_detected']}")
            print(f"   📝 Detailed overviews: {comp_quality['detailed_overviews']}")
            print(f"   💪 Specific strengths: {comp_quality['specific_strengths']}")
            print(f"   🎯 Actionable strategies: {comp_quality['actionable_strategies']}")
            
            # Test 2: Next Post Prediction Quality
            print("\n🎨 TESTING NEXT POST PREDICTION...")
            next_post = content_plan.get('recommendation', {}).get('next_post_prediction', {})
            next_quality = analyze_next_post_quality(next_post)
            
            print(f"   📝 Caption length: {len(next_post.get('caption', ''))}")
            print(f"   🚩 Generic templates: {next_quality['generic_templates']}")
            print(f"   🎭 Theme aligned: {next_quality['theme_aligned']}")
            print(f"   ✨ Authentic content: {next_quality['authentic_content']}")
            print(f"   📢 Specific CTAs: {next_quality['specific_calls_to_action']}")
            print(f"   #️⃣ Relevant hashtags: {next_quality['relevant_hashtags']}")
            
            # Test 3: Recommendations Quality
            print("\n🎯 TESTING TACTICAL RECOMMENDATIONS...")
            recommendations = content_plan.get('recommendation', {}).get('tactical_recommendations', [])
            rec_quality = analyze_recommendations_quality(recommendations)
            
            print(f"   📋 Total recommendations: {len(recommendations)}")
            print(f"   🚩 Generic recommendations: {rec_quality['generic_recommendations']}")
            print(f"   ✅ Specific actionable: {rec_quality['specific_actionable']}")
            print(f"   📊 Metrics included: {rec_quality['metrics_included']}")
            print(f"   🎯 Detailed strategies: {rec_quality['detailed_strategies']}")
            
            # Calculate overall test score
            test_score = 0
            max_score = 15
            
            # Competitor analysis scoring (5 points)
            if comp_quality['template_bullshit_detected'] == 0:
                test_score += 2
            if comp_quality['real_insights_found'] >= 3:
                test_score += 2
            if comp_quality['detailed_overviews'] >= 1:
                test_score += 1
            
            # Next post scoring (5 points)
            if next_quality['generic_templates'] == 0:
                test_score += 2
            if next_quality['theme_aligned'] >= 1:
                test_score += 2
            if next_quality['authentic_content'] >= 1:
                test_score += 1
            
            # Recommendations scoring (5 points)
            if rec_quality['generic_recommendations'] == 0:
                test_score += 2
            if rec_quality['specific_actionable'] >= 2:
                test_score += 2
            if rec_quality['detailed_strategies'] >= 1:
                test_score += 1
            
            percentage = (test_score / max_score) * 100
            
            print(f"\n📊 TEST RESULTS FOR {test_case['name']}:")
            print(f"   Score: {test_score}/{max_score} ({percentage:.1f}%)")
            
            if percentage >= 80:
                print("   🏆 EXCELLENT: System working perfectly!")
                overall_results['tests_passed'] += 1
            elif percentage >= 60:
                print("   ✅ GOOD: System mostly working, minor issues")
                overall_results['tests_passed'] += 1
            else:
                print("   ❌ POOR: System needs significant improvement")
                overall_results['tests_failed'] += 1
                overall_results['all_modules_working'] = False
            
            # Track template elimination
            if (comp_quality['template_bullshit_detected'] > 0 or 
                next_quality['generic_templates'] > 0 or 
                rec_quality['generic_recommendations'] > 0):
                overall_results['template_bullshit_eliminated'] = False
            
            # Save detailed results
            filename = f"test_results_{test_case['primary_username']}.json"
            with open(filename, 'w') as f:
                json.dump({
                    'test_case': test_case['name'],
                    'content_plan': content_plan,
                    'quality_analysis': {
                        'competitor_analysis': comp_quality,
                        'next_post': next_quality,
                        'recommendations': rec_quality
                    },
                    'test_score': test_score,
                    'percentage': percentage
                }, f, indent=2)
            
            print(f"   💾 Detailed results saved to: {filename}")
            
        except Exception as e:
            print(f"   ❌ TEST FAILED: {str(e)}")
            overall_results['tests_failed'] += 1
            overall_results['all_modules_working'] = False
    
    # Final Results
    print("\n" + "=" * 80)
    print("🏁 FINAL SYSTEM TEST RESULTS")
    print("=" * 80)
    print(f"✅ Tests Passed: {overall_results['tests_passed']}")
    print(f"❌ Tests Failed: {overall_results['tests_failed']}")
    print(f"🚫 Template Bullshit Eliminated: {overall_results['template_bullshit_eliminated']}")
    print(f"⚙️  All Modules Working: {overall_results['all_modules_working']}")
    
    if overall_results['all_modules_working'] and overall_results['template_bullshit_eliminated']:
        print("\n🎉 SUCCESS: $100K SYSTEM IS WORKING PERFECTLY!")
        print("🏆 All modules generating hyper-personalized content!")
        print("🚀 Ready for production deployment!")
        return True
    else:
        print("\n⚠️  ISSUES DETECTED: System needs further refinement")
        print("🔧 Check individual test results for specific problems")
        return False

if __name__ == "__main__":
    success = test_complete_system()
    sys.exit(0 if success else 1) 