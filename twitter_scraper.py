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

# Apify API token for Twitter scraper - UPDATED with fresh token
APIFY_API_TOKEN = "your_apify_token_here"
TWITTER_ACTOR_ID = "memo23/apify-twitter-profile-scraper"  # New reliable actor

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
                region_name='auto',  # Fixed: Use 'auto' for R2 storage
                config=Config(signature_version='s3v4')
            )
        else:
            self.s3 = None
            logger.info("Running in test_local mode - R2 storage operations will be skipped")
            
        self.running = False
        self.last_check_time = None
    
    def scrape_profile(self, username, results_limit=10):
        """Scrape Twitter profile using the memo23/apify-twitter-profile-scraper actor with bulletproof configuration."""
        if not username or not isinstance(username, str):
            logger.error(f"Invalid username: {username}")
            return None
        
        logger.info(f"Scraping Twitter profile: {username} with results_limit: {results_limit}")
        
        client = ApifyClient(self.api_token)
        
        # Clean up username for the actor format
        clean_username = username.strip()
        if clean_username.startswith('@'):
            clean_username = clean_username[1:]
        
        # BULLETPROOF CONFIGURATION - NEW ACTOR FORMAT
        run_input = {
            "proxy": {
                "useApifyProxy": True,
                "apifyProxyGroups": ["RESIDENTIAL"]
            },
            "startUrls": [clean_username],
            "maxConcurrency": 10,
            "minConcurrency": 1,
            "maxRequestRetries": 100
        }
        
        logger.info(f"SINGLE ATTEMPT Twitter scraping for {clean_username} with input: {run_input}")
        
        # SINGLE ATTEMPT - No retries, treat failures as private/new accounts
        try:
            logger.info(f"🚀 Starting Twitter scraping for {username}")
            
            actor = client.actor(TWITTER_ACTOR_ID)
            run = actor.call(run_input=run_input)
            
            if not run:
                logger.warning(f"❌ Actor run failed for {username} - treating as private/new account")
                return []
            
            run_id = run["id"]
            logger.info(f"✅ Twitter run started with ID: {run_id}")
            
            # WAIT TIME - Allow up to 10 minutes for completion
            logger.info(f"⏳ Waiting for Twitter scraping to complete for {username}...")
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
                    
                    logger.info(f"📊 Twitter status for {username}: {final_status} | Items: {items_count} | Waited: {i}s/{max_wait_time}s")
                    
                    if final_status in ["SUCCEEDED", "FAILED", "ABORTED", "TIMED-OUT"]:
                        run_completed = True
                        break
                    
                    time.sleep(check_interval)
                except Exception as e:
                    logger.warning(f"⚠️ Error checking run status: {str(e)}")
                    time.sleep(check_interval)
            
            # DATA RETRIEVAL
            try:
                dataset = client.dataset(run["defaultDatasetId"])
                items = dataset.list_items().items
                
                logger.info(f"📦 Retrieved {len(items) if items else 0} items for {username}")
                
                # SUCCESS CONDITIONS
                if items and len(items) > 0:
                    logger.info(f"🎉 SUCCESS: Found {len(items)} items for Twitter user {username}")
                    
                    # Validate the scraped data
                    first_item = items[0]
                    if isinstance(first_item, dict):
                        logger.info(f"✅ Data validation passed for {username}")
                        logger.debug(f"First item keys: {list(first_item.keys())}")
                        
                        # Check for user information in the new format
                        has_user_info = False
                        if 'author' in first_item and isinstance(first_item['author'], dict):
                            logger.info(f"✅ User info found in 'author' field for {username}")
                            has_user_info = True
                        elif any(field in first_item for field in ['userName', 'name', 'followers']):
                            logger.info(f"✅ User info found in item fields for {username}")
                            has_user_info = True
                        
                        if not has_user_info:
                            logger.warning(f"⚠️ No user info found for {username}, but continuing with tweets")
                    
                    return items
                
                # PARTIAL SUCCESS - Even if no items, check if run was successful
                elif final_status == "SUCCEEDED":
                    logger.warning(f"⚠️ Run succeeded but no items for {username} - treating as private/protected account")
                    return []
                
                # FAILED RUN
                else:
                    logger.warning(f"❌ Run status {final_status} with no items for {username} - treating as private/new account")
                    return []
            
            except Exception as dataset_error:
                logger.warning(f"❌ Error retrieving dataset for {username}: {str(dataset_error)} - treating as private/new account")
                return []
            
        except Exception as e:
            logger.warning(f"❌ Exception scraping Twitter user {username}: {str(e)} - treating as private/new account")
            return []
    
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
        """Extract short profile information from scraped data - BULLETPROOF with graceful degradation for NEW ACTOR FORMAT."""
        try:
            # BULLETPROOF HANDLING - Handle all edge cases
            if not profile_data:
                logger.warning("No profile data provided - creating default profile info")
                return self._create_default_profile_info("unknown_user")
            
            if not isinstance(profile_data, list):
                logger.warning("Profile data is not a list - converting to list")
                profile_data = [profile_data] if profile_data else []
            
            if len(profile_data) == 0:
                logger.warning("Empty profile data list - creating default profile info")
                return self._create_default_profile_info("unknown_user")
            
            logger.info(f"✅ Extracting profile info from {len(profile_data)} items")
            
            # NEW ACTOR FORMAT: Data structure is different
            # Each item is a tweet with author field containing user information
            user_data = None
            tweets = []
            
            # Find user info and collect tweets from the NEW actor format
            for item in profile_data:
                if isinstance(item, dict):
                    # NEW FORMAT: Check if this item has user information in 'author' field
                    if 'author' in item and isinstance(item['author'], dict):
                        if user_data is None:
                            user_data = item['author']
                            logger.info("✅ Found user profile data in 'author' field (NEW FORMAT)")
                    
                    # This is a tweet in the new format
                    if item.get('type') == 'tweet' or any(field in item for field in ['id', 'text', 'url', 'likeCount', 'retweetCount', 'createdAt']):
                        tweets.append(item)
                        
            # GRACEFUL FALLBACK - If no user data found, extract from first item
            if not user_data:
                logger.warning("⚠️ No user data found in expected format - trying fallback extraction")
                first_item = profile_data[0] if profile_data else None
                if first_item and isinstance(first_item, dict):
                    if 'author' in first_item and isinstance(first_item['author'], dict):
                        user_data = first_item['author']
                        logger.info("✅ Extracted user data from first item 'author' field")
                    elif any(field in first_item for field in ['userName', 'name', 'followers']):
                        user_data = first_item
                        logger.info("✅ Using first item as user data")
                    else:
                        # CREATE MINIMAL USER DATA from available fields
                        logger.warning("⚠️ Creating minimal user data from available fields")
                        user_data = self._extract_minimal_user_data(first_item)
                else:
                    logger.warning("🔒 Could not extract user data - creating default profile")
                    return self._create_default_profile_info("private_account")
            
            # BULLETPROOF FIELD EXTRACTION with NEW ACTOR field mappings
            logger.info(f"✅ Processing user data with fields: {list(user_data.keys())}")
            
            # Extract metrics using NEW ACTOR field names
            follower_count = self._safe_extract_count(user_data, [
                'followers', 'totalFollowers', 'followersCount', 'follower_count'
            ])
            
            following_count = self._safe_extract_count(user_data, [
                'following', 'totalFollowing', 'followingCount', 'follows_count'
            ])
            
            tweet_count = self._safe_extract_count(user_data, [
                'statusesCount', 'totalTweets', 'tweets', 'tweet_count', 'posts_count'
            ])
            
            # If no tweet count from user data, use actual tweets collected
            if tweet_count == 0 and tweets:
                tweet_count = len(tweets)
                logger.info(f"✅ Using actual tweets count: {tweet_count}")
            
            # BULLETPROOF ENGAGEMENT CALCULATION with NEW ACTOR field names
            total_likes = 0
            total_retweets = 0
            total_replies = 0
            total_quotes = 0
            
            for tweet in tweets:
                if isinstance(tweet, dict):
                    total_likes += self._safe_extract_count(tweet, ['likeCount', 'likes', 'like_count'])
                    total_retweets += self._safe_extract_count(tweet, ['retweetCount', 'retweets', 'retweet_count'])
                    total_replies += self._safe_extract_count(tweet, ['replyCount', 'replies', 'reply_count'])
                    total_quotes += self._safe_extract_count(tweet, ['quoteCount', 'quotes', 'quote_count'])
            
            engagement_per_post = (total_likes + total_retweets + total_replies + total_quotes) / len(tweets) if tweets else 0
            
            # BULLETPROOF STRING FIELD EXTRACTION with NEW ACTOR field names
            screen_name = self._safe_extract_string(user_data, [
                'userName', 'username', 'screen_name', 'screenName'
            ])
            
            full_name = self._safe_extract_string(user_data, [
                'name', 'userFullName', 'displayName', 'fullName'
            ])
            
            bio = self._safe_extract_string(user_data, [
                'description', 'bio', 'biography'
            ])
            
            profile_image = self._safe_extract_string(user_data, [
                'profilePicture', 'avatar', 'profileImageUrl', 'profile_image_url'
            ])
            
            # NEW ACTOR: Extract website from entities structure
            website = ""
            if 'entities' in user_data and isinstance(user_data['entities'], dict):
                if 'url' in user_data['entities'] and isinstance(user_data['entities']['url'], dict):
                    urls = user_data['entities']['url'].get('urls', [])
                    if urls and isinstance(urls, list) and len(urls) > 0:
                        website = urls[0].get('expanded_url', '') or urls[0].get('url', '')
            
            # Fallback to direct website field
            if not website:
                website = self._safe_extract_string(user_data, [
                    'website', 'url', 'externalUrl'
                ])
            
            location = self._safe_extract_string(user_data, [
                'location', 'geo_location'
            ])
            
            # BULLETPROOF BOOLEAN EXTRACTION with NEW ACTOR field names
            verified = (user_data.get('isVerified', False) or 
                       user_data.get('isBlueVerified', False) or 
                       user_data.get('verified', False))
            
            # BULLETPROOF DATE EXTRACTION with NEW ACTOR field names
            created_at = self._safe_extract_string(user_data, [
                'createdAt', 'joinDate', 'created_at'
            ])
            
            # Create bulletproof profile info
            profile_info = {
                'username': screen_name or 'unknown_user',
                'name': full_name or screen_name or 'Unknown User',
                'bio': bio or '',
                'website': website or '',
                'location': location or '',
                'profile_image_url': profile_image or '',
                'follower_count': follower_count,
                'following_count': following_count,
                'tweet_count': tweet_count,
                'verified': verified,
                'created_at': created_at or '',
                'engagement_metrics': {
                    'total_likes': total_likes,
                    'total_retweets': total_retweets,
                    'total_replies': total_replies,
                    'total_quotes': total_quotes,
                    'engagement_per_post': engagement_per_post
                },
                'recent_posts': [],
                'data_source': 'twitter_scraper_new_actor',
                'extraction_timestamp': datetime.now().isoformat()
            }
            
            # BULLETPROOF RECENT POSTS EXTRACTION (limit to 5) with NEW ACTOR format
            for i, tweet in enumerate(tweets[:5]):
                if isinstance(tweet, dict):
                    post_data = self._extract_tweet_data_new_format(tweet, i)
                    if post_data:
                        profile_info['recent_posts'].append(post_data)
            
            # VALIDATION AND LOGGING
            logger.info(f"🎉 Successfully extracted Twitter profile info for {screen_name}")
            logger.info(f"📊 Profile metrics - Followers: {follower_count}, Following: {following_count}, Tweets: {tweet_count}")
            logger.info(f"📝 Recent posts extracted: {len(profile_info['recent_posts'])}")
            
            return profile_info
            
        except Exception as e:
            logger.error(f"❌ Error extracting profile info: {str(e)}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            
            # ULTIMATE FALLBACK - Never return None
            logger.warning("🆘 Creating emergency fallback profile")
            return self._create_default_profile_info("error_user")

    def _safe_extract_count(self, data_dict, field_names):
        """Safely extract a numeric count from multiple possible field names."""
        for field in field_names:
            if field in data_dict:
                value = data_dict[field]
                if isinstance(value, (int, float)) and value >= 0:
                    return int(value)
                elif isinstance(value, str) and value.isdigit():
                    return int(value)
        return 0

    def _safe_extract_string(self, data_dict, field_names):
        """Safely extract a string from multiple possible field names."""
        for field in field_names:
            if field in data_dict:
                value = data_dict[field]
                if isinstance(value, str) and value.strip():
                    return value.strip()
                elif value is not None:
                    return str(value).strip()
        return ""

    def _extract_minimal_user_data(self, item):
        """Extract minimal user data from any available fields for NEW ACTOR FORMAT."""
        minimal_data = {}
        
        # Try to find any username-like field with NEW ACTOR field names
        for username_field in ['userName', 'username', 'screen_name', 'handle']:
            if username_field in item:
                minimal_data['userName'] = item[username_field]
                break
        
        # Try to find any count fields with NEW ACTOR field names
        for follower_field in ['followers', 'follower_count', 'totalFollowers']:
            if follower_field in item:
                minimal_data['followers'] = item[follower_field]
                break
                
        return minimal_data

    def _extract_tweet_data_new_format(self, tweet, index):
        """Extract tweet data safely for NEW ACTOR FORMAT."""
        try:
            tweet_text = self._safe_extract_string(tweet, ['text', 'content', 'tweet_text'])
            created_at = self._safe_extract_string(tweet, ['createdAt', 'timestamp', 'created_at'])
            
            # Extract media safely from NEW ACTOR format
            media_list = []
            if 'extendedEntities' in tweet and isinstance(tweet['extendedEntities'], dict):
                media = tweet['extendedEntities'].get('media', [])
                if isinstance(media, list):
                    for media_item in media:
                        if isinstance(media_item, dict):
                            media_url = media_item.get('media_url', '') or media_item.get('url', '')
                            if media_url:
                                media_list.append(media_url)
            
            # Fallback to direct media field
            if 'media' in tweet and isinstance(tweet['media'], list):
                for media in tweet['media']:
                    if isinstance(media, dict):
                        media_url = media.get('url', '') or media.get('src', '')
                        if media_url:
                            media_list.append(media_url)
                    elif isinstance(media, str):
                        media_list.append(media)
                    
            return {
                'id': str(tweet.get('id', f'tweet_{index}')),
                'text': tweet_text,
                'created_at': created_at,
                'likes': self._safe_extract_count(tweet, ['likeCount', 'likes', 'like_count']),
                'retweets': self._safe_extract_count(tweet, ['retweetCount', 'retweets', 'retweet_count']),
                'replies': self._safe_extract_count(tweet, ['replyCount', 'replies', 'reply_count']),
                'quotes': self._safe_extract_count(tweet, ['quoteCount', 'quotes', 'quote_count']),
                'is_retweet': tweet.get('isRetweet', False),
                'is_quote': tweet.get('isQuote', False),
                'is_reply': tweet.get('isReply', False),
                'media': media_list,
                'url': self._safe_extract_string(tweet, ['url', 'twitterUrl', 'tweet_url'])
            }
        except Exception as e:
            logger.warning(f"Error extracting tweet data: {str(e)}")
            return None

    def _create_default_profile_info(self, username_hint):
        """Create a default profile info structure for failed extractions."""
        return {
            'username': username_hint,
            'name': username_hint.replace('_', ' ').title(),
            'bio': '',
            'website': '',
            'location': '',
            'profile_image_url': '',
            'follower_count': 0,
            'following_count': 0,
            'tweet_count': 0,
            'verified': False,
            'created_at': '',
            'engagement_metrics': {
                'total_likes': 0,
                'total_retweets': 0,
                'total_replies': 0,
                'total_quotes': 0,
                'engagement_per_post': 0
            },
            'recent_posts': [],
            'data_source': 'twitter_scraper_fallback',
            'extraction_timestamp': datetime.now().isoformat(),
            'note': 'Default profile created due to data extraction issues'
        }

    def retrieve_and_process_twitter_usernames(self):
        """
        Retrieve and process ONE pending profileinfo.json from tasks/AccountInfo/twitter/<username>/info.json 
        or ProfileInfo/twitter/<username>/profileinfo.json (fallback for backward compatibility).
        Returns the processed usernames or an empty list if none processed.
        """
        tasks_bucket = self.r2_config['bucket_name2']
        processed_users = []
        
        try:
            paginator = self.s3.get_paginator('list_objects_v2')
            
            # PRIMARY: Check AccountInfo/twitter/ first (standard architecture)
            primary_prefix = "AccountInfo/twitter/"
            page_iterator = paginator.paginate(Bucket=tasks_bucket, Prefix=primary_prefix)
            
            info_files = []
            for page in page_iterator:
                if 'Contents' not in page:
                    logger.debug(f"No objects found for Twitter prefix {primary_prefix} in page")
                    continue
                for obj in page['Contents']:
                    if obj['Key'].endswith('/info.json'):
                        info_files.append(obj)
            
            # FALLBACK: Check ProfileInfo/twitter/ for backward compatibility
            if not info_files:
                fallback_prefix = "ProfileInfo/twitter/"
                logger.info(f"No Twitter accounts found in {primary_prefix}, checking fallback {fallback_prefix}")
                page_iterator = paginator.paginate(Bucket=tasks_bucket, Prefix=fallback_prefix)
                
                for page in page_iterator:
                    if 'Contents' not in page:
                        logger.debug(f"No objects found for Twitter fallback prefix {fallback_prefix} in page")
                        continue
                    for obj in page['Contents']:
                        if obj['Key'].endswith('/profileinfo.json'):
                            info_files.append(obj)
                
                # Also check alternative format: ProfileInfo/twitter/<username>.json
                if not info_files:
                    for page in page_iterator:
                        if 'Contents' not in page:
                            continue
                        for obj in page['Contents']:
                            if obj['Key'].endswith('.json') and not obj['Key'].endswith('/profileinfo.json'):
                                info_files.append(obj)
                
                if not info_files:
                    logger.info(f"No Twitter profileinfo.json files found in {tasks_bucket} with any Twitter prefix")
                    return processed_users
            
            info_files.sort(key=lambda x: x['LastModified'])
            logger.debug(f"Found {len(info_files)} Twitter account files: {[f['Key'] for f in info_files]}")
            
            for obj in info_files:
                info_key = obj['Key']
                logger.debug(f"Attempting to process Twitter {info_key}")
                
                try:
                    response = self.s3.get_object(Bucket=tasks_bucket, Key=info_key)
                    info_data = json.loads(response['Body'].read().decode('utf-8'))
                    logger.debug(f"Loaded Twitter account file content: {json.dumps(info_data, indent=2)}")
                    
                    # Extract username based on key format
                    username = None
                    if info_key.startswith('AccountInfo/twitter/'):
                        # Standard format: AccountInfo/twitter/<username>/info.json
                        parts = info_key.split('/')
                        if len(parts) >= 3:
                            username = parts[2]
                    elif '/profileinfo.json' in info_key:
                        # Legacy format: ProfileInfo/twitter/<username>/profileinfo.json
                        parts = info_key.split('/')
                        if len(parts) >= 3:
                            username = parts[2]
                    elif info_key.startswith('ProfileInfo/twitter/') and info_key.endswith('.json'):
                        # Legacy format: ProfileInfo/twitter/<username>.json
                        filename = info_key.split('/')[-1]
                        username = filename.replace('.json', '')
                    
                    # Fallback to username in data if path extraction fails
                    if not username:
                        username = info_data.get('username', '')
                        
                    account_type = info_data.get('accountType', '')
                    posting_style = info_data.get('postingStyle', '')
                    competitors = info_data.get('competitors', [])
                    timestamp = info_data.get('timestamp', '')
                    
                    if not username or not account_type:
                        logger.error(f"Invalid Twitter account file at {info_key}: missing username or accountType")
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
                        logger.info(f"Skipping already processed Twitter account file: {info_key} (status: {info_data.get('status')})")
                        continue
                    
                    logger.info(f"Processing Twitter account file for username: {username}")
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
                    
                    info_data['status'] = 'processed' if result.get('success', False) else 'failed'
                    info_data['processed_at'] = datetime.now().isoformat()
                    if not result.get('success', False):
                        info_data['error'] = result.get('message', f"Failed to process Twitter account batch for {username}")
                    
                    self.s3.put_object(
                        Bucket=tasks_bucket,
                        Key=info_key,
                        Body=json.dumps(info_data, indent=4),
                        ContentType='application/json'
                    )
                    
                    if result.get('success', False):
                        processed_users.append(username)
                        logger.info(f"Successfully processed Twitter user {username}")
                    else:
                        logger.error(f"Failed to process Twitter user {username}: {result.get('message', 'Unknown error')}")
                    
                    logger.debug("Processed one Twitter account file, exiting loop")
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
            logger.error(f"Failed to list Twitter account files in {tasks_bucket}: {str(e)}")
        
        return processed_users

    def continuous_processing_loop(self, sleep_interval=86400, check_interval=10):
        """
        Continuously process Twitter profileinfo.json files in an event-driven manner.
        
        Args:
            sleep_interval: Time to sleep after processing all files (in seconds, default 24 hours)
            check_interval: Time to wait between checks for new files during sleep (in seconds, default 10 seconds)
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
        """Check if there are any new pending Twitter account files."""
        tasks_bucket = self.r2_config['bucket_name2']
        
        try:
            # PRIMARY: Check AccountInfo/twitter/ first (standard architecture)
            primary_prefix = "AccountInfo/twitter/"
            response = self.s3.list_objects_v2(
                Bucket=tasks_bucket,
                Prefix=primary_prefix,
                MaxKeys=10  # Just need to check if any exist, don't need all
            )
            
            if 'Contents' in response:
                for obj in response['Contents']:
                    if obj['Key'].endswith('/info.json'):
                        # Download the file to check its status
                        info_key = obj['Key']
                        file_response = self.s3.get_object(Bucket=tasks_bucket, Key=info_key)
                        info_data = json.loads(file_response['Body'].read().decode('utf-8'))
                        
                        # If status is pending, we have a new file to process
                        if info_data.get('status', 'pending') == 'pending':
                            return True
            
            # FALLBACK: Check ProfileInfo/twitter/ for backward compatibility
            fallback_prefix = "ProfileInfo/twitter/"
            response = self.s3.list_objects_v2(
                Bucket=tasks_bucket,
                Prefix=fallback_prefix,
                MaxKeys=10
            )
            
            if 'Contents' in response:
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
        """Process a batch of Twitter accounts and upload to R2 storage - BULLETPROOF IMPLEMENTATION."""
        if not parent_username:
            logger.error("No parent username provided")
            return {"success": False, "message": "No parent username provided"}
        
        logger.info(f"🚀 Processing BULLETPROOF Twitter account batch for {parent_username} with {len(competitor_usernames)} competitors")
        
        # Create local directory for storing files
        local_dir = self.create_local_directory(f"twitter_{parent_username}")
        if not local_dir:
            return {"success": False, "message": f"Failed to create local directory for {parent_username}"}
        
        # BULLETPROOF PARENT ACCOUNT PROCESSING
        logger.info(f"📊 Starting bulletproof scraping for parent account: {parent_username}")
        parent_data = self.scrape_profile(parent_username, results_limit)
        
        # GRACEFUL HANDLING - Even if scraping returns empty list, continue processing
        if parent_data is None:
            logger.error(f"❌ FATAL: Parent account {parent_username} scraping returned None")
            try:
                shutil.rmtree(local_dir)
            except:
                pass
            return {"success": False, "message": f"Failed to scrape parent profile: {parent_username}"}
        
        # Handle empty list gracefully (private/protected accounts)
        if isinstance(parent_data, list) and len(parent_data) == 0:
            logger.warning(f"🔒 Parent account {parent_username} returned empty data - likely private/protected")
            # Continue processing with empty data - create minimal profile
        
        logger.info(f"✅ Parent data retrieved for {parent_username}: {len(parent_data) if parent_data else 0} items")
        
        # BULLETPROOF PROFILE INFO EXTRACTION - Always succeeds now
        logger.info(f"🔍 Extracting profile info for {parent_username}...")
        parent_short_info = self.extract_short_profile_info(parent_data)
        
        # This should never be None now, but double-check
        if not parent_short_info:
            logger.warning(f"⚠️ Profile extraction failed for {parent_username} - creating emergency profile")
            parent_short_info = self._create_default_profile_info(parent_username)
        
        # Add metadata from info_metadata if available
        if info_metadata:
            parent_short_info['account_type'] = info_metadata.get('accountType', '')
            parent_short_info['posting_style'] = info_metadata.get('postingStyle', '')
            
            logger.info(f"📝 Twitter Account type for {parent_username}: {parent_short_info['account_type']}")
            logger.info(f"📝 Twitter Posting style for {parent_username}: {parent_short_info['posting_style']}")
            
        # BULLETPROOF PROFILE UPLOAD - Always preserve profile data
        logger.info(f"💾 Preserving profile info for {parent_username}...")
        profile_upload_result = self.upload_short_profile_to_tasks(parent_short_info)
        if profile_upload_result:
            logger.info(f"✅ Successfully preserved Twitter profile info for {parent_username}")
        else:
            logger.warning(f"⚠️ Failed to preserve Twitter profile info for {parent_username} - continuing anyway")
        
        # BULLETPROOF LOCAL FILE SAVING
        logger.info(f"💾 Saving parent data to local file for {parent_username}...")
        parent_file = self.save_to_local_file(parent_data, local_dir, f"{parent_username}.json")
        if not parent_file:
            logger.warning(f"⚠️ Failed to save parent data locally for {parent_username} - creating placeholder")
            # Create a placeholder file with profile info
            placeholder_data = {"profile_info": parent_short_info, "note": "Placeholder due to save failure"}
            parent_file = self.save_to_local_file([placeholder_data], local_dir, f"{parent_username}.json")
            
            if not parent_file:
                logger.error(f"❌ FATAL: Cannot create any local file for {parent_username}")
                try:
                    shutil.rmtree(local_dir)
                except:
                    pass
                return {"success": False, "message": f"Failed to save parent data locally: {parent_username}"}
        
        # BULLETPROOF COMPETITOR PROCESSING - Never fail the whole batch for competitor issues
        processed_competitors = []
        logger.info(f"🏆 Processing {len(competitor_usernames)} competitors for {parent_username}...")
        
        for i, competitor in enumerate(competitor_usernames[:5]):  # Limit to 5 competitors
            logger.info(f"📊 Processing competitor {i+1}/5: {competitor}")
            
            try:
                # BULLETPROOF COMPETITOR SCRAPING
                competitor_data = self.scrape_profile(competitor, results_limit)
                
                # Handle all possible outcomes gracefully
                if competitor_data is None:
                    logger.warning(f"⚠️ Competitor {competitor} scraping returned None - creating minimal data")
                    competitor_data = []
                elif not isinstance(competitor_data, list):
                    logger.warning(f"⚠️ Competitor {competitor} data is not a list - converting")
                    competitor_data = [competitor_data] if competitor_data else []
                
                logger.info(f"✅ Competitor data for {competitor}: {len(competitor_data)} items")
                
                # BULLETPROOF COMPETITOR PROFILE EXTRACTION
                competitor_short_info = self.extract_short_profile_info(competitor_data)
                if not competitor_short_info:
                    logger.warning(f"⚠️ Creating default profile for competitor {competitor}")
                    competitor_short_info = self._create_default_profile_info(competitor)
                
                # BULLETPROOF COMPETITOR PROFILE UPLOAD
                comp_profile_result = self.upload_short_profile_to_tasks(competitor_short_info)
                if comp_profile_result:
                    logger.info(f"✅ Successfully preserved profile info for competitor: {competitor}")
                else:
                    logger.warning(f"⚠️ Failed to preserve profile info for competitor: {competitor}")
                
                # BULLETPROOF COMPETITOR FILE SAVING
                competitor_file = self.save_to_local_file(competitor_data, local_dir, f"{competitor}.json")
                if not competitor_file:
                    logger.warning(f"⚠️ Failed to save competitor data for {competitor} - creating placeholder")
                    placeholder_data = {"profile_info": competitor_short_info, "note": "Placeholder due to save failure"}
                    competitor_file = self.save_to_local_file([placeholder_data], local_dir, f"{competitor}.json")
                
                if competitor_file:
                    processed_competitors.append(competitor)
                    logger.info(f"✅ Successfully processed Twitter competitor: {competitor}")
                else:
                    logger.warning(f"⚠️ Could not save competitor {competitor} - skipping but continuing")
                
            except Exception as e:
                logger.warning(f"⚠️ Exception processing competitor {competitor}: {str(e)} - continuing with others")
                continue
        
        logger.info(f"🏆 Completed competitor processing: {len(processed_competitors)}/{len(competitor_usernames[:5])} successful")
        
        # BULLETPROOF DIRECTORY UPLOAD - The most critical part
        logger.info(f"☁️ Uploading directory to R2 storage for {parent_username}...")
        upload_result = self.upload_directory_to_both_buckets(local_dir, parent_username)
        
        # BULLETPROOF CLEANUP
        try:
            shutil.rmtree(local_dir)
            logger.info(f"🧹 Cleaned up local Twitter directory: {local_dir}")
        except Exception as e:
            logger.warning(f"⚠️ Failed to clean up local Twitter directory {local_dir}: {str(e)}")
        
        # BULLETPROOF METADATA STORAGE
        if upload_result.get('success', False) and info_metadata:
            try:
                metadata_result = self.store_info_metadata(info_metadata)
                if metadata_result:
                    logger.info(f"✅ Stored metadata for {parent_username}")
                else:
                    logger.warning(f"⚠️ Failed to store metadata for {parent_username}")
            except Exception as e:
                logger.warning(f"⚠️ Exception storing metadata for {parent_username}: {str(e)}")
        
        # BULLETPROOF SUCCESS DETERMINATION
        # Consider it successful if we preserved the profile info OR uploaded to at least one bucket
        bulletproof_success = (
            upload_result.get('success', False) or 
            profile_upload_result or 
            len(processed_competitors) > 0
        )
        
        success_message = f"Successfully processed Twitter account batch for: {parent_username}"
        if not upload_result.get('success', False):
            success_message += " (profile info preserved despite upload issues)"
        
        error_message = f"Partial failure for Twitter account batch: {parent_username}"
        if not bulletproof_success:
            error_message = f"Complete failure for Twitter account batch: {parent_username}"
        
        result = {
            "success": bulletproof_success,
            "message": success_message if bulletproof_success else error_message,
            "main_uploaded": upload_result.get('main_uploaded', False),
            "personal_uploaded": upload_result.get('personal_uploaded', False),
            "processed_competitors": processed_competitors,
            "profile_preserved": bool(profile_upload_result),
            "bulletproof_mode": True
        }
        
        logger.info(f"🎯 BULLETPROOF RESULT for {parent_username}: {result}")
        return result
    
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

    def upload_short_profile_to_tasks(self, profile_info):
        """Upload short profile info to tasks bucket - SAME AS INSTAGRAM."""
        if not profile_info or not isinstance(profile_info, dict):
            logger.warning("Invalid profile info for upload")
            return False
        try:
            tasks_bucket = self.r2_config['bucket_name2']
            username = profile_info.get("username", "")
            if not username:
                logger.warning("Username missing in profile info")
                return False
                
            profile_key = f"ProfileInfo/twitter/{username}.json"
            
            # Check if the new profile info has complete data 
            has_complete_data = (
                (profile_info.get('follower_count', 0) > 0) and
                (profile_info.get('following_count', 0) > 0) and
                (profile_info.get('profile_image_url'))
            )
            
            # Check if file already exists
            existing_profile = None
            exists = self._check_object_exists(tasks_bucket, profile_key)
            if exists:
                logger.info(f"Profile info for {username} already exists at {profile_key}")
                try:
                    # Retrieve existing profile data to preserve important fields
                    response = self.s3.get_object(Bucket=tasks_bucket, Key=profile_key)
                    existing_profile = json.loads(response['Body'].read().decode('utf-8'))
                    logger.info(f"Successfully retrieved existing profile data for {username}")
                    
                    # If we have complete data, we'll completely replace the profile
                    # This ensures we don't keep bad data when we have good data
                    if has_complete_data:
                        logger.info(f"New profile data for {username} is complete, will completely replace existing data")
                        
                        # But always preserve account_type and posting_style if they exist in the old profile
                        # and not in the new profile
                        if existing_profile.get('account_type') and not profile_info.get('account_type'):
                            profile_info['account_type'] = existing_profile.get('account_type')
                            logger.info(f"Preserved account_type: {profile_info['account_type']}")
                            
                        if existing_profile.get('posting_style') and not profile_info.get('posting_style'):
                            profile_info['posting_style'] = existing_profile.get('posting_style')
                            logger.info(f"Preserved posting_style: {profile_info['posting_style']}")
                    else:
                        logger.info(f"New profile data for {username} is incomplete, will merge with existing data")
                        # In this case we'll do a selective merge
                except Exception as e:
                    logger.warning(f"Failed to retrieve existing profile for {username}: {str(e)}")
            
            # Add timestamp if not present
            if 'extractedAt' not in profile_info:
                profile_info['extractedAt'] = datetime.now().isoformat()
            
            # If we're not replacing completely, merge selectively with existing data
            if exists and existing_profile and not has_complete_data:
                # Check which profile has better data for each field
                # Only use existing field if new field is missing or has a "worse" value
                
                # For follower counts, use the higher value if new value is 0
                if profile_info.get('follower_count', 0) == 0 and existing_profile.get('follower_count', 0) > 0:
                    logger.info(f"Using existing follower count: {existing_profile['follower_count']}")
                    profile_info['follower_count'] = existing_profile.get('follower_count')
                
                # For following counts, use the higher value if new value is 0
                if profile_info.get('following_count', 0) == 0 and existing_profile.get('following_count', 0) > 0:
                    logger.info(f"Using existing following count: {existing_profile['following_count']}")
                    profile_info['following_count'] = existing_profile.get('following_count')
                
                # For tweet counts, use the higher value if new value is 0
                if profile_info.get('tweet_count', 0) == 0 and existing_profile.get('tweet_count', 0) > 0:
                    logger.info(f"Using existing tweet count: {existing_profile['tweet_count']}")
                    profile_info['tweet_count'] = existing_profile.get('tweet_count')
                
                # For profile URLs, use existing if new is missing
                if not profile_info.get('profile_image_url') and existing_profile.get('profile_image_url'):
                    logger.info(f"Using existing profile_image_url")
                    profile_info['profile_image_url'] = existing_profile.get('profile_image_url')
                
                # For other basic fields, use existing if new is missing
                for field in ['name', 'bio', 'website', 'location']:
                    if not profile_info.get(field) and existing_profile.get(field):
                        logger.info(f"Using existing {field}")
                        profile_info[field] = existing_profile.get(field)
                
                # Always preserve account_type and posting_style
                if existing_profile.get('account_type') and not profile_info.get('account_type'):
                    profile_info['account_type'] = existing_profile.get('account_type')
                    
                if existing_profile.get('posting_style') and not profile_info.get('posting_style'):
                    profile_info['posting_style'] = existing_profile.get('posting_style')
            
            # Ensure profile URLs exist (even if empty)
            if 'profile_image_url' not in profile_info:
                logger.warning(f"profile_image_url missing in profile info for {username}")
                profile_info['profile_image_url'] = ""
            
            # Log detailed info about what we're uploading
            logger.info(f"Uploading Twitter profile info for {username}:")
            logger.info(f"  Follower count: {profile_info.get('follower_count', 0)}")
            logger.info(f"  Following count: {profile_info.get('following_count', 0)}")
            logger.info(f"  Tweet count: {profile_info.get('tweet_count', 0)}")
            logger.info(f"  Profile URL exists: {bool(profile_info.get('profile_image_url'))}")
            logger.info(f"  Account type: {profile_info.get('account_type', 'Not specified')}")
            logger.info(f"  Posting style: {profile_info.get('posting_style', 'Not specified')}")
            
            # Upload to S3
            self.s3.put_object(
                Bucket=tasks_bucket,
                Key=profile_key,
                Body=json.dumps(profile_info, indent=2),
                ContentType='application/json'
            )
            
            action_word = "Updated" if exists else "Uploaded"
            logger.info(f"{action_word} short Twitter profile info to tasks bucket: {profile_key}")
            return True
        except Exception as e:
            logger.error(f"Error uploading Twitter profile info to tasks bucket: {str(e)}")
            return False

    def _check_object_exists(self, bucket, key):
        """Check if an object already exists in the bucket."""
        try:
            self.s3.head_object(Bucket=bucket, Key=key)
            return True
        except Exception:
            return False

    def store_info_metadata(self, info_data):
        """Store info.json metadata in tasks bucket for downstream use - SAME AS INSTAGRAM."""
        try:
            username = info_data.get("username", "")
            if not username:
                logger.error("Missing username in Twitter info.json")
                return False
            tasks_bucket = self.r2_config['bucket_name2']
            metadata_key = f"ProcessedInfo/{username}.json"
            self.s3.put_object(
                Bucket=tasks_bucket,
                Key=metadata_key,
                Body=json.dumps(info_data, indent=2),
                ContentType='application/json'
            )
            logger.info(f"Stored Twitter info.json metadata: {metadata_key}")
            return True
        except Exception as e:
            logger.error(f"Error storing Twitter info.json metadata: {str(e)}")
            return False

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
        # Check for new files every 10 seconds during sleep
        scraper.continuous_processing_loop(
            sleep_interval=86400,  # 24 hours
            check_interval=10      # 10 seconds
        )
    except KeyboardInterrupt:
        logger.info("Twitter scraper interrupted by user")
    except Exception as e:
        logger.error(f"Error in Twitter main process: {str(e)}")
    finally:
        logger.info("Twitter scraper process ended") 