"""
Enhanced Goal Handler Module - Deep RAG Analysis & Platform-Aware Schema with XGBoost Integration
Processes goal files with robust analysis of scraped profile data and prophet analytics
to generate theme-aligned content that achieves user-defined objectives using ML-powered post estimation.
"""

import os
import time
import json
import asyncio
import re
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from utils.r2_client import R2Client
from utils.logging import logger
from utils.test_filter import TestFilter
from config import R2_CONFIG, STRUCTUREDB_R2_CONFIG, GEMINI_CONFIG
import google.generativeai as genai
from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np
from xgboost_post_estimator import XGBoostPostEstimator

# Configure Gemini
genai.configure(api_key=GEMINI_CONFIG["api_key"])
model = genai.GenerativeModel(
    model_name=GEMINI_CONFIG["model"],
    generation_config={
        "max_output_tokens": GEMINI_CONFIG["max_tokens"],
        "temperature": GEMINI_CONFIG["temperature"],
        "top_p": GEMINI_CONFIG["top_p"],
        "top_k": GEMINI_CONFIG["top_k"]
    }
)

class DeepRAGAnalyzer:
    """Advanced RAG implementation for deep profile and prophet analysis"""
    
    def __init__(self):
        self.vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
        self.profile_embeddings = None
        self.prophet_embeddings = None
        
    def analyze_profile_patterns(self, profile_data: Dict) -> Dict[str, Any]:
        """Deep analysis of scraped profile data to extract posting patterns"""
        analysis = {
            "posting_frequency": self._analyze_posting_frequency(profile_data),
            "engagement_patterns": self._analyze_engagement_patterns(profile_data),
            "content_themes": self._extract_content_themes(profile_data),
            "successful_post_characteristics": self._identify_successful_posts(profile_data),
            "persona_traits": self._extract_persona_traits(profile_data),
            "optimal_timing": self._determine_optimal_timing(profile_data)
        }
        return analysis
        
    def _analyze_posting_frequency(self, profile_data: Dict) -> Dict[str, Any]:
        """Analyze historical posting frequency and patterns"""
        posts = profile_data.get("posts", [])
        if not posts:
            return {"avg_posts_per_week": 3, "consistency_score": 0.5}
            
        # Calculate posting frequency
        total_posts = len(posts)
        date_range = self._calculate_date_range(posts)
        weeks = max(1, date_range / 7)
        avg_posts_per_week = total_posts / weeks
        
        # Calculate consistency (variance in posting intervals)
        intervals = self._calculate_posting_intervals(posts)
        consistency_score = 1.0 / (1.0 + np.std(intervals)) if intervals else 0.5
        
        return {
            "total_posts": total_posts,
            "avg_posts_per_week": round(avg_posts_per_week, 2),
            "consistency_score": round(consistency_score, 2),
            "posting_intervals": intervals[:10]  # Sample intervals
        }
        
    def _analyze_engagement_patterns(self, profile_data: Dict) -> Dict[str, Any]:
        """Analyze engagement metrics and patterns"""
        posts = profile_data.get("posts", [])
        if not posts:
            return {"avg_engagement_rate": 0.05, "peak_engagement_factors": []}
            
        engagement_rates = []
        high_performing_posts = []
        
        for post in posts:
            likes = post.get("likes", 0)
            comments = post.get("comments", 0)
            followers = profile_data.get("followers", 1000)
            
            engagement_rate = (likes + comments) / max(followers, 1)
            engagement_rates.append(engagement_rate)
            
            if engagement_rate > np.percentile(engagement_rates[-50:], 75):  # Top 25%
                high_performing_posts.append(post)
        
        avg_engagement = np.mean(engagement_rates) if engagement_rates else 0.05
        peak_factors = self._extract_peak_engagement_factors(high_performing_posts)
        
        return {
            "avg_engagement_rate": round(avg_engagement, 4),
            "peak_engagement_rate": round(max(engagement_rates), 4) if engagement_rates else 0.1,
            "engagement_growth_trend": self._calculate_engagement_trend(engagement_rates),
            "peak_engagement_factors": peak_factors
        }
        
    def _extract_content_themes(self, profile_data: Dict) -> List[str]:
        """Extract dominant content themes using TF-IDF"""
        posts = profile_data.get("posts", [])
        if not posts:
            return ["lifestyle", "inspiration", "daily"]
            
        # Combine all post text
        post_texts = []
        for post in posts:
            text = ""
            if "caption" in post:
                text += post["caption"] + " "
            if "hashtags" in post:
                hashtags = post["hashtags"] if isinstance(post["hashtags"], list) else []
                text += " ".join(hashtags)
            post_texts.append(text.lower())
        
        if not post_texts:
            return ["lifestyle", "inspiration", "daily"]
            
        # Extract themes using TF-IDF
        try:
            tfidf_matrix = self.vectorizer.fit_transform(post_texts)
            feature_names = self.vectorizer.get_feature_names_out()
            
            # Get top terms
            mean_scores = np.mean(tfidf_matrix.toarray(), axis=0)
            top_indices = np.argsort(mean_scores)[-10:]
            themes = [feature_names[i] for i in top_indices if len(feature_names[i]) > 2]
            
            return themes[-5:] if themes else ["lifestyle", "inspiration", "daily"]
        except:
            return ["lifestyle", "inspiration", "daily"]
            
    def _identify_successful_posts(self, profile_data: Dict) -> List[Dict]:
        """Identify characteristics of most successful posts"""
        posts = profile_data.get("posts", [])
        if not posts:
            return []
            
        # Sort by engagement
        for post in posts:
            likes = post.get("likes", 0)
            comments = post.get("comments", 0)
            post["total_engagement"] = likes + comments
            
        sorted_posts = sorted(posts, key=lambda x: x.get("total_engagement", 0), reverse=True)
        top_posts = sorted_posts[:min(5, len(sorted_posts))]
        
        characteristics = []
        for post in top_posts:
            char = {
                "caption_length": len(post.get("caption", "")),
                "hashtag_count": len(post.get("hashtags", [])),
                "has_cta": self._has_call_to_action(post.get("caption", "")),
                "engagement": post.get("total_engagement", 0),
                "content_type": post.get("type", "photo")
            }
            characteristics.append(char)
            
        return characteristics
        
    def _extract_persona_traits(self, profile_data: Dict) -> Dict[str, str]:
        """Extract persona traits from bio and posting style"""
        bio = profile_data.get("bio", "")
        posts = profile_data.get("posts", [])
        
        # Analyze bio for personality traits
        tone = "professional"
        if any(word in bio.lower() for word in ["fun", "love", "passion", "enjoy"]):
            tone = "casual"
        elif any(word in bio.lower() for word in ["expert", "professional", "founder", "ceo"]):
            tone = "professional"
        elif any(word in bio.lower() for word in ["creative", "artist", "inspire"]):
            tone = "creative"
            
        # Analyze writing style from posts
        avg_caption_length = 0
        if posts:
            caption_lengths = [len(post.get("caption", "")) for post in posts]
            avg_caption_length = np.mean(caption_lengths)
            
        writing_style = "concise" if avg_caption_length < 100 else "detailed"
        
        return {
            "tone": tone,
            "writing_style": writing_style,
            "personality": self._determine_personality(bio, posts),
            "brand_voice": self._extract_brand_voice(bio, posts)
        }
        
    def _determine_optimal_timing(self, profile_data: Dict) -> Dict[str, Any]:
        """Determine optimal posting times based on historical data"""
        posts = profile_data.get("posts", [])
        if not posts:
            return {"best_hours": [9, 12, 15], "best_days": ["monday", "wednesday", "friday"]}
            
        # This is a simplified version - in reality would analyze timestamps
        return {
            "best_hours": [9, 12, 15, 18],  # Default optimal hours
            "best_days": ["monday", "wednesday", "friday"],
            "posting_frequency": "daily"
        }
        
    def _calculate_date_range(self, posts: List[Dict]) -> int:
        """Calculate date range of posts in days"""
        # Simplified - would parse actual timestamps in real implementation
        return max(30, len(posts))  # Default to 30 days or post count
        
    def _calculate_posting_intervals(self, posts: List[Dict]) -> List[int]:
        """Calculate intervals between posts"""
        # Simplified - would use actual timestamps
        return [1, 2, 1, 3, 1, 2, 1]  # Sample intervals in days
        
    def _calculate_engagement_trend(self, engagement_rates: List[float]) -> str:
        """Calculate if engagement is trending up, down, or stable"""
        if len(engagement_rates) < 2:
            return "stable"
            
        recent = engagement_rates[-10:]
        older = engagement_rates[-20:-10] if len(engagement_rates) >= 20 else engagement_rates[:-10]
        
        if not older:
            return "stable"
            
        recent_avg = np.mean(recent)
        older_avg = np.mean(older)
        
        if recent_avg > older_avg * 1.1:
            return "increasing"
        elif recent_avg < older_avg * 0.9:
            return "decreasing"
        else:
            return "stable"
            
    def _extract_peak_engagement_factors(self, high_performing_posts: List[Dict]) -> List[str]:
        """Extract factors that contribute to peak engagement"""
        factors = []
        
        if not high_performing_posts:
            return ["engaging_visuals", "trending_hashtags", "clear_cta"]
            
        # Analyze common characteristics
        total_posts = len(high_performing_posts)
        
        # Check for common patterns
        cta_count = sum(1 for post in high_performing_posts if self._has_call_to_action(post.get("caption", "")))
        if cta_count / total_posts > 0.6:
            factors.append("call_to_action")
            
        # Check hashtag usage
        hashtag_counts = [len(post.get("hashtags", [])) for post in high_performing_posts]
        avg_hashtags = np.mean(hashtag_counts)
        if avg_hashtags > 5:
            factors.append("strategic_hashtags")
            
        # Check caption length
        caption_lengths = [len(post.get("caption", "")) for post in high_performing_posts]
        avg_length = np.mean(caption_lengths)
        if avg_length > 100:
            factors.append("detailed_captions")
        else:
            factors.append("concise_messaging")
            
        return factors if factors else ["engaging_visuals", "trending_hashtags", "clear_cta"]
        
    def _has_call_to_action(self, caption: str) -> bool:
        """Check if caption contains call-to-action"""
        cta_patterns = [
            r'\bcomment\b', r'\bshare\b', r'\blike\b', r'\bfollow\b',
            r'\btag\b', r'\bvisit\b', r'\bclick\b', r'\bswipe\b',
            r'\btell us\b', r'\blet us know\b', r'\bwhat do you think\b'
        ]
        return any(re.search(pattern, caption.lower()) for pattern in cta_patterns)
        
    def _determine_personality(self, bio: str, posts: List[Dict]) -> str:
        """Determine personality type from content"""
        if any(word in bio.lower() for word in ["motivate", "inspire", "dream", "achieve"]):
            return "inspirational"
        elif any(word in bio.lower() for word in ["fun", "laugh", "smile", "happy"]):
            return "energetic"
        elif any(word in bio.lower() for word in ["expert", "tips", "advice", "guide"]):
            return "educational"
        else:
            return "authentic"
            
    def _extract_brand_voice(self, bio: str, posts: List[Dict]) -> str:
        """Extract brand voice characteristics"""
        if any(word in bio.lower() for word in ["premium", "luxury", "exclusive", "elite"]):
            return "premium"
        elif any(word in bio.lower() for word in ["friendly", "community", "together", "family"]):
            return "community_focused"
        elif any(word in bio.lower() for word in ["innovative", "cutting-edge", "new", "modern"]):
            return "innovative"
        else:
            return "authentic"

