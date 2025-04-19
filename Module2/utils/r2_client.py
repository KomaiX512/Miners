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
                logger.debug(f"Listed objects with prefix {prefix}: {len(response.get('Contents', []))} found")
                return response.get("Contents", [])
            except ClientError as e:
                logger.error(f"Failed to list objects with prefix {prefix}: {e}")
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
                json_data = json.loads(data.decode("utf-8"))
                logger.debug(f"Read JSON from {key}")
                return json_data
            except ClientError as e:
                logger.error(f"Failed to read JSON from {key}: {e}")
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
                await client.put_object(
                    Bucket=self.bucket_name,
                    Key=key,
                    Body=json.dumps(data, indent=2).encode("utf-8")
                )
                logger.info(f"Successfully wrote JSON to {key}")
                return True
            except ClientError as e:
                logger.error(f"Failed to write JSON to {key}: {e}")
                return False