#!/usr/bin/env python3
"""Main script for competitive insight generation and social media analysis."""

import os
import sys
import json
import logging
import argparse
from datetime import datetime

from competitive_insight_engine import CompetitiveInsightEngine
from config import LOGGING_CONFIG

# Set up logging
logging.basicConfig(
    level=LOGGING_CONFIG['level'],
    format=LOGGING_CONFIG['format']
)
logger = logging.getLogger(__name__)

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Generate competitive insights for social media profiles.')
    parser.add_argument('--profiles_dir', type=str, default='profiles',
                        help='Directory containing profile JSON files')
    parser.add_argument('--output_dir', type=str, default='output',
                        help='Directory to save output JSON files')
    parser.add_argument('--primary_username', type=str,
                        help='Primary username to analyze (if not specified, first profile is used)')
    parser.add_argument('--query', type=str, default='competitive analysis',
                        help='Query for RAG implementation')
    parser.add_argument('--test', action='store_true',
                        help='Run in test mode with sample data')
    return parser.parse_args()

def ensure_dir(directory):
    """Ensure directory exists."""
    if not os.path.exists(directory):
        os.makedirs(directory)
        logger.info(f"Created directory: {directory}")

def save_output(results, output_dir, primary_username):
    """Save results to output directory."""
    ensure_dir(output_dir)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = os.path.join(output_dir, f"{primary_username}_insights_{timestamp}.json")
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Saved results to {output_file}")
    return output_file

def run_test_mode():
    """Run with sample data for testing."""
    logger.info("Running in test mode with sample data")
    engine = CompetitiveInsightEngine()
    
    # Import the test function directly
    from competitive_insight_engine import test_competitive_insight_engine
    success = test_competitive_insight_engine()
    
            if success:
        logger.info("Test completed successfully")
        return 0
            else:
        logger.error("Test failed")
                return 1
            
def main():
    """Main function."""
    args = parse_arguments()
    
    if args.test:
        return run_test_mode()
    
    # Initialize engine
    engine = CompetitiveInsightEngine()
    
    # Load profile data
    logger.info(f"Loading profiles from {args.profiles_dir}")
    profile_data, posts, primary_username, secondary_usernames = engine.load_json_profiles(args.profiles_dir)
    
    if not profile_data or not posts:
        logger.error("Failed to load profile data")
            return 1

    # Override primary username if specified
    if args.primary_username:
        if args.primary_username in profile_data:
            primary_username = args.primary_username
            # Reorder secondary usernames
            secondary_usernames = [u for u in profile_data.keys() if u != primary_username]
            logger.info(f"Using specified primary username: {primary_username}")
                else:
            logger.warning(f"Specified primary username {args.primary_username} not found in profiles")
    
    # Generate insights
    logger.info(f"Generating insights for {primary_username} with {len(secondary_usernames)} competitors")
    results = engine.analyze_profiles(
        primary_username,
        secondary_usernames,
        profile_data,
        posts,
        args.query
    )
    
    if not results:
        logger.error("Failed to generate insights")
        return 1
    
    # Save output
    output_file = save_output(results, args.output_dir, primary_username)
    
    # Print summary
    print(f"\nInsights for {primary_username} generated successfully!")
    print(f"Analyzed {len(secondary_usernames)} competitors: {', '.join(secondary_usernames)}")
    print(f"Results saved to: {output_file}")
    
    # Display key insights
    try:
        print("\nSUMMARY:")
        print("=========")
        
        # Account info
        primary_info = results['account_info'][primary_username]
        print(f"Primary Account: {primary_username}")
        print(f"Followers: {primary_info['followers']:,}")
        print(f"Category: {primary_info['category']}")
        print(f"Bio: {primary_info['bio'][:100]}{'...' if len(primary_info['bio']) > 100 else ''}")
        
        # Strategies
        print("\nKey Strategies:")
        strategies = results['strategies']
        if isinstance(strategies, str):
            # Print first 200 chars with ellipsis if longer
            print(f"{strategies[:200]}{'...' if len(strategies) > 200 else ''}")
        
        # Next post
        next_post = results['next_post']
        print("\nNext Post:")
        print(f"Caption: {next_post['caption'][:100]}{'...' if len(next_post['caption']) > 100 else ''}")
        print(f"Hashtags: {' '.join(next_post['hashtags'][:5])}{' ...' if len(next_post['hashtags']) > 5 else ''}")
        print(f"Call to action: {next_post['call_to_action']}")
        
        print("\nFor complete insights, review the output JSON file.")
    except Exception as e:
        logger.error(f"Error displaying summary: {str(e)}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())