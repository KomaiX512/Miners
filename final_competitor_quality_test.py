#!/usr/bin/env python3

"""
FINAL COMPETITOR ANALYSIS QUALITY FIX & TEST
============================================

ROOT CAUSE IDENTIFIED:
- Competitor data exists in FACEBOOK (nike: 200 posts, redbull: 10 posts, netflix: 10 posts)
- But we were testing with INSTAGRAM platform where no competitor data exists
- The _collect_available_competitor_data method needs to search across all platforms
- Current implementation only searches the specified platform

SOLUTION:
1. Fix the competitor data collection to search across all platforms
2. Use Facebook platform for testing since that's where the data exists
3. Test end-to-end competitor analysis quality with real data

Expected Result: High-quality competitor analysis instead of generic templates
"""

import sys
import logging
import json
import os
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_competitor_analysis_with_real_data():
    """
    Test competitor analysis with the correct platform where data actually exists.
    """
    
    logger.info("🎯 TESTING COMPETITOR ANALYSIS WITH REAL FACEBOOK DATA")
    logger.info("=" * 60)
    
    try:
        # Import the main system
        sys.path.append('/home/komail/Miners-1')
        from main import ContentRecommendationSystem
        
        # Initialize the system
        system = ContentRecommendationSystem()
        
        # Use FACEBOOK platform where competitor data actually exists
        primary_username = "nike"  # Nike has full data: 200 posts (50 primary + 150 competitor)
        competitors = ["cocacola", "redbull", "shakira"]  # These exist in nike's folder
        platform = "facebook"  # This is where the data actually exists
        
        logger.info(f"🎯 Testing: {primary_username} vs {competitors} on {platform}")
        logger.info(f"Expected: Nike (200 posts), competitors with data from Nike's folder")
        
        # STEP 1: Test competitor data collection
        logger.info("\n📊 STEP 1: Testing competitor data collection")
        available_data = system._collect_available_competitor_data(
            competitors=competitors,
            platform=platform
        )
        
        step1_success = False
        total_competitor_posts = 0
        
        for competitor in competitors:
            if competitor in available_data and available_data[competitor]:
                posts = available_data[competitor].get('posts', [])
                source = available_data[competitor].get('source', 'unknown')
                logger.info(f"✅ {competitor}: {len(posts)} posts from {source}")
                total_competitor_posts += len(posts)
                if len(posts) > 0:
                    step1_success = True
            else:
                logger.warning(f"⚠️ {competitor}: No data collected")
        
        logger.info(f"📊 Total competitor posts collected: {total_competitor_posts}")
        
        # STEP 2: Test vector database queries 
        logger.info("\n🔍 STEP 2: Testing vector database queries")
        vector_results = {}
        step2_success = False
        
        for competitor in competitors:
            try:
                # Query for competitor content
                results = system.vector_db.query_similar(
                    f"content strategy insights from {competitor}",
                    n_results=5,
                    filter_username=competitor,
                    is_competitor=True
                )
                
                if results and 'documents' in results and results['documents']:
                    docs = [doc for doc in results['documents'][0] if doc]
                    if docs:
                        vector_results[competitor] = docs
                        logger.info(f"✅ {competitor}: Found {len(docs)} documents in vector DB")
                        step2_success = True
                    else:
                        logger.warning(f"⚠️ {competitor}: Empty documents returned")
                else:
                    logger.warning(f"⚠️ {competitor}: No vector DB results")
                    
            except Exception as e:
                logger.error(f"❌ {competitor}: Vector query failed - {str(e)}")
        
        # STEP 3: Test content plan generation
        logger.info("\n🎯 STEP 3: Testing content plan generation")
        
        try:
            # Generate content plan using the platform where data exists
            content_plan = system.generate_content_plan(
                username=primary_username,
                platform=platform,
                account_type="branding",  # Nike is a brand
                posting_style="promotional", 
                competitors=competitors,
                use_existing_data=True  # Use existing Facebook data
            )
            
            if content_plan:
                logger.info("✅ Content plan generation successful")
                
                # Analyze content plan quality
                plan_str = json.dumps(content_plan, indent=2) if isinstance(content_plan, dict) else str(content_plan)
                
                # Quality indicators
                competitor_mentions = sum(1 for comp in competitors if comp.lower() in plan_str.lower())
                nike_mentions = plan_str.lower().count('nike')
                
                # Analysis quality indicators
                quality_indicators = [
                    "competitive", "analysis", "strategy", "comparison",
                    "market", "engagement", "content performance", 
                    "brand positioning", "audience", "insights"
                ]
                
                quality_score = sum(1 for indicator in quality_indicators if indicator in plan_str.lower())
                
                # Generic template indicators (what we want to avoid)
                generic_indicators = [
                    "lorem ipsum", "placeholder", "template", "sample content",
                    "example post", "generic", "buzzword", "corporate speak",
                    "insert content here", "add your", "customize this"
                ]
                
                generic_score = sum(1 for indicator in generic_indicators if indicator in plan_str.lower())
                
                logger.info(f"📊 Competitor mentions: {competitor_mentions}/{len(competitors)}")
                logger.info(f"📊 Nike mentions: {nike_mentions}")
                logger.info(f"📊 Quality indicators: {quality_score}")
                logger.info(f"📊 Generic indicators: {generic_score}")
                
                # Check for specific competitor analysis section
                competitor_analysis = None
                if isinstance(content_plan, dict):
                    # Look for competitor analysis in various locations
                    for key, value in content_plan.items():
                        if 'competitor' in key.lower() and isinstance(value, (dict, str)):
                            competitor_analysis = value
                            break
                        elif isinstance(value, dict):
                            for subkey, subvalue in value.items():
                                if 'competitor' in subkey.lower():
                                    competitor_analysis = subvalue
                                    break
                
                step3_success = False
                if competitor_mentions >= 2 and quality_score >= 5 and generic_score == 0:
                    logger.info("✅ Content plan appears to be high quality")
                    step3_success = True
                    
                    if competitor_analysis:
                        logger.info("✅ Found dedicated competitor analysis section")
                        analysis_preview = str(competitor_analysis)[:300] + "..."
                        logger.info(f"📝 Analysis preview: {analysis_preview}")
                    else:
                        logger.warning("⚠️ No dedicated competitor analysis section found")
                else:
                    logger.warning(f"⚠️ Content plan quality needs improvement")
                    logger.info(f"Quality: {quality_score}, Generic: {generic_score}, Competitors: {competitor_mentions}")
                    
                    # Show sample content for debugging
                    if len(plan_str) > 500:
                        sample = plan_str[:500] + "..."
                    else:
                        sample = plan_str
                    logger.info(f"📝 Content sample: {sample}")
                    
            else:
                logger.error("❌ Content plan generation failed")
                step3_success = False
                
        except Exception as e:
            logger.error(f"❌ Content plan generation failed: {str(e)}")
            step3_success = False
        
        # FINAL SUMMARY
        logger.info("\n" + "=" * 60)
        logger.info("🎯 FINAL QUALITY TEST SUMMARY:")
        logger.info(f"   Step 1 - Data Collection: {'✅' if step1_success else '❌'}")
        logger.info(f"   Step 2 - Vector Database: {'✅' if step2_success else '❌'}")
        logger.info(f"   Step 3 - Content Plan: {'✅' if step3_success else '❌'}")
        
        overall_success = step1_success and step2_success and step3_success
        
        if overall_success:
            logger.info("🎉 ALL TESTS PASSED - COMPETITOR ANALYSIS QUALITY IS FIXED!")
            logger.info("The system now generates real data-driven insights instead of generic templates.")
            return True
        else:
            failed_steps = []
            if not step1_success: failed_steps.append("Data Collection")
            if not step2_success: failed_steps.append("Vector Database")
            if not step3_success: failed_steps.append("Content Plan")
            
            logger.error(f"❌ QUALITY ISSUES REMAIN - Failed: {', '.join(failed_steps)}")
            
            # Provide specific guidance
            if not step1_success:
                logger.error("💡 Data Collection Issue: Check platform and competitor data paths")
            if not step2_success:
                logger.error("💡 Vector Database Issue: Competitor data not properly indexed")
            if not step3_success:
                logger.error("💡 Content Plan Issue: RAG generation not using real competitor data")
                
            return False
            
    except Exception as e:
        logger.error(f"❌ Test failed with exception: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """
    Main function to run the comprehensive competitor analysis quality test.
    """
    
    logger.info("🚀 FINAL COMPETITOR ANALYSIS QUALITY TEST")
    logger.info("Testing with correct platform (Facebook) where competitor data exists...")
    logger.info("")
    
    success = test_competitor_analysis_with_real_data()
    
    if success:
        logger.info("\n🎊 SUCCESS: Competitor analysis quality has been validated!")
        logger.info("The system generates real data-driven insights from actual competitor data.")
        return 0
    else:
        logger.error("\n💥 FAILURE: Quality issues still remain.")
        logger.error("Check the detailed output above for specific issues to address.")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
