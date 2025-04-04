"""Module for scraping Instagram profiles and uploading to R2 storage."""

import time
import json
import os
import logging
import boto3
from botocore.client import Config
from datetime import datetime
from apify_client import ApifyClient
from config import R2_CONFIG, LOGGING_CONFIG

# Set up logging
logging.basicConfig(
    level=LOGGING_CONFIG['level'],
    format=LOGGING_CONFIG['format']
)
logger = logging.getLogger(__name__)

# Apify API token
APIFY_API_TOKEN = "apify_api_88I8mu5LcmIjJa1fVUI3S3BvKGvNr60wvFPa"

class InstagramScraper:
    """Class for scraping Instagram profiles and uploading to R2 storage."""
    
    def __init__(self, api_token=APIFY_API_TOKEN, r2_config=R2_CONFIG):
        """Initialize with API token and R2 configuration."""
        self.api_token = api_token
        self.r2_config = r2_config
        
    def scrape_profile(self, username, results_limit=10):
        """
        Scrape Instagram profile using Apify.
        
        Args:
            username (str): Instagram username to scrape
            results_limit (int): Maximum number of results to fetch
        
        Returns:
            dict: Scraped data or None if failed
        """
        logger.info(f"Scraping Instagram profile: {username}")
        
        client = ApifyClient(self.api_token)
        
        run_input = {
            "usernames": [username],
            "resultsLimit": results_limit,
            "proxyConfig": {"useApifyProxy": True},
            "scrapeType": "posts"
        }
        
        try:
            actor = client.actor("apify/instagram-profile-scraper")
            run = actor.call(run_input=run_input)
            
            # Wait for scraping to complete
            logger.info(f"Waiting for scraping to complete for {username}")
            time.sleep(15)  # Increased wait time for more reliable results
            
            dataset = client.dataset(run["defaultDatasetId"])
            items = dataset.list_items().items
            
            if not items:
                logger.warning(f"No items found for {username} - account may be private or unavailable")
                return None
            else:
                logger.info(f"Successfully scraped {len(items)} items for {username}")
                return items
                
        except Exception as e:
            logger.error(f"Error occurred while scraping {username}: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return None
    
    def save_to_local_file(self, data, username):
        """
        Save scraped data to a local file.
        
        Args:
            data (dict): Scraped data
            username (str): Instagram username
        
        Returns:
            str: Path to the saved file or None if failed
        """
        if not data:
            logger.warning("No data to save to local file")
            return None
        
        # Create timestamp for unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{username}_{timestamp}.json"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            
            logger.info(f"Data saved to local file: {filename}")
            return filename
        
        except Exception as e:
            logger.error(f"Error saving data to local file: {str(e)}")
            return None
    
    def upload_to_r2(self, local_file_path, username):
        """
        Upload file to Cloudflare R2 storage.
        
        Args:
            local_file_path (str): Path to local file
            username (str): Instagram username
        
        Returns:
            str: Object key in R2 bucket or None if failed
        """
        if not local_file_path:
            logger.warning("No local file path provided for R2 upload")
            return None
        
        try:
            # Configure S3 client to use with R2
            s3 = boto3.client(
                's3',
                endpoint_url=self.r2_config['endpoint_url'],
                aws_access_key_id=self.r2_config['aws_access_key_id'],
                aws_secret_access_key=self.r2_config['aws_secret_access_key'],
                config=Config(signature_version='s3v4')
            )
            
            # Create a unique object key for the file in R2
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            object_key = f"{username}/{username}_{timestamp}.json"
            
            # Upload file to R2
            s3.upload_file(
                local_file_path, 
                self.r2_config['bucket_name'],
                object_key
            )
            
            logger.info(f"Successfully uploaded to R2 bucket {self.r2_config['bucket_name']} with key: {object_key}")
            
            # Clean up local file
            try:
                os.remove(local_file_path)
                logger.info(f"Removed local file: {local_file_path}")
            except Exception as e:
                logger.warning(f"Failed to remove local file {local_file_path}: {str(e)}")
            
            return object_key
        
        except Exception as e:
            logger.error(f"Error uploading to R2: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return None
    
    def scrape_and_upload(self, username, results_limit=10):
        """
        Scrape Instagram profile and upload to R2 in one operation.
        
        Args:
            username (str): Instagram username to scrape
            results_limit (int): Maximum number of results to fetch
        
        Returns:
            dict: Result with success status and object key
        """
        logger.info(f"Starting scrape and upload process for {username}")
        
        # Scrape profile
        data = self.scrape_profile(username, results_limit)
        
        if not data:
            logger.warning(f"No data retrieved for {username}")
            return {"success": False, "message": "Failed to scrape profile"}
        
        # Save to local file
        local_file_path = self.save_to_local_file(data, username)
        
        if not local_file_path:
            logger.warning(f"Failed to save data to local file for {username}")
            return {"success": False, "message": "Failed to save data to local file"}
        
        # Upload to R2
        object_key = self.upload_to_r2(local_file_path, username)
        
        if not object_key:
            logger.warning(f"Failed to upload data to R2 for {username}")
            return {"success": False, "message": "Failed to upload data to R2"}
        
        logger.info(f"Successfully completed scrape and upload process for {username}")
        return {
            "success": True, 
            "message": "Successfully scraped and uploaded data",
            "object_key": object_key
        }


def test_instagram_scraper():
    """Test the Instagram scraper functionality."""
    try:
        # Create scraper
        scraper = InstagramScraper()
        
        # Test username
        test_username = "humansofny"
        
        # Scrape and upload
        result = scraper.scrape_and_upload(test_username, results_limit=5)
        
        if result["success"]:
            logger.info(f"Test successful: {result['message']}")
            logger.info(f"Object key: {result['object_key']}")
            return True
        else:
            logger.warning(f"Test failed: {result['message']}")
            return False
            
    except Exception as e:
        logger.error(f"Test failed with exception: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False


if __name__ == "__main__":
    # Test the Instagram scraper
    success = test_instagram_scraper()
    print(f"Instagram scraper test {'successful' if success else 'failed'}")