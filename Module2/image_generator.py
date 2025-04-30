import aiohttp
import asyncio
import re
import json
import base64
import io
from utils.r2_client import R2Client
from utils.status_manager import StatusManager
from utils.logging import logger
from config import AI_HORDE_CONFIG
from tenacity import retry, stop_after_attempt, wait_exponential

class ImageGenerator:
    def __init__(self):
        self.r2_client = R2Client()
        self.status_manager = StatusManager()
        self.input_prefix = "next_posts/"
        self.output_prefix = "ready_post/"

    def fix_post_data(self, data, key):
        """
        Attempt to fix malformed post data by ensuring required fields exist.
        Returns fixed data or None if unfixable.
        """
        try:
            # If data is completely missing or not a dict, can't fix
            if not data or not isinstance(data, dict):
                logger.error(f"Unfixable data format in {key}: data is {type(data)}")
                return None
                
            # Check if post field exists
            if "post" not in data:
                # If there's direct fields that look like post content, wrap them in a post object
                post_fields = ["caption", "hashtags", "call_to_action", "visual_prompt", "image_prompt"]
                has_post_fields = any(field in data for field in post_fields)
                
                if has_post_fields:
                    logger.warning(f"Fixing missing 'post' wrapper in {key}")
                    fixed_data = {"post": {}}
                    
                    # Transfer relevant fields to post object
                    for field in post_fields:
                        if field in data:
                            fixed_data["post"][field] = data[field]
                    
                    # Preserve status field if it exists
                    if "status" in data:
                        fixed_data["status"] = data["status"]
                    else:
                        fixed_data["status"] = "pending"
                        
                    return fixed_data
                else:
                    logger.error(f"Cannot fix missing post data in {key}, no post fields found")
                    return None
            
            # Ensure post is a dictionary
            if not isinstance(data["post"], dict):
                logger.error(f"Unfixable post format in {key}: post is {type(data['post'])}")
                return None
                
            # Ensure required fields exist in post
            post = data["post"]
            required_fields = {
                "caption": "MAC Cosmetics - Beauty product showcase",
                "hashtags": ["#MAC", "#Beauty", "#Cosmetics"],
                "call_to_action": "Shop now at MAC Cosmetics!"
            }
            
            for field, default_value in required_fields.items():
                if field not in post or not post[field]:
                    logger.warning(f"Adding missing '{field}' in {key}")
                    post[field] = default_value
            
            # Ensure status exists
            if "status" not in data:
                data["status"] = "pending"
                
            return data
        except Exception as e:
            logger.error(f"Error while trying to fix post data in {key}: {e}")
            return None

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def generate_image(self, prompt, session):
        url = f"{AI_HORDE_CONFIG['base_url']}/generate/async"
        headers = {"apikey": AI_HORDE_CONFIG["api_key"]}
        payload = {
            "prompt": prompt,
            "params": {
                "width": 512,
                "height": 512,
                "steps": 50,
                "cfg_scale": 7.5
            }
        }
        try:
            async with session.post(url, json=payload, headers=headers) as response:
                if response.status != 202:
                    logger.error(f"AI Horde API error: {response.status}")
                    return None
                data = await response.json()
                job_id = data.get("id")
                if not job_id:
                    return None

                for _ in range(60):
                    async with session.get(f"{AI_HORDE_CONFIG['base_url']}/generate/check/{job_id}") as check:
                        status = await check.json()
                        if status.get("done"):
                            async with session.get(f"{AI_HORDE_CONFIG['base_url']}/generate/status/{job_id}") as result:
                                result_data = await result.json()
                                images = result_data.get("generations", [])
                                if images:
                                    return images[0].get("img")
                        await asyncio.sleep(10)
                logger.error(f"Image generation timed out for job {job_id}")
                return None
        except Exception as e:
            logger.error(f"Failed to generate image: {e}")
            return None

    async def download_image(self, image_url, session):
        """Download image from URL and return it as bytes."""
        try:
            async with session.get(image_url) as response:
                if response.status != 200:
                    logger.error(f"Failed to download image: {response.status}")
                    return None
                return await response.read()
        except Exception as e:
            logger.error(f"Error downloading image: {e}")
            return None

    async def save_image(self, image_data, key):
        """Save image data to R2 storage."""
        try:
            return await self.r2_client.write_binary(key, image_data)
        except Exception as e:
            logger.error(f"Error saving image to R2: {e}")
            return False

    async def process_post(self, key, session):
        if not await self.status_manager.is_pending(key):
            return

        data = await self.r2_client.read_json(key)
        
        # Handle invalid data format
        if not data or "post" not in data:
            logger.warning(f"Invalid JSON format in {key}, attempting to fix...")
            data = self.fix_post_data(data, key)
            
            if not data:
                logger.error(f"Could not fix invalid JSON format in {key}")
                # Mark as error in the source file if possible
                try:
                    error_data = {"status": "error", "status_message": "Invalid JSON format"}
                    await self.r2_client.write_json(key, error_data)
                except Exception as e:
                    logger.error(f"Failed to mark error status for {key}: {e}")
                return

        post = data["post"]
        
        # Check for either visual_prompt or image_prompt
        prompt = post.get("image_prompt") or post.get("visual_prompt")
        if not prompt:
            logger.error(f"No image prompt or visual prompt in {key}")
            data["status"] = "error"
            data["status_message"] = "Missing image or visual prompt"
            await self.r2_client.write_json(key, data)
            return

        logger.info(f"Generating image for {key}")
        image_url = await self.generate_image(prompt, session)
        if not image_url:
            logger.error(f"Failed to generate image for {key}")
            data["status"] = "error"
            data["status_message"] = "Image generation failed"
            await self.r2_client.write_json(key, data)
            return

        # Download the image from the temporary URL
        logger.info(f"Downloading image from URL for {key}")
        image_data = await self.download_image(image_url, session)
        if not image_data:
            logger.error(f"Failed to download image for {key}")
            data["status"] = "error"
            data["status_message"] = "Image download failed"
            await self.r2_client.write_json(key, data)
            return

        # Set up paths for storing files
        username = key.split("/")[1]
        output_dir = f"{self.output_prefix}{username}/"
        objects = await self.r2_client.list_objects(output_dir)
        post_number = len([o for o in objects if "ready_post_" in o["Key"]]) + 1
        
        # Create file paths for both JSON and image
        json_key = f"{output_dir}ready_post_{post_number}.json"
        image_key = f"{output_dir}image_{post_number}.jpg"
        
        # Save the image file
        logger.info(f"Saving image to {image_key}")
        if not await self.save_image(image_data, image_key):
            logger.error(f"Failed to save image to {image_key}")
            data["status"] = "error"
            data["status_message"] = "Failed to save image file"
            await self.r2_client.write_json(key, data)
            return

        # Create output post, handling potentially missing fields
        output_post = {
            "post": {
                "caption": post.get("caption", "MAC Cosmetics product"),
                "hashtags": post.get("hashtags", ["#MAC", "#Cosmetics"]),
                "call_to_action": post.get("call_to_action", "Shop now!"),
                "image_url": image_key  # Reference to our permanent image file
            },
            "status": "processed"
        }

        # Save the JSON file
        if await self.r2_client.write_json(json_key, output_post):
            await self.status_manager.mark_processed(key)
            logger.info(f"Successfully processed {key} to {json_key} with image at {image_key}")
        else:
            logger.error(f"Failed to write JSON to {json_key}")
            data["status"] = "error"
            data["status_message"] = "Failed to write output JSON"
            await self.r2_client.write_json(key, data)

    async def run(self):
        async with aiohttp.ClientSession() as session:
            while True:
                try:
                    logger.info("Checking for new posts...")
                    objects = await self.r2_client.list_objects(self.input_prefix)
                    logger.debug(f"Found {len(objects)} objects under {self.input_prefix}")
                    
                    # Separate files into urgent and regular posts
                    urgent_files = []
                    regular_files = []
                    
                    for obj in objects:
                        key = obj["Key"]
                        if key.endswith(".json"):
                            if "urgent_" in key:
                                urgent_files.append(key)
                            elif "post_" in key:
                                regular_files.append(key)
                    
                    # Process all files, with urgent files first
                    prioritized_files = urgent_files + regular_files
                    logger.debug(f"Processing order: {len(urgent_files)} urgent files, {len(regular_files)} regular files")
                    
                    tasks = []
                    for key in prioritized_files:
                        if await self.status_manager.is_pending(key):
                            if "urgent_" in key:
                                logger.info(f"Scheduling URGENT file for processing: {key}")
                            else:
                                logger.debug(f"Scheduling regular file for processing: {key}")
                            tasks.append(self.process_post(key, session))
                    
                    if tasks:
                        # Process one file at a time to maintain priority order
                        for task in tasks:
                            await task
                    else:
                        logger.debug("No processable posts found")
                    await asyncio.sleep(10)
                except Exception as e:
                    logger.error(f"Error in image generator loop: {e}")
                    await asyncio.sleep(10)
