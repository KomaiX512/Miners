#!/usr/bin/env python3
"""Utility to detect and recover missing profile URLs for all profiles in the system."""

import json
import logging
import boto3
import time
import os
import sys
from botocore.client import Config
from instagram_scraper import InstagramScraper
from config import R2_CONFIG
from main import ContentRecommendationSystem

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def find_profiles_with_missing_data():
    """Find all profiles with missing or potentially incorrect data in ProfileInfo directory."""
    try:
        s3 = boto3.client(
            's3',
            endpoint_url=R2_CONFIG['endpoint_url'],
            aws_access_key_id=R2_CONFIG['aws_access_key_id'],
            aws_secret_access_key=R2_CONFIG['aws_secret_access_key'],
            config=Config(signature_version='s3v4')
        )
        
        # List all objects in ProfileInfo directory
        response = s3.list_objects_v2(
            Bucket=R2_CONFIG['bucket_name2'],
            Prefix='ProfileInfo/'
        )
        
        all_profiles = []
        profiles_with_issues = []
        
        if 'Contents' in response:
            for obj in response['Contents']:
                if obj['Key'].endswith('.json'):
                    try:
                        response = s3.get_object(Bucket=R2_CONFIG['bucket_name2'], Key=obj['Key'])
                        profile_data = json.loads(response['Body'].read().decode('utf-8'))
                        
                        username = profile_data.get('username', '')
                        if not username:
                            username = obj['Key'].replace('ProfileInfo/', '').replace('.json', '')
                        
                        all_profiles.append(username)
                        
                        # Check for various issues
                        has_issues = False
                        issues = []
                        
                        # Check for missing profile URLs
                        if not profile_data.get("profilePicUrl") and not profile_data.get("profilePicUrlHD"):
                            has_issues = True
                            issues.append("missing profile URLs")
                        
                        # Check for missing follower/following counts
                        if profile_data.get("followersCount", 0) == 0:
                            has_issues = True
                            issues.append("zero follower count")
                            
                        if profile_data.get("followsCount", 0) == 0:
                            has_issues = True
                            issues.append("zero following count")
                            
                        if profile_data.get("postsCount", 0) == 0:
                            has_issues = True
                            issues.append("zero posts count")
                        
                        if has_issues:
                            profiles_with_issues.append({
                                "username": username,
                                "issues": issues
                            })
                            logger.info(f"Found profile with issues: {username} - {', '.join(issues)}")
                    except Exception as e:
                        logger.error(f"Error processing {obj['Key']}: {str(e)}")
        
        logger.info(f"Found {len(profiles_with_issues)} profiles with issues out of {len(all_profiles)} total profiles")
        return profiles_with_issues
    except Exception as e:
        logger.error(f"Error finding profiles with issues: {str(e)}")
        return []

