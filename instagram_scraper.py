"""Module for scraping Instagram profiles and uploading to R2 storage."""
import time
import json
import os
import logging
import shutil
import boto3
from botocore.client import Config
from botocore.exceptions import ClientError
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
        self.r2_config = r2_config  # Assumes R2_CONFIG is set for "structuredb"
        # Initialize S3 client
        self.s3 = boto3.client(
            's3',
            endpoint_url=self.r2_config['endpoint_url'],
            aws_access_key_id=self.r2_config['aws_access_key_id'],
            aws_secret_access_key=self.r2_config['aws_secret_access_key'],
            config=Config(signature_version='s3v4')
        )
    
    def scrape_profile(self, username, results_limit=10):
        """
        Scrape Instagram profile using Apify.
        
        Args:
            username (str): Instagram username to scrape
            results_limit (int): Maximum number of results to fetch
        
        Returns:
            list: Scraped data or None if failed
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
            
            logger.info(f"Waiting for scraping to complete for {username}")
            time.sleep(15)  # Wait for reliable results
            
            dataset = client.dataset(run["defaultDatasetId"])
            items = dataset.list_items().items
            
            if not items:
                logger.warning(f"No items found for {username} - account may be private or unavailable")
                return None
            logger.info(f"Successfully scraped {len(items)} items for {username}")
            return items
                
        except Exception as e:
            logger.error(f"Error scraping {username}: {str(e)}")
            return None
    
    def create_local_directory(self, directory_name):
        """
        Create a local directory for storing scraped files.
        
        Args:
            directory_name (str): Name of the directory to create
            
        Returns:
            str: Path to the created directory or None if failed
        """
        try:
            # Create directory in the temp folder
            dir_path = os.path.join('temp', directory_name)
            os.makedirs(dir_path, exist_ok=True)
            logger.info(f"Created local directory: {dir_path}")
            return dir_path
        except Exception as e:
            logger.error(f"Error creating local directory: {str(e)}")
            return None
    
    def save_to_local_file(self, data, directory_path, filename):
        """
        Save scraped data to local file within the specified directory.
        
        Args:
            data: The scraped data to save
            directory_path (str): Path to the directory to save in
            filename (str): The filename to save the data as
            
        Returns:
            str: Path to the saved file or None if failed
        """
        if not data:
            logger.warning("No data to save to local file")
            return None
        
        try:
            # Ensure directory exists
            os.makedirs(directory_path, exist_ok=True)
            file_path = os.path.join(directory_path, filename)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            logger.info(f"Data saved to local file: {file_path}")
            return file_path
        except Exception as e:
            logger.error(f"Error saving data to local file: {str(e)}")
            return None
    
    def upload_directory_to_r2(self, local_directory, r2_prefix):
        """
        Upload an entire directory to R2 storage.
        
        Args:
            local_directory (str): Path to the local directory
            r2_prefix (str): Prefix to use in R2 bucket
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not os.path.exists(local_directory):
            logger.error(f"Local directory does not exist: {local_directory}")
            return False
            
        try:
            # First create a directory marker
            self.s3.put_object(
                Bucket=self.r2_config['bucket_name'],
                Key=f"{r2_prefix}/"
            )
            logger.info(f"Created directory marker in R2: {r2_prefix}/")
            
            uploaded_files = []
            
            # Upload all files in the directory
            for filename in os.listdir(local_directory):
                local_file_path = os.path.join(local_directory, filename)
                
                # Skip directories
                if os.path.isdir(local_file_path):
                    continue
                    
                # Upload file
                object_key = f"{r2_prefix}/{filename}"
                self.s3.upload_file(
                    local_file_path,
                    self.r2_config['bucket_name'],
                    object_key,
                    ExtraArgs={'ContentType': 'application/json'}
                )
                logger.info(f"Uploaded file to R2: {object_key}")
                uploaded_files.append(object_key)
            
            logger.info(f"Successfully uploaded directory to R2: {r2_prefix}/")
            return True
        except Exception as e:
            logger.error(f"Failed to upload directory to R2: {str(e)}")
            return False
    
    def process_account_batch(self, parent_username, competitor_usernames, results_limit=10):
        """
        Process a parent account and its competitors, saving all files locally first.
        
        Args:
            parent_username (str): Username of the parent account
            competitor_usernames (list): List of competitor usernames
            results_limit (int): Maximum results to fetch
            
        Returns:
            dict: Result with success status and message
        """
        logger.info(f"Processing account batch for: {parent_username}")
        
        # Create temp directory if it doesn't exist
        os.makedirs('temp', exist_ok=True)
        
        # Create local directory for the parent account
        local_dir = self.create_local_directory(parent_username)
        if not local_dir:
            return {"success": False, "message": f"Failed to create local directory for {parent_username}"}
        
        # Scrape and save parent profile
        parent_data = self.scrape_profile(parent_username, results_limit)
        if not parent_data:
            return {"success": False, "message": f"Failed to scrape parent profile: {parent_username}"}
        
        # Save parent data to local file
        parent_file = f"{parent_username}.json"
        parent_path = self.save_to_local_file(parent_data, local_dir, parent_file)
        if not parent_path:
            return {"success": False, "message": f"Failed to save parent data locally: {parent_username}"}
        
        # Process competitor accounts (up to 5)
        for competitor in competitor_usernames[:5]:
            # Scrape competitor profile
            competitor_data = self.scrape_profile(competitor, results_limit)
            if not competitor_data:
                logger.warning(f"Failed to scrape competitor profile: {competitor}")
                continue
            
            # Save competitor data to local file
            competitor_file = f"{competitor}.json"
            competitor_path = self.save_to_local_file(competitor_data, local_dir, competitor_file)
            if not competitor_path:
                logger.warning(f"Failed to save competitor data locally: {competitor}")
                continue
                
            logger.info(f"Successfully processed competitor: {competitor}")
        
        # Upload entire directory to R2
        if self.upload_directory_to_r2(local_dir, parent_username):
            # Clean up local directory
            try:
                shutil.rmtree(local_dir)
                logger.info(f"Removed local directory: {local_dir}")
            except Exception as e:
                logger.warning(f"Failed to remove local directory {local_dir}: {str(e)}")
                
            return {
                "success": True,
                "message": f"Successfully processed account batch for: {parent_username}"
            }
        else:
            return {"success": False, "message": f"Failed to upload directory to R2: {parent_username}"}
    
    def verify_structure(self, parent_username):
        """
        Verify the directory structure for a parent account.
        
        Args:
            parent_username (str): Username of the parent account
            
        Returns:
            dict: Status of each file in the structure
        """
        structure = {
            f"{parent_username}/{parent_username}.json": False,
        }
        
        # Add competitor files to structure
        for i in range(1, 6):
            structure[f"{parent_username}/competitor{i}.json"] = False
        
        try:
            # List all objects in the parent directory
            response = self.s3.list_objects_v2(
                Bucket=self.r2_config['bucket_name'],
                Prefix=f"{parent_username}/"
            )
            
            if 'Contents' in response:
                for item in response['Contents']:
                    key = item['Key']
                    if key in structure:
                        structure[key] = True
            
            missing = [k for k, v in structure.items() if not v]
            if missing:
                logger.warning(f"Missing files in structure for {parent_username}: {missing}")
            else:
                logger.info(f"Complete structure verified for {parent_username}")
                
            return structure
        except Exception as e:
            logger.error(f"Failed to verify structure: {str(e)}")
            return structure
    
    def retrieve_and_process_usernames(self):
        """
        Retrieve ONE pending username from "tasks" bucket, process it with its competitors,
        and update its status. Returns the processed parent username or an empty list if none processed.
        
        This implements a sequential queue processing system to ensure hierarchies don't mix.
        Only one primary username (with its children) is processed in each call.
        """
        usernames_bucket = "tasks"
        usernames_key = "Usernames/instagram.json"
        processed_parents = []
        
        try:
            # Get usernames from tasks bucket
            response = self.s3.get_object(Bucket=usernames_bucket, Key=usernames_key)
            usernames_data = json.loads(response['Body'].read().decode('utf-8'))
        except ClientError as e:
            if e.response['Error']['Code'] == "NoSuchKey":
                logger.info("No usernames file found in 'tasks' bucket")
                return processed_parents
            logger.error(f"Failed to retrieve usernames from R2: {str(e)}")
            return processed_parents
        except Exception as e:
            logger.error(f"Failed to retrieve usernames from R2: {str(e)}")
            return processed_parents
            
        # Sort entries by timestamp to process oldest first
        if usernames_data:
            usernames_data.sort(key=lambda x: x.get('timestamp', ''))
        
        updated = False
        # Process only ONE pending parent username
        for entry in usernames_data:
            if entry.get('status') == 'pending':
                parent_username = entry['username']
                logger.info(f"Processing single parent username from queue: {parent_username}")
                
                # Get competitor usernames
                competitor_usernames = []
                for child in entry.get('children', []):
                    if child.get('status') == 'pending' and len(competitor_usernames) < 5:
                        competitor_usernames.append(child['username'])
                
                # Process parent and competitor accounts as a batch
                result = self.process_account_batch(parent_username, competitor_usernames)
                
                if result['success']:
                    # Update parent status
                    entry['status'] = 'processed'
                    entry['processed_at'] = datetime.now().isoformat()
                    processed_parents.append(parent_username)
                    updated = True
                    
                    # Update competitor statuses
                    for idx, child in enumerate(entry.get('children', [])):
                        if idx < len(competitor_usernames) and child['username'] == competitor_usernames[idx]:
                            child['status'] = 'processed'
                            child['processed_at'] = datetime.now().isoformat()
                    
                    # Verify structure
                    structure_status = self.verify_structure(parent_username)
                    entry['structure_verified'] = all(structure_status.values())
                    
                    # Break after processing ONE parent username - this ensures sequential processing
                    logger.info(f"Queue system: Completed processing {parent_username}. Exiting queue processing.")
                    break
                else:
                    logger.error(f"Failed to process parent username {parent_username}: {result.get('message')}")
                    # Mark as failed to prevent repeated processing attempts
                    entry['status'] = 'failed'
                    entry['error'] = result.get('message', 'Unknown error')
                    entry['failed_at'] = datetime.now().isoformat()
                    updated = True
                    # Don't break here so we can try the next pending username
        
        # Update statuses in tasks bucket
        if updated:
            try:
                self.s3.put_object(
                    Bucket=usernames_bucket,
                    Key=usernames_key,
                    Body=json.dumps(usernames_data, indent=4),
                    ContentType='application/json'
                )
                logger.info("Updated usernames status in 'tasks' bucket")
            except Exception as e:
                logger.error(f"Failed to update usernames in R2: {str(e)}")
                
        return processed_parents

def test_instagram_scraper():
    """Test the Instagram scraper with a single account and its competitors."""
    try:
        scraper = InstagramScraper()
        
        # Test with parent account and 2 competitors
        parent_username = "humansofny"
        competitors = ["natgeo", "instagram"]
        
        # Process entire batch
        result = scraper.process_account_batch(parent_username, competitors, results_limit=5)
        if not result["success"]:
            logger.error(f"Test failed: {result['message']}")
            return False
            
        # Verify the structure
        structure_status = scraper.verify_structure(parent_username)
        if not all([structure_status.get(f"{parent_username}/{parent_username}.json"), 
                   structure_status.get(f"{parent_username}/competitor1.json"),
                   structure_status.get(f"{parent_username}/competitor2.json")]):
            logger.error(f"Test failed: Structure verification failed")
            return False
        
        logger.info("Test successful: All accounts processed correctly with proper directory structure")
        return True
    except Exception as e:
        logger.error(f"Test failed with exception: {str(e)}")
        return False

if __name__ == "__main__":
    scraper = InstagramScraper()
    processed = scraper.retrieve_and_process_usernames()
    logger.info(f"Processed {len(processed)} parent accounts")