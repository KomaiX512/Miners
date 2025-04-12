#!/usr/bin/env python3
"""Test script for content plan export functionality."""

import json
import logging
import os
import sys
from main import ContentRecommendationSystem

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_export_content_plan():
    """Test exporting content plan sections to R2."""
    try:
        if not os.path.exists('content_plan.json'):
            logger.error("content_plan.json not found. Please run the main system first.")
            return False
            
        logger.info("Testing content plan export functionality")
        system = ContentRecommendationSystem()
        
        # Load content plan
        with open('content_plan.json', 'r') as f:
            content_plan = json.load(f)
        
        # Rename profile to profile_analysis for compatibility if needed
        if 'profile_analysis' not in content_plan and 'profile' in content_plan:
            content_plan['profile_analysis'] = content_plan['profile']
            
        # Export content plan sections
        result = system.export_content_plan_sections(content_plan)
        
        if result:
            logger.info("Content plan export test PASSED")
        else:
            logger.error("Content plan export test FAILED")
            
        return result
    except Exception as e:
        logger.error(f"Error testing content plan export: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    success = test_export_content_plan()
    sys.exit(0 if success else 1) 