from dotenv import load_dotenv
import os

load_dotenv()

R2_CONFIG = {
    "endpoint_url": os.getenv("R2_ENDPOINT_URL", "https://b21d96e73b908d7d7b822d41516ccc64.r2.cloudflarestorage.com"),
    "aws_access_key_id": os.getenv("R2_ACCESS_KEY", "986718fe67d6790c7fe4eeb78943adba"),
    "aws_secret_access_key": os.getenv("R2_SECRET_KEY", "08fb3b012163cce35bee80b54d83e3a6924f2679f466790a9c7fdd9456bc44fe"),
    "bucket_name": os.getenv("R2_BUCKET_NAME", "tasks")
}

STRUCTUREDB_R2_CONFIG = {
    "endpoint_url": os.getenv("STRUCTUREDB_ENDPOINT_URL", "https://b21d96e73b908d7d7b822d41516ccc64.r2.cloudflarestorage.com"),
    "aws_access_key_id": os.getenv("STRUCTUREDB_ACCESS_KEY", os.getenv("R2_ACCESS_KEY", "986718fe67d6790c7fe4eeb78943adba")),
    "aws_secret_access_key": os.getenv("STRUCTUREDB_SECRET_KEY", os.getenv("R2_SECRET_KEY", "08fb3b012163cce35bee80b54d83e3a6924f2679f466790a9c7fdd9456bc44fe")),
    "bucket_name": os.getenv("STRUCTUREDB_BUCKET_NAME", "structuredb")
}

AI_HORDE_CONFIG = {
    "api_key": os.getenv("AI_HORDE_API_KEY", "VxVGZGSL20PDRbi3mW2D5Q"),
    "base_url": "https://stablehorde.net/api/v2"
}

GEMINI_CONFIG = {
    "api_key": os.getenv("GEMINI_API_KEY", "AIzaSyDIPj_v_yICpcZayoPXfdymD1yVf0mjo2A"),
    "model": "gemini-2.0-flash",
    "max_tokens": 2000,
    "temperature": 0.2,
    "top_p": 0.95,
    "top_k": 40
}