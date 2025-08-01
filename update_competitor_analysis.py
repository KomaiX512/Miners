#!/usr/bin/env python3
"""
Update competitor_analysis with AI-generated threat assessment data
This script fixes the competitor analysis content generation issue by copying
properly generated competitor analysis from the threat_assessment section.
"""

import json
import os
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('competitor_analysis_updater')

def update_competitor_analysis():
    """
    Copy threat_assessment competitor_analysis data to main competitor_analysis section.
    This fixes the issue where competitor analysis is not AI-generated properly.
    """
    content_plan_file = 'content_plan.json'
    
    logger.info(f"Loading content plan from {content_plan_file}")
    try:
        with open(content_plan_file, 'r') as f:
            content_plan = json.load(f)
            
        # Check if content_plan has the threat_assessment data
        if 'recommendation' in content_plan and 'threat_assessment' in content_plan['recommendation']:
            threat_assessment = content_plan['recommendation']['threat_assessment']
            
            if 'competitor_analysis' in threat_assessment and isinstance(threat_assessment['competitor_analysis'], dict):
                threat_comp_analysis = threat_assessment['competitor_analysis']
                
                logger.info(f"Found {len(threat_comp_analysis)} competitors with AI-generated analysis in threat_assessment")
                
                # Ensure competitor_analysis section exists in content_plan
                if 'competitor_analysis' not in content_plan:
                    content_plan['competitor_analysis'] = {}
                
                # Copy each competitor analysis to the top-level competitor_analysis section
                for competitor, analysis in threat_comp_analysis.items():
                    # Create proper competitor analysis structure with the AI-generated content
                    competitor_analysis = {
                        "overview": analysis.get("overview", f"Analysis of {competitor}"),
                        "intelligence_source": "threat_assessment",
                        "strengths": analysis.get("strengths", []),
                        "vulnerabilities": analysis.get("vulnerabilities", []), 
                        "recommended_counter_strategies": analysis.get("recommended_counter_strategies", []),
                        "top_content_themes": []  # Initialize empty
                    }
                    
                    # Add top_content_themes if available but under a different key
                    if "themes" in analysis:
                        competitor_analysis["top_content_themes"] = analysis["themes"]
                    elif "top_themes" in analysis:
                        competitor_analysis["top_content_themes"] = analysis["top_themes"]
                        
                    # Update the competitor_analysis in content_plan
                    content_plan['competitor_analysis'][competitor] = competitor_analysis
                    logger.info(f"Updated competitor analysis for {competitor} with AI-generated content")
                
                # Save the updated content plan
                with open(content_plan_file, 'w') as f:
                    json.dump(content_plan, f, indent=2)
                    
                logger.info("Successfully updated content_plan.json with AI-generated competitor analysis")
                return True
            else:
                logger.warning("No competitor_analysis found in threat_assessment")
        else:
            logger.warning("No threat_assessment found in recommendation")
            
        return False
    
    except Exception as e:
        logger.error(f"Error updating competitor analysis: {str(e)}")
        return False

if __name__ == "__main__":
    update_competitor_analysis() 