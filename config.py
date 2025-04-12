"""Configuration settings for the project."""

# R2 Storage Configuration
R2_CONFIG = {
    'endpoint_url': f'https://9069781eea9a108d41848d73443b3a87.r2.cloudflarestorage.com',
    'aws_access_key_id': 'b94be077bc48dcc2aec3e4331233327e',
    'aws_secret_access_key': '791d5eeddcd8ed5bf3f41bfaebbd37e58af7dcb12275b1422747605d7dc75bc4',
    'bucket_name': 'structuredb',
    'bucket_name2': 'tasks'
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
    'api_key': 'AIzaSyDrvJG2BghzqtSK-HIZ_NsfRWiNwrIk3DQ',
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