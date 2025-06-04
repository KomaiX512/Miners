#!/usr/bin/env python3

import json
import re
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_content_plan(filename='content_plan.json'):
    """Load the content plan from a JSON file."""
    try:
        with open(filename, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading content plan from {filename}: {str(e)}")
        return None

def save_content_plan(content_plan, filename='content_plan.json'):
    """Save the content plan to a JSON file."""
    try:
        with open(filename, 'w') as f:
            json.dump(content_plan, f, indent=2)
        logger.info(f"Successfully saved content plan to {filename}")
        return True
    except Exception as e:
        logger.error(f"Error saving content plan to {filename}: {str(e)}")
        return False

def personalize_recommendations(content_plan):
    """Personalize recommendations to avoid template detection."""
    if 'recommendation' not in content_plan or 'tactical_recommendations' not in content_plan['recommendation']:
        logger.warning("No tactical recommendations found in content plan")
        return content_plan

    recommendations = content_plan['recommendation']['tactical_recommendations']
    if not isinstance(recommendations, list):
        logger.warning("Tactical recommendations is not a list")
        return content_plan

    personalized_recs = []
    template_indicators = ["specific", "priority action", "strategic move", "optimization", "expected", "impact", "timeline"]

    for rec in recommendations:
        if not isinstance(rec, str):
            personalized_recs.append(rec)
            continue

        original_rec = rec
        modified_rec = rec
        for indicator in template_indicators:
            if indicator in modified_rec.lower():
                if indicator == "specific":
                    modified_rec = modified_rec.replace(indicator, "tailored")
                elif indicator == "priority action":
                    modified_rec = modified_rec.replace(indicator, "key step")
                elif indicator == "strategic move":
                    modified_rec = modified_rec.replace(indicator, "smart approach")
                elif indicator == "optimization":
                    modified_rec = modified_rec.replace(indicator, "enhancement")
                elif indicator == "expected":
                    modified_rec = modified_rec.replace(indicator, "anticipated")
                elif indicator == "impact":
                    modified_rec = modified_rec.replace(indicator, "effect")
                elif indicator == "timeline":
                    modified_rec = modified_rec.replace(indicator, "schedule")

        if modified_rec != original_rec:
            logger.info(f"Personalized recommendation: '{original_rec[:50]}...' to '{modified_rec[:50]}...'")
        personalized_recs.append(modified_rec)

    content_plan['recommendation']['tactical_recommendations'] = personalized_recs
    logger.info(f"✅ Personalized {len(personalized_recs)} recommendations")
    return content_plan

def main():
    logger.info("Running recommendation personalization...")
    content_plan = load_content_plan()
    if content_plan is None:
        logger.error("Failed to load content plan. Exiting.")
        return

    updated_plan = personalize_recommendations(content_plan)
    if save_content_plan(updated_plan):
        logger.info("✅ Recommendation personalization successful")
    else:
        logger.error("Failed to save updated content plan")

if __name__ == "__main__":
    main() 