#!/usr/bin/env python3

import asyncio
import aiohttp
from utils.r2_client import R2Client
from utils.logging import logger

async def test_image_download_and_save():
    """
    Test downloading an image from a URL and saving it to R2 storage.
    """
    # Example image URL for testing (using a reliable test image)
    test_image_url = "https://httpbin.org/image/jpeg"
    
    # Output path in R2
    test_output_key = "test/image_download_test.jpg"
    
    logger.info(f"Testing image download from {test_image_url}")
    
    # Initialize R2 client
    r2_client = R2Client()
    
    # Download image
    async with aiohttp.ClientSession() as session:
        async with session.get(test_image_url) as response:
            if response.status != 200:
                logger.error(f"Failed to download test image: {response.status}")
                return False
                
            # Get image data
            image_data = await response.read()
            logger.info(f"Successfully downloaded image, size: {len(image_data)} bytes")
            
            # Save image to R2
            success = await r2_client.write_binary(test_output_key, image_data)
            
            if success:
                logger.info(f"Successfully saved image to {test_output_key}")
                return True
            else:
                logger.error(f"Failed to save image to {test_output_key}")
                return False

async def main():
    result = await test_image_download_and_save()
    print(f"Test {'succeeded' if result else 'failed'}")

if __name__ == "__main__":
    asyncio.run(main()) 