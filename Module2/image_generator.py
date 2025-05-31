import aiohttp
import asyncio
import re
import json
import base64
import io
from utils.r2_client import R2Client
from utils.status_manager import StatusManager
from utils.logging import logger
from config import AI_HORDE_CONFIG, R2_CONFIG, STRUCTUREDB_R2_CONFIG
from tenacity import retry, stop_after_attempt, wait_exponential
from datetime import datetime

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
        
        # Output: Write ready posts to structuredb bucket
        self.output_r2_client = R2Client(config=STRUCTUREDB_R2_CONFIG)
        
        # Status manager uses tasks bucket to track processing status
        self.status_manager = StatusManager()
        self.status_manager.r2_client = self.input_r2_client  # Use tasks bucket for status
        
        self.input_prefix = "next_posts/"
        self.output_prefix = "ready_post/"
        self.platforms = ["instagram", "twitter"]  # Support both platforms

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
            
            if "next_post_prediction" in data:
                post_content = data["next_post_prediction"]
                logger.debug(f"📦 Using next_post_prediction content from {key}")
            elif "post_data" in data:
                post_content = data["post_data"]
                logger.debug(f"📦 Using post_data content from {key}")
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
                "platform": data.get("platform", "instagram"),
                "username": data.get("username", "unknown"),
                "original_format": "nextpost_module"
            }
            
            logger.info(f"✅ Successfully converted NextPost format to standard format: {key}")
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
        """Standardize post fields to expected format."""
        try:
            # Handle different caption field names
            caption = (post_content.get("caption") or 
                      post_content.get("tweet_text") or 
                      post_content.get("text") or 
                      post_content.get("content") or 
                      "Engaging content coming soon!")
            
            # Ensure caption is a string
            if not isinstance(caption, str):
                caption = str(caption)
            
            # Handle hashtags
            hashtags = post_content.get("hashtags", [])
            if not isinstance(hashtags, list):
                if isinstance(hashtags, str):
                    # Extract hashtags from string
                    hashtags = re.findall(r'#\w+', hashtags)
                else:
                    hashtags = ["#Content", "#Engagement"]
            
            # Ensure we have at least some hashtags
            if not hashtags:
                hashtags = ["#Content", "#Engagement"]
            
            # Handle call to action
            call_to_action = (post_content.get("call_to_action") or 
                             post_content.get("cta") or 
                             "Share your thoughts!")
            
            if not isinstance(call_to_action, str):
                call_to_action = str(call_to_action)
            
            # 🎯 CRITICAL: Handle image prompt with multiple fallbacks
            image_prompt = (post_content.get("image_prompt") or 
                           post_content.get("visual_prompt") or 
                           post_content.get("media_suggestion") or 
                           post_content.get("visual_direction") or
                           post_content.get("image_description"))
            
            # If no image prompt found, create a reasonable default
            if not image_prompt:
                platform = post_content.get("platform", "instagram")
                if platform == "twitter":
                    image_prompt = "High-quality engaging visual for Twitter post"
                else:
                    image_prompt = "High-quality engaging visual for Instagram post"
                logger.warning(f"⚠️ No image prompt found in {key}, using default: {image_prompt}")
            else:
                logger.info(f"✅ Found image prompt in {key}: {str(image_prompt)[:50]}...")
            
            # Ensure image prompt is a string
            if not isinstance(image_prompt, str):
                image_prompt = str(image_prompt)
            
            # Validate image prompt length
            if len(image_prompt.strip()) < 10:
                image_prompt = f"High-quality engaging visual content: {image_prompt}"
                logger.warning(f"⚠️ Image prompt too short in {key}, enhanced to: {image_prompt[:50]}...")
            
            return {
                "caption": caption,
                "hashtags": hashtags,
                "call_to_action": call_to_action,
                "image_prompt": image_prompt
            }
            
        except Exception as e:
            logger.error(f"🚨 Error standardizing post fields for {key}: {e}")
            return {
                "caption": "Content coming soon!",
                "hashtags": ["#Content", "#Update"],
                "call_to_action": "Stay tuned!",
                "image_prompt": "High-quality engaging visual content"
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
        """Save image data to R2 storage."""
        try:
            return await self.output_r2_client.write_binary(key, image_data)
        except Exception as e:
            logger.error(f"Error saving image to R2: {e}")
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
        
        # 🎯 ENHANCED IMAGE PROMPT EXTRACTION with multiple fallbacks
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
            post_number = len([o for o in objects if "ready_post_" in o["Key"]]) + 1
            logger.info(f"📊 Current post number for {username}: {post_number}")
        except Exception as e:
            logger.warning(f"⚠️ Could not list existing objects in {output_dir}, assuming post_number=1: {e}")
            post_number = 1
        
        # Create file paths for both JSON and image
        json_key = f"{output_dir}ready_post_{post_number}.json"
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
        🎯 ENHANCED IMAGE PROMPT EXTRACTION with multiple fallback strategies.
        """
        try:
            # Strategy 1: Direct extraction from post object
            prompt = post.get("image_prompt") or post.get("visual_prompt")
            if prompt and len(str(prompt).strip()) > 10:
                logger.info(f"✅ Found direct image prompt in post for {key}: {str(prompt)[:50]}...")
                return str(prompt).strip()
            
            # Strategy 2: Alternative field names
            alt_fields = ["media_suggestion", "visual_direction", "image_description", "visual_concept"]
            for field in alt_fields:
                prompt = post.get(field)
                if prompt and len(str(prompt).strip()) > 10:
                    logger.info(f"✅ Found image prompt in alternative field '{field}' for {key}")
                    return str(prompt).strip()
            
            # Strategy 3: Search in original data structure
            for field_name, field_value in original_data.items():
                if isinstance(field_value, str) and any(keyword in field_name.lower() for keyword in ["image", "visual", "media"]):
                    if len(field_value.strip()) > 15:
                        logger.info(f"✅ Found image prompt in original data field '{field_name}' for {key}")
                        return field_value.strip()
                elif isinstance(field_value, dict):
                    nested_prompt = field_value.get("image_prompt") or field_value.get("visual_prompt")
                    if nested_prompt and len(str(nested_prompt).strip()) > 10:
                        logger.info(f"✅ Found image prompt in nested field '{field_name}' for {key}")
                        return str(nested_prompt).strip()
            
            # Strategy 4: Intelligent generation based on content
            logger.warning(f"⚠️ No explicit image prompt found for {key}, generating intelligent default")
            return self._generate_intelligent_image_prompt(post, original_data, key)
            
        except Exception as e:
            logger.error(f"🚨 Error extracting image prompt from {key}: {e}")
            return self._generate_intelligent_image_prompt(post, original_data, key)

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
            # Extract and validate fields with fallbacks
            caption = post.get("caption", post.get("tweet_text", "Amazing content coming soon!"))
            if not isinstance(caption, str):
                caption = str(caption)
            
            hashtags = post.get("hashtags", [])
            if not isinstance(hashtags, list):
                if isinstance(hashtags, str):
                    import re
                    hashtags = re.findall(r'#\w+', hashtags)
                else:
                    hashtags = ["#Content", "#Update"]
            
            call_to_action = post.get("call_to_action", "Share your thoughts!")
            if not isinstance(call_to_action, str):
                call_to_action = str(call_to_action)
            
            output_post = {
                "post": {
                    "caption": caption,
                    "hashtags": hashtags,
                    "call_to_action": call_to_action,
                    "image_url": image_key,
                    "platform": platform,
                    "username": username
                },
                "status": "pending", #pending for the frontend to show the post as pending
                "processed_at": datetime.now().isoformat(),
                "image_generated": True,
                "original_format": original_data.get("original_format", "unknown")
            }
            
            # Add platform-specific fields
            if platform.lower() == "twitter":
                output_post["post"]["tweet_text"] = caption
            
            logger.info(f"✅ Created enhanced output post structure for {username}")
            return output_post
            
        except Exception as e:
            logger.error(f"🚨 Error creating output post: {e}")
            return {
                "post": {
                    "caption": "Content processed successfully!",
                    "hashtags": ["#Processed", "#Content"],
                    "call_to_action": "Check it out!",
                    "image_url": image_key,
                    "platform": platform,
                    "username": username
                },
                "status": "pending", #pending for the frontend to show the post as pending
                "processed_at": datetime.now().isoformat(),
                "image_generated": True,
                "fallback_used": True
            }

    async def run(self):
        async with aiohttp.ClientSession() as session:
            while True:
                try:
                    logger.info("🔄 Checking for new posts across all platforms...")
                    
                    # Collect objects from ALL platforms
                    all_objects = []
                    for platform in self.platforms:
                        platform_prefix = f"{self.input_prefix}{platform}/"
                        objects = await self.input_r2_client.list_objects(platform_prefix)
                        all_objects.extend(objects)
                        logger.debug(f"Found {len(objects)} objects in {platform_prefix}")
                    
                    # Process all objects from all platforms
                    urgent_files = []
                    regular_files = []
                    
                    for obj in all_objects:
                        key = obj["Key"]
                        if key.endswith(".json"):
                            if "urgent_" in key:
                                urgent_files.append(key)
                            elif "post_" in key:
                                regular_files.append(key)
                    
                    logger.info(f"📊 Found {len(urgent_files)} urgent and {len(regular_files)} regular posts")
                    
                    # Check which files actually need processing
                    prioritized_files = urgent_files + regular_files
                    pending_files = []
                    
                    for key in prioritized_files:
                        if await self.status_manager.is_pending(key):
                            pending_files.append(key)
                    
                    # Log processing status
                    if pending_files:
                        logger.info(f"🚀 Processing {len(pending_files)} posts:")
                        for f in pending_files:
                            logger.info(f"  - {f}")
                        
                        # Process files one at a time
                        for key in pending_files:
                            await self.process_post(key, session)
                    else:
                        logger.info("✨ No pending posts to process")
                    
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

