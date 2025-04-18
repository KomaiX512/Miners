"""Module for scraping Instagram profiles and uploading to R2 storage."""
import time
import json
import os
import logging
import shutil
import boto3
from botocore.client import Config
from botocore.exceptions import ClientError
from datetime import datetime, timedelta
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
        # Validate and sanitize username
        if not username or not isinstance(username, str):
            logger.error(f"Invalid username: {username}")
            return None
        
        # List of known brand names to check for common typos
        known_brands = {
            "maccsometics": "maccosmetics",
            "fentybeaty": "fentybeauty",
            "urbandecay": "urbandecaycosmetics",
            "anastasiabeverly": "anastasiabeverlyhills"
        }
        
        # Check if username is a known typo and correct it
        if username.lower() in known_brands:
            corrected_username = known_brands[username.lower()]
            logger.warning(f"Corrected typo in username: {username} -> {corrected_username}")
            username = corrected_username
        
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
    
    def check_directory_exists(self, parent_username, bucket_name):
        """
        Check if a directory for a parent username already exists in the specified bucket.
        
        Args:
            parent_username (str): Username of the parent account
            bucket_name (str): Name of the bucket to check
            
        Returns:
            bool: True if directory exists, False otherwise
        """
        try:
            # List objects with the parent username prefix
            response = self.s3.list_objects_v2(
                Bucket=bucket_name,
                Prefix=f"{parent_username}/"
            )
            
            # If there are contents, the directory exists
            return 'Contents' in response and len(response['Contents']) > 0
        except Exception as e:
            logger.error(f"Error checking if directory exists in {bucket_name}: {str(e)}")
            return False
            
    def check_content_matches(self, local_file_path, bucket_name, object_key):
        """
        Check if a local file matches a remote file using file size comparison.
        Files are considered matching if their sizes differ by ≤20%.
        
        Args:
            local_file_path (str): Path to the local file
            bucket_name (str): Name of the bucket
            object_key (str): Key of the object in the bucket
            
        Returns:
            bool: True if content matches, False otherwise
        """
        try:
            # Get local file size
            local_size = os.path.getsize(local_file_path)
                
            # Get remote file info
            try:
                remote_obj = self.s3.head_object(
                    Bucket=bucket_name,
                    Key=object_key
                )
                remote_size = remote_obj['ContentLength']
                
                # Calculate the size ratio (always >= 1.0)
                size_ratio = max(local_size, remote_size) / min(local_size, remote_size)
                
                # Calculate the difference percentage for logging
                diff_percentage = (size_ratio - 1.0) * 100
                
                # Files match if their size ratio is at most 1.2 (20% difference)
                # Using a tiny epsilon to account for floating point precision
                epsilon = 0.00001
                max_ratio = 1.2 + epsilon
                
                if size_ratio <= max_ratio:
                    logger.info(f"File sizes within 20% tolerance: {local_file_path} ({local_size} bytes) vs {object_key} ({remote_size} bytes), diff: {diff_percentage:.2f}%")
                    return True
                else:
                    logger.info(f"File sizes differ by more than 20%: {local_file_path} ({local_size} bytes) vs {object_key} ({remote_size} bytes), diff: {diff_percentage:.2f}%")
                    return False
                    
            except ClientError as e:
                # Object doesn't exist
                if e.response['Error']['Code'] in ['404', 'NoSuchKey']:
                    return False
                raise
                
        except Exception as e:
            logger.error(f"Error checking content match: {str(e)}")
            return False
    
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
            
    def upload_directory_to_both_buckets(self, local_directory, r2_prefix):
        """
        Upload directory to both main and personal buckets with conditions.
        For main bucket: only upload if content doesn't already exist
        For personal bucket: always upload and add cleanup metadata
        
        Args:
            local_directory (str): Path to the local directory
            r2_prefix (str): Prefix to use in R2 bucket
            
        Returns:
            dict: Result with success status and details
        """
        if not os.path.exists(local_directory):
            logger.error(f"Local directory does not exist: {local_directory}")
            return {"main_uploaded": False, "personal_uploaded": False, "success": False}
            
        # Check if directory already exists in main bucket
        main_bucket = self.r2_config['bucket_name']
        personal_bucket = self.r2_config['personal_bucket_name']
        main_exists = self.check_directory_exists(r2_prefix, main_bucket)
        main_uploaded = False
        
        # Only upload to main bucket if it doesn't exist or content differs
        if not main_exists:
            logger.info(f"Directory doesn't exist in main bucket, uploading: {r2_prefix}")
            try:
                # First create a directory marker
                self.s3.put_object(
                    Bucket=main_bucket,
                    Key=f"{r2_prefix}/"
                )
                
                # Upload all files in the directory to main bucket
                all_files_match = True
                for filename in os.listdir(local_directory):
                    local_file_path = os.path.join(local_directory, filename)
                    
                    # Skip directories
                    if os.path.isdir(local_file_path):
                        continue
                        
                    # Check if content matches before uploading to main bucket
                    object_key = f"{r2_prefix}/{filename}"
                    content_matches = self.check_content_matches(local_file_path, main_bucket, object_key)
                    
                    if not content_matches:
                        # Upload file to main bucket
                        self.s3.upload_file(
                            local_file_path,
                            main_bucket,
                            object_key,
                            ExtraArgs={'ContentType': 'application/json'}
                        )
                        logger.info(f"Uploaded file to main bucket: {object_key}")
                        all_files_match = False
                    else:
                        logger.info(f"File already exists with similar content, skipping upload: {object_key}")
                
                if not all_files_match:
                    logger.info(f"Successfully uploaded directory to main bucket: {r2_prefix}/")
                    main_uploaded = True
                else:
                    logger.info(f"All files already exist in main bucket with matching content, skipping upload")
            except Exception as e:
                logger.error(f"Failed to upload directory to main bucket: {str(e)}")
        else:
            logger.info(f"Directory already exists in main bucket, checking content: {r2_prefix}")
            # Check if content matches for each file
            content_differs = False
            match_count = 0
            total_files = 0
            
            for filename in os.listdir(local_directory):
                local_file_path = os.path.join(local_directory, filename)
                
                # Skip directories
                if os.path.isdir(local_file_path):
                    continue
                    
                total_files += 1
                # Check if content matches
                object_key = f"{r2_prefix}/{filename}"
                if not self.check_content_matches(local_file_path, main_bucket, object_key):
                    content_differs = True
                    # Upload file to main bucket if content differs
                    self.s3.upload_file(
                        local_file_path,
                        main_bucket,
                        object_key,
                        ExtraArgs={'ContentType': 'application/json'}
                    )
                    logger.info(f"Content differs, uploaded file to main bucket: {object_key}")
                else:
                    match_count += 1
                    logger.info(f"Content matches within tolerance, no upload needed: {object_key}")
                    
            if content_differs:
                logger.info(f"Some files had different content ({total_files-match_count}/{total_files}), updated in main bucket: {r2_prefix}/")
                main_uploaded = True
            else:
                logger.info(f"All content matches within tolerance ({match_count}/{total_files}), no upload needed")
        
        # Always upload to personal bucket with cleanup metadata
        personal_uploaded = False
        try:
            # Set expiration timestamp (24 hours from now)
            expiration_time = (datetime.now() + timedelta(days=1)).isoformat()
            
            # Create a directory marker with metadata
            self.s3.put_object(
                Bucket=personal_bucket,
                Key=f"{r2_prefix}/",
                Metadata={
                    'expiration-time': expiration_time
                }
            )
            
            # Upload all files in the directory to personal bucket
            for filename in os.listdir(local_directory):
                local_file_path = os.path.join(local_directory, filename)
                
                # Skip directories
                if os.path.isdir(local_file_path):
                    continue
                    
                # Upload file to personal bucket with metadata
                object_key = f"{r2_prefix}/{filename}"
                self.s3.upload_file(
                    local_file_path,
                    personal_bucket,
                    object_key,
                    ExtraArgs={
                        'ContentType': 'application/json',
                        'Metadata': {
                            'expiration-time': expiration_time
                        }
                    }
                )
            
            logger.info(f"Successfully uploaded directory to personal bucket with expiration: {r2_prefix}/")
            personal_uploaded = True
            
        except Exception as e:
            logger.error(f"Failed to upload directory to personal bucket: {str(e)}")
        
        return {
            "main_uploaded": main_uploaded,
            "personal_uploaded": personal_uploaded,
            "success": main_uploaded or personal_uploaded
        }
    
    def cleanup_expired_personal_content(self):
        """
        Clean up expired content from the personal bucket that is older than 24 hours.
        
        Returns:
            int: Number of objects cleaned up
        """
        try:
            personal_bucket = self.r2_config['personal_bucket_name']
            current_time = datetime.now()
            cleaned_count = 0
            
            # List all objects in the personal bucket
            paginator = self.s3.get_paginator('list_objects_v2')
            for page in paginator.paginate(Bucket=personal_bucket):
                if 'Contents' not in page:
                    continue
                    
                for obj in page['Contents']:
                    key = obj['Key']
                    
                    try:
                        # Get object metadata to check expiration
                        response = self.s3.head_object(
                            Bucket=personal_bucket,
                            Key=key
                        )
                        
                        if 'Metadata' in response and 'expiration-time' in response['Metadata']:
                            expiration_str = response['Metadata']['expiration-time']
                            expiration_time = datetime.fromisoformat(expiration_str)
                            
                            # If expired, delete the object
                            if current_time > expiration_time:
                                self.s3.delete_object(
                                    Bucket=personal_bucket,
                                    Key=key
                                )
                                cleaned_count += 1
                                logger.info(f"Cleaned up expired object: {key}")
                    except Exception as e:
                        logger.error(f"Error processing object {key}: {str(e)}")
                        continue
            
            logger.info(f"Cleaned up {cleaned_count} expired objects from personal bucket")
            return cleaned_count
            
        except Exception as e:
            logger.error(f"Error cleaning up expired content: {str(e)}")
            return 0
    
    def extract_short_profile_info(self, profile_data):
        """
        Extract basic profile information from scraped data.
        
        Args:
            profile_data (dict): The scraped profile data
            
        Returns:
            dict: Short profile info or None if data is invalid
        """
        try:
            if not profile_data or not isinstance(profile_data, list) or len(profile_data) == 0:
                logger.warning("Invalid profile data for extraction")
                return None
            
            # Get the first item which contains profile info
            profile = profile_data[0]
            
            # Extract required fields
            short_info = {
                "username": profile.get("username", ""),
                "fullName": profile.get("fullName", ""),
                "biography": profile.get("biography", ""),
                "followersCount": profile.get("followersCount", 0),
                "followsCount": profile.get("followsCount", 0),
                "profilePicUrl": profile.get("profilePicUrl", ""),
                "profilePicUrlHD": profile.get("profilePicUrlHD", ""),
                "private": profile.get("private", False),
                "verified": profile.get("verified", False),
                "extractedAt": datetime.now().isoformat()
            }
            
            logger.info(f"Successfully extracted short profile info for {short_info['username']}")
            return short_info
        except Exception as e:
            logger.error(f"Error extracting short profile info: {str(e)}")
            return None
    
    def upload_short_profile_to_tasks(self, profile_info):
        """
        Upload short profile info to tasks bucket.
        
        Args:
            profile_info (dict): The short profile info to upload
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not profile_info or not isinstance(profile_info, dict):
            logger.warning("Invalid profile info for upload")
            return False
        
        try:
            # Use the tasks bucket from config
            tasks_bucket = self.r2_config['bucket_name2']
            
            # Create key for the profile info file
            username = profile_info.get("username", "")
            if not username:
                logger.warning("Username missing in profile info")
                return False
                
            # Use flat structure in "ProfileInfo" directory
            profile_key = f"ProfileInfo/{username}.json"
            
            # Convert to JSON and upload
            self.s3.put_object(
                Bucket=tasks_bucket,
                Key=profile_key,
                Body=json.dumps(profile_info, indent=2),
                ContentType='application/json'
            )
            
            logger.info(f"Uploaded short profile info to tasks bucket: {profile_key}")
            return True
        except Exception as e:
            logger.error(f"Error uploading profile info to tasks bucket: {str(e)}")
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
        
        # Extract and upload short profile info for parent
        parent_short_info = self.extract_short_profile_info(parent_data)
        if parent_short_info:
            self.upload_short_profile_to_tasks(parent_short_info)
        
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
            
            # Extract and upload short profile info for competitor
            competitor_short_info = self.extract_short_profile_info(competitor_data)
            if competitor_short_info:
                self.upload_short_profile_to_tasks(competitor_short_info)
            
            # Save competitor data to local file
            competitor_file = f"{competitor}.json"
            competitor_path = self.save_to_local_file(competitor_data, local_dir, competitor_file)
            if not competitor_path:
                logger.warning(f"Failed to save competitor data locally: {competitor}")
                continue
                
            logger.info(f"Successfully processed competitor: {competitor}")
        
        # Upload to both buckets with condition checking
        upload_result = self.upload_directory_to_both_buckets(local_dir, parent_username)
        
        # Clean up local directory
        try:
            shutil.rmtree(local_dir)
            logger.info(f"Removed local directory: {local_dir}")
        except Exception as e:
            logger.warning(f"Failed to remove local directory {local_dir}: {str(e)}")
        
        # Clean up expired content in personal bucket
        self.cleanup_expired_personal_content()
        
        if upload_result["success"]:
            return {
                "success": True,
                "message": f"Successfully processed account batch for: {parent_username}",
                "main_uploaded": upload_result["main_uploaded"],
                "personal_uploaded": upload_result["personal_uploaded"]
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
        
        # Process entire batch with dual bucket upload
        result = scraper.process_account_batch(parent_username, competitors, results_limit=5)
        if not result["success"]:
            logger.error(f"Test failed: {result['message']}")
            return False
        
        logger.info(f"Main bucket uploaded: {result['main_uploaded']}")
        logger.info(f"Personal bucket uploaded: {result['personal_uploaded']}")
        
        # Check if profile info was uploaded to tasks bucket
        tasks_bucket = scraper.r2_config['bucket_name2']
        try:
            # Check parent profile info
            scraper.s3.head_object(
                Bucket=tasks_bucket,
                Key=f"ProfileInfo/{parent_username}.json"
            )
            logger.info(f"Verified parent profile info in tasks bucket")
            
            # Check one competitor profile info
            scraper.s3.head_object(
                Bucket=tasks_bucket,
                Key=f"ProfileInfo/{competitors[0]}.json"
            )
            logger.info(f"Verified competitor profile info in tasks bucket")
        except Exception as e:
            logger.error(f"Test failed: Profile info verification failed: {str(e)}")
            # Don't return False here, as this is a new feature and older files might not have it
            logger.warning("Continuing despite profile info check failure")
            
        # Verify the structure in main bucket
        structure_status = scraper.verify_structure(parent_username)
        if not all([structure_status.get(f"{parent_username}/{parent_username}.json"), 
                   structure_status.get(f"{parent_username}/competitor1.json"),
                   structure_status.get(f"{parent_username}/competitor2.json")]):
            logger.error(f"Test failed: Structure verification failed in main bucket")
            return False
        
        # Verify existence in personal bucket
        personal_bucket = scraper.r2_config['personal_bucket_name']
        try:
            # Check parent file
            scraper.s3.head_object(
                Bucket=personal_bucket,
                Key=f"{parent_username}/{parent_username}.json"
            )
            # Check at least one competitor file
            scraper.s3.head_object(
                Bucket=personal_bucket,
                Key=f"{parent_username}/{competitors[0]}.json"
            )
            logger.info(f"Verified content in personal bucket")
        except Exception as e:
            logger.error(f"Test failed: Personal bucket verification failed: {str(e)}")
            return False
        
        # Test cleanup (just call it, don't actually clean for test purposes)
        cleanup_count = scraper.cleanup_expired_personal_content()
        logger.info(f"Cleanup test found {cleanup_count} expired objects")
        
        logger.info("Test successful: All accounts processed correctly with proper directory structure in both buckets")
        return True
    except Exception as e:
        logger.error(f"Test failed with exception: {str(e)}")
        return False

if __name__ == "__main__":
    scraper = InstagramScraper()
    # Run cleanup on startup
    logger.info(f"Cleaning up expired content from personal bucket")
    cleaned = scraper.cleanup_expired_personal_content()
    logger.info(f"Cleaned {cleaned} expired objects")
    
    # Process usernames
    processed = scraper.retrieve_and_process_usernames()
    logger.info(f"Processed {len(processed)} parent accounts")