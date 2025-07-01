"""Configuration settings for the project."""

# R2 Storage Configuration
R2_CONFIG = {
    'endpoint_url': f'https://570f213f1410829ee9a733a77a5f40e3.r2.cloudflarestorage.com',
    'aws_access_key_id': '18f60c98e08f1a24040de7cb7aab646c',
    'aws_secret_access_key': '0a8c50865ecab3c410baec4d751f35493fd981f4851203fe205fe0f86063a5f6',
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
    'embedding_model': 'all-MiniLM-L6-v2',  # Sentence transformer model
    'hnsw_space': 'cosine',
    'hnsw_M': 16,  # Higher M value for better performance, default is too small
    'hnsw_ef_construction': 100,  # Higher ef_construction value for better indexing
    'hnsw_ef_search': 20  # Higher ef_search value for more reliable search results
}

# Gemini API Configuration
GEMINI_CONFIG = {
    'api_key': 'AIzaSyAdap8Q8Srg_AKJXUsDcFChnK5lScWqgEY',
    'model': 'gemini-2.0-flash',  # Back to 2.0 for better performance
    'max_tokens': 2000,  # Increased back to 2000 for better quality
    'temperature': 0.2,  # Lower temperature for more focused, analytical responses
    'top_p': 0.95,       # Slightly more deterministic for business analysis
    'top_k': 40,         # Broader selection of tokens for more detailed responses
    'twitter_enabled': True,  # Enable Twitter-specific processing
    'platform_detection': True,  # Enable automatic platform detection
    'rate_limiting': {
        'requests_per_minute': 14,  # Conservative 14 RPM (leaving 1 RPM buffer)
        'min_delay_seconds': 4.0,   # 60/14 = ~4.3s, using 4s for safety
        'max_delay_seconds': 10.0,  # Maximum delay for backoff
        'enable_caching': True,     # Enable response caching
        'cache_duration': 1800,     # Cache for 30 minutes
        'fallback_to_mock': False   # NEVER fallback to mock mode - real content only
    }
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

