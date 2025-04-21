#!/usr/bin/env python3
"""Test script to verify redundancy check for profile exports."""

import logging
import json
import time
import boto3
from botocore.client import Config
from datetime import datetime
from main import ContentRecommendationSystem
from instagram_scraper import InstagramScraper
from config import R2_CONFIG

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_redundancy_check():
    """Test that redundancy check prevents duplicate profile exports."""
    try:
        print("=== Testing Redundancy Check for Profile Exports ===")
        
        # Create instances
        cms = ContentRecommendationSystem()
        scraper = InstagramScraper()
        
        # Test username with timestamp to ensure uniqueness
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        test_username = f"redundancy_test_{timestamp}"
        
        # Create S3 client for direct operations
        s3_client = boto3.client(
            's3',
            endpoint_url=R2_CONFIG['endpoint_url'],
            aws_access_key_id=R2_CONFIG['aws_access_key_id'],
            aws_secret_access_key=R2_CONFIG['aws_secret_access_key'],
            config=Config(signature_version='s3v4')
        )
        
        # Delete any existing test file first
        tasks_bucket = R2_CONFIG['bucket_name2']
        profile_key = f"ProfileInfo/{test_username}.json"
        try:
            # Try to delete the file if it exists
            print(f"Cleaning up any existing test file: {profile_key}")
            s3_client.delete_object(Bucket=tasks_bucket, Key=profile_key)
        except Exception as e:
            print(f"Note: Could not delete file (may not exist): {str(e)}")
        
        # Test data
        test_profile = {
            "username": test_username,
            "fullName": "Redundancy Test User",
            "biography": "Testing profile redundancy checks",
            "followersCount": 5000,
            "followsCount": 500,
            "profilePicUrl": "https://example.com/profile.jpg",
            "profilePicUrlHD": "https://example.com/profile_hd.jpg",
            "private": False,
            "verified": True
        }
        
        # FIRST EXPORT - Should succeed and upload
        print("\n1. First export attempt (should upload):")
        result1 = cms.export_profile_info(test_profile, test_username)
        print(f"First export result: {'Success' if result1 else 'Failed'}")
        
        # Wait a moment to ensure consistency
        time.sleep(2)
        
        # SECOND EXPORT - Should detect existing file and skip
        print("\n2. Second export attempt (should skip):")
        test_profile["fullName"] = "Updated Name - Should Not Be Uploaded"
        result2 = cms.export_profile_info(test_profile, test_username)
        print(f"Second export result: {'Success' if result2 else 'Failed'}")
        
        # Wait a moment
        time.sleep(2)
        
        # THIRD EXPORT - Try with Instagram scraper instead of CMS
        print("\n3. Instagram scraper export attempt (should skip):")
        mock_profile = [{
            "username": test_username,
            "fullName": "Scraper Updated Name - Should Not Be Uploaded",
            "biography": "Testing profile redundancy with scraper",
            "followersCount": 8000,
            "followsCount": 800,
            "profilePicUrl": "https://example.com/profile2.jpg",
            "profilePicUrlHD": "https://example.com/profile2_hd.jpg",
            "private": False,
            "verified": True
        }]
        
        short_info = scraper.extract_short_profile_info(mock_profile)
        result3 = scraper.upload_short_profile_to_tasks(short_info)
        print(f"Scraper export result: {'Success' if result3 else 'Failed'}")
        
        # VERIFICATION - Get the file and check its contents
        # This will tell us if any of the updates were incorrectly applied
        print("\n4. Verifying file contents:")
        
        try:
            # Get the file content
            response = s3_client.get_object(Bucket=tasks_bucket, Key=profile_key)
            content = json.loads(response['Body'].read().decode('utf-8'))
            
            print(f"Profile file content: {json.dumps(content, indent=2)}")
            
            # The fullName should be "Redundancy Test User" from the first upload
            # If it's either of the updated names, our redundancy check failed
            if content.get("fullName") == "Redundancy Test User":
                print("SUCCESS: Redundancy check is working correctly! Only the first upload was saved.")
                test_result = True
            else:
                print(f"FAILURE: File was updated when it shouldn't have been. Current name: {content.get('fullName')}")
                test_result = False
                
            # Clean up the test file
            print(f"\nCleaning up test file: {profile_key}")
            s3_client.delete_object(Bucket=tasks_bucket, Key=profile_key)
            
            return test_result
            
        except Exception as e:
            print(f"Error retrieving or cleaning up file: {str(e)}")
            return False
            
    except Exception as e:
        print(f"Error in test: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_redundancy_check()
    print(f"\nTest Result: {'PASSED' if success else 'FAILED'}") 