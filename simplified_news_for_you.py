"""
SIMPLIFIED NEWS FOR YOU MODULE - STREAMLINED HASHTAG-BASED NEWS CURATION
This module provides a clean, efficient replacement for the complex intelligent news system:
- Uses hashtags directly as keywords for 3 separate queries
- Fetches from NewsAPI.org with title, description, timestamp, and image URL
- No filtering, summarization, or domain intelligence
- Direct API calls with minimal processing
"""

import requests
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Set
import re
import google.generativeai as genai

logger = logging.getLogger(__name__)

class SimplifiedNewsForYouModule:
    """
    Simplified News For You module using direct hashtag-to-keyword mapping.
    Provides seamless replacement for IntelligentNewsForYouModule.
    """
    
    def __init__(self, config, ai_domain_intel=None, rag_implementation=None, vector_db=None, r2_storage=None):
        """Initialize with NewsAPI.org configuration."""
        # Use provided API key or default
        self.newsapi_key = config.get('NEWSAPI_KEY', 'a747734c8a9f41a4a6a6b98e3e66d9d2')
        self.base_url = "https://newsapi.org/v2/everything"
        
        # Store other components for compatibility (not used in simplified version)
        self.r2_storage = r2_storage
        
        # Initialize Gemini API for intelligent hashtag transformation
        self.gemini_config = config.get('GEMINI_CONFIG', {})
        self.gemini_api_key = self.gemini_config.get('api_key', 'AIzaSyBAX0Ifkf1l1-okLEx3mIFmCtJtsPOOHns')
        if self.gemini_api_key:
            genai.configure(api_key=self.gemini_api_key)
            self.gemini_model = genai.GenerativeModel(self.gemini_config.get('model', 'gemini-1.5-flash'))
            logger.info("🧠 Gemini API initialized for intelligent hashtag transformation")
        else:
            self.gemini_model = None
            logger.warning("⚠️ Gemini API not configured - falling back to basic hashtag processing")
        
        logger.info("🚀 SIMPLIFIED News For You Module initialized")
        logger.info(f"🔑 Using NewsAPI.org with key: {self.newsapi_key[:10]}...")
    
    def generate_news_for_account_sync(self, username: str, platform: str = "twitter", 
                                     account_type: str = "personal", posting_style: str = "casual",
                                     user_posts: List[Dict] = None, trending_hashtags: Optional[List[str]] = None) -> List[Dict]:
        """
        Generate simplified news using hashtags as keywords with seamless fallback system.
        Returns exactly 3 news items using intelligent keyword generation and fallback mechanisms.
        """
        try:
            logger.info(f"📰 Generating simplified News For You for @{username} on {platform}")
            
            # SEAMLESS FALLBACK SYSTEM - Always ensures keywords are available
            keywords = self._ensure_keywords_availability(username, platform, account_type, trending_hashtags)
            
            if not keywords:
                # Ultimate fallback - this should never happen, but if it does, we have backup
                logger.warning(f"⚠️ Critical fallback activated for @{username} - using emergency keywords")
                keywords = ['business news', 'technology trends', 'market updates']
            
            logger.info(f"🎯 Final keywords for @{username}: {keywords}")
            
            # Generate news items with seamless fallback
            news_results = self._generate_news_with_fallback(username, keywords)
            
            # Ensure we always have exactly 3 news items
            news_results = self._ensure_three_news_items(username, news_results, keywords)
            
            # Export news items with error handling
            self._export_news_items_safely(username, platform, news_results)
            
            logger.info(f"✅ Successfully generated {len(news_results)} news items for @{username}")
            return news_results
            
        except Exception as e:
            logger.error(f"❌ Critical error in news generation for @{username}: {str(e)}")
            # Emergency fallback - return basic news items to prevent system failure
            emergency_news = self._create_emergency_news_items(username)
            logger.info(f"🚨 Emergency fallback activated for @{username} - returning emergency news")
            return emergency_news
    
    def _ensure_keywords_availability(self, username: str, platform: str, account_type: str, 
                                    trending_hashtags: Optional[List[str]] = None) -> List[str]:
        """
        Seamlessly ensures keywords are always available through multiple fallback layers.
        This method never fails and always returns valid keywords.
        """
        try:
            # Layer 1: Try trending hashtags if available
            if trending_hashtags and isinstance(trending_hashtags, list) and len(trending_hashtags) > 0:
                try:
                    keywords = self._transform_hashtags_with_gemini(trending_hashtags, username, platform, account_type)
                    if keywords and len(keywords) >= 3:
                        logger.info(f"📌 Using trending hashtags for @{username}: {keywords[:3]}")
                        return keywords[:3]
                except Exception as e:
                    logger.warning(f"⚠️ Hashtag transformation failed for @{username}, using fallback: {e}")
            
            # Layer 2: Intelligent fallback keywords
            try:
                fallback_keywords = self._get_fallback_keywords(username, platform, account_type)
                if fallback_keywords and len(fallback_keywords) >= 3:
                    logger.info(f"🔄 Using intelligent fallback keywords for @{username}: {fallback_keywords[:3]}")
                    return fallback_keywords[:3]
            except Exception as e:
                logger.warning(f"⚠️ Intelligent fallback failed for @{username}, using basic fallback: {e}")
            
            # Layer 3: Basic platform-specific keywords
            try:
                basic_keywords = self._get_basic_platform_keywords(platform, account_type)
                if basic_keywords and len(basic_keywords) >= 3:
                    logger.info(f"🔧 Using basic platform keywords for @{username}: {basic_keywords[:3]}")
                    return basic_keywords[:3]
            except Exception as e:
                logger.warning(f"⚠️ Basic fallback failed for @{username}, using emergency keywords: {e}")
            
            # Layer 4: Emergency keywords (never fails)
            emergency_keywords = ['business news', 'technology trends', 'market updates']
            logger.info(f"🚨 Using emergency keywords for @{username}: {emergency_keywords}")
            return emergency_keywords
            
        except Exception as e:
            logger.error(f"❌ Critical error in keyword generation for @{username}: {e}")
            # Ultimate fallback - this should never fail
            return ['business news', 'technology trends', 'market updates']
    
    def _get_basic_platform_keywords(self, platform: str, account_type: str) -> List[str]:
        """Get basic platform keywords as a safety net."""
        try:
            # Simple, reliable keyword mappings
            platform_map = {
                'twitter': ['social media', 'digital marketing', 'online business'],
                'instagram': ['social media', 'visual content', 'digital marketing'],
                'facebook': ['social networking', 'community', 'digital engagement'],
                'linkedin': ['professional', 'business', 'career'],
                'tiktok': ['social media', 'content creation', 'digital trends'],
                'youtube': ['content creation', 'digital media', 'online video']
            }
            
            account_map = {
                'personal': ['personal development', 'social media', 'digital presence'],
                'business': ['business strategy', 'market trends', 'industry insights'],
                'influencer': ['content creation', 'social media', 'digital influence'],
                'creator': ['content creation', 'digital art', 'creative trends'],
                'professional': ['professional development', 'business insights', 'career growth'],
                'brand': ['brand strategy', 'marketing trends', 'business growth']
            }
            
            platform_keywords = platform_map.get(platform.lower(), ['social media', 'digital trends', 'online business'])
            account_keywords = account_map.get(account_type.lower(), ['digital strategy', 'online presence', 'business growth'])
            
            # Combine and return
            combined = platform_keywords + account_keywords
            return list(dict.fromkeys(combined))[:4]  # Remove duplicates, take top 4
            
        except Exception as e:
            logger.error(f"❌ Error in basic platform keywords: {e}")
            return ['social media', 'digital trends', 'business news']
    
    def _generate_news_with_fallback(self, username: str, keywords: List[str]) -> List[Dict]:
        """
        Generate news items with seamless fallback - never fails to return news.
        """
        news_results = []
        
        try:
            # Try to get real news from NewsAPI
            for keyword in keywords:
                if len(news_results) >= 3:
                    break
                
                try:
                    news_item = self.get_news_for_keyword(keyword)
                    if news_item and self._is_valid_news_item(news_item):
                        news_results.append(news_item)
                        logger.info(f"✅ Generated real news for '{keyword}'")
                    else:
                        logger.warning(f"⚠️ Invalid news item for '{keyword}', creating fallback")
                        fallback_item = self._create_fallback_news_item(keyword, len(news_results) + 1)
                        news_results.append(fallback_item)
                except Exception as e:
                    logger.warning(f"⚠️ News generation failed for '{keyword}', creating fallback: {e}")
                    fallback_item = self._create_fallback_news_item(keyword, len(news_results) + 1)
                    news_results.append(fallback_item)
            
            # If we still don't have enough, create more fallbacks
            while len(news_results) < 3:
                fallback_item = self._create_fallback_news_item('general business', len(news_results) + 1)
                news_results.append(fallback_item)
                logger.info(f"📰 Added fallback news item #{len(news_results)}")
            
        except Exception as e:
            logger.error(f"❌ Critical error in news generation for @{username}: {e}")
            # Emergency fallback - create all fallback items
            for i in range(3):
                fallback_item = self._create_fallback_news_item('emergency', i + 1)
                news_results.append(fallback_item)
        
        return news_results
    
    def _ensure_three_news_items(self, username: str, news_results: List[Dict], keywords: List[str]) -> List[Dict]:
        """Ensure exactly 3 news items are always returned."""
        try:
            if len(news_results) >= 3:
                return news_results[:3]
            
            # Create additional fallback items if needed
            while len(news_results) < 3:
                position = len(news_results) + 1
                fallback_item = self._create_fallback_news_item('completion', position)
                news_results.append(fallback_item)
                logger.info(f"📰 Added completion fallback item #{position} for @{username}")
            
            return news_results[:3]
            
        except Exception as e:
            logger.error(f"❌ Error ensuring three news items for @{username}: {e}")
            # Emergency fallback
            return [self._create_fallback_news_item('emergency', i + 1) for i in range(3)]
    
    def _export_news_items_safely(self, username: str, platform: str, news_results: List[Dict]):
        """Export news items with comprehensive error handling - never fails."""
        try:
            if not self.r2_storage:
                logger.warning(f"⚠️ R2 storage not available for @{username}, skipping export")
                return
            
            exported_count = 0
            
            for i, news_item in enumerate(news_results, 1):
                try:
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    filename = f"news_{timestamp}_{username}_{i}.json"
                    r2_key = f"news_for_you/{platform}/{username}/{filename}"
                    
                    # Create export data
                    export_data = {
                        "username": username,
                        "platform": platform,
                        "generated_at": datetime.now().isoformat(),
                        "news_item": news_item,
                        "autonomous_system": True,
                        "system_version": "1.0",
                        "fallback_used": news_item.get('is_fallback', False)
                    }
                    
                    # Upload to R2
                    success = self.r2_storage.put_object(
                        key=r2_key,
                        content=json.dumps(export_data, indent=2),
                        bucket="tasks"
                    )
                    
                    if success:
                        exported_count += 1
                        logger.info(f"📤 Exported news item #{i} for @{username}: {filename}")
                    else:
                        logger.warning(f"⚠️ Failed to export news item #{i} for @{username}")
                        
                except Exception as e:
                    logger.warning(f"⚠️ Export failed for news item #{i} for @{username}: {e}")
                    # Continue with next item - don't fail the entire process
            
            logger.info(f"📤 Successfully exported {exported_count}/{len(news_results)} news items for @{username}")
            
        except Exception as e:
            logger.error(f"❌ Critical export error for @{username}: {e}")
            # Export failure should not stop the news generation process
            logger.info(f"🔄 Continuing without export for @{username}")
    
    def _is_valid_news_item(self, news_item: Dict) -> bool:
        """Check if news item is valid and complete."""
        try:
            required_fields = ['title', 'description', 'keyword']
            
            for field in required_fields:
                if not news_item.get(field):
                    return False
            
            # Check content quality
            title = news_item.get('title', '')
            description = news_item.get('description', '')
            
            if len(title) < 5 or len(description) < 10:
                return False
            
            return True
            
        except Exception:
            return False
    
    def _create_fallback_news_item(self, keyword: str, position: int) -> Dict:
        """Create a high-quality fallback news item."""
        try:
            # Enhanced fallback templates
            templates = [
                {
                    'keyword': keyword,
                    'title': f'Emerging Trends in {keyword.title()} for 2024',
                    'description': f'Discover the latest developments and opportunities in {keyword} that are shaping the future of business and technology.',
                    'source': 'Industry Insights'
                },
                {
                    'keyword': keyword,
                    'title': f'Strategic Insights: {keyword.title()} Market Analysis',
                    'description': f'Comprehensive analysis of current {keyword} trends, market dynamics, and strategic opportunities for growth and innovation.',
                    'source': 'Market Intelligence'
                },
                {
                    'keyword': keyword,
                    'title': f'Innovation Spotlight: {keyword.title()} Breakthroughs',
                    'description': f'Explore cutting-edge innovations and breakthroughs in {keyword} that are revolutionizing industries and creating new opportunities.',
                    'source': 'Innovation Report'
                }
            ]
            
            template = templates[(position - 1) % len(templates)]
            
            fallback_news = {
                'keyword': template['keyword'],
                'title': template['title'],
                'description': template['description'],
                'timestamp': datetime.now().isoformat(),
                'image_url': '',
                'url': '',
                'source': template['source'],
                'is_fallback': True,
                'fallback_position': position,
                'fallback_type': 'seamless'
            }
            
            return fallback_news
            
        except Exception as e:
            logger.error(f"❌ Error creating fallback news item: {e}")
            # Ultimate fallback template
            return {
                'keyword': keyword,
                'title': f'Industry Insights: {keyword.title()} Trends',
                'description': f'Comprehensive analysis of {keyword} trends and opportunities in the current market landscape.',
                'timestamp': datetime.now().isoformat(),
                'image_url': '',
                'url': '',
                'source': 'Industry Analysis',
                'is_fallback': True,
                'fallback_position': position,
                'fallback_type': 'emergency'
            }
    
    def _create_emergency_news_items(self, username: str) -> List[Dict]:
        """Create emergency news items when all else fails."""
        try:
            emergency_items = []
            
            emergency_templates = [
                {
                    'keyword': 'business innovation',
                    'title': 'Business Innovation Trends Shaping 2024',
                    'description': 'Discover the latest innovations driving business transformation and growth across industries.',
                    'source': 'Business Intelligence'
                },
                {
                    'keyword': 'technology trends',
                    'title': 'Technology Breakthroughs Revolutionizing Industries',
                    'description': 'Explore cutting-edge technologies that are reshaping how businesses operate and compete.',
                    'source': 'Tech Analysis'
                },
                {
                    'keyword': 'market insights',
                    'title': 'Global Market Dynamics and Strategic Opportunities',
                    'description': 'Comprehensive analysis of market trends and strategic insights for informed decision-making.',
                    'source': 'Market Research'
                }
            ]
            
            for i, template in enumerate(emergency_templates, 1):
                emergency_item = {
                    'keyword': template['keyword'],
                    'title': template['title'],
                    'description': template['description'],
                    'timestamp': datetime.now().isoformat(),
                    'image_url': '',
                    'url': '',
                    'source': template['source'],
                    'is_fallback': True,
                    'fallback_position': i,
                    'fallback_type': 'emergency',
                    'username': username
                }
                emergency_items.append(emergency_item)
            
            logger.info(f"🚨 Created {len(emergency_items)} emergency news items for @{username}")
            return emergency_items
            
        except Exception as e:
            logger.error(f"❌ Critical error creating emergency news for @{username}: {e}")
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
                    'fallback_type': 'last_resort'
                }
                for _ in range(3)
            ]
    
    def _transform_hashtags_with_gemini(self, hashtags: List[str], username: str, platform: str, account_type: str) -> List[str]:
        """Transform hashtags into 3 highly relevant keywords using Gemini AI intelligence."""
        if not self.gemini_model:
            logger.warning("⚠️ Gemini not available - falling back to basic transformation")
            return self._transform_hashtags_to_keywords_fallback(hashtags)
        
        try:
            # Clean hashtags
            clean_hashtags = []
            for tag in hashtags:
                clean_tag = str(tag).replace('#', '').strip()
                if clean_tag:
                    clean_hashtags.append(clean_tag)
            
            if not clean_hashtags:
                raise ValueError("No valid hashtags to process")
            
            # Take up to 20 hashtags as specified
            hashtags_to_process = clean_hashtags[:20]
            
            # Create intelligent prompt for Gemini
            prompt = self._create_hashtag_transformation_prompt(hashtags_to_process, username, platform, account_type)
            
            logger.info(f"🧠 Sending {len(hashtags_to_process)} hashtags to Gemini for intelligent transformation")
            
            # Call Gemini API
            response = self.gemini_model.generate_content(prompt)
            
            if response and response.text:
                keywords = self._parse_gemini_keywords_response(response.text)
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
                    
                    logger.info(f"✅ Refined {len(final_keywords)} hashtags to searchable keywords: {final_keywords}")
                    logger.info(f"🌍 Detected country for localized news: {detected_country}")
                    return final_keywords
                else:
                    logger.warning("⚠️ Gemini returned invalid keywords format")
            else:
                logger.warning("⚠️ Gemini returned empty response")
        
        except Exception as e:
            logger.error(f"❌ Gemini hashtag transformation failed: {str(e)}")
        
        # Fallback to basic transformation
        logger.info("🔄 Falling back to basic hashtag transformation")
        # Set default country for fallback
        self._detected_country = 'us'
        return self._transform_hashtags_to_keywords_fallback(hashtags)
    
    def _get_fallback_keywords(self, username: str, platform: str, account_type: str) -> List[str]:
        """
        Generate intelligent fallback keywords when trending hashtags are not available.
        Provides 3-4 relevant keywords based on platform, account type, and common interests.
        """
        try:
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
    
    def _create_fallback_news(self, position: int) -> Dict:
        """Create a fallback news item when NewsAPI doesn't return enough results."""
        try:
            # High-quality fallback news templates
            fallback_templates = [
                {
                    'keyword': 'business innovation',
                    'title': 'Emerging Business Trends Reshaping Industries in 2024',
                    'description': 'Discover the latest innovations driving business transformation across sectors, from AI integration to sustainable practices.',
                    'timestamp': datetime.now().isoformat(),
                    'image_url': '',
                    'url': '',
                    'source': 'Business Insights'
                },
                {
                    'keyword': 'technology trends',
                    'title': 'Breakthrough Technologies Revolutionizing Digital Landscape',
                    'description': 'Explore cutting-edge technological advancements that are reshaping how businesses operate and compete in the digital age.',
                    'timestamp': datetime.now().isoformat(),
                    'image_url': '',
                    'url': '',
                    'source': 'Tech Analysis'
                },
                {
                    'keyword': 'market updates',
                    'title': 'Global Market Dynamics: Key Trends and Opportunities',
                    'description': 'Comprehensive analysis of current market conditions, emerging opportunities, and strategic insights for informed decision-making.',
                    'timestamp': datetime.now().isoformat(),
                    'image_url': '',
                    'url': '',
                    'source': 'Market Intelligence'
                }
            ]
            
            # Use position to select appropriate template (1-indexed)
            template_index = (position - 1) % len(fallback_templates)
            template = fallback_templates[template_index]
            
            # Create fallback news item
            fallback_news = {
                'keyword': template['keyword'],
                'title': template['title'],
                'description': template['description'],
                'timestamp': template['timestamp'],
                'image_url': template['image_url'],
                'url': template['url'],
                'source': template['source'],
                'is_fallback': True,
                'fallback_position': position
            }
            
            logger.info(f"📰 Created fallback news item #{position}: {template['keyword']}")
            return fallback_news
            
        except Exception as e:
            logger.error(f"❌ Error creating fallback news item #{position}: {str(e)}")
            # Ultimate fallback
            return {
                'keyword': 'industry insights',
                'title': 'Industry Trends and Strategic Insights',
                'description': 'Comprehensive analysis of current industry trends and strategic insights for business growth and innovation.',
                'timestamp': datetime.now().isoformat(),
                'image_url': '',
                'url': '',
                'source': 'Industry Analysis',
                'is_fallback': True,
                'fallback_position': position
            }
    
    def _create_hashtag_transformation_prompt(self, hashtags: List[str], username: str, platform: str, account_type: str) -> str:
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
    
    def _parse_gemini_keywords_response(self, response_text: str) -> List[str]:
        """Parse Gemini's hashtag separation response."""
        try:
            # Try to find JSON in the response
            response_text = response_text.strip()
            
            # Handle cases where response might have markdown formatting
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
                    logger.info(f"🎯 Gemini separated {len(refined_hashtags)} hashtags into searchable phrases")
                    return refined_hashtags
                else:
                    logger.warning("⚠️ No valid refined hashtags found in Gemini response")
        
        except json.JSONDecodeError as e:
            logger.error(f"❌ Failed to parse Gemini JSON response: {str(e)}")
        except Exception as e:
            logger.error(f"❌ Error parsing Gemini response: {str(e)}")
        
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
    
    def _validate_newsapi_keywords(self, keywords: List[str], hashtags: List[str]) -> List[str]:
        """Validate keywords for NewsAPI compatibility and optimize for article availability."""
        validated_keywords = []
        
        for keyword in keywords:
            # Clean and optimize keyword
            optimized_keyword = self._optimize_keyword_for_newsapi(keyword)
            
            if optimized_keyword:
                validated_keywords.append(optimized_keyword)
                logger.info(f"✅ Validated keyword: '{keyword}' -> '{optimized_keyword}'")
        
        return validated_keywords
    
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
    
    def _optimize_keyword_for_newsapi(self, keyword: str) -> str:
        """Preserve Gemini's intelligent compound keywords while cleaning only when necessary."""
        # Remove quotes and clean
        keyword = keyword.strip().strip('"').strip("'")
        
        # Check if keyword is already well-formed (2-3 words, niche-specific)
        words = keyword.split()
        if len(words) <= 3 and len(keyword) <= 25:
            # Keyword is already good - preserve Gemini's intelligence
            logger.info(f"🎯 Preserving Gemini's intelligent keyword: '{keyword}'")
            return keyword
        
        # Only optimize if keyword is too long or poorly formed
        if len(words) > 3 or len(keyword) > 25:
            # NewsAPI optimization for overly complex terms only
            optimizations = {
                # Only simplify overly complex phrases
                'AI-driven Fintech investments strategy': 'AI investment',
                'Artificial Intelligence Stock Market analysis trends': 'AI stocks',
                'Short Selling Big Tech companies strategy': 'short selling',
                'cryptocurrency investment market analysis': 'crypto investment',
                'venture capital funding rounds analysis': 'venture capital',
                'IPO market performance analysis': 'tech IPO',
                'earnings report financial analysis': 'tech earnings',
                'comprehensive market analysis strategy': 'market analysis'
            }
            
            # Apply optimizations only for overly complex terms
            keyword_lower = keyword.lower()
            for long_term, short_term in optimizations.items():
                if long_term in keyword_lower:
                    return short_term
        
        # Default: return original keyword (trust Gemini's intelligence)
        return keyword
    
    def _generate_intelligent_fallback(self, hashtags: List[str], position: int, existing_keywords: List[str] = None) -> Optional[str]:
        """Generate intelligent NewsAPI-compatible fallback keyword."""
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
                'startup': 'tech startup',
                'beauty': 'beauty brands',
                'makeup': 'makeup brands',
                'skincare': 'skincare brands',
                'fashion': 'luxury fashion'
            }
            
            return hashtag_mappings.get(hashtag, hashtag)
        return None
    
    def _transform_hashtags_to_keywords_fallback(self, hashtags: List[str]) -> List[str]:
        """Fallback method: Transform hashtags into keywords by splitting compound words and removing duplicates."""
        keywords = []
        
        for tag in hashtags:
            # Remove # and clean the tag
            clean_tag = str(tag).replace('#', '').strip()
            if not clean_tag:
                continue
            
            # Split compound words into separate keywords
            split_words = self._split_compound_words(clean_tag)
            keywords.extend(split_words)
        
        # Remove duplicates while preserving order and return top 3
        unique_keywords = list(dict.fromkeys(keywords))
        return unique_keywords[:3]
    
    def _split_compound_words(self, text: str) -> List[str]:
        """Split compound words into separate keywords using multiple strategies."""
        if not text:
            return []
        
        import re
        
        # Strategy 1: camelCase splitting
        camel_words = re.findall(r'[A-Z]?[a-z]+|[A-Z]+(?=[A-Z][a-z]|\b)', text)
        
        # Strategy 2: common compound word patterns
        # Split on common boundaries: beauty+hack, makeup+tutorial, etc.
        compound_patterns = [
            r'(beauty|makeup|fashion|skin|hair|nail|cosmetic|product|tutorial|hack|tip|trick|review|guide)',
            r'(pakistani|indian|asian|american|european|arabic|desi)',
            r'(collection|look|style|trend|outfit|accessory|jewelry|bag|shoe|dress)',
            r'(artist|blogger|influencer|creator|expert|professional|guru)',
            r'(flawless|perfect|natural|organic|vegan|cruelty|free|clean|green)',
            r'(huda|mac|nars|fenty|dior|chanel|gucci|prada|louis|vuitton)',
            r'(eid|ramadan|diwali|christmas|halloween|wedding|bridal|party|event)'
        ]
        
        all_words = []
        
        # Add camelCase words
        all_words.extend([word.lower() for word in camel_words if word and len(word) > 2])
        
        # Add pattern matches
        for pattern in compound_patterns:
            matches = re.findall(pattern, text.lower())
            all_words.extend(matches)
        
        # Strategy 3: Split on common boundaries if no other splits found
        if len(all_words) <= 1:
            # Try splitting on common boundaries
            boundaries = [
                r'(beauty)(hack|tip|trick|tutorial|review|guide)',
                r'(makeup)(tutorial|tip|hack|review|guide|look|style)',
                r'(pakistani)(makeup|fashion|style|beauty|food|culture)',
                r'(flawless)(skin|face|makeup|beauty)',
                r'(huda)(beauty|makeup|cosmetics)',
                r'(eid)(collection|look|outfit|style|makeup)'
            ]
            
            for boundary in boundaries:
                matches = re.findall(boundary, text.lower())
                if matches:
                    for match in matches:
                        if isinstance(match, tuple):
                            all_words.extend(list(match))
                        else:
                            all_words.append(match)
        
        # Remove duplicates while preserving order
        seen = set()
        result = []
        for word in all_words:
            if word and len(word) > 2 and word not in seen:
                seen.add(word)
                result.append(word)
        
        # If no splits found, return original as fallback
        if not result:
            return [text.lower()]
        
        return result
    
    def _extract_hashtags_as_keywords(self, user_posts: List[Dict], username: str, platform: str) -> List[str]:
        """Extract hashtags ONLY from recommendation.trending_hashtags in content_plan.json."""
        logger.info(f"🔍 Extracting trending hashtags from recommendation section for @{username}")
        
        # ONLY use trending hashtags from recommendation section - no fallbacks
        hashtags = self._get_recommendation_trending_hashtags(username, platform)
        
        if not hashtags:
            # Critical error - pipeline should not proceed without recommendation hashtags
            raise ValueError(f"❌ CRITICAL: No trending hashtags found in recommendation section for @{username}. " +
                           "Pipeline cannot proceed without recommendation hashtags. " +
                           "Ensure recommendation generation completes before news module.")
        
        # Apply camelCase transformation to hashtags
        keywords = self._transform_hashtags_to_keywords(hashtags)
        
        logger.info(f"✅ Successfully extracted and transformed {len(keywords)} keywords for @{username}: {keywords[:3]}")
        return keywords
    
    def _get_recommendation_trending_hashtags(self, username: str, platform: str) -> List[str]:
        """Get trending hashtags from recommendation.trending_hashtags in content_plan.json."""
        try:
            # Read from content plan file
            with open('/home/komail/Miners-1/content_plan.json', 'r') as f:
                content_plan = json.load(f)
                
            # Extract trending hashtags from recommendation section
            recommendation = content_plan.get('recommendation', {})
            trending_hashtags = recommendation.get('trending_hashtags', [])
            
            if trending_hashtags:
                # Clean hashtags (remove # if present)
                cleaned_hashtags = []
                for tag in trending_hashtags:
                    clean_tag = tag.replace('#', '').strip()
                    if clean_tag:
                        cleaned_hashtags.append(clean_tag)
                
                logger.info(f"📥 Found {len(cleaned_hashtags)} trending hashtags from recommendation section")
                return cleaned_hashtags
            else:
                logger.error(f"❌ No trending_hashtags found in recommendation section for @{username}")
                
        except FileNotFoundError:
            logger.error(f"❌ content_plan.json not found - recommendation must be generated first")
        except json.JSONDecodeError as e:
            logger.error(f"❌ Invalid JSON in content_plan.json: {str(e)}")
        except Exception as e:
            logger.error(f"❌ Error extracting recommendation trending hashtags: {str(e)}")
        
        return []
    

    
    def get_news_for_keyword(self, keyword: str) -> Optional[Dict]:
        """Get news article for a specific keyword using NewsAPI.org with enhanced parameters."""
        try:
            # Get detected country or default to US
            country = getattr(self, '_detected_country', 'us')
            
            # Construct NewsAPI.org URL
            url = f"https://newsapi.org/v2/everything"
            
            params = {
                'q': keyword,
                'apiKey': self.newsapi_key,
                'language': 'en',
                'sortBy': 'relevancy',
                'pageSize': 1,
                'searchIn': 'title',  # Focus on headlines for better relevancy
                'country': country if country != 'us' else None  # Only add country if not US (default)
            }
            
            # Remove None values
            params = {k: v for k, v in params.items() if v is not None}
            
            logger.info(f"🔍 Fetching news for keyword: '{keyword}' (country: {country.upper()}, searchIn: title)")
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('status') == 'ok' and data.get('articles'):
                article = data['articles'][0]
                
                # Extract required fields
                news_item = {
                    'keyword': keyword,
                    'title': article.get('title', ''),
                    'description': article.get('description', ''),
                    'timestamp': article.get('publishedAt', ''),
                    'image_url': article.get('urlToImage', ''),
                    'url': article.get('url', ''),
                    'source': article.get('source', {}).get('name', '')
                }
                
                logger.info(f"✅ Found localized news for '{keyword}': {news_item['title'][:50]}...")
                return news_item
            else:
                logger.warning(f"⚠️ No articles found for keyword: '{keyword}' with enhanced parameters")
                
                # Fallback: try without country restriction and searchIn parameter
                fallback_params = {
                    'q': keyword,
                    'apiKey': self.newsapi_key,
                    'language': 'en',
                    'sortBy': 'relevancy',
                    'pageSize': 1
                }
                
                logger.info(f"🔄 Trying fallback search for '{keyword}' without restrictions")
                fallback_response = requests.get(url, params=fallback_params, timeout=10)
                fallback_response.raise_for_status()
                fallback_data = fallback_response.json()
                
                if fallback_data.get('status') == 'ok' and fallback_data.get('articles'):
                    article = fallback_data['articles'][0]
                    news_item = {
                        'keyword': keyword,
                        'title': article.get('title', ''),
                        'description': article.get('description', ''),
                        'timestamp': article.get('publishedAt', ''),
                        'image_url': article.get('urlToImage', ''),
                        'url': article.get('url', ''),
                        'source': article.get('source', {}).get('name', '')
                    }
                    logger.info(f"✅ Found fallback news for '{keyword}': {news_item['title'][:50]}...")
                    return news_item
                
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ NewsAPI request failed for '{keyword}': {str(e)}")
            return None
        except Exception as e:
            logger.error(f"❌ Error fetching news for '{keyword}': {str(e)}")
            return None
    
    def _is_valid_article(self, article: Dict) -> bool:
        """Check if article has required fields and good quality."""
        required_fields = ['title', 'description', 'publishedAt']
        
        # Check for required fields
        for field in required_fields:
            if not article.get(field):
                return False
        
        # Check for meaningful content
        title = article.get('title', '')
        description = article.get('description', '')
        
        if len(title) < 10 or len(description) < 20:
            return False
        
        # Avoid removed/deleted articles
        if '[Removed]' in title or '[Removed]' in description:
            return False
        
        return True
    
    def _format_news_item(self, article: Dict, keyword: str, query_number: int) -> Dict:
        """Format a news article into our required structure."""
        return {
            'query_number': query_number,
            'keyword': keyword,
            'title': article.get('title', '').strip(),
            'description': article.get('description', '').strip(),
            'timestamp': article.get('publishedAt', ''),
            'image_url': article.get('urlToImage', ''),
            'source_url': article.get('url', ''),
            'source': article.get('source', {}).get('name', 'Unknown'),
            'fetched_at': datetime.now().isoformat(),
            'author': article.get('author', '')
        }
    

    

    
    def _create_error_response(self, username: str, platform: str) -> List[Dict]:
        """Return empty list when hashtags are not available."""
        logger.error(f"❌ Cannot generate news without trending hashtags for @{username} on {platform}")
        return []
    
    # Compatibility methods for existing integration
    def test_news_api_connection(self):
        """Test the NewsAPI connection."""
        try:
            params = {
                'q': 'test',
                'pageSize': 1,
                'apiKey': self.newsapi_key
            }
            
            response = requests.get(self.base_url, params=params, timeout=5)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('status') == 'ok':
                logger.info("✅ NewsAPI connection test successful")
                return True
            else:
                logger.error(f"❌ NewsAPI returned error: {data.get('message', 'Unknown error')}")
                return False
                
        except Exception as e:
            logger.error(f"❌ NewsAPI connection test failed: {str(e)}")
            return False
    
    def get_news_system_status(self):
        """Get status of the simplified news system."""
        status = {
            'module': 'SimplifiedNewsForYouModule',
            'api': 'NewsAPI.org',
            'api_key_configured': bool(self.newsapi_key),
            'connection_test': self.test_news_api_connection(),
            'features': [
                'Hashtag-based keyword extraction',
                'Direct API queries (no filtering)',
                'Title, description, timestamp, image URL',
                '3 news items per request'
            ]
        }
        
        return status


# Test functions removed for production use
