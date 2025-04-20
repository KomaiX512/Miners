from utils.r2_client import R2Client
from utils.logging import logger

class StatusManager:
    def __init__(self):
        self.r2_client = R2Client()

    async def is_pending(self, key):
        data = await self.r2_client.read_json(key)
        if data:
            # If status is explicitly pending or error, process it
            if data.get("status") in ["pending", "error"]:
                logger.debug(f"File {key} is processable with status: {data.get('status')}")
                return True
            # If status field is missing, consider it as pending
            elif "status" not in data:
                logger.debug(f"File {key} has no status field, treating as pending")
                return True
            # Otherwise, it has a different status (e.g., processed)
            else:
                logger.debug(f"File {key} skipped, status: {data.get('status')}")
                return False
        logger.debug(f"File {key} skipped, invalid or empty data")
        return False

    async def mark_processed(self, key):
        data = await self.r2_client.read_json(key)
        if data:
            data["status"] = "processed"
            data.pop("status_message", None)
            return await self.r2_client.write_json(key, data)
        logger.error(f"Failed to mark {key} as processed: no data")
        return False
