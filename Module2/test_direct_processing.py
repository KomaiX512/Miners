import asyncio
import json
import time
from utils.r2_client import R2Client
from config import R2_CONFIG
from query_handler import QueryHandler
from utils.status_manager import StatusManager

async def create_test_query():
    """Create a test query file in the R2 bucket"""
    r2_client = R2Client(config=R2_CONFIG)
    
    # Test username
    username = "maccosmetics"
    
    # Create a sample query
    query_data = {
        "query": "Create three engaging posts featuring our bestselling lipstick shades perfect for summer events",
        "timestamp": int(time.time()),
        "status": "pending"  # Explicitly set status to pending
    }
    
    # Create the query file key
    query_number = int(time.time()) % 1000  # Use part of current timestamp to avoid conflicts
    query_key = f"queries/{username}/query_{query_number}.json"
    
    # Upload the query file
    success = await r2_client.write_json(query_key, query_data)
    
    if success:
        print(f"Successfully created test query: {query_key}")
        return query_key
    else:
        print("Failed to create test query")
        return None

async def process_query_directly(query_key):
    """Process the query directly without going through the API"""
    print(f"Processing query: {query_key}")
    handler = QueryHandler()
    await handler.process_query(query_key)
    return True

async def check_output(username):
    """Check for the output post in the next_posts directory"""
    r2_client = R2Client(config=R2_CONFIG)
    output_dir = f"next_posts/{username}/"
    
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
        
        print("No output posts found.")
        return False
    except Exception as e:
        print(f"Error checking for output: {e}")
        return False

async def main():
    """Run the direct processing test"""
    username = "maccosmetics"
    
    print("1. Creating test query...")
    query_key = await create_test_query()
    if not query_key:
        print("Failed to create test query. Exiting.")
        return
    
    print("\n2. Processing query directly...")
    success = await process_query_directly(query_key)
    if not success:
        print("Failed to process query. Exiting.")
        return
    
    print("\n3. Checking for output post...")
    success = await check_output(username)
    
    if success:
        print("\nDirect processing test completed successfully!")
    else:
        print("\nDirect processing test failed.")

if __name__ == "__main__":
    asyncio.run(main()) 