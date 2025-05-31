import asyncio
import sys
sys.path.append('Module2')
from utils.r2_client import R2Client
from utils.logging import logger
from config import R2_CONFIG

async def check_tasks_bucket():
    # Use the tasks bucket configuration
    tasks_config = {
        "endpoint_url": R2_CONFIG["endpoint_url"],
        "aws_access_key_id": R2_CONFIG["aws_access_key_id"],
        "aws_secret_access_key": R2_CONFIG["aws_secret_access_key"],
        "bucket_name": "tasks"  # Explicitly use tasks bucket
    }
    
    r2_client = R2Client(config=tasks_config)
    
    # Check what files actually exist in next_posts in tasks bucket
    platforms = ["instagram", "twitter"]
    
    for platform in platforms:
        platform_prefix = f"next_posts/{platform}/"
        print(f"\n=== Checking {platform} files in TASKS bucket ===")
        
        try:
            objects = await r2_client.list_objects(platform_prefix)
            print(f"Found {len(objects)} objects under {platform_prefix}")
            
            for obj in objects:
                key = obj["Key"]
                print(f"  - {key}")
                
                # Try to read each file to see if it actually exists
                try:
                    data = await r2_client.read_json(key)
                    if data:
                        status = data.get('status', 'NO_STATUS_FIELD')
                        print(f"    Status: {status}")
                        if 'next_post_prediction' in data:
                            print(f"    Has next_post_prediction: YES")
                        if 'post' in data:
                            print(f"    Has post wrapper: YES")
                    else:
                        print(f"    Could not read data")
                except Exception as e:
                    print(f"    Error reading: {e}")
                    
        except Exception as e:
            print(f"Error listing objects for {platform}: {e}")

if __name__ == "__main__":
    asyncio.run(check_tasks_bucket()) 