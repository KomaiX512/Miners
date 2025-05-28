"""Module for scraping Twitter profiles and uploading to R2 storage."""
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

# Apify API token for Twitter scraper - UPDATED
APIFY_API_TOKEN = "apify_api_wFKozVJYcTV7EYXD89MfH7kr01hgA11DYk2I"
TWITTER_ACTOR_ID = "web.harvester/twitter-scraper"

class TwitterScraper:
    """Class for scraping Twitter profiles and uploading to R2 storage."""
    
    def __init__(self, api_token=APIFY_API_TOKEN, r2_config=R2_CONFIG, test_local=False):
        """Initialize with API token and R2 configuration."""
        self.api_token = api_token
        self.r2_config = r2_config
        self.test_local = test_local  # Flag for local testing without R2 operations
        
        if not test_local:
            self.s3 = boto3.client(
                's3',
                endpoint_url=self.r2_config['endpoint_url'],
                aws_access_key_id=self.r2_config['aws_access_key_id'],
                aws_secret_access_key=self.r2_config['aws_secret_access_key'],
                config=Config(signature_version='s3v4')
            )
        else:
            self.s3 = None
            logger.info("Running in test_local mode - R2 storage operations will be skipped")
            
        self.running = False
        self.last_check_time = None
    
    def scrape_profile(self, username, results_limit=10):
        """Scrape Twitter profile using the new Apify actor."""
        if not username or not isinstance(username, str):
            logger.error(f"Invalid username: {username}")
            return None
        
        logger.info(f"Scraping Twitter profile: {username}")
        
        client = ApifyClient(self.api_token)
        
        # Clean up username for the new actor format
        clean_username = username.strip()
        if clean_username.startswith('@'):
            clean_username = clean_username[1:]
        
        # Prepare input for the new web.harvester/twitter-scraper actor
        run_input = {
            "handles": [clean_username],
            "tweetsDesired": results_limit,
            "withReplies": True,
            "includeUserInfo": True
        }
        
        try:
            actor = client.actor(TWITTER_ACTOR_ID)
            run = actor.call(run_input=run_input)
            
            # Wait for the run to finish
            logger.info(f"Waiting for Twitter scraping to complete for {username}...")
            time.sleep(45)  # Give time for the actor to collect data
            
            dataset = client.dataset(run["defaultDatasetId"])
            items = dataset.list_items().items
            
            if not items:
                logger.warning(f"No items found for Twitter user {username} - account may be private or unavailable")
                return None
                
            logger.info(f"Successfully scraped {len(items)} items for Twitter user {username}")
            return items
        except Exception as e:
            logger.error(f"Error scraping Twitter user {username}: {str(e)}")
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
        if self.test_local:
            # Skip R2 check in test_local mode
            logger.info(f"[test_local] Skipping directory check for {parent_username} in {bucket_name}")
            return False

        try:
            response = self.s3.list_objects_v2(
                Bucket=bucket_name,
                Prefix=f"twitter/{parent_username}/"
            )
            return 'Contents' in response and len(response['Contents']) > 0
        except Exception as e:
            logger.error(f"Error checking if directory exists in {bucket_name}: {str(e)}")
            return False
    
    def delete_previous_profile_data(self, username, bucket_name):
        """Delete previous profile data for a username in the specified bucket."""
        if self.test_local:
            # Skip delete in test_local mode
            logger.info(f"[test_local] Skipping deletion of previous Twitter profile data for {username} in {bucket_name}")
            return True
            
        try:
            # List all objects with the username prefix
            prefix = f"twitter/{username}/"
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
                    logger.info(f"Deleted previous Twitter profile data for {username} in bucket {bucket_name}: {len(objects_to_delete)} objects")
                return True
            else:
                logger.info(f"No previous Twitter profile data found for {username} in bucket {bucket_name}")
                return False
        except Exception as e:
            # Handle NoSuchBucket errors gracefully
            if "NoSuchBucket" in str(e):
                logger.warning(f"Bucket {bucket_name} does not exist, skipping deletion for {username}")
                return True  # Return True so upload can continue
            else:
                logger.error(f"Error deleting previous Twitter profile data for {username} in bucket {bucket_name}: {str(e)}")
                return False
    
    def upload_directory_to_both_buckets(self, local_directory, r2_prefix):
        """Upload directory to main and personal buckets with conditions."""
        if not os.path.exists(local_directory):
            logger.error(f"Local directory does not exist: {local_directory}")
            return {"main_uploaded": False, "personal_uploaded": False, "success": False}
        
        if self.test_local:
            # In test_local mode, report success without actually uploading
            logger.info(f"[test_local] Simulating successful upload of {local_directory} to R2 buckets for prefix {r2_prefix}")
            return {"main_uploaded": True, "personal_uploaded": True, "success": True}
        
        main_bucket = self.r2_config['bucket_name']
        personal_bucket = self.r2_config['personal_bucket_name']
        
        # Delete previous profile data before uploading (handle bucket errors gracefully)
        self.delete_previous_profile_data(r2_prefix, main_bucket)
        self.delete_previous_profile_data(r2_prefix, personal_bucket)
        
        # Upload to main bucket
        main_uploaded = False
        try:
            self.s3.put_object(Bucket=main_bucket, Key=f"twitter/{r2_prefix}/")
            
            for filename in os.listdir(local_directory):
                local_file_path = os.path.join(local_directory, filename)
                if os.path.isdir(local_file_path):
                    continue
                object_key = f"twitter/{r2_prefix}/{filename}"
                self.s3.upload_file(
                    local_file_path,
                    main_bucket,
                    object_key,
                    ExtraArgs={'ContentType': 'application/json'}
                )
                logger.info(f"Uploaded Twitter file to main bucket: {object_key}")
            
            main_uploaded = True
            logger.info(f"Successfully uploaded Twitter directory to main bucket: twitter/{r2_prefix}/")
        except Exception as e:
            if "NoSuchBucket" in str(e):
                logger.warning(f"Main bucket {main_bucket} does not exist, skipping main bucket upload")
            else:
                logger.error(f"Failed to upload Twitter directory to main bucket: {str(e)}")
            main_uploaded = False
        
        # Upload to personal bucket
        personal_uploaded = False
        try:
            expiration_time = (datetime.now() + timedelta(days=1)).isoformat()
            self.s3.put_object(
                Bucket=personal_bucket,
                Key=f"twitter/{r2_prefix}/",
                Metadata={'expiration-time': expiration_time}
            )
            for filename in os.listdir(local_directory):
                local_file_path = os.path.join(local_directory, filename)
                if os.path.isdir(local_file_path):
                    continue
                object_key = f"twitter/{r2_prefix}/{filename}"
                self.s3.upload_file(
                    local_file_path,
                    personal_bucket,
                    object_key,
                    ExtraArgs={
                        'ContentType': 'application/json',
                        'Metadata': {'expiration-time': expiration_time}
                    }
                )
            logger.info(f"Successfully uploaded Twitter directory to personal bucket: twitter/{r2_prefix}/")
            personal_uploaded = True
        except Exception as e:
            if "NoSuchBucket" in str(e):
                logger.warning(f"Personal bucket {personal_bucket} does not exist, skipping personal bucket upload")
            else:
                logger.error(f"Failed to upload Twitter directory to personal bucket: {str(e)}")
            personal_uploaded = False
        
        # Return success if at least one bucket upload succeeded
        success = main_uploaded or personal_uploaded
        if success:
            logger.info(f"Twitter upload completed - Main: {main_uploaded}, Personal: {personal_uploaded}")
        else:
            logger.error(f"All Twitter bucket uploads failed for {r2_prefix}")
        
        return {
            "main_uploaded": main_uploaded,
            "personal_uploaded": personal_uploaded,
            "success": success
        }
    
    def extract_short_profile_info(self, profile_data):
        """Extract short profile information from scraped data."""
        try:
            if not profile_data or len(profile_data) == 0:
                logger.warning("No profile data provided for extraction")
                return None
            
            # With the new web.harvester/twitter-scraper actor, we need to find user info
            # The user info is included in each tweet
            user_data = None
            tweets = []
            
            for item in profile_data:
                if 'user' in item:
                    if user_data is None:
                        user_data = item['user']  # Get user info from first tweet
                    tweets.append(item)
            
            if not user_data:
                logger.warning("No user data found in Twitter profile data")
                return None
            
            # Extract metrics for analysis
            follower_count = user_data.get('totalFollowers', 0)
            following_count = user_data.get('totalFollowing', 0)
            tweet_count = user_data.get('totalTweets', 0)
            
            # Calculate engagement metrics from tweets
            total_likes = 0
            total_retweets = 0
            total_replies = 0
            total_quotes = 0
            
            for tweet in tweets:
                total_likes += tweet.get('likes', 0)
                total_retweets += tweet.get('retweets', 0)
                total_replies += tweet.get('replies', 0)
                total_quotes += tweet.get('quotes', 0)
            
            engagement_per_post = (total_likes + total_retweets + total_replies + total_quotes) / len(tweets) if tweets else 0
            
            # Get profile information
            screen_name = user_data.get('username', '')
            
            # Create short profile info
            profile_info = {
                'username': screen_name,
                'name': user_data.get('userFullName', ''),
                'bio': user_data.get('description', ''),
                'website': user_data.get('website', ''),
                'location': user_data.get('location', ''),
                'profile_image_url': user_data.get('avatar', ''),
                'follower_count': follower_count,
                'following_count': following_count,
                'tweet_count': tweet_count,
                'verified': user_data.get('verified', False),
                'created_at': user_data.get('joinDate', ''),
                'engagement_metrics': {
                    'total_likes': total_likes,
                    'total_retweets': total_retweets,
                    'total_replies': total_replies,
                    'total_quotes': total_quotes,
                    'engagement_per_post': engagement_per_post
                },
                'recent_posts': []
            }
            
            # Add recent posts (limit to 5 most recent)
            for i, tweet in enumerate(tweets):
                if i >= 5:  # Only include 5 most recent posts
                    break
                
                media_list = []
                # Handle media from the new format
                if 'media' in tweet and isinstance(tweet['media'], list):
                    media_list = [m.get('url', '') for m in tweet['media'] if isinstance(m, dict)]
                
                profile_info['recent_posts'].append({
                    'id': str(tweet.get('id', '')),
                    'text': tweet.get('text', ''),
                    'created_at': tweet.get('timestamp', ''),
                    'likes': tweet.get('likes', 0),
                    'retweets': tweet.get('retweets', 0),
                    'replies': tweet.get('replies', 0),
                    'quotes': tweet.get('quotes', 0),
                    'is_retweet': tweet.get('isRetweet', False),
                    'is_quote': tweet.get('isQuote', False),
                    'media': media_list
                })
            
            logger.info(f"Successfully extracted short profile info for Twitter user {screen_name}")
            return profile_info
        except Exception as e:
            logger.error(f"Error extracting short profile info: {str(e)}")
            return None
    
    def retrieve_and_process_twitter_usernames(self):
        """
        Retrieve and process ONE pending profileinfo.json from tasks/ProfileInfo/twitter/<username>/profileinfo.json.
        Returns the processed usernames or an empty list if none processed.
        """
        tasks_bucket = self.r2_config['bucket_name2']
        prefix = "ProfileInfo/twitter/"
        processed_users = []
        
        try:
            paginator = self.s3.get_paginator('list_objects_v2')
            page_iterator = paginator.paginate(Bucket=tasks_bucket, Prefix=prefix)
            
            info_files = []
            for page in page_iterator:
                if 'Contents' not in page:
                    logger.debug(f"No objects found for prefix {prefix} in page")
                    continue
                for obj in page['Contents']:
                    if obj['Key'].endswith('/profileinfo.json'):
                        info_files.append(obj)
            
            if not info_files:
                # Check alternative path format: ProfileInfo/twitter/<username>.json
                alt_prefix = "ProfileInfo/twitter/"
                alt_page_iterator = paginator.paginate(Bucket=tasks_bucket, Prefix=alt_prefix)
                
                for page in alt_page_iterator:
                    if 'Contents' not in page:
                        logger.debug(f"No objects found for prefix {alt_prefix} in page")
                        continue
                    for obj in page['Contents']:
                        if obj['Key'].endswith('.json') and not obj['Key'].endswith('/profileinfo.json'):
                            info_files.append(obj)
                
                if not info_files:
                    # Check AccountInfo/twitter/<username>/info.json as another alternative
                    alt_prefix = "AccountInfo/twitter/"
                    alt_page_iterator = paginator.paginate(Bucket=tasks_bucket, Prefix=alt_prefix)
                    
                    for page in alt_page_iterator:
                        if 'Contents' not in page:
                            logger.debug(f"No objects found for prefix {alt_prefix} in page")
                            continue
                        for obj in page['Contents']:
                            if obj['Key'].endswith('/info.json'):
                                info_files.append(obj)
                
                if not info_files:
                    logger.info(f"No profileinfo.json files found in {tasks_bucket} with any Twitter prefix")
                return processed_users
            
            info_files.sort(key=lambda x: x['LastModified'])
            logger.debug(f"Found {len(info_files)} Twitter profileinfo.json files: {[f['Key'] for f in info_files]}")
            
            for obj in info_files:
                info_key = obj['Key']
                logger.debug(f"Attempting to process Twitter {info_key}")
                
                try:
                    response = self.s3.get_object(Bucket=tasks_bucket, Key=info_key)
                    info_data = json.loads(response['Body'].read().decode('utf-8'))
                    logger.debug(f"Loaded Twitter profileinfo.json content: {json.dumps(info_data, indent=2)}")
                    
                    # Extract username based on key format
                    username = None
                    if '/profileinfo.json' in info_key:
                        # Format: ProfileInfo/twitter/<username>/profileinfo.json
                        parts = info_key.split('/')
                        if len(parts) >= 3:
                            username = parts[2]
                    elif info_key.startswith('ProfileInfo/twitter/') and info_key.endswith('.json'):
                        # Format: ProfileInfo/twitter/<username>.json
                        filename = info_key.split('/')[-1]
                        username = filename.replace('.json', '')
                    else:
                        # Format: AccountInfo/twitter/<username>/info.json or fallback to username in data
                        parts = info_key.split('/')
                        if len(parts) >= 3:
                            username = parts[2]
                    
                    # Fallback to username in data if path extraction fails
                    if not username:
                        username = info_data.get('username', '')
                        
                    account_type = info_data.get('accountType', '')
                    posting_style = info_data.get('postingStyle', '')
                    competitors = info_data.get('competitors', [])
                    timestamp = info_data.get('timestamp', '')
                    
                    if not username:
                        logger.error(f"Invalid Twitter profileinfo.json at {info_key}: missing username")
                        info_data['status'] = 'failed'
                        info_data['error'] = 'Missing username'
                        info_data['failed_at'] = datetime.now().isoformat()
                        self.s3.put_object(
                            Bucket=tasks_bucket,
                            Key=info_key,
                            Body=json.dumps(info_data, indent=4),
                            ContentType='application/json'
                        )
                        continue
                    
                    if info_data.get('status', 'pending') != 'pending':
                        logger.info(f"Skipping already processed Twitter profileinfo.json: {info_key} (status: {info_data.get('status')})")
                        continue
                    
                    logger.info(f"Processing Twitter profileinfo.json for username: {username}")
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
                    
                    logger.debug(f"Twitter competitor usernames: {competitor_usernames}")
                    
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
                    
                    info_data['status'] = 'processed' if result else 'failed'
                    info_data['processed_at'] = datetime.now().isoformat()
                    if not result:
                        info_data['error'] = f"Failed to process Twitter account batch for {username}"
                    
                    self.s3.put_object(
                        Bucket=tasks_bucket,
                        Key=info_key,
                        Body=json.dumps(info_data, indent=4),
                        ContentType='application/json'
                    )
                    
                    if result:
                        processed_users.append(username)
                        logger.info(f"Successfully processed Twitter user {username}")
                    else:
                        logger.error(f"Failed to process Twitter user {username}")
                    
                    logger.debug("Processed one Twitter profileinfo.json, exiting loop")
                    break
                
                except Exception as e:
                    logger.error(f"Error processing Twitter {info_key}: {str(e)}")
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
                        logger.error(f"Failed to update status for Twitter {info_key}: {update_e}")
                    continue
        
        except Exception as e:
            logger.error(f"Failed to list Twitter profileinfo.json files in {tasks_bucket} with prefix {prefix}: {str(e)}")
        
        return processed_users

    def continuous_processing_loop(self, sleep_interval=86400, check_interval=300):
        """
        Continuously process Twitter profileinfo.json files in an event-driven manner.
        
        Args:
            sleep_interval: Time to sleep after processing all files (in seconds, default 24 hours)
            check_interval: Time to wait between checks for new files during sleep (in seconds, default 5 minutes)
        """
        self.running = True
        logger.info(f"Starting Twitter continuous processing loop with sleep interval of {sleep_interval} seconds")
        
        try:
            while self.running:
                # Process all pending profileinfo.json files
                processed_count = 0
                while True:
                    processed = self.retrieve_and_process_twitter_usernames()
                    if not processed:
                        # No more pending files to process
                        break
                    processed_count += len(processed)
                    logger.info(f"Processed {len(processed)} Twitter accounts, total in this cycle: {processed_count}")
                
                logger.info(f"All pending Twitter files processed. Entering sleep mode for {sleep_interval} seconds")
                self.last_check_time = datetime.now()
                
                # Sleep with periodic checks for new files
                sleep_start_time = datetime.now()
                while (datetime.now() - sleep_start_time).total_seconds() < sleep_interval:
                    # Check if enough time has passed since the last check
                    if (datetime.now() - self.last_check_time).total_seconds() >= check_interval:
                        # Check for new pending files
                        logger.info("Checking for new Twitter files during sleep period")
                        new_files_exist = self._check_for_new_pending_twitter_files()
                        self.last_check_time = datetime.now()
                        
                        if new_files_exist:
                            logger.info("New pending Twitter files detected during sleep, processing now")
                            processed = self.retrieve_and_process_twitter_usernames()
                            if processed:
                                logger.info(f"Processed {len(processed)} new Twitter accounts during sleep period")
                    
                    # Sleep for a short time before checking again
                    time.sleep(10)  # Check every 10 seconds if we need to do the full check
                
                logger.info("Twitter sleep interval completed, restarting processing cycle")
                
        except KeyboardInterrupt:
            logger.info("Twitter processing loop interrupted by user")
            self.running = False
        except Exception as e:
            logger.error(f"Error in Twitter continuous processing loop: {str(e)}")
            self.running = False
            raise

    def _check_for_new_pending_twitter_files(self):
        """Check if there are any new pending Twitter profileinfo.json files."""
        tasks_bucket = self.r2_config['bucket_name2']
        prefix = "ProfileInfo/twitter/"
        
        try:
            response = self.s3.list_objects_v2(
                Bucket=tasks_bucket,
                Prefix=prefix,
                MaxKeys=10  # Just need to check if any exist, don't need all
            )
            
            if 'Contents' not in response:
                return False
                
            for obj in response['Contents']:
                if obj['Key'].endswith('/profileinfo.json'):
                    # Download the file to check its status
                    info_key = obj['Key']
                    file_response = self.s3.get_object(Bucket=tasks_bucket, Key=info_key)
                    info_data = json.loads(file_response['Body'].read().decode('utf-8'))
                    
                    # If status is pending, we have a new file to process
                    if info_data.get('status', 'pending') == 'pending':
                        return True
            
            return False
        except Exception as e:
            logger.error(f"Error checking for new pending Twitter files: {str(e)}")
            return False

    def stop_processing(self):
        """Stop the continuous processing loop safely."""
        logger.info("Stopping Twitter continuous processing loop")
        self.running = False
    
    def process_account_batch(self, parent_username, competitor_usernames, results_limit=10, info_metadata=None):
        """Process a batch of Twitter accounts and upload to R2 storage."""
        if not parent_username:
            logger.error("No parent username provided")
            return False
        
        logger.info(f"Processing Twitter account batch for {parent_username} with {len(competitor_usernames)} competitors")
        
        # Create local directory for storing files
        local_dir = self.create_local_directory(f"twitter_{parent_username}")
        if not local_dir:
            return False
        
        # Process parent account
        parent_data = self.scrape_profile(parent_username, results_limit)
        if parent_data:
            parent_file = self.save_to_local_file(parent_data, local_dir, f"{parent_username}.json")
            if not parent_file:
                logger.error(f"Failed to save Twitter parent data to local file for {parent_username}")
                return False
        else:
            logger.error(f"Failed to scrape Twitter parent account {parent_username}")
            return False
        
        # Process competitor accounts (limit to 5)
        processed_competitors = []
        for competitor in competitor_usernames[:5]:
            competitor_data = self.scrape_profile(competitor, results_limit)
            if competitor_data:
                competitor_file = self.save_to_local_file(competitor_data, local_dir, f"{competitor}.json")
                if not competitor_file:
                    logger.warning(f"Failed to save Twitter competitor data to local file for {competitor}")
                    continue
                processed_competitors.append(competitor)
                logger.info(f"Successfully processed Twitter competitor: {competitor}")
            else:
                logger.warning(f"Failed to scrape Twitter competitor account {competitor}")
        
        # Upload to R2
        upload_result = self.upload_directory_to_both_buckets(local_dir, parent_username)
        
        # Clean up local files
        try:
            shutil.rmtree(local_dir)
            logger.info(f"Cleaned up local Twitter directory: {local_dir}")
        except Exception as e:
            logger.warning(f"Failed to clean up local Twitter directory {local_dir}: {str(e)}")
        
        return upload_result.get('success', False)
    
    def scrape_and_upload(self, username, results_limit=10, info_metadata=None):
        """Scrape a single Twitter account and upload to R2 storage."""
        if not username:
            logger.error("No username provided")
            return None
        
        logger.info(f"Scraping and uploading Twitter account {username}")
        
        # Create local directory for storing files
        local_dir = self.create_local_directory(f"twitter_{username}")
        if not local_dir:
            return None
        
        # Scrape profile
        profile_data = self.scrape_profile(username, results_limit)
        if not profile_data:
            logger.error(f"Failed to scrape Twitter profile {username}")
            shutil.rmtree(local_dir)
            return None
        
        # Save to local file
        local_file = self.save_to_local_file(profile_data, local_dir, f"{username}.json")
        if not local_file:
            logger.error(f"Failed to save Twitter profile data to local file for {username}")
            shutil.rmtree(local_dir)
            return None
        
        # Extract short profile info
        profile_info = self.extract_short_profile_info(profile_data)
        
        # In test_local mode, skip the actual upload and return the profile info
        if self.test_local:
            logger.info(f"[test_local] Skipping R2 upload for {username}, returning profile info directly")
            try:
                shutil.rmtree(local_dir)
                logger.info(f"Cleaned up local Twitter directory: {local_dir}")
            except Exception as e:
                logger.warning(f"Failed to clean up local Twitter directory {local_dir}: {str(e)}")
            return profile_info
            
        # Try to upload to R2
        try:
            upload_result = self.upload_directory_to_both_buckets(local_dir, username)
            
            # If upload fails, still return profile_info with a warning
            if not upload_result.get('success', False):
                logger.warning(f"Failed to upload to R2, but returning profile data anyway for {username}")
                # Keep the local file for debugging
                logger.info(f"Local data saved at: {local_file}")
                return profile_info
                
        except Exception as e:
            logger.error(f"Error uploading to R2: {str(e)}")
            logger.warning(f"Continuing with local data for {username}")
            # Keep the local file for debugging
            logger.info(f"Local data saved at: {local_file}")
            return profile_info
        
        # Clean up local files if upload was successful
        try:
            shutil.rmtree(local_dir)
            logger.info(f"Cleaned up local Twitter directory: {local_dir}")
        except Exception as e:
            logger.warning(f"Failed to clean up local Twitter directory {local_dir}: {str(e)}")
        
        return profile_info