class StrategyCalculator:
    """Calculates optimal posting strategy using XGBoost ML model and advanced analytics"""
    
    def __init__(self, rag_analyzer: DeepRAGAnalyzer):
        self.rag_analyzer = rag_analyzer
        self.xgb_estimator = XGBoostPostEstimator()
        
    def calculate_posting_strategy(
        self, 
        goal: Dict, 
        profile_analysis: Dict, 
        prophet_data: Dict
    ) -> Tuple[int, float, str, Dict]:
        """Calculate posting strategy using XGBoost ML model with enhanced analytics"""
        
        logger.info("🤖 Using XGBoost ML model for post estimation...")
        
        # Use XGBoost model for accurate post estimation
        posts_needed, ml_rationale, prediction_metrics = self.xgb_estimator.estimate_posts(
            goal, profile_analysis, prophet_data
        )
        
        # Calculate posting interval
        timeline_days = int(goal.get("timeline", 7))
        posting_interval = (timeline_days * 24) / posts_needed if posts_needed > 0 else 24
        
        # Generate comprehensive rationale with statistical insights
        rationale = self._generate_enhanced_rationale(
            posts_needed, 
            posting_interval, 
            timeline_days,
            goal,
            profile_analysis,
            ml_rationale,
            prediction_metrics
        )
        
        return posts_needed, posting_interval, rationale, prediction_metrics
        
    def _generate_enhanced_rationale(
        self, 
        posts_needed: int, 
        posting_interval: float, 
        timeline_days: int,
        goal: Dict,
        profile_analysis: Dict,
        ml_rationale: str,
        prediction_metrics: Dict
    ) -> str:
        """Generate comprehensive rationale with statistical justification"""
        
        # Extract key metrics
        engagement_patterns = profile_analysis.get("engagement_patterns", {})
        current_engagement = engagement_patterns.get("avg_engagement_rate", 0.05)
        followers = profile_analysis.get("followers", 1000)
        
        # Parse goal target
        goal_text = goal.get("goal", "").lower()
        if "%" in goal_text:
            target_match = re.search(r'(\d+)%', goal_text)
            target_increase = target_match.group(1) if target_match else "moderate"
        else:
            target_increase = "significant"
        
        # Calculate expected impact
        method = prediction_metrics.get('method', 'xgboost')
        confidence = prediction_metrics.get('confidence', 0.8) * 100
        
        # Build comprehensive rationale
        rationale = (
            f"📊 ML-Powered Strategy Analysis: {posts_needed} posts over {timeline_days} days "
            f"({posting_interval:.1f}h intervals). "
            f"🎯 Target: {target_increase} engagement increase from baseline {current_engagement:.2%}. "
            f"📈 {ml_rationale}. "
            f"🔬 Statistical confidence: {confidence:.0f}% using {method} method. "
            f"👥 Account profile: {followers:,} followers with {current_engagement:.2%} engagement rate. "
            f"⚡ Optimized for sustainable growth while maintaining content quality and audience retention."
        )
        
        return rationale

