"""Module for retrieving data from R2 storage."""

import json
import logging
import boto3
from tenacity import retry, stop_after_attempt, wait_exponential
from config import R2_CONFIG, LOGGING_CONFIG

# Set up logging
logging.basicConfig(
    level=LOGGING_CONFIG['level'],
    format=LOGGING_CONFIG['format']
)
logger = logging.getLogger(__name__)

class R2DataRetriever:
    """Class to handle data retrieval from R2 storage."""
    
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
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def list_objects(self, prefix=None):
        """List objects in the R2 bucket, optionally filtered by prefix."""
        try:
            params = {'Bucket': self.config['bucket_name']}
            if prefix:
                params['Prefix'] = prefix
            response = self.client.list_objects_v2(**params)
            objects = response.get('Contents', [])
            logger.info(f"Found {len(objects)} objects in bucket with prefix '{prefix or ''}'")
            return objects
        except Exception as e:
            logger.error(f"Error listing objects: {str(e)}")
            raise
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def get_object(self, key):
        """Get an object from the R2 bucket."""
        try:
            logger.info(f"Retrieving object: {key}")
            response = self.client.get_object(
                Bucket=self.config['bucket_name'],
                Key=key
            )
            return response
        except Exception as e:
            logger.error(f"Error retrieving object {key}: {str(e)}")
            raise
    
    def get_json_data(self, key):
        """Get and parse JSON data from an object."""
        try:
            response = self.get_object(key)
            content = response['Body'].read()
            data = json.loads(content)
            logger.info(f"Successfully retrieved and parsed JSON data from {key}")
            return data
        except Exception as e:
            logger.error(f"Error parsing JSON from {key}: {str(e)}")
            return None
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def put_object(self, key, content=None):
        """Put an object into the R2 bucket.
        
        Args:
            key (str): The key (filename) to use in R2
            content (str, optional): Content to put in the object, if None creates an empty object (e.g., for directory markers)
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            params = {
                'Bucket': self.config['bucket_name'],
                'Key': key
            }
            
            if content is not None:
                if isinstance(content, str):
                    params['Body'] = content
                else:
                    params['Body'] = json.dumps(content)
            
            self.client.put_object(**params)
            logger.info(f"Successfully put object at {key}")
            return True
        except Exception as e:
            logger.error(f"Error putting object at {key}: {str(e)}")
            return False
    
    def get_social_media_data(self, primary_username):
        """
        Get social media data for a primary username and its competitors.
        
        Args:
            primary_username (str): The primary Instagram username (e.g., 'maccosmetics')
            
        Returns:
            list: Combined list of post data from primary and competitor files, or None if failed
        """
        try:
            # Define the prefix for the primary username's directory
            prefix = f"{primary_username}/"
            logger.info(f"Retrieving social media data for {primary_username} with prefix '{prefix}'")
            
            # List all objects under the primary username's directory
            objects = self.list_objects(prefix=prefix)
            if not objects:
                logger.warning(f"No objects found under prefix '{prefix}'")
                return None
            
            combined_data = []
            primary_key = f"{primary_username}/{primary_username}.json"
            found_primary = False
            
            # Retrieve and combine data from all relevant files
            for obj in objects:
                key = obj['Key']
                if key.endswith('.json'):  # Only process JSON files
                    data = self.get_json_data(key)
                    if data:
                        if key == primary_key:
                            found_primary = True
                        combined_data.extend(data)  # Assuming data is a list of posts
            
            if not found_primary:
                logger.warning(f"Primary file '{primary_key}' not found")
                return None
                
            if not combined_data:
                logger.warning(f"No valid data retrieved for {primary_username}")
                return None
                
            logger.info(f"Successfully retrieved {len(combined_data)} posts for {primary_username} and competitors")
            return combined_data
            
        except Exception as e:
            logger.error(f"Error retrieving social media data for {primary_username}: {str(e)}")
            return None

    def upload_file(self, key, file_obj):
        """
        Upload a file to R2 storage.
        
        Args:
            key: The key (filename) to use in R2
            file_obj: File object to upload
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.client.upload_fileobj(file_obj, self.config['bucket_name'], key)
            logger.info(f"Successfully uploaded file to {key}")
            return True
        except Exception as e:
            logger.error(f"Error uploading file to {key}: {str(e)}")
            return False


# Function to test the data retrieval
def test_connection():
    """Test connection to R2 and multi-file retrieval."""
    try:
        retriever = R2DataRetriever()
        # Test with a sample primary username
        primary_username = "maccosmetics"
        logger.info(f"Testing retrieval for primary username: {primary_username}")
        
        data = retriever.get_social_media_data(primary_username)
        if data:
            logger.info(f"Successfully retrieved {len(data)} posts for {primary_username}")
            return True
        else:
            logger.warning(f"No data retrieved for {primary_username}")
            return False
            
    except Exception as e:
        logger.error(f"Test connection failed: {str(e)}")
        return False


if __name__ == "__main__":
    # Test the connection and data retrieval
    success = test_connection()
    print(f"Connection test {'successful' if success else 'failed'}")