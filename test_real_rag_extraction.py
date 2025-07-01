#!/usr/bin/env python3
"""
CRITICAL TEST: Verify that our $100k RAG system now generates REAL hyper-personalized content
This will test if the complete overhaul of _force_rag_reconstruction eliminates all template bullshit
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

def analyze_content_quality(content_plan):
    """Analyze if content is hyper-personalized vs generic template bullshit."""
    
    quality_score = 0
    total_checks = 0
    issues = []
    
    print("\n🔍 HYPER-PERSONALIZATION QUALITY ANALYSIS:")
    print("=" * 60)
    
    # Check 1: Template Bullshit Detection
    template_bullshit = [
        "Strategic positioning for",
        "competitive advantage",
        "Engaging content optimized for maximum",
        "authentic engagement",
        "Share your thoughts and engage",
        "High-quality, engaging visual optimized",
        "platform engagement",
        "with strategic insights for",
        "optimization",
        "enhancement strategies"
    ]
    
    content_str = json.dumps(content_plan, indent=2).lower()
    bullshit_detected = []
    
    for bullshit in template_bullshit:
        if bullshit.lower() in content_str:
            bullshit_detected.append(bullshit)
    
    if bullshit_detected:
        print(f"❌ TEMPLATE BULLSHIT DETECTED: {len(bullshit_detected)} instances")
        for bs in bullshit_detected:
            print(f"   🚩 '{bs}'")
        issues.append(f"Template bullshit detected: {len(bullshit_detected)} instances")
    else:
        print("✅ NO TEMPLATE BULLSHIT DETECTED")
        quality_score += 20
    
    total_checks += 20
    
    # Check 2: Real Product/Brand Mentions
    real_indicators = [
        "mascara", "foundation", "lipstick", "collection", "campaign", "launch",
        "sale", "contest", "challenge", "@", "#", "ribbon wrapped", "studio fix",
        "gloss bomb", "fenty", "mac", "tarte", "nars", "toofaced", "friends & family",
        "tubing mascara", "universal lip", "luminizer", "james charles"
    ]
    
    real_mentions = []
    for indicator in real_indicators:
        if indicator.lower() in content_str:
            real_mentions.append(indicator)
    
    if len(real_mentions) >= 5:
        print(f"✅ REAL BRAND/PRODUCT MENTIONS: {len(real_mentions)} found")
        quality_score += 20
    else:
        print(f"❌ INSUFFICIENT REAL MENTIONS: Only {len(real_mentions)} found")
        issues.append(f"Insufficient real brand/product mentions: {len(real_mentions)}")
    
    total_checks += 20
    
    # Check 3: Numerical Data/Metrics
    import re
    metrics = re.findall(r'\d+(?:,\d+)*', content_str)
    percentages = re.findall(r'\d+%', content_str)
    
    total_metrics = len(metrics) + len(percentages)
    
    if total_metrics >= 3:
        print(f"✅ NUMERICAL METRICS FOUND: {total_metrics} metrics/numbers")
        quality_score += 15
    else:
        print(f"❌ INSUFFICIENT METRICS: Only {total_metrics} found")
        issues.append(f"Insufficient numerical data: {total_metrics}")
    
    total_checks += 15
    
    # Check 4: Competitor Analysis Quality
    if 'competitor_analysis' in content_plan:
        comp_analysis = content_plan['competitor_analysis']
        
        # Check for meaningful competitor insights
        comp_quality = 0
        for competitor, data in comp_analysis.items():
            if isinstance(data, dict):
                overview = data.get('overview', '')
                strengths = data.get('strengths', [])
                
                # Check if overview contains real insights vs templates
                if len(overview) > 100 and not any(bs.lower() in overview.lower() for bs in template_bullshit):
                    comp_quality += 1
                
                # Check if strengths are meaningful
                if isinstance(strengths, list) and len(strengths) > 0:
                    meaningful_strengths = [s for s in strengths if len(s) > 50 and not any(bs.lower() in s.lower() for bs in template_bullshit)]
                    if meaningful_strengths:
                        comp_quality += 1
        
        if comp_quality >= 4:  # At least 2 competitors with good insights
            print(f"✅ QUALITY COMPETITOR ANALYSIS: {comp_quality}/6 quality indicators")
            quality_score += 20
        else:
            print(f"❌ POOR COMPETITOR ANALYSIS: Only {comp_quality}/6 quality indicators")
            issues.append(f"Poor competitor analysis quality: {comp_quality}/6")
    else:
        print("❌ NO COMPETITOR ANALYSIS FOUND")
        issues.append("No competitor analysis found")
    
    total_checks += 20
    
    # Check 5: Content Originality and Specificity
    if 'recommendation' in content_plan:
        rec = content_plan['recommendation']
        
        if 'next_post_prediction' in rec:
            next_post = rec['next_post_prediction']
            caption = next_post.get('caption', '')
            
            if len(caption) > 50 and not any(bs.lower() in caption.lower() for bs in template_bullshit):
                print("✅ ORIGINAL NEXT POST CONTENT")
                quality_score += 15
            else:
                print("❌ GENERIC/TEMPLATE NEXT POST CONTENT")
                issues.append("Generic next post content")
        
        if 'tactical_recommendations' in rec:
            recs = rec['tactical_recommendations']
            if isinstance(recs, list):
                original_recs = [r for r in recs if len(r) > 30 and not any(bs.lower() in r.lower() for bs in template_bullshit)]
                
                if len(original_recs) >= 3:
                    print(f"✅ ORIGINAL RECOMMENDATIONS: {len(original_recs)} quality recommendations")
                    quality_score += 10
                else:
                    print(f"❌ GENERIC RECOMMENDATIONS: Only {len(original_recs)} original recommendations")
                    issues.append(f"Generic recommendations: {len(original_recs)}")
    
    total_checks += 25
    
    # Calculate final score
    percentage_score = (quality_score / total_checks) * 100
    
    print(f"\n📊 FINAL QUALITY SCORE: {percentage_score:.1f}% ({quality_score}/{total_checks})")
    
    if percentage_score >= 80:
        print("🏆 EXCELLENT: True hyper-personalized content!")
        return True, percentage_score, []
    elif percentage_score >= 60:
        print("⚠️ ACCEPTABLE: Good content with some template elements")
        return True, percentage_score, issues
    else:
        print("💥 FAILURE: Still too much template bullshit!")
        return False, percentage_score, issues

def test_real_rag_extraction():
    """Test if the completely overhauled RAG extraction works."""
    
    print("🎯 TESTING REAL RAG EXTRACTION - $100K SYSTEM VALIDATION")
    print("=" * 70)
    
    try:
        # Create system
        system = ContentRecommendationSystem()
        
        # Test data for TooFaced beauty brand - FIXED DATA STRUCTURE
        test_data = {
            'primary_username': 'toofaced',  # FIXED: Use primary_username instead of username
            'username': 'toofaced',          # Also include username for compatibility
            'platform': 'instagram',
            'account_type': 'branding',
            'bio': 'Get ready to unwrap the secret to your best lashes yet! Our NEW Ribbon Wrapped Lash Extreme Tubing Mascara is almost here!! 🎀',
            'followers_count': 1200000,
            'secondary_usernames': ['fentybeauty', 'maccosmetics', 'narsissist'],  # FIXED: Add competitor usernames
            'posts': [
                {
                    'caption': 'Get ready to unwrap the secret to your best lashes yet! 😍 Our NEW Ribbon Wrapped Lash Extreme Tubing Mascara is almost here!! 🎀 #TooFacedWrappedMasterpiece',
                    'engagement': 8300,
                    'likes': 7600,
                    'comments': 700,
                    'username': 'toofaced',  # IMPORTANT: Add username to posts
                    'timestamp': datetime.now().isoformat()
                },
                {
                    'caption': '🎉 Friends & Family Sale happening NOW! Get 20% off everything including our cult-favorite Better Than Sex Mascara 💕 #TooFaced #BetterThanSex',
                    'engagement': 5200,
                    'likes': 4800,
                    'comments': 400,
                    'username': 'toofaced',  # IMPORTANT: Add username to posts
                    'timestamp': datetime.now().isoformat()
                },
                {
                    'caption': '✨ NEW DROP ALERT ✨ Born This Way Super Coverage Multi-Use Sculpting Concealer is HERE! Full coverage that feels weightless 💫 #BornThisWay #TooFaced',
                    'engagement': 6700,
                    'likes': 6200,
                    'comments': 500,
                    'username': 'toofaced',  # IMPORTANT: Add username to posts
                    'timestamp': datetime.now().isoformat()
                }
            ],
            'profile': {  # ADD PROFILE DATA that system expects
                'username': 'toofaced',
                'fullName': 'Too Faced',
                'biography': 'Get ready to unwrap the secret to your best lashes yet! Our NEW Ribbon Wrapped Lash Extreme Tubing Mascara is almost here!! 🎀',
                'followersCount': 1200000,
                'isBusinessAccount': True,
                'businessCategoryName': 'Beauty & Personal Care',
                'verified': True
            }
        }
        
        # Remove the competitors list since we're using secondary_usernames in data
        # competitors = [
        #     {'username': 'fentybeauty', 'account_type': 'branding'},
        #     {'username': 'maccosmetics', 'account_type': 'branding'},
        #     {'username': 'narsissist', 'account_type': 'branding'}
        # ]
        
        print("🎨 Generating content plan with REAL RAG extraction...")
        print("⏳ Testing if we get hyper-personalized content...")
        
        # Generate content plan
        content_plan = system.generate_content_plan(
            test_data,
            topics=['beauty', 'makeup', 'cosmetics', 'mascara'],
            n_recommendations=5
        )
        
        print(f"\n✅ Content plan generated successfully!")
        
        # Analyze content quality
        is_quality, score, issues = analyze_content_quality(content_plan)
        
        if is_quality and score >= 80:
            print(f"\n🎉 SUCCESS! RAG extraction is working perfectly!")
            print(f"💯 Quality Score: {score:.1f}%")
            print("🏆 The system is generating hyper-personalized content!")
            
            # Save the quality content for inspection
            with open('quality_content_plan.json', 'w') as f:
                json.dump(content_plan, f, indent=2)
            print("📄 Quality content saved to 'quality_content_plan.json'")
            
            return True
        else:
            print(f"\n💥 FAILURE! RAG extraction still has issues!")
            print(f"📊 Quality Score: {score:.1f}%")
            print("🚩 Issues found:")
            for issue in issues:
                print(f"   - {issue}")
            
            # Save the problematic content for debugging
            with open('problematic_content_plan.json', 'w') as f:
                json.dump(content_plan, f, indent=2)
            print("📄 Problematic content saved to 'problematic_content_plan.json'")
            
            return False
            
    except Exception as e:
        print(f"💥 ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_real_rag_extraction()
    
    if success:
        print("\n🎯 MISSION ACCOMPLISHED! The $100k RAG system is working!")
    else:
        print("\n💥 MISSION FAILED! More debugging needed!")
    
    exit(0 if success else 1) 