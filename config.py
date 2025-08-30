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

# StructuredDB R2 Configuration (for Module2)
STRUCTUREDB_R2_CONFIG = {
    'endpoint_url': f'https://570f213f1410829ee9a733a77a5f40e3.r2.cloudflarestorage.com',
    'aws_access_key_id': '18f60c98e08f1a24040de7cb7aab646c',
    'aws_secret_access_key': '0a8c50865ecab3c410baec4d751f35493fd981f4851203fe205fe0f86063a5f6',
    'bucket_name': 'structuredb'
}

# Ideogram API Configuration (replacing AI Horde)
IDEOGRAM_CONFIG = {
    'api_key': 'TzHxkD9XaGv-moRmaRAHx0lCXpBjd7quw_savsvNHY6kir1saKdGMp97c52cHF85ANslt4kJycCpfznX_PeYXQ',
    'base_url': 'https://api.ideogram.ai/v1/ideogram-v3/generate'
}

# Legacy AI Horde Config (for backward compatibility)
AI_HORDE_CONFIG = {
    'api_key': 'TzHxkD9XaGv-moRmaRAHx0lCXpBjd7quw_savsvNHY6kir1saKdGMp97c52cHF85ANslt4kJycCpfznX_PeYXQ',
    'base_url': 'https://api.ideogram.ai/v1/ideogram-v3/generate'
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
    'api_key': 'AIzaSyBAX0Ifkf1l1-okLEx3mIFmCtJtsPOOHns',
    'model': 'gemini-1.5-flash',  # More reliable than 2.5-flash-lite, less strict filtering
    'fallback_model': 'gemini-1.5-flash-exp',  # Alternative model for fallback
    'max_tokens': 2000,  # Increased back to 2000 for better quality
    'temperature': 0.7,  # Lower temperature for more focused, analytical responses
    'top_p': 0.95,       # Slightly more deterministic for business analysis
    'top_k': 40,         # Broader selection of tokens for more detailed responses
    'twitter_enabled': True,  # Enable Twitter-specific processing
    'platform_detection': True,  # Enable automatic platform detection
    'enable_ai_generation': True,  # Enable/disable AI content generation
    'fallback_to_ai_free': True,   # Use AI-free content when AI fails
    'safety_filter_bypass': True,  # Enable enhanced safety filter bypass
    'rate_limiting': {
        'requests_per_minute': 12,  # Increased to 12 RPM for better responsiveness
        'min_delay_seconds': 6.0,   # 60/12 = 5s + 1s buffer = 6s
        'max_delay_seconds': 120.0, # Maximum delay for backoff (2 minutes)
        'enable_caching': True,     # Enable response caching
        'cache_duration': 1800,     # Cache for 30 minutes
        'fallback_to_mock': False,  # NEVER fallback to mock mode - real content only
        'quota_safety_buffer': 0.30,  # 30% safety buffer
        'adaptive_backoff': True,   # Enable adaptive backoff on errors
        'max_retries': 3           # Allow more retries for better success rate
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

# Global account configuration functions
def get_global_account_config():
    """Get complete account configuration globally."""
    return get_account_info()

def get_global_primary_username():
    """Get primary username globally."""
    from global_config_manager import get_primary_username
    return get_primary_username()

def get_global_account_type():
    """Get account type (branding/personal) globally."""
    from global_config_manager import get_account_type
    return get_account_type()

def get_global_posting_style():
    """Get posting style globally."""
    from global_config_manager import get_posting_style
    return get_posting_style()

def get_global_platform():
    """Get platform globally."""
    from global_config_manager import get_platform
    return get_platform()

def get_global_competitors():
    """Get competitors list globally."""
    from global_config_manager import get_competitors
    return get_competitors()

def ensure_account_config():
    """Ensure account configuration is available."""
    return ensure_global_config()