def recover_profile_from_main_bucket(username):
    """Try to recover profile data from the main bucket data."""
    try:
        s3 = boto3.client(
            's3',
            endpoint_url=R2_CONFIG['endpoint_url'],
            aws_access_key_id=R2_CONFIG['aws_access_key_id'],
            aws_secret_access_key=R2_CONFIG['aws_secret_access_key'],
            config=Config(signature_version='s3v4')
        )
        
        # Look for the user's data file in the main bucket
        object_key = f"{username}/{username}.json"
        
        try:
            response = s3.get_object(Bucket=R2_CONFIG['bucket_name'], Key=object_key)
            raw_data = json.loads(response['Body'].read().decode('utf-8'))
            
            if isinstance(raw_data, list) and raw_data:
                logger.info(f"Found raw profile data for {username} in main bucket")
                profile_data = raw_data[0]
                
                # Enhanced extraction method to ensure all fields are captured
                follower_count = profile_data.get("followersCount", 0)
                follows_count = profile_data.get("followsCount", 0)
                posts_count = profile_data.get("postsCount", 0)
                
                # Check alternative field names if the standard names aren't populated
                if follower_count == 0 and "followers" in profile_data:
                    follower_count = profile_data.get("followers", 0)
                    logger.info(f"Using alternative field 'followers': {follower_count}")
                    
                if follows_count == 0 and "following" in profile_data:
                    follows_count = profile_data.get("following", 0)
                    logger.info(f"Using alternative field 'following': {follows_count}")
                    
                if posts_count == 0 and "mediaCount" in profile_data:
                    posts_count = profile_data.get("mediaCount", 0)
                    logger.info(f"Using alternative field 'mediaCount': {posts_count}")
                
                # Create a profile info object with all available fields
                profile_info = {
                    "username": username,
                    "fullName": profile_data.get("fullName", ""),
                    "biography": profile_data.get("biography", ""),
                    "followersCount": follower_count,
                    "followsCount": follows_count,
                    "postsCount": posts_count,
                    "externalUrl": profile_data.get("externalUrl", ""),
                    "profilePicUrl": profile_data.get("profilePicUrl", ""),
                    "profilePicUrlHD": profile_data.get("profilePicUrlHD", ""),
                    "private": profile_data.get("private", False),
                    "verified": profile_data.get("verified", False),
                    "extractedAt": profile_data.get("extractedAt", time.strftime("%Y-%m-%dT%H:%M:%S.000Z"))
                }
                
                # Add business fields if available
                if "businessCategoryName" in profile_data:
                    profile_info["businessCategoryName"] = profile_data.get("businessCategoryName", "")
                    
                if "isBusinessAccount" in profile_data:
                    profile_info["isBusinessAccount"] = profile_data.get("isBusinessAccount", False)
                
                # Add account type and posting style if available
                if "account_type" in profile_data:
                    profile_info["account_type"] = profile_data.get("account_type", "")
                
                if "posting_style" in profile_data:
                    profile_info["posting_style"] = profile_data.get("posting_style", "")
                
                # Check existing profile for account_type and posting_style
                try:
                    profile_key = f"ProfileInfo/{username}.json"
                    existing_response = s3.get_object(Bucket=R2_CONFIG['bucket_name2'], Key=profile_key)
                    existing_profile = json.loads(existing_response['Body'].read().decode('utf-8'))
                    
                    # Preserve account_type and posting_style if available in existing profile
                    if not profile_info.get("account_type") and existing_profile.get("account_type"):
                        profile_info["account_type"] = existing_profile.get("account_type")
                        
                    if not profile_info.get("posting_style") and existing_profile.get("posting_style"):
                        profile_info["posting_style"] = existing_profile.get("posting_style")
                except Exception:
                    logger.info(f"No existing profile found for {username}, creating new one")
                
                # Log detailed information about what we're recovering
                logger.info(f"Recovering profile for {username}:")
                logger.info(f"  Follower count: {profile_info['followersCount']}")
                logger.info(f"  Following count: {profile_info['followsCount']}")
                logger.info(f"  Posts count: {profile_info['postsCount']}")
                logger.info(f"  Profile URL: {'Present' if profile_info['profilePicUrl'] else 'Missing'}")
                logger.info(f"  Profile URL HD: {'Present' if profile_info['profilePicUrlHD'] else 'Missing'}")
                logger.info(f"  Account type: {profile_info.get('account_type', 'Not specified')}")
                logger.info(f"  Posting style: {profile_info.get('posting_style', 'Not specified')}")
                
                # Upload to ProfileInfo - completely replace the existing profile
                profile_key = f"ProfileInfo/{username}.json"
                s3.put_object(
                    Bucket=R2_CONFIG['bucket_name2'],
                    Key=profile_key,
                    Body=json.dumps(profile_info, indent=2),
                    ContentType='application/json'
                )
                
                logger.info(f"Recovered full profile data for {username} from main bucket")
                return True
        except Exception as e:
            logger.warning(f"Failed to retrieve {username} data from main bucket: {str(e)}")
        
        return False
    except Exception as e:
        logger.error(f"Error recovering profile from main bucket: {str(e)}")
        return False

