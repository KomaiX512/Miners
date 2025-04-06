"""Module for managing R2 storage operations."""

import json
import logging
import boto3
from datetime import datetime
from config import R2_CONFIG, LOGGING_CONFIG

# Set up logging
logging.basicConfig(
    level=LOGGING_CONFIG['level'],
    format=LOGGING_CONFIG['format']
)
logger = logging.getLogger(__name__)

class R2StorageManager:
    """Class to handle R2 storage operations."""
    
    def __init__(self, config=R2_CONFIG):
        """Initialize with R2 configuration."""
        self.config = config
        self.client = self._create_client()
        
    def _create_client(self):
        """Create and return an S3 client configured for R2."""
        try:
            client = boto3.client(
                's3',
                endpoint_url=self.config['endpoint_url'],
                aws_access_key_id=self.config['aws_access_key_id'],
                aws_secret_access_key=self.config['aws_secret_access_key']
            )
            logger.info("Successfully created R2 client")
            return client
        except Exception as e:
            logger.error(f"Failed to create R2 client: {str(e)}")
            raise

    def save_username(self, username):
        """Save username to R2 storage."""
        try:
            # Create user folder path
            user_folder = f"Usernames/{username}/"
            
            # Create insta.json content
            data = {
                "username": username,
                "timestamp": datetime.now().isoformat()
            }
            
            # Upload to R2
            self.client.put_object(
                Bucket=self.config['bucket_name2'],
                Key=f"{user_folder}insta.json",
                Body=json.dumps(data),
                ContentType='application/json'
            )
            
            logger.info(f"Successfully saved username {username}")
            return True
        except Exception as e:
            logger.error(f"Error saving username: {str(e)}")
            return False

    def save_recommendations(self, username, recommendations):
        """Save recommendations to R2 storage."""
        try:
            # Create recommendations folder path
            folder = f"recommendation/{username}/"
            
            # Upload to R2
            self.client.put_object(
                Bucket=self.config['bucket_name'],
                Key=f"{folder}u_tmp.json",
                Body=json.dumps(recommendations),
                ContentType='application/json'
            )
            
            logger.info(f"Successfully saved recommendations for {username}")
            return True
        except Exception as e:
            logger.error(f"Error saving recommendations: {str(e)}")
            return False

    def save_image_prompts(self, username, prompts):
        """Save image prompts and captions to R2 storage."""
        try:
            # Create image prompts folder path
            folder = f"image_prompt_and_captions/{username}/"
            
            # Upload to R2
            self.client.put_object(
                Bucket=self.config['bucket_name'],
                Key=f"{folder}u1_tmp.json",
                Body=json.dumps(prompts),
                ContentType='application/json'
            )
            
            logger.info(f"Successfully saved image prompts for {username}")
            return True
        except Exception as e:
            logger.error(f"Error saving image prompts: {str(e)}")
            return False 