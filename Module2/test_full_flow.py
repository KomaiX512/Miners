import asyncio
import json
import os
import time
from utils.r2_client import R2Client
from config import R2_CONFIG
from utils.logging import logger
import requests

async def create_test_query():
    """Create a test query file in the R2 bucket"""
    r2_client = R2Client(config=R2_CONFIG)
    
    # Test username
    username = "maccosmetics"
    
    # Create a sample query
    query_data = {
        "query": "Create three engaging posts featuring our bestselling lipstick shades perfect for summer events",
        "timestamp": int(time.time())
    }
    
    # Create the query file key
    query_number = 1  # Can be increased if needed
    query_key = f"queries/{username}/query_{query_number}.json"
    
    # Upload the query file
    success = await r2_client.write_json(query_key, query_data)
    
    if success:
        print(f"Successfully created test query: {query_key}")
        return query_key
    else:
        print("Failed to create test query")
        return None

async def trigger_query_processing(query_key):
    """Trigger the query processor to process the query"""
    query_processor_url = os.environ.get("QUERY_PROCESSOR_URL", "http://localhost:8000")
    
    try:
        response = requests.post(
            f"{query_processor_url}/process-query",
            json={"key": query_key},
            timeout=5
        )
        if response.status_code == 200:
            print(f"Successfully triggered processing for {query_key}")
            return True
        else:
            print(f"Failed to trigger processing for {query_key}: {response.text}")
            return False
    except Exception as e:
        print(f"Error triggering processing for {query_key}: {e}")
        return False

async def check_output(username, timeout=120):
    """Check for the output post in the next_posts directory"""
    r2_client = R2Client(config=R2_CONFIG)
    output_dir = f"next_posts/{username}/"
    
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            objects = await r2_client.list_objects(output_dir)
            urgent_files = [o for o in objects if "urgent_" in o["Key"]]
            
            if urgent_files:
                # Get the most recent post
                urgent_files.sort(key=lambda x: x["LastModified"], reverse=True)
                latest_post_key = urgent_files[0]["Key"]
                
                # Read the post content
                post_content = await r2_client.read_json(latest_post_key)
                if post_content:
                    print(f"\nFound output post at {latest_post_key}:")
                    print(json.dumps(post_content, indent=2))
                    
                    # Verify the required fields
                    required_fields = ["caption", "hashtags", "call_to_action", "visual_prompt", "status"]
                    missing_fields = [field for field in required_fields if field not in post_content]
                    
                    if missing_fields:
                        print(f"\nWARNING: Missing required fields: {', '.join(missing_fields)}")
                    else:
                        print("\nAll required fields are present.")
                        
                    return True
            
            print(f"Waiting for output post... ({int(time.time() - start_time)}s elapsed)")
            await asyncio.sleep(5)  # Wait 5 seconds before checking again
            
        except Exception as e:
            print(f"Error checking for output: {e}")
            await asyncio.sleep(5)
    
    print(f"Timeout ({timeout}s) reached waiting for output post")
    return False

async def main():
    """Run the full end-to-end test"""
    username = "maccosmetics"
    
    print("1. Creating test query...")
    query_key = await create_test_query()
    if not query_key:
        print("Failed to create test query. Exiting.")
        return
    
    print("\n2. Triggering query processing...")
    success = await trigger_query_processing(query_key)
    if not success:
        print("Failed to trigger query processing. Exiting.")
        return
    
    print("\n3. Checking for output post...")
    success = await check_output(username)
    
    if success:
        print("\nEnd-to-end test completed successfully!")
    else:
        print("\nEnd-to-end test failed.")

if __name__ == "__main__":
    asyncio.run(main()) 