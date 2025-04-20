import aiobotocore.session
from botocore.exceptions import ClientError
import json
from config import R2_CONFIG
from utils.logging import logger

class R2Client:
    def __init__(self, config=None):
        self.session = aiobotocore.session.get_session()
        self.config = config or R2_CONFIG
        self.bucket_name = self.config["bucket_name"]

    async def list_all_objects(self, max_items=1000):
        """List all objects in the bucket to help with debugging and finding files."""
        async with self.session.create_client(
            "s3",
            endpoint_url=self.config["endpoint_url"],
            aws_access_key_id=self.config["aws_access_key_id"],
            aws_secret_access_key=self.config["aws_secret_access_key"],
            region_name="auto"
        ) as client:
            try:
                response = await client.list_objects_v2(Bucket=self.bucket_name, MaxKeys=max_items)
                contents = response.get('Contents', [])
                logger.info(f"Listed all objects in bucket {self.bucket_name}: {len(contents)} found")
                return contents
            except Exception as e:
                logger.error(f"Failed to list all objects in bucket {self.bucket_name}: {str(e)}")
                return []

    async def find_file_by_pattern(self, pattern):
        """Find files matching a specific pattern."""
        all_objects = await self.list_all_objects()
        matching_files = [obj["Key"] for obj in all_objects if pattern.lower() in obj["Key"].lower()]
        logger.info(f"Found {len(matching_files)} files matching pattern '{pattern}'")
        return matching_files

    async def list_objects(self, prefix):
        async with self.session.create_client(
            "s3",
            endpoint_url=self.config["endpoint_url"],
            aws_access_key_id=self.config["aws_access_key_id"],
            aws_secret_access_key=self.config["aws_secret_access_key"],
            region_name="auto"
        ) as client:
            try:
                response = await client.list_objects_v2(Bucket=self.bucket_name, Prefix=prefix)
                contents = response.get('Contents', [])
                logger.debug(f"Listed objects with prefix {prefix}: {len(contents)} found")
                if not contents:
                    logger.warning(f"No objects found with prefix {prefix} in bucket {self.bucket_name}")
                return contents
            except ClientError as e:
                error_code = e.response.get('Error', {}).get('Code', 'Unknown')
                error_message = e.response.get('Error', {}).get('Message', str(e))
                logger.error(f"Failed to list objects with prefix {prefix}: {error_code} - {error_message}")
                return []
            except Exception as e:
                logger.error(f"Unexpected error when listing objects with prefix {prefix}: {str(e)}")
                return []

    async def read_json(self, key):
        async with self.session.create_client(
            "s3",
            endpoint_url=self.config["endpoint_url"],
            aws_access_key_id=self.config["aws_access_key_id"],
            aws_secret_access_key=self.config["aws_secret_access_key"],
            region_name="auto"
        ) as client:
            try:
                response = await client.get_object(Bucket=self.bucket_name, Key=key)
                async with response["Body"] as stream:
                    data = await stream.read()
                try:
                    json_data = json.loads(data.decode("utf-8"))
                    logger.debug(f"Read JSON from {key}")
                    return json_data
                except json.JSONDecodeError as je:
                    logger.error(f"Failed to decode JSON from {key}: {je}")
                    return None
            except ClientError as e:
                error_code = e.response.get('Error', {}).get('Code', 'Unknown')
                error_message = e.response.get('Error', {}).get('Message', str(e))
                logger.error(f"Failed to read JSON from {key}: {error_code} - {error_message}")
                return None
            except Exception as e:
                logger.error(f"Unexpected error when reading {key}: {str(e)}")
                return None

    async def write_json(self, key, data):
        async with self.session.create_client(
            "s3",
            endpoint_url=self.config["endpoint_url"],
            aws_access_key_id=self.config["aws_access_key_id"],
            aws_secret_access_key=self.config["aws_secret_access_key"],
            region_name="auto"
        ) as client:
            try:
                json_data = json.dumps(data, indent=2).encode("utf-8")
                await client.put_object(
                    Bucket=self.bucket_name,
                    Key=key,
                    Body=json_data
                )
                logger.info(f"Successfully wrote JSON to {key}")
                return True
            except ClientError as e:
                error_code = e.response.get('Error', {}).get('Code', 'Unknown')
                error_message = e.response.get('Error', {}).get('Message', str(e))
                logger.error(f"Failed to write JSON to {key}: {error_code} - {error_message}")
                return False
            except Exception as e:
                logger.error(f"Unexpected error when writing to {key}: {str(e)}")
                return False