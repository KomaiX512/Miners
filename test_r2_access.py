#!/usr/bin/env python3
"""Script to test direct R2 bucket access."""

import boto3
import json
import logging
from botocore.client import Config
from datetime import datetime
from config import R2_CONFIG

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_r2_access():
    """Test direct access to R2 buckets."""
    try:
        # Initialize S3 client with R2 configuration
        client = boto3.client(
            's3',
            endpoint_url=R2_CONFIG['endpoint_url'],
            aws_access_key_id=R2_CONFIG['aws_access_key_id'],
            aws_secret_access_key=R2_CONFIG['aws_secret_access_key'],
            config=Config(signature_version='s3v4')
        )
        
        # List all buckets
        response = client.list_buckets()
        buckets = [bucket['Name'] for bucket in response['Buckets']]
        logger.info(f"Available buckets: {buckets}")
        
        # List buckets from config
        logger.info(f"Buckets in config: structuredb={R2_CONFIG['bucket_name']}, miner={R2_CONFIG['personal_bucket_name']}, tasks={R2_CONFIG['bucket_name2']}")
        
        # Test write to tasks bucket
        tasks_bucket = R2_CONFIG['bucket_name2']
        test_key = f"ProfileInfo/test_direct_access_{datetime.now().strftime('%Y%m%d%H%M%S')}.json"
        
        # Sample profile data
        test_data = {
            "username": "test_direct_access",
            "fullName": "Test Direct Access",
            "biography": "Testing direct R2 access",
            "followersCount": 5000,
            "followsCount": 500,
            "profilePicUrl": "https://example.com/pic.jpg",
            "profilePicUrlHD": "https://example.com/pic_hd.jpg",
            "private": False,
            "verified": True,
            "extractedAt": datetime.now().isoformat()
        }
        
        # Put the object
        logger.info(f"Attempting to put object at {test_key} in bucket {tasks_bucket}")
        put_response = client.put_object(
            Bucket=tasks_bucket,
            Key=test_key,
            Body=json.dumps(test_data, indent=2),
            ContentType='application/json'
        )
        logger.info(f"Put object response: {put_response}")
        
        # List objects to verify it was created
        list_response = client.list_objects_v2(
            Bucket=tasks_bucket,
            Prefix="ProfileInfo/"
        )
        
        if 'Contents' in list_response:
            objects = [obj['Key'] for obj in list_response['Contents']]
            logger.info(f"Objects in ProfileInfo/: {objects}")
            
            if test_key in objects:
                logger.info(f"SUCCESS: Test object {test_key} found in bucket!")
            else:
                logger.warning(f"Test object {test_key} not found in bucket.")
        else:
            logger.warning("No objects found in ProfileInfo/ prefix")
            
        return True
    except Exception as e:
        logger.error(f"Error testing R2 access: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_r2_access()
    print(f"R2 access test {'successful' if success else 'failed'}") 