def test_twitter_scraper():
    """Test the Twitter scraper functionality."""
    scraper = TwitterScraper()
    
    # Test scraping a public profile
    test_username = "elonmusk"  # Elon Musk's Twitter account
    
    print(f"Testing Twitter scraper with {test_username}...")
    
    # Test scrape and upload
    profile_info = scraper.scrape_and_upload(test_username, results_limit=5)
    
    if profile_info:
        print(f"Successfully scraped Twitter profile: {profile_info['username']}")
        print(f"Follower count: {profile_info['follower_count']}")
        print(f"Recent posts: {len(profile_info['recent_posts'])}")
        return True
    else:
        print("Failed to scrape Twitter profile")
        return False

if __name__ == "__main__":
    scraper = TwitterScraper()
    logger.info("Starting Twitter scraper continuous processing")
    
    try:
        # Start the continuous processing loop with configurable intervals
        # Default: 24 hours (86400 seconds) sleep between full cycles
        # Check for new files every 5 minutes (300 seconds) during sleep
        scraper.continuous_processing_loop(
            sleep_interval=86400,  # 24 hours
            check_interval=300     # 5 minutes
        )
    except KeyboardInterrupt:
        logger.info("Twitter scraper interrupted by user")
    except Exception as e:
        logger.error(f"Error in Twitter main process: {str(e)}")
    finally:
        logger.info("Twitter scraper process ended") 