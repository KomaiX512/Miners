"""
AUTONOMOUS NEWS4U SYSTEM
Runs independently every 24 hours to generate News4U for all accounts in R2 bucket.

This system:
1. Reads account info from R2 bucket: AccountInfo/<platform>/<username>/info.json
2. Retrieves hashtags from: recommendations/<platform>/<username>/recommendations_*.json
3. Generates 3 news articles using SimplifiedNewsForYouModule
4. Exports to: news_for_you/<platform>/<username>/news_*.json
5. Tracks processed accounts to avoid duplicates
6. Loops every 24 hours (2 minutes for testing)
"""

import requests
import json
import logging
import time
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Set
import re
from pathlib import Path
import google.generativeai as genai

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('autonomous_news4u.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class AutonomousNews4USystem:
    """
    Autonomous News4U system that processes all accounts daily.
    """
    
    def __init__(self, config_file="config.py", test_mode=False):
        """Initialize autonomous system."""
        self.test_mode = test_mode
        self.processing_interval = 120 if test_mode else 86400  # 2 minutes vs 24 hours
        
        # Load configuration
        self.config = self._load_config(config_file)
        
        # Initialize R2 storage
        self.r2_storage = self._initialize_r2_storage()
        
        # Initialize News4U module
        self.news_module = self._initialize_news_module()
        
        # Initialize Gemini API for intelligent hashtag transformation
        self.gemini_config = self.config.get('GEMINI_CONFIG', {})
        self.gemini_api_key = self.gemini_config.get('api_key')
        if self.gemini_api_key:
            genai.configure(api_key=self.gemini_api_key)
            self.gemini_model = genai.GenerativeModel(self.gemini_config.get('model', 'gemini-1.5-flash'))
            logger.info("🧠 Gemini API initialized for autonomous hashtag intelligence")
        else:
            self.gemini_model = None
            logger.warning("⚠️ Gemini API not configured in autonomous system")
        
        # Track processed accounts (in-memory for session)
        self.processed_accounts = set()
        self.processed_accounts_file = "processed_accounts.json"
        
        logger.info(f"🚀 Autonomous News4U System initialized")
        logger.info(f"⏰ Processing interval: {self.processing_interval}s ({'TEST MODE' if test_mode else 'PRODUCTION'})")
    
    def _load_config(self, config_file):
        """Load configuration from config file."""
        try:
            import importlib.util
            spec = importlib.util.spec_from_file_location("config", config_file)
            config_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(config_module)
            
            config = {
                'R2_CONFIG': config_module.R2_CONFIG,
                'NEWSAPI_KEY': getattr(config_module, 'NEWSAPI_KEY', 'a747734c8a9f41a4a6a6b98e3e66d9d2'),
                'GEMINI_CONFIG': getattr(config_module, 'GEMINI_CONFIG', {})
            }
            logger.info("✅ Configuration loaded successfully")
            return config
        except Exception as e:
            logger.error(f"❌ Failed to load configuration: {e}")
            raise
    
    def _initialize_r2_storage(self):
        """Initialize R2 storage manager."""
        try:
            from r2_storage_manager import R2StorageManager
            r2_storage = R2StorageManager(self.config['R2_CONFIG'])
            logger.info("✅ R2 Storage Manager initialized")
            return r2_storage
        except Exception as e:
            logger.error(f"❌ Failed to initialize R2 storage: {e}")
            raise
    
    def _initialize_news_module(self):
        """Initialize the simplified news module."""
        try:
            from simplified_news_for_you import SimplifiedNewsForYouModule
            news_module = SimplifiedNewsForYouModule(
                config=self.config,
                r2_storage=self.r2_storage
            )
            logger.info("✅ SimplifiedNewsForYouModule initialized")
            return news_module
        except Exception as e:
            logger.error(f"❌ Failed to initialize news module: {e}")
            raise
    
    def run_autonomous_loop(self):
        """Main autonomous loop that runs every 24 hours."""
        logger.info("🔄 Starting autonomous News4U processing loop")
        
        while True:
            try:
                cycle_start = datetime.now()
                logger.info(f"📅 Starting new processing cycle at {cycle_start}")
                
                # Reset processed accounts for new cycle
                self.processed_accounts.clear()
                
                # Process all accounts
                success_count, error_count = self.process_all_accounts()
                
                cycle_end = datetime.now()
                cycle_duration = (cycle_end - cycle_start).total_seconds()
                
                logger.info(f"✅ Processing cycle completed in {cycle_duration:.2f}s")
                logger.info(f"📊 Results: {success_count} successful, {error_count} errors")
                
                # Wait for next cycle
                logger.info(f"😴 Waiting {self.processing_interval}s until next cycle...")
                time.sleep(self.processing_interval)
                
            except KeyboardInterrupt:
                logger.info("🛑 Autonomous loop stopped by user")
                break
            except Exception as e:
                logger.error(f"❌ Critical error in autonomous loop: {e}")
                logger.info(f"⏳ Waiting {self.processing_interval}s before retry...")
                time.sleep(self.processing_interval)
    
    def process_all_accounts(self):
        """Process all accounts found in R2 bucket."""
        success_count = 0
        error_count = 0
        
        try:
            # Get all account info files from R2 bucket
            account_infos = self._get_all_account_infos()
            logger.info(f"🔍 Found {len(account_infos)} account info files")
            
            for account_info in account_infos:
                try:
                    if self._process_single_account(account_info):
                        success_count += 1
                    else:
                        error_count += 1
                except Exception as e:
                    logger.error(f"❌ Error processing account {account_info}: {e}")
                    error_count += 1
            
        except Exception as e:
            logger.error(f"❌ Error in process_all_accounts: {e}")
            error_count += 1
        
        return success_count, error_count
    
    def _get_all_account_infos(self):
        """Get all account info files from R2 bucket."""
        try:
            # List all objects with AccountInfo prefix
            objects = self.r2_storage.list_objects(prefix="AccountInfo/", bucket="tasks")
            
            # Filter for info.json files
            account_infos = []
            for obj in objects:
                key = obj['Key']
                if key.endswith('/info.json'):
                    account_infos.append(key)
            
            logger.info(f"📋 Found {len(account_infos)} account info files")
            return account_infos
            
        except Exception as e:
            logger.error(f"❌ Error getting account infos: {e}")
            return []
    
    def _process_single_account(self, account_info_key):
        """Process a single account for News4U generation with seamless fallback."""
        try:
            # Extract platform and username from key
            # Expected format: AccountInfo/<platform>/<username>/info.json
            parts = account_info_key.split('/')
            if len(parts) != 4:
                logger.error(f"❌ Invalid account info key format: {account_info_key}")
                return False
            
            platform = parts[1]
            username = parts[2]
            
            # Create unique identifier for this account
            account_id = f"{platform}:{username}"
            
            # Skip if already processed in this cycle
            if account_id in self.processed_accounts:
                logger.info(f"⏭️ Skipping {account_id} - already processed this cycle")
                return True
            
            logger.info(f"🎯 Processing account: {account_id}")
            
            # Read account info with fallback
            account_info = self._read_account_info_safely(account_info_key, account_id)
            if not account_info:
                logger.warning(f"⚠️ Skipping {account_id} - no account info available")
                return True  # Not an error, just no data available
            
            # Get hashtags with seamless fallback
            hashtags = self._get_account_hashtags_with_fallback(platform, username, account_info)
            
            # Transform hashtags using intelligent Gemini processing with fallback
            intelligent_keywords = self._transform_hashtags_intelligently_with_fallback(hashtags, username, platform, account_info)
            if intelligent_keywords:
                logger.info(f"🧠 Generated intelligent keywords for {account_id}: {intelligent_keywords}")
                hashtags = intelligent_keywords  # Use intelligent keywords instead
            
            # Generate news using simplified module with fallback
            news_results = self._generate_news_for_account_with_fallback(
                username, platform, account_info, hashtags
            )
            
            if not news_results:
                logger.warning(f"⚠️ No news generated for {account_id} - this should not happen with fallback system")
                return False
            
            # Export news to R2 bucket with fallback
            if self._export_news_to_r2_with_fallback(platform, username, news_results):
                logger.info(f"✅ Successfully processed {account_id}")
                self.processed_accounts.add(account_id)
                return True
            else:
                logger.warning(f"⚠️ Export failed for {account_id}, but news was generated successfully")
                # Still mark as processed since news generation succeeded
                self.processed_accounts.add(account_id)
                return True
            
        except Exception as e:
            logger.error(f"❌ Critical error processing account {account_info_key}: {e}")
            # Even critical errors should not stop the autonomous system
            logger.info(f"🔄 Continuing with next account after error in {account_info_key}")
            return False
    
    def _read_account_info_safely(self, account_info_key: str, account_id: str) -> Optional[Dict]:
        """Read account info with comprehensive error handling."""
        try:
            account_info = self.r2_storage.read_json(account_info_key, bucket="tasks")
            if account_info:
                return account_info
            else:
                logger.warning(f"⚠️ No account info found for {account_id}")
                return None
        except Exception as e:
            logger.error(f"❌ Error reading account info for {account_id}: {e}")
            return None
    
    def _get_account_hashtags(self, platform, username):
        """Get trending hashtags from recommendations bucket."""
        try:
            # List recommendation files for this account
            prefix = f"recommendations/{platform}/{username}/"
            objects = self.r2_storage.list_objects(prefix=prefix, bucket="tasks")
            
            # Find the most recent recommendations file
            recommendation_files = [obj['Key'] for obj in objects if obj['Key'].endswith('.json')]
            if not recommendation_files:
                logger.warning(f"⚠️ No recommendation files found for {platform}:{username}")
                return []
            
            # Use the most recent file (or first available)
            recommendation_file = recommendation_files[0]  # Could sort by timestamp if needed
            
            # Read recommendations
            recommendations = self.r2_storage.read_json(recommendation_file, bucket="tasks")
            if not recommendations:
                logger.warning(f"⚠️ Failed to read recommendations for {platform}:{username}")
                return []
            
            # Extract trending hashtags
            content_intelligence = recommendations.get('content_intelligence', {})
            hashtags = content_intelligence.get('trending_hashtags', [])
            
            if hashtags:
                logger.info(f"📌 Found {len(hashtags)} hashtags for {platform}:{username}")
                return hashtags
            else:
                logger.warning(f"⚠️ No trending hashtags in recommendations for {platform}:{username}")
                return []
            
        except Exception as e:
            logger.error(f"❌ Error getting hashtags for {platform}:{username}: {e}")
            return []
    
    def _get_account_hashtags_with_fallback(self, platform: str, username: str, account_info: Dict) -> List[str]:
        """Get hashtags with seamless fallback - never returns empty list."""
        try:
            # Try to get hashtags from recommendations
            hashtags = self._get_account_hashtags(platform, username)
            
            if hashtags and len(hashtags) > 0:
                logger.info(f"📌 Found {len(hashtags)} hashtags for {platform}:{username}")
                return hashtags
            else:
                logger.info(f"🔄 No hashtags found for {platform}:{username} - using intelligent fallback")
                fallback_keywords = self._get_fallback_keywords(username, platform, account_info)
                if fallback_keywords:
                    logger.info(f"✅ Generated fallback keywords for {platform}:{username}: {fallback_keywords}")
                    return fallback_keywords
                else:
                    logger.warning(f"⚠️ Fallback keywords failed for {platform}:{username} - using emergency keywords")
                    return ['business news', 'technology trends', 'market updates']
                    
        except Exception as e:
            logger.error(f"❌ Error getting hashtags for {platform}:{username}: {e}")
            logger.info(f"🚨 Using emergency keywords for {platform}:{username}")
            return ['business news', 'technology trends', 'market updates']
    
    def _generate_news_for_account(self, username, platform, account_info, hashtags):
        """Generate news using the simplified news module."""
        try:
            # Extract account details
            account_type = account_info.get('accountType', 'personal')
            posting_style = account_info.get('postingStyle', 'casual')
            
            # Generate news using simplified module
            news_results = self.news_module.generate_news_for_account_sync(
                username=username,
                platform=platform,
                account_type=account_type,
                posting_style=posting_style,
                user_posts=None,  # Not needed for simplified module
                trending_hashtags=hashtags
            )
            
            if news_results and len(news_results) > 0:
                logger.info(f"✅ Generated {len(news_results)} news items for {username}")
                return news_results
            else:
                logger.warning(f"⚠️ No news results for {username}")
                return []
            
        except Exception as e:
            logger.error(f"❌ Error generating news for {username}: {e}")
            return []
    
    def _generate_news_for_account_with_fallback(self, username: str, platform: str, 
                                               account_info: Dict, hashtags: List[str]) -> List[Dict]:
        """Generate news with seamless fallback - never fails."""
        try:
            # Extract account details
            account_type = account_info.get('accountType', 'personal')
            posting_style = account_info.get('postingStyle', 'casual')
            
            # Generate news using simplified module
            news_results = self.news_module.generate_news_for_account_sync(
                username=username,
                platform=platform,
                account_type=account_type,
                posting_style=posting_style,
                user_posts=None,  # Not needed for simplified module
                trending_hashtags=hashtags
            )
            
            if news_results and len(news_results) > 0:
                logger.info(f"✅ Generated {len(news_results)} news items for {username}")
                return news_results
            else:
                logger.warning(f"⚠️ No news results for {username} - this should not happen with fallback system")
                # Emergency fallback - create basic news items
                return self._create_emergency_news_items(username, platform, account_type)
            
        except Exception as e:
            logger.error(f"❌ Error generating news for {username}: {e}")
            # Emergency fallback
            return self._create_emergency_news_items(username, platform, account_type)
    
    def _export_news_to_r2(self, platform, username, news_results):
        """Export news results to R2 bucket."""
        try:
            # Create export filename with timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"news_{timestamp}_{username}.json"
            
            # Create R2 key following the pattern: news_for_you/<platform>/<username>/news_*.json
            r2_key = f"news_for_you/{platform}/{username}/{filename}"
            
            # Prepare export data structure
            export_data = {
                "username": username,
                "platform": platform,
                "generated_at": datetime.now().isoformat(),
                "news_count": len(news_results),
                "news_items": news_results,
                "autonomous_system": True,
                "system_version": "1.0"
            }
            
            # Upload to R2 bucket
            success = self.r2_storage.put_object(
                key=r2_key,
                content=json.dumps(export_data, indent=2),
                bucket="tasks"
            )
            
            if success:
                logger.info(f"📤 Exported news to: {r2_key}")
                return True
            else:
                logger.error(f"❌ Failed to export news to: {r2_key}")
                return False
            
        except Exception as e:
            logger.error(f"❌ Error exporting news: {e}")
            return False
    
    def _export_news_to_r2_with_fallback(self, platform: str, username: str, news_results: List[Dict]) -> bool:
        """Export news to R2 with comprehensive fallback - never fails completely."""
        try:
            # Create export filename with timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"news_{timestamp}_{username}.json"
            
            # Create R2 key following the pattern: news_for_you/<platform>/<username>/news_*.json
            r2_key = f"news_for_you/{platform}/{username}/{filename}"
            
            # Prepare export data structure
            export_data = {
                "username": username,
                "platform": platform,
                "generated_at": datetime.now().isoformat(),
                "news_count": len(news_results),
                "news_items": news_results,
                "autonomous_system": True,
                "system_version": "1.0",
                "fallback_used": any(item.get('is_fallback', False) for item in news_results)
            }
            
            # Upload to R2 bucket
            success = self.r2_storage.put_object(
                key=r2_key,
                content=json.dumps(export_data, indent=2),
                bucket="tasks"
            )
            
            if success:
                logger.info(f"📤 Exported news to: {r2_key}")
                return True
            else:
                logger.warning(f"⚠️ Failed to export news to: {r2_key}")
                return False
            
        except Exception as e:
            logger.error(f"❌ Error exporting news: {e}")
            # Export failure should not stop the autonomous system
            logger.info(f"🔄 Continuing without export for {username}")
            return False
    
    def test_single_account(self, platform, username):
        """Test processing for a single account (for debugging)."""
        logger.info(f"🧪 Testing single account: {platform}:{username}")
        
        account_info_key = f"AccountInfo/{platform}/{username}/info.json"
        result = self._process_single_account(account_info_key)
        
        if result:
            logger.info(f"✅ Test successful for {platform}:{username}")
        else:
            logger.error(f"❌ Test failed for {platform}:{username}")
        
        return result
    
    def _transform_hashtags_intelligently(self, hashtags: List[str], username: str, platform: str, account_info: Dict) -> List[str]:
        """Transform hashtags using Gemini intelligence (mirrors simplified_news_for_you.py logic)."""
        if not self.gemini_model:
            logger.warning(f"⚠️ Gemini not available for {username} - using original hashtags")
            return hashtags[:3]  # Return top 3 original hashtags
        
        try:
            # Clean hashtags
            clean_hashtags = []
            for tag in hashtags:
                clean_tag = str(tag).replace('#', '').strip()
                if clean_tag:
                    clean_hashtags.append(clean_tag)
            
            if not clean_hashtags:
                return hashtags[:3]
            
            # Take up to 20 hashtags as specified
            hashtags_to_process = clean_hashtags[:20]
            account_type = account_info.get('accountType', 'personal')
            
            # Create intelligent prompt for Gemini
            prompt = self._create_hashtag_intelligence_prompt(hashtags_to_process, username, platform, account_type)
            
            logger.info(f"🧠 Autonomous system sending {len(hashtags_to_process)} hashtags to Gemini for {username}")
            
            # Call Gemini API
            response = self.gemini_model.generate_content(prompt)
            
            if response and response.text:
                keywords = self._parse_intelligent_keywords(response.text)
                if keywords and len(keywords) >= 1:
                    # Now we have refined hashtags with proper spacing
                    refined_hashtags = keywords
                    
                    # Detect country from hashtags for localized news
                    detected_country = self._detect_country_from_hashtags(hashtags_to_process + refined_hashtags)
                    
                    # Priority system: 1) Multi-word phrases, 2) Single words, 3) Take top 3
                    phrase_keywords = []
                    single_keywords = []
                    
                    for hashtag in refined_hashtags:
                        if ' ' in hashtag.strip():
                            phrase_keywords.append(hashtag.strip())
                        else:
                            single_keywords.append(hashtag.strip())
                    
                    # Combine with priority: phrases first, then single words
                    prioritized_keywords = phrase_keywords + single_keywords
                    
                    # Take exactly 3 keywords
                    final_keywords = prioritized_keywords[:3]
                    
                    # If we still need more, use original hashtags as fallback
                    while len(final_keywords) < 3 and len(final_keywords) < len(hashtags_to_process):
                        fallback = hashtags_to_process[len(final_keywords)].lower()
                        if fallback not in final_keywords:
                            final_keywords.append(fallback)
                        else:
                            break
                    
                    # Store detected country for NewsAPI calls
                    self._detected_country = detected_country
                    
                    logger.info(f"✅ Autonomous refined {len(final_keywords)} hashtags to searchable keywords for {username}: {final_keywords}")
                    logger.info(f"🌍 Detected country for localized news: {detected_country}")
                    return final_keywords
                else:
                    logger.warning(f"⚠️ Invalid Gemini response format for {username}")
            else:
                logger.warning(f"⚠️ Empty Gemini response for {username}")
        
        except Exception as e:
            logger.error(f"❌ Gemini intelligence failed for {username}: {str(e)}")
        
        # Fallback to original hashtags
        logger.info(f"🔄 Using original hashtags for {username}")
        # Set default country for fallback
        self._detected_country = 'us'
        return hashtags[:3]
    
    def _transform_hashtags_intelligently_with_fallback(self, hashtags: List[str], username: str, 
                                                       platform: str, account_info: Dict) -> List[str]:
        """Transform hashtags with seamless fallback - never fails."""
        try:
            if not self.gemini_model:
                logger.info(f"🔄 Gemini not available for {username} - using original hashtags")
                return hashtags[:3] if len(hashtags) >= 3 else hashtags
            
            # Try Gemini transformation
            intelligent_keywords = self._transform_hashtags_intelligently(hashtags, username, platform, account_info)
            if intelligent_keywords and len(intelligent_keywords) >= 3:
                logger.info(f"✅ Gemini transformation successful for {username}: {intelligent_keywords[:3]}")
                return intelligent_keywords[:3]
            else:
                logger.warning(f"⚠️ Gemini transformation incomplete for {username}, using original hashtags")
                return hashtags[:3] if len(hashtags) >= 3 else hashtags
                
        except Exception as e:
            logger.error(f"❌ Gemini transformation failed for {username}: {e}")
            logger.info(f"🔄 Using original hashtags for {username}")
            return hashtags[:3] if len(hashtags) >= 3 else hashtags
    
    def _create_hashtag_intelligence_prompt(self, hashtags: List[str], username: str, platform: str, account_type: str) -> str:
        """Create prompt for Gemini to ONLY separate merged words in hashtags."""
        hashtags_text = ", ".join(hashtags)
        
        prompt = f"""You are a hashtag word separation specialist. Your ONLY job is to add spaces between merged words in hashtags.

HASHTAGS TO REFINE:
{hashtags_text}

TASK: For each hashtag, identify if it contains merged words and separate them with spaces. DO NOT create new keywords or hallucinate - only separate existing merged words.

EXAMPLES:
- "fentybeauty" -> "fenty beauty"
- "aiinvestment" -> "ai investment" 
- "techstocks" -> "tech stocks"
- "shortselling" -> "short selling"
- "makeup" -> "makeup" (already single word, no change)

RULES:
1. ONLY separate merged words - do not create new terms
2. Keep original hashtag meaning intact
3. If hashtag is already a single word, return as-is
4. Remove # symbol but preserve all original words

RESPONSE FORMAT (JSON only):
{{
  "refined_hashtags": ["separated phrase 1", "separated phrase 2", "etc"]
}}

Separate merged words now:"""
        
        return prompt
    
    def _parse_intelligent_keywords(self, response_text: str) -> List[str]:
        """Parse Gemini's intelligent keywords response (mirrors simplified_news_for_you.py logic)."""
        try:
            # Clean response text
            response_text = response_text.strip()
            
            # Handle markdown formatting
            if '```json' in response_text:
                start = response_text.find('```json') + 7
                end = response_text.find('```', start)
                response_text = response_text[start:end].strip()
            elif '```' in response_text:
                start = response_text.find('```') + 3
                end = response_text.find('```', start)
                response_text = response_text[start:end].strip()
            
            # Find JSON object
            start_brace = response_text.find('{')
            end_brace = response_text.rfind('}') + 1
            
            if start_brace != -1 and end_brace > start_brace:
                json_text = response_text[start_brace:end_brace]
                parsed = json.loads(json_text)
                
                refined_hashtags = parsed.get('refined_hashtags', [])
                
                if refined_hashtags and isinstance(refined_hashtags, list):
                    # Clean and validate refined hashtags
                    clean_hashtags = []
                    for hashtag in refined_hashtags:
                        if isinstance(hashtag, str) and hashtag.strip():
                            clean_hashtags.append(hashtag.strip())
                    
                    logger.info(f"🎯 Parsed {len(clean_hashtags)} refined hashtags from Gemini response")
                    return clean_hashtags
                else:
                    logger.warning("⚠️ No valid refined hashtags found in Gemini response")
            else:
                logger.warning("⚠️ No valid JSON found in Gemini response")
                
        except json.JSONDecodeError as e:
            logger.error(f"❌ JSON parsing error: {e}")
        except Exception as e:
            logger.error(f"❌ Error parsing Gemini response: {e}")
        
        return []
    
    def _detect_country_from_hashtags(self, hashtags: List[str]) -> str:
        """Detect country from hashtags based on brands, cities, or country names."""
        # Country mappings for brands, companies, cities, and country names
        country_mappings = {
            # US brands and companies
            'spacex': 'us', 'tesla': 'us', 'apple': 'us', 'google': 'us', 'microsoft': 'us',
            'amazon': 'us', 'facebook': 'us', 'meta': 'us', 'netflix': 'us', 'uber': 'us',
            'airbnb': 'us', 'twitter': 'us', 'instagram': 'us', 'youtube': 'us', 'linkedin': 'us',
            'walmart': 'us', 'mcdonalds': 'us', 'starbucks': 'us', 'cocacola': 'us', 'pepsi': 'us',
            'nike': 'us', 'adidas': 'de', 'boeing': 'us', 'ford': 'us', 'gm': 'us', 'chevrolet': 'us',
            
            # US cities
            'newyork': 'us', 'losangeles': 'us', 'chicago': 'us', 'houston': 'us', 'miami': 'us',
            'sanfrancisco': 'us', 'boston': 'us', 'seattle': 'us', 'denver': 'us', 'atlanta': 'us',
            'dallas': 'us', 'philadelphia': 'us', 'phoenix': 'us', 'detroit': 'us', 'vegas': 'us',
            
            # UK brands and cities
            'london': 'gb', 'manchester': 'gb', 'birmingham': 'gb', 'liverpool': 'gb', 'bristol': 'gb',
            'bbc': 'gb', 'virgin': 'gb', 'bp': 'gb', 'shell': 'gb', 'vodafone': 'gb',
            
            # German brands
            'bmw': 'de', 'mercedes': 'de', 'volkswagen': 'de', 'audi': 'de', 'porsche': 'de',
            'siemens': 'de', 'sap': 'de', 'berlin': 'de', 'munich': 'de', 'hamburg': 'de',
            
            # French brands
            'loreal': 'fr', 'chanel': 'fr', 'lvmh': 'fr', 'paris': 'fr', 'lyon': 'fr', 'marseille': 'fr',
            
            # Japanese brands
            'toyota': 'jp', 'honda': 'jp', 'sony': 'jp', 'nintendo': 'jp', 'panasonic': 'jp',
            'tokyo': 'jp', 'osaka': 'jp', 'kyoto': 'jp',
            
            # Chinese brands
            'alibaba': 'cn', 'tencent': 'cn', 'baidu': 'cn', 'huawei': 'cn', 'xiaomi': 'cn',
            'beijing': 'cn', 'shanghai': 'cn', 'guangzhou': 'cn',
            
            # Indian brands
            'tata': 'in', 'reliance': 'in', 'infosys': 'in', 'wipro': 'in', 'mumbai': 'in',
            'delhi': 'in', 'bangalore': 'in', 'chennai': 'in', 'hyderabad': 'in',
            
            # Country names
            'america': 'us', 'usa': 'us', 'unitedstates': 'us', 'american': 'us',
            'britain': 'gb', 'uk': 'gb', 'england': 'gb', 'british': 'gb',
            'germany': 'de', 'german': 'de', 'deutschland': 'de',
            'france': 'fr', 'french': 'fr', 'japan': 'jp', 'japanese': 'jp',
            'china': 'cn', 'chinese': 'cn', 'india': 'in', 'indian': 'in'
        }
        
        # Check each hashtag for country indicators
        for hashtag in hashtags:
            hashtag_lower = hashtag.lower().replace('#', '').replace(' ', '').replace('_', '')
            
            # Direct match
            if hashtag_lower in country_mappings:
                detected = country_mappings[hashtag_lower]
                logger.info(f"🌍 Country detected from hashtag '{hashtag}': {detected.upper()}")
                return detected
            
            # Partial match for compound hashtags
            for brand, country in country_mappings.items():
                if brand in hashtag_lower:
                    logger.info(f"🌍 Country detected from hashtag '{hashtag}' (contains '{brand}'): {country.upper()}")
                    return country
        
        # Default to US/English if no country detected
        logger.info("🌍 No country detected from hashtags, defaulting to US")
        return 'us'
    
    def _get_fallback_keywords(self, username: str, platform: str, account_info: Dict) -> List[str]:
        """
        Generate intelligent fallback keywords when trending hashtags are not available.
        Provides 3-4 relevant keywords based on platform, account type, and common interests.
        """
        try:
            account_type = account_info.get('accountType', 'personal')
            logger.info(f"🔄 Generating intelligent fallback keywords for @{username} on {platform} ({account_type})")
            
            # Platform-specific fallback keywords
            platform_keywords = self._get_platform_fallback_keywords(platform)
            
            # Account type specific keywords
            account_type_keywords = self._get_account_type_fallback_keywords(account_type)
            
            # Username-based intelligent keywords
            username_keywords = self._get_username_based_keywords(username, platform)
            
            # Combine all keyword sources with priority
            all_keywords = []
            
            # Priority 1: Username-based keywords (most relevant)
            if username_keywords:
                all_keywords.extend(username_keywords)
                logger.info(f"🎯 Added username-based keywords: {username_keywords}")
            
            # Priority 2: Account type keywords
            if account_type_keywords:
                all_keywords.extend(account_type_keywords)
                logger.info(f"👤 Added account type keywords: {account_type_keywords}")
            
            # Priority 3: Platform keywords
            if platform_keywords:
                all_keywords.extend(platform_keywords)
                logger.info(f"📱 Added platform keywords: {platform_keywords}")
            
            # Remove duplicates while preserving order
            unique_keywords = list(dict.fromkeys(all_keywords))
            
            # Take exactly 4 fallback keywords
            final_keywords = unique_keywords[:4]
            
            # If we still need more, add generic high-value keywords
            while len(final_keywords) < 4:
                generic_keywords = ['business news', 'technology trends', 'market updates', 'industry insights']
                for generic in generic_keywords:
                    if generic not in final_keywords:
                        final_keywords.append(generic)
                        break
            
            # Set default country for fallback
            self._detected_country = 'us'
            
            logger.info(f"✅ Generated {len(final_keywords)} intelligent fallback keywords for @{username}: {final_keywords}")
            return final_keywords
            
        except Exception as e:
            logger.error(f"❌ Error generating fallback keywords for @{username}: {str(e)}")
            # Ultimate fallback: return basic high-value keywords
            return ['business news', 'technology trends', 'market updates']
    
    def _get_platform_fallback_keywords(self, platform: str) -> List[str]:
        """Get platform-specific fallback keywords."""
        platform_keywords = {
            'twitter': ['social media trends', 'digital marketing', 'online engagement', 'content strategy'],
            'instagram': ['visual content trends', 'social media marketing', 'influencer insights', 'brand engagement'],
            'facebook': ['social networking trends', 'community engagement', 'digital advertising', 'user behavior'],
            'linkedin': ['professional networking', 'business insights', 'career development', 'industry trends'],
            'tiktok': ['short-form content', 'viral trends', 'social media innovation', 'youth engagement'],
            'youtube': ['video content trends', 'creator economy', 'digital entertainment', 'content monetization']
        }
        
        return platform_keywords.get(platform.lower(), ['social media trends', 'digital marketing', 'online engagement'])
    
    def _get_account_type_fallback_keywords(self, account_type: str) -> List[str]:
        """Get account type specific fallback keywords."""
        account_type_keywords = {
            'personal': ['personal branding', 'social media tips', 'digital presence', 'online networking'],
            'business': ['business strategy', 'market analysis', 'industry insights', 'competitive intelligence'],
            'influencer': ['influencer marketing', 'content creation', 'audience engagement', 'brand partnerships'],
            'creator': ['content creation', 'creative trends', 'digital art', 'online communities'],
            'professional': ['professional development', 'career growth', 'industry expertise', 'business networking'],
            'brand': ['brand strategy', 'marketing trends', 'customer engagement', 'market positioning']
        }
        
        return account_type_keywords.get(account_type.lower(), ['digital strategy', 'online presence', 'social media'])
    
    def _get_username_based_keywords(self, username: str, platform: str) -> List[str]:
        """Generate intelligent keywords based on username analysis."""
        try:
            username_lower = username.lower()
            
            # Industry/domain detection from username
            industry_keywords = []
            
            # Technology/IT related
            if any(tech in username_lower for tech in ['tech', 'ai', 'data', 'code', 'dev', 'software', 'digital']):
                industry_keywords.extend(['artificial intelligence', 'technology innovation', 'digital transformation'])
            
            # Business/Finance related
            if any(biz in username_lower for biz in ['biz', 'finance', 'invest', 'trade', 'market', 'stock', 'crypto']):
                industry_keywords.extend(['financial markets', 'investment trends', 'business strategy'])
            
            # Beauty/Fashion related
            if any(beauty in username_lower for beauty in ['beauty', 'fashion', 'style', 'makeup', 'cosmetic', 'glam']):
                industry_keywords.extend(['beauty industry', 'fashion trends', 'cosmetics market'])
            
            # Education/Knowledge related
            if any(edu in username_lower for edu in ['edu', 'learn', 'study', 'knowledge', 'academic', 'research']):
                industry_keywords.extend(['education technology', 'learning trends', 'academic insights'])
            
            # Entertainment/Media related
            if any(ent in username_lower for ent in ['entertainment', 'media', 'show', 'tv', 'film', 'music']):
                industry_keywords.extend(['entertainment industry', 'media trends', 'content creation'])
            
            # Location-based keywords
            location_keywords = []
            if any(loc in username_lower for loc in ['pakistan', 'pakistani', 'desi', 'asian', 'middleeast']):
                location_keywords.extend(['Pakistani business', 'South Asian markets', 'emerging economies'])
            elif any(loc in username_lower for loc in ['us', 'usa', 'american', 'california', 'newyork']):
                location_keywords.extend(['US markets', 'American business', 'North American trends'])
            elif any(loc in username_lower for loc in ['uk', 'british', 'london', 'european']):
                location_keywords.extend(['UK markets', 'European business', 'British economy'])
            
            # Combine industry and location keywords
            combined_keywords = industry_keywords + location_keywords
            
            # If no specific keywords found, use generic high-value ones
            if not combined_keywords:
                combined_keywords = ['business innovation', 'market trends', 'industry insights']
            
            logger.info(f"🎯 Generated username-based keywords for @{username}: {combined_keywords}")
            return combined_keywords[:3]  # Return top 3
            
        except Exception as e:
            logger.error(f"❌ Error generating username-based keywords: {str(e)}")
            return ['business trends', 'industry insights', 'market analysis']
    
    def _enforce_keyword_diversity(self, keywords: List[str]) -> List[str]:
        """Enforce diversity by removing duplicates and similar terms."""
        if not keywords:
            return []
        
        diverse_keywords = []
        used_roots = set()
        
        for keyword in keywords:
            # Extract root terms to check for similarity
            keyword_lower = keyword.lower()
            root_terms = set()
            
            # Common root terms to check for similarity
            if 'ai' in keyword_lower or 'artificial intelligence' in keyword_lower:
                root_terms.add('ai')
            if 'tech' in keyword_lower or 'technology' in keyword_lower:
                root_terms.add('tech')
            if 'invest' in keyword_lower or 'fund' in keyword_lower:
                root_terms.add('investment')
            if 'stock' in keyword_lower or 'market' in keyword_lower:
                root_terms.add('market')
            if 'beauty' in keyword_lower or 'cosmetic' in keyword_lower:
                root_terms.add('beauty')
            if 'crypto' in keyword_lower or 'bitcoin' in keyword_lower:
                root_terms.add('crypto')
            
            # Check if this keyword is too similar to existing ones
            is_similar = bool(root_terms.intersection(used_roots))
            
            if not is_similar:
                diverse_keywords.append(keyword)
                used_roots.update(root_terms)
                logger.info(f"🎯 Diverse keyword accepted: '{keyword}'")
            else:
                logger.warning(f"⚠️ Keyword rejected for similarity: '{keyword}' (conflicts with: {root_terms.intersection(used_roots)})")
        
        return diverse_keywords
    
    def _generate_intelligent_fallback(self, hashtags: List[str], position: int, existing_keywords: List[str] = None) -> Optional[str]:
        """Generate intelligent NewsAPI-compatible fallback keyword."""
        if existing_keywords is None:
            existing_keywords = []
            
        if position < len(hashtags):
            hashtag = hashtags[position].lower()
            
            # Map hashtags to niche-specific NewsAPI terms
            hashtag_mappings = {
                'aiinvestment': 'AI investment',
                'techstocks': 'tech stocks', 
                'shortselling': 'short selling',
                'fintech': 'fintech stocks',
                'cryptocurrency': 'crypto investment',
                'stockmarket': 'stock market',
                'investment': 'tech investment',
                'beauty': 'beauty brands',
                'makeup': 'cosmetics industry',
                'skincare': 'skincare market',
                'fashion': 'fashion trends'
            }
            
            fallback = hashtag_mappings.get(hashtag, hashtag.replace('_', ' '))
            
            # Ensure it's not already used
            if fallback not in existing_keywords:
                return fallback
        
        # Generic fallbacks if needed
        generic_fallbacks = ['market news', 'industry trends', 'business updates']
        for fallback in generic_fallbacks:
            if fallback not in existing_keywords:
                return fallback
        
        return None
    
    def _create_emergency_news_items(self, username: str, platform: str, account_type: str) -> List[Dict]:
        """Create emergency news items when all else fails."""
        try:
            emergency_items = []
            
            # Platform-specific emergency templates
            emergency_templates = {
                'twitter': [
                    {'keyword': 'social media trends', 'title': 'Social Media Trends Shaping Digital Engagement', 'source': 'Social Media Insights'},
                    {'keyword': 'digital marketing', 'title': 'Digital Marketing Strategies for 2024', 'source': 'Marketing Intelligence'},
                    {'keyword': 'online business', 'title': 'Online Business Opportunities and Trends', 'source': 'Business Analysis'}
                ],
                'instagram': [
                    {'keyword': 'visual content', 'title': 'Visual Content Trends in Social Media', 'source': 'Content Intelligence'},
                    {'keyword': 'social media marketing', 'title': 'Social Media Marketing Best Practices', 'source': 'Marketing Insights'},
                    {'keyword': 'influencer insights', 'title': 'Influencer Marketing Trends and Strategies', 'source': 'Influencer Analysis'}
                ],
                'linkedin': [
                    {'keyword': 'professional networking', 'title': 'Professional Networking Strategies', 'source': 'Career Intelligence'},
                    {'keyword': 'business insights', 'title': 'Business Strategy and Market Insights', 'source': 'Business Intelligence'},
                    {'keyword': 'career development', 'title': 'Career Development and Growth Strategies', 'source': 'Career Analysis'}
                ]
            }
            
            # Get templates for platform, fallback to generic
            templates = emergency_templates.get(platform.lower(), [
                {'keyword': 'business news', 'title': 'Business and Technology Insights', 'source': 'Business Intelligence'},
                {'keyword': 'technology trends', 'title': 'Technology Trends and Innovations', 'source': 'Tech Analysis'},
                {'keyword': 'market updates', 'title': 'Market Trends and Strategic Insights', 'source': 'Market Research'}
            ])
            
            for i, template in enumerate(templates, 1):
                emergency_item = {
                    'keyword': template['keyword'],
                    'title': template['title'],
                    'description': f'Comprehensive insights into {template["keyword"]} and related trends for strategic decision-making.',
                    'timestamp': datetime.now().isoformat(),
                    'image_url': '',
                    'url': '',
                    'source': template['source'],
                    'is_fallback': True,
                    'fallback_position': i,
                    'fallback_type': 'emergency',
                    'username': username,
                    'platform': platform,
                    'account_type': account_type
                }
                emergency_items.append(emergency_item)
            
            logger.info(f"🚨 Created {len(emergency_items)} emergency news items for {username}")
            return emergency_items
            
        except Exception as e:
            logger.error(f"❌ Critical error creating emergency news for {username}: {e}")
            # Last resort - return minimal items
            return [
                {
                    'keyword': 'business news',
                    'title': 'Business and Technology Insights',
                    'description': 'Latest insights into business and technology trends.',
                    'timestamp': datetime.now().isoformat(),
                    'image_url': '',
                    'url': '',
                    'source': 'System',
                    'is_fallback': True,
                    'fallback_type': 'last_resort',
                    'username': username
                }
                for _ in range(3)
            ]
    
    def get_system_status(self):
        """Get status of the autonomous system."""
        return {
            "system": "AutonomousNews4USystem",
            "test_mode": self.test_mode,
            "processing_interval": self.processing_interval,
            "processed_accounts_count": len(self.processed_accounts),
            "r2_connection": bool(self.r2_storage),
            "news_module": bool(self.news_module),
            "newsapi_test": self.news_module.test_news_api_connection() if self.news_module else False
        }


def main():
    """Main entry point for autonomous system."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Autonomous News4U System')
    parser.add_argument('--test', action='store_true', help='Run in test mode (2 minute intervals)')
    parser.add_argument('--single', metavar=('PLATFORM', 'USERNAME'), nargs=2, 
                       help='Test single account (platform username)')
    parser.add_argument('--status', action='store_true', help='Show system status')
    
    args = parser.parse_args()
    
    try:
        # Initialize system
        system = AutonomousNews4USystem(test_mode=args.test)
        
        if args.status:
            # Show status
            status = system.get_system_status()
            print("🔍 Autonomous News4U System Status:")
            for key, value in status.items():
                print(f"  {key}: {value}")
        
        elif args.single:
            # Test single account
            platform, username = args.single
            system.test_single_account(platform, username)
        
        else:
            # Run autonomous loop
            system.run_autonomous_loop()
    
    except KeyboardInterrupt:
        logger.info("🛑 System stopped by user")
    except Exception as e:
        logger.error(f"❌ Critical system error: {e}")
        raise


if __name__ == "__main__":
    main()
