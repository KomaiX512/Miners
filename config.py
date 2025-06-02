"""Configuration settings for the project."""

# R2 Storage Configuration
R2_CONFIG = {
    'endpoint_url': f'https://b21d96e73b908d7d7b822d41516ccc64.r2.cloudflarestorage.com',
    'aws_access_key_id': '986718fe67d6790c7fe4eeb78943adba',
    'aws_secret_access_key': '08fb3b012163cce35bee80b54d83e3a6924f2679f466790a9c7fdd9456bc44fe',
    'bucket_name': 'structuredb',
    'personal_bucket_name': 'miner',  # Personal bucket for miner validation
    'bucket_name2': 'tasks',
    'NEWSDATA_API_KEY': 'pub_81555ab19b0046a7b3d947cddc59fe99c9146'
}


# Time Series Analysis Configuration
TIME_SERIES_CONFIG = {
    'forecast_periods': 3,  # Number of days to forecast
    'trend_threshold': 0.75  # Threshold for identifying trending content (75th percentile)
}

# Vector Database Configuration
VECTOR_DB_CONFIG = {
    'collection_name': 'social_posts',
    'embedding_model': 'all-MiniLM-L6-v2'  # Sentence transformer model
}

# Gemini API Configuration
GEMINI_CONFIG = {
    'api_key': 'AIzaSyA3CCL8Oyl29e7RK5UST5sNFW0wYhCZNsI',
    'model': 'gemini-2.0-flash',
    'max_tokens': 2000,
    'temperature': 0.2,  # Lower temperature for more focused, analytical responses
    'top_p': 0.95,       # Slightly more deterministic for business analysis
    'top_k': 40          # Broader selection of tokens for more detailed responses
}

# Content Templates
CONTENT_TEMPLATES = {
    'promotional': '🚀 New Drop Alert! {caption} {hashtags}',
    'informative': '📢 Did you know? {caption} {hashtags}',
    'engaging': '💬 Let us know what you think! {caption} {hashtags}',
    'trending': '🔥 Trending now: {caption} {hashtags}'
}

# Logging Configuration
LOGGING_CONFIG = {
    'level': 'INFO',
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
}

# Redis Configuration
REDIS_CONFIG = {
    'host': 'localhost',
    'port': 6379,
    'db': 0
}

