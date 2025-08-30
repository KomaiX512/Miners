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
        
    def _clean_username(self, username):
        """Remove '@' symbol and other special characters from username for export compatibility."""
        if not username:
            return username
        # Remove '@' symbol and any other special characters that cause retrieval issues
        cleaned = username.replace('@', '').strip()
        return cleaned
    
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
        """Get and parse JSON data from an object with comprehensive error handling."""
        try:
            response = self.get_object(key)
            content = response['Body'].read()
            
            # CRITICAL FIX: Handle corrupted files - detect non-UTF-8 content
            try:
                content_str = content.decode('utf-8')
            except UnicodeDecodeError as unicode_error:
                logger.error(f"CORRUPTED FILE DETECTED: {key} - {str(unicode_error)}")
                logger.error(f"File contains invalid UTF-8 bytes at position {unicode_error.start}")
                
                # Delete corrupted file to prevent infinite processing loops
                try:
                    self.client.delete_object(
                        Bucket=self.config['bucket_name'],
                        Key=key
                    )
                    logger.info(f"✅ Deleted corrupted file: {key}")
                except Exception as delete_error:
                    logger.error(f"Failed to delete corrupted file {key}: {str(delete_error)}")
                    
                return None
            
            # Validate JSON content before parsing
            if not content_str.strip():
                logger.warning(f"Empty content found for key: {key}")
                return None
                
            try:
                data = json.loads(content_str)
                logger.info(f"Successfully retrieved and parsed JSON data from {key}")
                return data
            except json.JSONDecodeError as json_error:
                logger.error(f"JSON decode error for {key}: {str(json_error)}")
                logger.error(f"Content preview: {content_str[:200]}...")
                
                # CRITICAL FIX: Delete invalid JSON files to prevent infinite loops
                try:
                    self.client.delete_object(
                        Bucket=self.config['bucket_name'],
                        Key=key
                    )
                    logger.info(f"✅ Deleted invalid JSON file: {key}")
                except Exception as delete_error:
                    logger.error(f"Failed to delete invalid JSON file {key}: {str(delete_error)}")
                    
                return None
                
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
    
    def get_social_media_data(self, primary_username, platform="instagram"):
        """
        Get social media data for a primary username and its competitors.
        
        Args:
            primary_username (str): The primary username (e.g., 'maccosmetics')
            platform (str): The social media platform (instagram or twitter)
            
        Returns:
            list: Combined list of post data with PRIMARY USER'S DATA FIRST, or None if failed
        """
        try:
            # FIXED: Use consistent schema across platforms - platform/username/
            # NEW SCHEMA: platform/username/ for both Twitter and Instagram
            prefix = f"{platform.lower()}/{primary_username}/"
                
            logger.info(f"Retrieving {platform} data for {primary_username} with prefix '{prefix}'")
            
            # List all objects under the primary username's directory
            objects = self.list_objects(prefix=prefix)
            if not objects:
                logger.warning(f"No objects found under prefix '{prefix}'")
                return None
            
            # CRITICAL FIX: Separate primary and competitor data to prevent contamination
            primary_key = f"{prefix}{primary_username}.json"
            primary_data = None
            competitor_data = []
            
            # First, retrieve primary user data ONLY
            for obj in objects:
                key = obj['Key']
                if key == primary_key:
                    data = self.get_json_data(key)
                    if data:
                        primary_data = data
                        logger.info(f"✅ Found primary user data: {primary_key}")
                        break
            
            if not primary_data:
                logger.error(f"❌ CRITICAL: Primary file '{primary_key}' not found")
                return None
            
            # CRITICAL FIX: Handle both list and dict data structures from JSON files
            # Processing methods expect dictionary with profile info, but JSON files may contain lists of posts
            if not primary_data:
                logger.warning(f"No valid primary data retrieved for {primary_username}")
                return None
            
            # If primary_data is a list (array of posts), convert to expected dict structure
            if isinstance(primary_data, list):
                logger.info(f"Converting list data structure to expected dict format for {primary_username}")
                # Extract profile info from first post if available, or create minimal structure
                if primary_data and len(primary_data) > 0 and isinstance(primary_data[0], dict):
                    first_post = primary_data[0]
                    # Create expected structure with profile info and posts
                    structured_data = {
                        'username': primary_username,
                        'posts': primary_data,
                        # Extract profile fields if available in posts
                        'profile': {
                            'username': primary_username,
                            'followerCount': first_post.get('followerCount', 0),
                            'followingCount': first_post.get('followingCount', 0),
                            'postCount': len(primary_data)
                        }
                    }
                    # Add any other profile fields found in the first post
                    for key, value in first_post.items():
                        if key not in ['text', 'timestamp', 'likes', 'comments', 'shares'] and key not in structured_data:
                            structured_data[key] = value
                else:
                    # Fallback: create minimal structure
                    structured_data = {
                        'username': primary_username,
                        'posts': primary_data if primary_data else [],
                        'profile': {'username': primary_username}
                    }
                logger.info(f"✅ CONVERTED LIST TO DICT: {len(primary_data)} posts for {primary_username}")
                return structured_data
            else:
                # Data is already a dict, return as-is
                logger.info(f"✅ DICT STRUCTURE CONFIRMED for {primary_username}")
                return primary_data
            
        except Exception as e:
            logger.error(f"Error retrieving social media data for {primary_username}: {str(e)}")
            return None
    
    def get_twitter_data(self, primary_username):
        """
        Get Twitter data for a primary username and its competitors.
        
        Args:
            primary_username (str): The primary Twitter username
            
        Returns:
            list: Combined list of tweet data from primary and competitor files, or None if failed
        """
        return self.get_social_media_data(primary_username, platform="twitter")

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

    def export_recommendations(self, username, recommendations, index=1, platform="instagram"):
        """
        Export recommendations to R2 storage with appropriate directory structure.
        
        Args:
            username (str): The username to export recommendations for
            recommendations (dict): Recommendations data
            index (int, optional): Index for the recommendation file
            platform (str): Social media platform (instagram or twitter)
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if not username or not recommendations:
                logger.warning("Invalid username or recommendations for export")
                return False
            
            # Define the key (path) for the recommendations with platform support
            key = f"recommendations/{platform.lower()}/{self._clean_username(username)}/recommendation_{index}.json"
            
            # Add platform information to recommendations data
            if isinstance(recommendations, dict):
                recommendations['platform'] = platform.lower()
                recommendations['username'] = self._clean_username(username)
            
            logger.info(f"Exporting {platform} recommendations for {self._clean_username(username)} to {key}")
            return self.put_object(key, content=recommendations)
        except Exception as e:
            logger.error(f"Error exporting recommendations for {self._clean_username(username)}: {str(e)}")
            return False
    
    def export_competitor_analysis(self, username, analysis, platform="instagram"):
        """
        Export competitor analysis to R2 storage with appropriate directory structure.
        
        Args:
            username (str): The username to export analysis for
            analysis (dict): Competitor analysis data
            platform (str): Social media platform (instagram or twitter)
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if not username or not analysis:
                logger.warning("Invalid username or analysis for export")
                return False
            
            # Define the key (path) for the analysis with platform support
            key = f"competitor_analysis/{platform.lower()}/{self._clean_username(username)}/analysis.json"
            
            # Add platform information to analysis data
            if isinstance(analysis, dict):
                analysis['platform'] = platform.lower()
                analysis['username'] = self._clean_username(username)
            
            logger.info(f"Exporting {platform} competitor analysis for {self._clean_username(username)} to {key}")
            return self.put_object(key, content=analysis)
        except Exception as e:
            logger.error(f"Error exporting competitor analysis for {self._clean_username(username)}: {str(e)}")
            return False
    
    def export_engagement_strategies(self, username, strategies, platform="instagram"):
        """
        Export engagement strategies to R2 storage with appropriate directory structure.
        
        Args:
            username (str): The username to export strategies for
            strategies (dict): Engagement strategies data
            platform (str): Social media platform (instagram or twitter)
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if not username or not strategies:
                logger.warning("Invalid username or strategies for export")
                return False
            
            # Define the key (path) for the strategies with platform support
            key = f"engagement_strategies/{platform.lower()}/{self._clean_username(username)}/strategies.json"
            
            # Add platform information to strategies data
            if isinstance(strategies, dict):
                strategies['platform'] = platform.lower()
                strategies['username'] = self._clean_username(username)
            elif isinstance(strategies, list):
                # If strategies is a list, wrap it in a dict with metadata
                strategies = {
                    'strategies': strategies,
                    'platform': platform.lower(),
                    'username': self._clean_username(username)
                }
            
            logger.info(f"Exporting {platform} engagement strategies for {self._clean_username(username)} to {key}")
            return self.put_object(key, content=strategies)
        except Exception as e:
            logger.error(f"Error exporting engagement strategies for {self._clean_username(username)}: {str(e)}")
            return False
    
    def export_next_post(self, username, post_data, platform="instagram"):
        """
        Export next post prediction to R2 storage with appropriate directory structure.
        
        Args:
            username (str): The username to export post for
            post_data (dict): Next post prediction data
            platform (str): Social media platform (instagram or twitter)
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if not username or not post_data:
                logger.warning("Invalid username or post data for export")
                return False
            
            # Define the key (path) for the next post with platform support
            key = f"next_posts/{platform.lower()}/{self._clean_username(username)}/next_post.json"
            
            # Add platform information to post data
            if isinstance(post_data, dict):
                post_data['platform'] = platform.lower()
                post_data['username'] = self._clean_username(username)
            
            logger.info(f"Exporting {platform} next post prediction for {self._clean_username(username)} to {key}")
            return self.put_object(key, content=post_data)
        except Exception as e:
            logger.error(f"Error exporting next post prediction for {self._clean_username(username)}: {str(e)}")
            return False

# Test functions removed for production use