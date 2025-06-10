import aiohttp
import asyncio
import re
import json
import base64
import io
from utils.r2_client import R2Client
from utils.status_manager import StatusManager
from utils.logging import logger
from utils.test_filter import TestFilter
from config import AI_HORDE_CONFIG, R2_CONFIG, STRUCTUREDB_R2_CONFIG
from tenacity import retry, stop_after_attempt, wait_exponential
from datetime import datetime
import os

class ImageGenerator:
    def __init__(self):
        # 🎯 CRITICAL FIX: Use correct buckets for input and output
        # Input: Read NextPost files from tasks bucket
        self.input_r2_client = R2Client(config={
            "endpoint_url": R2_CONFIG["endpoint_url"],
            "aws_access_key_id": R2_CONFIG["aws_access_key_id"],
            "aws_secret_access_key": R2_CONFIG["aws_secret_access_key"],
            "bucket_name": "tasks"  # NextPost files are in tasks bucket
        })
        
        # Output: Write ready posts to tasks bucket (not structuredb)
        self.output_r2_client = R2Client(config={
            "endpoint_url": R2_CONFIG["endpoint_url"],
            "aws_access_key_id": R2_CONFIG["aws_access_key_id"],
            "aws_secret_access_key": R2_CONFIG["aws_secret_access_key"],
            "bucket_name": "tasks"  # Ready posts should also go to tasks bucket
        })
        
        # Status manager uses tasks bucket to track processing status
        self.status_manager = StatusManager()
        self.status_manager.r2_client = self.input_r2_client  # Use tasks bucket for status
        
        self.input_prefix = "next_posts/"
        self.output_prefix = "ready_post/"
        self.platforms = ["instagram", "twitter", "facebook"]  # Support all three platforms

    def fix_post_data(self, data, key):
        """
        🔧 BULLETPROOF POST DATA NORMALIZER - Handles ALL NextPost formats intelligently.
        
        This method provides comprehensive format detection and normalization for:
        - Direct NextPost module outputs (next_post_prediction format)
        - Legacy post wrapper formats
        - Twitter format (tweet_text, hashtags, image_prompt)
        - Instagram format (caption, hashtags, image_prompt/visual_prompt)
        - Malformed or incomplete data structures
        
        Returns fixed data in the expected format or None if unfixable.
        """
        try:
            # 🛡️ DEFENSIVE: Handle completely invalid input
            if not data:
                logger.error(f"🚨 Data is None or empty in {key}")
                return None
                
            if not isinstance(data, dict):
                logger.error(f"🚨 Data is not a dictionary in {key}: {type(data)}")
                return None
            
            logger.info(f"🔧 INTELLIGENT FORMAT DETECTION: Processing {key}")
            logger.debug(f"📊 Input data keys: {list(data.keys())}")
            
            # 🎯 STRATEGY 1: Check if data already has the expected wrapper format
            if "post" in data and isinstance(data["post"], dict):
                post = data["post"]
                    
                # Verify essential fields
                if self._has_valid_image_prompt(post):
                    logger.info(f"✅ Data already in expected format with valid image prompt: {key}")
                    return self._ensure_status_field(data)
                else:
                    logger.warning(f"⚠️ Post wrapper exists but missing valid image prompt in {key}")
                    # Try to fix the image prompt
                    fixed_post = self._fix_missing_image_prompt(post, data, key)
                    if fixed_post:
                        data["post"] = fixed_post
                        return self._ensure_status_field(data)
            
            # 🎯 STRATEGY 2: Detect and convert NextPost module format (MOST COMMON CASE)
            if self._is_nextpost_format(data):
                logger.info(f"🎯 DETECTED: NextPost module format in {key}")
                return self._convert_nextpost_to_standard_format(data, key)
            
            # 🎯 STRATEGY 3: Detect and convert Twitter format
            if self._is_twitter_format(data):
                logger.info(f"🐦 DETECTED: Twitter format in {key}")
                return self._convert_twitter_to_standard_format(data, key)
            
            # 🎯 STRATEGY 4: Detect direct post fields (legacy or malformed wrapper)
            if self._has_direct_post_fields(data):
                logger.info(f"📦 DETECTED: Direct post fields format in {key}")
                return self._convert_direct_fields_to_standard_format(data, key)
            
            # 🎯 STRATEGY 5: Detect nested structures (complex formats)
            if self._has_nested_post_structure(data):
                logger.info(f"🔍 DETECTED: Nested post structure in {key}")
                return self._extract_from_nested_structure(data, key)
            
            # 🎯 STRATEGY 6: Last resort - attempt intelligent reconstruction
            logger.warning(f"🔄 ATTEMPTING: Intelligent reconstruction for unrecognized format in {key}")
            return self._intelligent_reconstruction(data, key)
            
        except Exception as e:
            logger.error(f"🚨 Critical error in fix_post_data for {key}: {e}")
            return None
            
    def _has_valid_image_prompt(self, post):
        """Check if post has a valid image prompt."""
        return (post.get("image_prompt") and len(str(post["image_prompt"]).strip()) > 10) or \
               (post.get("visual_prompt") and len(str(post["visual_prompt"]).strip()) > 10)

    def _ensure_status_field(self, data):
        """Ensure data has a status field."""
        if "status" not in data:
            data["status"] = "pending"
        return data

    def _is_nextpost_format(self, data):
        """Detect NextPost module format (next_post_prediction, post_data, etc.)."""
        nextpost_indicators = [
            "next_post_prediction",
            "post_data", 
            "module_type",
            "generated_at"
        ]
        
        # Check for NextPost module wrapper
        if "module_type" in data and data.get("module_type") == "next_post_prediction":
            return True
            
        # Check for direct next_post_prediction
        if "next_post_prediction" in data:
            return True
            
        # Check for post_data wrapper (NEW: main.py export format)
        if "post_data" in data and isinstance(data["post_data"], dict):
            return True
            
        return False

    def _convert_nextpost_to_standard_format(self, data, key):
        """Convert NextPost module format to standard format."""
        try:
            # Extract the actual post content
            post_content = None
            
            # Check for the exported structure where content is in data.data (nested)
            if "module_type" in data and data.get("module_type") == "next_post_prediction" and "data" in data:
                post_content = data["data"]
                logger.debug(f"📦 Using exported module format next_post_prediction.data from {key}")
            # Check for direct next_post_prediction field
            elif "next_post_prediction" in data:
                post_content = data["next_post_prediction"]
                logger.debug(f"📦 Using next_post_prediction content from {key}")
            # Check for post_data format
            elif "post_data" in data:
                post_content = data["post_data"]
                logger.debug(f"📦 Using post_data content from {key}")
            # Check for wrapped post_data format with module_type
            elif "module_type" in data and "post_data" in data:
                post_content = data["post_data"]
                logger.debug(f"📦 Using wrapped post_data content from {key}")
            
            if not post_content or not isinstance(post_content, dict):
                logger.error(f"🚨 Could not extract valid post content from NextPost format in {key}")
                return None
                
            # Create standardized format
            standardized = {
                "post": self._standardize_post_fields(post_content, key),
                "status": data.get("status", "pending"),  # Use existing status if available
                "platform": data.get("platform", post_content.get("platform", "instagram")),
                "username": data.get("primary_username", data.get("username", "unknown")),
                "original_format": "nextpost_module"
            }
            
            # Log the standardization result
            logger.info(f"✅ Successfully converted NextPost format to standard format: {key}")
            logger.debug(f"📊 Original data keys: {list(data.keys())}")
            logger.debug(f"📊 Standardized format: {standardized}")
            
            return standardized
            
        except Exception as e:
            logger.error(f"🚨 Error converting NextPost format in {key}: {e}")
            return None

    def _is_twitter_format(self, data):
        """Detect Twitter format (tweet_text, hashtags, image_prompt)."""
        twitter_indicators = ["tweet_text", "media_suggestion", "follow_up_tweets"]
        return any(indicator in data for indicator in twitter_indicators)

    def _convert_twitter_to_standard_format(self, data, key):
        """Convert Twitter format to standard format."""
        try:
            post_content = {
                "caption": data.get("tweet_text", ""),
                "hashtags": data.get("hashtags", []),
                "call_to_action": data.get("call_to_action", ""),
                "image_prompt": data.get("image_prompt", data.get("media_suggestion", ""))
            }
            
            standardized = {
                "post": self._standardize_post_fields(post_content, key),
                "status": "pending",
                "platform": "twitter",
                "username": data.get("username", "unknown"),
                "original_format": "twitter"
            }
            
            logger.info(f"✅ Successfully converted Twitter format to standard format: {key}")
            return standardized
            
        except Exception as e:
            logger.error(f"🚨 Error converting Twitter format in {key}: {e}")
            return None

    def _has_direct_post_fields(self, data):
        """Check if data has direct post fields."""
        post_field_indicators = ["caption", "hashtags", "call_to_action", "image_prompt", "visual_prompt"]
        return any(field in data for field in post_field_indicators)

    def _convert_direct_fields_to_standard_format(self, data, key):
        """Convert direct post fields to standard format."""
        try:
            standardized = {
                "post": self._standardize_post_fields(data, key),
                "status": data.get("status", "pending"),
                "platform": data.get("platform", "instagram"),
                "username": data.get("username", "unknown"),
                "original_format": "direct_fields"
            }
            
            logger.info(f"✅ Successfully converted direct fields to standard format: {key}")
            return standardized
            
        except Exception as e:
            logger.error(f"🚨 Error converting direct fields in {key}: {e}")
            return None

    def _has_nested_post_structure(self, data):
        """Detect nested post structures."""
        for key, value in data.items():
            if isinstance(value, dict) and any(field in value for field in ["caption", "hashtags", "image_prompt", "visual_prompt"]):
                return True
        return False

    def _extract_from_nested_structure(self, data, key):
        """Extract post content from nested structures."""
        try:
            # Look for nested post content
            for field_name, field_value in data.items():
                if isinstance(field_value, dict):
                    if any(post_field in field_value for post_field in ["caption", "hashtags", "image_prompt", "visual_prompt"]):
                        logger.info(f"📦 Found nested post content in field '{field_name}' for {key}")
                        
                        standardized = {
                            "post": self._standardize_post_fields(field_value, key),
                            "status": "pending",
                            "platform": data.get("platform", "instagram"),
                            "username": data.get("username", "unknown"),
                            "original_format": f"nested_{field_name}"
                        }
                        
                        logger.info(f"✅ Successfully extracted from nested structure: {key}")
                        return standardized
            
            logger.error(f"🚨 Could not extract post content from nested structure in {key}")
            return None
            
        except Exception as e:
            logger.error(f"🚨 Error extracting from nested structure in {key}: {e}")
            return None

    def _intelligent_reconstruction(self, data, key):
        """Last resort: intelligent reconstruction from any available data."""
        try:
            logger.warning(f"🔧 Attempting intelligent reconstruction for {key}")
            
            # Try to find any text content that could be a caption
            caption = ""
            hashtags = []
            call_to_action = ""
            image_prompt = ""
            
            # Look for any text content
            for field_name, field_value in data.items():
                if isinstance(field_value, str) and len(field_value) > 20:
                    if not caption and any(word in field_value.lower() for word in ["post", "content", "caption", "text"]):
                        caption = field_value[:500]  # Limit length
                        logger.debug(f"📝 Found potential caption in field '{field_name}': {caption[:50]}...")
                    elif not image_prompt and any(word in field_value.lower() for word in ["image", "visual", "photo", "picture"]):
                        image_prompt = field_value
                        logger.debug(f"🖼️ Found potential image prompt in field '{field_name}': {image_prompt[:50]}...")
                elif isinstance(field_value, list):
                    if not hashtags and all(isinstance(item, str) for item in field_value):
                        hashtags = field_value[:10]  # Limit hashtags
                        logger.debug(f"🏷️ Found potential hashtags in field '{field_name}': {hashtags}")
            
            # Set reasonable defaults if nothing found
            if not caption:
                username = data.get("username", "user")
                caption = f"Exciting updates from {username}! Stay tuned for more content."
                logger.debug(f"📝 Using default caption for {key}")
            
            if not hashtags:
                hashtags = ["#Content", "#Update", "#Engagement"]
                logger.debug(f"🏷️ Using default hashtags for {key}")
            
            if not call_to_action:
                call_to_action = "What do you think? Share your thoughts!"
                logger.debug(f"💬 Using default call_to_action for {key}")
            
            if not image_prompt:
                image_prompt = "High-quality, engaging visual content that represents the brand"
                logger.debug(f"🖼️ Using default image_prompt for {key}")
            
            standardized = {
                "post": {
                    "caption": caption,
                    "hashtags": hashtags,
                    "call_to_action": call_to_action,
                    "image_prompt": image_prompt
                },
                "status": "pending",
                "platform": data.get("platform", "instagram"),
                "username": data.get("username", "unknown"),
                "original_format": "intelligent_reconstruction"
            }
            
            logger.info(f"✅ Successfully reconstructed post data for {key}")
            return standardized
            
        except Exception as e:
            logger.error(f"🚨 Error in intelligent reconstruction for {key}: {e}")
            return None

    def _standardize_post_fields(self, post_content, key):
        """Standardize post fields while preserving original content exactly."""
        try:
            # Start with required fields
            standard_post = {}
            
            # CRITICAL: Preserve caption exactly as is
            caption_field = None
            if "caption" in post_content:
                caption_field = "caption"
            elif "tweet_text" in post_content:
                caption_field = "tweet_text"
                
            if caption_field:
                standard_post["caption"] = post_content[caption_field]
            else:
                logger.warning(f"⚠️ No caption/tweet_text found in {key}, using empty string")
                standard_post["caption"] = ""
            
            # CRITICAL: Preserve hashtags exactly as is
            if "hashtags" in post_content:
                standard_post["hashtags"] = post_content["hashtags"]
            else:
                logger.warning(f"⚠️ No hashtags found in {key}, using empty list")
                standard_post["hashtags"] = []
            
            # CRITICAL: Preserve call_to_action exactly as is
            if "call_to_action" in post_content:
                standard_post["call_to_action"] = post_content["call_to_action"]
            else:
                logger.warning(f"⚠️ No call_to_action found in {key}, using empty string")
                standard_post["call_to_action"] = ""
            
            # Handle image_prompt - try various field names but preserve content exactly
            image_prompt = None
            for field in ["image_prompt", "visual_prompt", "media_suggestion", "image_description"]:
                if field in post_content:
                    image_prompt = post_content[field]
                    standard_post[field] = image_prompt
                    break
                    
            if not image_prompt:
                logger.warning(f"⚠️ No image prompt found in {key}, field will need to be generated")
            
            # Copy any other fields as-is
            for key, value in post_content.items():
                if key not in standard_post:
                    standard_post[key] = value
            
            # Verify preservation of key fields
            logger.info(f"✓ Standardized post fields while preserving original content for {key}")
            return standard_post
            
        except Exception as e:
            logger.error(f"🚨 Error in _standardize_post_fields for {key}: {e}")
            # Return minimal structure
            return {
                "caption": post_content.get("caption", post_content.get("tweet_text", "")),
                "hashtags": post_content.get("hashtags", []),
                "call_to_action": post_content.get("call_to_action", ""),
                "image_prompt": post_content.get("image_prompt", post_content.get("visual_prompt", ""))
            }

    def _fix_missing_image_prompt(self, post, original_data, key):
        """Fix missing image prompt by looking in original data or creating default."""
        try:
            # Look for image prompt in original data
            for field_name, field_value in original_data.items():
                if isinstance(field_value, str) and "image" in field_name.lower():
                    post["image_prompt"] = field_value
                    logger.info(f"✅ Found image prompt in original data field '{field_name}' for {key}")
                    return post
                elif isinstance(field_value, dict):
                    if "image_prompt" in field_value or "visual_prompt" in field_value:
                        post["image_prompt"] = field_value.get("image_prompt") or field_value.get("visual_prompt")
                        logger.info(f"✅ Found image prompt in nested field '{field_name}' for {key}")
                        return post
            
            # Create intelligent default based on post content
            caption = post.get("caption", "")
            hashtags = post.get("hashtags", [])
            
            # Analyze content to create relevant image prompt
            if any(tag for tag in hashtags if "beauty" in tag.lower() or "makeup" in tag.lower()):
                post["image_prompt"] = "High-quality beauty shot with professional makeup and lighting"
            elif any(tag for tag in hashtags if "food" in tag.lower() or "recipe" in tag.lower()):
                post["image_prompt"] = "Appetizing food photography with beautiful presentation"
            elif any(tag for tag in hashtags if "fashion" in tag.lower() or "style" in tag.lower()):
                post["image_prompt"] = "Stylish fashion photography with modern aesthetic"
            elif any(tag for tag in hashtags if "tech" in tag.lower() or "ai" in tag.lower()):
                post["image_prompt"] = "Clean, modern technology-focused visual design"
            else:
                post["image_prompt"] = "High-quality, engaging visual content that matches the brand aesthetic"
            
            logger.info(f"✅ Created intelligent default image prompt for {key}: {post['image_prompt']}")
            return post
            
        except Exception as e:
            logger.error(f"🚨 Error fixing missing image prompt for {key}: {e}")
            post["image_prompt"] = "High-quality engaging visual content"
            return post

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
            logger.info("🎨 Submitting image generation request to AI Horde...")
            async with session.post(url, json=payload, headers=headers) as response:
                if response.status != 202:
                    logger.error(f"🚨 AI Horde API error: {response.status}")
                    return None
                data = await response.json()
                job_id = data.get("id")
                if not job_id:
                    logger.error("🚨 No job ID received from AI Horde")
                    return None

                logger.info(f"⏳ Image generation job started with ID: {job_id}")
                for attempt in range(60):
                    logger.debug(f"🔄 Checking job status (attempt {attempt + 1}/60)...")
                    async with session.get(f"{AI_HORDE_CONFIG['base_url']}/generate/check/{job_id}") as check:
                        status = await check.json()
                        if status.get("done"):
                            logger.info("✅ Image generation completed, retrieving result...")
                            async with session.get(f"{AI_HORDE_CONFIG['base_url']}/generate/status/{job_id}") as result:
                                result_data = await result.json()
                                images = result_data.get("generations", [])
                                if images:
                                    logger.info("🎉 Successfully generated image")
                                    return images[0].get("img")
                                else:
                                    logger.error("🚨 No images in generation result")
                                    return None
                        await asyncio.sleep(10)
                logger.error(f"⏰ Image generation timed out for job {job_id}")
                return None
        except Exception as e:
            logger.error(f"🚨 Failed to generate image: {e}")
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
        """Save image data to R2 storage with enhanced logging and validation."""
        try:
            logger.info(f"🔄 Starting image upload to R2: {key}")
            logger.debug(f"📊 Image data size: {len(image_data)} bytes")
            
            # Validate image data
            if not image_data or len(image_data) < 1000:  # Minimum reasonable image size
                logger.error(f"🚨 Invalid image data for {key}: size={len(image_data) if image_data else 0} bytes")
                return False
            
            # Validate R2 client
            if not self.output_r2_client:
                logger.error(f"🚨 R2 output client not initialized for {key}")
                return False
            
            # Attempt upload with detailed logging
            logger.info(f"📤 Uploading image to bucket: {self.output_r2_client.bucket_name}")
            result = await self.output_r2_client.write_binary(key, image_data)
            
            if result:
                logger.info(f"✅ Successfully uploaded image to R2: {key} ({len(image_data)} bytes)")
                
                # Verify upload by checking if object exists
                try:
                    # Check if the uploaded image exists by listing objects with the exact key
                    image_dir = os.path.dirname(key)
                    objects = await self.output_r2_client.list_objects(image_dir + "/" if image_dir else "")
                    
                    # Look for our specific key in the objects
                    found_object = any(obj["Key"] == key for obj in objects)
                    
                    if found_object:
                        logger.info(f"🔍 Verified: Image exists in R2 bucket at {key}")
                    else:
                        logger.warning(f"⚠️ Image upload reported success but object not found in bucket listing for {key}")
                        # Still return True as the upload call succeeded
                        
                except Exception as verify_error:
                    logger.warning(f"⚠️ Could not verify image upload for {key}: {verify_error}")
                    # Don't fail the upload if verification fails
                
                return True
            else:
                logger.error(f"❌ Failed to upload image to R2: {key}")
                return False
                
        except Exception as e:
            logger.error(f"🚨 Error saving image to R2 bucket '{self.output_r2_client.bucket_name if self.output_r2_client else 'unknown'}' with key '{key}': {e}")
            logger.debug(f"🔍 R2 client config: endpoint={getattr(self.output_r2_client, 'endpoint_url', 'unknown')}")
            return False

    async def process_post(self, key, session):
        """
        🎯 BULLETPROOF POST PROCESSOR - Handles all NextPost formats intelligently.
        
        This method processes posts from the NextPost module with enhanced format detection,
        intelligent image prompt extraction, and robust error handling.
        """
        if not await self.status_manager.is_pending(key):
            logger.debug(f"⏭️ Skipping {key} - not pending")
            return

        logger.info(f"🔧 Starting to process post: {key}")
        
        try:
            logger.info(f"📥 Reading post data from {key}")
            data = await self.input_r2_client.read_json(key)
        except Exception as e:
            logger.error(f"🚨 Failed to read JSON from {key}: {e}")
            return

        # 🛡️ BULLETPROOF: Handle invalid data format with intelligent recovery
        if not data or not isinstance(data, dict):
            logger.warning(f"⚠️ Invalid or empty JSON data in {key}, marking as error")
            try:
                error_data = {"status": "error", "status_message": "Invalid or empty JSON data"}
                await self.input_r2_client.write_json(key, error_data)
            except Exception as e:
                logger.error(f"🚨 Failed to mark error status for {key}: {e}")
            return

        original_data = data.copy()  # Keep original for debugging
        
        # 🎯 INTELLIGENT FORMAT DETECTION AND NORMALIZATION
        if "post" not in data or not isinstance(data["post"], dict):
            logger.info(f"🔧 Detecting and normalizing format for {key}")
            
            fixed_data = self.fix_post_data(data, key)
            
            if not fixed_data:
                logger.error(f"🚨 Could not fix invalid JSON format in {key}")
                try:
                    error_data = {"status": "error", "status_message": "Invalid JSON format - unable to normalize"}
                    await self.input_r2_client.write_json(key, error_data)
                except Exception as e:
                    logger.error(f"🚨 Failed to mark error status for {key}: {e}")
                return
            
            data = fixed_data
            logger.info(f"✅ Successfully normalized format for {key}")

        post = data["post"]
        
        # 🎯 ENHANCED IMAGE PROMPT EXTRACTION with comprehensive keyword search and error handling
        logger.info(f"🎨 Extracting image prompt for {key}")
        prompt = self._extract_image_prompt(post, original_data, key)
        
        if not prompt:
            logger.error(f"🚨 No valid image prompt found in {key} after all extraction attempts")
            data["status"] = "error"
            data["status_message"] = "Missing or invalid image prompt - unable to generate visual"
            await self.input_r2_client.write_json(key, data)
            return

        logger.info(f"🎨 Generating image with prompt: {prompt[:100]}...")
        
        # Generate image
        image_url = await self.generate_image(prompt, session)
        if not image_url:
            logger.error(f"🚨 AI Horde image generation failed for {key}")
            data["status"] = "error"
            data["status_message"] = "Image generation failed - AI Horde service error"
            await self.input_r2_client.write_json(key, data)
            return

        # Download the image from the temporary URL
        logger.info(f"📥 Downloading generated image for {key}")
        image_data = await self.download_image(image_url, session)
        if not image_data:
            logger.error(f"🚨 Failed to download generated image for {key}")
            data["status"] = "error"
            data["status_message"] = "Image download failed - network or service error"
            await self.input_r2_client.write_json(key, data)
            return

        # 🎯 SMART PATH EXTRACTION with validation
        try:
            key_parts = key.split("/")
            if len(key_parts) < 4:
                logger.error(f"🚨 Invalid key format for schema: {key} (expected: next_posts/platform/username/file.json)")
                return
                
            platform = key_parts[1]  # next_posts/platform/username/file.json
            username = key_parts[2]
            
            # Clean username (remove @ if present)
            if username.startswith('@'):
                username = username[1:]
            
            logger.info(f"📂 Extracted path components: platform={platform}, username={username}")
            
        except Exception as e:
            logger.error(f"🚨 Error extracting path components from {key}: {e}")
            return
        
        # Create platform-aware output directory path
        output_dir = f"{self.output_prefix}{platform}/{username}/"
        
        try:
            objects = await self.output_r2_client.list_objects(output_dir)
            
            # 🏷️ FIX 3: Enforce naming conventions based on input file type
            # Determine if this is a campaign post based on input filename
            is_campaign_post = (
                "campaign_next_post_" in key or 
                "campaign_post_" in key or 
                "compaign_next_post_" in key or  # Handle typo in spec
                "campaign" in key.lower()
            )
            
            if is_campaign_post:
                file_prefix = "campaign_ready_post_"
                existing_pattern = "campaign_ready_post_"
                logger.info(f"📋 Detected campaign post input: {key} → using campaign naming")
            else:
                file_prefix = "ready_post_"
                existing_pattern = "ready_post_"
                logger.info(f"📄 Detected regular post input: {key} → using regular naming")
                
            post_number = len([o for o in objects if existing_pattern in o["Key"]]) + 1
            logger.info(f"📊 Current {file_prefix}{post_number} for {username}")
        except Exception as e:
            logger.warning(f"⚠️ Could not list existing objects in {output_dir}, assuming post_number=1: {e}")
            post_number = 1
            # Use campaign detection for fallback naming too
            if "campaign" in key.lower() or "compaign" in key.lower():
                file_prefix = "campaign_ready_post_"
            else:
                file_prefix = "ready_post_"
        
        # Create file paths for both JSON and image
        json_key = f"{output_dir}{file_prefix}{post_number}.json"
        image_key = f"{output_dir}image_{post_number}.jpg"
        
        # Save the image file
        logger.info(f"💾 Saving image to {image_key}")
        if not await self.save_image(image_data, image_key):
            logger.error(f"🚨 Failed to save image to {image_key}")
            data["status"] = "error"
            data["status_message"] = "Failed to save image file to storage"
            await self.input_r2_client.write_json(key, data)
            return

        # 🎯 CREATE ENHANCED OUTPUT POST with robust field handling
        logger.info(f"📝 Creating output post structure for {username}")
        output_post = self._create_output_post(post, image_key, platform, username, original_data)

        # Save the JSON file
        logger.info(f"💾 Saving post JSON to {json_key}")
        if await self.output_r2_client.write_json(json_key, output_post):
            await self.status_manager.mark_processed(key)
            logger.info(f"✅ Successfully processed {key} → {json_key} with image at {image_key}")
        else:
            logger.error(f"🚨 Failed to write JSON to {json_key}")
            data["status"] = "error"
            data["status_message"] = "Failed to write output JSON to storage"
            await self.input_r2_client.write_json(key, data)

    def _extract_image_prompt(self, post, original_data, key):
        """
        🎯 ENHANCED IMAGE PROMPT EXTRACTION with comprehensive keyword search and error handling.
        Fix 2: Intelligent search for image_prompt, visual_prompt, prompt keywords.
        """
        try:
            # 🔍 STRATEGY 1: Direct extraction from post object using all known keywords
            prompt_keywords = ["image_prompt", "visual_prompt", "prompt"]
            
            for keyword in prompt_keywords:
                prompt = post.get(keyword)
                if prompt and self._is_valid_image_prompt(prompt):
                    logger.info(f"✅ Found direct image prompt using keyword '{keyword}' in post for {key}: {str(prompt)[:50]}...")
                    return str(prompt).strip()
            
            # 🔍 STRATEGY 2: Alternative field names
            alt_fields = ["media_suggestion", "visual_direction", "image_description", "visual_concept", "media_prompt", "image_desc"]
            for field in alt_fields:
                prompt = post.get(field)
                if prompt and self._is_valid_image_prompt(prompt):
                    logger.info(f"✅ Found image prompt in alternative field '{field}' for {key}")
                    return str(prompt).strip()
            
            # 🔍 STRATEGY 3: Deep search in original data structure (parent, child, nested)
            prompt = self._deep_search_for_image_prompt(original_data, key)
            if prompt:
                return prompt
            
            # 🔍 STRATEGY 4: Recursive search in nested structures
            prompt = self._recursive_prompt_search(original_data, key)
            if prompt:
                return prompt
            
            # ⚠️ STRATEGY 5: Skip file if no valid prompt found
            logger.warning(f"⚠️ No valid image prompt found in {key} after comprehensive search")
            logger.info(f"🚫 Skipping file {key} due to missing/invalid image prompt")
            return None  # This will cause the file to be skipped
            
        except Exception as e:
            logger.error(f"🚨 Error extracting image prompt from {key}: {e}")
            logger.info(f"🚫 Skipping file {key} due to extraction error")
            return None  # This will cause the file to be skipped

    def _is_valid_image_prompt(self, prompt):
        """Check if image prompt is valid (not empty, not malformed, sufficient length)"""
        if not prompt:
            return False
        
        prompt_str = str(prompt).strip()
        
        # Check minimum length (at least 15 characters for meaningful prompt)
        if len(prompt_str) < 15:
            return False
        
        # Check for malformed prompts (just numbers, single words, etc.)
        if prompt_str.isdigit():
            return False
            
        # Check for meaningful content (not just spaces or special characters)
        if not any(c.isalpha() for c in prompt_str):
            return False
            
        # Check for placeholder text that indicates invalid prompt
        invalid_indicators = [
            "null", "none", "undefined", "placeholder", "todo", "fix", "error",
            "missing", "empty", "n/a", "tbd", "coming soon"
        ]
        
        if any(indicator in prompt_str.lower() for indicator in invalid_indicators):
            return False
            
        return True

    def _deep_search_for_image_prompt(self, data, key):
        """Deep search for image prompt in original data structure"""
        prompt_keywords = ["image_prompt", "visual_prompt", "prompt"]
        
        try:
            # Search in all fields and values
            for field_name, field_value in data.items():
                # Check if field name contains prompt keywords
                if any(keyword in field_name.lower() for keyword in ["image", "visual", "media", "prompt"]):
                    if isinstance(field_value, str) and self._is_valid_image_prompt(field_value):
                        logger.info(f"✅ Found image prompt in original data field '{field_name}' for {key}")
                        return field_value.strip()
                
                # Check nested dictionaries
                elif isinstance(field_value, dict):
                    for nested_key, nested_value in field_value.items():
                        if any(keyword in nested_key.lower() for keyword in prompt_keywords):
                            if self._is_valid_image_prompt(nested_value):
                                logger.info(f"✅ Found image prompt in nested field '{field_name}.{nested_key}' for {key}")
                                return str(nested_value).strip()
                
                # Check lists for prompt objects
                elif isinstance(field_value, list):
                    for item in field_value:
                        if isinstance(item, dict):
                            for list_key, list_value in item.items():
                                if any(keyword in list_key.lower() for keyword in prompt_keywords):
                                    if self._is_valid_image_prompt(list_value):
                                        logger.info(f"✅ Found image prompt in list item '{field_name}[].{list_key}' for {key}")
                                        return str(list_value).strip()
            
            return None
            
        except Exception as e:
            logger.error(f"🚨 Error in deep search for image prompt in {key}: {e}")
            return None

    def _recursive_prompt_search(self, data, key, depth=0, max_depth=3):
        """Recursively search for image prompts in nested structures"""
        if depth > max_depth or not isinstance(data, dict):
            return None
        
        prompt_keywords = ["image_prompt", "visual_prompt", "prompt"]
        
        try:
            for field_name, field_value in data.items():
                # Direct prompt field check
                if any(keyword in field_name.lower() for keyword in prompt_keywords):
                    if self._is_valid_image_prompt(field_value):
                        logger.info(f"✅ Found image prompt via recursive search at depth {depth} in field '{field_name}' for {key}")
                        return str(field_value).strip()
                
                # Recursive search in nested dictionaries
                if isinstance(field_value, dict):
                    result = self._recursive_prompt_search(field_value, key, depth + 1, max_depth)
                    if result:
                        return result
                
                # Search in lists
                elif isinstance(field_value, list):
                    for item in field_value:
                        if isinstance(item, dict):
                            result = self._recursive_prompt_search(item, key, depth + 1, max_depth)
                            if result:
                                return result
            
            return None
            
        except Exception as e:
            logger.error(f"🚨 Error in recursive prompt search at depth {depth} for {key}: {e}")
            return None

    def _generate_intelligent_image_prompt(self, post, original_data, key):
        """Generate intelligent image prompt based on post content."""
        try:
            # Analyze post content
            caption = post.get("caption", post.get("tweet_text", ""))
            hashtags = post.get("hashtags", [])
            platform = original_data.get("platform", "instagram")
            username = original_data.get("username", "user")
            
            # Combine text for analysis
            content_text = f"{caption} {' '.join(hashtags) if isinstance(hashtags, list) else hashtags}"
            content_lower = content_text.lower()
            
            # Content-based prompt generation
            if any(word in content_lower for word in ["beauty", "makeup", "cosmetics", "skincare", "lipstick", "foundation"]):
                prompt = "Professional beauty photography with high-quality makeup, perfect lighting, and elegant composition showcasing cosmetic products"
            elif any(word in content_lower for word in ["food", "recipe", "cooking", "restaurant", "delicious", "meal"]):
                prompt = "Appetizing food photography with beautiful presentation, natural lighting, and mouth-watering appeal"
            elif any(word in content_lower for word in ["fashion", "style", "outfit", "clothing", "designer", "trendy"]):
                prompt = "Stylish fashion photography with modern aesthetic, professional styling, and contemporary design elements"
            elif any(word in content_lower for word in ["tech", "ai", "technology", "innovation", "digital", "software"]):
                prompt = "Clean, modern technology-focused visual design with sleek aesthetics and innovative presentation"
            elif any(word in content_lower for word in ["fitness", "workout", "health", "exercise", "gym", "training"]):
                prompt = "Dynamic fitness photography with energy, motivation, and athletic performance showcase"
            elif any(word in content_lower for word in ["travel", "vacation", "adventure", "explore", "journey", "destination"]):
                prompt = "Stunning travel photography with breathtaking scenery, wanderlust appeal, and destination highlights"
            elif any(word in content_lower for word in ["art", "creative", "design", "artistic", "culture", "gallery"]):
                prompt = "Artistic and creative visual composition with aesthetic appeal and cultural significance"
            else:
                # Platform and username-specific default
                if platform.lower() == "twitter":
                    prompt = f"High-quality engaging visual for Twitter that represents {username}'s brand identity and content style with professional presentation"
                else:
                    prompt = f"High-quality engaging visual for Instagram that represents {username}'s brand aesthetic with stunning photography and professional quality"
            
            logger.info(f"🎨 Generated intelligent image prompt for {key}: {prompt[:50]}...")
            return prompt
            
        except Exception as e:
            logger.error(f"🚨 Error generating intelligent image prompt for {key}: {e}")
            return "High-quality, engaging visual content with professional photography and aesthetic appeal"

    def _create_output_post(self, post, image_key, platform, username, original_data):
        """Create enhanced output post with robust field handling."""
        try:
            # Extract fields - CRITICAL: Preserve exact original values without modifications
            caption = post.get("caption", post.get("tweet_text", ""))
            hashtags = post.get("hashtags", [])
            call_to_action = post.get("call_to_action", "")
            
            # IMPORTANT: Don't modify the caption or other text content - preserve exactly as is
            output_post = {
                "post": {
                    "caption": caption,  # Keep original caption exactly as is
                    "hashtags": hashtags,  # Keep original hashtags exactly as is
                    "call_to_action": call_to_action,  # Keep original call_to_action exactly as is
                    "image_url": image_key,
                    "platform": platform,
                    "username": username
                },
                "status": "pending",  # Status should be pending for frontend to handle
                "processed_at": datetime.now().isoformat(),
                "image_generated": True,
                "original_format": original_data.get("original_format", "unknown")
            }
            
            # Add platform-specific fields - but keep content identical
            if platform.lower() == "twitter":
                output_post["post"]["tweet_text"] = caption  # Same as caption for Twitter
            
            # Verify content preservation
            logger.info(f"✅ Created output post preserving original content for {username}")
            logger.debug(f"Original caption: {caption[:30]}...")
            logger.debug(f"Original hashtags: {hashtags[:3]}...")
            
            return output_post
            
        except Exception as e:
            logger.error(f"🚨 Error creating output post: {e}")
            # Even in fallback, try to preserve original content
            fallback_caption = ""
            fallback_hashtags = []
            fallback_cta = ""
            
            try:
                fallback_caption = post.get("caption", post.get("tweet_text", ""))
                fallback_hashtags = post.get("hashtags", [])
                fallback_cta = post.get("call_to_action", "")
            except:
                pass
            
            return {
                "post": {
                    "caption": fallback_caption if fallback_caption else "Content processed successfully!",
                    "hashtags": fallback_hashtags if fallback_hashtags else ["#Processed", "#Content"],
                    "call_to_action": fallback_cta if fallback_cta else "Check it out!",
                    "image_url": image_key,
                    "platform": platform,
                    "username": username
                },
                "status": "pending", 
                "processed_at": datetime.now().isoformat(),
                "image_generated": True,
                "fallback_used": True
            }

    async def run(self):
        async with aiohttp.ClientSession() as session:
            while True:
                try:
                    logger.info("🔄 Checking for new campaign posts across all platforms...")
                    
                    # Collect objects from ALL platforms
                    all_objects = []
                    for platform in self.platforms:
                        platform_prefix = f"{self.input_prefix}{platform}/"
                        objects = await self.input_r2_client.list_objects(platform_prefix)
                        all_objects.extend(objects)
                        logger.debug(f"Found {len(objects)} objects in {platform_prefix}")
                    
                    # 🧹 COMPREHENSIVE TEST FILTERING - Filter out all test objects
                    production_objects = TestFilter.filter_test_objects(all_objects)
                    
                    # Log filtering statistics
                    if len(all_objects) != len(production_objects):
                        filtered_count = len(all_objects) - len(production_objects)
                        logger.info(f"🧹 Image Generator filtered out {filtered_count} test files")
                    
                    # Process production objects - specifically look for campaign posts
                    urgent_files = []
                    campaign_files = []
                    regular_files = []
                    
                    for obj in production_objects:
                        key = obj["Key"]
                        if key.endswith(".json"):
                            # Additional username-based filtering
                            parts = key.split('/')
                            if len(parts) >= 3:
                                platform = parts[1] if len(parts) > 1 else "unknown"
                                username = parts[2] if len(parts) > 2 else "unknown"
                                
                                # 🚫 PRODUCTION FILTER - Username check
                                if TestFilter.should_skip_processing(platform, username, key):
                                    logger.debug(f"🚫 Skipping test file: {key}")
                                    continue
                                
                                # 🎯 PRODUCTION FILE - Categorize for processing
                                if "urgent_campaign_post_" in key:
                                    urgent_files.append(key)
                                elif "campaign_post_" in key:
                                    campaign_files.append(key)
                                elif "urgent_" in key:
                                    urgent_files.append(key)
                                elif "post_" in key:
                                    regular_files.append(key)
                    
                    logger.info(f"📊 Found {len(urgent_files)} urgent, {len(campaign_files)} campaign, and {len(regular_files)} regular production posts")
                    
                    # Check which files actually need processing
                    prioritized_files = urgent_files + campaign_files + regular_files
                    pending_files = []
                    
                    for key in prioritized_files:
                        if await self.status_manager.is_pending(key):
                            pending_files.append(key)
                    
                    # Log processing status
                    if pending_files:
                        logger.info(f"🚀 Processing {len(pending_files)} production posts:")
                        for f in pending_files:
                            logger.info(f"  - {f}")
                        
                        # Process files one at a time
                        for key in pending_files:
                            await self.process_post(key, session)
                    else:
                        logger.info("✨ No pending production posts to process")
                    
                    logger.info("💤 Waiting 10 seconds before next check...")
                    await asyncio.sleep(10)
                except Exception as e:
                    logger.error(f"🚨 Error in image generator loop: {e}")
                    logger.info("💤 Waiting 10 seconds before retry...")
                    await asyncio.sleep(10)

if __name__ == "__main__":
    import asyncio
    generator = ImageGenerator()
    asyncio.run(generator.run())

