#!/usr/bin/env python3
import asyncio
import json
from utils.r2_client import R2Client
from utils.logging import logger
from image_generator import ImageGenerator

async def create_default_humansofny_post(r2_client, post_path, post_number):
    """Create a valid default post file for humansofny"""
    
    default_post = {
        "post": {
            "caption": f"Humans of New York - Story #{post_number}",
            "hashtags": [
                "#HumansOfNewYork",
                "#HONY",
                "#StoriesOfHumanity",
                "#HumanStories",
                "#StreetPhotography",
                "#NewYorkStories",
                "#RealLife",
                "#HumanConnection",
                "#CommunityStories",
                "#LifeStories"
            ],
            "call_to_action": "Follow Humans of New York for more stories of humanity.",
            "visual_prompt": "A tasteful street portrait photograph in the style of Humans of New York, featuring a diverse individual with an authentic expression against a New York City background. The image should have warm, natural lighting and a candid, documentary feel. The subject should appear engaged and real, like they're sharing their personal story.",
            "image_prompt": "A tasteful street portrait photograph in the style of Humans of New York, featuring a diverse individual with an authentic expression against a New York City background. The image should have warm, natural lighting and a candid, documentary feel. The subject should appear engaged and real, like they're sharing their personal story."
        },
        "status": "pending"
    }
    
    logger.info(f"Creating default humansofny post for {post_path}")
    result = await r2_client.write_json(post_path, default_post)
    
    if result:
        logger.info(f"Successfully created default post at {post_path}")
        return True
    else:
        logger.error(f"Failed to create default post at {post_path}")
        return False

async def fix_humansofny_posts():
    """Specifically fix the humansofny post files that are failing"""
    logger.info("==== HUMANSOFNY POST FIXER ====")
    
    # Create instances
    r2_client = R2Client()
    
    # Specific paths that need fixing
    problem_paths = [
        "next_posts/humansofny/post_1.json",
        "next_posts/humansofny/post_2.json",
        "next_posts/humansofny/post_3.json",
        "next_posts/humansofny/post_4.json"
    ]
    
    fixed_count = 0
    
    for i, path in enumerate(problem_paths):
        logger.info(f"Processing {path}...")
        
        # Read current file content
        data = await r2_client.read_json(path)
        
        # Check if file is valid
        if data and isinstance(data, dict) and "post" in data:
            post = data["post"]
            required_fields = ["caption", "hashtags", "call_to_action"]
            has_required = all(field in post and post[field] for field in required_fields)
            has_prompt = post.get("image_prompt") or post.get("visual_prompt")
            
            if has_required and has_prompt:
                logger.info(f"{path} is already valid")
                fixed_count += 1
                continue
        
        # Create a default post file since it's invalid or missing fields
        post_num = i + 1
        if await create_default_humansofny_post(r2_client, path, post_num):
            fixed_count += 1
        
    # Summary
    logger.info("==== HUMANSOFNY POST FIXER SUMMARY ====")
    logger.info(f"Total posts attempted: {len(problem_paths)}")
    logger.info(f"Successfully fixed/created: {fixed_count}")
    logger.info("==============================")

if __name__ == "__main__":
    asyncio.run(fix_humansofny_posts()) 