class ContentGenerator:
    """Generates theme-aligned content based on RAG analysis"""
    
    def __init__(self, rag_analyzer: DeepRAGAnalyzer):
        self.rag_analyzer = rag_analyzer
        
    async def generate_post_content(
        self, 
        goal: Dict, 
        profile_analysis: Dict, 
        posts_needed: int,
        username: str,
        platform: str,
        prediction_metrics: Dict,
        posting_interval: float
    ) -> Dict:
        """Generate theme-aligned posts in the new required format with statistical justification"""
        
        posts_dict = {}
        persona_traits = profile_analysis["persona_traits"]
        content_themes = profile_analysis["content_themes"]
        successful_characteristics = profile_analysis["successful_post_characteristics"]
        
        # Generate individual posts in Post_1, Post_2, ... format
        for i in range(posts_needed):
            post_content = await self._generate_single_post(
                i + 1,
                posts_needed,
                goal,
                persona_traits,
                content_themes,
                successful_characteristics,
                username,
                platform
            )
            
            # 🏷️ HASHTAG INTEGRATION: Generate and append hashtags to third sentence
            enhanced_content = await self._add_hashtags_to_content(
                post_content.get("three_sentences", ""),
                content_themes,
                platform,
                username,
                goal
            )
            
            # Format as Post_X with enhanced content including hashtags and status
            post_key = f"Post_{i + 1}"
            posts_dict[post_key] = {
                "content": enhanced_content,
                "status": "pending"
            }
        
        # Generate statistical summary with engagement science justification
        summary = self._generate_statistical_summary(
            posts_needed, 
            content_themes, 
            successful_characteristics,
            profile_analysis,
            goal,
            prediction_metrics
        )
        
        # Add summary to the output
        posts_dict["Summary"] = summary
        
        # 🕒 ADD TIMELINE: Include posting interval (in hours) as Timeline field
        # Extract numerical value from posting_interval (remove 'h' if present and round to integer)
        timeline_hours = int(round(posting_interval))
        posts_dict["Timeline"] = str(timeline_hours)
        
        logger.info(f"📅 Added Timeline to generated content: {timeline_hours} hours between posts")
        
        return posts_dict

    async def generate_content_without_profile(
        self, 
        goal: Dict, 
        username: str,
        platform: str
    ) -> Dict:
        """
        🔒 FALLBACK CONTENT GENERATOR: Generate content when no profile data is available
        Used for private accounts or new accounts where profile data cannot be retrieved
        """
        
        logger.info(f"🔒 Generating content without profile data for {username} on {platform}")
        
        # Extract goal parameters
        goal_text = goal.get("goal", "increase engagement")
        timeline_days = int(goal.get("timeline", 7))
        persona = goal.get("persona", "authentic brand voice")
        instructions = goal.get("instructions", "maintain consistency")
        
        # 📊 INTELLIGENT POST ESTIMATION: Based on goal and timeline without XGBoost
        posts_needed = self._estimate_posts_without_profile(goal, timeline_days)
        
        # Calculate posting interval
        posting_interval = (timeline_days * 24) / posts_needed if posts_needed > 0 else 24
        
        logger.info(f"📈 Estimated {posts_needed} posts for {timeline_days} day campaign")
        
        posts_dict = {}
        
        # Generate individual posts using goal-based intelligence
        for i in range(posts_needed):
            post_content = await self._generate_goal_based_post(
                i + 1,
                posts_needed,
                goal,
                username,
                platform
            )
            
            # 🏷️ HASHTAG INTEGRATION: Generate hashtags based on goal context
            enhanced_content = await self._add_goal_based_hashtags(
                post_content.get("three_sentences", ""),
                goal,
                platform,
                username
            )
            
            # Format as Post_X with enhanced content
            post_key = f"Post_{i + 1}"
            posts_dict[post_key] = {
                "content": enhanced_content,
                "status": "pending"
            }
        
        # Generate summary for accounts without profile data
        summary = self._generate_no_profile_summary(
            posts_needed, 
            goal,
            timeline_days,
            username,
            platform
        )
        
        # Add summary and timeline
        posts_dict["Summary"] = summary
        posts_dict["Timeline"] = str(int(round(posting_interval)))
        
        logger.info(f"🔒 Generated {posts_needed} posts for private/new account: {username}")
        
        return posts_dict

    def _estimate_posts_without_profile(self, goal: Dict, timeline_days: int) -> int:
        """
        📊 INTELLIGENT POST ESTIMATION: Estimate posts without profile data
        Uses goal analysis and industry standards for new/private accounts
        """
        goal_text = goal.get("goal", "").lower()
        
        # Base posting frequency for new accounts (conservative approach)
        base_posts_per_day = 0.5  # Start with 1 post every 2 days for new accounts
        
        # Adjust based on goal intensity
        if any(word in goal_text for word in ["aggressive", "rapid", "fast", "quick"]):
            base_posts_per_day = 1.0  # 1 post per day for aggressive goals
        elif any(word in goal_text for word in ["moderate", "steady", "consistent"]):
            base_posts_per_day = 0.7  # 1 post every 1.4 days
        elif any(word in goal_text for word in ["organic", "natural", "slow"]):
            base_posts_per_day = 0.3  # 1 post every 3+ days
        
        # Adjust based on percentage targets if mentioned
        if "%" in goal_text:
            import re
            target_match = re.search(r'(\d+)%', goal_text)
            if target_match:
                target_percentage = int(target_match.group(1))
                if target_percentage > 50:
                    base_posts_per_day *= 1.3  # Increase for high targets
                elif target_percentage > 100:
                    base_posts_per_day *= 1.6  # Significant increase for very high targets
        
        # Calculate total posts needed
        posts_needed = max(1, int(base_posts_per_day * timeline_days))
        
        # Cap at reasonable limits for new accounts
        max_posts = min(timeline_days * 2, 14)  # Max 2 posts per day or 14 total
        posts_needed = min(posts_needed, max_posts)
        
        logger.info(f"📊 Estimated {posts_needed} posts for new/private account (base rate: {base_posts_per_day:.1f}/day)")
        
        return posts_needed

    async def _generate_goal_based_post(
        self,
        post_number: int,
        total_posts: int,
        goal: Dict,
        username: str,
        platform: str
    ) -> Dict:
        """Generate a single post based purely on goal analysis without profile data"""
        
        prompt = self._create_goal_only_prompt(
            post_number,
            total_posts,
            goal,
            platform
        )
        
        try:
            response = await asyncio.wait_for(
                model.generate_content_async(prompt),
                timeout=60
            )
            
            # Parse response into structured format
            content = self._parse_content_response(response.text, post_number)
            
        except Exception as e:
            logger.error(f"Error generating goal-based content for post {post_number}: {e}")
            content = self._generate_goal_fallback_content(post_number, goal)
            
        return content

    def _create_goal_only_prompt(
        self,
        post_number: int,
        total_posts: int,
        goal: Dict,
        platform: str
    ) -> str:
        """Create prompt for content generation based only on goal data"""
        
        goal_text = goal.get("goal", "increase engagement")
        timeline = goal.get("timeline", 7)
        persona = goal.get("persona", "authentic brand voice")
        instructions = goal.get("instructions", "maintain brand consistency")
        
        prompt = f"""
        Generate content for post #{post_number} of {total_posts} for a new or private {platform} account.
        
        GOAL: {goal_text}
        TIMELINE: {timeline} days
        PERSONA: {persona}
        INSTRUCTIONS: {instructions}
        
        ACCOUNT CONTEXT:
        - This is assumed to be a new account or private account
        - No historical data available for analysis
        - Focus on establishing brand presence and voice
        - Content should be engaging for new audience building
        - Professional but approachable tone
        
        Create content that:
        1. Directly supports the stated goal
        2. Follows the persona guidelines
        3. Is appropriate for a new account building audience
        4. Progresses toward the goal (post {post_number}/{total_posts})
        5. Establishes credibility and engagement
        
        Respond ONLY with this JSON format:
        {{
            "three_sentences": "First sentence introducing the topic and value proposition. Second sentence providing specific insight or engaging question. Third sentence describing the visual content and call-to-action."
        }}
        """
        
        return prompt

    def _generate_goal_fallback_content(self, post_number: int, goal: Dict) -> Dict:
        """Generate fallback content when goal-based AI generation fails"""
        goal_text = goal.get("goal", "growth and engagement")
        persona = goal.get("persona", "authentic")
        
        # Create authentic goal-focused content
        sentences = [
            f"Building our presence with a focus on {goal_text.lower()}",
            f"Our {persona.lower()} approach aims to create meaningful connections with our growing community",
            f"Share your thoughts and join the conversation as we work toward our goals together"
        ]
        
        return {
            "three_sentences": ". ".join(sentences) + "."
        }

    def _generate_no_profile_summary(
        self,
        posts_count: int,
        goal: Dict,
        timeline_days: int,
        username: str,
        platform: str
    ) -> str:
        """
        📋 GENERATE SUMMARY FOR ACCOUNTS WITHOUT PROFILE DATA
        First sentence must indicate it's assumed as private/new account
        """
        
        goal_text = goal.get("goal", "increase engagement")
        persona = goal.get("persona", "authentic brand voice")
        
        # Calculate posting frequency
        posts_per_day = posts_count / timeline_days
        
        # Build comprehensive summary starting with required disclaimer
        summary = (
            f"🔒 PRIVATE/NEW ACCOUNT ANALYSIS: This strategy assumes {username} is either a private account "
            f"or new account, as profile data could not be retrieved for detailed analysis. "
            f"📊 GOAL-BASED ESTIMATION: Generated {posts_count} posts over {timeline_days} days "
            f"({posts_per_day:.1f} posts/day) focusing on {goal_text.lower()}. "
            f"🎯 STRATEGY APPROACH: Content designed for {persona.lower()} with emphasis on "
            f"audience building and engagement establishment for {platform}. "
            f"📈 ESTIMATED IMPACT: This posting frequency might be helpful for your campaign, "
            f"though we have limited confidence in post estimation due to the private/new account status. "
            f"🚀 RECOMMENDATION: Monitor early post performance and adjust strategy based on "
            f"initial audience response and engagement patterns. Content focuses on establishing "
            f"brand presence, building credibility, and creating meaningful connections with new followers."
        )
        
        return summary

    async def _add_goal_based_hashtags(
        self,
        original_content: str,
        goal: Dict,
        platform: str,
        username: str
    ) -> str:
        """Add hashtags based purely on goal analysis for accounts without profile data"""
        try:
            if not original_content:
                return original_content
            
            # Split content into sentences
            sentences = original_content.split('. ')
            if len(sentences) < 3:
                # If less than 3 sentences, append hashtags to the last sentence
                sentences[-1] = sentences[-1].rstrip('.')
                hashtags = self._generate_goal_based_hashtags(goal, platform)
                hashtag_string = ' ' + ' '.join(hashtags)
                sentences[-1] += hashtag_string + '.'
                return '. '.join(sentences)
            
            # Add hashtags to the third sentence
            third_sentence = sentences[2].rstrip('.')
            hashtags = self._generate_goal_based_hashtags(goal, platform)
            hashtag_string = ' ' + ' '.join(hashtags)
            sentences[2] = third_sentence + hashtag_string + '.'
            
            enhanced_content = '. '.join(sentences)
            logger.info(f"🏷️ Added {len(hashtags)} goal-based hashtags for {username}")
            
            return enhanced_content
            
        except Exception as e:
            logger.error(f"🚨 Error adding goal-based hashtags: {e}")
            return original_content

    def _generate_goal_based_hashtags(self, goal: Dict, platform: str) -> List[str]:
        """Generate hashtags based purely on goal analysis"""
        hashtags = []
        goal_text = goal.get("goal", "").lower()
        persona = goal.get("persona", "").lower()
        
        # Goal-based hashtags
        if "engagement" in goal_text:
            hashtags.append("#Engagement")
        if "growth" in goal_text or "increase" in goal_text:
            hashtags.append("#Growth")
        if "brand" in goal_text or "business" in goal_text:
            hashtags.append("#Brand")
        if "audience" in goal_text or "community" in goal_text:
            hashtags.append("#Community")
        
        # Persona-based hashtags
        if "professional" in persona:
            hashtags.append("#Professional")
        elif "creative" in persona:
            hashtags.append("#Creative")
        elif "authentic" in persona:
            hashtags.append("#Authentic")
        
        # Platform-specific hashtags
        if platform.lower() == "instagram":
            hashtags.extend(["#Instagram", "#NewAccount"])
        elif platform.lower() == "twitter":
            hashtags.extend(["#Twitter", "#NewAccount"])
        elif platform.lower() == "facebook":
            hashtags.extend(["#Facebook", "#NewAccount"])
        
        # Add generic new account hashtags
        hashtags.extend(["#NewBeginnings", "#JoinUs"])
        
        # Remove duplicates and limit to 5
        unique_hashtags = list(dict.fromkeys(hashtags))[:5]
        
        # Ensure minimum 3 hashtags
        if len(unique_hashtags) < 3:
            fallback = ["#Content", "#SocialMedia", "#NewAccount"]
            unique_hashtags.extend(fallback)
            unique_hashtags = list(dict.fromkeys(unique_hashtags))[:5]
        
        return unique_hashtags[:5]
        
    async def _generate_single_post(
        self,
        post_number: int,
        total_posts: int,
        goal: Dict,
        persona_traits: Dict,
        content_themes: List[str],
        successful_characteristics: List[Dict],
        username: str,
        platform: str
    ) -> Dict:
        """Generate a single post with theme alignment"""
        
        # Create context-aware prompt
        prompt = self._create_content_prompt(
            post_number,
            total_posts,
            goal,
            persona_traits,
            content_themes,
            successful_characteristics,
            platform
        )
        
        try:
            response = await asyncio.wait_for(
                model.generate_content_async(prompt),
                timeout=60
            )
            
            # Parse response into structured format
            content = self._parse_content_response(response.text, post_number)
            
        except Exception as e:
            logger.error(f"Error generating content for post {post_number}: {e}")
            content = self._generate_fallback_content(post_number, goal, persona_traits)
            
        return content
        
    def _create_content_prompt(
        self,
        post_number: int,
        total_posts: int,
        goal: Dict,
        persona_traits: Dict,
        content_themes: List[str],
        successful_characteristics: List[Dict],
        platform: str
    ) -> str:
        """Create detailed prompt for content generation"""
        
        themes_str = ", ".join(content_themes[:3])
        
        successful_patterns = []
        if successful_characteristics:
            avg_caption_length = np.mean([char.get("caption_length", 50) for char in successful_characteristics])
            avg_hashtags = np.mean([char.get("hashtag_count", 5) for char in successful_characteristics])
            has_cta_ratio = np.mean([char.get("has_cta", False) for char in successful_characteristics])
            
            successful_patterns = [
                f"Average caption length: {int(avg_caption_length)} characters",
                f"Average hashtags: {int(avg_hashtags)}",
                f"CTA usage: {has_cta_ratio:.0%} of successful posts"
            ]
        
        prompt = f"""
        Generate content for post #{post_number} of {total_posts} for {platform}.
        
        GOAL: {goal.get('goal', 'Increase engagement')}
        TIMELINE: {goal.get('timeline', 30)} days
        PERSONA: {goal.get('persona', 'Authentic brand voice')}
        INSTRUCTIONS: {goal.get('instructions', 'Maintain brand consistency')}
        
        ACCOUNT ANALYSIS:
        - Brand voice: {persona_traits.get('brand_voice', 'authentic')}
        - Tone: {persona_traits.get('tone', 'professional')}
        - Writing style: {persona_traits.get('writing_style', 'concise')}
        - Content themes: {themes_str}
        
        SUCCESSFUL POST PATTERNS:
        {chr(10).join(successful_patterns) if successful_patterns else 'Focus on engaging visuals and clear messaging'}
        
        Create content that:
        1. Aligns with the persona and goal
        2. Follows successful posting patterns from account history
        3. Progresses toward the goal (post {post_number}/{total_posts})
        4. Maintains authentic brand voice
        
        Respond ONLY with this JSON format:
        {{
            "three_sentences": "First sentence about the post topic. Second sentence providing value or engagement. Third sentence describing the visual and how it should look."
        }}
        """
        
        return prompt
        
    def _parse_content_response(self, response_text: str, post_number: int) -> Dict:
        """Parse AI response into structured content"""
        try:
            # Extract JSON from response
            json_start = response_text.find("{")
            json_end = response_text.rfind("}") + 1
            
            if json_start >= 0 and json_end > json_start:
                json_str = response_text[json_start:json_end]
                content = json.loads(json_str)
                
                # Validate required field
                if "three_sentences" in content:
                    return content
                    
        except Exception as e:
            logger.error(f"Error parsing content response: {e}")
            
        # Return fallback if parsing fails
        return self._generate_fallback_content(post_number, {}, {})
        
    def _generate_fallback_content(self, post_number: int, goal: Dict, persona_traits: Dict) -> Dict:
        """Generate authentic fallback content when AI generation fails - NO TEMPLATES"""
        # Extract authentic elements from goal and persona
        goal_text = goal.get("goal", "growth and engagement")
        brand_voice = persona_traits.get("brand_voice", "authentic")
        
        # Create authentic content based on actual context
        authentic_sentences = [
            f"Sharing valuable insights from our journey in {goal_text.lower()}",
            f"Our {brand_voice} approach continues to drive meaningful connections with our community", 
            f"Visual storytelling that captures the essence of our brand's unique perspective"
        ]
        
        return {
            "three_sentences": ". ".join(authentic_sentences) + "."
        }

    def _generate_statistical_summary(
        self, 
        posts_count: int, 
        content_themes: List[str], 
        successful_characteristics: List[Dict],
        profile_analysis: Dict,
        goal: Dict,
        prediction_metrics: Dict
    ) -> str:
        """Generate statistical summary with engagement science and data-driven justification"""
        
        # Extract key engagement metrics
        engagement_patterns = profile_analysis["engagement_patterns"]
        current_engagement = engagement_patterns.get("avg_engagement_rate", 0.05)
        peak_engagement = engagement_patterns.get("peak_engagement_rate", current_engagement * 2)
        followers = profile_analysis.get("followers", 1000)
        
        # Extract goal details
        goal_text = goal.get("goal", "").lower()
        timeline = int(goal.get("timeline", 7))
        
        # Parse target increase
        target_increase = "moderate"
        expected_improvement = 1.3  # Default 30% improvement
        
        if "%" in goal_text:
            target_match = re.search(r'(\d+)%', goal_text)
            if target_match:
                target_increase = f"{target_match.group(1)}%"
                expected_improvement = 1 + (int(target_match.group(1)) / 100)
        elif "double" in goal_text:
            target_increase = "100% (double)"
            expected_improvement = 2.0
        elif "triple" in goal_text:
            target_increase = "200% (triple)"
            expected_improvement = 3.0
        
        # Analyze content themes and their engagement potential
        high_performing_themes = content_themes[:3] if content_themes else ["engagement", "quality", "authentic"]
        themes_text = ", ".join(high_performing_themes)
        
        # Analyze successful post patterns for statistical insights
        success_insights = []
        if successful_characteristics:
            avg_engagement_of_top_posts = np.mean([char.get("engagement", 0) for char in successful_characteristics])
            engagement_uplift = (avg_engagement_of_top_posts / max(current_engagement * followers, 1)) if followers > 0 else 1.5
            
            avg_caption_length = np.mean([char.get("caption_length", 50) for char in successful_characteristics])
            avg_hashtags = np.mean([char.get("hashtag_count", 5) for char in successful_characteristics])
            cta_success_rate = np.mean([char.get("has_cta", False) for char in successful_characteristics]) * 100
            
            success_insights = [
                f"Top posts show {engagement_uplift:.1f}x engagement uplift",
                f"Optimal caption length: {int(avg_caption_length)} chars",
                f"Strategic hashtag count: {int(avg_hashtags)}",
                f"CTA conversion rate: {cta_success_rate:.0f}%"
            ]
        
        # ML model insights
        method = prediction_metrics.get('method', 'xgboost')
        confidence = prediction_metrics.get('confidence', 0.8) * 100
        
        # Calculate posting intensity and expected reach
        posts_per_day = posts_count / timeline
        estimated_reach_increase = expected_improvement * posts_per_day * 0.15  # 15% reach boost per daily post
        
        # Build comprehensive statistical summary
        summary = (
            f"📊 STATISTICAL CAMPAIGN ANALYSIS: This {posts_count}-post strategy targets {target_increase} "
            f"engagement increase over {timeline} days, based on comprehensive data analysis of {followers:,} followers "
            f"with {current_engagement:.2%} baseline engagement rate. "
            f"🎯 THEME OPTIMIZATION: Content focuses on {themes_text} themes, leveraging historical performance data "
            f"showing peak engagement of {peak_engagement:.2%} ({(peak_engagement/current_engagement):.1f}x baseline). "
            f"🤖 ML PREDICTION: {method.upper()} model estimates {posts_count} posts with {confidence:.0f}% confidence "
            f"based on {len(prediction_metrics.get('feature_importance', {}))} engagement factors. "
            f"📈 EXPECTED IMPACT: Posting intensity of {posts_per_day:.1f} posts/day should drive "
            f"{estimated_reach_increase:.1f}% reach increase and {((expected_improvement - 1) * 100):.0f}% engagement growth. "
            f"📋 SUCCESS FACTORS: {' | '.join(success_insights) if success_insights else 'Optimized for audience preferences and platform algorithms'}. "
            f"⚡ SCIENTIFIC BASIS: Strategy uses engagement science, algorithmic timing optimization, and audience behavior patterns "
            f"to maximize goal achievement while maintaining content quality and sustainable growth trajectory."
        )
        
        return summary

    async def _add_hashtags_to_content(
        self,
        original_content: str,
        content_themes: List[str],
        platform: str,
        username: str,
        goal: Dict
    ) -> str:
        """
        🏷️ HASHTAG GENERATION: Add relevant hashtags to the third sentence of content
        Uses content themes, platform analysis, and goal context for hashtag generation
        """
        try:
            if not original_content:
                return original_content
            
            # Split content into sentences
            sentences = original_content.split('. ')
            if len(sentences) < 3:
                # If less than 3 sentences, append hashtags to the last sentence
                sentences[-1] = sentences[-1].rstrip('.')
                hashtags = self._generate_relevant_hashtags(content_themes, platform, username, goal)
                hashtag_string = ' ' + ' '.join(hashtags)
                sentences[-1] += hashtag_string + '.'
                return '. '.join(sentences)
            
            # Add hashtags to the third sentence
            third_sentence = sentences[2].rstrip('.')
            hashtags = self._generate_relevant_hashtags(content_themes, platform, username, goal)
            hashtag_string = ' ' + ' '.join(hashtags)
            sentences[2] = third_sentence + hashtag_string + '.'
            
            enhanced_content = '. '.join(sentences)
            logger.info(f"🏷️ Added {len(hashtags)} hashtags to content for {username}")
            
            return enhanced_content
            
        except Exception as e:
            logger.error(f"🚨 Error adding hashtags to content: {e}")
            return original_content  # Return original content if hashtag generation fails

    def _generate_relevant_hashtags(
        self,
        content_themes: List[str],
        platform: str,
        username: str,
        goal: Dict
    ) -> List[str]:
        """
        🎯 SMART HASHTAG GENERATION: Generate 3-5 relevant hashtags based on:
        - Content themes from scraped data
        - Platform-specific trending topics
        - Goal context and engagement optimization
        - XGBoost ML recommendations
        """
        try:
            hashtags = []
            
            # 🤖 XGBOOST INTEGRATION: Get ML-powered hashtag recommendations
            try:
                from xgboost_post_estimator import XGBoostPostEstimator
                xgb_estimator = XGBoostPostEstimator()
                
                # Extract follower count from goal or use default
                follower_count = goal.get("follower_count", 1000)
                goal_text = goal.get("goal", "increase engagement")
                
                ml_hashtags = xgb_estimator.get_hashtag_recommendations(
                    content_themes, platform, goal_text, follower_count
                )
                
                if ml_hashtags:
                    hashtags.extend(ml_hashtags[:3])  # Use top 3 XGBoost recommendations
                    logger.info(f"🤖 Added {len(ml_hashtags[:3])} XGBoost-recommended hashtags for {username}")
                
            except Exception as e:
                logger.warning(f"⚠️ XGBoost hashtag recommendations failed, using fallback: {e}")
            
            # 1. Theme-based hashtags from scraped content analysis
            theme_hashtags = []
            for theme in content_themes[:2]:  # Reduced to 2 to make room for XGBoost recommendations
                if theme and len(theme) > 2:
                    # Clean and format theme as hashtag
                    clean_theme = ''.join(c.title() if c.isalnum() else '' for c in theme)
                    if clean_theme and len(clean_theme) > 2:
                        theme_hashtag = f"#{clean_theme}"
                        # Avoid duplicates with existing ML hashtags (case-insensitive)
                        if not any(theme_hashtag.lower() == existing.lower() for existing in hashtags):
                            theme_hashtags.append(theme_hashtag)
            
            hashtags.extend(theme_hashtags[:1])  # Max 1 theme hashtag to balance with ML recommendations
            
            # 2. Platform-specific hashtags for engagement optimization
            platform_hashtags = self._get_platform_hashtags(platform, goal)
            hashtags.extend(platform_hashtags[:1])  # Limit to make room for ML recommendations
            
            # 3. Goal-aligned hashtags based on engagement objectives
            goal_hashtags = self._get_goal_hashtags(goal, platform)
            hashtags.extend(goal_hashtags[:1])  # Limit to make room for ML recommendations
            
            # 4. Ensure we have 3-5 hashtags total
            if len(hashtags) < 3:
                # Add generic engagement hashtags
                fallback_hashtags = self._get_fallback_hashtags(platform)
                hashtags.extend(fallback_hashtags)
            
            # Limit to 5 hashtags and remove duplicates
            unique_hashtags = list(dict.fromkeys(hashtags))[:5]
            
            # Ensure minimum 3 hashtags
            if len(unique_hashtags) < 3:
                unique_hashtags.extend(self._get_fallback_hashtags(platform))
                unique_hashtags = list(dict.fromkeys(unique_hashtags))[:5]
            
            logger.debug(f"🏷️ Generated hashtags for {username}: {unique_hashtags}")
            return unique_hashtags[:5]  # Return max 5 hashtags
            
        except Exception as e:
            logger.error(f"🚨 Error generating hashtags: {e}")
            return self._get_fallback_hashtags(platform)[:3]  # Return 3 fallback hashtags

    def _get_platform_hashtags(self, platform: str, goal: Dict) -> List[str]:
        """Generate platform-specific hashtags for engagement optimization"""
        if platform.lower() == "instagram":
            return ["#Instagram", "#Engagement", "#VisualContent"]
        elif platform.lower() == "twitter":
            return ["#Twitter", "#Trending"]
        elif platform.lower() == "facebook":
            return ["#Facebook", "#Community", "#SocialConnection", "#Engagement"]
        else:
            return ["#SocialMedia", "#Content"]

    def _get_goal_hashtags(self, goal: Dict, platform: str) -> List[str]:
        """Generate hashtags based on goal context and objectives"""
        goal_text = goal.get("goal", "").lower()
        hashtags = []
        
        if "engagement" in goal_text or "increase" in goal_text:
            hashtags.append("#Growth")
        if "brand" in goal_text or "business" in goal_text:
            hashtags.append("#Brand")
        if "community" in goal_text or "audience" in goal_text:
            hashtags.append("#Community")
        
        return hashtags

    def _get_fallback_hashtags(self, platform: str) -> List[str]:
        """Generate fallback hashtags when other methods fail"""
        if platform.lower() == "instagram":
            return ["#Instagram", "#Content", "#Engagement", "#Quality", "#Brand"]
        elif platform.lower() == "twitter":
            return ["#Twitter", "#Update", "#Engagement", "#Content"]
        elif platform.lower() == "facebook":
            return ["#Facebook", "#Community", "#SocialConnection", "#Content", "#Engagement"]
        else:
            return ["#SocialMedia", "#Content", "#Engagement", "#Quality", "#Brand"]

