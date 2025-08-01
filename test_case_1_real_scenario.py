#!/usr/bin/env python3

"""
REAL CASE 1 TEST: Zero Primary Data + Real Competitor Data
==========================================================

Testing the exact scenario you described:
- Primary: Appleass (no data in R2)
- Competitors: nike, redbull, netflix (data EXISTS in R2 bucket)

The system SHOULD:
1. Detect zero data for primary user
2. Retrieve REAL competitor data from R2
3. Generate QUALITY competitor analysis from real data
4. NOT fall back to generic templates

If it fails, we'll identify the exact limitation in zero post handler.
"""

import sys
import logging
import json
import os
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_case_1_zero_primary_real_competitors():
    """
    Test Case 1: Zero primary data + real competitor data
    """
    
    logger.info("🎯 TESTING CASE 1: ZERO PRIMARY + REAL COMPETITORS")
    logger.info("=" * 60)
    logger.info("Primary: Appleass (no data)")
    logger.info("Competitors: nike, redbull, netflix (data exists)")
    logger.info("Expected: Quality competitor analysis from real data")
    logger.info("=" * 60)
    
    try:
        # Import the main system
        sys.path.append('/home/komail/Miners-1')
        from main import ContentRecommendationSystem
        
        # Initialize the system
        system = ContentRecommendationSystem()
        
        # Test parameters - EXACT scenario you described
        primary_username = "Appleass"  # No data (typo username)
        competitors = ["nike", "redbull", "netflix"]  # Real data exists
        platform = "facebook"  # Where competitor data actually exists
        
        logger.info(f"🧪 Testing: {primary_username} vs {competitors} on {platform}")
        
        # STEP 1: Verify primary has no data
        logger.info("\n📊 STEP 1: Verifying primary user has no data")
        try:
            primary_data = system.data_retriever.get_social_media_data(primary_username, platform=platform)
            if primary_data:
                logger.warning(f"⚠️ {primary_username}: Found {len(primary_data)} posts (should be zero)")
            else:
                logger.info(f"✅ {primary_username}: No data found (as expected)")
        except Exception as e:
            logger.info(f"✅ {primary_username}: No data accessible - {str(e)}")
        
        # STEP 2: Verify competitors have data
        logger.info("\n📊 STEP 2: Verifying competitors have real data")
        competitor_data_available = {}
        total_competitor_posts = 0
        
        for competitor in competitors:
            try:
                comp_data = system.data_retriever.get_social_media_data(competitor, platform=platform)
                if comp_data:
                    if isinstance(comp_data, list):
                        post_count = len(comp_data)
                    elif isinstance(comp_data, dict) and 'posts' in comp_data:
                        post_count = len(comp_data['posts'])
                    else:
                        post_count = 1  # Some data format
                    
                    competitor_data_available[competitor] = post_count
                    total_competitor_posts += post_count
                    logger.info(f"✅ {competitor}: {post_count} posts available")
                else:
                    logger.warning(f"❌ {competitor}: No data found")
                    competitor_data_available[competitor] = 0
            except Exception as e:
                logger.error(f"❌ {competitor}: Error retrieving data - {str(e)}")
                competitor_data_available[competitor] = 0
        
        logger.info(f"📊 Total competitor posts available: {total_competitor_posts}")
        
        if total_competitor_posts == 0:
            logger.error("❌ CRITICAL: No competitor data found - test cannot proceed")
            return False
        
        # STEP 3: Test content plan generation with zero primary + real competitors
        logger.info("\n🎯 STEP 3: Testing content plan generation")
        
        try:
            # This should trigger zero data handler with competitor analysis
            content_plan = system.generate_content_plan(
                data={
                    'posts': [],  # Zero primary posts
                    'engagement_history': [],
                    'profile': {
                        'username': primary_username,
                        'account_type': 'personal',
                        'posting_style': 'informational'
                    },
                    'account_type': 'personal',
                    'posting_style': 'informational',
                    'primary_username': primary_username,
                    'secondary_usernames': competitors,
                    'platform': platform
                }
            )
            
            if content_plan:
                logger.info("✅ Content plan generation successful")
                
                # STEP 4: Analyze quality of competitor analysis
                logger.info("\n📊 STEP 4: Analyzing competitor analysis quality")
                
                # Extract competitor analysis
                competitor_analysis = None
                
                if isinstance(content_plan, dict):
                    # Look for competitor analysis in various locations
                    for key, value in content_plan.items():
                        if 'competitor' in key.lower():
                            competitor_analysis = value
                            logger.info(f"Found competitor analysis in '{key}'")
                            # Prefer the detailed analysis over the simple list
                            if key == 'competitor_analysis' and isinstance(value, dict):
                                break
                            elif key == 'competitors' and isinstance(value, list):
                                continue  # Keep looking for better analysis
                
                if competitor_analysis:
                    analysis_str = json.dumps(competitor_analysis, indent=2) if isinstance(competitor_analysis, dict) else str(competitor_analysis)
                    
                    # Check for real competitor mentions
                    competitor_mentions = 0
                    for comp in competitors:
                        if comp.lower() in analysis_str.lower():
                            competitor_mentions += 1
                    
                    # Check for quality indicators (real analysis)
                    quality_indicators = [
                        "engagement", "strategy", "content", "performance",
                        "brand", "audience", "posting", "frequency",
                        "growth", "competition", "market", "insights"
                    ]
                    
                    quality_score = sum(1 for indicator in quality_indicators if indicator in analysis_str.lower())
                    
                    # Check for generic/template indicators (what we want to avoid)
                    generic_indicators = [
                        "lorem ipsum", "placeholder", "template", "sample",
                        "example", "generic", "insert", "add your",
                        "customize", "bullshit", "corporate speak"
                    ]
                    
                    generic_score = sum(1 for indicator in generic_indicators if indicator in analysis_str.lower())
                    
                    logger.info(f"📊 Competitor mentions: {competitor_mentions}/{len(competitors)}")
                    logger.info(f"📊 Quality indicators: {quality_score}")
                    logger.info(f"📊 Generic indicators: {generic_score}")
                    
                    # Show sample of analysis
                    sample = analysis_str[:500] + "..." if len(analysis_str) > 500 else analysis_str
                    logger.info(f"📝 Analysis sample:\n{sample}")
                    
                    # Determine quality
                    if competitor_mentions >= 2 and quality_score >= 5 and generic_score == 0:
                        logger.info("✅ HIGH QUALITY: Real competitor analysis generated")
                        step4_success = True
                    elif competitor_mentions >= 1 and quality_score >= 3:
                        logger.warning("⚠️ MEDIUM QUALITY: Some real analysis but could be better")
                        step4_success = True
                    else:
                        logger.error("❌ LOW QUALITY: Generic/template content detected")
                        step4_success = False
                else:
                    logger.error("❌ No competitor analysis found in content plan")
                    step4_success = False
                    
                    # Show what's in the content plan
                    if isinstance(content_plan, dict):
                        logger.info(f"Content plan sections: {list(content_plan.keys())}")
                        for key, value in content_plan.items():
                            if isinstance(value, (dict, list)):
                                logger.info(f"  {key}: {type(value)} with {len(value)} items")
                            else:
                                preview = str(value)[:100] + "..." if len(str(value)) > 100 else str(value)
                                logger.info(f"  {key}: {preview}")
                
            else:
                logger.error("❌ Content plan generation failed")
                step4_success = False
                
        except Exception as e:
            logger.error(f"❌ Content plan generation failed: {str(e)}")
            import traceback
            traceback.print_exc()
            step4_success = False
        
        # FINAL SUMMARY
        logger.info("\n" + "=" * 60)
        logger.info("🎯 CASE 1 TEST SUMMARY:")
        logger.info(f"   Primary Data: ❌ (as expected)")
        logger.info(f"   Competitor Data: {'✅' if total_competitor_posts > 0 else '❌'}")
        logger.info(f"   Content Generation: {'✅' if 'content_plan' in locals() and content_plan else '❌'}")
        logger.info(f"   Analysis Quality: {'✅' if step4_success else '❌'}")
        
        overall_success = total_competitor_posts > 0 and step4_success
        
        if overall_success:
            logger.info("🎉 CASE 1 SUCCESS: Zero primary + real competitors = quality analysis!")
            return True
        else:
            logger.error("💥 CASE 1 FAILURE: Zero data handler limitation identified")
            
            # Provide specific diagnosis
            if total_competitor_posts == 0:
                logger.error("💡 Issue: No competitor data retrieved from R2")
            elif not step4_success:
                logger.error("💡 Issue: Poor quality analysis despite available data")
                
            return False
            
    except Exception as e:
        logger.error(f"❌ Test failed with exception: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """
    Main function to run Case 1 test.
    """
    
    logger.info("🚀 CASE 1 TEST: ZERO PRIMARY + REAL COMPETITORS")
    logger.info("Testing the exact scenario you described...")
    logger.info("")
    
    success = test_case_1_zero_primary_real_competitors()
    
    if success:
        logger.info("\n🎊 SUCCESS: Case 1 works correctly!")
        logger.info("Zero primary data + real competitor data = quality analysis")
        return 0
    else:
        logger.error("\n💥 FAILURE: Case 1 has limitations!")
        logger.error("Zero data handler needs improvement for competitor analysis")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
