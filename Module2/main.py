import asyncio
from image_generator import ImageGenerator
from query_handler import QueryHandler
from utils.logging import logger

async def main():
    image_generator = ImageGenerator()
    query_handler = QueryHandler()
    try:
        await asyncio.gather(
            image_generator.run(),
            query_handler.run()
        )
    except KeyboardInterrupt:
        logger.info("Shutting down both modules...")
    except Exception as e:
        logger.error(f"Fatal error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
