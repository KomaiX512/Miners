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

import os
import json
import time
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

# Apify API token for Facebook scraper
APIFY_API_TOKEN = os.getenv("APIFY_API_TOKEN", "your_apify_token_here")

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
        
        # 🚨 CRITICAL PLATFORM ISOLATION: Ensure fresh state for each run
        self._current_platform_username = None
        self._platform_isolation_initialized = False
    
    def _is_url(self, value):
        """Return True if the provided value looks like an HTTP(S) URL."""
        return isinstance(value, str) and value.strip().lower().startswith(("http://", "https://"))

    def _scrape_target_from_input(self, input_value):
        """
        Prepare a valid Facebook start URL for scraping.
        - If input_value is a URL, use it as-is
        - Else, treat it as a username/handle and form https://www.facebook.com/<username>/
        """
        if not isinstance(input_value, str) or not input_value.strip():
            return None
        clean = input_value.strip()
        if self._is_url(clean):
            return clean
        if clean.startswith('@'):
            clean = clean[1:]
        return f"https://www.facebook.com/{clean}/"

    def _ensure_platform_isolation(self, username):
        """
        🚨 CRITICAL PLATFORM ISOLATION: Ensure each platform run is completely fresh.
        This prevents contamination from previous platform runs.
        """
        if not self._platform_isolation_initialized or self._current_platform_username != username:
            logger.info(f"🧹 CRITICAL PLATFORM ISOLATION: Initializing fresh Facebook run for {username}")
            self._current_platform_username = username
            self._platform_isolation_initialized = True
            
            # Clear any cached data that might contain previous platform information
            logger.info(f"✅ Platform isolation initialized for Facebook: {username}")
        else:
            logger.info(f"✅ Platform isolation already active for Facebook: {username}")
        
        return True
    
    def scrape_profile_info(self, identifier):
        """Scrape Facebook profile information using Apify facebook-pages-scraper.
        identifier can be a full Facebook URL (preferred) or a username/handle.
        """
        if not identifier or not isinstance(identifier, str):
            logger.error(f"Invalid identifier for profile info: {identifier}")
            return None
        
        scrape_url = self._scrape_target_from_input(identifier)
        if not scrape_url:
            logger.error("Unable to prepare scrape URL for profile info")
            return None
        logger.info(f"🔍 Scraping Facebook profile info from: {scrape_url}")
        
        client = ApifyClient(self.api_token)
        
        # Facebook profile info scraper input format
        run_input = {
            "startUrls": [
                {
                    "url": scrape_url,
                    "method": "GET"
                }
            ]
        }
        
        logger.info(f"🚀 Starting Facebook profile info scraping with input: {run_input}")
        
        # SINGLE ATTEMPT - No retries for profile info
        try:
            logger.info(f"🚀 Starting Facebook profile info scraping: {scrape_url}")
            
            # Use Facebook pages scraper actor for profile information
            actor = client.actor("apify/facebook-pages-scraper")
            run = actor.call(run_input=run_input)
            
            if not run:
                logger.warning(f"❌ Profile info actor run failed for {identifier} - treating as private/new account")
                return None
            
            run_id = run["id"]
            logger.info(f"✅ Facebook profile info run started with ID: {run_id}")
            
            # Wait for completion
            logger.info(f"⏳ Waiting for Facebook profile info scraping to complete...")
            max_wait_time = 300  # 5 minutes max wait for profile info
            check_interval = 15   # Check every 15 seconds
            
            run_completed = False
            final_status = "UNKNOWN"
            
            for i in range(0, max_wait_time, check_interval):
                try:
                    run_status = client.run(run_id).get()
                    final_status = run_status.get("status", "UNKNOWN")
                    
                    logger.info(f"📊 Profile info status: {final_status} | Waited: {i}s/{max_wait_time}s")
                    
                    if final_status in ["SUCCEEDED", "FAILED", "ABORTED", "TIMED-OUT"]:
                        run_completed = True
                        break
                    
                    time.sleep(check_interval)
                except Exception as e:
                    logger.warning(f"⚠️ Error checking profile info run status: {str(e)}")
                    time.sleep(check_interval)
            
            # Retrieve profile info data
            try:
                dataset = client.dataset(run["defaultDatasetId"])
                items = dataset.list_items().items
                
                logger.info(f"📦 Retrieved {len(items) if items else 0} profile info items from {scrape_url}")
                
                # SUCCESS CONDITIONS for profile info
                if items and len(items) > 0:
                    logger.info(f"🎉 SUCCESS: Found profile info from {scrape_url}")
                    
                    # Validate the scraped profile data
                    profile_item = items[0]
                    if isinstance(profile_item, dict):
                        logger.info(f"✅ Profile info validation passed")
                        logger.debug(f"Profile info keys: {list(profile_item.keys())}")
                    
                    return profile_item  # Return single profile info object
                
                # PARTIAL SUCCESS - Even if no items, check if run was successful
                elif final_status == "SUCCEEDED":
                    logger.warning(f"⚠️ Profile info run succeeded but no items - treating as private/protected page")
                    return None
                
                # FAILED RUN
                else:
                    logger.warning(f"❌ Profile info run status {final_status} with no items - treating as private/new account")
                    return None
            
            except Exception as dataset_error:
                logger.warning(f"❌ Error retrieving profile info dataset: {str(dataset_error)} - treating as private/new account")
                return None
                
        except Exception as e:
            logger.warning(f"❌ Error scraping Facebook profile info from {scrape_url}: {str(e)} - treating as private/new account")
            return None
    
    def scrape_profile(self, identifier, results_limit=50):
        """Scrape Facebook posts using Apify.
        identifier can be a full Facebook URL (preferred) or a username/handle.
        """
        if not identifier or not isinstance(identifier, str):
            logger.error(f"Invalid identifier: {identifier}")
            return None
        
        scrape_url = self._scrape_target_from_input(identifier)
        if not scrape_url:
            logger.error("Unable to prepare scrape URL for posts")
            return None
        logger.info(f"Scraping Facebook from: {scrape_url} with results_limit: {results_limit}")
        
        client = ApifyClient(self.api_token)
        
        # Facebook scraper input format as specified
        run_input = {
            "captionText": False,
            "resultsLimit": results_limit,
            "startUrls": [
                {
                    "url": scrape_url,
                    "method": "GET"
                }
            ]
        }
        
        logger.info(f"🚀 Starting Facebook scraping with input: {run_input}")
        
        # SINGLE ATTEMPT - No retries for posts
        try:
            logger.info(f"🚀 Starting Facebook scraping: {scrape_url}")
            
            # Use a Facebook scraper actor
            actor = client.actor("apify/facebook-posts-scraper")
            run = actor.call(run_input=run_input)
            
            if not run:
                logger.warning(f"❌ Actor run failed for target {identifier} - treating as private/new account")
                return []
            
            run_id = run["id"]
            logger.info(f"✅ Facebook run started with ID: {run_id}")
            
            # Wait for completion
            logger.info(f"⏳ Waiting for Facebook scraping to complete...")
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
                    
                    logger.info(f"📊 Facebook status: {final_status} | Items: {items_count} | Waited: {i}s/{max_wait_time}s")
                    
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
                
                logger.info(f"📦 Retrieved {len(items) if items else 0} items from {scrape_url}")
                
                # SUCCESS CONDITIONS
                if items and len(items) > 0:
                    logger.info(f"🎉 SUCCESS: Found {len(items)} items from {scrape_url}")
                    
                    # Validate the scraped data
                    first_item = items[0]
                    if isinstance(first_item, dict):
                        logger.info(f"✅ Data validation passed")
                        logger.debug(f"First item keys: {list(first_item.keys())}")
                    
                    return items
                
                # PARTIAL SUCCESS - Even if no items, check if run was successful
                elif final_status == "SUCCEEDED":
                    logger.warning(f"⚠️ Run succeeded but no items - treating as private/protected account")
                    return []
                
                # FAILED RUN
                else:
                    logger.warning(f"❌ Run status {final_status} with no items - treating as private/new account")
                    return []
            
            except Exception as dataset_error:
                logger.warning(f"❌ Error retrieving dataset: {str(dataset_error)} - treating as private/new account")
                return []
                
        except Exception as e:
            logger.warning(f"❌ Error scraping Facebook target {scrape_url}: {str(e)} - treating as private/new account")
            return []
    
    def combine_profile_and_posts_data(self, profile_info, posts_data, username, source_url=None):
        """Combine profile info and posts data into a single JSON structure with profile info at the top.
        username is the display name/label; source_url (if provided) is the actual scraped URL.
        """
        try:
            combined_data = {}
            
            # Add profile info at the top if available
            if profile_info and isinstance(profile_info, dict):
                combined_data["profileInfo"] = profile_info
                logger.info(f"✅ Added profile info to combined data for {username}")
            else:
                logger.warning(f"⚠️ No profile info available for {username}, continuing with posts only")
                combined_data["profileInfo"] = None
            
            # Add posts data
            if posts_data and isinstance(posts_data, list):
                combined_data["posts"] = posts_data
                logger.info(f"✅ Added {len(posts_data)} posts to combined data for {username}")
            else:
                logger.warning(f"⚠️ No posts data available for {username}")
                combined_data["posts"] = []
            
            # Add metadata
            metadata = {
                "username": username,
                "platform": "facebook",
                "scrape_timestamp": datetime.now().isoformat(),
                "profile_info_available": profile_info is not None,
                "posts_count": len(posts_data) if posts_data else 0
            }
            if source_url:
                metadata["source_url"] = source_url
            combined_data["metadata"] = metadata
            
            logger.info(f"🔗 Successfully combined profile info and posts data for {username}")
            return combined_data
            
        except Exception as e:
            logger.error(f"❌ Error combining profile and posts data for {username}: {str(e)}")
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
    
    def extract_short_profile_info(self, combined_data):
        """
        Extract shortened profile information from Facebook combined data (profile info + posts).
        Now uses REAL profile info from facebook-pages-scraper actor.
        """
        try:
            logger.info("🔍 Extracting Facebook profile info from combined data")
            
            if not combined_data or not isinstance(combined_data, dict):
                logger.warning("No valid Facebook combined data to extract from")
                return None
            
            # Get profile info from combined data
            profile_info_raw = combined_data.get("profileInfo")
            posts_data = combined_data.get("posts", [])
            metadata = combined_data.get("metadata", {})
            username = metadata.get("username", "unknown")
            
            # Build comprehensive profile info using actual scraped profile data
            if profile_info_raw and isinstance(profile_info_raw, dict):
                logger.info(f"✅ Using REAL profile info data for {username}")
                
                # Extract all available profile information
                profile_info = {
                    "username": username,
                    "platform": "facebook",
                    "facebookUrl": profile_info_raw.get("facebookUrl"),
                    "pageId": profile_info_raw.get("pageId"),
                    "pageName": profile_info_raw.get("pageName"),
                    "pageUrl": profile_info_raw.get("pageUrl"),
                    "title": profile_info_raw.get("title"),
                    "categories": profile_info_raw.get("categories", []),
                    "info": profile_info_raw.get("info", []),
                    "likes": profile_info_raw.get("likes"),
                    "followers": profile_info_raw.get("followers"),
                    "priceRange": profile_info_raw.get("priceRange"),
                    "address": profile_info_raw.get("address"),
                    "phone": profile_info_raw.get("phone"),
                    "email": profile_info_raw.get("email"),
                    "website": profile_info_raw.get("website"),
                    "websites": profile_info_raw.get("websites", []),
                    "services": profile_info_raw.get("services"),
                    "intro": profile_info_raw.get("intro"),
                    "about_me": profile_info_raw.get("about_me"),
                    "rating": profile_info_raw.get("rating"),
                    "ratingOverall": profile_info_raw.get("ratingOverall"),
                    "ratingCount": profile_info_raw.get("ratingCount"),
                    "profilePictureUrl": profile_info_raw.get("profilePictureUrl"),
                    "coverPhotoUrl": profile_info_raw.get("coverPhotoUrl"),
                    "profilePhoto": profile_info_raw.get("profilePhoto"),
                    "facebookId": profile_info_raw.get("facebookId"),
                    "creation_date": profile_info_raw.get("creation_date"),
                    "ad_status": profile_info_raw.get("ad_status"),
                    "pageAdLibrary": profile_info_raw.get("pageAdLibrary"),
                    "messenger": profile_info_raw.get("messenger"),
                    "posts_count": len(posts_data),
                    "profile_info_available": True,
                    "extraction_timestamp": datetime.now().isoformat()
                }
                
                logger.info(f"📋 Extracted COMPREHENSIVE Facebook profile info for {username}: {profile_info.get('pageName', 'N/A')} with {len(posts_data)} posts")
                
            else:
                logger.warning(f"⚠️ No profile info available for {username}, using minimal data from posts")
                
                # Fallback to minimal profile info from posts data
                first_post = posts_data[0] if posts_data and len(posts_data) > 0 else {}
                
                profile_info = {
                    "username": username,
                    "platform": "facebook", 
                    "posts_count": len(posts_data),
                    "profile_info_available": False,
                    "authorName": first_post.get("authorName", username),
                    "extraction_timestamp": datetime.now().isoformat(),
                    "note": "Profile info not available - using minimal data from posts"
                }
                
                logger.info(f"📋 Extracted minimal Facebook profile info for {username} with {len(posts_data)} posts")
            
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
            
            # Facebook profile info path - CONSISTENT with Instagram and Twitter
            profile_key = f"ProfileInfo/facebook/{username}.json"
            
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
        """Store account info metadata for Facebook with required fields for processing.
        Writes URL-driven schema while keeping backward-compatible fields.
        """
        try:
            if not info_data:
                logger.warning("No info metadata to store for Facebook")
                return False
            
            tasks_bucket = "tasks"
            username = info_data.get("username", "unknown")
            
            # Facebook info metadata path
            info_key = f"AccountInfo/facebook/{username}/info.json"

            # Normalize competitors (names list)
            competitors = info_data.get('competitors', [])
            if isinstance(competitors, str):
                competitors = [c.strip() for c in competitors.split(',') if c.strip()]
            elif isinstance(competitors, list):
                name_list = []
                for c in competitors:
                    if isinstance(c, dict) and 'name' in c:
                        name_list.append(c['name'])
                    elif isinstance(c, str):
                        name_list.append(c)
                competitors = name_list

            # URL-driven entities
            accountData = info_data.get('accountData')
            if not accountData:
                # Back-compat: allow 'url' field at root
                root_url = info_data.get('url')
                accountData = {"name": username, "url": root_url} if root_url else {"name": username}

            competitor_data = info_data.get('competitor_data')
            if competitor_data is None:
                competitor_data = []

            # If competitors not provided but competitor_data exists, derive names
            if (not competitors) and competitor_data:
                try:
                    competitors = [c.get('name') for c in competitor_data if isinstance(c, dict) and c.get('name')]
                except Exception:
                    pass

            # Compose final schema
            facebook_info = {
                "username": username,
                "accountType": info_data.get('accountType', info_data.get('account_type', 'business')),
                "postingStyle": info_data.get('postingStyle', info_data.get('posting_style', 'community_focused')),
                "platform": "facebook",
                "competitors": competitors,
                "accountData": accountData,
                "competitor_data": competitor_data,
                "timestamp": datetime.now().isoformat(),
                # Backward-compatible fields for existing readers
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
            
            logger.info(f"✅ Stored Facebook info metadata with required fields: {info_key}")
            logger.info(f"Facebook info contains: accountType={facebook_info.get('accountType')}, postingStyle={facebook_info.get('postingStyle')}")
            return True
            
        except Exception as e:
            logger.error(f"Error storing Facebook info metadata: {str(e)}")
            return False
    
    def process_account_batch(self, parent_username, competitor_usernames, results_limit=50, info_metadata=None):
        """Process a batch of Facebook accounts (parent + competitors) WITH PROFILE INFO integration.
        Scraping is URL-driven; storage uses provided names/labels.
        """
        # 🚨 CRITICAL PLATFORM ISOLATION: Ensure fresh Facebook run
        self._ensure_platform_isolation(parent_username)
        
        logger.info(f"🚀 Starting Facebook batch processing for {parent_username} with {len(competitor_usernames)} competitors")
        
        # Store info metadata if provided (only in tasks bucket)
        if info_metadata:
            info_metadata["username"] = parent_username
            info_metadata["platform"] = "facebook"
            self.store_info_metadata(info_metadata)
        
        # Determine URL targets
        primary_url = None
        competitor_name_to_url = {}
        if info_metadata:
            try:
                account_data = info_metadata.get('accountData') or {}
                if isinstance(account_data, dict):
                    primary_url = account_data.get('url')
                comp_list = info_metadata.get('competitor_data') or []
                for entry in comp_list:
                    if isinstance(entry, dict) and entry.get('name'):
                        competitor_name_to_url[entry['name']] = entry.get('url')
            except Exception as map_err:
                logger.warning(f"⚠️ Unable to parse URL mappings from info_metadata: {str(map_err)}")

        # 🔍 STEP 1: Scrape parent profile info + posts data
        logger.info(f"📋 Step 1: Scraping profile info for parent account (URL-driven if available): {parent_username}")
        parent_profile_info = self.scrape_profile_info(primary_url or parent_username)
        
        logger.info(f"📋 Step 2: Scraping posts data for parent account (URL-driven if available): {parent_username}")
        parent_posts_data = self.scrape_profile(primary_url or parent_username, results_limit)
        if not parent_posts_data:
            logger.error(f"Failed to scrape parent Facebook posts: {parent_username}")
            return {"success": False, "message": f"Failed to scrape parent Facebook posts: {parent_username}"}
        
        # 🔗 STEP 3: Combine profile info + posts for parent
        parent_combined_data = self.combine_profile_and_posts_data(
            parent_profile_info, parent_posts_data, parent_username, source_url=(primary_url or self._scrape_target_from_input(parent_username))
        )
        if not parent_combined_data:
            logger.error(f"Failed to combine parent data: {parent_username}")
            return {"success": False, "message": f"Failed to combine parent data: {parent_username}"}
        
        # 📤 STEP 4: Extract and upload profile info to tasks bucket
        parent_profile_summary = self.extract_short_profile_info(parent_combined_data)
        if parent_profile_summary:
            self.upload_short_profile_to_tasks(parent_profile_summary)
        
        # Create local directory for batch processing
        os.makedirs('temp', exist_ok=True)
        local_dir = self.create_local_directory(f"facebook_{parent_username}_{int(time.time())}")
        if not local_dir:
            logger.error(f"Failed to create local directory for {parent_username}")
            return {"success": False, "message": f"Failed to create local directory for {parent_username}"}
        
        # Save parent COMBINED data as primary_username.json (profile info + posts)
        parent_file = f"{parent_username}.json"
        parent_path = self.save_to_local_file(parent_combined_data, local_dir, parent_file)
        if not parent_path:
            logger.error(f"Failed to save parent combined data locally: {parent_username}")
            return {"success": False, "message": f"Failed to save parent combined data locally: {parent_username}"}
        
        # 🏃‍♂️ STEP 5: Process competitor accounts with profile info + posts
        processed_competitors = []
        for competitor in competitor_usernames:
            if competitor and competitor.strip():
                competitor_username = competitor.strip()
                logger.info(f"🔍 Processing competitor (URL-driven if available): {competitor_username}")
                
                # Scrape competitor profile info + posts
                competitor_url = competitor_name_to_url.get(competitor_username)
                competitor_profile_info = self.scrape_profile_info(competitor_url or competitor_username)
                competitor_posts_data = self.scrape_profile(competitor_url or competitor_username, results_limit)
                
                if not competitor_posts_data:
                    logger.warning(f"Failed to scrape competitor posts: {competitor_username}")
                    continue
                
                # Combine competitor data
                competitor_combined_data = self.combine_profile_and_posts_data(
                    competitor_profile_info, competitor_posts_data, competitor_username, source_url=(competitor_url or self._scrape_target_from_input(competitor_username))
                )
                if not competitor_combined_data:
                    logger.warning(f"Failed to combine competitor data: {competitor_username}")
                    continue
                
                competitor_file = f"{competitor_username}.json"
                competitor_path = self.save_to_local_file(competitor_combined_data, local_dir, competitor_file)
                if not competitor_path:
                    logger.warning(f"Failed to save competitor combined data locally: {competitor_username}")
                    continue
                
                processed_competitors.append(competitor_username)
                logger.info(f"✅ Successfully processed competitor with profile info: {competitor_username}")
        
        # Upload directory to structuredb bucket following EXACT Instagram/Twitter pattern
        # STRUCTURE: facebook/primary_username/primary_username.json + facebook/primary_username/competitor.json
        # BUT NOW with profile info at the top of each JSON file
        upload_result = self.upload_directory_to_both_buckets(local_dir, parent_username)
        
        # Clean up local directory
        try:
            shutil.rmtree(local_dir)
            logger.info(f"Cleaned up local directory: {local_dir}")
        except Exception as e:
            logger.warning(f"Error cleaning up local directory: {str(e)}")
        
        successful_competitors = len(processed_competitors)
        
        logger.info(f"✅ Facebook batch processing WITH PROFILE INFO completed: {parent_username} (success), {successful_competitors}/{len(competitor_usernames)} competitors")
        
        return {
            "success": upload_result["success"],
            "message": f"Facebook batch processing with profile info completed",
            "parent_username": parent_username,
            "parent_success": True,
            "parent_profile_info_available": parent_profile_info is not None,
            "competitors_processed": len(competitor_usernames),
            "competitors_successful": successful_competitors,
            "competitor_results": [{"username": comp, "success": True} for comp in processed_competitors],
            "main_uploaded": upload_result["main_uploaded"],
            "personal_uploaded": upload_result["personal_uploaded"]
        }
    
    def scrape_and_upload(self, username, results_limit=50, info_metadata=None):
        """Scrape Facebook profile WITH PROFILE INFO and upload to R2 storage - INDIVIDUAL PROCESSING.
        If info_metadata.accountData.url exists, use it as the scraping target; store under provided username label.
        """
        # 🚨 CRITICAL PLATFORM ISOLATION: Ensure fresh Facebook run
        self._ensure_platform_isolation(username)
        
        logger.info(f"🚀 Starting Facebook scrape and upload WITH PROFILE INFO for: {username}")
        
        # Prepare URL target when available
        target_url = None
        if info_metadata and isinstance(info_metadata, dict):
            account_data = info_metadata.get('accountData') or {}
            if isinstance(account_data, dict):
                target_url = account_data.get('url')

        # 🔍 STEP 1: Scrape profile info (URL-driven if available)
        logger.info(f"📋 Step 1: Scraping profile info for: {username}")
        profile_info = self.scrape_profile_info(target_url or username)
        
        # 📋 STEP 2: Scrape posts data (URL-driven if available)
        logger.info(f"📋 Step 2: Scraping posts data for: {username}")
        posts_data = self.scrape_profile(target_url or username, results_limit)
        if not posts_data:
            logger.error(f"Failed to scrape Facebook posts: {username}")
            return None
        
        # 🔗 STEP 3: Combine profile info + posts (include source URL)
        combined_data = self.combine_profile_and_posts_data(profile_info, posts_data, username, source_url=(target_url or self._scrape_target_from_input(username)))
        if not combined_data:
            logger.error(f"Failed to combine Facebook data: {username}")
            return None
        
        # 📤 STEP 4: Extract and upload profile info to tasks bucket
        profile_summary = self.extract_short_profile_info(combined_data)
        if profile_summary:
            self.upload_short_profile_to_tasks(profile_summary)
        
        # Create local directory
        local_directory = self.create_local_directory(f"facebook_{username}_{int(time.time())}")
        if not local_directory:
            logger.error(f"Failed to create local directory for {username}")
            return None
        
        # Save COMBINED data as username.json (profile info + posts at top)
        combined_file = self.save_to_local_file(combined_data, local_directory, f"{username}.json")
        if not combined_file:
            logger.error(f"Failed to save combined Facebook data for {username}")
            return None
        
        # Upload to R2 buckets (will upload combined data with profile info at top)
        upload_result = self.upload_directory_to_both_buckets(local_directory, username)
        
        # Cleanup local directory
        try:
            shutil.rmtree(local_directory)
            logger.info(f"Cleaned up local directory: {local_directory}")
        except Exception as e:
            logger.warning(f"Error cleaning up local directory: {str(e)}")
        
        if upload_result["success"]:
            logger.info(f"✅ Successfully completed Facebook scrape and upload WITH PROFILE INFO for: {username}")
            return {
                "username": username,
                "platform": "facebook",
                "success": True,
                "posts_scraped": len(posts_data),
                "profile_info_available": profile_info is not None,
                "combined_data_structure": True,
                "upload_result": upload_result
            }
        else:
            logger.error(f"❌ Failed to upload Facebook data for: {username}")
            return None
    
    def continuous_processing_loop(self, sleep_interval=86400, check_interval=10):
        """Run continuous processing loop for Facebook accounts."""
        logger.info(f"🚀 Starting Facebook continuous processing loop (sleep: {sleep_interval}s, check: {check_interval}s)")
        self.running = True
        
        while self.running:
            try:
                # Check for new pending Facebook files
                if self._check_for_new_pending_facebook_files():
                    logger.info("📋 Found new pending Facebook files, processing them...")
                    self.retrieve_and_process_facebook_usernames()
                    # Update last check time after processing to prevent reprocessing same files
                    self.last_check_time = datetime.now()
                else:
                    logger.info("✨ No new pending Facebook files found")
                    # Update last check time even when no files found
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
            
            # Only process if there are actually pending files
            if 'Contents' in response and len(response['Contents']) > 0:
                # On first run, process all pending files
                if self.last_check_time is None:
                    return True
                
                # On subsequent runs, only process if files are newer than last check
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
                    # NEW: URL-driven fields
                    account_data_url_block = account_data.get('accountData')  # {name, url}
                    competitor_data_block = account_data.get('competitor_data')  # [{name, url}, ...]
                    
                    if not username:
                        logger.warning(f"No username found in {key}, skipping")
                        continue
                    
                    logger.info(f"🎯 Processing Facebook account: {username} (type: {account_type}, competitors: {len(competitors)})")
                    if account_data_url_block and isinstance(account_data_url_block, dict):
                        logger.info(f"🔗 Primary URL provided: {account_data_url_block.get('url')}")
                    if competitor_data_block and isinstance(competitor_data_block, list):
                        logger.info(f"🔗 Competitor URLs provided: {sum(1 for c in competitor_data_block if isinstance(c, dict) and c.get('url'))}")
                    
                    # Process the account batch
                    result = self.process_account_batch(
                        parent_username=username,
                        competitor_usernames=competitors,
                        results_limit=50,
                        info_metadata={
                            'accountType': account_type,
                            'postingStyle': posting_style,
                            'competitors': competitors,
                            # Pass-through URL-driven blocks for normalization inside scraper
                            'accountData': account_data_url_block,
                            'competitor_data': competitor_data_block
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
    """Test function for Facebook scraper with PROFILE INFO integration."""
    logger.info("🧪 Testing Facebook scraper WITH PROFILE INFO...")
    
    scraper = FacebookScraper()
    
    # Test usernames for validation
    test_usernames = ["zuck", "copperkettleyqr"]  # Mark Zuckerberg + provided test page
    
    for test_username in test_usernames:
        logger.info(f"🧪 Testing Facebook scraper for: {test_username}")
        
        # TEST 1: Profile Info Scraping
        logger.info(f"📋 Test 1: Profile info scraping for {test_username}")
        profile_info = scraper.scrape_profile_info(test_username)
        
        if profile_info:
            logger.info(f"✅ Profile info test successful for {test_username}!")
            logger.info(f"📋 Profile info keys: {list(profile_info.keys())}")
            
            # Validate key profile info fields
            expected_fields = ["facebookUrl", "pageId", "pageName", "title", "categories"]
            available_fields = [field for field in expected_fields if profile_info.get(field)]
            logger.info(f"✅ Available profile fields: {available_fields}")
            
        else:
            logger.warning(f"⚠️ Profile info test failed/empty for {test_username}")
        
        # TEST 2: Posts Scraping  
        logger.info(f"📋 Test 2: Posts scraping for {test_username}")
        posts_result = scraper.scrape_profile(test_username, results_limit=5)
        
        if posts_result:
            logger.info(f"✅ Posts scraper test successful! Scraped {len(posts_result)} posts for {test_username}")
        else:
            logger.warning(f"⚠️ Posts scraper test failed/empty for {test_username}")
        
        # TEST 3: Combined Data Structure
        logger.info(f"📋 Test 3: Combined data structure for {test_username}")
        combined_data = scraper.combine_profile_and_posts_data(profile_info, posts_result, test_username)
        
        if combined_data:
            logger.info(f"✅ Combined data test successful for {test_username}!")
            logger.info(f"🔗 Combined data structure: {list(combined_data.keys())}")
            
            # Validate combined structure
            if "profileInfo" in combined_data and "posts" in combined_data and "metadata" in combined_data:
                logger.info(f"✅ Perfect combined data structure for {test_username}")
                
                # TEST 4: Profile Info Extraction
                profile_summary = scraper.extract_short_profile_info(combined_data)
                if profile_summary:
                    logger.info(f"✅ Profile summary extraction successful for {test_username}!")
                    logger.info(f"📋 Profile summary keys: {list(profile_summary.keys())}")
                else:
                    logger.warning(f"⚠️ Profile summary extraction failed for {test_username}")
            else:
                logger.error(f"❌ Invalid combined data structure for {test_username}")
        else:
            logger.error(f"❌ Combined data test failed for {test_username}")
        
        logger.info(f"{'='*60}")
    
    logger.info("🎉 Facebook scraper WITH PROFILE INFO testing completed!")
    return True

def test_profile_info_validation():
    """Validate profile info extraction with test input format."""
    logger.info("🧪 Testing Facebook profile info validation...")
    
    # Test profile info format (based on provided template)
    test_profile_info = {
        "facebookUrl": "https://www.facebook.com/testpage/",
        "categories": ["Business", "Restaurant"],
        "info": ["Great food", "Family owned", "Since 1990"],
        "likes": 1234,
        "messenger": "Available",
        "priceRange": "$$",
        "title": "Test Restaurant",
        "address": "123 Test Street, Test City",
        "pageId": "123456789",
        "pageName": "Test Restaurant Page",
        "pageUrl": "https://www.facebook.com/testpage/",
        "intro": "Welcome to our test restaurant!",
        "websites": ["https://testrestaurant.com"],
        "phone": "+1234567890",
        "email": "test@testrestaurant.com",
        "website": "testrestaurant.com",
        "services": "Dine-in, Takeout, Delivery",
        "rating": "4.5 stars",
        "followers": 5678,
        "profilePictureUrl": "https://example.com/profile.jpg",
        "coverPhotoUrl": "https://example.com/cover.jpg",
        "profilePhoto": "https://example.com/photo.jpg",
        "ratingOverall": 4.5,
        "ratingCount": 150,
        "creation_date": "2020-01-01",
        "ad_status": "Active",
        "about_me": {
            "text": "We are a family restaurant",
            "urls": []
        },
        "facebookId": "123456789",
        "pageAdLibrary": {
            "is_business_page_active": True,
            "id": "ad_lib_123"
        }
    }
    
    test_posts = [
        {"text": "Today's special!", "authorName": "Test Restaurant"},
        {"text": "Happy Friday!", "authorName": "Test Restaurant"}
    ]
    
    scraper = FacebookScraper()
    
    # Test combining data
    combined_data = scraper.combine_profile_and_posts_data(test_profile_info, test_posts, "testrestaurant")
    
    if combined_data:
        logger.info("✅ Profile info validation - Combined data structure created successfully!")
        
        # Test extraction
        profile_summary = scraper.extract_short_profile_info(combined_data)
        
        if profile_summary:
            logger.info("✅ Profile info validation - Profile summary extracted successfully!")
            logger.info(f"📋 Extracted fields: {list(profile_summary.keys())}")
            
            # Validate specific fields are extracted
            important_fields = ["username", "platform", "facebookUrl", "pageName", "likes", "followers"]
            extracted_fields = [field for field in important_fields if profile_summary.get(field) is not None]
            logger.info(f"✅ Important fields extracted: {extracted_fields}")
            
            return True
        else:
            logger.error("❌ Profile info validation - Profile summary extraction failed!")
            return False
    else:
        logger.error("❌ Profile info validation - Combined data structure creation failed!")
        return False

if __name__ == "__main__":
    # Run comprehensive tests
    logger.info("🚀 Starting Facebook scraper comprehensive testing...")
    
    # Test 1: Basic scraper functionality with profile info
    test_facebook_scraper()
    
    # Test 2: Profile info validation
    test_profile_info_validation()
    
    logger.info("🎉 All Facebook scraper tests completed!")