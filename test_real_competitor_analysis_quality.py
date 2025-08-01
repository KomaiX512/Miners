#!/usr/bin/env python3
"""
Real Competitor Analysis Quality Test
===================================

Testing with real usernames to examine the quality of competitor analysis:
- Primary: Appleass (existing data)
- Competitors: nike, redbull, netflix (real existing data)

This will help us identify why the competitor analysis is producing low-quality, generic content.
"""

import logging
import json
import os
from datetime import datetime

# Set up logging to show important info
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Reduce noise from non-critical loggers
logging.getLogger('httpx').setLevel(logging.WARNING)
logging.getLogger('chromadb').setLevel(logging.WARNING)
logging.getLogger('numexpr').setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

def main():
    """Test real competitor analysis quality with existing usernames."""
    
    print("🔍 REAL COMPETITOR ANALYSIS QUALITY TEST")
    print("=" * 50)
    print("Primary: Appleass (existing data)")
    print("Competitors: nike, redbull, netflix (real data)")
    print("Platform: facebook")
    print("=" * 50)
    
    try:
        from main import ContentRecommendationSystem
        
        # Initialize the system
        logger.info("Initializing Content Recommendation System...")
        system = ContentRecommendationSystem()
        
        # Test with real existing usernames
        primary_username = "Appleass"
        competitors = ["nike", "redbull", "netflix"]
        platform = "facebook"
        
        print(f"\n🧪 Testing competitor analysis quality...")
        print(f"Primary: {primary_username}")
        print(f"Competitors: {competitors}")
        print(f"Platform: {platform}")
        
        # Create account info structure
        account_info = {
            'accountType': 'business',
            'postingStyle': 'professional tech content focused on innovative products and user experience',
            'competitors': competitors,
            'username': primary_username,
            'platform': platform
        }
        
        # Store account info temporarily
        account_info_path = f"ProfileInfo/{platform}/{primary_username}/profileinfo.json"
        try:
            system.r2_storage.put_object(account_info_path, account_info, bucket='tasks')
            logger.info(f"Created account info for {primary_username}")
        except Exception as e:
            logger.warning(f"Could not create account info: {str(e)}")
        
        # Test the process_social_data method
        data_key = f"{platform}/{primary_username}/{primary_username}.json"
        
        print(f"\n📊 Processing social data for {primary_username}...")
        result = system.process_social_data(data_key)
        
        # Clean up account info
        try:
            if hasattr(system.r2_storage, 'delete_object'):
                system.r2_storage.delete_object(account_info_path, bucket='tasks')
        except:
            pass
        
        if result is None:
            print("❌ No result returned from process_social_data")
            return False
        
        print(f"✅ Successfully processed data")
        print(f"Posts found: {len(result.get('posts', []))}")
        print(f"Competitors: {result.get('secondary_usernames', [])}")
        
        # Now test competitor data collection specifically
        print(f"\n🔍 Testing competitor data collection...")
        competitor_data = system._collect_available_competitor_data(competitors, platform)
        
        print(f"Competitors with data: {len(competitor_data) if competitor_data else 0}")
        if competitor_data:
            for comp_name, comp_posts in competitor_data.items():
                print(f"  - {comp_name}: {len(comp_posts)} posts")
        
        # Test content plan generation (this includes competitor analysis)
        print(f"\n📋 Generating content plan with competitor analysis...")
        try:
            content_plan = system.generate_content_plan(result)
            
            # Examine competitor analysis quality
            print(f"\n🔍 COMPETITOR ANALYSIS QUALITY EXAMINATION:")
            print("=" * 60)
            
            if 'competitor_analysis' in content_plan:
                comp_analysis = content_plan['competitor_analysis']
                print(f"Found competitor analysis for {len(comp_analysis)} competitors")
                
                for comp_name, analysis in comp_analysis.items():
                    print(f"\n📊 Analysis for {comp_name}:")
                    print("-" * 40)
                    
                    if isinstance(analysis, dict):
                        # Check for quality indicators
                        strengths = analysis.get('strengths', {})
                        vulnerabilities = analysis.get('vulnerabilities', {})
                        strategies = analysis.get('recommended_counter_strategies', [])
                        
                        print(f"Strengths: {strengths}")
                        print(f"Vulnerabilities: {vulnerabilities}")
                        print(f"Strategies: {len(strategies) if isinstance(strategies, list) else 'N/A'}")
                        
                        # Check for generic/template content
                        analysis_text = str(analysis).lower()
                        quality_issues = []
                        
                        if 'rag_extraction' in analysis_text:
                            quality_issues.append("Contains RAG extraction placeholder")
                        if 'market intelligence reveals' in analysis_text:
                            quality_issues.append("Generic template language")
                        if 'strategic differentiation' in analysis_text:
                            quality_issues.append("Vague strategic language")
                        if len(str(analysis)) < 200:
                            quality_issues.append("Analysis too short/shallow")
                        
                        if quality_issues:
                            print(f"❌ QUALITY ISSUES: {quality_issues}")
                        else:
                            print(f"✅ Analysis appears substantive")
                    else:
                        print(f"❌ Analysis is not a dictionary: {type(analysis)}")
            else:
                print("❌ NO COMPETITOR ANALYSIS FOUND in content plan")
            
            # Examine recommendation quality
            print(f"\n🔍 RECOMMENDATION QUALITY EXAMINATION:")
            print("=" * 60)
            
            if 'recommendation' in content_plan:
                recommendation = content_plan['recommendation']
                rec_text = str(recommendation).lower()
                
                print(f"Recommendation length: {len(str(recommendation))} characters")
                
                # Check for quality issues
                rec_quality_issues = []
                if 'replicate peak performance' in rec_text:
                    rec_quality_issues.append("Generic peak performance language")
                if 'market dominance blueprint' in rec_text:
                    rec_quality_issues.append("Buzzword-heavy language")
                if '20%+ higher' in rec_text:
                    rec_quality_issues.append("Fake/arbitrary statistics")
                if 'engagement rate' in rec_text and 'competitor inactive periods' in rec_text:
                    rec_quality_issues.append("Generic timing advice")
                
                if rec_quality_issues:
                    print(f"❌ RECOMMENDATION QUALITY ISSUES: {rec_quality_issues}")
                else:
                    print(f"✅ Recommendations appear specific")
                    
                # Show first 500 chars of recommendation
                print(f"\nSample recommendation text:")
                print(f"'{str(recommendation)[:500]}...'")
            else:
                print("❌ NO RECOMMENDATION FOUND in content plan")
            
            return True
            
        except Exception as e:
            print(f"❌ Content plan generation failed: {str(e)}")
            return False
        
    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
        print(f"❌ TEST FAILED: {str(e)}")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
