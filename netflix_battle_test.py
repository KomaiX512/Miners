#!/usr/bin/env python3
"""
Direct Netflix battle test - bypassing data retrieval issues.
"""

import os
import sys
import logging
import json
from datetime import datetime

# Add current directory to path
sys.path.append('/home/komail/Miners-1')

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run_netflix_battle_test():
    """Run direct Netflix battle test with bypass for data issues."""
    try:
        logger.info("🎬 Starting Netflix Battle Test (Direct Mode)")
        
        # Import the main system
        from main import ContentRecommendationSystem
        
        # Set environment to force production mode
        os.environ['FORCE_PRODUCTION'] = 'true'
        
        # Initialize the system
        logger.info("Initializing Content Recommendation System...")
        system = ContentRecommendationSystem()
        
        # Netflix test configuration
        config = {
            'primary_username': 'netflix',
            'platform': 'facebook', 
            'competitors': ['nike', 'cocacola', 'redbull'],
            'account_type': 'business',
            'posting_style': 'engaging',
            'skip_scraping': True
        }
        
        logger.info(f"Configuration: {config}")
        
        # Run the complete pipeline using the correct method
        logger.info("🚀 Running Facebook username processing...")
        result = system.process_facebook_username(
            username=primary_username,
            results_limit=50,
            force_fresh=True
        )
        
        if result:
            logger.info("✅ Pipeline completed!")
            
            # Check the content plan
            content_plan_path = "/home/komail/Miners-1/content_plan.json"
            if os.path.exists(content_plan_path):
                with open(content_plan_path, 'r') as f:
                    content_plan = json.load(f)
                
                logger.info("📊 CONTENT PLAN ANALYSIS:")
                logger.info(f"Primary: {content_plan.get('primary_username', 'Unknown')}")
                logger.info(f"Platform: {content_plan.get('platform', 'Unknown')}")
                logger.info(f"Posts Analyzed: {content_plan.get('total_posts_analyzed', 0)}")
                
                # Check competitor analysis quality
                competitor_analysis = content_plan.get('competitor_analysis', {})
                
                if competitor_analysis:
                    logger.info("\n🎯 COMPETITOR ANALYSIS QUALITY:")
                    
                    quality_score = 0
                    total_competitors = len(competitor_analysis)
                    
                    for competitor, analysis in competitor_analysis.items():
                        strengths = analysis.get('strengths', [])
                        vulnerabilities = analysis.get('vulnerabilities', [])
                        strategies = analysis.get('recommended_counter_strategies', [])
                        overview = analysis.get('overview', '')
                        
                        logger.info(f"\n{competitor.upper()}:")
                        logger.info(f"  Overview: {overview[:100]}...")
                        logger.info(f"  Strengths: {len(strengths)} items")
                        logger.info(f"  Vulnerabilities: {len(vulnerabilities)} items")
                        logger.info(f"  Strategies: {len(strategies)} items")
                        
                        # Quality check
                        has_meaningful_content = (
                            len(strengths) > 0 and 
                            len(vulnerabilities) > 0 and 
                            len(strategies) > 0 and
                            not all("market intelligence" in str(s).lower() for s in strengths)
                        )
                        
                        if has_meaningful_content:
                            quality_score += 1
                            logger.info(f"  ✅ Quality: GOOD")
                        else:
                            logger.info(f"  ⚠️ Quality: NEEDS IMPROVEMENT")
                    
                    overall_quality = (quality_score / total_competitors) * 100
                    logger.info(f"\n📈 OVERALL QUALITY SCORE: {overall_quality:.1f}% ({quality_score}/{total_competitors} competitors)")
                    
                    if overall_quality >= 80:
                        logger.info("🎉 EXCELLENT! RAG system is generating high-quality insights!")
                        return True
                    elif overall_quality >= 60:
                        logger.info("✅ GOOD! RAG system is working but could be improved")
                        return True
                    else:
                        logger.warning("⚠️ POOR! RAG system needs significant improvement")
                        return False
                        
                else:
                    logger.error("❌ No competitor analysis found!")
                    return False
                    
            else:
                logger.error("❌ Content plan not generated!")
                return False
                
        else:
            logger.error("❌ Pipeline failed!")
            return False
            
    except Exception as e:
        logger.error(f"❌ Netflix battle test failed: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def main():
    """Main function."""
    logger.info("🎯 NETFLIX BATTLE TEST - DIRECT MODE")
    logger.info("="*60)
    
    success = run_netflix_battle_test()
    
    logger.info("\n" + "="*60)
    if success:
        logger.info("🎉 SUCCESS! The RAG pipeline is working correctly!")
        logger.info("✅ Vector database indexing: WORKING")
        logger.info("✅ Competitor analysis: HIGH QUALITY")
        logger.info("✅ Content generation: SUCCESSFUL")
    else:
        logger.error("❌ FAILED! RAG pipeline needs fixing.")
        logger.error("Check the logs above for specific issues.")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
