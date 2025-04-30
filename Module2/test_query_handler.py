import asyncio
import json
from query_handler import QueryHandler
import os

async def test_generate_post_content():
    """Test the post content generation functionality"""
    handler = QueryHandler()
    
    # Test query
    test_query = "Create a post about our new summer collection with bright colors and floral patterns"
    test_username = "maccosmetics"
    
    # Load documents
    docs_loaded = await handler.load_documents(test_username)
    print(f"Documents loaded: {docs_loaded}")
    
    # Generate post content
    post_content = await handler.generate_post_content(test_query, test_username)
    
    if post_content:
        print("\nGenerated post content:")
        print(json.dumps(post_content, indent=2))
        
        # Verify the required fields
        required_fields = ["caption", "hashtags", "call_to_action", "visual_prompt"]
        missing_fields = [field for field in required_fields if field not in post_content]
        
        if missing_fields:
            print(f"\nWARNING: Missing required fields: {', '.join(missing_fields)}")
        else:
            print("\nAll required fields are present.")
            
        # Verify hashtags format
        if "hashtags" in post_content and isinstance(post_content["hashtags"], list):
            for hashtag in post_content["hashtags"]:
                if not hashtag.startswith("#"):
                    print(f"WARNING: Hashtag '{hashtag}' does not start with #")
        
        return True
    else:
        print("Failed to generate post content")
        return False

async def test_save_post():
    """Test saving post to the R2 bucket"""
    handler = QueryHandler()
    
    # Create a test post content
    test_post = {
        "caption": "Test caption for our amazing new product! Check it out!",
        "hashtags": ["#test", "#beauty", "#makeup", "#new", "#amazing"],
        "call_to_action": "Shop now while supplies last!",
        "visual_prompt": "Close-up image of a makeup palette with vibrant colors in a studio setting with soft lighting",
        "status": "processed"
    }
    
    test_username = "maccosmetics"
    output_dir = f"{handler.output_prefix}{test_username}/"
    
    # Get sequential post number
    try:
        objects = await handler.r2_client.list_objects(output_dir)
        urgent_number = len([o for o in objects if "urgent_" in o["Key"]]) + 1
    except Exception as e:
        print(f"Error listing objects in {output_dir}, assuming first urgent post: {e}")
        urgent_number = 1
    
    output_key = f"{output_dir}urgent_{urgent_number}.json"
    
    # Save the post
    success = await handler.r2_client.write_json(output_key, test_post)
    
    if success:
        print(f"Successfully saved test post to {output_key}")
        return True
    else:
        print(f"Failed to save test post to {output_key}")
        return False

async def main():
    """Run all tests"""
    print("Testing post content generation...")
    generation_success = await test_generate_post_content()
    
    print("\nTesting post saving...")
    save_success = await test_save_post()
    
    if generation_success and save_success:
        print("\nAll tests passed successfully!")
    else:
        print("\nSome tests failed.")

if __name__ == "__main__":
    asyncio.run(main()) 