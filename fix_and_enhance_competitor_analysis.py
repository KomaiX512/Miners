#!/usr/bin/env python3
"""
Fix and enhance competitor analysis in content_plan.json

This script provides a comprehensive solution to:
1. Remove any top-level competitor_analysis (it should only exist inside recommendation structure)
2. Ensure proper competitor_analysis exists in the recommendation.threat_assessment structure
3. Enhance the competitor analysis with platform-specific, account-type specific, intelligence-level insights

PERMANENT SOLUTION:
The script permanently addresses both structural and quality issues with competitor analysis by:
- Ensuring the correct structure (competitor analysis only inside recommendation.threat_assessment)
- Providing detailed, platform-specific analysis based on the actual platform (Twitter, Instagram, etc.)
- Customizing analysis based on account type (branding, business, personal)
- Including comprehensive intelligence-level insights resembling professional competitive intelligence
"""

import subprocess
import os
import sys
import logging
import json
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('fix_and_enhance_competitor_analysis')

def backup_content_plan(content_plan_file='content_plan.json'):
    """Create a backup of the content plan before modifications"""
    try:
        if not os.path.exists(content_plan_file):
            logger.warning(f"{content_plan_file} not found, cannot create backup")
            return False
            
        # Create timestamp for backup filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = f"content_plan_backup_{timestamp}.json"
        
        # Copy content plan to backup file
        with open(content_plan_file, 'r') as src:
            content = src.read()
            
        with open(backup_file, 'w') as dst:
            dst.write(content)
            
        logger.info(f"✅ Created backup of content plan at {backup_file}")
        return True
    except Exception as e:
        logger.error(f"Error creating backup: {str(e)}")
        return False

def fix_and_enhance_competitor_analysis():
    """Run both fix and enhancement scripts to completely address competitor analysis issues"""
    logger.info("🔧 Starting comprehensive competitor analysis fix and enhancement")
    
    # Step 1: Create backup of content plan
    backup_content_plan()
    
    # Step 2: Run fix_competitor_analysis.py to fix structure issues
    logger.info("Step 1: Running fix_competitor_analysis.py to fix structure issues...")
    try:
        result = subprocess.run(['python3', 'fix_competitor_analysis.py'], 
                              capture_output=True, 
                              text=True)
        
        if result.returncode == 0:
            logger.info("✅ Successfully fixed competitor analysis structure")
            logger.info(f"Output: {result.stdout.strip()}")
        else:
            logger.error(f"❌ Fix script failed with exit code {result.returncode}")
            logger.error(f"Error output: {result.stderr.strip()}")
            return False
    except Exception as e:
        logger.error(f"Error running fix script: {str(e)}")
        return False
    
    # Step 3: Run enhance_recommendation_competitor_analysis.py to improve content quality
    logger.info("Step 2: Running enhance_recommendation_competitor_analysis.py to improve content quality...")
    try:
        result = subprocess.run(['python3', 'enhance_recommendation_competitor_analysis.py'], 
                              capture_output=True, 
                              text=True)
        
        if result.returncode == 0:
            logger.info("✅ Successfully enhanced competitor analysis content")
            logger.info(f"Output: {result.stdout.strip()}")
        else:
            logger.error(f"❌ Enhancement script failed with exit code {result.returncode}")
            logger.error(f"Error output: {result.stderr.strip()}")
            return False
    except Exception as e:
        logger.error(f"Error running enhancement script: {str(e)}")
        return False
    
    # Step 4: Verify the content plan is in the correct structure with enhanced content
    logger.info("Step 3: Verifying fixes and enhancements...")
    try:
        with open('content_plan.json', 'r') as f:
            content_plan = json.load(f)
            
        # Check if top-level competitor_analysis has been removed
        if 'competitor_analysis' in content_plan:
            logger.error("❌ Verification failed: top-level competitor_analysis still exists")
            return False
            
        # Check if competitor_analysis exists in recommendation structure
        if ('recommendation' not in content_plan or
            'threat_assessment' not in content_plan['recommendation'] or
            'competitor_analysis' not in content_plan['recommendation']['threat_assessment']):
            logger.error("❌ Verification failed: competitor_analysis not found in recommendation structure")
            return False
            
        # Check if competitors exist and have comprehensive analysis
        competitors = content_plan.get('competitors', [])
        competitor_analysis = content_plan['recommendation']['threat_assessment']['competitor_analysis']
        
        for competitor in competitors:
            if competitor not in competitor_analysis:
                logger.error(f"❌ Verification failed: Competitor {competitor} not found in competitor_analysis")
                return False
                
            comp_data = competitor_analysis[competitor]
            
            # Check required fields
            required_fields = ["overview", "strengths", "vulnerabilities", "weaknesses", "recommended_counter_strategies"]
            for field in required_fields:
                if field not in comp_data:
                    logger.error(f"❌ Verification failed: Required field '{field}' missing for {competitor}")
                    return False
                    
                # Check content quality for list fields
                if field != "overview" and (not isinstance(comp_data[field], list) or len(comp_data[field]) < 3):
                    logger.error(f"❌ Verification failed: Field '{field}' for {competitor} has insufficient content")
                    return False
        
        logger.info("✅ Verification successful: All competitors have comprehensive analysis in the correct structure")
        return True
        
    except Exception as e:
        logger.error(f"Error during verification: {str(e)}")
        return False

