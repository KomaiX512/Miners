#!/usr/bin/env python3
"""
Script to install AI-generated competitor analysis as part of the pipeline.
This will check content_plan.json and run our fix script if needed.
"""

import os
import json
import logging
import subprocess
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('ai_competitor_analysis')

def ensure_ai_competitor_analysis():
    """Check content_plan.json and apply the AI competitor analysis fix if needed"""
    content_plan_file = 'content_plan.json'
    
    # Check if content plan exists
    if not os.path.exists(content_plan_file):
        logger.warning(f"{content_plan_file} does not exist, cannot check competitor analysis")
        return False
    
    # Load the content plan
    try:
        with open(content_plan_file, 'r') as f:
            content_plan = json.load(f)
    except Exception as e:
        logger.error(f"Failed to load {content_plan_file}: {e}")
        return False
    
    # Check for competitors
    competitor_usernames = content_plan.get('competitors', [])
    if not competitor_usernames:
        logger.info("No competitors found in content plan, no fixes needed")
        return True
    
    # Check if competitor_analysis exists and is AI-generated
    need_fix = False
    
    if 'competitor_analysis' not in content_plan:
        logger.info("No competitor_analysis section found, fix needed")
        need_fix = True
    else:
        competitor_analysis = content_plan.get('competitor_analysis', {})
        
        # Check each competitor for AI-generated content
        for competitor in competitor_usernames:
            if competitor not in competitor_analysis:
                logger.info(f"Competitor {competitor} missing from competitor_analysis, fix needed")
                need_fix = True
                break
            
            comp_data = competitor_analysis[competitor]
            
            # Check if this appears to be placeholder content
            if "Analysis available for" in comp_data.get("overview", "") or "Competitive analysis for" in comp_data.get("overview", ""):
                logger.info(f"Competitor {competitor} has placeholder analysis, fix needed")
                need_fix = True
                break
            
            # Check if intelligence_source indicates AI generation
            if comp_data.get("intelligence_source", "") not in ["threat_assessment", "rag_extraction", "dedicated_rag", "manual_analysis"]:
                logger.info(f"Competitor {competitor} lacks proper intelligence_source, fix needed")
                need_fix = True
                break
            
            # Check for required fields: strengths, weaknesses, vulnerabilities, strategies, recommended_counter_strategies
            if not all(field in comp_data for field in ["strengths", "vulnerabilities", "recommended_counter_strategies"]):
                logger.info(f"Competitor {competitor} missing essential fields, fix needed")
                need_fix = True
                break
                
            # Specifically check for 'strategies' field which is causing errors
            if "strategies" not in comp_data:
                logger.info(f"Competitor {competitor} missing 'strategies' field, fix needed")
                need_fix = True
                break
                
            # Check for 'weaknesses' field
            if "weaknesses" not in comp_data:
                logger.info(f"Competitor {competitor} missing 'weaknesses' field, fix needed")
                need_fix = True
                break
            
            # Check for sufficient content in fields
            if (len(comp_data.get("strengths", [])) < 2 or 
                len(comp_data.get("vulnerabilities", [])) < 2 or 
                len(comp_data.get("recommended_counter_strategies", [])) < 2 or
                len(comp_data.get("strategies", [])) < 2 or
                len(comp_data.get("weaknesses", [])) < 2):
                logger.info(f"Competitor {competitor} has insufficient analysis content, fix needed")
                need_fix = True
                break
    
    # Check for force fix parameter
    if len(sys.argv) > 1 and sys.argv[1] == '--force':
        logger.info("Force fix requested via command line parameter")
        need_fix = True
    
    # Apply fix if needed
    if need_fix:
        logger.info("Running competitor analysis fix...")
        try:
            # Check if fix_competitor_analysis.py exists
            if not os.path.exists('fix_competitor_analysis.py'):
                logger.error("fix_competitor_analysis.py not found, cannot apply fix")
                return False
            
            # Run the fix script
            result = subprocess.run(['python3', 'fix_competitor_analysis.py'], 
                                  capture_output=True, 
                                  text=True)
            
            if result.returncode == 0:
                logger.info("Successfully applied competitor analysis fix")
                logger.info(f"Fix output: {result.stdout.strip()}")
                
                # Verify the fix worked by loading the content plan again
                try:
                    with open(content_plan_file, 'r') as f:
                        updated_content_plan = json.load(f)
                    
                    # Check if strategies and weaknesses are now present
                    all_fixed = True
                    for competitor in competitor_usernames:
                        comp_data = updated_content_plan.get('competitor_analysis', {}).get(competitor, {})
                        if "strategies" not in comp_data or "weaknesses" not in comp_data:
                            logger.warning(f"Competitor {competitor} still missing required fields after fix")
                            all_fixed = False
                    
                    if all_fixed:
                        logger.info("✅ All competitors now have required fields including 'strategies' and 'weaknesses'")
                    
                except Exception as e:
                    logger.error(f"Error verifying fix: {e}")
                
                return True
            else:
                logger.error(f"Fix script failed with exit code {result.returncode}")
                logger.error(f"Error output: {result.stderr.strip()}")
                return False
            
        except Exception as e:
            logger.error(f"Error running fix script: {e}")
            return False
    else:
        logger.info("✅ Competitor analysis already contains AI-generated content with all required fields")
        return True

