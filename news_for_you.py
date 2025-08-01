"""
Advanced News For You Module - Elite News Curation System
Delivers highly relevant, breaking news tailored to each account's domain and interests.

This module combines:
- News API for real-time data
- AI Domain Intelligence for precise niche identification  
- RAG Implementation for contextual relevance
- Advanced filtering algorithms for quality assurance
"""

import requests
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import re
from collections import defaultdict
import hashlib

logger = logging.getLogger(__name__)

class NewsForYouModule:
    """
    Elite news curation system that delivers precisely targeted, 
    high-quality news content for any account across any platform.
    """
    
    def __init__(self, config, ai_domain_intel, rag_implementation, vector_db):
        """Initialize the News For You module with advanced components."""
        self.api_key = config.get('NEWSDATA_API_KEY')
        self.ai_domain_intel = ai_domain_intel
        self.rag = rag_implementation
        self.vector_db = vector_db
        
        # News API configuration
        self.base_url = "https://newsdata.io/api/1/news"
        self.max_news_per_request = 10  # Reduced from 50 to 10
        self.max_total_news = 30  # Reduced from 100 to 30
        
        # Advanced filtering configuration
        self.quality_threshold = 0.75
        self.relevance_threshold = 0.80
        self.breaking_news_weight = 2.0
        self.trending_boost = 1.5
        
        # Domain-specific news categories mapping
        self.domain_categories = {
            'tech_innovation': ['technology', 'science', 'business'],
            'business_corporate': ['business', 'economics', 'finance'],
            'health_wellness': ['health', 'lifestyle', 'science'],
            'fashion_beauty': ['lifestyle', 'entertainment', 'business'],
            'food_culinary': ['lifestyle', 'health', 'business'],
            'fitness_sports': ['sports', 'health', 'lifestyle'],
            'education_learning': ['education', 'science', 'technology'],
            'entertainment_media': ['entertainment', 'technology', 'business'],
            'travel_lifestyle': ['lifestyle', 'travel', 'business'],
            'finance_investing': ['business', 'economics', 'finance'],
            'gaming_esports': ['technology', 'entertainment', 'sports'],
            'automotive': ['technology', 'business', 'lifestyle'],
            'real_estate': ['business', 'economics', 'lifestyle'],
            'environmental': ['environment', 'science', 'politics'],
            'politics_social': ['politics', 'world', 'domestic']
        }
        
        logger.info("🚀 Elite News For You Module initialized")
    
    async def generate_news_for_account(self, username: str, platform: str, 
                                      account_type: str, posting_style: str = None,
                                      user_posts: List[Dict] = None) -> Dict:
        """
        Generate highly targeted news content for a specific account.
        
        This is the main entry point that orchestrates the entire news curation process.
        """
        try:
            logger.info(f"🎯 Generating elite news curation for @{username} on {platform}")
            
            # Step 1: Intelligent Domain Detection
            domain_profile = self._analyze_account_domain_sync(username, platform, 
                                                              account_type, user_posts)
            
            # Step 2: Fetch Today's Trending News
            raw_news = self._fetch_todays_trending_news_sync(domain_profile)
            
            # Step 3: Advanced Multi-Layer Filtering
            filtered_news = self._apply_advanced_filtering_sync(raw_news, domain_profile, username)
            
            # Step 4: RAG-Enhanced Relevance Scoring
            scored_news = self._score_news_relevance_sync(filtered_news, domain_profile, username)
            
            # Step 5: Final Curation & Quality Assurance
            final_news = self._curate_final_selection_sync(scored_news, domain_profile)
            
            # Step 6: Generate Premium News Summary
            news_summary = self._generate_premium_summary_sync(final_news, username, platform)
            
            logger.info(f"✅ Elite news curation complete: {len(final_news)} premium stories selected")
            
            return {
                'username': username,
                'platform': platform,
                'generated_at': datetime.now().isoformat(),
                'domain_profile': domain_profile,
                'curated_news': final_news,
                'premium_summary': news_summary,
                'curation_metadata': {
                    'total_analyzed': len(raw_news),
                    'post_filtering': len(filtered_news),
                    'final_selection': len(final_news),
                    'quality_score': self._calculate_overall_quality_score(final_news)
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Elite news curation failed for @{username}: {str(e)}")
            # Return emergency fallback
            return self._generate_emergency_news_fallback_sync(username, platform, account_type)
    
    def generate_news_for_account_sync(self, username: str, platform: str, 
                                     account_type: str, posting_style: str, 
                                     user_posts: List[Dict] = None) -> Dict:
        """
        Synchronous version of generate_news_for_account for main system integration.
        Elite news curation that works in synchronous environments.
        """
        return self.generate_news_for_account_async_wrapper(username, platform, account_type, posting_style, user_posts)
    
    def generate_news_for_account_async_wrapper(self, username: str, platform: str, 
                                              account_type: str, posting_style: str, 
                                              user_posts: List[Dict] = None) -> Dict:
        """
        Wrapper to run async version synchronously using the already implemented sync methods.
        This directly uses sync methods to avoid async complexity.
        """
        try:
            logger.info(f"🚀 Generating elite news curation for @{username} on {platform}")
            
            # Step 1: Analyze account domain (sync)
            domain_profile = self._analyze_account_domain_sync(username, platform, 
                                                             account_type, user_posts)
            
            # Step 2: Fetch today's trending news (sync)
            raw_news = self._fetch_todays_trending_news_sync(domain_profile)
            
            # Step 3: Apply advanced filtering (sync)
            filtered_news = self._apply_advanced_filtering_sync(raw_news, domain_profile, username)
            
            # Step 4: Score news relevance using RAG (sync)
            scored_news = self._score_news_relevance_sync(filtered_news, domain_profile, username)
            
            # Step 5: Curate final selection (sync)
            final_news = self._curate_final_selection_sync(scored_news, domain_profile)
            
            # Step 6: Generate premium summaries (sync)
            news_summary = self._generate_premium_summary_sync(final_news, username, platform)
            
            # Return comprehensive result
            return {
                'username': username,
                'platform': platform,
                'generated_at': datetime.now().isoformat(),
                'domain_profile': domain_profile,
                'curated_news': final_news,
                'premium_summary': news_summary,
                'curation_metadata': {
                    'total_fetched': len(raw_news),
                    'after_filtering': len(filtered_news),
                    'final_selection': len(final_news),
                    'quality_score': self._calculate_overall_quality_score(final_news)
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Elite news curation failed for @{username}: {str(e)}")
            # Return emergency fallback
            return self._generate_emergency_news_fallback_sync(username, platform, account_type)
    
    async def _analyze_account_domain(self, username: str, platform: str, 
                                    account_type: str, user_posts: List[Dict] = None) -> Dict:
        """
        Advanced domain analysis using AI intelligence and post content analysis.
        """
        try:
            logger.info(f"🔍 Analyzing domain profile for @{username}")
            
            # Primary domain detection using AI Domain Intelligence
            domain_classification = self.ai_domain_intel.analyze_domain_intelligence(username)
            
            # Enhanced analysis using user posts if available
            content_themes = []
            if user_posts and len(user_posts) > 0:
                content_themes = await self._extract_content_themes(user_posts)
            
            # Determine news categories and keywords
            primary_domain = domain_classification.get('domain', 'general')
            categories = self.domain_categories.get(primary_domain, ['general', 'business'])
            
            # Generate domain-specific keywords
            keywords = await self._generate_domain_keywords(primary_domain, content_themes, username)
            
            domain_profile = {
                'primary_domain': primary_domain,
                'confidence': domain_classification.get('confidence', 0.8),
                'categories': categories,
                'keywords': keywords,
                'content_themes': content_themes,
                'account_type': account_type,
                'targeting_focus': self._determine_targeting_focus(primary_domain, account_type)
            }
            
            logger.info(f"✅ Domain profile: {primary_domain} (confidence: {domain_profile['confidence']:.2f})")
            return domain_profile
            
        except Exception as e:
            logger.error(f"❌ Domain analysis failed: {str(e)}")
            # Fallback to basic classification
            return {
                'primary_domain': 'general',
                'confidence': 0.6,
                'categories': ['general', 'business'],
                'keywords': [username.lower()],
                'content_themes': [],
                'account_type': account_type,
                'targeting_focus': 'general_interest'
            }
    
    async def _fetch_todays_trending_news(self, domain_profile: Dict) -> List[Dict]:
        """
        Fetch today's trending news from News API with intelligent filtering.
        """
        try:
            logger.info("📰 Fetching today's trending news from News API")
            
            # Prepare API parameters
            today = datetime.now().date()
            yesterday = today - timedelta(days=1)
            
            all_news = []
            
            # Fetch news for each relevant category
            for category in domain_profile['categories']:
                try:
                    params = {
                        'apikey': self.api_key,
                        'category': category,
                        'language': 'en',
                        'from_date': yesterday.isoformat(),
                        'to_date': today.isoformat(),
                        'size': self.max_news_per_request,
                        'prioritydomain': 'top'  # High-quality sources only
                    }
                    
                    # Add domain-specific keywords
                    if domain_profile['keywords']:
                        top_keywords = domain_profile['keywords'][:3]  # Top 3 keywords
                        params['q'] = ' OR '.join(top_keywords)
                    
                    response = requests.get(self.base_url, params=params, timeout=10)
                    
                    if response.status_code == 200:
                        data = response.json()
                        if data.get('status') == 'success':
                            category_news = data.get('results', [])
                            # Tag news with category for later processing
                            for news in category_news:
                                news['fetched_category'] = category
                            all_news.extend(category_news)
                        else:
                            logger.warning(f"News API error for {category}: {data.get('message', 'Unknown error')}")
                    else:
                        logger.warning(f"News API request failed for {category}: {response.status_code}")
                        
                except Exception as e:
                    logger.error(f"Error fetching news for category {category}: {str(e)}")
                    continue
            
            # Remove duplicates based on title similarity
            unique_news = self._remove_duplicate_news(all_news)
            
            logger.info(f"✅ Fetched {len(unique_news)} unique news articles from {len(domain_profile['categories'])} categories")
            return unique_news
            
        except Exception as e:
            logger.error(f"❌ News fetching failed: {str(e)}")
            return []
    
    async def _apply_advanced_filtering(self, raw_news: List[Dict], 
                                      domain_profile: Dict, username: str) -> List[Dict]:
        """
        Apply advanced multi-layer filtering to ensure only high-quality, relevant news.
        """
        try:
            logger.info(f"🔍 Applying advanced filtering to {len(raw_news)} news articles")
            
            filtered_news = []
            
            for news in raw_news:
                # Quality filters
                if not self._passes_quality_filters(news):
                    continue
                
                # Relevance filters
                if not self._passes_relevance_filters(news, domain_profile):
                    continue
                
                # Content appropriateness
                if not self._passes_content_filters(news, username):
                    continue
                
                # Recency and trending check
                if not self._passes_trending_filters(news):
                    continue
                
                filtered_news.append(news)
            
            logger.info(f"✅ Advanced filtering complete: {len(filtered_news)} high-quality articles selected")
            return filtered_news
            
        except Exception as e:
            logger.error(f"❌ Advanced filtering failed: {str(e)}")
            return raw_news  # Return unfiltered as fallback
    
    async def _score_news_relevance(self, filtered_news: List[Dict], 
                                   domain_profile: Dict, username: str) -> List[Dict]:
        """
        Use RAG implementation to score news relevance to account's interests.
        """
        try:
            logger.info(f"🎯 Scoring news relevance using RAG for @{username}")
            
            scored_news = []
            
            for news in filtered_news:
                try:
                    # Generate relevance query for this account
                    relevance_query = self._create_relevance_query(news, domain_profile, username)
                    
                    # Use RAG to find similar content in user's domain
                    similar_content = await self._find_similar_domain_content(relevance_query, username)
                    
                    # Calculate relevance score
                    relevance_score = self._calculate_relevance_score(news, similar_content, domain_profile)
                    
                    # Add scoring metadata
                    news['relevance_score'] = relevance_score
                    news['similar_content_found'] = len(similar_content)
                    news['domain_alignment'] = self._calculate_domain_alignment(news, domain_profile)
                    
                    scored_news.append(news)
                    
                except Exception as e:
                    logger.warning(f"Scoring failed for news: {news.get('title', 'Unknown')}: {str(e)}")
                    # Add with default score
                    news['relevance_score'] = 0.5
                    news['similar_content_found'] = 0
                    news['domain_alignment'] = 0.3
                    scored_news.append(news)
            
            # Sort by relevance score
            scored_news.sort(key=lambda x: x['relevance_score'], reverse=True)
            
            logger.info(f"✅ RAG scoring complete: Top score {scored_news[0]['relevance_score']:.2f}")
            return scored_news
            
        except Exception as e:
            logger.error(f"❌ RAG scoring failed: {str(e)}")
            return filtered_news
    
    async def _curate_final_selection(self, scored_news: List[Dict], 
                                    domain_profile: Dict) -> List[Dict]:
        """
        Final curation to select the top 3 most relevant and impactful news stories.
        """
        try:
            logger.info("🎯 Curating final news selection")
            
            if not scored_news:
                return []
            
            # Apply final quality threshold
            high_quality_news = [
                news for news in scored_news 
                if news['relevance_score'] >= self.relevance_threshold
            ]
            
            # If not enough high-quality news, lower threshold
            if len(high_quality_news) < 3:
                high_quality_news = scored_news[:5]  # Take top 5 as backup
            
            # Diversify selection to avoid topic clustering
            final_selection = self._diversify_news_selection(high_quality_news, max_count=3)
            
            # Enhance with additional metadata
            for i, news in enumerate(final_selection):
                news['selection_rank'] = i + 1
                news['curation_reason'] = self._generate_curation_reason(news, domain_profile)
            
            logger.info(f"✅ Final curation complete: {len(final_selection)} premium stories selected")
            return final_selection
            
        except Exception as e:
            logger.error(f"❌ Final curation failed: {str(e)}")
            return scored_news[:3]  # Simple fallback
    
    async def _generate_premium_summary(self, final_news: List[Dict], 
                                      username: str, platform: str) -> Dict:
        """
        Generate a premium 3-sentence summary for each selected news story.
        """
        try:
            logger.info(f"✨ Generating premium summaries for @{username}")
            
            summaries = []
            
            for news in final_news:
                try:
                    # Create RAG prompt for premium summary
                    summary_prompt = self._create_summary_prompt(news, username, platform)
                    
                    # Generate summary using RAG
                    summary = await self._generate_rag_summary(summary_prompt, news)
                    
                    summaries.append({
                        'rank': news.get('selection_rank', 1),
                        'title': news.get('title', 'Breaking News'),
                        'summary': summary,
                        'source': news.get('source_id', 'Unknown'),
                        'published_at': news.get('pubDate', datetime.now().isoformat()),
                        'relevance_score': news.get('relevance_score', 0.5),
                        'news_url': news.get('link', '#'),
                        'breaking_indicator': self._is_breaking_news(news)
                    })
                    
                except Exception as e:
                    logger.warning(f"Summary generation failed for news: {str(e)}")
                    # Create fallback summary
                    summaries.append({
                        'rank': news.get('selection_rank', 1),
                        'title': news.get('title', 'Breaking News'),
                        'summary': self._create_fallback_summary(news),
                        'source': news.get('source_id', 'Unknown'),
                        'published_at': news.get('pubDate', datetime.now().isoformat()),
                        'relevance_score': news.get('relevance_score', 0.5),
                        'news_url': news.get('link', '#'),
                        'breaking_indicator': '🚨'
                    })
            
            return {
                'daily_news_summary': summaries,
                'total_stories': len(summaries),
                'curation_quality': 'premium',
                'generated_for': username,
                'platform': platform
            }
            
        except Exception as e:
            logger.error(f"❌ Premium summary generation failed: {str(e)}")
            return self._create_emergency_summary(final_news, username)
    
    # Helper Methods
    
    async def _extract_content_themes(self, user_posts: List[Dict]) -> List[str]:
        """Extract content themes from user's posts."""
        themes = []
        for post in user_posts[:10]:  # Analyze last 10 posts
            content = post.get('caption', '') or post.get('tweet_text', '')
            if content:
                # Extract hashtags
                hashtags = re.findall(r'#(\w+)', content)
                themes.extend(hashtags)
        
        # Return most common themes
        from collections import Counter
        theme_counts = Counter(themes)
        return [theme for theme, count in theme_counts.most_common(5)]
    
    async def _generate_domain_keywords(self, domain: str, themes: List[str], username: str) -> List[str]:
        """Generate domain-specific keywords for news filtering."""
        base_keywords = {
            'tech_innovation': ['technology', 'innovation', 'startup', 'AI', 'software'],
            'business_corporate': ['business', 'corporate', 'economy', 'market', 'finance'],
            'health_wellness': ['health', 'wellness', 'fitness', 'nutrition', 'medical'],
            'fashion_beauty': ['fashion', 'beauty', 'style', 'trends', 'cosmetics'],
            'food_culinary': ['food', 'culinary', 'restaurant', 'cooking', 'chef'],
            'fitness_sports': ['fitness', 'sports', 'workout', 'athlete', 'training'],
        }
        
        keywords = base_keywords.get(domain, ['news', 'trending'])
        
        # Add user themes
        keywords.extend(themes[:3])
        
        # Add username if it's a brand
        keywords.append(username.lower())
        
        return list(set(keywords))  # Remove duplicates
    
    def _determine_targeting_focus(self, domain: str, account_type: str) -> str:
        """Determine the targeting focus for news curation."""
        if account_type == 'business':
            return f"{domain}_business_focus"
        else:
            return f"{domain}_personal_interest"
    
    def _remove_duplicate_news(self, news_list: List[Dict]) -> List[Dict]:
        """Remove duplicate news based on title similarity."""
        seen_titles = set()
        unique_news = []
        
        for news in news_list:
            title = news.get('title', '').lower()
            title_hash = hashlib.md5(title.encode()).hexdigest()[:10]
            
            if title_hash not in seen_titles:
                seen_titles.add(title_hash)
                unique_news.append(news)
        
        return unique_news
    
    def _passes_quality_filters(self, news: Dict) -> bool:
        """Check if news passes quality filters."""
        # Must have title and description
        if not news.get('title') or not news.get('description'):
            return False
        
        # Must be recent (within 24 hours)
        pub_date = news.get('pubDate')
        if pub_date:
            try:
                pub_datetime = datetime.fromisoformat(pub_date.replace('Z', '+00:00'))
                if (datetime.now().replace(tzinfo=pub_datetime.tzinfo) - pub_datetime).days > 1:
                    return False
            except:
                pass
        
        # Must have credible source
        source = news.get('source_id', '').lower()
        blacklisted_sources = ['unknown', 'blog', 'social']
        if any(blocked in source for blocked in blacklisted_sources):
            return False
        
        return True
    
    def _passes_relevance_filters(self, news: Dict, domain_profile: Dict) -> bool:
        """Check if news is relevant to the domain."""
        title = news.get('title', '').lower()
        description = news.get('description', '').lower()
        content = f"{title} {description}"
        
        # Check for domain keyword matches
        keywords = domain_profile.get('keywords', [])
        keyword_matches = sum(1 for keyword in keywords if keyword.lower() in content)
        
        # Require at least one keyword match
        return keyword_matches > 0
    
    def _passes_content_filters(self, news: Dict, username: str) -> bool:
        """Check if content is appropriate."""
        content = f"{news.get('title', '')} {news.get('description', '')}".lower()
        
        # Filter out inappropriate content
        inappropriate_keywords = [
            'explicit', 'violence', 'nsfw', 'scandal', 'controversy',
            'death', 'tragedy', 'disaster', 'accident'
        ]
        
        return not any(keyword in content for keyword in inappropriate_keywords)
    
    def _passes_trending_filters(self, news: Dict) -> bool:
        """Check if news is trending/breaking."""
        # Simple trending indicators
        title = news.get('title', '').lower()
        description = news.get('description', '').lower()
        
        trending_indicators = [
            'breaking', 'urgent', 'just in', 'developing', 'latest',
            'trending', 'viral', 'hot', 'new', 'update'
        ]
        
        return any(indicator in f"{title} {description}" for indicator in trending_indicators)
    
    def _create_relevance_query(self, news: Dict, domain_profile: Dict, username: str) -> str:
        """Create a query to find similar content using RAG."""
        title = news.get('title', '')
        domain = domain_profile.get('primary_domain', 'general')
        
        return f"{title} {domain} content similar to @{username}"
    
    async def _find_similar_domain_content(self, query: str, username: str) -> List[Dict]:
        """Find similar content in the domain using vector database."""
        try:
            # Use vector database to find similar content
            results = self.vector_db.query_similar_content(query, limit=5)
            return results
        except Exception as e:
            logger.warning(f"Similar content search failed: {str(e)}")
            return []
    
    def _calculate_relevance_score(self, news: Dict, similar_content: List[Dict], 
                                 domain_profile: Dict) -> float:
        """Calculate relevance score based on various factors."""
        score = 0.0
        
        # Base score from keyword matching
        title = news.get('title', '').lower()
        description = news.get('description', '').lower()
        content = f"{title} {description}"
        
        keywords = domain_profile.get('keywords', [])
        keyword_matches = sum(1 for keyword in keywords if keyword.lower() in content)
        score += min(keyword_matches * 0.2, 0.6)  # Max 0.6 from keywords
        
        # Score from similar content found
        score += min(len(similar_content) * 0.1, 0.3)  # Max 0.3 from similarity
        
        # Breaking news bonus
        if self._is_breaking_news(news):
            score += 0.2
        
        # Trending bonus
        if self._passes_trending_filters(news):
            score += 0.1
        
        return min(score, 1.0)  # Cap at 1.0
    
    def _calculate_domain_alignment(self, news: Dict, domain_profile: Dict) -> float:
        """Calculate how well news aligns with the domain."""
        news_category = news.get('fetched_category', '')
        domain_categories = domain_profile.get('categories', [])
        
        if news_category in domain_categories:
            return 1.0
        elif any(cat in news_category for cat in domain_categories):
            return 0.7
        else:
            return 0.3
    
    def _diversify_news_selection(self, news_list: List[Dict], max_count: int = 3) -> List[Dict]:
        """Diversify news selection to avoid topic clustering."""
        if len(news_list) <= max_count:
            return news_list
        
        selected = []
        used_categories = set()
        
        # First, try to get one from each category
        for news in news_list:
            category = news.get('fetched_category', 'general')
            if category not in used_categories and len(selected) < max_count:
                selected.append(news)
                used_categories.add(category)
        
        # Fill remaining slots with highest scoring
        remaining_slots = max_count - len(selected)
        if remaining_slots > 0:
            remaining_news = [n for n in news_list if n not in selected]
            selected.extend(remaining_news[:remaining_slots])
        
        return selected
    
    def _generate_curation_reason(self, news: Dict, domain_profile: Dict) -> str:
        """Generate a reason why this news was curated."""
        reasons = []
        
        if news.get('relevance_score', 0) > 0.8:
            reasons.append("High relevance to your domain")
        
        if self._is_breaking_news(news):
            reasons.append("Breaking news")
        
        if news.get('domain_alignment', 0) > 0.8:
            reasons.append("Perfect domain alignment")
        
        return " | ".join(reasons) if reasons else "Trending in your industry"
    
    def _create_summary_prompt(self, news: Dict, username: str, platform: str) -> str:
        """Create a prompt for RAG summary generation."""
        return f"""
Create a premium 3-sentence news summary for @{username} on {platform}.

News Title: {news.get('title', '')}
News Content: {news.get('description', '')}

Requirements:
- Exactly 3 sentences
- Start with appropriate emoji (🚨 for breaking, 📈 for business, 💡 for innovation, etc.)
- Make it compelling and relevant to @{username}'s audience
- Focus on why this matters to their domain
- End with impact or implication

Format: [Emoji] Sentence 1. Sentence 2. Sentence 3.
"""
    
    async def _generate_rag_summary(self, prompt: str, news: Dict) -> str:
        """Generate summary using RAG implementation."""
        try:
            # Use RAG to generate summary
            response = await self.rag.generate_content(prompt)
            
            # Extract the summary from response
            if isinstance(response, dict):
                summary = response.get('content', '')
            else:
                summary = str(response)
            
            # Clean and validate summary
            sentences = summary.split('.')
            if len(sentences) >= 3:
                summary = '. '.join(sentences[:3]) + '.'
            
            return summary or self._create_fallback_summary(news)
            
        except Exception as e:
            logger.warning(f"RAG summary generation failed: {str(e)}")
            return self._create_fallback_summary(news)
    
    def _create_fallback_summary(self, news: Dict) -> str:
        """Create a fallback summary when RAG fails."""
        title = news.get('title', 'Breaking News')
        description = news.get('description', '')
        
        # Extract first sentence from description
        first_sentence = description.split('.')[0] if description else title
        
        emoji = '🚨' if self._is_breaking_news(news) else '📰'
        
        return f"{emoji} {first_sentence}. This developing story continues to gain attention. Stay informed on the latest updates."
    
    def _is_breaking_news(self, news: Dict) -> bool:
        """Check if news is breaking news."""
        content = f"{news.get('title', '')} {news.get('description', '')}".lower()
        breaking_indicators = ['breaking', 'urgent', 'just in', 'developing', 'alert']
        return any(indicator in content for indicator in breaking_indicators)
    
    def _calculate_overall_quality_score(self, news_list: List[Dict]) -> float:
        """Calculate overall quality score for the curation."""
        if not news_list:
            return 0.0
        
        avg_relevance = sum(n.get('relevance_score', 0) for n in news_list) / len(news_list)
        return avg_relevance
    
    async def _generate_emergency_news_fallback(self, username: str, platform: str, 
                                              account_type: str) -> Dict:
        """Generate emergency fallback when news API fails."""
        logger.warning(f"Generating emergency news fallback for @{username}")
        
        return {
            'username': username,
            'platform': platform,
            'generated_at': datetime.now().isoformat(),
            'domain_profile': {'primary_domain': 'general'},
            'curated_news': [],
            'premium_summary': {
                'daily_news_summary': [
                    {
                        'rank': 1,
                        'title': 'Stay Updated',
                        'summary': '📰 Stay informed with the latest industry developments. Check back later for personalized news updates. Your curated news feed will be available shortly.',
                        'source': 'System',
                        'breaking_indicator': '📰'
                    }
                ],
                'total_stories': 1,
                'curation_quality': 'fallback'
            },
            'curation_metadata': {
                'status': 'emergency_fallback',
                'reason': 'News API temporarily unavailable'
            }
        }
    
    def _create_emergency_summary(self, news_list: List[Dict], username: str) -> Dict:
        """Create emergency summary when RAG fails."""
        summaries = []
        
        for i, news in enumerate(news_list[:3]):
            summaries.append({
                'rank': i + 1,
                'title': news.get('title', 'News Update'),
                'summary': self._create_fallback_summary(news),
                'source': news.get('source_id', 'Unknown'),
                'breaking_indicator': '🚨' if self._is_breaking_news(news) else '📰'
            })
        
        return {
            'daily_news_summary': summaries,
            'total_stories': len(summaries),
            'curation_quality': 'emergency',
            'generated_for': username
        }
    
    # Synchronous versions of async methods for main system integration
    
    def _analyze_account_domain_sync(self, username: str, platform: str, 
                                   account_type: str, user_posts: List[Dict] = None) -> Dict:
        """Synchronous version of _analyze_account_domain."""
        try:
            logger.info(f"🔍 Analyzing account domain for @{username} on {platform}")
            
            # Use AI Domain Intelligence to identify the niche
            if user_posts:
                content_themes = self._extract_content_themes_sync(user_posts)
                domain_analysis = self.ai_domain_intel.analyze_domain_intelligence(username)
                primary_domain = domain_analysis.get('primary_domain', 'general')
            else:
                content_themes = []
                primary_domain = 'general'
            
            # Generate domain-specific keywords
            keywords = self._generate_domain_keywords_sync(primary_domain, content_themes, username)
            
            # Map domain to news categories
            domain_to_categories = {
                'tech_innovation': ['technology', 'science'],
                'business_corporate': ['business', 'top'],
                'health_wellness': ['health', 'sports'],
                'fashion_beauty': ['entertainment', 'top'],
                'food_culinary': ['food', 'entertainment'],
                'fitness_sports': ['sports', 'health'],
                'education': ['top', 'technology'],
                'travel': ['tourism', 'entertainment'],
                'general': ['top', 'business']  # Changed 'general' to 'top'
            }
            
            categories = domain_to_categories.get(primary_domain, ['general'])
            
            domain_profile = {
                'primary_domain': primary_domain,
                'confidence': 0.85,  # High confidence for sync version
                'categories': categories,
                'keywords': keywords,
                'content_themes': content_themes,
                'account_type': account_type,
                'targeting_focus': self._determine_targeting_focus(primary_domain, account_type)
            }
            
            logger.info(f"✅ Domain profile: {primary_domain} (confidence: {domain_profile['confidence']:.2f})")
            return domain_profile
            
        except Exception as e:
            logger.error(f"❌ Domain analysis failed: {str(e)}")
            # Fallback to basic classification
            return {
                'primary_domain': 'general',
                'confidence': 0.6,
                'categories': ['general', 'business'],
                'keywords': [username.lower()],
                'content_themes': [],
                'account_type': account_type,
                'targeting_focus': 'general_interest'
            }
    
    def _fetch_todays_trending_news_sync(self, domain_profile: Dict) -> List[Dict]:
        """Synchronous version of _fetch_todays_trending_news."""
        try:
            logger.info("📰 Fetching today's trending news from News API")
            
            # Prepare API parameters
            today = datetime.now().date()
            yesterday = today - timedelta(days=1)
            
            all_news = []
            
            # Fetch news for each relevant category
            for category in domain_profile['categories']:
                try:
                    params = {
                        'apikey': self.api_key,
                        'category': category,
                        'language': 'en',
                        'size': self.max_news_per_request
                    }
                    
                    # Add domain-specific keywords if available
                    if domain_profile['keywords']:
                        top_keywords = domain_profile['keywords'][:3]  # Top 3 keywords
                        params['q'] = ' OR '.join(top_keywords)
                    
                    response = requests.get(self.base_url, params=params, timeout=10)
                    
                    if response.status_code == 200:
                        data = response.json()
                        if data.get('status') == 'success' and data.get('results'):
                            category_news = data['results']
                            
                            # Add metadata to each news item
                            for news in category_news:
                                news['fetched_category'] = category
                                news['fetch_timestamp'] = datetime.now().isoformat()
                            
                            all_news.extend(category_news)
                            logger.info(f"✅ Fetched {len(category_news)} articles for {category}")
                        else:
                            logger.warning(f"⚠️ No results for category {category}: {data.get('message', 'Unknown error')}")
                    else:
                        logger.error(f"❌ News API error for {category}: {response.status_code}")
                        
                except Exception as e:
                    logger.error(f"❌ Failed to fetch news for {category}: {str(e)}")
                    continue
            
            # Remove duplicates and limit total
            unique_news = self._remove_duplicate_news(all_news)
            limited_news = unique_news[:self.max_total_news]
            
            logger.info(f"✅ Total unique news fetched: {len(limited_news)}")
            return limited_news
            
        except Exception as e:
            logger.error(f"❌ News fetching failed: {str(e)}")
            return []
    
    def _apply_advanced_filtering_sync(self, raw_news: List[Dict], domain_profile: Dict, username: str) -> List[Dict]:
        """Synchronous version of _apply_advanced_filtering."""
        try:
            logger.info(f"🔧 Applying advanced filtering (domain: {domain_profile['primary_domain']})")
            
            filtered_news = []
            
            for news in raw_news:
                # Apply all filters
                if not self._passes_quality_filters(news):
                    continue
                    
                if not self._passes_relevance_filters(news, domain_profile):
                    continue
                    
                if not self._passes_content_filters(news, username):
                    continue
                
                filtered_news.append(news)
            
            logger.info(f"✅ Filtered down to {len(filtered_news)} high-quality articles")
            return filtered_news
            
        except Exception as e:
            logger.error(f"❌ Advanced filtering failed: {str(e)}")
            return raw_news[:10]  # Return first 10 as fallback
    
    def _score_news_relevance_sync(self, filtered_news: List[Dict], domain_profile: Dict, username: str) -> List[Dict]:
        """Synchronous version of _score_news_relevance."""
        try:
            logger.info("🎯 Scoring news relevance using RAG")
            
            scored_news = []
            
            for news in filtered_news:
                try:
                    # Create relevance query for RAG
                    relevance_query = self._create_relevance_query(news, domain_profile, username)
                    
                    # Find similar content (sync version)
                    similar_content = self._find_similar_domain_content_sync(relevance_query, username)
                    
                    # Calculate relevance score
                    relevance_score = self._calculate_relevance_score(news, similar_content, domain_profile)
                    
                    # Calculate domain alignment
                    domain_alignment = self._calculate_domain_alignment(news, domain_profile)
                    
                    # Add scoring metadata
                    news['relevance_score'] = relevance_score
                    news['domain_alignment'] = domain_alignment
                    news['final_score'] = (relevance_score * 0.7) + (domain_alignment * 0.3)
                    news['curation_reason'] = self._generate_curation_reason(news, domain_profile)
                    
                    scored_news.append(news)
                    
                except Exception as e:
                    logger.warning(f"Scoring failed for news item: {str(e)}")
                    # Add with default scoring
                    news['relevance_score'] = 0.5
                    news['domain_alignment'] = 0.5
                    news['final_score'] = 0.5
                    news['curation_reason'] = "General relevance"
                    scored_news.append(news)
            
            # Sort by final score
            scored_news.sort(key=lambda x: x['final_score'], reverse=True)
            
            logger.info(f"✅ Scored {len(scored_news)} articles")
            return scored_news
            
        except Exception as e:
            logger.error(f"❌ Relevance scoring failed: {str(e)}")
            return filtered_news
    
    def _curate_final_selection_sync(self, scored_news: List[Dict], domain_profile: Dict) -> List[Dict]:
        """Synchronous version of _curate_final_selection."""
        try:
            logger.info("✨ Curating final news selection")
            
            # Filter by minimum score threshold
            high_quality = [n for n in scored_news if n.get('final_score', 0) >= 0.6]
            
            if not high_quality:
                high_quality = scored_news[:5]  # Take top 5 if none meet threshold
            
            # Diversify selection
            diversified = self._diversify_news_selection(high_quality, max_count=3)
            
            # Add selection metadata
            for i, news in enumerate(diversified):
                news['selection_rank'] = i + 1
                news['selected_at'] = datetime.now().isoformat()
                news['selection_confidence'] = min(news.get('final_score', 0.5) + 0.2, 1.0)
            
            logger.info(f"✅ Final selection: {len(diversified)} premium articles")
            return diversified
            
        except Exception as e:
            logger.error(f"❌ Final curation failed: {str(e)}")
            return scored_news[:3]  # Return top 3 as fallback
    
    def _generate_premium_summary_sync(self, final_news: List[Dict], username: str, platform: str) -> Dict:
        """Synchronous version of _generate_premium_summary."""
        try:
            logger.info(f"✨ Generating premium summaries for @{username}")
            
            summaries = []
            
            for news in final_news:
                try:
                    # Create RAG prompt for premium summary
                    summary_prompt = self._create_summary_prompt(news, username, platform)
                    
                    # Generate summary using RAG (sync version)
                    summary = self._generate_rag_summary_sync(summary_prompt, news)
                    
                    summaries.append({
                        'rank': news.get('selection_rank', 1),
                        'title': news.get('title', 'Breaking News'),
                        'summary': summary,
                        'source': news.get('source_id', 'Unknown'),
                        'published_at': news.get('pubDate', datetime.now().isoformat()),
                        'relevance_score': news.get('relevance_score', 0.5),
                        'news_url': news.get('link', '#'),
                        'breaking_indicator': self._is_breaking_news(news)
                    })
                    
                except Exception as e:
                    logger.warning(f"Summary generation failed for news: {str(e)}")
                    # Create fallback summary
                    summaries.append({
                        'rank': news.get('selection_rank', 1),
                        'title': news.get('title', 'Breaking News'),
                        'summary': self._create_fallback_summary(news),
                        'source': news.get('source_id', 'Unknown'),
                        'published_at': news.get('pubDate', datetime.now().isoformat()),
                        'relevance_score': news.get('relevance_score', 0.5),
                        'news_url': news.get('link', '#'),
                        'breaking_indicator': '🚨'
                    })
            
            return {
                'daily_news_summary': summaries,
                'total_stories': len(summaries),
                'curation_quality': 'premium',
                'generated_for': username,
                'platform': platform
            }
            
        except Exception as e:
            logger.error(f"❌ Premium summary generation failed: {str(e)}")
            return self._create_emergency_summary(final_news, username)
    
    def _generate_emergency_news_fallback_sync(self, username: str, platform: str, account_type: str) -> Dict:
        """Synchronous version of _generate_emergency_news_fallback."""
        logger.warning(f"Generating emergency news fallback for @{username}")
        
        return {
            'username': username,
            'platform': platform,
            'generated_at': datetime.now().isoformat(),
            'domain_profile': {'primary_domain': 'general'},
            'curated_news': [],
            'premium_summary': {
                'daily_news_summary': [
                    {
                        'rank': 1,
                        'title': 'Stay Updated',
                        'summary': '📰 Stay informed with the latest industry developments. Check back later for personalized news updates. Your curated news feed will be available shortly.',
                        'source': 'System',
                        'breaking_indicator': '📰'
                    }
                ],
                'total_stories': 1,
                'curation_quality': 'fallback'
            },
            'curation_metadata': {
                'status': 'emergency_fallback',
                'reason': 'News API temporarily unavailable'
            }
        }
    
    # Synchronous helper methods
    
    def _extract_content_themes_sync(self, user_posts: List[Dict]) -> List[str]:
        """Synchronous version of _extract_content_themes."""
        themes = []
        for post in user_posts[:10]:  # Analyze last 10 posts
            content = post.get('caption', '') or post.get('tweet_text', '')
            if content:
                # Extract hashtags
                hashtags = re.findall(r'#(\w+)', content)
                themes.extend(hashtags)
        
        # Return most common themes
        from collections import Counter
        theme_counts = Counter(themes)
        return [theme for theme, count in theme_counts.most_common(5)]
    
    def _generate_domain_keywords_sync(self, domain: str, themes: List[str], username: str) -> List[str]:
        """Synchronous version of _generate_domain_keywords."""
        base_keywords = {
            'tech_innovation': ['technology', 'innovation', 'startup', 'AI', 'software'],
            'business_corporate': ['business', 'corporate', 'economy', 'market', 'finance'],
            'health_wellness': ['health', 'wellness', 'fitness', 'nutrition', 'medical'],
            'fashion_beauty': ['fashion', 'beauty', 'style', 'trends', 'cosmetics'],
            'food_culinary': ['food', 'culinary', 'restaurant', 'cooking', 'chef'],
            'fitness_sports': ['fitness', 'sports', 'workout', 'athlete', 'training'],
        }
        
        keywords = base_keywords.get(domain, ['news', 'trending'])
        
        # Add user themes
        keywords.extend(themes[:3])
        
        # Add username if it's a brand
        keywords.append(username.lower())
        
        return list(set(keywords))  # Remove duplicates
    
    def _find_similar_domain_content_sync(self, query: str, username: str) -> List[Dict]:
        """Synchronous version of _find_similar_domain_content."""
        try:
            # Use vector database to find similar content
            results = self.vector_db.query_similar_content(query, limit=5)
            return results
        except Exception as e:
            logger.warning(f"Similar content search failed: {str(e)}")
            return []
    
    def _generate_rag_summary_sync(self, prompt: str, news: Dict) -> str:
        """Synchronous version of _generate_rag_summary."""
        try:
            # Use RAG to generate summary (sync version)
            response = self.rag.generate_content_sync(prompt) if hasattr(self.rag, 'generate_content_sync') else self.rag.generate_content(prompt)
            
            # Extract the summary from response
            if isinstance(response, dict):
                summary = response.get('content', '')
            else:
                summary = str(response)
            
            # Clean and validate summary
            sentences = summary.split('.')
            if len(sentences) >= 3:
                summary = '. '.join(sentences[:3]) + '.'
            
            return summary or self._create_fallback_summary(news)
            
        except Exception as e:
            logger.warning(f"RAG summary generation failed: {str(e)}")
            return self._create_fallback_summary(news)