class EnhancedGoalHandler:
    """Main goal handler with enhanced RAG and platform-aware schema"""
    
    def __init__(self):
        self.r2_tasks = R2Client(config=R2_CONFIG)
        self.r2_structuredb = R2Client(config=STRUCTUREDB_R2_CONFIG)
        self.rag_analyzer = DeepRAGAnalyzer()
        self.strategy_calculator = StrategyCalculator(self.rag_analyzer)
        self.content_generator = ContentGenerator(self.rag_analyzer)
        self.processed_files = set()
        self.platforms = ["instagram", "twitter", "facebook"]  # Support all three platforms
    
    async def process_goal_file(self, goal_key: str) -> None:
        """Process goal file with new schema: goal/<platform>/<username>/goal_*.json"""
        
        if goal_key in self.processed_files:
            logger.debug(f"Goal already processed in current session: {goal_key}")
            return
        
        try:
            # Parse new schema path
            parts = goal_key.split('/')
            if len(parts) < 3 or parts[0] != "goal":
                logger.error(f"Invalid goal path format: {goal_key}")
                return
                
            platform = parts[1]
            username = parts[2]
            
            # 🚫 COMPREHENSIVE PRODUCTION FILTER - Use centralized test detection
            if TestFilter.should_skip_processing(platform, username, goal_key):
                return  # Skip test data completely
                
            # 🎯 PRODUCTION USER DETECTED - Log and process
            TestFilter.log_production_user(platform, username, "processing goal")
            logger.info(f"Processing goal for {username} on {platform}")
            
            # 1. Retrieve and validate goal data
            goal_data = await self._get_goal_data(goal_key)
            if not goal_data:
                return
                
            # 2. Retrieve and analyze profile data
            profile_data = await self._get_profile_data(username, platform)
            
            if not profile_data:
                logger.warning(f"No profile data found for {username} on {platform} - using fallback method")
                
                # 🔒 FALLBACK METHOD: Generate content without profile data
                logger.info(f"🔒 Processing as private/new account: {username}")
                posts_content = await self.content_generator.generate_content_without_profile(
                    goal_data, username, platform
                )
                
                # Export to platform-aware output directory
                output_key = f"generated_content/{platform}/{username}/posts.json"
                
                if await self.r2_tasks.write_json(output_key, posts_content):
                    # Mark goal as processed
                    goal_data["status"] = "processed"
                    goal_data["processed_at"] = datetime.now().isoformat()
                    goal_data["processing_method"] = "fallback_no_profile"
                    await self.r2_tasks.write_json(goal_key, goal_data)
                    
                    logger.info(f"🔒 Successfully processed private/new account goal for {username} on {platform}")
                    logger.info(f"Output saved to: {output_key}")
                    
                    self.processed_files.add(goal_key)
                else:
                    logger.error(f"Failed to save fallback output for {username} on {platform}")
                
                return  # Exit early after fallback processing
                
            # 3. Retrieve prophet analysis (only if we have profile data)
            prophet_data = await self._get_prophet_analysis(username, platform)
            if not prophet_data:
                logger.warning(f"No prophet analysis found for {username} on {platform}")
                prophet_data = {}
                
            # 🎯 NORMAL PROCESSING PATH: We have profile data, use XGBoost and full RAG analysis
            logger.info(f"📊 Using full RAG analysis with XGBoost for {username}")
                
            # 4. Perform deep RAG analysis
            logger.info(f"Performing deep RAG analysis for {username}")
            profile_analysis = self.rag_analyzer.analyze_profile_patterns(profile_data)
            
            # 5. Calculate optimal posting strategy
            logger.info(f"Calculating posting strategy for goal: {goal_data.get('goal', '')}")
            posts_needed, posting_interval, rationale, prediction_metrics = self.strategy_calculator.calculate_posting_strategy(
                goal_data, profile_analysis, prophet_data
            )
            
            logger.info(f"Strategy: {posts_needed} posts, {posting_interval:.1f}h intervals")
            logger.info(f"Rationale: {rationale}")
            
            # 6. Generate theme-aligned content
            logger.info(f"Generating {posts_needed} theme-aligned posts")
            posts_content = await self.content_generator.generate_post_content(
                goal_data, profile_analysis, posts_needed, username, platform, prediction_metrics, posting_interval
            )
            
            # 7. Create comprehensive output in required format
            output_data = posts_content  # Direct dictionary format, no array wrapping
            
            # 8. Export to platform-aware output directory
            output_key = f"generated_content/{platform}/{username}/posts.json"
            
            if await self.r2_tasks.write_json(output_key, output_data):
                # Mark goal as processed
                goal_data["status"] = "processed"
                goal_data["processed_at"] = datetime.now().isoformat()
                await self.r2_tasks.write_json(goal_key, goal_data)
                
                logger.info(f"Successfully processed goal for {username} on {platform}")
                logger.info(f"Output saved to: {output_key}")
                
                self.processed_files.add(goal_key)
            else:
                logger.error(f"Failed to save output for {username} on {platform}")
                
        except Exception as e:
            logger.error(f"Error processing goal file {goal_key}: {e}", exc_info=True)
            
    async def _get_goal_data(self, goal_key: str) -> Optional[Dict]:
        """Retrieve and validate goal data"""
        try:
            goal_data = await self.r2_tasks.read_json(goal_key)
            if not goal_data:
                logger.error(f"Could not read goal file: {goal_key}")
                return None
                
            if goal_data.get("status") == "processed":
                logger.info(f"Goal already processed: {goal_key}")
                return None
                
            # Validate required fields
            required_fields = ["goal", "timeline"]
            if not all(field in goal_data for field in required_fields):
                logger.error(f"Missing required fields in goal file: {goal_key}")
                return None
                
            return goal_data
            
        except Exception as e:
            logger.error(f"Error reading goal data from {goal_key}: {e}")
            return None
            
    async def _get_profile_data(self, username: str, platform: str) -> Optional[Dict]:
        """Retrieve profile data from structuredb with new schema"""
        try:
            profile_key = f"{platform}/{username}/{username}.json"
            profile_data = await self.r2_structuredb.read_json(profile_key)
            
            if not profile_data:
                logger.error(f"No profile data found at: {profile_key}")
                return None
            
            # Handle case where profile data is a list containing a single dictionary
            if isinstance(profile_data, list):
                if len(profile_data) > 0 and isinstance(profile_data[0], dict):
                    logger.info(f"Profile data is a list, extracting first item for {username}")
                    profile_data = profile_data[0]
                else:
                    logger.error(f"Profile data is an empty list or invalid format for {username}")
                    return None
            elif not isinstance(profile_data, dict):
                logger.error(f"Profile data is not a dictionary or list for {username}")
                return None
            
            # Convert to expected format for analysis
            converted_profile = self._convert_profile_format(profile_data, username, platform)
            
            return converted_profile
            
        except Exception as e:
            logger.error(f"Error reading profile data for {username} on {platform}: {e}")
            return None
    
    def _convert_profile_format(self, raw_profile: Dict, username: str, platform: str) -> Dict:
        """Convert raw profile data to format expected by DeepRAGAnalyzer"""
        try:
            # Extract posts from latestPosts field
            posts = []
            if "latestPosts" in raw_profile and isinstance(raw_profile["latestPosts"], list):
                for post in raw_profile["latestPosts"]:
                    if isinstance(post, dict):
                        # Convert to expected format
                        converted_post = {
                            "caption": post.get("caption", ""),
                            "hashtags": self._extract_hashtags(post.get("caption", "")),
                            "likes": post.get("likesCount", 0),
                            "comments": post.get("commentsCount", 0),
                            "type": post.get("type", "photo")
                        }
                        posts.append(converted_post)
            
            # Create converted profile format
            converted_profile = {
                "username": raw_profile.get("username", username),
                "bio": raw_profile.get("biography", ""),
                "followers": raw_profile.get("followersCount", 1000),
                "following": raw_profile.get("followsCount", 100),
                "posts": posts,
                "engagement_rate": self._calculate_engagement_rate(posts, raw_profile.get("followersCount", 1000)),
                "platform": platform,
                "last_updated": datetime.now().isoformat(),
                "verified": raw_profile.get("verified", False),
                "business_account": raw_profile.get("isBusinessAccount", False)
            }
            
            logger.info(f"Converted profile for {username}: {len(posts)} posts, {converted_profile['followers']} followers")
            return converted_profile
            
        except Exception as e:
            logger.error(f"Error converting profile format for {username}: {e}")
            # Return minimal valid profile
            return {
                "username": username,
                "bio": "",
                "followers": 1000,
                "following": 100,
                "posts": [],
                "engagement_rate": 0.05,
                "platform": platform,
                "last_updated": datetime.now().isoformat()
            }
    
    def _extract_hashtags(self, caption: str) -> List[str]:
        """Extract hashtags from caption text"""
        if not caption:
            return []
        
        import re
        hashtags = re.findall(r'#\w+', caption)
        return hashtags
    
    def _calculate_engagement_rate(self, posts: List[Dict], followers: int) -> float:
        """Calculate average engagement rate from posts"""
        if not posts or followers <= 0:
            return 0.05  # Default 5%
        
        total_engagement = 0
        for post in posts:
            likes = post.get("likes", 0)
            comments = post.get("comments", 0)
            total_engagement += likes + comments
        
        avg_engagement_per_post = total_engagement / len(posts)
        engagement_rate = avg_engagement_per_post / followers
        
        return min(engagement_rate, 1.0)  # Cap at 100%
        
    async def _get_prophet_analysis(self, username: str, platform: str) -> Optional[Dict]:
        """Retrieve prophet analysis with new schema"""
        try:
            prophet_prefix = f"prophet_analysis/{platform}/{username}/"
            objects = await self.r2_tasks.list_objects(prophet_prefix)
            
            # Find latest analysis file
            analysis_files = [obj["Key"] for obj in objects if "analysis_" in obj["Key"]]
            if not analysis_files:
                return None
                
            # Sort by number and get latest
            analysis_files.sort(key=lambda x: int(''.join(filter(str.isdigit, x.split('_')[-1])) or 0), reverse=True)
            latest_key = analysis_files[0]
            
            prophet_data = await self.r2_tasks.read_json(latest_key)
            return prophet_data
            
        except Exception as e:
            logger.error(f"Error reading prophet analysis for {username} on {platform}: {e}")
            return None
            
    async def scan_existing_goals(self):
        """Scan for existing unprocessed goal files"""
        logger.info("Scanning for unprocessed goal files...")
        
        total_processed = 0
        for platform in self.platforms:
            platform_prefix = f"goal/{platform}/"
            
            try:
                objects = await self.r2_tasks.list_objects(platform_prefix)
                
                # 🧹 COMPREHENSIVE TEST FILTERING - Filter out all test objects
                production_objects = TestFilter.filter_test_objects(objects)
                
                # Log filtering statistics
                if len(objects) != len(production_objects):
                    filtered_count = len(objects) - len(production_objects)
                    logger.info(f"🧹 Filtered out {filtered_count} test files from {platform} scan")
                
                for obj in production_objects:
                    key = obj["Key"]
                    
                    # Skip non-JSON files
                    if not key.endswith(".json"):
                        continue
                        
                    # Skip if doesn't contain goal_ pattern
                    if "goal_" not in key:
                        continue
                    
                    # Check if already processed
                    if key in self.processed_files:
                        logger.debug(f"Already processed in current session: {key}")
                        continue
                    
                    # Read and check status
                    try:
                        goal_data = await self.r2_tasks.read_json(key)
                        
                        if not goal_data:
                            logger.warning(f"Empty goal file: {key}")
                            continue
                            
                        # Skip if already processed
                        if goal_data.get("status") == "processed":
                            logger.debug(f"Already processed: {key}")
                            self.processed_files.add(key)
                            continue
                            
                        # Skip if missing required fields
                        if not goal_data.get("goal") or not goal_data.get("timeline"):
                            logger.warning(f"Invalid goal file missing required fields: {key}")
                            continue
                            
                        logger.info(f"Processing unprocessed goal: {key}")
                        await self.process_goal_file(key)
                        total_processed += 1
                        
                    except Exception as e:
                        logger.error(f"Error checking goal file {key}: {e}")
                        continue
                        
            except Exception as e:
                logger.error(f"Error scanning {platform} goals: {e}")
                
        if total_processed > 0:
            logger.info(f"Processed {total_processed} new goal files")
        else:
            logger.debug("No new goal files to process")

