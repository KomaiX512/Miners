#!/usr/bin/env python3

import os
import json
import logging
import argparse
from pathlib import Path
from datetime import datetime

# Import the necessary modules from the project
from data_processor import DataProcessor
from recommendation_engine import RecommendationEngine
from user_profile import UserProfile

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("ContentPlanGenerator")

def create_content_plan(username=None, output_file="content_plan.json", debug=False):
    """
    Generate content recommendations and save them to a JSON file.
    
    Args:
        username (str, optional): The username to generate recommendations for.
                                If None, will use sample data or all users.
        output_file (str): Path to save the JSON output.
        debug (bool): Whether to enable debug mode with more verbose logging.
    
    Returns:
        bool: True if successful, False otherwise.
    """
    if debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Debug mode enabled")
    
    try:
        # Initialize components
        logger.info("Initializing recommendation engine...")
        data_processor = DataProcessor()
        recommendation_engine = RecommendationEngine()
        
        # Get user data
        if username:
            logger.info(f"Generating recommendations for user: {username}")
            user_profile = UserProfile(username)
            user_data = user_profile.get_user_data()
            users_to_process = [user_data]
        else:
            logger.info("No username provided, processing sample users")
            # Get sample data or all users
            users_to_process = data_processor.get_sample_users()
        
        # Process each user and generate recommendations
        recommendations = {}
        for user_data in users_to_process:
            try:
                current_username = user_data.get('username', 'unknown_user')
                logger.info(f"Processing user: {current_username}")
                
                # Generate recommendations
                user_recommendation = recommendation_engine.generate_recommendation(user_data)
                
                # Add to results
                recommendations[current_username] = user_recommendation
                logger.info(f"Successfully generated recommendation for {current_username}")
            except Exception as e:
                logger.error(f"Error processing user {user_data.get('username', 'unknown')}: {str(e)}")
        
        # Save to JSON file
        output_path = Path(output_file)
        with open(output_path, 'w') as f:
            json.dump(
                {
                    "generated_at": datetime.now().isoformat(),
                    "recommendations": recommendations
                }, 
                f, 
                indent=2
            )
        
        logger.info(f"Successfully saved recommendations to {output_path.absolute()}")
        return True
    
    except Exception as e:
        logger.error(f"Error creating content plan: {str(e)}")
        return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate content recommendations and save to JSON")
    parser.add_argument("-u", "--username", help="Username to generate recommendations for")
    parser.add_argument("-o", "--output", default="content_plan.json", help="Output JSON file (default: content_plan.json)")
    parser.add_argument("-d", "--debug", action="store_true", help="Enable debug mode")
    
    args = parser.parse_args()
    
    if create_content_plan(args.username, args.output, args.debug):
        print(f"✅ Successfully created content plan at {args.output}")
    else:
        print(f"❌ Failed to create content plan. Check logs for details.")
        exit(1) 