#!/usr/bin/env python3
"""Test script to check profile info export pipeline."""

import logging
import json
import time
import boto3
from botocore.client import Config
from main import ContentRecommendationSystem
from instagram_scraper import InstagramScraper
from datetime import datetime
from config import R2_CONFIG

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_profile_pipeline():
    """Test profile info export pipeline."""
    try:
        print("=== Starting Profile Pipeline Test ===")
        
        # Create scraper and CMS instances
        instagram_scraper = InstagramScraper()
        cms = ContentRecommendationSystem()
        
        # Test username
        test_username = "test_profile_pipeline"
        
        # 1. Test InstagramScraper extract_short_profile_info and upload_short_profile_to_tasks methods
        print("\n=== Testing InstagramScraper Profile Export ===")
        
        # Create a mock profile to simulate scraped data
        mock_profile = [{
            "username": test_username,
            "fullName": "Test Profile Pipeline",
            "biography": "This is a test profile for testing the profile info export pipeline",
            "followersCount": 15000,
            "followsCount": 800,
            "profilePicUrl": "https://example.com/profile.jpg",
            "profilePicUrlHD": "https://example.com/profile_hd.jpg",
            "private": False,
            "verified": True
        }]
        
        # Extract and upload short profile info
        short_info = instagram_scraper.extract_short_profile_info(mock_profile)
        if short_info:
            print(f"Successfully extracted short profile info: {json.dumps(short_info, indent=2)}")
            
            # Upload to tasks bucket
            result = instagram_scraper.upload_short_profile_to_tasks(short_info)
            if result:
                print(f"Successfully uploaded short profile info to tasks/ProfileInfo/{test_username}.json")
            else:
                print("Failed to upload short profile info to tasks bucket")
                return False
        else:
            print("Failed to extract short profile info")
            return False
            
        # Wait a moment to ensure consistency
        time.sleep(2)
        
        # 2. Test ContentRecommendationSystem export_profile_info method
        print("\n=== Testing ContentRecommendationSystem Profile Export ===")
        
        # Create a mock profile data with slightly different values to confirm it updates
        cms_profile = {
            "username": test_username,
            "fullName": "CMS Test Profile",
            "biography": "This profile was exported by the ContentRecommendationSystem",
            "followersCount": 20000,
            "followsCount": 1000,
            "profilePicUrl": "https://example.com/cms_profile.jpg",
            "profilePicUrlHD": "https://example.com/cms_profile_hd.jpg",
            "private": False,
            "verified": True
        }
        
        # Export profile info
        cms_result = cms.export_profile_info(cms_profile, test_username)
        if cms_result:
            print(f"Successfully exported profile info via CMS to tasks/ProfileInfo/{test_username}.json")
        else:
            print("Failed to export profile info via CMS")
            return False
            
        # Wait longer to ensure consistency
        print("Waiting 5 seconds for R2 consistency...")
        time.sleep(5)
        
        # 3. Verify the profile info was exported correctly
        print("\n=== Verifying Exported Profile Info ===")
        
        # Use direct boto3 call to verify
        s3_client = boto3.client(
            's3',
            endpoint_url=R2_CONFIG['endpoint_url'],
            aws_access_key_id=R2_CONFIG['aws_access_key_id'],
            aws_secret_access_key=R2_CONFIG['aws_secret_access_key'],
            config=Config(signature_version='s3v4')
        )
        
        # List objects in the ProfileInfo/ prefix
        try:
            tasks_bucket = R2_CONFIG['bucket_name2']
            list_response = s3_client.list_objects_v2(
                Bucket=tasks_bucket,
                Prefix="ProfileInfo/"
            )
            
            if 'Contents' in list_response:
                objects = [obj['Key'] for obj in list_response['Contents']]
                print(f"Objects in ProfileInfo/ directory: {objects}")
                
                # Look for our test profile
                test_profile_key = f"ProfileInfo/{test_username}.json"
                if test_profile_key in objects:
                    print(f"Found test profile: {test_profile_key}")
                    
                    # Try to get the content to verify it was updated properly
                    response = s3_client.get_object(
                        Bucket=tasks_bucket,
                        Key=test_profile_key
                    )
                    
                    content = json.loads(response['Body'].read().decode('utf-8'))
                    print(f"Profile content: {json.dumps(content, indent=2)}")
                    
                    # Verify the content was updated with the CMS values
                    if content.get('fullName') == "CMS Test Profile":
                        print("Successfully verified the profile was updated by CMS")
                    else:
                        print("Profile was not updated with CMS values")
                    
                    print("\n=== Test Completed Successfully ===")
                    return True
                else:
                    print(f"Could not find test profile: {test_profile_key}")
                    return False
            else:
                print("No objects found in ProfileInfo/ prefix")
                return False
        except Exception as e:
            print(f"Error verifying exported profile info: {str(e)}")
            return False
    except Exception as e:
        print(f"Error in test_profile_pipeline: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_profile_pipeline()
    print(f"\nFinal Result: Test {'PASSED' if success else 'FAILED'}") 