"""Module for scraping Facebook profiles and uploading to R2 storage."""
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

# Apify API token for Facebook scraper
APIFY_API_TOKEN = "apify_api_vSeStT6lqBddgKi2B0AgMcpus9nHYG03uFHH"

class FacebookScraper:
    """Class for scraping Facebook profiles and uploading to R2 storage."""
    
    def __init__(self, api_token=APIFY_API_TOKEN, r2_config=R2_CONFIG):
        """Initialize with API token and R2 configuration."""
        self.api_token = api_token
        self.r2_config = r2_config
        self.s3 = boto3.client(
            's3',
            endpoint_url=self.r2_config['endpoint_url'],
            aws_access_key_id=self.r2_config['aws_access_key_id'],
            aws_secret_access_key=self.r2_config['aws_secret_access_key'],
            region_name='auto',  # Use 'auto' for R2 storage
            config=Config(signature_version='s3v4')
        )
        self.running = False
        self.last_check_time = None
    
    def scrape_profile(self, username, results_limit=50):
        """Scrape Facebook profile using Apify."""
        if not username or not isinstance(username, str):
            logger.error(f"Invalid username: {username}")
            return None
        
        logger.info(f"Scraping Facebook profile: {username} with results_limit: {results_limit}")
        
        client = ApifyClient(self.api_token)
        
        # Clean up username for the Facebook URL format
        clean_username = username.strip()
        if clean_username.startswith('@'):
            clean_username = clean_username[1:]
        
        # Facebook scraper input format as specified
        run_input = {
            "captionText": False,
            "resultsLimit": results_limit,
            "startUrls": [
                {
                    "url": f"https://www.facebook.com/{clean_username}/",
                    "method": "GET"
                }
            ]
        }
        
        logger.info(f"🚀 Starting Facebook scraping for {username} with input: {run_input}")
        
        # RETRY MECHANISM - Try up to 3 times
        for attempt in range(1, 4):
            try:
                logger.info(f"🚀 ATTEMPT {attempt}/3: Starting Facebook scraping for {username}")
                
                # Use a Facebook scraper actor - you may need to adjust the actor ID based on available Facebook scrapers
                actor = client.actor("apify/facebook-posts-scraper")
                run = actor.call(run_input=run_input)
                
                if not run:
                    logger.warning(f"❌ Attempt {attempt}: Actor run failed for {username}")
                    if attempt < 3:
                        time.sleep(10)  # Wait before retry
                        continue
                    return None
                
                run_id = run["id"]
                logger.info(f"✅ Attempt {attempt}: Facebook run started with ID: {run_id}")
                
                # Wait for completion
                logger.info(f"⏳ Waiting for Facebook scraping to complete for {username}...")
                max_wait_time = 600  # 10 minutes max wait
                check_interval = 20   # Check every 20 seconds
                
                run_completed = False
                final_status = "UNKNOWN"
                
                for i in range(0, max_wait_time, check_interval):
                    try:
                        run_status = client.run(run_id).get()
                        final_status = run_status.get("status", "UNKNOWN")
                        
                        # Enhanced status logging
                        stats = run_status.get("stats", {})
                        items_count = stats.get("itemCount", 0)
                        
                        logger.info(f"📊 Attempt {attempt}: Facebook status for {username}: {final_status} | Items: {items_count} | Waited: {i}s/{max_wait_time}s")
                        
                        if final_status in ["SUCCEEDED", "FAILED", "ABORTED", "TIMED-OUT"]:
                            run_completed = True
                            break
                        
                        time.sleep(check_interval)
                    except Exception as e:
                        logger.warning(f"⚠️ Error checking run status: {str(e)}")
                        time.sleep(check_interval)
                
                # Retrieve data
                try:
                    dataset = client.dataset(run["defaultDatasetId"])
                    items = dataset.list_items().items
                    
                    logger.info(f"📦 Attempt {attempt}: Retrieved {len(items) if items else 0} items for {username}")
                    
                    # SUCCESS CONDITIONS
                    if items and len(items) > 0:
                        logger.info(f"🎉 SUCCESS on attempt {attempt}: Found {len(items)} items for Facebook user {username}")
                        
                        # Validate the scraped data
                        first_item = items[0]
                        if isinstance(first_item, dict):
                            logger.info(f"✅ Data validation passed for {username}")
                            logger.debug(f"First item keys: {list(first_item.keys())}")
                        
                        return items
                    
                    # PARTIAL SUCCESS - Even if no items, check if run was successful
                    elif final_status == "SUCCEEDED":
                        logger.warning(f"⚠️ Attempt {attempt}: Run succeeded but no items for {username} - may be private/protected account")
                        
                        # For private accounts, return empty list instead of None to avoid failure
                        if attempt == 3:  # Last attempt
                            logger.info(f"🔒 Treating {username} as private/protected account - returning empty data")
                            return []
                    
                    # FAILED RUN - Try different configuration on retry
                    else:
                        logger.warning(f"❌ Attempt {attempt}: Run status {final_status} with no items for {username}")
                        
                        if attempt < 3:
                            time.sleep(15)  # Wait before retry
                            continue
                
                except Exception as dataset_error:
                    logger.error(f"❌ Attempt {attempt}: Error retrieving dataset for {username}: {str(dataset_error)}")
                    if attempt < 3:
                        time.sleep(10)
                        continue
                
                # Get detailed run information for debugging
                try:
                    run_info = client.run(run_id).get()
                    logger.info(f"📋 Attempt {attempt}: Run details for {username}:")
                    logger.info(f"   Status: {run_info.get('status')}")
                    logger.info(f"   Started: {run_info.get('startedAt')}")
                    logger.info(f"   Finished: {run_info.get('finishedAt')}")
                    logger.info(f"   Stats: {run_info.get('stats', {})}")
                    
                    # Check if this is a final failure
                    if run_info.get('status') == 'FAILED' and attempt == 3:
                        logger.error(f"💥 FINAL FAILURE: Facebook scraper failed for {username} after 3 attempts")
                        return None
                except Exception as e:
                    logger.warning(f"Could not get detailed run info: {str(e)}")
                
                if attempt < 3:
                    logger.info(f"🔄 Retrying Facebook scraping for {username} (attempt {attempt + 1}/3)")
                    time.sleep(10)
                    continue
                else:
                    logger.error(f"❌ All attempts failed for Facebook user {username}")
                    return None
                    
            except Exception as e:
                logger.error(f"❌ Attempt {attempt}: Error scraping Facebook profile {username}: {str(e)}")
                if attempt < 3:
                    time.sleep(10)
                    continue
                else:
                    return None
        
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
                Prefix=f"facebook/{parent_username}/"
            )
            return 'Contents' in response and len(response['Contents']) > 0
        except Exception as e:
            logger.error(f"Error checking if directory exists in {bucket_name}: {str(e)}")
            return False
    
    def delete_previous_profile_data(self, username, bucket_name):
        """Delete previous profile data for a username in the specified bucket with graceful error handling."""
        try:
            # List all objects with the Facebook username prefix
            prefix = f"facebook/{username}/"
            response = self.s3.list_objects_v2(
                Bucket=bucket_name,
                Prefix=prefix
            )
            
            if 'Contents' in response:
                # Create a list of objects to delete
                objects_to_delete = [{'Key': obj['Key']} for obj in response['Contents']]
                
                if objects_to_delete:
                    # Delete the objects
                    self.s3.delete_objects(
                        Bucket=bucket_name,
                        Delete={'Objects': objects_to_delete}
                    )
                    logger.info(f"Deleted previous Facebook profile data for {username} in bucket {bucket_name}: {len(objects_to_delete)} objects")
                return True
            else:
                logger.info(f"No previous Facebook profile data found for {username} in bucket {bucket_name}")
                return False
        except Exception as e:
            if "NoSuchBucket" in str(e):
                logger.warning(f"Bucket {bucket_name} does not exist, skipping deletion for {username}")
            else:
                logger.error(f"Error deleting previous Facebook profile data for {username} in bucket {bucket_name}: {str(e)}")
            return False
    
    def upload_directory_to_both_buckets(self, local_directory, r2_prefix):
        """Upload directory to main and personal buckets with EXACT Instagram/Twitter schema - ONLY RAW DATA."""
        if not os.path.exists(local_directory):
            logger.error(f"Local directory does not exist: {local_directory}")
            return {"main_uploaded": False, "personal_uploaded": False, "success": False}
        
        main_bucket = self.r2_config['bucket_name']
        personal_bucket = self.r2_config['personal_bucket_name']
        
        # EXACT MATCH: facebook/username/ schema (same as Instagram/Twitter)
        facebook_prefix = f"facebook/{r2_prefix}"
        
        # Delete previous profile data before uploading (handle bucket errors gracefully)
        self.delete_previous_profile_data(r2_prefix, main_bucket)
        self.delete_previous_profile_data(r2_prefix, personal_bucket)
        
        # Upload to main bucket (structuredb) - ONLY RAW JSON FILES
        main_uploaded = False
        try:
            self.s3.put_object(Bucket=main_bucket, Key=f"{facebook_prefix}/")
            
            for filename in os.listdir(local_directory):
                local_file_path = os.path.join(local_directory, filename)
                if os.path.isdir(local_file_path):
                    continue
                
                # ONLY upload .json files (raw scraped data) - NO profile info files
                if not filename.endswith('.json'):
                    logger.info(f"Skipping non-JSON file: {filename}")
                    continue
                
                # SKIP any profile info files - only raw scraped data
                if 'profile_info' in filename:
                    logger.info(f"🚫 SKIPPING profile info file from structuredb: {filename}")
                    continue
                
                r2_key = f"{facebook_prefix}/{filename}"
                self.s3.upload_file(
                    local_file_path,
                    main_bucket,
                    r2_key,
                    ExtraArgs={'ContentType': 'application/json'}
                )
                logger.info(f"Uploaded Facebook RAW data to main bucket: {r2_key}")
            
            main_uploaded = True
            logger.info(f"Successfully uploaded Facebook directory to main bucket: {facebook_prefix}/")
        except Exception as e:
            if "NoSuchBucket" in str(e):
                logger.warning(f"Main bucket {main_bucket} does not exist, skipping main bucket upload")
            else:
                logger.error(f"Failed to upload Facebook directory to main bucket: {str(e)}")
            main_uploaded = False
        
        # Upload to personal bucket (with same filtering)
        personal_uploaded = False
        try:
            expiration_time = (datetime.now() + timedelta(days=1)).isoformat()
            self.s3.put_object(
                Bucket=personal_bucket,
                Key=f"{facebook_prefix}/",
                Metadata={'expiration-time': expiration_time}
            )
            
            for filename in os.listdir(local_directory):
                local_file_path = os.path.join(local_directory, filename)
                if os.path.isdir(local_file_path):
                    continue
                
                # ONLY upload .json files (raw scraped data) - NO profile info files
                if not filename.endswith('.json'):
                    continue
                
                # SKIP any profile info files - only raw scraped data
                if 'profile_info' in filename:
                    continue
                
                r2_key = f"{facebook_prefix}/{filename}"
                self.s3.upload_file(
                    local_file_path,
                    personal_bucket,
                    r2_key,
                    ExtraArgs={
                        'ContentType': 'application/json',
                        'Metadata': {'expiration-time': expiration_time}
                    }
                )
            
            logger.info(f"Successfully uploaded Facebook directory to personal bucket: {facebook_prefix}/")
            personal_uploaded = True
        except Exception as e:
            if "NoSuchBucket" in str(e):
                logger.warning(f"Personal bucket {personal_bucket} does not exist, skipping personal bucket upload")
            else:
                logger.error(f"Failed to upload Facebook directory to personal bucket: {str(e)}")
            personal_uploaded = False
        
        # Return success if at least one bucket upload succeeded
        success = main_uploaded or personal_uploaded
        if success:
            logger.info(f"Facebook upload completed - Main: {main_uploaded}, Personal: {personal_uploaded}")
        else:
            logger.error(f"All Facebook bucket uploads failed for {r2_prefix}")
        
        return {
            "main_uploaded": main_uploaded,
            "personal_uploaded": personal_uploaded,
            "success": success
        }
    
    def extract_short_profile_info(self, profile_data):
        """
        Extract shortened profile information from Facebook data.
        SKIP PROFILE INFO EXPLOITATION for Facebook as requested.
        """
        try:
            logger.info("🚫 SKIPPING Profile Info Exploitation for Facebook as requested")
            logger.info("📋 Facebook doesn't provide detailed profile metrics like Instagram/Twitter")
            
            # Return minimal profile info for Facebook
            if not profile_data or not isinstance(profile_data, list) or len(profile_data) == 0:
                logger.warning("No valid Facebook profile data to extract from")
                return None
            
            # Get basic info from first post
            first_item = profile_data[0] if profile_data else {}
            
            # Extract minimal user information available from Facebook posts
            profile_info = {
                "username": first_item.get("authorName", "unknown"),
                "platform": "facebook",
                "posts_count": len(profile_data),
                "profile_exploitation_skipped": True,
                "extraction_timestamp": datetime.now().isoformat(),
                "note": "Facebook profile info exploitation skipped - limited public data available"
            }
            
            logger.info(f"📋 Extracted minimal Facebook profile info: {profile_info['username']} with {profile_info['posts_count']} posts")
            return profile_info
            
        except Exception as e:
            logger.error(f"Error extracting Facebook profile info: {str(e)}")
            return None
    
    def _check_object_exists(self, bucket, key):
        """Check if an object exists in bucket."""
        try:
            self.s3.head_object(Bucket=bucket, Key=key)
            return True
        except ClientError:
            return False
    
    def upload_short_profile_to_tasks(self, profile_info):
        """Upload minimal profile info to tasks bucket (Facebook-specific)."""
        if not profile_info:
            logger.warning("No Facebook profile info to upload")
            return False
        
        try:
            tasks_bucket = "tasks"
            username = profile_info.get("username", "unknown")
            
            # Facebook profile info path
            profile_key = f"profile_info/facebook/{username}/profile_info.json"
            
            # Check if profile info already exists
            if self._check_object_exists(tasks_bucket, profile_key):
                logger.info(f"Facebook profile info already exists for {username}, skipping upload")
                return True
            
            # Upload profile info
            profile_json = json.dumps(profile_info, indent=2)
            self.s3.put_object(
                Bucket=tasks_bucket,
                Key=profile_key,
                Body=profile_json,
                ContentType='application/json'
            )
            
            logger.info(f"✅ Uploaded Facebook profile info to tasks bucket: {profile_key}")
            return True
            
        except Exception as e:
            logger.error(f"Error uploading Facebook profile info to tasks bucket: {str(e)}")
            return False
    
    def store_info_metadata(self, info_data):
        """Store account info metadata for Facebook."""
        try:
            if not info_data:
                logger.warning("No info metadata to store for Facebook")
                return False
            
            tasks_bucket = "tasks"
            username = info_data.get("username", "unknown")
            
            # Facebook info metadata path
            info_key = f"account_info/facebook/{username}/info.json"
            
            # Add Facebook-specific metadata
            facebook_info = {
                **info_data,
                "platform": "facebook",
                "profile_exploitation_available": False,
                "stored_timestamp": datetime.now().isoformat()
            }
            
            # Upload info metadata
            info_json = json.dumps(facebook_info, indent=2)
            self.s3.put_object(
                Bucket=tasks_bucket,
                Key=info_key,
                Body=info_json,
                ContentType='application/json'
            )
            
            logger.info(f"✅ Stored Facebook info metadata: {info_key}")
            return True
            
        except Exception as e:
            logger.error(f"Error storing Facebook info metadata: {str(e)}")
            return False
    
    def process_account_batch(self, parent_username, competitor_usernames, results_limit=50, info_metadata=None):
        """Process a batch of Facebook accounts (parent + competitors) matching Instagram/Twitter structure."""
        logger.info(f"🚀 Starting Facebook batch processing for {parent_username} with {len(competitor_usernames)} competitors")
        
        # Store info metadata if provided (only in tasks bucket)
        if info_metadata:
            info_metadata["username"] = parent_username
            info_metadata["platform"] = "facebook"
            self.store_info_metadata(info_metadata)
        
        # Process parent account and get raw data
        parent_data = self.scrape_profile(parent_username, results_limit)
        if not parent_data:
            logger.error(f"Failed to scrape parent Facebook account: {parent_username}")
            return {"success": False, "message": f"Failed to scrape parent Facebook account: {parent_username}"}
        
        # Create local directory for batch processing
        os.makedirs('temp', exist_ok=True)
        local_dir = self.create_local_directory(f"facebook_{parent_username}_{int(time.time())}")
        if not local_dir:
            logger.error(f"Failed to create local directory for {parent_username}")
            return {"success": False, "message": f"Failed to create local directory for {parent_username}"}
        
        # Save parent data as primary_username.json (EXACTLY like Instagram/Twitter)
        parent_file = f"{parent_username}.json"
        parent_path = self.save_to_local_file(parent_data, local_dir, parent_file)
        if not parent_path:
            logger.error(f"Failed to save parent data locally: {parent_username}")
            return {"success": False, "message": f"Failed to save parent data locally: {parent_username}"}
        
        # Process competitor accounts and save as competitor_username.json
        processed_competitors = []
        for competitor in competitor_usernames:
            if competitor and competitor.strip():
                competitor_data = self.scrape_profile(competitor.strip(), results_limit)
                if not competitor_data:
                    logger.warning(f"Failed to scrape competitor profile: {competitor}")
                    continue
                
                competitor_file = f"{competitor.strip()}.json"
                competitor_path = self.save_to_local_file(competitor_data, local_dir, competitor_file)
                if not competitor_path:
                    logger.warning(f"Failed to save competitor data locally: {competitor}")
                    continue
                
                processed_competitors.append(competitor.strip())
                logger.info(f"Successfully processed competitor: {competitor}")
        
        # Upload directory to structuredb bucket following EXACT Instagram/Twitter pattern
        # STRUCTURE: facebook/primary_username/primary_username.json + facebook/primary_username/competitor.json
        upload_result = self.upload_directory_to_both_buckets(local_dir, parent_username)
        
        # Clean up local directory
        try:
            shutil.rmtree(local_dir)
            logger.info(f"Cleaned up local directory: {local_dir}")
        except Exception as e:
            logger.warning(f"Error cleaning up local directory: {str(e)}")
        
        successful_competitors = len(processed_competitors)
        
        logger.info(f"✅ Facebook batch processing completed: {parent_username} (success), {successful_competitors}/{len(competitor_usernames)} competitors")
        
        return {
            "success": upload_result["success"],
            "message": f"Facebook batch processing completed",
            "parent_username": parent_username,
            "parent_success": True,
            "competitors_processed": len(competitor_usernames),
            "competitors_successful": successful_competitors,
            "competitor_results": [{"username": comp, "success": True} for comp in processed_competitors],
            "main_uploaded": upload_result["main_uploaded"],
            "personal_uploaded": upload_result["personal_uploaded"]
        }
    
    def scrape_and_upload(self, username, results_limit=50, info_metadata=None):
        """Scrape Facebook profile and upload to R2 storage - INDIVIDUAL PROCESSING (not batch)."""
        logger.info(f"🚀 Starting Facebook scrape and upload for: {username}")
        
        # Scrape the profile
        profile_data = self.scrape_profile(username, results_limit)
        if not profile_data:
            logger.error(f"Failed to scrape Facebook profile: {username}")
            return None
        
        # Create local directory
        local_directory = self.create_local_directory(f"facebook_{username}_{int(time.time())}")
        if not local_directory:
            logger.error(f"Failed to create local directory for {username}")
            return None
        
        # Save ONLY raw data as username.json (NO profile info files in structuredb)
        raw_file = self.save_to_local_file(profile_data, local_directory, f"{username}.json")
        if not raw_file:
            logger.error(f"Failed to save raw Facebook data for {username}")
            return None
        
        # Upload to R2 buckets (will only upload .json files, not profile info)
        upload_result = self.upload_directory_to_both_buckets(local_directory, username)
        
        # Cleanup local directory
        try:
            shutil.rmtree(local_directory)
            logger.info(f"Cleaned up local directory: {local_directory}")
        except Exception as e:
            logger.warning(f"Error cleaning up local directory: {str(e)}")
        
        if upload_result["success"]:
            logger.info(f"✅ Successfully completed Facebook scrape and upload for: {username}")
            return {
                "username": username,
                "platform": "facebook",
                "success": True,
                "posts_scraped": len(profile_data),
                "upload_result": upload_result
            }
        else:
            logger.error(f"❌ Failed to upload Facebook data for: {username}")
            return None
    
    def continuous_processing_loop(self, sleep_interval=86400, check_interval=300):
        """Run continuous processing loop for Facebook accounts."""
        logger.info(f"🚀 Starting Facebook continuous processing loop (sleep: {sleep_interval}s, check: {check_interval}s)")
        self.running = True
        
        while self.running:
            try:
                # Check for new pending Facebook files
                if self._check_for_new_pending_facebook_files():
                    logger.info("📋 Found new pending Facebook files, processing them...")
                    self.retrieve_and_process_facebook_usernames()
                else:
                    logger.info("✨ No new pending Facebook files found")
                
                # Update last check time
                self.last_check_time = datetime.now()
                
                # Sleep for check interval
                logger.info(f"💤 Sleeping for {check_interval} seconds before next check...")
                time.sleep(check_interval)
                
            except KeyboardInterrupt:
                logger.info("👋 Facebook processing interrupted by user")
                self.running = False
                break
            except Exception as e:
                logger.error(f"❌ Error in Facebook continuous processing loop: {str(e)}")
                time.sleep(60)  # Wait 60 seconds before retry on error
    
    def _check_for_new_pending_facebook_files(self):
        """Check for new pending Facebook processing files."""
        try:
            tasks_bucket = "tasks"
            pending_prefix = "pending_facebook/"
            
            response = self.s3.list_objects_v2(
                Bucket=tasks_bucket,
                Prefix=pending_prefix
            )
            
            if 'Contents' in response:
                # Check if any files are newer than last check
                if self.last_check_time is None:
                    return len(response['Contents']) > 0
                
                for obj in response['Contents']:
                    obj_time = obj['LastModified'].replace(tzinfo=None)
                    if obj_time > self.last_check_time:
                        return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking for new pending Facebook files: {str(e)}")
            return False
    
    def retrieve_and_process_facebook_usernames(self):
        """Retrieve and process Facebook usernames from pending files."""
        try:
            tasks_bucket = "tasks"
            pending_prefix = "pending_facebook/"
            
            # List all pending Facebook files
            response = self.s3.list_objects_v2(
                Bucket=tasks_bucket,
                Prefix=pending_prefix
            )
            
            if 'Contents' not in response:
                logger.info("No pending Facebook files found")
                return
            
            for obj in response['Contents']:
                try:
                    key = obj['Key']
                    logger.info(f"📋 Processing pending Facebook file: {key}")
                    
                    # Download and parse the file
                    response_obj = self.s3.get_object(Bucket=tasks_bucket, Key=key)
                    file_content = response_obj['Body'].read().decode('utf-8')
                    account_data = json.loads(file_content)
                    
                    # Extract account information
                    username = account_data.get('username', '')
                    competitors = account_data.get('competitors', [])
                    account_type = account_data.get('accountType', '')
                    posting_style = account_data.get('postingStyle', '')
                    
                    if not username:
                        logger.warning(f"No username found in {key}, skipping")
                        continue
                    
                    logger.info(f"🎯 Processing Facebook account: {username} (type: {account_type}, competitors: {len(competitors)})")
                    
                    # Process the account batch
                    result = self.process_account_batch(
                        parent_username=username,
                        competitor_usernames=competitors,
                        results_limit=50,
                        info_metadata={
                            'accountType': account_type,
                            'postingStyle': posting_style,
                            'competitors': competitors
                        }
                    )
                    
                    if result and result.get('success'):
                        logger.info(f"✅ Successfully processed Facebook account: {username}")
                        
                        # Move processed file to completed folder
                        completed_key = key.replace('pending_facebook/', 'completed_facebook/')
                        self.s3.copy_object(
                            Bucket=tasks_bucket,
                            CopySource={'Bucket': tasks_bucket, 'Key': key},
                            Key=completed_key
                        )
                        self.s3.delete_object(Bucket=tasks_bucket, Key=key)
                        logger.info(f"📁 Moved {key} to {completed_key}")
                    else:
                        logger.error(f"❌ Failed to process Facebook account: {username}")
                        
                        # Move failed file to failed folder
                        failed_key = key.replace('pending_facebook/', 'failed_facebook/')
                        self.s3.copy_object(
                            Bucket=tasks_bucket,
                            CopySource={'Bucket': tasks_bucket, 'Key': key},
                            Key=failed_key
                        )
                        self.s3.delete_object(Bucket=tasks_bucket, Key=key)
                        logger.info(f"📁 Moved {key} to {failed_key}")
                
                except Exception as e:
                    logger.error(f"Error processing Facebook file {obj['Key']}: {str(e)}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error in retrieve_and_process_facebook_usernames: {str(e)}")
    
    def stop_processing(self):
        """Stop the continuous processing loop."""
        logger.info("🛑 Stopping Facebook processing loop...")
        self.running = False

def test_facebook_scraper():
    """Test function for Facebook scraper."""
    logger.info("🧪 Testing Facebook scraper...")
    
    scraper = FacebookScraper()
    
    # Test scraping a Facebook profile
    test_username = "zuck"  # Mark Zuckerberg's public Facebook page
    result = scraper.scrape_profile(test_username, results_limit=10)
    
    if result:
        logger.info(f"✅ Facebook scraper test successful! Scraped {len(result)} items for {test_username}")
    else:
        logger.error(f"❌ Facebook scraper test failed for {test_username}")
    
    return result

if __name__ == "__main__":
    test_facebook_scraper()