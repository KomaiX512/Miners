from flask import Flask, request, jsonify
from flask_cors import CORS
from apify_client import ApifyClient
import time
import json
import os
import boto3
from botocore.client import Config
from datetime import datetime

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Configuration
APIFY_API_TOKEN = "apify_api_88I8mu5LcmIjJa1fVUI3S3BvKGvNr60wvFPa"

# R2 Credentials
R2_CREDENTIALS = {
    "access_key_id": "2093fa05ee0323bb39de512a19638e78",
    "secret_access_key": "e9e7173d1ee514b452b3a3eb7cef6fb57a248423114f1f949d71dabd34eee04f",
    "account_id": "51abf57b5c6f9b6cf2f91cc87e0b9ffe",
    "bucket_name": "structuredb"
}

def scrape_instagram_profile(username, api_token, results_limit=5):
    """
    Scrape Instagram profile using Apify
    
    Args:
        username (str): Instagram username to scrape
        api_token (str): Apify API token
        results_limit (int): Maximum number of results to fetch
    
    Returns:
        dict: Scraped data
    """
    client = ApifyClient(api_token)
    
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
        time.sleep(15)  # Increased wait time for more reliable results
        
        dataset = client.dataset(run["defaultDatasetId"])
        items = dataset.list_items().items
        
        if not items:
            print(f"No items found for {username} - account may be private or unavailable")
            return None
        else:
            print(f"Successfully scraped {len(items)} items for {username}")
            return items
            
    except Exception as e:
        print(f"Error occurred while scraping {username}: {str(e)}")
        return None

def save_to_local_file(data, username):
    """
    Save scraped data to a local file
    
    Args:
        data (dict): Scraped data
        username (str): Instagram username
    
    Returns:
        str: Path to the saved file
    """
    if not data:
        return None
    
    # Create timestamp for unique filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{username}_{timestamp}.json"
    
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        
        print(f"Data saved to local file: {filename}")
        return filename
    
    except Exception as e:
        print(f"Error saving data to local file: {str(e)}")
        return None

def upload_to_r2(local_file_path, username, r2_credentials):
    """
    Upload file to Cloudflare R2 storage
    
    Args:
        local_file_path (str): Path to local file
        username (str): Instagram username
        r2_credentials (dict): R2 credentials
    
    Returns:
        bool: True if upload successful, False otherwise
    """
    if not local_file_path:
        return False
    
    try:
        # Configure S3 client to use with R2
        s3 = boto3.client(
            's3',
            endpoint_url=f"https://{r2_credentials['account_id']}.r2.cloudflarestorage.com",
            aws_access_key_id=r2_credentials['access_key_id'],
            aws_secret_access_key=r2_credentials['secret_access_key'],
            config=Config(signature_version='s3v4')
        )
        
        # Create a unique object key for the file in R2
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        object_key = f"{username}/{username}_{timestamp}.json"
        
        # Upload file to R2
        s3.upload_file(
            local_file_path, 
            r2_credentials['bucket_name'],
            object_key
        )
        
        print(f"Successfully uploaded to R2 bucket {r2_credentials['bucket_name']} with key: {object_key}")
        return True
    
    except Exception as e:
        print(f"Error uploading to R2: {str(e)}")
        return False

def extract_profile_data(data):
    """
    Extract profile data from scraped items
    
    Args:
        data (list): List of scraped items
    
    Returns:
        dict: Extracted profile data
    """
    if not data or len(data) == 0:
        return None
    
    # Get profile info from the first item
    profile_item = data[0]
    
    profile = {
        "username": profile_item.get("username", ""),
        "full_name": profile_item.get("fullName", ""),
        "biography": profile_item.get("biography", ""),
        "profile_pic_url": profile_item.get("profilePicUrl", ""),
        "is_verified": profile_item.get("verified", False),
        "followers_count": profile_item.get("followersCount", 0),
        "follows_count": profile_item.get("followsCount", 0),
        "is_private": profile_item.get("private", False)
    }
    
    return profile

def extract_posts_data(data):
    """
    Extract posts data from scraped items
    
    Args:
        data (list): List of scraped items
    
    Returns:
        list: Extracted posts data
    """
    if not data or len(data) == 0:
        return []
    
    posts = []
    
    # Get the first item which contains the posts
    profile_item = data[0]
    
    if "latestPosts" in profile_item:
        for post in profile_item["latestPosts"]:
            post_data = {
                "id": post.get("id", ""),
                "shortcode": post.get("shortCode", ""),
                "url": f"https://www.instagram.com/p/{post.get('shortCode', '')}/",
                "image_url": post.get("displayUrl", ""),
                "caption": post.get("caption", ""),
                "likes": post.get("likesCount", 0),
                "comments": post.get("commentsCount", 0),
                "timestamp": post.get("timestamp", ""),
                "hashtags": ",".join(post.get("hashtags", []))
            }
            posts.append(post_data)
    
    return posts

@app.route('/scrape', methods=['POST'])
def scrape():
    data = request.json
    username = data.get('username', '')
    
    if not username:
        return jsonify({"success": False, "message": "Username is required"}), 400
    
    # Scrape Instagram profile
    results_limit = 10  # Number of posts to retrieve
    scraped_data = scrape_instagram_profile(username, APIFY_API_TOKEN, results_limit)
    
    if not scraped_data:
        return jsonify({"success": False, "message": "Failed to scrape profile or profile not found"}), 404
    
    # Save data to local file
    local_file_path = save_to_local_file(scraped_data, username)
    
    # Upload to R2 storage
    if local_file_path:
        upload_to_r2(local_file_path, username, R2_CREDENTIALS)
    
    # Extract profile data
    profile_data = extract_profile_data(scraped_data)
    
    if not profile_data:
        return jsonify({"success": False, "message": "Failed to extract profile data"}), 500
    
    return jsonify({"success": True, "data": profile_data})

@app.route('/posts/<username>', methods=['GET'])
def get_posts(username):
    if not username:
        return jsonify({"success": False, "message": "Username is required"}), 400
    
    # Scrape Instagram profile
    results_limit = 10  # Number of posts to retrieve
    scraped_data = scrape_instagram_profile(username, APIFY_API_TOKEN, results_limit)
    
    if not scraped_data:
        return jsonify({"success": False, "message": "Failed to scrape posts or profile not found"}), 404
    
    # Extract posts data
    posts_data = extract_posts_data(scraped_data)
    
    return jsonify({"success": True, "data": posts_data})

if __name__ == "__main__":
    app.run(debug=True, port=5000)
