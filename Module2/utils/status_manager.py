from utils.r2_client import R2Client
from utils.logging import logger
from config import STRUCTUREDB_R2_CONFIG

class StatusManager:
    def __init__(self):
        self.r2_client = R2Client()
        # Output client to check if files have been processed by Image Generator
        self.output_r2_client = R2Client(config=STRUCTUREDB_R2_CONFIG)

    async def is_pending(self, key):
        """
        🎯 ENHANCED STATUS CHECK: Determines if a file needs Image Generator processing.
        
        A file is considered pending for Image Generator if:
        1. It has status "pending" or "error" (standard cases)
        2. It has no status field (legacy case)
        3. It has status "processed" BUT no corresponding output exists in ready_post/ (NextPost processed, but Image Generator hasn't)
        """
        data = await self.r2_client.read_json(key)
        if not data:
            logger.debug(f"File {key} skipped, invalid or empty data")
            return False
            
        current_status = data.get("status")
        
        # Standard pending cases
        if current_status in ["pending", "error"]:
            logger.debug(f"File {key} is processable with status: {current_status}")
            return True
            
        # Legacy case - no status field
        if "status" not in data:
            logger.debug(f"File {key} has no status field, treating as pending")
            return True
            
        # 🎯 CRITICAL: Check if NextPost processed but Image Generator hasn't
        if current_status == "processed":
            # Extract platform and username from key: next_posts/platform/username/file.json
            try:
                key_parts = key.split("/")
                if len(key_parts) >= 4:
                    platform = key_parts[1]
                    username = key_parts[2]
                    
                    # Check if corresponding output exists in ready_post/
                    output_dir = f"ready_post/{platform}/{username}/"
                    
                    try:
                        output_objects = await self.output_r2_client.list_objects(output_dir)
                        ready_posts = [o for o in output_objects if "ready_post_" in o["Key"]]
                        
                        if not ready_posts:
                            logger.info(f"✅ File {key} marked as processed by NextPost but no Image Generator output found - needs processing")
                            return True
                        else:
                            logger.debug(f"File {key} already processed by Image Generator ({len(ready_posts)} outputs found)")
                            return False
                            
                    except Exception as e:
                        logger.warning(f"Could not check output for {key}: {e} - treating as pending")
                        return True
                        
            except Exception as e:
                logger.warning(f"Could not parse key format for {key}: {e} - treating as pending")
                return True
        
        # Other statuses (like "image_generated", "completed", etc.)
        logger.debug(f"File {key} skipped, status: {current_status}")
        return False

    async def mark_processed(self, key):
        """Mark a file as processed by Image Generator."""
        data = await self.r2_client.read_json(key)
        if data:
            data["status"] = "image_generated"  # More specific status
            data["image_generated_at"] = __import__('datetime').datetime.now().isoformat()
            data.pop("status_message", None)
            return await self.r2_client.write_json(key, data)
        logger.error(f"Failed to mark {key} as processed: no data")
        return False