def recover_profile_from_scraper(username):
    """Try to recover full profile by scraping fresh data."""
    try:
        scraper = InstagramScraper()
        
        logger.info(f"Attempting to scrape fresh data for {username}")
        profile_data = scraper.scrape_profile(username, 1)
        
        if profile_data:
            profile_info = scraper.extract_short_profile_info(profile_data)
            
            if profile_info:
                # Check if we got non-zero values for critical fields
                has_follower_count = profile_info.get('followersCount', 0) > 0
                has_follows_count = profile_info.get('followsCount', 0) > 0
                has_profile_urls = bool(profile_info.get('profilePicUrl') or profile_info.get('profilePicUrlHD'))
                
                if has_follower_count and has_follows_count and has_profile_urls:
                    logger.info(f"Successfully obtained complete profile data for {username}")
                else:
                    logger.warning(f"Profile data for {username} may be incomplete: followers={has_follower_count}, following={has_follows_count}, urls={has_profile_urls}")
                
                # Try to preserve account_type and posting_style from existing profile
                try:
                    s3 = boto3.client(
                        's3',
                        endpoint_url=R2_CONFIG['endpoint_url'],
                        aws_access_key_id=R2_CONFIG['aws_access_key_id'],
                        aws_secret_access_key=R2_CONFIG['aws_secret_access_key'],
                        config=Config(signature_version='s3v4')
                    )
                    
                    profile_key = f"ProfileInfo/{username}.json"
                    existing_response = s3.get_object(Bucket=R2_CONFIG['bucket_name2'], Key=profile_key)
                    existing_profile = json.loads(existing_response['Body'].read().decode('utf-8'))
                    
                    # Preserve important fields
                    if existing_profile.get("account_type"):
                        profile_info["account_type"] = existing_profile.get("account_type")
                        
                    if existing_profile.get("posting_style"):
                        profile_info["posting_style"] = existing_profile.get("posting_style")
                except Exception:
                    logger.info(f"No existing profile found for {username} to preserve account_type and posting_style")
                
                # Check for account type in ProcessedInfo
                try:
                    processed_info_key = f"ProcessedInfo/{username}.json"
                    processed_info_response = s3.get_object(Bucket=R2_CONFIG['bucket_name2'], Key=processed_info_key)
                    processed_info = json.loads(processed_info_response['Body'].read().decode('utf-8'))
                    
                    if processed_info.get("accountType") and not profile_info.get("account_type"):
                        profile_info["account_type"] = processed_info.get("accountType")
                        logger.info(f"Recovered account_type '{profile_info['account_type']}' from ProcessedInfo")
                        
                    if processed_info.get("postingStyle") and not profile_info.get("posting_style"):
                        profile_info["posting_style"] = processed_info.get("postingStyle")
                        logger.info(f"Recovered posting_style '{profile_info['posting_style']}' from ProcessedInfo")
                except Exception:
                    logger.info(f"No ProcessedInfo found for {username}")
                
                # Upload the profile info, replacing the existing one
                result = scraper.upload_short_profile_to_tasks(profile_info)
                
                if result:
                    logger.info(f"Successfully recovered profile for {username} using scraper")
                    return True
        
        logger.warning(f"Failed to recover profile for {username} using scraper")
        return False
    except Exception as e:
        logger.error(f"Error recovering profile using scraper: {str(e)}")
        return False

def recover_all_profiles_with_issues():
    """Find and recover all profiles with missing or incorrect data."""
    profiles_with_issues = find_profiles_with_missing_data()
    
    if not profiles_with_issues:
        logger.info("No profiles with issues found")
        return []
    
    usernames = [profile["username"] for profile in profiles_with_issues]
    
    logger.info(f"Attempting to recover {len(usernames)} profiles with issues")
    
    recovered = []
    failed = []
    
    for profile in profiles_with_issues:
        username = profile["username"]
        issues = profile["issues"]
        
        logger.info(f"Attempting to recover profile for {username} with issues: {', '.join(issues)}")
        
        # First try to recover from main bucket
        if recover_profile_from_main_bucket(username):
            recovered.append(username)
            continue
        
        # If that fails, try to recover using scraper
        if recover_profile_from_scraper(username):
            recovered.append(username)
            continue
        
        # If all recovery methods fail
        failed.append(username)
        logger.warning(f"All recovery methods failed for {username}")
    
    # Print summary
    logger.info(f"Recovery summary:")
    logger.info(f"Total profiles with issues: {len(usernames)}")
    logger.info(f"Successfully recovered: {len(recovered)}")
    logger.info(f"Failed to recover: {len(failed)}")
    
    if recovered:
        logger.info(f"Recovered profiles: {', '.join(recovered)}")
    
    if failed:
        logger.info(f"Failed profiles: {', '.join(failed)}")
    
    return recovered

# Main code section
if __name__ == "__main__":
    # Check command line arguments
    if len(sys.argv) > 1:
        # If username is provided, recover that specific profile
        username = sys.argv[1]
        logger.info(f"Attempting to recover profile for {username}")
        if recover_profile_from_main_bucket(username) or recover_profile_from_scraper(username):
            logger.info(f"Successfully recovered profile for {username}")
        else:
            logger.error(f"Failed to recover profile for {username}")
    else:
        # Otherwise, recover all profiles with issues
        logger.info("Searching for and recovering all profiles with issues")
        recover_all_profiles_with_issues() 