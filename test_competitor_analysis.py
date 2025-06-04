#!/usr/bin/env python3
"""
Test script to verify the competitor analysis handling of 'strategies' field.
"""

import os
import json
import logging
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('competitor_analysis_test')

def test_strategies_field():
    """
    Test the handling of the 'strategies' field in competitor analysis.
    This simulates the common error and verifies our fix works.
    """
    content_plan_file = 'content_plan.json'
    
    if not os.path.exists(content_plan_file):
        logger.error(f"{content_plan_file} does not exist")
        return False
    
    try:
        # 1. Load the current content plan
        with open(content_plan_file, 'r') as f:
            original_data = json.load(f)
        
        # Make a backup
        with open('content_plan.backup.json', 'w') as f:
            json.dump(original_data, f, indent=2)
        logger.info("Created backup of content plan")
            
        # 2. Simulate the error by removing 'strategies' field from all competitors
        competitors = original_data.get('competitors', [])
        competitor_analysis = original_data.get('competitor_analysis', {})
        
        for comp in competitors:
            if comp in competitor_analysis:
                if 'strategies' in competitor_analysis[comp]:
                    competitor_analysis[comp].pop('strategies')
                    logger.info(f"Removed 'strategies' field from {comp}")
        
        # 3. Save the modified content plan
        with open(content_plan_file, 'w') as f:
            json.dump(original_data, f, indent=2)
        logger.info("Saved content plan without 'strategies' fields")
        
        # 4. Run the ensure_ai_competitor_analysis script
        logger.info("Running ensure_ai_competitor_analysis.py")
        exit_code = os.system('python ensure_ai_competitor_analysis.py')
        
        if exit_code != 0:
            logger.error(f"ensure_ai_competitor_analysis.py failed with exit code {exit_code}")
            return False
        
        # 5. Verify the fix worked
        with open(content_plan_file, 'r') as f:
            fixed_data = json.load(f)
        
        all_fixed = True
        for comp in competitors:
            if comp in fixed_data.get('competitor_analysis', {}):
                if 'strategies' not in fixed_data['competitor_analysis'][comp]:
                    logger.error(f"'strategies' field still missing for {comp}")
                    all_fixed = False
                else:
                    strategies = fixed_data['competitor_analysis'][comp]['strategies']
                    if not strategies or len(strategies) < 1:
                        logger.error(f"'strategies' field is empty for {comp}")
                        all_fixed = False
                    else:
                        logger.info(f"✅ {comp} has valid 'strategies' field with {len(strategies)} strategies")
        
        # 6. Restore the backup
        with open('content_plan.backup.json', 'r') as f:
            backup_data = json.load(f)
        
        with open(content_plan_file, 'w') as f:
            json.dump(backup_data, f, indent=2)
        logger.info("Restored content plan from backup")
        
        if all_fixed:
            logger.info("✅ TEST PASSED: All competitors have valid 'strategies' fields after fix")
            return True
        else:
            logger.error("❌ TEST FAILED: Some competitors still missing 'strategies' fields")
            return False
            
    except Exception as e:
        logger.error(f"Test error: {e}")
        # Try to restore from backup if it exists
        if os.path.exists('content_plan.backup.json'):
            try:
                with open('content_plan.backup.json', 'r') as f:
                    backup_data = json.load(f)
                
                with open(content_plan_file, 'w') as f:
                    json.dump(backup_data, f, indent=2)
                logger.info("Restored content plan from backup after error")
            except Exception as restore_error:
                logger.error(f"Failed to restore backup: {restore_error}")
                
        return False

if __name__ == "__main__":
    logger.info("Starting competitor analysis 'strategies' field test")
    success = test_strategies_field()
    
    if success:
        logger.info("✅✅✅ All tests passed successfully")
        sys.exit(0)
    else:
        logger.error("❌❌❌ Tests failed")
        sys.exit(1) 