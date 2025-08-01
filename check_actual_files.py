import asyncio
import sys
sys.path.append('Module2')
from utils.r2_client import R2Client
from utils.logging import logger

async def check_actual_files():
    r2_client = R2Client()
    
    # Check what files actually exist in next_posts
    platforms = ["instagram", "twitter"]
    
    for platform in platforms:
        platform_prefix = f"next_posts/{platform}/"
        print(f"\n=== Checking {platform} files ===")
        
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
                    else:
                        print(f"    Could not read data")
                except Exception as e:
                    print(f"    Error reading: {e}")
                    
        except Exception as e:
            print(f"Error listing objects for {platform}: {e}")

if __name__ == "__main__":
    asyncio.run(check_actual_files()) 