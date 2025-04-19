"""Module for scraping Instagram profiles and uploading to R2 storage."""
import time
import json
import os
import shutil
import logging
from datetime import datetime, timedelta
from apify_client import ApifyClient
from botocore.client import Config
from botocore.exceptions import ClientError
import boto3
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
        self.s3 = boto3.client(
            's3',
            endpoint_url=self.r2_config['endpoint_url'],
            aws_access_key_id=self.r2_config['aws_access_key_id'],  # Updated
            aws_secret_access_key=self.r2_config['aws_secret_access_key'],  # Updated
            config=Config(signature_version='s3v4')
        )
        self.running = False
        self.last_check_time = None
    
    def scrape_profile(self, username, results_limit=10):
        """Scrape Instagram profile using Apify."""
        if not username or not isinstance(username, str):
            logger.error(f"Invalid username: {username}")
            return None
        
        known_brands = {
            "maccsometics": "maccosmetics",
            "fentybeaty": "fentybeauty",
            "urbandecay": "urbandecaycosmetics",
            "anastasiabeverly": "anastasiabeverlyhills"
        }
        
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
            time.sleep(15)
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
        """Create a local directory for storing scraped files."""
        try:
            dir_path = os.path.join('temp', directory_name)
            os.makedirs(dir_path, exist_ok=True)
            logger.info(f"Created local directory: {dir_path}")
            return dir_path
        except Exception as e:
            logger.error(f"Error creating local directory: {str(e)}")
            return None
    
    def save_to_local_file(self, data, directory_path, filename):
        """Save scraped data to local file."""
        if not data:
            logger.warning("No data to save to local file")
            return None
        try:
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
        """Check if a directory exists in the specified bucket."""
        try:
            response = self.s3.list_objects_v2(
                Bucket=bucket_name,
                Prefix=f"{parent_username}/"
            )
            return 'Contents' in response and len(response['Contents']) > 0
        except Exception as e:
            logger.error(f"Error checking if directory exists in {bucket_name}: {str(e)}")
            return False
    
    def check_content_matches(self, local_file_path, bucket_name, object_key):
        """Check if local file matches remote file by size (within 20% tolerance)."""
        try:
            local_size = os.path.getsize(local_file_path)
            try:
                remote_obj = self.s3.head_object(Bucket=bucket_name, Key=object_key)
                remote_size = remote_obj['ContentLength']
                size_ratio = max(local_size, remote_size) / min(local_size, remote_size)
                diff_percentage = (size_ratio - 1.0) * 100
                if size_ratio <= 1.2:
                    logger.info(f"File sizes within 20% tolerance: {local_file_path} ({local_size} bytes) vs {object_key} ({remote_size} bytes), diff: {diff_percentage:.2f}%")
                    return True
                logger.info(f"File sizes differ by more than 20%: {local_file_path} ({local_size} bytes) vs {object_key} ({remote_size} bytes), diff: {diff_percentage:.2f}%")
                return False
            except ClientError as e:
                if e.response['Error']['Code'] in ['404', 'NoSuchKey']:
                    return False
                raise
        except Exception as e:
            logger.error(f"Error checking content match: {str(e)}")
            return False
    
    def upload_directory_to_both_buckets(self, local_directory, r2_prefix):
        """Upload directory to main and personal buckets with conditions."""
        if not os.path.exists(local_directory):
            logger.error(f"Local directory does not exist: {local_directory}")
            return {"main_uploaded": False, "personal_uploaded": False, "success": False}
        
        main_bucket = self.r2_config['bucket_name']
        personal_bucket = self.r2_config['personal_bucket_name']
        main_exists = self.check_directory_exists(r2_prefix, main_bucket)
        main_uploaded = False
        
        if not main_exists:
            try:
                self.s3.put_object(Bucket=main_bucket, Key=f"{r2_prefix}/")
                all_files_match = True
                for filename in os.listdir(local_directory):
                    local_file_path = os.path.join(local_directory, filename)
                    if os.path.isdir(local_file_path):
                        continue
                    object_key = f"{r2_prefix}/{filename}"
                    content_matches = self.check_content_matches(local_file_path, main_bucket, object_key)
                    if not content_matches:
                        self.s3.upload_file(
                            local_file_path,
                            main_bucket,
                            object_key,
                            ExtraArgs={'ContentType': 'application/json'}
                        )
                        logger.info(f"Uploaded file to main bucket: {object_key}")
                        all_files_match = False
                main_uploaded = not all_files_match
            except Exception as e:
                logger.error(f"Failed to upload directory to main bucket: {str(e)}")
        else:
            content_differs = False
            for filename in os.listdir(local_directory):
                local_file_path = os.path.join(local_directory, filename)
                if os.path.isdir(local_file_path):
                    continue
                object_key = f"{r2_prefix}/{filename}"
                if not self.check_content_matches(local_file_path, main_bucket, object_key):
                    self.s3.upload_file(
                        local_file_path,
                        main_bucket,
                        object_key,
                        ExtraArgs={'ContentType': 'application/json'}
                    )
                    logger.info(f"Content differs, uploaded file to main bucket: {object_key}")
                    content_differs = True
            main_uploaded = content_differs
        
        personal_uploaded = False
        try:
            expiration_time = (datetime.now() + timedelta(days=1)).isoformat()
            self.s3.put_object(
                Bucket=personal_bucket,
                Key=f"{r2_prefix}/",
                Metadata={'expiration-time': expiration_time}
            )
            for filename in os.listdir(local_directory):
                local_file_path = os.path.join(local_directory, filename)
                if os.path.isdir(local_file_path):
                    continue
                object_key = f"{r2_prefix}/{filename}"
                self.s3.upload_file(
                    local_file_path,
                    personal_bucket,
                    object_key,
                    ExtraArgs={
                        'ContentType': 'application/json',
                        'Metadata': {'expiration-time': expiration_time}
                    }
                )
            logger.info(f"Successfully uploaded directory to personal bucket: {r2_prefix}/")
            personal_uploaded = True
        except Exception as e:
            logger.error(f"Failed to upload directory to personal bucket: {str(e)}")
        
        return {
            "main_uploaded": main_uploaded,
            "personal_uploaded": personal_uploaded,
            "success": main_uploaded or personal_uploaded
        }
    
    def cleanup_expired_personal_content(self):
        """Clean up expired content from the personal bucket."""
        try:
            personal_bucket = self.r2_config['personal_bucket_name']
            current_time = datetime.now()
            cleaned_count = 0
            paginator = self.s3.get_paginator('list_objects_v2')
            for page in paginator.paginate(Bucket=personal_bucket):
                if 'Contents' not in page:
                    continue
                for obj in page['Contents']:
                    key = obj['Key']
                    try:
                        response = self.s3.head_object(Bucket=personal_bucket, Key=key)
                        if 'Metadata' in response and 'expiration-time' in response['Metadata']:
                            expiration_str = response['Metadata']['expiration-time']
                            expiration_time = datetime.fromisoformat(expiration_str)
                            if current_time > expiration_time:
                                self.s3.delete_object(Bucket=personal_bucket, Key=key)
                                cleaned_count += 1
                                logger.info(f"Cleaned up expired object: {key}")
                    except Exception as e:
                        logger.error(f"Error processing object {key}: {str(e)}")
            logger.info(f"Cleaned up {cleaned_count} expired objects from personal bucket")
            return cleaned_count
        except Exception as e:
            logger.error(f"Error cleaning up expired content: {str(e)}")
            return 0
    
    def extract_short_profile_info(self, profile_data):
        """Extract basic profile information from scraped data."""
        try:
            if not profile_data or not isinstance(profile_data, list) or len(profile_data) == 0:
                logger.warning("Invalid profile data for extraction")
                return None
            profile = profile_data[0]
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
        """Upload short profile info to tasks bucket."""
        if not profile_info or not isinstance(profile_info, dict):
            logger.warning("Invalid profile info for upload")
            return False
        try:
            tasks_bucket = self.r2_config['bucket_name2']
            username = profile_info.get("username", "")
            if not username:
                logger.warning("Username missing in profile info")
            return False
            profile_key = f"ProfileInfo/{username}.json"
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
    
    def store_info_metadata(self, info_data):
        """Store info.json metadata in tasks bucket for downstream use."""
        try:
            username = info_data.get("username", "")
            if not username:
                logger.error("Missing username in info.json")
                return False
            tasks_bucket = self.r2_config['bucket_name2']
            metadata_key = f"ProcessedInfo/{username}.json"
            self.s3.put_object(
                Bucket=tasks_bucket,
                Key=metadata_key,
                Body=json.dumps(info_data, indent=2),
                ContentType='application/json'
            )
            logger.info(f"Stored info.json metadata: {metadata_key}")
            return True
        except Exception as e:
            logger.error(f"Error storing info.json metadata: {str(e)}")
            return False
    
    def process_account_batch(self, parent_username, competitor_usernames, results_limit=10, info_metadata=None):
        """Process a parent account and its competitors, saving files locally."""
        logger.info(f"Processing account batch for: {parent_username}")
        os.makedirs('temp', exist_ok=True)
        local_dir = self.create_local_directory(parent_username)
        if not local_dir:
            return {"success": False, "message": f"Failed to create local directory for {parent_username}"}
        
        parent_data = self.scrape_profile(parent_username, results_limit)
        if not parent_data:
            return {"success": False, "message": f"Failed to scrape parent profile: {parent_username}"}
        
        parent_short_info = self.extract_short_profile_info(parent_data)
        if parent_short_info:
            # Add account type and posting style from info_metadata if available
            if info_metadata:
                parent_short_info['account_type'] = info_metadata.get('accountType', '')
                parent_short_info['posting_style'] = info_metadata.get('postingStyle', '')
                
                # Log account type for debugging
                logger.info(f"Account type for {parent_username}: {parent_short_info['account_type']}")
                logger.info(f"Posting style for {parent_username}: {parent_short_info['posting_style']}")
                
            self.upload_short_profile_to_tasks(parent_short_info)
        
        parent_file = f"{parent_username}.json"
        parent_path = self.save_to_local_file(parent_data, local_dir, parent_file)
        if not parent_path:
            return {"success": False, "message": f"Failed to save parent data locally: {parent_username}"}
        
        for competitor in competitor_usernames[:5]:
            competitor_data = self.scrape_profile(competitor, results_limit)
            if not competitor_data:
                logger.warning(f"Failed to scrape competitor profile: {competitor}")
                continue
            competitor_short_info = self.extract_short_profile_info(competitor_data)
            if competitor_short_info:
                self.upload_short_profile_to_tasks(competitor_short_info)
            competitor_file = f"{competitor}.json"
            competitor_path = self.save_to_local_file(competitor_data, local_dir, competitor_file)
            if not competitor_path:
                logger.warning(f"Failed to save competitor data locally: {competitor}")
                continue
            logger.info(f"Successfully processed competitor: {competitor}")
        
        upload_result = self.upload_directory_to_both_buckets(local_dir, parent_username)
        
        try:
            shutil.rmtree(local_dir)
            logger.info(f"Removed local directory: {local_dir}")
        except Exception as e:
            logger.warning(f"Failed to remove local directory {local_dir}: {str(e)}")
        
        self.cleanup_expired_personal_content()
        
        if upload_result["success"] and info_metadata:
            self.store_info_metadata(info_metadata)
        
        return {
            "success": upload_result["success"],
            "message": f"Successfully processed account batch for: {parent_username}" if upload_result["success"] else f"Failed to upload directory to R2: {parent_username}",
            "main_uploaded": upload_result["main_uploaded"],
            "personal_uploaded": upload_result["personal_uploaded"]
        }
    
    def verify_structure(self, parent_username):
        """Verify the directory structure for a parent account."""
        structure = {f"{parent_username}/{parent_username}.json": False}
        for i in range(1, 6):
            structure[f"{parent_username}/competitor{i}.json"] = False
        try:
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
        Retrieve and process ONE pending info.json from tasks/AccountInfo/<username>/info.json.
        Returns the processed parent username or an empty list if none processed.
        """
        tasks_bucket = self.r2_config['bucket_name2']
        prefix = "AccountInfo/"
        processed_parents = []
        
        try:
            paginator = self.s3.get_paginator('list_objects_v2')
            page_iterator = paginator.paginate(Bucket=tasks_bucket, Prefix=prefix)
            
            info_files = []
            for page in page_iterator:
                if 'Contents' not in page:
                    logger.debug(f"No objects found for prefix {prefix} in page")
                    continue
                for obj in page['Contents']:
                    if obj['Key'].endswith('/info.json'):
                        info_files.append(obj)
            
            if not info_files:
                logger.info(f"No info.json files found in {tasks_bucket} with prefix {prefix}")
                return processed_parents
            
            info_files.sort(key=lambda x: x['LastModified'])
            logger.debug(f"Found {len(info_files)} info.json files: {[f['Key'] for f in info_files]}")
            
            for obj in info_files:
                info_key = obj['Key']
                logger.debug(f"Attempting to process {info_key}")
                
                try:
                    response = self.s3.get_object(Bucket=tasks_bucket, Key=info_key)
                    info_data = json.loads(response['Body'].read().decode('utf-8'))
                    logger.debug(f"Loaded info.json content: {json.dumps(info_data, indent=2)}")
                    
                    username = info_data.get('username', '')
                    account_type = info_data.get('accountType', '')
                    posting_style = info_data.get('postingStyle', '')
                    competitors = info_data.get('competitors', [])
                    timestamp = info_data.get('timestamp', '')
                    
                    if not username or not account_type:
                        logger.error(f"Invalid info.json at {info_key}: missing username or accountType")
                        info_data['status'] = 'failed'
                        info_data['error'] = 'Missing required fields'
                        info_data['failed_at'] = datetime.now().isoformat()
                        self.s3.put_object(
                            Bucket=tasks_bucket,
                            Key=info_key,
                            Body=json.dumps(info_data, indent=4),
                            ContentType='application/json'
                        )
                        continue
                    
                    if info_data.get('status', 'pending') != 'pending':
                        logger.info(f"Skipping already processed info.json: {info_key} (status: {info_data.get('status')})")
                        continue
                    
                    logger.info(f"Processing info.json for username: {username}")
                    logger.info(f"Account type: {account_type}, Posting style: {posting_style}")
                    
                    # Handle different competitors field formats
                    competitor_usernames = []
                    if isinstance(competitors, list):
                        for comp in competitors:
                            if isinstance(comp, dict) and 'username' in comp:
                                competitor_usernames.append(comp['username'])
                            elif isinstance(comp, str):
                                competitor_usernames.append(comp)
                    elif isinstance(competitors, str):
                        # If competitors is a comma-separated string
                        competitor_usernames = [username.strip() for username in competitors.split(',') if username.strip()]
                        # If it's a single username without commas
                        if not competitor_usernames and competitors.strip():
                            competitor_usernames = [competitors.strip()]
                    
                    logger.debug(f"Competitor usernames: {competitor_usernames}")
                    
                    info_data['status'] = 'processing'
                    info_data['processing_started_at'] = datetime.now().isoformat()
                    self.s3.put_object(
                        Bucket=tasks_bucket,
                        Key=info_key,
                        Body=json.dumps(info_data, indent=4),
                        ContentType='application/json'
                    )
                    
                    result = self.process_account_batch(
                        parent_username=username,
                        competitor_usernames=competitor_usernames,
                        results_limit=10,
                        info_metadata=info_data
                    )
                    
                    info_data['status'] = 'processed' if result['success'] else 'failed'
                    info_data['processed_at'] = datetime.now().isoformat()
                    if not result['success']:
                        info_data['error'] = result['message']
                    
                    self.s3.put_object(
                        Bucket=tasks_bucket,
                        Key=info_key,
                        Body=json.dumps(info_data, indent=4),
                        ContentType='application/json'
                    )
                    
                    if result['success']:
                        processed_parents.append(username)
                        logger.info(f"Successfully processed {username}")
                    else:
                        logger.error(f"Failed to process {username}: {result['message']}")
                    
                    logger.debug("Processed one info.json, exiting loop")
                    break
                
                except Exception as e:
                    logger.error(f"Error processing {info_key}: {str(e)}")
                    try:
                        info_data['status'] = 'failed'
                        info_data['error'] = str(e)
                        info_data['failed_at'] = datetime.now().isoformat()
                        self.s3.put_object(
                            Bucket=tasks_bucket,
                            Key=info_key,
                            Body=json.dumps(info_data, indent=4),
                            ContentType='application/json'
                        )
                    except Exception as update_e:
                        logger.error(f"Failed to update status for {info_key}: {update_e}")
                    continue
        
        except Exception as e:
            logger.error(f"Failed to list info.json files in {tasks_bucket} with prefix {prefix}: {str(e)}")
        
        return processed_parents
    
    def scrape_and_upload(self, username, results_limit=10, info_metadata=None):
        """Scrape Instagram profile and upload to R2 buckets."""
        try:
            if not username or not isinstance(username, str):
                logger.error(f"Invalid username: {username}")
                return {"success": False, "message": f"Invalid username: {username}"}
            
            parent_data = self.scrape_profile(username, results_limit)
            if not parent_data:
                return {"success": False, "message": f"Failed to scrape profile: {username}"}
            
            local_dir = self.create_local_directory(username)
            if not local_dir:
                return {"success": False, "message": f"Failed to create local directory for {username}"}
            
            parent_file = f"{username}.json"
            parent_path = self.save_to_local_file(parent_data, local_dir, parent_file)
            if not parent_path:
                return {"success": False, "message": f"Failed to save data locally: {username}"}
            
            upload_result = self.upload_directory_to_both_buckets(local_dir, username)
            
            try:
                shutil.rmtree(local_dir)
                logger.info(f"Removed local directory: {local_dir}")
            except Exception as e:
                logger.warning(f"Failed to remove local directory {local_dir}: {str(e)}")
            
            if upload_result["success"] and info_metadata:
                parent_short_info = self.extract_short_profile_info(parent_data)
                if parent_short_info:
                    self.upload_short_profile_to_tasks(parent_short_info)
                self.store_info_metadata(info_metadata)
            
            self.cleanup_expired_personal_content()
            
            object_key = f"{username}/{username}.json"
            return {
                "success": upload_result["success"],
                "message": f"Successfully scraped and uploaded {username}" if upload_result["success"] else f"Failed to upload {username}",
                "object_key": object_key
            }
        except Exception as e:
            logger.error(f"Error in scrape_and_upload for {username}: {str(e)}")
            return {"success": False, "message": str(e)}
    
    def continuous_processing_loop(self, sleep_interval=86400, check_interval=300):
        """
        Continuously process info.json files in an event-driven manner.
        
        Args:
            sleep_interval: Time to sleep after processing all files (in seconds, default 24 hours)
            check_interval: Time to wait between checks for new files during sleep (in seconds, default 5 minutes)
        """
        self.running = True
        logger.info(f"Starting continuous processing loop with sleep interval of {sleep_interval} seconds")
        
        try:
            while self.running:
                # Process all pending info.json files
                processed_count = 0
                while True:
                    processed = self.retrieve_and_process_usernames()
                    if not processed:
                        # No more pending files to process
                        break
                    processed_count += len(processed)
                    logger.info(f"Processed {len(processed)} accounts, total in this cycle: {processed_count}")
                
                logger.info(f"All pending files processed. Entering sleep mode for {sleep_interval} seconds")
                self.last_check_time = datetime.now()
                
                # Sleep with periodic checks for new files
                sleep_start_time = datetime.now()
                while (datetime.now() - sleep_start_time).total_seconds() < sleep_interval:
                    # Check if enough time has passed since the last check
                    if (datetime.now() - self.last_check_time).total_seconds() >= check_interval:
                        # Check for new pending files
                        logger.info("Checking for new files during sleep period")
                        new_files_exist = self._check_for_new_pending_files()
                        self.last_check_time = datetime.now()
                        
                        if new_files_exist:
                            logger.info("New pending files detected during sleep, processing now")
                            processed = self.retrieve_and_process_usernames()
                            if processed:
                                logger.info(f"Processed {len(processed)} new accounts during sleep period")
                    
                    # Sleep for a short time before checking again
                    time.sleep(10)  # Check every 10 seconds if we need to do the full check
                
                logger.info("Sleep interval completed, restarting processing cycle")
                
                # Clean up expired content before starting new cycle
                self.cleanup_expired_personal_content()
                
        except KeyboardInterrupt:
            logger.info("Processing loop interrupted by user")
            self.running = False
        except Exception as e:
            logger.error(f"Error in continuous processing loop: {str(e)}")
            self.running = False
            raise
    
    def _check_for_new_pending_files(self):
        """Check if there are any new pending info.json files."""
        tasks_bucket = self.r2_config['bucket_name2']
        prefix = "AccountInfo/"
        
        try:
            response = self.s3.list_objects_v2(
                Bucket=tasks_bucket,
                Prefix=prefix,
                MaxKeys=10  # Just need to check if any exist, don't need all
            )
            
            if 'Contents' not in response:
                return False
                
            for obj in response['Contents']:
                if obj['Key'].endswith('/info.json'):
                    # Download the file to check its status
                    info_key = obj['Key']
                    file_response = self.s3.get_object(Bucket=tasks_bucket, Key=info_key)
                    info_data = json.loads(file_response['Body'].read().decode('utf-8'))
                    
                    # If status is pending, we have a new file to process
                    if info_data.get('status', 'pending') == 'pending':
                        return True
            
            return False
        except Exception as e:
            logger.error(f"Error checking for new pending files: {str(e)}")
            return False
    
    def stop_processing(self):
        """Stop the continuous processing loop safely."""
        logger.info("Stopping continuous processing loop")
        self.running = False

def test_instagram_scraper():
    """Test the Instagram scraper with a single account."""
    try:
        scraper = InstagramScraper()
        parent_username = "humansofny"
        competitors = []
        info_metadata = {
            "username": parent_username,
            "accountType": "non-branding",
            "postingStyle": "Storytelling",
            "competitors": [{"username": comp} for comp in competitors],
            "timestamp": datetime.now().isoformat(),
            "status": "pending"
        }
        
        result = scraper.process_account_batch(parent_username, competitors, results_limit=5, info_metadata=info_metadata)
        if not result["success"]:
            logger.error(f"Test failed: {result['message']}")
            return False
        
        tasks_bucket = scraper.r2_config['bucket_name2']
        scraper.s3.head_object(Bucket=tasks_bucket, Key=f"ProfileInfo/{parent_username}.json")
        scraper.s3.head_object(Bucket=tasks_bucket, Key=f"ProcessedInfo/{parent_username}.json")
        logger.info("Test successful: Processed info.json and stored metadata")
        return True
    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
        return False

if __name__ == "__main__":
    scraper = InstagramScraper()
    logger.info("Cleaning up expired content from personal bucket")
    cleaned = scraper.cleanup_expired_personal_content()
    logger.info(f"Cleaned {cleaned} expired objects")
    
    try:
        # Start the continuous processing loop with configurable intervals
        # Default: 24 hours (86400 seconds) sleep between full cycles
        # Check for new files every 5 minutes (300 seconds) during sleep
        scraper.continuous_processing_loop(
            sleep_interval=86400,  # 24 hours
            check_interval=300     # 5 minutes
        )
    except KeyboardInterrupt:
        logger.info("Script interrupted by user")
    except Exception as e:
        logger.error(f"Error in main process: {str(e)}")
    finally:
        logger.info("Instagram scraper process ended")