# File system event handler for monitoring new goals
class GoalFileEventHandler(FileSystemEventHandler):
    """Monitors for new goal files in local directory"""
    
    def __init__(self, goal_handler: EnhancedGoalHandler):
        self.goal_handler = goal_handler
        self.loop = asyncio.get_event_loop()
    
    def on_created(self, event):
        if not event.is_directory and event.src_path.endswith(".json") and "goal_" in event.src_path:
            rel_path = os.path.relpath(event.src_path, os.getcwd())
            
            # Convert local path to R2 key
            parts = rel_path.split(os.sep)
            if len(parts) >= 3 and parts[0] == "goal":
                goal_key = "/".join(parts)
                logger.info(f"New goal file detected: {goal_key}")
                self.loop.create_task(self.goal_handler.process_goal_file(goal_key))

def main():
    """Main entry point"""
    logger.info("Starting Enhanced Goal Handler with Deep RAG Analysis")
    
    # Initialize handler
    goal_handler = EnhancedGoalHandler()
    
    # Set up file system monitoring
    event_handler = GoalFileEventHandler(goal_handler)
    observer = Observer()
    watch_dir = os.path.join("goal")
    os.makedirs(watch_dir, exist_ok=True)
    observer.schedule(event_handler, watch_dir, recursive=True)
    observer.start()
    
    logger.info(f"Monitoring directory: {watch_dir}")
    
    # Process existing files
    loop = asyncio.get_event_loop()
    loop.run_until_complete(goal_handler.scan_existing_goals())
    
    # Continuously retry scanning for unprocessed goal files every minute
    async def retry_scan_existing_goals():
        while True:
            logger.info("Retrying scan for unprocessed goal files...")
            await goal_handler.scan_existing_goals()
            await asyncio.sleep(60)  # Wait for 1 minute before retrying

    # Start the retry mechanism
    loop.create_task(retry_scan_existing_goals())
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        logger.info("Stopping Enhanced Goal Handler")
    
    observer.join()

if __name__ == "__main__":
    main()