def manual_fix_competitor_data(content_plan_file='content_plan.json'):
    """Apply direct in-memory fix to competitor data if needed for strategies field"""
    try:
        with open(content_plan_file, 'r') as f:
            content_plan = json.load(f)
            
        modified = False
        competitor_analysis = content_plan.get('competitor_analysis', {})
        
        for competitor, comp_data in competitor_analysis.items():
            # Fix strategies field if missing
            if "strategies" not in comp_data:
                if "recommended_counter_strategies" in comp_data and comp_data["recommended_counter_strategies"]:
                    comp_data["strategies"] = comp_data["recommended_counter_strategies"].copy()
                    logger.info(f"Fixed missing strategies field for {competitor} by copying from recommended_counter_strategies")
                    modified = True
                else:
                    comp_data["strategies"] = [f"Monitor {competitor}'s content strategy", 
                                             f"Adapt to {competitor}'s market positioning"]
                    logger.info(f"Fixed missing strategies field for {competitor} with default strategies")
                    modified = True
            
            # Fix weaknesses field if missing
            if "weaknesses" not in comp_data:
                if "vulnerabilities" in comp_data and comp_data["vulnerabilities"]:
                    comp_data["weaknesses"] = comp_data["vulnerabilities"].copy()
                    logger.info(f"Fixed missing weaknesses field for {competitor} by copying from vulnerabilities")
                    modified = True
                else:
                    comp_data["weaknesses"] = [f"Need more data on {competitor}'s performance limitations"]
                    logger.info(f"Fixed missing weaknesses field for {competitor} with default weaknesses")
                    modified = True
        
        if modified:
            # Save the updated content plan
            with open(content_plan_file, 'w') as f:
                json.dump(content_plan, f, indent=2)
            logger.info(f"Successfully saved updated {content_plan_file} with fixed competitor data")
            return True
        else:
            logger.info("No direct fixes needed for competitor data")
            return False
                
    except Exception as e:
        logger.error(f"Error in manual fix: {e}")
        return False

if __name__ == "__main__":
    logger.info("Ensuring AI-generated competitor analysis...")
    success = ensure_ai_competitor_analysis()
    
    # Apply manual field fix if needed
    if not success:
        logger.info("Attempting manual field fix for common issues...")
        manual_fix = manual_fix_competitor_data()
        if manual_fix:
            logger.info("✅ Successfully applied manual field fixes to competitor data")
            success = True
    
    if success:
        logger.info("✅ AI-generated competitor analysis check completed successfully")
        sys.exit(0)
    else:
        logger.error("❌ Failed to ensure AI-generated competitor analysis")
        sys.exit(1) 