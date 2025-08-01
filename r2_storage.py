#!/usr/bin/env python3
"""
R2 storage handler for content plan exports
"""

import logging
import io
import os
import boto3
from botocore.exceptions import ClientError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('r2_storage')

class R2Storage:
    def __init__(self, mock_mode=False):
        """Initialize R2 storage client"""
        self.mock_mode = mock_mode
        
        try:
            if not mock_mode:
                # Initialize R2 client
                self.s3 = boto3.client(
                    's3',
                    endpoint_url='https://example.r2.cloudflarestorage.com',  # Replace with actual endpoint
                    aws_access_key_id='dummy_key',  # Replace with actual key
                    aws_secret_access_key='dummy_secret'  # Replace with actual secret
                )
                logger.info("R2 storage client initialized successfully")
            else:
                logger.info("R2 storage client initialized in mock mode")
        except Exception as e:
            logger.error(f"Failed to initialize R2 storage client: {str(e)}")
            if not mock_mode:
                raise
    
    def upload_file(self, key, file_obj, bucket):
        """Upload a file to R2 storage"""
        try:
            if self.mock_mode:
                # In mock mode, just log and return success
                logger.info(f"MOCK: Successfully uploaded file to {bucket}/{key}")
                return True
                
            self.s3.upload_fileobj(file_obj, bucket, key)
            logger.info(f"Successfully uploaded file to {bucket}/{key}")
            return True
        except ClientError as e:
            logger.error(f"Failed to upload file to {bucket}/{key}: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error uploading file to {bucket}/{key}: {str(e)}")
            return False
    
    def list_files(self, prefix, bucket):
        """List files in R2 storage with given prefix"""
        try:
            if self.mock_mode:
                # In mock mode, return an empty list
                logger.info(f"MOCK: Listing files with prefix {prefix} in bucket {bucket}")
                return []
                
            # Ensure the directory exists in the bucket or return empty list
            response = self.s3.list_objects_v2(
                Bucket=bucket,
                Prefix=prefix
            )
            
            if 'Contents' in response:
                return [obj['Key'] for obj in response['Contents']]
            
            logger.info(f"No objects found with prefix {prefix} in bucket {bucket}")
            return []
            
        except ClientError as e:
            logger.error(f"Failed to list files with prefix {prefix}: {str(e)}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error listing files with prefix {prefix}: {str(e)}")
            return []
    
    def _ensure_directory_exists(self, key, bucket):
        """Ensure a directory exists in the bucket"""
        # In S3/R2, directories don't really exist, but we can create an empty object
        # with a trailing slash to simulate a directory
        try:
            if not key.endswith('/'):
                key = key + '/'
                
            if self.mock_mode:
                logger.info(f"MOCK: Ensuring directory {key} exists in bucket {bucket}")
                return True
                
            self.s3.put_object(
                Bucket=bucket,
                Key=key,
                Body=''
            )
            logger.info(f"Ensured directory {key} exists in bucket {bucket}")
            return True
        except Exception as e:
            logger.error(f"Failed to ensure directory {key} exists: {str(e)}")
            return False 