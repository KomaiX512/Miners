#!/usr/bin/env python3
import asyncio
import json
from utils.r2_client import R2Client
from utils.logging import logger
from image_generator import ImageGenerator

async def fix_all_post_files():
    """
    Scan all post files in the next_posts directory, 
    check for invalid formats, and attempt to fix them.
    """
    logger.info("==== POST FILE FIXER UTILITY ====")
    
    # Create instances
    r2_client = R2Client()
    image_gen = ImageGenerator()
    
    # List all objects in next_posts directory
    input_prefix = "next_posts/"
    logger.info(f"Scanning for posts in {input_prefix}...")
    
    all_objects = await r2_client.list_objects(input_prefix)
    post_files = [obj["Key"] for obj in all_objects if obj["Key"].endswith(".json") and "post_" in obj["Key"]]
    
    logger.info(f"Found {len(post_files)} post files")
    
    fixed_count = 0
    unfixable_count = 0
    already_valid_count = 0
    
    # Process each post file
    for file_path in post_files:
        logger.info(f"Checking post file: {file_path}")
        
        # Read the current file
        data = await r2_client.read_json(file_path)
        
        # Check if file is valid
        is_valid = data and isinstance(data, dict) and "post" in data
        
        if is_valid:
            # Check if post contains required fields
            post = data["post"]
            required_fields = ["caption", "hashtags", "call_to_action"]
            missing_fields = [field for field in required_fields if field not in post or not post[field]]
            
            if missing_fields:
                logger.warning(f"{file_path} is missing required fields: {missing_fields}")
                is_valid = False
            else:
                # Also check for image or visual prompt
                has_prompt = post.get("image_prompt") or post.get("visual_prompt")
                if not has_prompt:
                    logger.warning(f"{file_path} is missing both image_prompt and visual_prompt")
                    is_valid = False
        
        if is_valid:
            logger.info(f"{file_path} is already valid")
            already_valid_count += 1
            continue
        
        # Attempt to fix the file
        logger.warning(f"Attempting to fix {file_path}...")
        fixed_data = image_gen.fix_post_data(data, file_path)
        
        if fixed_data:
            # Verify the fix worked
            if "post" in fixed_data:
                post = fixed_data["post"]
                has_required = all(field in post and post[field] for field in ["caption", "hashtags", "call_to_action"])
                has_prompt = post.get("image_prompt") or post.get("visual_prompt")
                
                if has_required and has_prompt:
                    # Write the fixed data back
                    if await r2_client.write_json(file_path, fixed_data):
                        logger.info(f"Successfully fixed and saved {file_path}")
                        fixed_count += 1
                    else:
                        logger.error(f"Failed to save fixed data for {file_path}")
                        unfixable_count += 1
                else:
                    logger.error(f"Fix was incomplete for {file_path}")
                    unfixable_count += 1
            else:
                logger.error(f"Fix didn't add required 'post' field to {file_path}")
                unfixable_count += 1
        else:
            logger.error(f"Unable to fix {file_path}")
            unfixable_count += 1
            
            # Mark as error in the source file
            try:
                error_data = {"status": "error", "status_message": "Invalid JSON format, unfixable"}
                await r2_client.write_json(file_path, error_data)
                logger.info(f"Marked {file_path} as error")
            except Exception as e:
                logger.error(f"Failed to mark error status for {file_path}: {e}")
    
    # Summary
    logger.info("==== POST FILE FIXER SUMMARY ====")
    logger.info(f"Total post files: {len(post_files)}")
    logger.info(f"Already valid: {already_valid_count}")
    logger.info(f"Successfully fixed: {fixed_count}")
    logger.info(f"Unfixable: {unfixable_count}")
    logger.info("==============================")

if __name__ == "__main__":
    asyncio.run(fix_all_post_files()) 