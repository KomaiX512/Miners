#!/usr/bin/env python3
"""Check the profile info in the tasks bucket."""

import json
import boto3
from botocore.client import Config
from config import R2_CONFIG

def check_profile_info(username="fentybeauty"):
    """Check profile info for a specific username."""
    # Initialize S3 client
    s3 = boto3.client(
        's3',
        endpoint_url=R2_CONFIG['endpoint_url'],
        aws_access_key_id=R2_CONFIG['aws_access_key_id'],
        aws_secret_access_key=R2_CONFIG['aws_secret_access_key'],
        config=Config(signature_version='s3v4')
    )
    
    try:
        # Get profile info from tasks bucket
        tasks_bucket = R2_CONFIG['bucket_name2']
        profile_key = f"ProfileInfo/{username}.json"
        
        response = s3.get_object(
            Bucket=tasks_bucket,
            Key=profile_key
        )
        
        # Parse and print profile info
        profile_info = json.loads(response['Body'].read())
        print(f"Profile info for {username}:")
        print(json.dumps(profile_info, indent=2))
        
        return True
    except Exception as e:
        print(f"Error checking profile info: {str(e)}")
        return False

if __name__ == "__main__":
    check_profile_info() 