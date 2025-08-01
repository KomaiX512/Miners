from dotenv import load_dotenv
import os

load_dotenv()

R2_CONFIG = {
    "endpoint_url": "https://570f213f1410829ee9a733a77a5f40e3.r2.cloudflarestorage.com",
    "aws_access_key_id": "18f60c98e08f1a24040de7cb7aab646c",
    "aws_secret_access_key": "0a8c50865ecab3c410baec4d751f35493fd981f4851203fe205fe0f86063a5f6",
    "bucket_name": "tasks"
}

STRUCTUREDB_R2_CONFIG = {
    "endpoint_url": "https://570f213f1410829ee9a733a77a5f40e3.r2.cloudflarestorage.com",
    "aws_access_key_id": "18f60c98e08f1a24040de7cb7aab646c",
    "aws_secret_access_key": "0a8c50865ecab3c410baec4d751f35493fd981f4851203fe205fe0f86063a5f6",
    "bucket_name": "structuredb"
}

AI_HORDE_CONFIG = {
    # Hardcoded AI Horde API key for guaranteed availability
    "api_key": "EaSj6zj-BZ9gL2ghaoN5sg",
    "base_url": "https://stablehorde.net/api/v2"
}

GEMINI_CONFIG = {
    "api_key": os.getenv("GEMINI_API_KEY", "AIzaSyAdap8Q8Srg_AKJXUsDcFChnK5lScWqgEY"),
    "model": "gemini-2.0-flash",
    "max_tokens": 2000,
    "temperature": 0.2,
    "top_p": 0.95,
    "top_k": 40,
    "rate_limiting": {
        "requests_per_minute": 14,
        "min_delay_seconds": 4.0,
        "max_delay_seconds": 10.0,
        "enable_caching": True,
        "cache_duration": 1800,
        "fallback_to_mock": False
    }
}

# Platform Configuration - Dynamic support for all three platforms
PLATFORM_CONFIG = {
    "supported_platforms": ["instagram", "twitter", "facebook"],
    "platform_features": {
        "instagram": {
            "content_type": "caption",
            "max_hashtags": 30,
            "character_limit": 2200,
            "tone": "casual_visual",
            "focus": "visual_storytelling"
        },
        "twitter": {
            "content_type": "tweet_text", 
            "max_hashtags": 5,
            "character_limit": 280,
            "tone": "concise_impactful",
            "focus": "quick_engagement"
        },
        "facebook": {
            "content_type": "caption",
            "max_hashtags": 15,
            "character_limit": 63206,
            "tone": "conversational_community",
            "focus": "community_engagement"
        }
    },
    "platform_detection": True,
    "auto_platform_optimization": True
}