def output_summary():
    """Output a summary of the competitor analysis structure and content"""
    try:
        with open('content_plan.json', 'r') as f:
            content_plan = json.load(f)
            
        # Get basics
        competitors = content_plan.get('competitors', [])
        platform = content_plan.get('platform', 'unknown')
        account_type = content_plan.get('account_type', 'unknown')
        primary_username = content_plan.get('primary_username', 'unknown')
        
        # Check for competitor_analysis in recommendation structure
        has_recommendation = 'recommendation' in content_plan
        has_threat_assessment = has_recommendation and 'threat_assessment' in content_plan['recommendation']
        has_competitor_analysis = has_threat_assessment and 'competitor_analysis' in content_plan['recommendation']['threat_assessment']
        
        # Print summary
        print("\n" + "="*80)
        print(f"COMPETITOR ANALYSIS SUMMARY FOR {primary_username.upper()} ON {platform.upper()}")
        print("="*80)
        print(f"Account type: {account_type}")
        print(f"Total competitors: {len(competitors)}")
        print(f"Competitors: {', '.join(competitors)}")
        print(f"Has recommendation structure: {'✅ Yes' if has_recommendation else '❌ No'}")
        print(f"Has threat_assessment: {'✅ Yes' if has_threat_assessment else '❌ No'}")
        print(f"Has competitor_analysis in recommendation: {'✅ Yes' if has_competitor_analysis else '❌ No'}")
        print(f"Has top-level competitor_analysis (SHOULD BE NO): {'❌ Yes' if 'competitor_analysis' in content_plan else '✅ No'}")
        
        # If competitor_analysis exists in recommendation structure, show details
        if has_competitor_analysis:
            competitor_analysis = content_plan['recommendation']['threat_assessment']['competitor_analysis']
            print("\nCOMPETITOR ANALYSIS DETAILS:")
            print("-"*80)
            
            for competitor in competitors:
                if competitor in competitor_analysis:
                    comp_data = competitor_analysis[competitor]
                    print(f"\n{competitor.upper()}:")
                    print(f"  Overview length: {len(comp_data.get('overview', ''))}")
                    print(f"  Strengths: {len(comp_data.get('strengths', []))}")
                    print(f"  Vulnerabilities: {len(comp_data.get('vulnerabilities', []))}")
                    print(f"  Weaknesses: {len(comp_data.get('weaknesses', []))}")
                    print(f"  Counter-strategies: {len(comp_data.get('recommended_counter_strategies', []))}")
                else:
                    print(f"\n{competitor.upper()}: ❌ NOT FOUND IN COMPETITOR ANALYSIS")
        
        print("\nSTATUS:")
        if has_competitor_analysis and 'competitor_analysis' not in content_plan:
            print("✅ Competitor analysis structure is correct (only inside recommendation)")
            
            # Check content quality
            all_complete = True
            for competitor in competitors:
                if competitor not in competitor_analysis:
                    all_complete = False
                    break
                    
                comp_data = competitor_analysis[competitor]
                required_fields = ["overview", "strengths", "vulnerabilities", "weaknesses", "recommended_counter_strategies"]
                
                for field in required_fields:
                    if field not in comp_data:
                        all_complete = False
                        break
                        
                    if field != "overview" and (not isinstance(comp_data[field], list) or len(comp_data[field]) < 3):
                        all_complete = False
                        break
            
            if all_complete:
                print("✅ Competitor analysis content is comprehensive and complete")
            else:
                print("⚠️ Competitor analysis structure is correct but content may be incomplete")
        else:
            print("❌ Competitor analysis structure is incorrect")
        
        print("="*80)
        
    except Exception as e:
        logger.error(f"Error generating summary: {str(e)}")
        print("\n❌ Error generating summary. Check logs for details.")

if __name__ == "__main__":
    success = fix_and_enhance_competitor_analysis()
    
    # Output summary regardless of success/failure
    output_summary()
    
    if success:
        logger.info("🎉 Successfully fixed and enhanced competitor analysis")
        sys.exit(0)
    else:
        logger.error("❌ Failed to completely fix and enhance competitor analysis")
        sys.exit(1) 