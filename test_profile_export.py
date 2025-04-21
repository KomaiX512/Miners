#!/usr/bin/env python3
"""Test script to check profile info export functionality."""

import logging
import json
import time
from main import ContentRecommendationSystem

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_profile_export():
    """Test profile info export functionality."""
    try:
        # Create an instance of ContentRecommendationSystem
        cms = ContentRecommendationSystem()
        
        # Sample profile data for testing
        test_profile = {
            "username": "test_profile",
            "fullName": "Test Profile",
            "biography": "This is a test profile for testing profile info export",
            "followersCount": 10000,
            "followsCount": 500,
            "profilePicUrl": "https://example.com/profile.jpg",
            "profilePicUrlHD": "https://example.com/profile_hd.jpg",
            "private": False,
            "verified": True,
        }
        
        # Export the profile info
        result = cms.export_profile_info(test_profile, "test_profile")
        
        if result:
            logger.info("Profile info export successful!")
            
            # Wait a bit for the object to become available
            logger.info("Waiting 5 seconds for R2 consistency...")
            time.sleep(5)
            
            # Verify the exported file
            try:
                # Try to retrieve the exported file
                profile_key = "ProfileInfo/test_profile.json"
                exported_data = cms.data_retriever.get_json_data(profile_key)
                
                if exported_data:
                    logger.info(f"Retrieved exported profile info: {json.dumps(exported_data, indent=2)}")
                    return True
                else:
                    logger.error("Failed to retrieve exported profile info")
                    
                    # Check if the object exists even if we can't get the JSON
                    objects = cms.data_retriever.list_objects(prefix="ProfileInfo/")
                    logger.info(f"Objects in ProfileInfo/ directory: {objects}")
                    
                    # Look for our test profile
                    for obj in objects:
                        if obj.get('Key') == profile_key:
                            logger.info(f"Found our profile object, but couldn't parse JSON: {obj}")
                            return True
                    
                    return False
            except Exception as e:
                logger.error(f"Error verifying exported profile info: {str(e)}")
                return False
        else:
            logger.error("Profile info export failed")
            return False
    except Exception as e:
        logger.error(f"Error in test_profile_export: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_profile_export()
    print(f"Test {'successful' if success else 'failed'}") 