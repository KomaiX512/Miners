
import aiohttp
import asyncio
import re
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

    async def process_post(self, key, session):
        if not await self.status_manager.is_pending(key):
            return

        data = await self.r2_client.read_json(key)
        if not data or "post" not in data:
            logger.error(f"Invalid JSON format in {key}")
            return

        post = data["post"]
        prompt = post.get("visual_prompt")
        if not prompt:
            logger.error(f"No visual prompt in {key}")
            return

        logger.info(f"Generating image for {key}")
        image_url = await self.generate_image(prompt, session)
        if not image_url:
            logger.error(f"Failed to generate image for {key}")
            data["status"] = "error"
            data["status_message"] = "Image generation failed"
            await self.r2_client.write_json(key, data)
            return

        output_post = {
            "post": {
                "caption": post["caption"],
                "hashtags": post["hashtags"],
                "call_to_action": post["call_to_action"],
                "image_url": image_url
            },
            "status": "processed"
        }

        username = key.split("/")[1]
        output_dir = f"{self.output_prefix}{username}/"
        objects = await self.r2_client.list_objects(output_dir)
        post_number = len([o for o in objects if "ready_post_" in o["Key"]]) + 1
        output_key = f"{output_dir}ready_post_{post_number}.json"

        if await self.r2_client.write_json(output_key, output_post):
            await self.status_manager.mark_processed(key)
            logger.info(f"Successfully processed {key} to {output_key}")

    async def run(self):
        async with aiohttp.ClientSession() as session:
            while True:
                try:
                    logger.info("Checking for new posts...")
                    objects = await self.r2_client.list_objects(self.input_prefix)
                    logger.debug(f"Found {len(objects)} objects under {self.input_prefix}")
                    tasks = []
                    processable_files = []
                    for obj in objects:
                        key = obj["Key"]
                        if key.endswith(".json") and "post_" in key:
                            processable_files.append(key)
                            if await self.status_manager.is_pending(key):
                                logger.debug(f"Scheduling file for processing: {key}")
                                tasks.append(self.process_post(key, session))
                    logger.debug(f"Evaluated files: {processable_files}")
                    if tasks:
                        for task in tasks:
                            await task
                    else:
                        logger.debug("No processable posts found")
                    await asyncio.sleep(10)
                except Exception as e:
                    logger.error(f"Error in image generator loop: {e}")
                    await asyncio.sleep(10)
