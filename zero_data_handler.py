"""
ENHANCED Zero Data Handler Module
Add-on module for handling new/private accounts with zero data.
This module provides comprehensive multi-stage recommendations based on competitor data or global posting style.
"""

import logging
import json
import traceback
from typing import Dict, List, Optional
import google.generativeai as genai
import os
from export_content_plan import ContentPlanExporter
from datetime import datetime
import re
from zero_post_rag_implementation import ZeroPostRAGImplementation
from rag_implementation import RagImplementation
from recommendation_generation import RecommendationGenerator

# Set up logging
logger = logging.getLogger(__name__)

# Global posting style configurations for different account types
GLOBAL_POSTING_STYLES = {
    "brand": {
        "instagram": {
            "posting_style": "Professional brand content with high-quality visuals, consistent aesthetic, product showcases, behind-the-scenes content, and strategic use of branded hashtags to build community engagement.",
            "content_themes": ["product showcase", "brand story", "customer testimonials", "industry insights", "behind the scenes"],
            "tone": "professional, authentic, engaging",
            "hashtag_strategy": "mix of branded, industry-specific, and trending hashtags",
            "engagement_style": "community-focused, responsive to comments, educational"
        },
        "twitter": {
            "posting_style": "Concise, professional tweets with industry insights, company updates, thought leadership content, and strategic engagement with relevant conversations.",
            "content_themes": ["industry insights", "company updates", "thought leadership", "customer support", "trending topics"],
            "tone": "professional, authoritative, conversational",
            "hashtag_strategy": "industry-specific hashtags and trending topics",
            "engagement_style": "thought leadership, customer support, industry participation"
        },
        "facebook": {
            "posting_style": "Comprehensive posts with detailed descriptions, community engagement, event promotion, and customer-centric content that drives meaningful interactions.",
            "content_themes": ["community building", "event promotion", "customer stories", "educational content", "brand updates"],
            "tone": "friendly, professional, community-oriented",
            "hashtag_strategy": "minimal, focused on community and brand terms",
            "engagement_style": "community building, customer service, event promotion"
        }
    },
    "personal": {
        "instagram": {
            "posting_style": "Authentic personal content with lifestyle moments, personal interests, casual photography, and genuine interactions with followers.",
            "content_themes": ["lifestyle", "personal interests", "daily moments", "travel", "hobbies"],
            "tone": "casual, authentic, relatable",
            "hashtag_strategy": "lifestyle and interest-based hashtags",
            "engagement_style": "personal connections, authentic interactions, community building"
        },
        "twitter": {
            "posting_style": "Personal thoughts, opinions, casual conversations, sharing interesting content, and engaging with community topics.",
            "content_themes": ["personal opinions", "interesting finds", "casual thoughts", "community engagement", "hobby discussions"],
            "tone": "casual, conversational, opinionated",
            "hashtag_strategy": "trending topics and personal interest hashtags",
            "engagement_style": "conversational, opinion sharing, community participation"
        },
        "facebook": {
            "posting_style": "Personal updates, family moments, life events, and meaningful connections with friends and family.",
            "content_themes": ["personal updates", "family moments", "life events", "shared interests", "community involvement"],
            "tone": "personal, warm, family-oriented",
            "hashtag_strategy": "minimal, personal event focused",
            "engagement_style": "personal connections, family updates, community involvement"
        }
    }
}

