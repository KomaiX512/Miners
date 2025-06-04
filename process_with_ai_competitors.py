#!/usr/bin/env python3
"""
Process content plan with AI competitors
This script ensures competitor analysis fields are properly fixed before running the main pipeline
"""

import os
import sys
import json
import logging
import subprocess
import shutil
import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run_fix_and_verify():
    """Run the fix and verification scripts for competitor analysis."""
    try:
        logger.info("Running fix_competitor_analysis.py...")
        result = subprocess.run(['python', 'fix_competitor_analysis.py'], check=True, capture_output=True, text=True)
        logger.info(result.stdout)
        if result.stderr:
            logger.error(result.stderr)

        logger.info("Running verify_competitor_fields.py...")
        result = subprocess.run(['python', 'verify_competitor_fields.py'], check=True, capture_output=True, text=True)
        logger.info(result.stdout)
        if result.stderr:
            logger.error(result.stderr)
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Error running fix/verify scripts: {str(e)}")
        logger.error(e.stderr)
        return False

def backup_content_plan():
    """Backup the content plan file with a timestamp."""
    content_plan_file = 'content_plan.json'
    if os.path.exists(content_plan_file):
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = f"content_plan_backup_{timestamp}.json"
        shutil.copy2(content_plan_file, backup_file)
        logger.info(f"Backed up content_plan.json to {backup_file}")
    else:
        logger.warning("content_plan.json not found, no backup created")

def check_competitor_strategies():
    """Check if competitor strategies are present in the content plan."""
    import json
    content_plan_file = 'content_plan.json'
    if not os.path.exists(content_plan_file):
        logger.error(f"{content_plan_file} not found")
        return False

    with open(content_plan_file, 'r') as f:
        content_plan = json.load(f)

    if 'competitor_analysis' not in content_plan:
        logger.error("competitor_analysis not found in content plan")
        return False

    all_have_strategies = True
    for competitor, analysis in content_plan['competitor_analysis'].items():
        if 'strategies' not in analysis or not analysis.get('strategies'):
            logger.warning(f"Competitor {competitor} missing strategies field")
            all_have_strategies = False
        else:
            logger.info(f"✅ Competitor {competitor} has strategies field")

    return all_have_strategies

def run_main_pipeline():
    """Run the main pipeline with the updated content plan."""
    try:
        logger.info("Running main.py with updated content plan in automated mode...")
        result = subprocess.run(['python', 'main.py', 'run_automated'], check=False, capture_output=True, text=True)
        logger.info(result.stdout)
        if result.stderr:
            logger.error(result.stderr)
        if result.returncode != 0:
            logger.error(f"main.py exited with non-zero status code: {result.returncode}")
            return False
        return True
    except Exception as e:
        logger.error(f"Error running main.py: {str(e)}")
        return False

def personalize_recommendations():
    """Run the personalization script for recommendations."""
    try:
        logger.info("Running personalize_recommendations.py...")
        result = subprocess.run(['python', 'personalize_recommendations.py'], check=True, capture_output=True, text=True)
        logger.info(result.stdout)
        if result.stderr:
            logger.error(result.stderr)
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Error running personalize_recommendations.py: {str(e)}")
        logger.error(e.stderr)
        return False

def process_with_ai_competitors():
    """Process content plan with AI, ensuring competitor analysis is fixed."""
    logger.info("Starting process with AI competitors...")

    # Step 1: Backup current content plan
    backup_content_plan()

    # Step 2: Run fix and verify scripts
    if not run_fix_and_verify():
        logger.error("Fix and verification failed. Exiting.")
        return False

    # Step 3: Verify competitor strategies
    if not check_competitor_strategies():
        logger.warning("Not all competitors have strategies field. Proceeding with caution.")
    else:
        logger.info("✅ All competitors have strategies field")

    # Step 4: Personalize recommendations
    if not personalize_recommendations():
        logger.error("Personalization of recommendations failed. Exiting.")
        return False

    # Step 5: Run main pipeline
    if run_main_pipeline():
        logger.info("🎉 Successfully processed content plan with AI competitors")
        return True
    else:
        logger.error("Main pipeline execution failed")
        return False

if __name__ == "__main__":
    logger.info("Starting process_with_ai_competitors.py")
    success = process_with_ai_competitors()
    if success:
        logger.info("✅ Process completed successfully")
        sys.exit(0)
    else:
        logger.error("❌ Process failed")
        sys.exit(1) 