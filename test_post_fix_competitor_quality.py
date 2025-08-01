#!/usr/bin/env python3

"""
POST-FIX VALIDATION: Test Fixed Competitor Analysis Quality
============================================================

This script validates that the critical bug fixes have resolved the poor quality
competitor analysis issue. It tests:

1. Competitor data indexing with correct usernames 
2. Vector database queries returning real competitor data
3. RAG generation producing quality insights instead of generic templates
4. End-to-end competitor analysis quality

EXPECTED IMPROVEMENTS:
- Nike, redbull, netflix data should be properly indexed and queryable
- RAG queries should return actual competitor insights
- Content plan should contain real data-driven competitor analysis
"""

import sys
import logging
import json
import os
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_fixed_competitor_analysis_quality():
    """
    Test the quality of competitor analysis after applying critical bug fixes.
    """
    
    logger.info("🧪 TESTING FIXED COMPETITOR ANALYSIS QUALITY")
    logger.info("=" * 60)
    
    try:
        # Import the main system
        sys.path.append('/home/komail/Miners-1')
        from main import ContentRecommendationSystem
        
        # Initialize the system
        system = ContentRecommendationSystem()
        
        # Test parameters (same as before but now should work properly)
        primary_username = "Appleass"  # Valid primary with real data
        competitors = ["nike", "redbull", "netflix"]  # Real competitors with known data
        platform = "instagram"
        
        logger.info(f"🎯 Testing: {primary_username} vs {competitors} on {platform}")
        
        # STEP 1: Test competitor data collection
        logger.info("\n📊 STEP 1: Testing competitor data collection")
        available_data = system._collect_available_competitor_data(
            competitors=competitors,
            platform=platform
        )
        
        step1_success = False
        for competitor in competitors:
            if competitor in available_data and available_data[competitor]:
                posts = available_data[competitor].get('posts', [])
                source = available_data[competitor].get('source', 'unknown')
                logger.info(f"✅ {competitor}: {len(posts)} posts from {source}")
                if len(posts) > 0:
                    step1_success = True
            else:
                logger.warning(f"⚠️ {competitor}: No data collected")
        
        if not step1_success:
            logger.error("❌ STEP 1 FAILED: No competitor data collected")
            return False
        
        # STEP 2: Test vector database indexing and queries
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
        
        if not step2_success:
            logger.error("❌ STEP 2 FAILED: No competitor data found in vector database")
            return False
        
        # STEP 3: Test RAG generation with competitor data
        logger.info("\n🤖 STEP 3: Testing RAG generation")
        
        try:
            # Test RAG query for competitive intelligence
            rag_query = f"Analyze competitive strategy differences between {primary_username} and competitors {', '.join(competitors)}"
            
            rag_results = system.rag_system.generate_content_plan(
                username=primary_username,
                platform=platform,
                account_type="personal",
                posting_style="informational",
                competitors=competitors,
                query=rag_query,
                mode="real"
            )
            
            if rag_results:
                logger.info("✅ RAG generation successful")
                
                # Check for quality indicators vs generic templates
                rag_content = str(rag_results).lower()
                
                # Quality indicators (real competitor data)
                quality_indicators = [
                    "nike", "redbull", "netflix",  # Competitor names mentioned
                    "strategy", "content", "engagement",  # Real analysis terms
                    "compared to", "versus", "different from",  # Comparative analysis
                ]
                
                # Generic template indicators (bad quality)
                generic_indicators = [
                    "lorem ipsum", "placeholder", "template",
                    "sample content", "example post", "generic",
                    "buzzword", "corporate speak"
                ]
                
                quality_score = sum(1 for indicator in quality_indicators if indicator in rag_content)
                generic_score = sum(1 for indicator in generic_indicators if indicator in rag_content)
                
                logger.info(f"📊 Quality indicators found: {quality_score}")
                logger.info(f"📊 Generic indicators found: {generic_score}")
                
                if quality_score > generic_score and quality_score >= 3:
                    logger.info("✅ RAG content appears to be high quality")
                    step3_success = True
                else:
                    logger.warning(f"⚠️ RAG content quality questionable - Quality: {quality_score}, Generic: {generic_score}")
                    step3_success = False
                    
            else:
                logger.error("❌ RAG generation returned empty results")
                step3_success = False
                
        except Exception as e:
            logger.error(f"❌ RAG generation failed: {str(e)}")
            step3_success = False
        
        # STEP 4: Test full competitor analysis generation
        logger.info("\n🎯 STEP 4: Testing full competitor analysis generation")
        
        try:
            # Use the existing data instead of re-scraping
            system._current_primary_username = primary_username  # Set context
            
            # Generate content plan with competitor analysis
            content_plan = system.generate_content_plan(
                username=primary_username,
                platform=platform,
                account_type="personal",
                posting_style="informational",
                competitors=competitors,
                use_existing_data=True  # Skip scraping, use existing data
            )
            
            if content_plan:
                logger.info("✅ Content plan generation successful")
                
                # Extract competitor analysis from content plan
                competitor_analysis = None
                
                # Look for competitor analysis in different parts of the content plan
                if isinstance(content_plan, dict):
                    # Check for direct competitor analysis
                    competitor_analysis = content_plan.get('competitor_analysis')
                    
                    # Check in recommendations
                    if not competitor_analysis and 'recommendations' in content_plan:
                        recommendations = content_plan['recommendations']
                        if isinstance(recommendations, dict):
                            competitor_analysis = recommendations.get('competitor_analysis')
                            
                            # Check in sub-sections
                            for key, value in recommendations.items():
                                if isinstance(value, dict) and 'competitor_analysis' in value:
                                    competitor_analysis = value['competitor_analysis']
                                    break
                
                if competitor_analysis:
                    analysis_content = str(competitor_analysis).lower()
                    
                    # Check for specific competitor mentions and real insights
                    competitor_mentions = sum(1 for comp in competitors if comp in analysis_content)
                    
                    # Quality indicators for competitor analysis
                    analysis_quality_indicators = [
                        "engagement rate", "posting frequency", "content style",
                        "audience interaction", "brand positioning", "competitive advantage",
                        "market share", "content performance", "strategy differences"
                    ]
                    
                    analysis_quality_score = sum(1 for indicator in analysis_quality_indicators if indicator in analysis_content)
                    
                    logger.info(f"📊 Competitors mentioned: {competitor_mentions}/{len(competitors)}")
                    logger.info(f"📊 Analysis quality indicators: {analysis_quality_score}")
                    
                    if competitor_mentions >= 2 and analysis_quality_score >= 3:
                        logger.info("✅ Competitor analysis appears to be high quality")
                        step4_success = True
                    else:
                        logger.warning(f"⚠️ Competitor analysis quality needs improvement")
                        logger.info(f"Analysis preview: {str(competitor_analysis)[:200]}...")
                        step4_success = False
                else:
                    logger.warning("⚠️ No competitor analysis found in content plan")
                    step4_success = False
                    
            else:
                logger.error("❌ Content plan generation failed")
                step4_success = False
                
        except Exception as e:
            logger.error(f"❌ Full competitor analysis test failed: {str(e)}")
            step4_success = False
        
        # FINAL SUMMARY
        logger.info("\n" + "=" * 60)
        logger.info("🎯 POST-FIX VALIDATION SUMMARY:")
        logger.info(f"   Step 1 - Data Collection: {'✅' if step1_success else '❌'}")
        logger.info(f"   Step 2 - Vector Database: {'✅' if step2_success else '❌'}")
        logger.info(f"   Step 3 - RAG Generation: {'✅' if step3_success else '❌'}")
        logger.info(f"   Step 4 - Full Analysis: {'✅' if step4_success else '❌'}")
        
        overall_success = step1_success and step2_success and step3_success and step4_success
        
        if overall_success:
            logger.info("🎉 ALL TESTS PASSED - COMPETITOR ANALYSIS QUALITY FIXED!")
            return True
        else:
            failed_steps = []
            if not step1_success: failed_steps.append("Data Collection")
            if not step2_success: failed_steps.append("Vector Database")
            if not step3_success: failed_steps.append("RAG Generation")
            if not step4_success: failed_steps.append("Full Analysis")
            
            logger.error(f"❌ QUALITY ISSUES REMAIN - Failed: {', '.join(failed_steps)}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Test failed with exception: {str(e)}")
        return False

def main():
    """
    Main function to run the post-fix validation test.
    """
    
    logger.info("🚀 POST-FIX COMPETITOR ANALYSIS QUALITY VALIDATION")
    logger.info("Testing if the critical bug fixes resolved the poor quality analysis...")
    logger.info("")
    
    success = test_fixed_competitor_analysis_quality()
    
    if success:
        logger.info("\n🎊 SUCCESS: The competitor analysis quality has been fixed!")
        logger.info("The system should now generate real data-driven insights instead of generic templates.")
        return 0
    else:
        logger.error("\n💥 FAILURE: Quality issues still remain after fixes.")
        logger.error("Further investigation needed to identify additional root causes.")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