class ZeroDataHandler:
    """
    ENHANCED: Add-on class for handling new/private accounts with zero data.
    Comprehensive multi-stage fallback system with battle-tested data exploration.
    Provides recommendations using competitor data or global posting style.
    """
    
    def __init__(self, rag=None, recommendation_generator=None, vector_db=None, r2_storage=None, data_retriever=None):
        """Initialize the enhanced zero data handler."""
        self.rag = rag if rag else RagImplementation(vector_db=vector_db)
        self.recommendation_generator = recommendation_generator
        self.vector_db = vector_db
        self.data_retriever = data_retriever  # Add data retriever for main bucket access
        
        # R2 storage for exports – allow injection from caller for easier testing
        try:
            from r2_storage_manager import R2StorageManager
            self.r2_storage = r2_storage if r2_storage else R2StorageManager()
            logger.info("✅ R2StorageManager initialized for ZeroDataHandler exports")
        except Exception as e:
            logger.warning(f"⚠️ Failed to initialize R2StorageManager inside ZeroDataHandler: {str(e)}")
            self.r2_storage = None
        
        # Initialize dedicated zero-post RAG implementation
        try:
            self.zero_post_rag = ZeroPostRAGImplementation()
            logger.info("✅ Dedicated Zero-Post RAG Implementation initialized")
        except Exception as e:
            logger.warning(f"⚠️ Failed to initialize Zero-Post RAG: {str(e)} - Using fallback methods")
            self.zero_post_rag = None
        
        logger.info("🔄 ENHANCED ZeroDataHandler initialized for comprehensive zero-data account handling")
    
    def handle_zero_data_account(self, primary_username: str, secondary_usernames: List[str], 
                                platform: str = "instagram", account_type: str = "brand", 
                                posting_style: str = None, info_json_data: Dict = None,
                                available_competitor_data: Dict = None) -> Dict:
        """
        BULLETPROOF: Handle recommendation generation for accounts with zero data.
        Comprehensive multi-stage approach with battle-tested data exploration and pre-collected competitor data.
        
        Args:
            primary_username: The primary account username (new/private)
            secondary_usernames: List of competitor usernames for analysis
            platform: Social media platform (instagram, twitter, facebook)
            account_type: Account type (brand, personal) 
            posting_style: Posting style from info.json (CRITICAL for fallback)
            info_json_data: Complete info.json data for enhanced context
            available_competitor_data: Pre-collected competitor data from main pipeline
            
        Returns:
            Structured recommendation dictionary with WARNING HEADERS
        """
        logger.info(f"🚀 BULLETPROOF Zero Data Handler activated for @{primary_username} on {platform}")
        logger.info(f"📊 Context: {account_type} account, {len(secondary_usernames)} competitors, competitor_data: {len(available_competitor_data or {})}/{len(secondary_usernames)}")
        
        try:
            # ------------------------------------------------------------------
            # FIXED: DO NOT CLEAR VECTOR DATABASE - Keep freshly scraped competitor data
            # The vector database contains valuable competitor data that was just scraped
            # ------------------------------------------------------------------
            logger.info("🔍 KEEPING vector database intact - preserving freshly scraped competitor data for RAG")
            
            # Check what data is available in vector database before proceeding
            if self.vector_db and hasattr(self.vector_db, 'get_count'):
                try:
                    doc_count = self.vector_db.get_count()
                    logger.info(f"📊 Vector database contains {doc_count} documents for RAG analysis")
                except Exception as e:
                    logger.warning(f"⚠️ Could not get vector DB count: {str(e)}")

            # Multi-stage approach with comprehensive data exploration
            recommendation = None
            approach_used = None
            
            # Stage 1: BULLETPROOF - Use pre-collected competitor data if available
            if available_competitor_data and len(available_competitor_data) > 0:
                logger.info(f"🔍 Stage 1: Using pre-collected competitor data ({len(available_competitor_data)} sources)...")
                recommendation = self._generate_from_available_competitor_data(
                    primary_username, available_competitor_data, platform, account_type, posting_style, info_json_data
                )
                
                if recommendation:
                    approach_used = "available_competitor_data"
                    logger.info(f"✅ SUCCESS: Using available competitor data for @{primary_username}")
                else:
                    logger.warning(f"⚠️ Stage 1 failed: Could not generate from available competitor data")
            else:
                logger.warning(f"⚠️ Stage 1 skipped: No pre-collected competitor data available")

            # Stage 2: BULLETPROOF - Battle test for ANY competitor data in any storage
            if not recommendation:
                logger.info(f"🔍 Stage 2: Battle testing for competitor data in any storage...")
                battle_test_result = self._battle_test_competitor_data_approach(
                    primary_username, secondary_usernames, platform, account_type, posting_style, info_json_data
                )
                
                if battle_test_result.get('success'):
                    recommendation = battle_test_result.get('recommendation')
                    approach_used = "competitor_battle_tested"
                    logger.info(f"✅ SUCCESS: Using battle-tested competitor data for @{primary_username}")
                else:
                    logger.warning(f"⚠️ Stage 2 failed: {battle_test_result.get('reason', 'unknown')}")
            
            # ------------------------------------------------------------------
            # NEW REQUIREMENT (2025-07-27): If we still have no data after all
            # competitor attempts, **STOP**.  No posting-style fallback.
            # ------------------------------------------------------------------
            if not recommendation:
                logger.error("❌ ZERO DATA: No primary or competitor data available – stopping operation per user directive")
                return None
            
            # CRITICAL: Add comprehensive WARNING HEADERS and limitation messaging
            formatted_recommendation = self._add_enhanced_warning_headers(
                recommendation, primary_username, platform, account_type, approach_used, secondary_usernames
            )
            
            # ------------------------------------------------------------------
            # 🚚 EXPORT: Call ContentPlanExporter to persist the content plan sections
            # ------------------------------------------------------------------
            try:
                if self.r2_storage:
                    from export_content_plan import ContentPlanExporter
                    exporter = ContentPlanExporter(self.r2_storage)
                    export_payload = {
                        "platform": platform,
                        "primary_username": primary_username,
                        "recommendation": formatted_recommendation
                    }
                    export_success = exporter.export_content_plan(export_payload)
                    if export_success:
                        logger.info(f"📦 ZeroDataHandler export completed successfully for @{primary_username}")
                    else:
                        logger.error(f"❌ ZeroDataHandler export failed for @{primary_username}")
                else:
                    logger.warning("⚠️ R2StorageManager not available – skipping export from ZeroDataHandler")
            except Exception as export_e:
                logger.error(f"❌ Exception during ZeroDataHandler export for @{primary_username}: {str(export_e)}")
                import traceback
                logger.error(traceback.format_exc())
        
            logger.info(f"✅ BULLETPROOF Zero Data Handler completed for @{primary_username} using {approach_used}")
            return formatted_recommendation
            
        except Exception as e:
            logger.error(f"❌ BULLETPROOF Zero Data Handler failed for @{primary_username}: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return None
    
    def _generate_from_available_competitor_data(self, primary_username: str, available_competitor_data: Dict,
                                               platform: str, account_type: str, posting_style: str, 
                                               info_json_data: Dict) -> Optional[Dict]:
        """
        BULLETPROOF: Generate recommendations using pre-collected competitor data.
        This method uses the dedicated zero-post RAG implementation for high-quality content generation.
        
        Args:
            primary_username: Primary username with zero data
            available_competitor_data: Pre-collected competitor data indexed by username
            platform: Social media platform
            account_type: Account type (brand/personal)
            posting_style: Posting style from info.json
            info_json_data: Complete info.json data
            
        Returns:
            Recommendation dictionary or None if generation fails
        """
        logger.info(f"📊 BULLETPROOF: Generating from {len(available_competitor_data)} competitor data sources for @{primary_username}")
        
        try:
            # BULLETPROOF APPROACH: Use dedicated zero-post RAG implementation
            if self.zero_post_rag:
                logger.info(f"🎯 Using dedicated Zero-Post RAG implementation for @{primary_username}")
                
                # Generate comprehensive recommendations using dedicated RAG
                rag_recommendation = self.zero_post_rag.generate_zero_post_recommendations(
                    primary_username=primary_username,
                    platform=platform,
                    account_type=account_type,
                    posting_style=posting_style or "professional",
                    available_competitor_data=available_competitor_data
                )
                
                if rag_recommendation:
                    logger.info(f"✅ BULLETPROOF RAG generation successful for @{primary_username} using competitor data")
                    
                    # Clean up session data to free memory
                    self.zero_post_rag.cleanup_session_data(primary_username, platform)
                    
                    return rag_recommendation
                else:
                    logger.warning(f"⚠️ Dedicated RAG failed, falling back to legacy method for @{primary_username}")
            
            # FALLBACK: Legacy approach if dedicated RAG fails
            logger.info(f"🔄 Using fallback competitor data processing for @{primary_username}")
            
            # Aggregate all available competitor posts for fallback RAG
            all_competitor_posts = []
            competitor_usernames = []
            
            for competitor, competitor_data in available_competitor_data.items():
                posts = competitor_data.get('posts', [])
                source = competitor_data.get('source', 'unknown')
                
                logger.info(f"📊 Processing {len(posts)} posts from {competitor} (source: {source})")
                
                for post in posts:
                    # Normalize post format for RAG
                    post_content = ""
                    if isinstance(post, dict):
                        post_content = post.get('caption') or post.get('text') or post.get('content') or str(post)
                    elif isinstance(post, str):
                        post_content = post
                    
                    if post_content and len(post_content.strip()) > 10:  # Ensure meaningful content
                        all_competitor_posts.append({
                            'content': post_content.strip(),
                            'username': competitor,
                            'platform': platform,
                            'source': source
                        })
                
                competitor_usernames.append(competitor)
            
            if not all_competitor_posts:
                logger.warning(f"⚠️ No usable competitor posts found for @{primary_username}")
                return None
            
            logger.info(f"✅ Aggregated {len(all_competitor_posts)} usable competitor posts from {len(competitor_usernames)} competitors")
            
            # Index competitor posts in vector database temporarily for RAG
            if hasattr(self, 'vector_db') and self.vector_db:
                try:
                    # Use a temporary collection or namespace for competitor data
                    for i, post in enumerate(all_competitor_posts):
                        # Index under original competitor username (competitor=True)
                        self.vector_db.add_post(
                            post_id=f"temp_competitor_{primary_username}_{i}",
                            content=post['content'],
                            metadata={
                                'username': post['username'],
                                'platform': platform,
                                'is_competitor': True,
                                'primary_for': primary_username,
                                'source': post['source']
                            },
                            is_competitor=True
                        )
                        # ALSO index the SAME content again but mark as non-competitor so that
                        # any downstream RAG query that filters is_competitor=False (legacy path)
                        # can still retrieve these documents when it searches by the competitor username.
                        self.vector_db.add_post(
                            post_id=f"temp_competitor_nc_{primary_username}_{i}",
                            content=post['content'],
                            metadata={
                                'username': post['username'],
                                'platform': platform,
                                'is_competitor': False,
                                'primary_for': primary_username,
                                'source': post['source']
                            },
                            is_competitor=False
                        )
                        # ALSO index a shadow copy under the primary_username so that the standard
                        self.vector_db.add_post(
                            post_id=f"temp_competitor_{primary_username}_{i}",
                            content=post['content'],
                            metadata={
                                'username': post['username'],
                                'platform': platform,
                                'is_competitor': True,
                                'primary_for': primary_username,
                                'source': post['source']
                            },
                            is_competitor=True
                        )
                        # ALSO index a shadow copy under the primary_username so that the standard
                        # RagImplementation can treat these as if they were the user's own posts.
                        self.vector_db.add_post(
                            post_id=f"shadow_{primary_username}_{i}",
                            content=post['content'],
                            metadata={
                                'username': primary_username,
                                'platform': platform,
                                'is_competitor_shadow': True,
                                'origin_competitor': post['username'],
                                'source': post['source']
                            },
                            is_competitor=False
                        )
                    logger.info(f"✅ Indexed {len(all_competitor_posts)} competitor posts for RAG analysis")
                except Exception as e:
                    logger.warning(f"⚠️ Could not index competitor posts for RAG: {str(e)}")
            
            # Generate RAG-based recommendations using competitor data AS IF it's primary data
            if hasattr(self, 'rag') and self.rag:
                try:
                    # Create RAG query focused on generating strategy for the primary username
                    rag_query = f"""
                    Generate strategic content recommendations for @{primary_username}, a {account_type} account on {platform}.
                    
                    CRITICAL CONTEXT: @{primary_username} is a new/private account with no posting history. 
                    Use the following competitor analysis data to generate strategic recommendations:
                    
                    Competitor data shows successful content patterns in this niche. Generate recommendations that:
                    1. Leverage insights from competitor success patterns
                    2. Differentiate @{primary_username} from competitors
                    3. Provide specific content strategies for {platform}
                    4. Include specific post recommendations
                    
                    Platform: {platform}
                    Account Type: {account_type}
                    Posting Style: {posting_style or 'Not specified'}
                    """
                    
                    rag_response = self.rag.generate_recommendation(
                        primary_username=primary_username,
                        secondary_usernames=competitor_usernames,
                        query=rag_query,
                        is_branding=(account_type == "brand"),
                        platform=platform
                    )
                    
                    if rag_response and isinstance(rag_response, dict):
                        logger.info(f"✅ BULLETPROOF RAG generation successful for @{primary_username} using competitor data")
                        
                        # Add metadata about the data source
                        rag_response['metadata'] = rag_response.get('metadata', {})
                        rag_response['metadata'].update({
                            'data_source': 'available_competitor_data',
                            'competitor_count': len(competitor_usernames),
                            'competitors_used': competitor_usernames,
                            'post_count_analyzed': len(all_competitor_posts)
                        })
                        
                        return rag_response
                    else:
                        logger.warning(f"⚠️ RAG response was empty or invalid for @{primary_username}")
                        
                except Exception as e:
                    logger.warning(f"⚠️ RAG generation failed for @{primary_username}: {str(e)}")
            
            # Fallback: Create structured recommendation directly from competitor analysis
            logger.info(f"🔄 Creating direct competitor-based recommendation for @{primary_username}")
            return self._create_competitor_based_recommendation(
                primary_username, competitor_usernames, all_competitor_posts, platform, account_type, posting_style
            )
            
        except Exception as e:
            logger.error(f"❌ Error generating from available competitor data for @{primary_username}: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return None
    
    def _create_competitor_based_recommendation(self, primary_username: str, competitor_usernames: List[str],
                                              competitor_posts: List[Dict], platform: str, account_type: str,
                                              posting_style: str) -> Dict:
        """
        BULLETPROOF: Create a structured recommendation directly from competitor analysis.
        This is used when RAG fails but we still have competitor data to work with.
        
        Args:
            primary_username: Primary username with zero data
            competitor_usernames: List of competitor usernames
            competitor_posts: List of competitor posts with content
            platform: Social media platform
            account_type: Account type
            posting_style: Posting style preference
            
        Returns:
            Structured recommendation dictionary
        """
        logger.info(f"📊 Creating competitor-based recommendation for @{primary_username} using {len(competitor_posts)} posts from {len(competitor_usernames)} competitors")
        
        try:
            # Analyze competitor content themes
            content_themes = self._extract_content_themes_from_posts(competitor_posts)
            common_hashtags = self._extract_common_hashtags_from_posts(competitor_posts)
            
            # Create strategic recommendations based on competitor analysis
            strategic_recommendations = {
                "approach": f"Competitor-informed strategy for @{primary_username}",
                "recommendations": [
                    f"Focus on {', '.join(content_themes[:3])} content themes based on competitor success patterns",
                    f"Use strategic hashtag combinations like: {', '.join(common_hashtags[:5])}",
                    f"Post consistently on {platform} to build audience engagement like successful competitors",
                    "Differentiate your voice while leveraging proven content categories",
                    f"Engage authentically with {account_type} account positioning"
                ],
                "competitive_insights": f"Based on analysis of {len(competitor_usernames)} competitors: {', '.join(competitor_usernames)}",
                "content_strategy": f"Leverage successful {platform} patterns while maintaining authentic {account_type} voice"
            }
            
            # Create competitor analysis section
            competitive_analysis = {}
            for competitor in competitor_usernames:
                competitor_posts_for_user = [p for p in competitor_posts if p.get('username') == competitor]
                competitive_analysis[competitor] = {
                    "overview": f"Analyzed {len(competitor_posts_for_user)} posts from @{competitor}",
                    "intelligence_source": "direct_competitor_content_analysis",
                    "key_themes": [theme for theme in content_themes if any(theme.lower() in post.get('content', '').lower() for post in competitor_posts_for_user)],
                    "recommendation": f"Monitor @{competitor}'s content patterns for strategic insights"
                }
            
            # Create next post prediction
            next_post_prediction = {
                "caption": f"Excited to share my {account_type} journey on {platform}! 🚀 Stay tuned for {content_themes[0] if content_themes else 'amazing content'}.",
                "hashtags": common_hashtags[:8] if common_hashtags else [f"#{account_type}", f"#{platform}", "#newaccount"],
                "call_to_action": "Follow me for updates and insights!",
                "image_prompt": f"Professional {account_type} introduction post for {platform} with {content_themes[0] if content_themes else 'engaging'} theme"
            }
            
            # Structure final recommendation
            recommendation = {
                "strategic_recommendations": strategic_recommendations,
                "competitive_analysis": competitive_analysis,
                "next_post_prediction": next_post_prediction,
                "metadata": {
                    "generation_method": "competitor_based_direct",
                    "competitor_count": len(competitor_usernames),
                    "post_count_analyzed": len(competitor_posts),
                    "primary_username": primary_username,
                    "platform": platform,
                    "account_type": account_type
                }
            }
            
            logger.info(f"✅ Successfully created competitor-based recommendation for @{primary_username}")
            return recommendation
            
        except Exception as e:
            logger.error(f"❌ Error creating competitor-based recommendation for @{primary_username}: {str(e)}")
            return {
                "strategic_recommendations": {
                    "recommendations": [f"Start posting on {platform} to enable data-driven recommendations"]
                },
                "competitive_analysis": {"status": "analysis_failed"},
                "next_post_prediction": {
                    "caption": f"Welcome to my {platform} account!",
                    "hashtags": [f"#{account_type}", f"#{platform}"],
                    "call_to_action": "Follow for updates!",
                    "image_prompt": f"Welcome post for {platform}"
                }
            }
    
    def _extract_content_themes_from_posts(self, posts: List[Dict]) -> List[str]:
        """Extract common content themes from competitor posts."""
        themes = []
        common_keywords = {}
        
        for post in posts:
            content = post.get('content', '').lower()
            # Simple keyword extraction (could be enhanced with NLP)
            words = content.split()
            for word in words:
                if len(word) > 4 and word.isalpha():  # Filter meaningful words
                    common_keywords[word] = common_keywords.get(word, 0) + 1
        
        # Get most common themes
        sorted_keywords = sorted(common_keywords.items(), key=lambda x: x[1], reverse=True)
        themes = [word for word, count in sorted_keywords[:5] if count > 1]
        
        return themes if themes else ["content", "engagement", "community"]
    
    def _extract_common_hashtags_from_posts(self, posts: List[Dict]) -> List[str]:
        """Extract common hashtags from competitor posts."""
        hashtag_counts = {}
        
        for post in posts:
            content = post.get('content', '')
            # Simple hashtag extraction
            import re
            hashtags = re.findall(r'#\w+', content)
            for hashtag in hashtags:
                hashtag_counts[hashtag] = hashtag_counts.get(hashtag, 0) + 1
        
        # Get most common hashtags
        sorted_hashtags = sorted(hashtag_counts.items(), key=lambda x: x[1], reverse=True)
        common_hashtags = [hashtag for hashtag, count in sorted_hashtags[:10] if count > 1]
        
        return common_hashtags if common_hashtags else ["#content", "#engagement", "#community"]
    
    def _add_enhanced_warning_headers(self, recommendation: Dict, primary_username: str, 
                                   platform: str, account_type: str, approach_used: str, 
                                   competitor_usernames: List[str] = None) -> Dict:
        """
        BULLETPROOF: Add comprehensive warning headers and limitation messaging to the recommendation.
        This ensures users understand the data limitations and source of recommendations.
        
        Args:
            recommendation: Base recommendation dictionary
            primary_username: Primary username with zero data
            platform: Social media platform
            account_type: Account type
            approach_used: Method used to generate recommendation
            
        Returns:
            Enhanced recommendation with warning headers
        """
        logger.info(f"📝 Adding enhanced warning headers for @{primary_username} (approach: {approach_used})")
        
        try:
            # Create copy to avoid modifying original
            enhanced_recommendation = recommendation.copy() if recommendation else {}
            
            # Ensure metadata exists
            if 'metadata' not in enhanced_recommendation:
                enhanced_recommendation['metadata'] = {}
            
            # Add approach-specific warning headers
            if approach_used == "available_competitor_data":
                header_message = (
                    f"🚨 IMPORTANT NOTICE: @{primary_username} appears to be private/new with no posting history. "
                    f"These strategic recommendations are based on competitive analysis of similar accounts. "
                    f"Start posting publicly to get personalized, data-driven recommendations."
                )
                limitation_message = (
                    f"⚠️ DATA LIMITATION: Recommendations generated using competitor analysis for @{primary_username}. "
                    f"These lack personalization to your unique content style, audience preferences, and engagement patterns. "
                    f"Post 15-20 pieces of content to unlock fully personalized insights."
                )
                competitive_analysis_note = (
                    f"Competitive intelligence based on similar accounts in your niche. Results will be significantly "
                    f"more accurate once @{primary_username} has public posting history for comparison."
                )
                
            elif approach_used == "competitor_battle_tested":
                header_message = (
                    f"🚨 IMPORTANT NOTICE: @{primary_username} is private/new. Recommendations generated using "
                    f"extensive competitive intelligence gathering. However, these cannot be personalized to your "
                    f"specific audience and content style."
                )
                limitation_message = (
                    f"⚠️ DATA LIMITATION: Advanced competitor analysis used for @{primary_username}, but recommendations "
                    f"lack personalization to your unique voice, engagement patterns, and audience preferences."
                )
                competitive_analysis_note = (
                    f"Comprehensive competitive analysis completed, but personalized comparison requires your "
                    f"account to have public content history."
                )
                
            elif approach_used == "gemini_only_posting_style":
                header_message = (
                    f"🚨 IMPORTANT NOTICE: @{primary_username} has no public data and no competitor data available. "
                    f"Recommendations generated using your stated posting style preferences. These are general "
                    f"guidelines - start posting to get data-driven insights."
                )
                limitation_message = (
                    f"⚠️ DATA LIMITATION: Generic recommendations for @{primary_username} based only on posting "
                    f"style preferences. No competitive analysis or performance data available."
                )
                competitive_analysis_note = (
                    f"No competitive analysis possible - insufficient data. Manual competitor research recommended."
                )
            else:
                header_message = (
                    f"🚨 IMPORTANT NOTICE: @{primary_username} has limited data available. Recommendations "
                    f"generated using alternative analysis methods. Quality will improve with posting history."
                )
                limitation_message = (
                    f"⚠️ DATA LIMITATION: Alternative recommendation method used for @{primary_username}. "
                    f"Results may lack full personalization."
                )
                competitive_analysis_note = "Limited competitive analysis available."
            
            # Insert header at the top of strategic recommendations
            if 'strategic_recommendations' in enhanced_recommendation:
                if isinstance(enhanced_recommendation['strategic_recommendations'], dict):
                    # Create new dict with header first
                    strategic_with_header = {
                        "🚨 CRITICAL DATA LIMITATION NOTICE": header_message
                    }
                    strategic_with_header.update(enhanced_recommendation['strategic_recommendations'])
                    enhanced_recommendation['strategic_recommendations'] = strategic_with_header
                elif isinstance(enhanced_recommendation['strategic_recommendations'], list):
                    # If it's a list, convert to dict format with header
                    enhanced_recommendation['strategic_recommendations'] = {
                        "🚨 CRITICAL DATA LIMITATION NOTICE": header_message,
                        "recommendations": enhanced_recommendation['strategic_recommendations']
                    }
            else:
                # Create strategic recommendations section with header
                enhanced_recommendation['strategic_recommendations'] = {
                    "🚨 CRITICAL DATA LIMITATION NOTICE": header_message,
                    "recommendations": ["Start posting publicly to enable data-driven recommendations"]
                }
            
            # Update competitive analysis with limitation note and smart export logic
            # Check for both possible key names for competitor analysis
            competitive_analysis_key = None
            has_real_competitor_data = False
            
            if 'competitive_analysis' in enhanced_recommendation:
                competitive_analysis_key = 'competitive_analysis'
            elif 'competitor_analysis' in enhanced_recommendation:
                competitive_analysis_key = 'competitor_analysis'
                
            if competitive_analysis_key:
                if isinstance(enhanced_recommendation[competitive_analysis_key], dict):
                    # Check if this contains real competitor data
                    for key, value in enhanced_recommendation[competitive_analysis_key].items():
                        if (isinstance(value, dict) and 
                            value.get('intelligence_source') in ['direct_competitor_content_analysis', 'rag_competitor_analysis']):
                            has_real_competitor_data = True
                            break
                    
                    # Only add limitation note if this is real data, not fallback
                    if has_real_competitor_data:
                        enhanced_recommendation[competitive_analysis_key]['📋 COMPETITIVE ANALYSIS LIMITATION'] = competitive_analysis_note
                    
                    # BULLETPROOF: Skip individual competitor exports if no meaningful data
                    filtered_competitive_analysis = {}
                    for key, value in enhanced_recommendation[competitive_analysis_key].items():
                        # Keep limitation notices and status info
                        if key.startswith('📋') or key.startswith('🚨') or key in ['status', 'message', 'recommendation']:
                            filtered_competitive_analysis[key] = value
                        # Only include competitor-specific analysis if it has substantial data
                        elif isinstance(value, dict) and (
                            value.get('intelligence_source') in ['direct_competitor_content_analysis', 'rag_competitor_analysis'] or
                            value.get('overview', '').count('post') > 0 or
                            len(str(value)) > 100  # Has substantial content
                        ):
                            filtered_competitive_analysis[key] = value
                        # Skip competitors with minimal/no data
                        elif isinstance(value, dict) and (
                            'analysis_failed' in str(value) or
                            'insufficient data' in str(value) or
                            len(str(value)) < 50
                        ):
                            logger.info(f"🚫 Skipping export for competitor {key} - insufficient data")
                            continue
                        else:
                            filtered_competitive_analysis[key] = value
                    
                    enhanced_recommendation[competitive_analysis_key] = filtered_competitive_analysis
            elif not has_real_competitor_data:  # Only create fallback if no real data was found
                # Create competitive_analysis structure with actual competitor usernames
                competitive_analysis_fallback = {}
                
                # Use actual competitor usernames if available
                if competitor_usernames:
                    for competitor in competitor_usernames:
                        competitive_analysis_fallback[competitor] = {
                            "overview": f"Limited data available for competitor @{competitor}",
                            "intelligence_source": "limited_data_framework",
                            "data_quality": "limited",
                            "note": f"Individual competitor analysis for {competitor} requires additional data collection",
                            "status": "monitoring_required",
                            "strategic_priority": "enhanced_data_collection"
                        }
                else:
                    # Fallback if no competitor usernames available
                    competitive_analysis_fallback['strategic_competitor_analysis'] = {
                        "overview": "Competitive analysis framework active with limited data",
                        "intelligence_source": "strategic_framework", 
                        "data_quality": "limited",
                        "note": "Individual competitor analysis requires additional data collection",
                        "status": "monitoring_required"
                    }
                
                # Use a consistent key name
                enhanced_recommendation['competitive_analysis'] = competitive_analysis_fallback
                
                # Add general limitation note
                enhanced_recommendation['competitive_analysis']['📋 COMPETITIVE ANALYSIS LIMITATION'] = competitive_analysis_note
                enhanced_recommendation['competitive_analysis']['status'] = 'limited_data_available'
            
            # Add metadata about limitations
            enhanced_recommendation['metadata'].update({
                'data_limitation_notice': header_message,
                'limitation_message': limitation_message,
                'approach_used': approach_used,
                'personalization_level': 'low' if approach_used == 'gemini_only_posting_style' else 'medium',
                'accuracy_note': f"Recommendation accuracy will improve significantly once @{primary_username} has posting history",
                'primary_username': primary_username,
                'platform': platform,
                'account_type': account_type,
                'timestamp': datetime.now().isoformat()
            })
            
            logger.info(f"✅ Enhanced warning headers added successfully for @{primary_username}")
            return enhanced_recommendation
            
        except Exception as e:
            logger.error(f"❌ Error adding warning headers for @{primary_username}: {str(e)}")
            # Return original recommendation if header addition fails
            return recommendation if recommendation else {
                'strategic_recommendations': {
                    '🚨 ERROR': f'Could not add proper headers for @{primary_username}. Recommendations may have data limitations.'
                }
            }
    
    def _battle_test_competitor_data_approach(self, primary_username: str, secondary_usernames: List[str],
                                            platform: str, account_type: str, posting_style: str, 
                                            info_json_data: Dict) -> Dict:
        """
        ENHANCED: Battle-test for ANY available competitor data and use it as primary data.
        Exhaustively search for competitor data and treat it as primary user data for RAG.
        
        Returns:
{{ ... }}
            Dictionary with success status and recommendation data
        """
        logger.info(f"🔍 BATTLE TESTING: Exhaustive competitor data search for {primary_username}")
        
        if not secondary_usernames:
            logger.warning(f"❌ BATTLE TEST FAILED: No competitor usernames provided for {primary_username}")
            return {"success": False, "reason": "no_competitors", "battle_test_results": "no_competitors_provided"}
        
        # STAGE 1A: Check vector database for ANY competitor data
        available_competitors_vector = self._exhaustive_vector_competitor_check(secondary_usernames, platform)
        
        # STAGE 1B: Check R2 storage for ANY competitor data
        available_competitors_r2 = self._exhaustive_r2_competitor_check(secondary_usernames, platform)
        
        # STAGE 1C: Combine all available competitor data sources
        all_available_competitors = list(set(available_competitors_vector + available_competitors_r2))
        
        if not all_available_competitors:
            logger.warning(f"❌ BATTLE TEST COMPLETE: No competitor data found in any source")
            return {
                "success": False, 
                "reason": "no_competitor_data_after_battle_test",
                "battle_test_results": {
                    "vector_db_competitors": available_competitors_vector,
                    "r2_storage_competitors": available_competitors_r2,
                    "total_found": 0
                }
            }
        
        logger.info(f"✅ BATTLE TEST SUCCESS: Found competitor data for {len(all_available_competitors)} competitors")
        logger.info(f"📊 Available competitors: {all_available_competitors}")
        
        try:
            # CRITICAL: Treat competitor data as PRIMARY USER DATA for enhanced personalization
            logger.info(f"🎯 TREATING COMPETITOR DATA AS PRIMARY USER DATA for enhanced personalization")
            
            # Create enhanced query that treats competitor data as user's own data
            enhanced_query = self._generate_competitor_as_primary_query(
                primary_username, platform, account_type, posting_style, info_json_data
            )
            
            # Generate recommendations using competitor data AS IF it's the primary user's data
            recommendation = self.rag.generate_recommendation(
                primary_username=primary_username,  # Keep original username for identification
                secondary_usernames=all_available_competitors,  # Use competitor data
                query=enhanced_query,
                n_context=5,  # Increase context for better analysis
                is_branding=(account_type == "brand"),
                platform=platform
            )
            
            # Add enhanced metadata about the battle-testing approach
            recommendation['metadata'] = {
                'approach': 'competitor_as_primary_data',
                'competitors_used': all_available_competitors,
                'battle_test_results': {
                    'vector_db_competitors': available_competitors_vector,
                    'r2_storage_competitors': available_competitors_r2,
                    'total_sources_checked': 2,
                    'data_treatment': 'competitor_data_treated_as_primary_user_data'
                },
                'personalization_warning': (
                    f"🔥 HYPER-PERSONALIZED STRATEGY GENERATED! "
                    f"Account {primary_username} has no historical data (new/private account). "
                    f"We analyzed your competitors' successful strategies and adapted them for your unique positioning. "
                    f"This gives you insider intelligence to outperform your competition from day one! "
                    f"Start posting publicly to get authentic personalized recommendations."
                )
            }
            
            return {"success": True, "recommendation": recommendation}
            
        except Exception as e:
            logger.error(f"❌ Error in competitor-as-primary data approach: {str(e)}")
            return {
                "success": False, 
                "reason": "competitor_processing_error", 
                "error": str(e),
                "battle_test_results": {
                    "competitors_found": all_available_competitors,
                    "processing_failed": True
                }
            }
    
    def _generate_gemini_only_recommendation(self, primary_username: str, platform: str, 
                                           account_type: str, posting_style: str, info_json_data: Dict) -> Dict:
        """
        ENHANCED: Generate recommendations using GEMINI-ONLY (NO RAG) based on posting style.
        
        Returns:
            Structured recommendation dictionary
        """
        logger.info(f"📝 GEMINI-ONLY GENERATION: Creating recommendations for {primary_username}")
        
        # Create enhanced prompt for Gemini-only generation
        prompt = self._create_enhanced_gemini_prompt(primary_username, platform, account_type, posting_style, info_json_data)
        
        try:
            # Use Gemini directly (NO RAG)
            response = self.rag.generative_model.generate_content(prompt)
            
            # Parse the response into structured format
            recommendation = self._parse_gemini_only_response(response.text, platform, account_type)
            
            # Add enhanced metadata about the approach used
            recommendation['metadata'] = {
                'approach': 'gemini_only_posting_style',
                'no_rag_used': True,
                'posting_style_used': posting_style,
                'data_limitation_message': (
                    f"Recommendations generated using posting style guidelines only. "
                    f"Account {primary_username} has no available data and no competitor data was accessible. "
                    f"These are strategic recommendations based on your stated posting style preferences."
                ),
                'info_json_data_available': info_json_data is not None
            }
            
            return recommendation
            
        except Exception as e:
            logger.error(f"❌ Error in Gemini-only generation: {str(e)}")
            return self._create_emergency_fallback_recommendation(primary_username, platform, account_type, posting_style)
    
    def _create_enhanced_gemini_prompt(self, primary_username: str, platform: str, 
                                     account_type: str, posting_style: str, info_json_data: Dict) -> str:
        """
        ENHANCED: Create comprehensive prompt for Gemini-only generation.
        
        Returns:
            Formatted prompt string for maximum personalization
        """
        prompt = f"""
        You are an expert social media strategist and market analyst creating comprehensive recommendations 
        for @{primary_username}, a {account_type} account on {platform}.

        CRITICAL CONTEXT:
        - Account: @{primary_username}
        - Platform: {platform}
        - Account Type: {account_type}
        - Status: New account with no historical data
        - Posting Style: "{posting_style}"

        STRATEGIC ANALYSIS REQUIRED:
        Based on the posting style "{posting_style}", you must act as both:
        1. Account Management Strategist (for branding accounts)
        2. Personal Brand Consultant (for personal accounts)
        
        """
        
        if account_type.lower() == "brand" or account_type.lower() == "branding":
            prompt += f"""
            BRAND ACCOUNT STRATEGY:
            As a market strategist and account management expert, analyze the posting style "{posting_style}" 
            and create a comprehensive brand strategy that includes:
            
            - Market positioning based on the posting style
            - Content themes that align with "{posting_style}"
            - Competitive advantages this posting style can create
            - Audience engagement strategies
            - Growth tactics specific to {platform}
            - Brand voice and tone guidelines
            - Content calendar recommendations
            """
        else:
            prompt += f"""
            PERSONAL ACCOUNT STRATEGY:
            As a personal brand consultant, analyze the posting style "{posting_style}" 
            and create a comprehensive personal branding strategy that includes:
            
            - Personal brand positioning based on "{posting_style}"
            - Authentic content themes that reflect this posting style
            - Personal growth opportunities
            - Community building strategies
            - Engagement tactics for {platform}
            - Personal voice development
            - Content consistency guidelines
            """
        
        if info_json_data:
            prompt += f"\n\nADDITIONAL ACCOUNT CONTEXT:\n"
            for key, value in info_json_data.items():
                if key not in ['username', 'accountType', 'account_type', 'postingStyle', 'posting_style']:
                    prompt += f"- {key}: {value}\n"
        
        prompt += f"""
        
        OUTPUT REQUIREMENTS:
        Generate a comprehensive content strategy in this EXACT JSON structure:
        
        {{
            "competitive_intelligence": {{
                "account_analysis": "Analysis of {primary_username}'s positioning potential",
                "growth_opportunities": "Specific opportunities based on posting style",
                "strategic_positioning": "How to position based on '{posting_style}'"
            }},
            "tactical_recommendations": [
                {{
                    "category": "Content Strategy",
                    "recommendation": "Specific recommendation",
                    "priority": "High/Medium/Low",
                    "implementation": "How to implement"
                }}
            ],
            "content_calendar": {{
                "posting_frequency": "Recommended frequency",
                "content_themes": ["theme1", "theme2", "theme3"],
                "optimal_times": "Best posting times"
            }},
            "next_post_prediction": {{
                "caption": "Specific caption for first post",
                "hashtags": ["hashtag1", "hashtag2", "hashtag3"],
                "call_to_action": "Specific CTA",
                "image_prompt": "Description for visual content"
            }},
            "engagement_strategy": {{
                "tactics": ["tactic1", "tactic2"],
                "community_building": "Approach to building community",
                "growth_methods": ["method1", "method2"]
            }}
        }}
        
        CRITICAL: Base ALL recommendations on the posting style "{posting_style}" and ensure 
        they are specific, actionable, and tailored to {platform} best practices.
        """
        
        return prompt
    
    def _get_default_posting_style(self, account_type: str, platform: str) -> str:
        """Get default posting style if none provided."""
        style_config = GLOBAL_POSTING_STYLES.get(account_type, {}).get(platform, {})
        return style_config.get('posting_style', 'Professional content creation with consistent engagement')
    
    def _parse_gemini_only_response(self, response_text: str, platform: str, account_type: str) -> Dict:
        """
        ENHANCED: Parse Gemini-only response into structured format.
        
        Returns:
            Structured recommendation dictionary
        """
        # Try to parse JSON first
        try:
            # Look for JSON content in the response
            import re
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                parsed = json.loads(json_match.group())
                return parsed
        except json.JSONDecodeError:
            pass
        
        # If JSON parsing fails, extract structured data from text
        try:
            return self._extract_structured_data_from_text(response_text, platform, account_type)
        except Exception as e:
            logger.error(f"❌ Error parsing Gemini response: {str(e)}")
            return self._create_minimal_structured_recommendation(response_text, platform, account_type)
    
    def _extract_structured_data_from_text(self, response_text: str, platform: str, account_type: str) -> Dict:
        """Extract structured data from unstructured text response."""
        # Basic extraction logic for when JSON parsing fails
        lines = response_text.split('\n')
        
        # Try to find key sections
        competitive_intel = ""
        recommendations = []
        next_post = {}
        
        current_section = None
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Identify sections
            if any(keyword in line.lower() for keyword in ['competitive', 'analysis', 'positioning']):
                current_section = 'competitive'
                competitive_intel += line + " "
            elif any(keyword in line.lower() for keyword in ['recommendation', 'strategy', 'tactical']):
                current_section = 'recommendations'
                if line and not line.startswith('#'):
                    recommendations.append({
                        "category": "Content Strategy",
                        "recommendation": line,
                        "priority": "High"
                    })
            elif any(keyword in line.lower() for keyword in ['next post', 'first post', 'caption']):
                current_section = 'next_post'
                if 'caption' in line.lower():
                    next_post['caption'] = line.replace('caption:', '').replace('Caption:', '').strip()
            elif current_section == 'competitive':
                competitive_intel += line + " "
            elif current_section == 'recommendations' and line and not line.startswith('#'):
                recommendations.append({
                    "category": "Content Strategy",
                    "recommendation": line,
                    "priority": "Medium"
                })
        
        return {
            "competitive_intelligence": {
                "account_analysis": competitive_intel[:200] if competitive_intel else f"New {account_type} account on {platform} with growth potential",
                "growth_opportunities": "Content-based growth through consistent posting and engagement",
                "strategic_positioning": f"Position as authentic {account_type} voice on {platform}"
            },
            "tactical_recommendations": recommendations if recommendations else [
                {
                    "category": "Content Strategy",
                    "recommendation": "Focus on consistent, high-quality content creation",
                    "priority": "High"
                }
            ],
            "next_post_prediction": next_post if next_post else {
                "caption": f"Welcome to our {platform} presence! Excited to share our journey with you.",
                "hashtags": [f"#{account_type}", f"#{platform}", "#newaccount"],
                "call_to_action": "Follow for updates!",
                "image_prompt": f"Professional introduction image for {platform}"
            }
        }
    
    def _exhaustive_vector_competitor_check(self, secondary_usernames: List[str], platform: str) -> List[str]:
        """
        ENHANCED: Exhaustively check vector database for ANY competitor data.
        
        Returns:
            List of competitor usernames with available data in vector database
        """
        available_competitors = []
        
        for competitor in secondary_usernames:
            try:
                # Multiple query strategies to find ANY data
                query_strategies = [
                    f"content from {competitor}",
                    f"{competitor} posts",
                    f"{competitor} {platform}",
                    f"username {competitor}",
                    competitor  # Direct username search
                ]
                
                for query_strategy in query_strategies:
                    try:
                        results = self.vector_db.query_similar(
                            query=query_strategy,
                            n_results=1,
                            filter_username=competitor
                        )
                        
                        if results and len(results) > 0:
                            available_competitors.append(competitor)
                            logger.info(f"✅ VECTOR DB: Found data for competitor {competitor} using query: {query_strategy}")
                            break  # Found data, move to next competitor
                            
                    except Exception as query_e:
                        logger.debug(f"Query strategy '{query_strategy}' failed for {competitor}: {str(query_e)}")
                        continue
                    
                if competitor not in available_competitors:
                    logger.warning(f"❌ VECTOR DB: No data found for competitor: {competitor}")
                    
            except Exception as e:
                logger.error(f"❌ Error checking vector database for competitor {competitor}: {str(e)}")
                continue
        
        logger.info(f"📊 VECTOR DB BATTLE TEST: Found {len(available_competitors)}/{len(secondary_usernames)} competitors with data")
        return available_competitors
    
    def _exhaustive_r2_competitor_check(self, secondary_usernames: List[str], platform: str) -> List[str]:
        """
        ENHANCED: Exhaustively check R2 storage for ANY competitor data.
        
        Returns:
            List of competitor usernames with available data in R2 storage
        """
        available_competitors = []
        
        # Use the main data retriever if available, otherwise fall back to R2StorageManager
        data_source = None
        if hasattr(self, 'data_retriever') and self.data_retriever:
            data_source = self.data_retriever
            logger.info("Using main data retriever for R2 competitor check (structuredb bucket)")
        else:
            try:
                from r2_storage_manager import R2StorageManager
                data_source = R2StorageManager()
                logger.info("Using R2StorageManager for competitor check (tasks bucket)")
            except Exception as e:
                logger.warning(f"❌ R2 storage not accessible for competitor check: {str(e)}")
                return available_competitors
        
        for competitor in secondary_usernames:
            try:
                # Check multiple possible paths in R2 storage
                possible_paths = [
                    f"processed_data/{platform}/{competitor}/",
                    f"raw_data/{platform}/{competitor}/",
                    f"AccountInfo/{platform}/{competitor}/",
                    f"ProfileInfo/{platform}/{competitor}/",
                    f"competitive_analysis/{platform}/{competitor}/",
                    # NEW: Check primary username folders (where Instagram scraper saves competitor data)
                    f"{platform}/fahdi1999/{competitor}.json",  # Specific known primary username
                ]
                
                for path in possible_paths:
                    try:
                        # Handle different data source types
                        if hasattr(data_source, 'list_objects'):
                            # R2StorageManager method
                            objects = data_source.list_objects(prefix=path)
                            if objects and len(objects) > 0:
                                available_competitors.append(competitor)
                                logger.info(f"✅ R2 STORAGE: Found data for competitor {competitor} in path: {path}")
                                break  # Found data, move to next competitor
                        elif hasattr(data_source, 'get_json_data'):
                            # DataRetriever method - try to get the file directly
                            if path.endswith('.json'):
                                try:
                                    data = data_source.get_json_data(path)
                                    if data:
                                        available_competitors.append(competitor)
                                        logger.info(f"✅ R2 DATA RETRIEVER: Found data for competitor {competitor} at: {path}")
                                        break
                                except:
                                    continue
                            else:
                                continue
                        else:
                            continue
                            
                    except Exception as path_e:
                        logger.debug(f"R2 path check failed for {path}: {str(path_e)}")
                        continue
                
                if competitor not in available_competitors:
                    logger.warning(f"❌ R2 STORAGE: No data found for competitor: {competitor}")
                    
            except Exception as e:
                logger.error(f"❌ Error checking R2 storage for competitor {competitor}: {str(e)}")
                continue
        
        logger.info(f"📊 R2 STORAGE BATTLE TEST: Found {len(available_competitors)}/{len(secondary_usernames)} competitors with data")
        return available_competitors
    
    def _generate_competitor_as_primary_query(self, primary_username: str, platform: str, 
                                            account_type: str, posting_style: str, info_json_data: Dict) -> str:
        """
        ENHANCED: Generate query that treats competitor data as primary user data.
        
        Returns:
            Enhanced query string for competitor-as-primary analysis
        """
        base_query = f"""
        You are analyzing data for @{primary_username}, a {account_type} account on {platform}.
        
        CRITICAL CONTEXT: This is a new or private account with no historical data. However, we have analyzed 
        their competitive landscape and market positioning. Use this competitive intelligence AS IF it represents 
        the user's own strategic positioning and content opportunities.
        
        Account Details:
        - Username: {primary_username}
        - Platform: {platform}
        - Account Type: {account_type}
        - Status: New/Private account (zero historical data)
        """
        
        if posting_style:
            base_query += f"\n- Posting Style Preference: {posting_style}"
        
        if info_json_data:
            if 'competitors' in info_json_data:
                base_query += f"\n- Known Competitors: {info_json_data.get('competitors', [])}"
            if 'target_audience' in info_json_data:
                base_query += f"\n- Target Audience: {info_json_data.get('target_audience', 'Not specified')}"
        
        base_query += f"""
        
        ANALYSIS APPROACH:
        Treat the analyzed competitive data as strategic insights for {primary_username}'s positioning. 
        Generate hyper-personalized recommendations that give {primary_username} competitive advantages 
        based on market gaps and opportunities identified in the competitive landscape.
        
        Focus on:
        1. Competitive positioning strategies
        2. Content gaps {primary_username} can exploit
        3. Audience engagement opportunities
        4. Unique value propositions for {primary_username}
        5. Immediate actionable content strategies
        
        Generate comprehensive recommendations as if {primary_username} has strategic insights 
        into their competitive landscape and is ready to outperform competitors from day one.
        """
        
        return base_query
    
    def _enhanced_posting_style_approach(self, primary_username: str, platform: str, 
                                       account_type: str, posting_style: str, info_json_data: Dict) -> Dict:
        """
        ENHANCED: Generate recommendations using Gemini-only approach with posting style.
        NO RAG - Direct Gemini API with enhanced prompting.
        
        Returns:
            Dictionary with recommendation data
        """
        logger.info(f"🌍 ENHANCED POSTING STYLE APPROACH: Using Gemini-only for {primary_username}")
        
        if not posting_style:
            logger.warning(f"❌ No posting style provided, using default for {account_type} on {platform}")
            posting_style = self._get_default_posting_style(account_type, platform)
        
        # Generate recommendations using GEMINI-ONLY (NO RAG)
        recommendation = self._generate_gemini_only_recommendation(
            primary_username, platform, account_type, posting_style, info_json_data
        )
        
        return {"success": True, "recommendation": recommendation}
    
    def _generate_from_global_style(self, primary_username: str, platform: str, 
                                  account_type: str, style_config: Dict) -> Dict:
        """
        Generate recommendations using global posting style configuration.
        
        Returns:
            Structured recommendation dictionary
        """
        logger.info(f"📝 Generating recommendations from global style for {primary_username}")
        
        # Create a specialized prompt for global style approach
        prompt = self._create_global_style_prompt(primary_username, platform, account_type, style_config)
        
        try:
            # Use RAG to generate based on global style
            response = self.rag.generative_model.generate_content(prompt)
            
            # Parse the response into structured format
            recommendation = self._parse_global_style_response(response.text, platform, account_type)
            
            # Add metadata about the approach used
            recommendation['metadata'] = {
                'approach': 'global_style',
                'style_used': style_config,
                'data_limitation_message': f"Recommendations generated using global posting style due to no available data for {primary_username}. This is a new or private account with no historical data."
            }
            
            return recommendation
            
        except Exception as e:
            logger.error(f"❌ Error generating from global style: {str(e)}")
            return self._create_fallback_recommendation(primary_username, platform, account_type, style_config)
    
    def _create_global_style_prompt(self, primary_username: str, platform: str, 
                                  account_type: str, style_config: Dict) -> str:
        """
        Create a prompt for global style-based generation.
        
        Returns:
            Formatted prompt string
        """
        return f"""
        You are an expert social media strategist creating recommendations for a new {platform} {account_type} account @{primary_username}.

        Account Information:
        - Username: {primary_username}
        - Platform: {platform}
        - Account Type: {account_type}
        - Status: New account with no historical data

        Global Posting Style Guidelines:
        - Posting Style: {style_config.get('posting_style', 'Professional content creation')}
        - Content Themes: {', '.join(style_config.get('content_themes', []))}
        - Tone: {style_config.get('tone', 'professional')}
        - Hashtag Strategy: {style_config.get('hashtag_strategy', 'relevant hashtags')}
        - Engagement Style: {style_config.get('engagement_style', 'active engagement')}

        Please provide a comprehensive content strategy including:
        1. Competitive Intelligence (market positioning for new account)
        2. Tactical Recommendations (specific content suggestions)
        3. Content Calendar (posting schedule and themes)
        4. Engagement Strategy (growth tactics)
        5. Next Post Prediction (immediate content suggestions)

        Format your response as structured JSON with all the standard modules.
        """
    
    def _parse_global_style_response(self, response_text: str, platform: str, 
                                   account_type: str) -> Dict:
        """
        Parse global style response into structured format.
        
        Returns:
            Structured recommendation dictionary
        """
        # Try to parse JSON first
        try:
            parsed = json.loads(response_text)
            return parsed
        except json.JSONDecodeError:
            pass
        
        # If JSON parsing fails, use the RAG's existing parsing logic
        try:
            return self.rag._parse_unified_response(response_text, platform, account_type == "brand")
        except Exception as e:
            logger.error(f"❌ Error parsing global style response: {str(e)}")
            return self._create_minimal_recommendation(response_text, platform, account_type)
    
    def _create_fallback_recommendation(self, primary_username: str, platform: str, 
                                      account_type: str, style_config: Dict) -> Dict:
        """
        Create a fallback recommendation when all else fails.
        
        Returns:
            Basic recommendation structure
        """
        logger.info(f"🔄 Creating fallback recommendation for {primary_username}")
        
        return {
            "competitive_intelligence": {
                "market_positioning": f"New {account_type} account on {platform} with growth potential",
                "competitive_advantages": ["Fresh start", "Opportunity for authentic brand building", "Clean slate for content strategy"],
                "threat_assessment": "Low immediate threats due to new account status"
            },
            "tactical_recommendations": [
                {
                    "category": "Content Strategy",
                    "recommendation": f"Focus on {style_config.get('posting_style', 'consistent content creation')}",
                    "priority": "High",
                    "implementation": "Start with introductory posts and gradually build content library"
                },
                {
                    "category": "Engagement",
                    "recommendation": f"Implement {style_config.get('engagement_style', 'active engagement')} strategy",
                    "priority": "High",
                    "implementation": "Engage with relevant accounts and communities in your niche"
                }
            ],
            "content_calendar": {
                "posting_frequency": "3-4 times per week initially",
                "content_themes": style_config.get('content_themes', ['general content']),
                "optimal_times": "Peak engagement hours for your target audience"
            },
            "next_post_prediction": {
                "suggested_content": f"Introduction post for new {account_type} account",
                "content_type": "Introduction",
                "caption": f"Welcome to our new {platform} presence! Stay tuned for {', '.join(style_config.get('content_themes', ['great content']))}.",
                "hashtags": ["#new", f"#{account_type}", f"#{platform}"],
                "call_to_action": "Follow for updates!",
                "image_prompt": f"Professional {account_type} introduction image for {platform}"
            },
            "metadata": {
                "approach": "fallback",
                "style_used": style_config,
                "data_limitation_message": f"Basic recommendations generated for new {account_type} account {primary_username} due to limited data availability."
            }
        }
    
    def _create_minimal_recommendation(self, response_text: str, platform: str, 
                                     account_type: str) -> Dict:
        """
        Create minimal recommendation structure from raw response.
        
        Returns:
            Minimal recommendation dictionary
        """
        return {
            "competitive_intelligence": {
                "market_positioning": f"New {account_type} account on {platform}",
                "analysis": response_text[:500] + "..." if len(response_text) > 500 else response_text
            },
            "tactical_recommendations": [
                {
                    "category": "Content Strategy",
                    "recommendation": "Focus on consistent, high-quality content creation",
                    "priority": "High"
                }
            ],
            "next_post_prediction": {
                "suggested_content": "Introduction or welcome post",
                "content_type": "Introduction",
                "caption": f"Welcome to our {platform} presence!",
                "hashtags": [f"#{account_type}", f"#{platform}"],
                "call_to_action": "Follow for updates!",
                "image_prompt": f"Professional introduction image for {platform}"
            }
        }
    
    def _create_emergency_fallback_recommendation(self, primary_username: str, platform: str, 
                                                account_type: str, posting_style: str) -> Dict:
        """
        ENHANCED: Create emergency fallback when all generation methods fail.
        
        Returns:
            Basic but complete recommendation structure
        """
        logger.info(f"🚨 EMERGENCY FALLBACK: Creating basic recommendation for {primary_username}")
        
        # Extract key themes from posting style if available
        posting_themes = self._extract_posting_themes(posting_style) if posting_style else []
        
        return {
            "competitive_intelligence": {
                "account_analysis": f"New {account_type} account @{primary_username} on {platform} starting content journey",
                "growth_opportunities": [
                    "Establish consistent posting schedule",
                    "Build authentic audience engagement",
                    "Develop unique content voice",
                    "Leverage platform-specific features"
                ],
                "strategic_positioning": f"Position as authentic {account_type} voice based on: {posting_style}" if posting_style else f"Develop authentic {account_type} positioning on {platform}"
            },
            "tactical_recommendations": [
                {
                    "category": "Content Strategy",
                    "recommendation": f"Start with introduction posts that reflect your posting style: {posting_style}" if posting_style else "Begin with authentic introduction content",
                    "priority": "High",
                    "implementation": "Create 3-5 initial posts to establish your presence"
                },
                {
                    "category": "Engagement",
                    "recommendation": "Engage authentically with your target audience and relevant accounts",
                    "priority": "High",
                    "implementation": "Spend 15-20 minutes daily engaging with relevant content"
                },
                {
                    "category": "Growth",
                    "recommendation": "Maintain consistent posting schedule to build momentum",
                    "priority": "Medium",
                    "implementation": f"Post 3-4 times per week initially on {platform}"
                }
            ],
            "content_calendar": {
                "posting_frequency": "3-4 times per week initially",
                "content_themes": posting_themes if posting_themes else ["introduction", "value content", "engagement"],
                "optimal_times": f"Peak engagement hours for {platform} audience"
            },
            "next_post_prediction": {
                "caption": f"Welcome to our {platform}! {posting_style.split('.')[0] if posting_style else 'Excited to share our journey with you'}.",
                "hashtags": [f"#{account_type}", f"#{platform}", "#newaccount"],
                "call_to_action": "Follow for updates and engaging content!",
                "image_prompt": f"Professional, welcoming introduction image suitable for {account_type} account on {platform}"
            },
            "engagement_strategy": {
                "tactics": ["authentic commenting", "story engagement", "community participation"],
                "community_building": "Focus on building genuine connections through consistent value delivery",
                "growth_methods": ["consistent posting", "authentic engagement", "value-driven content"]
            },
            "metadata": {
                'approach': 'emergency_fallback',
                'posting_style_used': posting_style,
                'generation_method': 'rule_based_fallback',
                'data_limitation_message': (
                    f"Basic strategic recommendations generated for {primary_username}. "
                    f"This is a new account with limited data. Start posting to get personalized recommendations."
                )
            }
        }
    
    def _extract_posting_themes(self, posting_style: str) -> List[str]:
        """Extract content themes from posting style description."""
        if not posting_style:
            return []
        
        # Common theme indicators
        theme_keywords = {
            'product': ['product', 'showcase', 'review', 'launch'],
            'lifestyle': ['lifestyle', 'daily', 'personal', 'life'],
            'educational': ['educational', 'tutorial', 'how-to', 'tips'],
            'behind-scenes': ['behind', 'process', 'making', 'journey'],
            'industry': ['industry', 'professional', 'business', 'market'],
            'community': ['community', 'audience', 'engagement', 'social']
        }
        
        posting_lower = posting_style.lower()
        themes = []
        
        for theme, keywords in theme_keywords.items():
            if any(keyword in posting_lower for keyword in keywords):
                themes.append(theme)
        
        return themes[:4]  # Return up to 4 themes
    
    def _create_minimal_structured_recommendation(self, response_text: str, platform: str, account_type: str) -> Dict:
        """
        Create minimal but complete recommendation structure from any text.
        
        Returns:
            Minimal recommendation dictionary with all required fields
        """
        return {
            "competitive_intelligence": {
                "account_analysis": f"New {account_type} account on {platform}",
                "analysis_summary": response_text[:300] + "..." if len(response_text) > 300 else response_text
            },
            "tactical_recommendations": [
                {
                    "category": "Content Strategy",
                    "recommendation": "Focus on consistent, high-quality content creation",
                    "priority": "High"
                },
                {
                    "category": "Engagement",
                    "recommendation": "Build authentic connections with your audience",
                    "priority": "High"
                }
            ],
            "next_post_prediction": {
                "caption": f"Welcome to our {platform} presence! Excited to connect with you.",
                "hashtags": [f"#{account_type}", f"#{platform}", "#welcome"],
                "call_to_action": "Follow for updates!",
                "image_prompt": f"Professional introduction image for {platform}"
            }
        }
    
    def _format_enhanced_final_result(self, result: Dict, approach: str, primary_username: str, 
                                    platform: str, account_type: str, posting_style: str) -> Dict:
        """
        ENHANCED: Format the final result with comprehensive structure and metadata.
        
        Returns:
            Enhanced formatted result dictionary
        """
        recommendation = result.get('recommendation', result)
        
        # CRITICAL: Add prominent warning header for zero data accounts
        warning_header = {
            "🚨 IMPORTANT NOTICE - NEW/PRIVATE ACCOUNT DETECTED 🚨": {
                "account_status": f"Account @{primary_username} was identified as a NEW or PRIVATE account",
                "data_limitation": "No historical posting data available for personalized analysis",
                "recommendation_type": "GENERAL STRATEGIC RECOMMENDATIONS (Not Personalized)",
                "explanation": (
                    f"Your account @{primary_username} appears to be new or private, which means we don't have "
                    f"access to your historical posting data. This prevents us from generating powerful "
                    f"personalized recommendations based on your unique content patterns and engagement history."
                ),
                "action_required": {
                    "step_1": "Make your account PUBLIC if it's currently private",
                    "step_2": "Start posting content regularly to build your content history", 
                    "step_3": "Engage with your audience through comments, stories, and interactions",
                    "step_4": "Return in 2-3 weeks for truly personalized recommendations"
                },
                "current_recommendations": (
                    f"The recommendations below are strategic and based on {'competitive analysis' if approach == 'competitor_as_primary' else 'best practices for your posting style'}. "
                    f"They will help you start building engagement, but they are NOT personalized to your unique voice and audience preferences."
                ),
                "future_improvement": (
                    f"Once you have 10-20 public posts with engagement data, we can generate HYPER-PERSONALIZED "
                    f"recommendations that analyze your unique content style, optimal posting times, "
                    f"audience preferences, and engagement patterns for maximum impact."
                )
            }
        }
        
        # Insert warning header at the beginning of recommendation
        formatted_recommendation = {**warning_header, **recommendation}
        
        # Ensure metadata exists
        if 'metadata' not in formatted_recommendation:
            formatted_recommendation['metadata'] = {}
        
        # Add comprehensive enhanced metadata
        formatted_recommendation['metadata'].update({
            'account_status': 'zero_data_enhanced',
            'primary_username': primary_username,
            'platform': platform,
            'account_type': account_type,
            'posting_style': posting_style,
            'generation_approach': approach,
            'timestamp': datetime.now().isoformat(),
            'data_limitation_acknowledged': True,
            'enhancement_level': 'comprehensive_battle_tested',
            'warning_header_displayed': True,
            'personalization_status': 'NOT_PERSONALIZED_NEW_OR_PRIVATE_ACCOUNT'
        })
        
        # Add approach-specific messaging
        if approach == "competitor_as_primary":
            formatted_recommendation['metadata']['success_message'] = (
                f"🔥 COMPETITIVE INTELLIGENCE STRATEGY GENERATED! "
                f"We analyzed your competitive landscape and created strategic recommendations "
                f"to help @{primary_username} compete effectively. However, these are NOT personalized "
                f"to your unique voice - start posting publicly to unlock authentic personalized recommendations!"
            )
            formatted_recommendation['metadata']['limitation_message'] = (
                f"⚠️ IMPORTANT: Strategy based on competitive analysis only. Account @{primary_username} is new/private. "
                f"These recommendations lack personalization to your unique content style and audience preferences."
            )
        elif approach == "gemini_only_posting_style":
            formatted_recommendation['metadata']['success_message'] = (
                f"📋 STRATEGIC RECOMMENDATIONS GENERATED! "
                f"Based on your posting style preferences for @{primary_username}. "
                f"However, these are general guidelines - start posting publicly to get data-driven personalized recommendations!"
            )
            formatted_recommendation['metadata']['limitation_message'] = (
                f"⚠️ IMPORTANT: Recommendations based on posting style guidelines only. Account @{primary_username} "
                f"has no historical data. These lack personalization to your actual content performance and audience engagement patterns."
            )
        
        # CRITICAL: Always export competitor analysis, even if minimal
        if 'competitive_analysis' not in formatted_recommendation:
            formatted_recommendation['competitive_analysis'] = self._create_minimal_competitor_analysis(
                primary_username, platform, approach
            )
        
        logger.info(f"✅ ENHANCED final recommendation with WARNING HEADER generated for {primary_username} using {approach} approach")
        return formatted_recommendation
    
    def _create_minimal_competitor_analysis(self, primary_username: str, platform: str, approach: str) -> Dict:
        """
        ENHANCED: Create minimal competitor analysis section to ensure export completeness.
        
        Returns:
            Minimal competitor analysis dictionary
        """
        if approach == "competitor_as_primary":
            return {
                "🔍 COMPETITIVE ANALYSIS NOTICE": (
                    f"Competitive intelligence integrated into recommendations for @{primary_username}. "
                    f"However, this analysis cannot be personalized to your unique voice and audience "
                    f"because your account appears to be new or private."
                ),
                "competitive_positioning": "Strategic positioning based on competitive landscape analysis (NOT personalized)",
                "market_opportunities": "Identified opportunities through competitive data analysis",
                "personalization_limitation": (
                    f"⚠️ This competitive analysis lacks personalization to @{primary_username}'s unique "
                    f"content style, audience engagement patterns, and brand voice. Start posting publicly "
                    f"to unlock personalized competitive intelligence."
                )
            }
        else:
            return {
                "🔍 COMPETITIVE ANALYSIS NOTICE": (
                    f"⚠️ No competitive analysis available for @{primary_username}. Account appears to be "
                    f"new or private, preventing access to both your historical data and competitive intelligence."
                ),
                "status": "PENDING_DATA_COLLECTION",
                "limitation_explanation": (
                    f"Comprehensive competitor analysis requires your account to have public posting history. "
                    f"Without your content data, we cannot create meaningful competitive comparisons."
                ),
                "action_required": (
                    f"1. Make @{primary_username} public if currently private\n"
                    f"2. Post 10-20 pieces of content with engagement\n"
                    f"3. Return for personalized competitive analysis that compares your performance "
                    f"against competitors in your exact niche"
                )
            }
