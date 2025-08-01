import boto3
import logging
from config import R2_CONFIG
import json

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
                aws_secret_access_key=self.config['aws_secret_access_key'],
                region_name='auto'
            )
            logger.info("Successfully created R2 client")
            return client
        except Exception as e:
            logger.error(f"Failed to create R2 client: {str(e)}")
            raise

    def upload_file(self, key, file_obj, bucket='tasks'):
        """Upload file-like object to specified bucket"""
        try:
            file_obj.seek(0)  # Reset file position
            self.client.upload_fileobj(
                Fileobj=file_obj,
                Bucket=bucket,
                Key=key
            )
            logger.info(f"Uploaded {key} to {bucket}")
            return True
        except Exception as e:
            logger.error(f"Failed to upload {key} to {bucket}: {str(e)}")
            return False

    def put_object(self, key, content=None, bucket='tasks'):
        """Put an object into the specified bucket.
        
        Args:
            key (str): The key (filename) to use
            content (str, optional): Content to put in the object, if None creates an empty object (e.g., for directory markers)
            bucket (str): Target bucket name
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            params = {
                'Bucket': bucket,
                'Key': key
            }
            
            if content is not None:
                if isinstance(content, str):
                    params['Body'] = content
                else:
                    params['Body'] = json.dumps(content)
            
            self.client.put_object(**params)
            logger.info(f"Successfully put object at {key} in bucket {bucket}")
            return True
        except Exception as e:
            logger.error(f"Error putting object at {key} in bucket {bucket}: {str(e)}")
            return False
            
    def list_objects(self, prefix=None, bucket='tasks'):
        """List objects in the specified bucket, optionally filtered by prefix.
        
        Args:
            prefix (str, optional): Prefix to filter objects
            bucket (str): Target bucket name
            
        Returns:
            list: List of objects
        """
        try:
            params = {'Bucket': bucket}
            if prefix:
                params['Prefix'] = prefix
            response = self.client.list_objects_v2(**params)
            objects = response.get('Contents', [])
            logger.info(f"Found {len(objects)} objects in bucket {bucket} with prefix '{prefix or ''}'")
            return objects
        except Exception as e:
            logger.error(f"Error listing objects in bucket {bucket}: {str(e)}")
            return []
    
    def list_files(self, prefix, bucket='tasks'):
        """List files in R2 storage with given prefix.
        
        This method provides compatibility with the R2Storage interface.
        
        Args:
            prefix (str): Prefix to filter objects
            bucket (str): Target bucket name
            
        Returns:
            list: List of object keys
        """
        try:
            objects = self.list_objects(prefix=prefix, bucket=bucket)
            return [obj['Key'] for obj in objects]
        except Exception as e:
            logger.error(f"Error listing files with prefix {prefix} in bucket {bucket}: {str(e)}")
            return []