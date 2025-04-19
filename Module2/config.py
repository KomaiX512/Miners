from dotenv import load_dotenv
import os

load_dotenv()

R2_CONFIG = {
    "endpoint_url": os.getenv("R2_ENDPOINT_URL", "https://9069781eea9a108d41848d73443b3a87.r2.cloudflarestorage.com"),
    "aws_access_key_id": os.getenv("R2_ACCESS_KEY", "b94be077bc48dcc2aec3e4331233327e"),
    "aws_secret_access_key": os.getenv("R2_SECRET_KEY", "791d5eeddcd8ed5bf3f41bfaebbd37e58af7dcb12275b1422747605d7dc75bc4"),
    "bucket_name": os.getenv("R2_BUCKET_NAME", "tasks")
}

STRUCTUREDB_R2_CONFIG = {
    "endpoint_url": os.getenv("STRUCTUREDB_ENDPOINT_URL", "https://9069781eea9a108d41848d73443b3a87.r2.cloudflarestorage.com"),
    "aws_access_key_id": os.getenv("STRUCTUREDB_ACCESS_KEY", os.getenv("R2_ACCESS_KEY", "b94be077bc48dcc2aec3e4331233327e")),
    "aws_secret_access_key": os.getenv("STRUCTUREDB_SECRET_KEY", os.getenv("R2_SECRET_KEY", "791d5eeddcd8ed5bf3f41bfaebbd37e58af7dcb12275b1422747605d7dc75bc4")),
    "bucket_name": os.getenv("STRUCTUREDB_BUCKET_NAME", "structuredb")
}

AI_HORDE_CONFIG = {
    "api_key": os.getenv("AI_HORDE_API_KEY", "VxVGZGSL20PDRbi3mW2D5Q"),
    "base_url": "https://stablehorde.net/api/v2"
}

GEMINI_CONFIG = {
    "api_key": os.getenv("GEMINI_API_KEY", "AIzaSyDrvJG2BghzqtSK-HIZ_NsfRWiNwrIk3DQ"),
    "model": "gemini-2.0-flash",
    "max_tokens": 2000,
    "temperature": 0.2,
    "top_p": 0.95,
    "top_k": 40
}