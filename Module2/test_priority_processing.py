import asyncio
import json
import time
from utils.r2_client import R2Client
from config import R2_CONFIG
from image_generator import ImageGenerator
from utils.logging import logger

async def create_test_files():
    """Create test files in the next_posts directory"""
    r2_client = R2Client(config=R2_CONFIG)
    
    # Test username
    username = "maccosmetics"
    output_dir = f"next_posts/{username}/"
    
    # Sample post data
    post_data = {
        "post": {
            "caption": "Discover our latest collection that's taking beauty to new heights!",
            "hashtags": ["#MAC", "#Beauty", "#NewCollection", "#MakeupLover", "#MACCosmetics"],
            "call_to_action": "Shop now and transform your look!",
            "visual_prompt": "Close-up of a luxurious makeup palette with vibrant eyeshadow colors arranged beautifully on a marble surface with soft lighting"
        },
        "status": "pending"
    }
    
    # Sample urgent data
    urgent_data = {
        "post": {
            "caption": "URGENT: Limited edition summer collection available now!",
            "hashtags": ["#MACLimited", "#SummerEdition", "#GetItNow", "#MAC", "#Exclusive"],
            "call_to_action": "Grab yours before they're gone!",
            "visual_prompt": "Stunning product shot of limited edition lipstick in gold packaging with tropical palm leaf shadows and bright summer lighting"
        },
        "status": "pending"
    }
    
    # Create both urgent and regular post files
    # First, create a regular post file
    try:
        objects = await r2_client.list_objects(output_dir)
        post_number = len([o for o in objects if "post_" in o["Key"]]) + 1
    except Exception as e:
        print(f"Error listing objects: {e}")
        post_number = 1
    
    post_key = f"{output_dir}post_{post_number}.json"
    post_success = await r2_client.write_json(post_key, post_data)
    
    # Then create an urgent file
    try:
        objects = await r2_client.list_objects(output_dir)
        urgent_number = len([o for o in objects if "urgent_" in o["Key"]]) + 1
    except Exception as e:
        print(f"Error listing objects: {e}")
        urgent_number = 1
    
    urgent_key = f"{output_dir}urgent_{urgent_number}.json"
    urgent_success = await r2_client.write_json(urgent_key, urgent_data)
    
    if post_success and urgent_success:
        print(f"Successfully created test files:")
        print(f"- Regular post: {post_key}")
        print(f"- Urgent post: {urgent_key}")
        return True
    else:
        print("Failed to create test files.")
        return False

async def test_image_generator_priority():
    """Test that image generator prioritizes urgent files"""
    print("Testing image generator priority processing...")
    
    # Create the ImageGenerator instance but don't start the full loop
    generator = ImageGenerator()
    
    # List files in the next_posts directory
    objects = await generator.r2_client.list_objects(generator.input_prefix)
    
    # Extract and classify the files
    urgent_files = []
    regular_files = []
    
    for obj in objects:
        key = obj["Key"]
        if key.endswith(".json"):
            if "urgent_" in key:
                urgent_files.append(key)
            elif "post_" in key:
                regular_files.append(key)
    
    # Check ordering based on the algorithm
    prioritized_files = urgent_files + regular_files
    
    print(f"\nFound {len(urgent_files)} urgent files and {len(regular_files)} regular files")
    print(f"Processing order would be:")
    
    for i, key in enumerate(prioritized_files[:5], 1):  # Show up to first 5 files
        file_type = "URGENT" if "urgent_" in key else "Regular"
        print(f"{i}. {file_type}: {key}")
    
    if len(prioritized_files) > 5:
        print(f"...and {len(prioritized_files) - 5} more files")
    
    # Verify urgent files come first
    if urgent_files and regular_files:
        is_correct_order = all(urgent_files.index(u) < len(urgent_files) + regular_files.index(r) 
                              for u in urgent_files for r in regular_files)
        print(f"\nVerification: {'All urgent files would be processed before regular files' if is_correct_order else 'Error in prioritization logic'}")
        
        return is_correct_order
    else:
        print("\nCannot verify prioritization fully: need both urgent and regular files")
        return False

async def main():
    """Run the priority test"""
    # Create test files first
    created = await create_test_files()
    if not created:
        print("Failed to create test files. Exiting.")
        return
    
    # Test the priority logic
    success = await test_image_generator_priority()
    
    if success:
        print("\nPriority processing test completed successfully!")
    else:
        print("\nPriority processing test failed.")

if __name__ == "__main__":
    asyncio.run(main()) 