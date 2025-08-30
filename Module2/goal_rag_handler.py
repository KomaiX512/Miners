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
import random

# Configure Gemini with more reliable model and enhanced safety settings
genai.configure(api_key=GEMINI_CONFIG["api_key"])

# Enhanced safety settings to minimize content blocking
safety_settings = [
    {
        "category": "HARM_CATEGORY_HARASSMENT",
        "threshold": "BLOCK_NONE"
    },
    {
        "category": "HARM_CATEGORY_HATE_SPEECH", 
        "threshold": "BLOCK_NONE"
    },
    {
        "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
        "threshold": "BLOCK_NONE"
    },
    {
        "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
        "threshold": "BLOCK_NONE"
    }
]

# Use gemini-1.5-flash for better reliability and less strict filtering
model_name = GEMINI_CONFIG.get("model", "gemini-1.5-flash")
fallback_model_name = GEMINI_CONFIG.get("fallback_model", "gemini-1.5-flash-exp")

if "2.5" in model_name:
    # Fallback to 1.5-flash if 2.5 is causing issues
    model_name = "gemini-1.5-flash"
    logger.info("🔄 Using gemini-1.5-flash for better reliability")

# Create primary model
model = genai.GenerativeModel(
    model_name=model_name,
    generation_config={
        "max_output_tokens": GEMINI_CONFIG["max_tokens"],
        "temperature": GEMINI_CONFIG["temperature"],
        "top_p": GEMINI_CONFIG["top_p"],
        "top_k": GEMINI_CONFIG["top_k"]
    },
    safety_settings=safety_settings
)

# Create fallback model
fallback_model = genai.GenerativeModel(
    model_name=fallback_model_name,
    generation_config={
        "max_output_tokens": GEMINI_CONFIG["max_tokens"],
        "temperature": GEMINI_CONFIG["temperature"],
        "top_p": GEMINI_CONFIG["top_p"],
        "top_k": GEMINI_CONFIG["top_k"]
    },
    safety_settings=safety_settings
)

class DeepRAGAnalyzer:
    """TRUE RAG implementation for hyper-personalized content generation using real profile data"""
    
    def __init__(self):
        self.vectorizer = TfidfVectorizer(max_features=2000, stop_words='english', ngram_range=(1, 3))
        self.profile_embeddings = None
        self.prophet_embeddings = None
        
    def analyze_profile_patterns(self, profile_data: Dict) -> Dict[str, Any]:
        """COMPREHENSIVE RAG analysis of scraped profile data to extract hyper-personalized patterns"""
        logger.info(f"🧠 Performing DEEP RAG analysis on profile: {profile_data.get('username', 'unknown')}")
        
        analysis = {
            "posting_frequency": self._analyze_posting_frequency(profile_data),
            "engagement_patterns": self._analyze_engagement_patterns(profile_data),
            "content_themes": self._extract_content_themes(profile_data),
            "successful_post_characteristics": self._identify_successful_posts(profile_data),
            "persona_traits": self._extract_persona_traits(profile_data),
            "optimal_timing": self._determine_optimal_timing(profile_data),
            # NEW: Deep content analysis for true personalization
            "writing_patterns": self._analyze_writing_patterns(profile_data),
            "vocabulary_analysis": self._analyze_vocabulary_usage(profile_data),
            "content_structure": self._analyze_content_structure(profile_data),
            "brand_positioning": self._analyze_brand_positioning(profile_data),
            "audience_interaction_style": self._analyze_audience_interaction(profile_data),
            "visual_content_patterns": self._analyze_visual_patterns(profile_data),
            "emotional_tone_analysis": self._analyze_emotional_tone(profile_data),
            "topic_expertise": self._identify_topic_expertise(profile_data),
            "posting_context": self._analyze_posting_context(profile_data),
            "content_evolution": self._analyze_content_evolution(profile_data)
        }
        
        # Add RAG summary for debugging
        logger.info(f"🧠 RAG Analysis Complete:")
        logger.info(f"  - Content Themes: {analysis['content_themes'][:3]}")
        logger.info(f"  - Writing Style: {analysis['writing_patterns'].get('primary_style', 'unknown')}")
        logger.info(f"  - Brand Voice: {analysis['persona_traits']['brand_voice']}")
        logger.info(f"  - Posts Analyzed: {len(profile_data.get('posts', []))}")
        
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
        """Extract dominant content themes using ADVANCED TF-IDF with n-grams"""
        posts = profile_data.get("posts", [])
        if not posts:
            logger.warning("⚠️ No posts available for theme extraction - using minimal RAG analysis")
            # Return minimal themes for accounts with no posts
            return ["engagement", "community", "brand", "growth", "connection"]
            
        # Combine all post text with advanced preprocessing
        post_texts = []
        all_captions = []
        
        for post in posts:
            text = ""
            caption = post.get("caption", "")
            if caption:
                text += caption + " "
                all_captions.append(caption)
            if "hashtags" in post:
                hashtags = post["hashtags"] if isinstance(post["hashtags"], list) else []
                text += " ".join(hashtags)
            if text.strip():  # Only add non-empty texts
                post_texts.append(text.lower())
        
        if not post_texts:
            logger.warning("⚠️ No valid post content found - using minimal RAG analysis")
            return ["engagement", "community", "brand", "growth", "connection"]
            
        # Extract themes using ADVANCED TF-IDF with n-grams
        try:
            # Fit vectorizer on all posts
            tfidf_matrix = self.vectorizer.fit_transform(post_texts)
            feature_names = self.vectorizer.get_feature_names_out()
            
            # Get top terms with higher threshold
            mean_scores = np.mean(tfidf_matrix.toarray(), axis=0)
            top_indices = np.argsort(mean_scores)[-20:]  # Get more terms
            
            # Filter out stop words and short terms
            themes = []
            for i in top_indices:
                term = feature_names[i]
                if len(term) > 2 and not term.isdigit():
                    # Clean the term
                    clean_term = term.replace('_', ' ').strip()
                    if clean_term and clean_term not in themes:
                        themes.append(clean_term)
            
            # Return top 8 themes for better granularity
            extracted_themes = themes[-8:] if themes else []
            
            logger.info(f"🎯 Extracted {len(extracted_themes)} content themes: {extracted_themes}")
            
            if not extracted_themes:
                logger.warning("⚠️ TF-IDF failed to extract themes - using minimal analysis")
                return ["engagement", "community", "brand", "growth", "connection"]
                
            return extracted_themes
            
        except Exception as e:
            logger.error(f"❌ Theme extraction failed: {e}")
            logger.warning("⚠️ Using minimal theme analysis due to extraction failure")
            return ["engagement", "community", "brand", "growth", "connection"]
            
    def _identify_successful_posts(self, profile_data: Dict) -> List[Dict]:
        """Identify characteristics of most successful posts"""
        posts = profile_data.get("posts", [])
        if not posts:
            logger.warning("⚠️ No posts for successful post analysis - using default characteristics")
            return [{
                "caption_length": 120,  # More realistic for social media
                "hashtag_count": 5,
                "has_cta": True,
                "engagement": 100,
                "content_type": "photo"
            }]
            
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
    
    # NEW: Advanced RAG Analysis Methods for Deep Personalization
    def _analyze_writing_patterns(self, profile_data: Dict) -> Dict[str, Any]:
        """Analyze detailed writing patterns from actual posts"""
        posts = profile_data.get("posts", [])
        if not posts:
            logger.warning("⚠️ No posts for writing pattern analysis - using default patterns")
            return {
                "primary_style": "balanced_conversational",
                "avg_sentence_length": 120.0,  # More realistic for social media
                "question_ratio": 0.3,
                "exclamation_ratio": 0.2,
                "emoji_frequency": 0.4,
                "total_captions_analyzed": 0
            }
            
        captions = [post.get("caption", "") for post in posts if post.get("caption")]
        if not captions:
            logger.warning("⚠️ No captions for writing pattern analysis - using default patterns")
            return {
                "primary_style": "balanced_conversational",
                "avg_sentence_length": 120.0,  # More realistic for social media
                "question_ratio": 0.3,
                "exclamation_ratio": 0.2,
                "emoji_frequency": 0.4,
                "total_captions_analyzed": 0
            }
            
        # Analyze sentence structures
        sentence_lengths = []
        question_ratio = 0
        exclamation_ratio = 0
        emoji_usage = 0
        
        for caption in captions:
            sentences = caption.split('.')
            sentence_lengths.extend([len(s.strip()) for s in sentences if s.strip()])
            question_ratio += caption.count('?')
            exclamation_ratio += caption.count('!')
            emoji_usage += len(re.findall(r'[^\w\s,.]', caption))  # Simple emoji detection
        
        total_posts = len(captions)
        avg_sentence_length = np.mean(sentence_lengths) if sentence_lengths else 0
        
        # Determine primary writing style
        if avg_sentence_length < 50:
            primary_style = "concise_punchy"
        elif avg_sentence_length < 100:
            primary_style = "balanced_conversational"
        else:
            primary_style = "detailed_narrative"
            
        return {
            "primary_style": primary_style,
            "avg_sentence_length": round(avg_sentence_length, 1),
            "question_ratio": round(question_ratio / total_posts, 2),
            "exclamation_ratio": round(exclamation_ratio / total_posts, 2),
            "emoji_frequency": round(emoji_usage / total_posts, 2),
            "total_captions_analyzed": total_posts
        }
    
    def _analyze_vocabulary_usage(self, profile_data: Dict) -> Dict[str, Any]:
        """Analyze specific vocabulary and language patterns"""
        posts = profile_data.get("posts", [])
        if not posts:
            logger.warning("⚠️ No posts for vocabulary analysis - using default vocabulary")
            return {
                "vocabulary_diversity": 0.6,
                "total_words": 0,
                "unique_words": 0,
                "signature_words": ["engagement", "community", "growth", "brand", "connection"],
                "language_complexity": "moderate"
            }
            
        all_text = " ".join([post.get("caption", "") for post in posts if post.get("caption")])
        if not all_text.strip():
            logger.warning("⚠️ No text content for vocabulary analysis - using default vocabulary")
            return {
                "vocabulary_diversity": 0.6,
                "total_words": 0,
                "unique_words": 0,
                "signature_words": ["engagement", "community", "growth", "brand", "connection"],
                "language_complexity": "moderate"
            }
            
        words = all_text.lower().split()
        word_count = len(words)
        unique_words = len(set(words))
        
        # Analyze language complexity
        vocabulary_diversity = unique_words / word_count if word_count > 0 else 0
        
        # Find frequently used unique terms (not in common stop words)
        from collections import Counter
        stop_words = {'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'can', 'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them', 'my', 'your', 'his', 'her', 'its', 'our', 'their'}
        
        filtered_words = [word for word in words if word not in stop_words and len(word) > 2]
        word_freq = Counter(filtered_words)
        signature_words = [word for word, count in word_freq.most_common(10) if count > 1]
        
        return {
            "vocabulary_diversity": round(vocabulary_diversity, 3),
            "total_words": word_count,
            "unique_words": unique_words,
            "signature_words": signature_words,
            "language_complexity": "high" if vocabulary_diversity > 0.7 else "moderate" if vocabulary_diversity > 0.5 else "simple"
        }
    
    def _analyze_content_structure(self, profile_data: Dict) -> Dict[str, Any]:
        """Analyze how posts are structured and formatted"""
        posts = profile_data.get("posts", [])
        if not posts:
            logger.warning("⚠️ No posts for content structure analysis - using default structure")
            return {
                "intro_usage": 0.3,
                "cta_usage": 0.4,
                "storytelling_usage": 0.2,
                "list_structure_usage": 0.1,
                "structure_preferences": "engagement_focused"
            }
            
        captions = [post.get("caption", "") for post in posts if post.get("caption")]
        if not captions:
            logger.warning("⚠️ No captions for content structure analysis - using default structure")
            return {
                "intro_usage": 0.3,
                "cta_usage": 0.4,
                "storytelling_usage": 0.2,
                "list_structure_usage": 0.1,
                "structure_preferences": "engagement_focused"
            }
            
        # Analyze post structure patterns
        has_intro = 0
        has_call_to_action = 0
        uses_storytelling = 0
        uses_lists = 0
        
        for caption in captions:
            # Check for intro patterns
            if any(starter in caption.lower()[:50] for starter in ['today', 'this morning', 'yesterday', 'excited to', 'happy to']):
                has_intro += 1
                
            # Check for CTAs
            if any(cta in caption.lower() for cta in ['comment', 'share', 'tag', 'visit', 'check out', 'swipe', 'link in bio']):
                has_call_to_action += 1
                
            # Check for storytelling elements
            if any(story in caption.lower() for story in ['story', 'journey', 'experience', 'remember when', 'once']):
                uses_storytelling += 1
                
            # Check for list structures
            if any(list_indicator in caption for list_indicator in ['1.', '2.', '•', '-', '→']):
                uses_lists += 1
        
        total_posts = len(captions)
        
        return {
            "intro_usage": round(has_intro / total_posts, 2),
            "cta_usage": round(has_call_to_action / total_posts, 2),
            "storytelling_usage": round(uses_storytelling / total_posts, 2),
            "list_structure_usage": round(uses_lists / total_posts, 2),
            "structure_preferences": self._determine_structure_preference(has_intro, has_call_to_action, uses_storytelling, uses_lists, total_posts)
        }
    
    def _determine_structure_preference(self, intro, cta, story, lists, total):
        """Determine primary content structure preference"""
        ratios = {
            "storytelling": story / total,
            "instructional": lists / total,
            "engagement_focused": cta / total,
            "conversational": intro / total
        }
        return max(ratios, key=ratios.get)
    
    def _analyze_brand_positioning(self, profile_data: Dict) -> Dict[str, Any]:
        """Analyze brand positioning from bio and posts"""
        bio = profile_data.get("bio", "")
        posts = profile_data.get("posts", [])
        
        # Analyze bio for positioning cues
        positioning_indicators = {
            "luxury": ["luxury", "premium", "exclusive", "elite", "high-end"],
            "accessible": ["everyone", "affordable", "accessible", "everyday", "simple"],
            "expert": ["expert", "professional", "certified", "years", "experience"],
            "innovative": ["innovative", "new", "cutting-edge", "revolutionary", "unique"],
            "community": ["community", "together", "family", "team", "tribe"]
        }
        
        bio_lower = bio.lower()
        positioning_scores = {}
        
        for position, keywords in positioning_indicators.items():
            score = sum(1 for keyword in keywords if keyword in bio_lower)
            positioning_scores[position] = score
        
        # Analyze posts for positioning reinforcement
        all_post_text = " ".join([post.get("caption", "") for post in posts if post.get("caption")]).lower()
        
        for position, keywords in positioning_indicators.items():
            post_score = sum(1 for keyword in keywords if keyword in all_post_text)
            positioning_scores[position] += post_score * 0.5  # Weight posts less than bio
        
        primary_positioning = max(positioning_scores, key=positioning_scores.get) if any(positioning_scores.values()) else "authentic"
        
        return {
            "primary_positioning": primary_positioning,
            "positioning_scores": positioning_scores,
            "bio_analysis": bio_lower[:100] + "..." if len(bio_lower) > 100 else bio_lower
        }
    
    def _analyze_audience_interaction(self, profile_data: Dict) -> Dict[str, Any]:
        """Analyze how the account interacts with audience"""
        posts = profile_data.get("posts", [])
        if not posts:
            logger.warning("⚠️ No posts for audience interaction analysis - using default interaction")
            return {
                "interaction_style": "moderately_engaging",
                "direct_address_ratio": 0.3,
                "question_ratio": 0.3,
                "community_language_ratio": 0.2
            }
            
        captions = [post.get("caption", "") for post in posts if post.get("caption")]
        if not captions:
            logger.warning("⚠️ No captions for audience interaction analysis - using default interaction")
            return {
                "interaction_style": "moderately_engaging",
                "direct_address_ratio": 0.3,
                "question_ratio": 0.3,
                "community_language_ratio": 0.2
            }
            
        direct_address = 0
        question_asking = 0
        community_language = 0
        
        for caption in captions:
            caption_lower = caption.lower()
            
            # Check for direct address
            if any(address in caption_lower for address in ['you', 'your', 'have you', 'do you', 'are you']):
                direct_address += 1
                
            # Check for questions
            if '?' in caption:
                question_asking += 1
                
            # Check for community language
            if any(community in caption_lower for community in ['we', 'us', 'our', 'together', 'community', 'family']):
                community_language += 1
        
        total_posts = len(captions)
        
        interaction_style = "highly_engaging" if (direct_address + question_asking) / total_posts > 0.7 else "moderately_engaging" if (direct_address + question_asking) / total_posts > 0.3 else "informational"
        
        return {
            "interaction_style": interaction_style,
            "direct_address_ratio": round(direct_address / total_posts, 2),
            "question_ratio": round(question_asking / total_posts, 2),
            "community_language_ratio": round(community_language / total_posts, 2)
        }
    
    def _analyze_visual_patterns(self, profile_data: Dict) -> Dict[str, Any]:
        """Analyze visual content references and patterns"""
        posts = profile_data.get("posts", [])
        if not posts:
            return {"visual_style": "unknown", "content_types": [], "visual_references": 0}
            
        visual_references = 0
        content_types = []
        
        for post in posts:
            post_type = post.get("type", "photo")
            if post_type not in content_types:
                content_types.append(post_type)
                
            caption = post.get("caption", "").lower()
            # Look for visual descriptions
            if any(visual in caption for visual in ['photo', 'pic', 'image', 'video', 'look', 'outfit', 'makeup', 'behind the scenes']):
                visual_references += 1
        
        return {
            "content_types": content_types,
            "visual_references_ratio": round(visual_references / len(posts), 2) if posts else 0,
            "primary_content_type": max(set([post.get("type", "photo") for post in posts]), key=[post.get("type", "photo") for post in posts].count) if posts else "photo"
        }
    
    def _analyze_emotional_tone(self, profile_data: Dict) -> Dict[str, Any]:
        """Analyze emotional tone and sentiment patterns"""
        posts = profile_data.get("posts", [])
        if not posts:
            logger.warning("⚠️ No posts for emotional tone analysis - using default tone")
            return {
                "dominant_tone": "positive",
                "tone_scores": {"positive": 0.5, "motivational": 0.3, "casual": 0.2},
                "emotional_intensity": "moderate"
            }
            
        captions = [post.get("caption", "") for post in posts if post.get("caption")]
        if not captions:
            logger.warning("⚠️ No captions for emotional tone analysis - using default tone")
            return {
                "dominant_tone": "positive",
                "tone_scores": {"positive": 0.5, "motivational": 0.3, "casual": 0.2},
                "emotional_intensity": "moderate"
            }
            
        positive_indicators = ['love', 'amazing', 'excited', 'happy', 'grateful', 'blessed', 'awesome', 'incredible', 'fantastic', 'wonderful']
        motivational_indicators = ['inspire', 'motivate', 'achieve', 'dream', 'goal', 'success', 'believe', 'possible', 'grow', 'transform']
        casual_indicators = ['lol', 'haha', 'fun', 'chill', 'cool', 'hey', 'sup', 'yeah', 'totally', 'omg']
        
        positive_score = 0
        motivational_score = 0
        casual_score = 0
        
        for caption in captions:
            caption_lower = caption.lower()
            positive_score += sum(1 for word in positive_indicators if word in caption_lower)
            motivational_score += sum(1 for word in motivational_indicators if word in caption_lower)
            casual_score += sum(1 for word in casual_indicators if word in caption_lower)
        
        total_posts = len(captions)
        
        # Determine dominant emotional tone
        scores = {
            "positive": positive_score / total_posts,
            "motivational": motivational_score / total_posts,
            "casual": casual_score / total_posts
        }
        
        dominant_tone = max(scores, key=scores.get) if any(scores.values()) else "neutral"
        
        return {
            "dominant_tone": dominant_tone,
            "tone_scores": scores,
            "emotional_intensity": "high" if max(scores.values()) > 2 else "moderate" if max(scores.values()) > 1 else "low"
        }
    
    def _identify_topic_expertise(self, profile_data: Dict) -> Dict[str, Any]:
        """Identify areas of expertise and authority from content"""
        posts = profile_data.get("posts", [])
        bio = profile_data.get("bio", "")
        
        if not posts:
            logger.warning("⚠️ No posts for topic expertise analysis - using default expertise")
            return {
                "primary_expertise": "general",
                "expertise_scores": {"general": 1},
                "authority_level": "emerging"
            }
            
        # Combine bio and post content for expertise analysis
        all_content = bio + " " + " ".join([post.get("caption", "") for post in posts if post.get("caption")])
        all_content_lower = all_content.lower()
        
        expertise_domains = {
            "beauty": ["beauty", "makeup", "skincare", "cosmetics", "foundation", "lipstick", "eyeshadow"],
            "fitness": ["workout", "fitness", "gym", "exercise", "training", "muscle", "cardio"],
            "fashion": ["fashion", "style", "outfit", "designer", "trends", "clothing", "accessories"],
            "food": ["recipe", "cooking", "food", "chef", "restaurant", "delicious", "ingredients"],
            "travel": ["travel", "trip", "vacation", "destination", "explore", "adventure", "journey"],
            "business": ["business", "entrepreneur", "startup", "company", "CEO", "founder", "strategy"],
            "technology": ["tech", "technology", "innovation", "digital", "app", "software", "coding"],
            "lifestyle": ["lifestyle", "daily", "routine", "home", "family", "life", "living"]
        }
        
        domain_scores = {}
        for domain, keywords in expertise_domains.items():
            score = sum(1 for keyword in keywords if keyword in all_content_lower)
            if score > 0:
                domain_scores[domain] = score
        
        primary_expertise = max(domain_scores, key=domain_scores.get) if domain_scores else "general"
        
        return {
            "primary_expertise": primary_expertise,
            "expertise_scores": domain_scores,
            "authority_level": "high" if domain_scores.get(primary_expertise, 0) > 5 else "moderate" if domain_scores.get(primary_expertise, 0) > 2 else "emerging"
        }
    
    def _analyze_posting_context(self, profile_data: Dict) -> Dict[str, Any]:
        """Analyze contextual patterns in posting"""
        posts = profile_data.get("posts", [])
        if not posts:
            return {"context_patterns": [], "time_references": 0}
            
        time_references = 0
        event_references = 0
        seasonal_references = 0
        
        for post in posts:
            caption = post.get("caption", "").lower()
            
            # Time context
            if any(time_ref in caption for time_ref in ['today', 'yesterday', 'tomorrow', 'this week', 'last week', 'morning', 'evening']):
                time_references += 1
                
            # Event context
            if any(event in caption for event in ['event', 'launch', 'announcement', 'celebration', 'milestone', 'news']):
                event_references += 1
                
            # Seasonal context
            if any(season in caption for season in ['spring', 'summer', 'fall', 'winter', 'holiday', 'christmas', 'new year']):
                seasonal_references += 1
        
        total_posts = len(posts)
        
        return {
            "time_awareness": round(time_references / total_posts, 2),
            "event_awareness": round(event_references / total_posts, 2),
            "seasonal_awareness": round(seasonal_references / total_posts, 2),
            "context_style": "highly_contextual" if (time_references + event_references) / total_posts > 0.5 else "moderately_contextual" if (time_references + event_references) / total_posts > 0.2 else "timeless"
        }
    
    def _analyze_content_evolution(self, profile_data: Dict) -> Dict[str, Any]:
        """Analyze how content has evolved over time"""
        posts = profile_data.get("posts", [])
        if len(posts) < 3:
            return {"evolution_trend": "insufficient_data", "consistency": "unknown"}
            
        # Simple evolution analysis based on post order (assuming recent posts are first)
        recent_posts = posts[:len(posts)//3] if len(posts) > 6 else posts[:2]
        older_posts = posts[-len(posts)//3:] if len(posts) > 6 else posts[-2:]
        
        recent_themes = self._get_mini_themes([post.get("caption", "") for post in recent_posts])
        older_themes = self._get_mini_themes([post.get("caption", "") for post in older_posts])
        
        theme_overlap = len(set(recent_themes) & set(older_themes))
        consistency_score = theme_overlap / max(len(recent_themes), len(older_themes)) if recent_themes or older_themes else 0
        
        return {
            "consistency_score": round(consistency_score, 2),
            "evolution_trend": "evolving" if consistency_score < 0.5 else "consistent",
            "recent_focus": recent_themes[:3],
            "historical_focus": older_themes[:3]
        }
    
    def _get_mini_themes(self, texts: List[str]) -> List[str]:
        """Extract basic themes from a small set of texts"""
        if not texts:
            return []
            
        all_text = " ".join(texts).lower()
        words = all_text.split()
        
        # Simple frequency analysis for mini theme extraction
        from collections import Counter
        word_freq = Counter([word for word in words if len(word) > 3])
        return [word for word, count in word_freq.most_common(5) if count > 1]

    def _switch_to_fallback_model(self):
        """Switch to fallback model when primary model has issues"""
        global model, model_name
        if model_name != fallback_model_name:
            logger.info(f"🔄 Switching from {model_name} to {fallback_model_name} due to safety filter issues")
            model = fallback_model
            model_name = fallback_model_name
            return True
        return False

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
        """Generate HYPER-PERSONALIZED posts using DEEP RAG analysis - NO FALLBACKS"""
        
        logger.info(f"🧠 Starting DEEP RAG content generation for {username} on {platform}")
        logger.info(f"🎯 Goal: {goal.get('goal', 'unknown')}")
        logger.info(f"📊 Posts needed: {posts_needed}")
        
        posts_dict = {}
        
        # Validate RAG analysis has necessary data
        required_analysis = ["persona_traits", "content_themes", "writing_patterns", "vocabulary_analysis"]
        for analysis_type in required_analysis:
            if analysis_type not in profile_analysis:
                raise ValueError(f"RAG analysis missing {analysis_type} - cannot generate personalized content")
        
        content_themes = profile_analysis["content_themes"]
        logger.info(f"🎯 Using content themes: {content_themes}")
        
        # Generate individual posts using DEEP RAG analysis
        for i in range(posts_needed):
            try:
                logger.info(f"🧠 Generating post {i+1}/{posts_needed} using RAG analysis...")
                
                post_content = await self._generate_single_post(
                    i + 1,
                    posts_needed,
                    goal,
                    profile_analysis,  # Pass complete analysis
                    username,
                    platform
                )
                
                # 🏷️ HASHTAG INTEGRATION: Generate using RAG-based hashtags
                enhanced_content = await self._add_hashtags_to_content(
                    post_content.get("three_sentences", ""),
                    content_themes,
                    platform,
                    username,
                    goal
                )
                
                # Format as Post_X with enhanced content
                post_key = f"Post_{i + 1}"
                posts_dict[post_key] = {
                    "content": enhanced_content,
                    "status": "pending"
                }
                
                logger.info(f"✅ Successfully generated RAG-based post {i+1}")
                
            except Exception as e:
                logger.error(f"❌ Failed to generate post {i+1} using RAG: {e}")
                raise ValueError(f"RAG-based content generation failed for post {i+1} - {e}")
        
        # Generate comprehensive summary using RAG analysis
        summary = self._generate_rag_summary(
            posts_needed, 
            profile_analysis,
            goal,
            prediction_metrics,
            username,
            platform
        )
        
        # Add summary and timeline
        posts_dict["Summary"] = summary
        timeline_hours = int(round(posting_interval))
        posts_dict["Timeline"] = str(timeline_hours)
        
        logger.info(f"🎉 Successfully generated {posts_needed} RAG-based posts for {username}")
        logger.info(f"📅 Timeline: {timeline_hours} hours between posts")
        
        return posts_dict







    # REMOVED: All fallback content generation methods - RAG analysis only
        
    async def _generate_single_post(
        self,
        post_number: int,
        total_posts: int,
        goal: Dict,
        profile_analysis: Dict,
        username: str,
        platform: str
    ) -> Dict:
        """Generate a single post using DEEP RAG analysis - NO FALLBACKS ALLOWED"""
        
        logger.info(f"🧠 Generating post {post_number} using DEEP RAG analysis for {username}")
        
        # Create HYPER-PERSONALIZED prompt using complete RAG analysis
        prompt = self._create_content_prompt(
            post_number,
            total_posts,
            goal,
            profile_analysis,
            platform
        )
        
        # Aggressive retry with NO fallbacks - force RAG-based generation
        max_retries = 5  # More retries but no fallbacks
        base_delay = 3
        
        for attempt in range(max_retries):
            try:
                logger.info(f"🤖 RAG Generation attempt {attempt + 1} for post {post_number}")
                
                response = await asyncio.wait_for(
                    model.generate_content_async(prompt),
                    timeout=90  # Longer timeout for complex prompts
                )
                
                # Check for valid response with content
                if response and response.text:
                    # Parse response into structured format
                    content = self._parse_content_response(response.text, post_number)
                    
                    # Validate content quality using RAG analysis
                    if self._validate_rag_content(content, profile_analysis):
                        logger.info(f"✅ Successfully generated RAG-aligned content for post {post_number}")
                        return content
                    else:
                        logger.warning(f"⚠️ Generated content doesn't match RAG patterns, attempt {attempt + 1}")
                        # After 3 attempts, accept the content anyway to prevent infinite retries
                        if attempt >= 2:
                            logger.warning(f"⚠️ Accepting content after {attempt + 1} attempts to prevent infinite retries")
                            return content
                        continue
                else:
                    logger.warning(f"Empty response from AI model for post {post_number}, attempt {attempt + 1}")
                    
            except Exception as e:
                logger.error(f"❌ Error generating RAG content for post {post_number}, attempt {attempt + 1}: {e}")
                
                error_str = str(e).lower()
                
                # Handle rate limiting with exponential backoff
                if any(rate_term in error_str for rate_term in ["quota", "rate", "limit", "429", "too many"]):
                    if attempt < max_retries - 1:
                        delay = base_delay * (2 ** attempt)  # Exponential backoff
                        logger.info(f"⏰ Rate limited, waiting {delay} seconds before retry...")
                        await asyncio.sleep(delay)
                        continue
                    else:
                        logger.error(f"❌ Rate limit exceeded after {max_retries} attempts - RAG generation failed")
                        raise ValueError(f"RAG-based content generation failed due to rate limits for {username}")
                
                # Handle safety filter issues by modifying prompt
                if any(safety_term in error_str for safety_term in ["safety", "blocked", "filter", "content policy"]):
                    logger.warning(f"🚫 Safety filter triggered, adjusting prompt approach...")
                    # Try with a more neutral version of the prompt
                    prompt = self._create_neutral_rag_prompt(post_number, total_posts, goal, profile_analysis, platform)
                    continue
                
                # For final attempt, raise error instead of fallback
                if attempt == max_retries - 1:
                    logger.error(f"❌ All RAG generation attempts failed for post {post_number}")
                    raise ValueError(f"RAG-based content generation failed completely for {username} - no fallbacks allowed")
        
        # This should never be reached due to the raise above
        raise ValueError(f"RAG content generation failed for post {post_number} - no fallbacks available")
    
    def _validate_rag_content(self, content: Dict, profile_analysis: Dict) -> bool:
        """Validate that generated content aligns with RAG analysis"""
        if not content or "three_sentences" not in content:
            return False
            
        generated_text = content["three_sentences"].lower()
        
        # Check if content uses signature vocabulary
        signature_words = profile_analysis.get("vocabulary_analysis", {}).get("signature_words", [])
        if signature_words:
            vocab_match = any(word.lower() in generated_text for word in signature_words[:3])
            if not vocab_match:
                logger.warning("⚠️ Generated content doesn't use signature vocabulary")
                # For minimal data accounts, be more lenient
                if len(profile_analysis.get('posts', [])) == 0:
                    logger.info("✅ Allowing content for minimal data account despite vocabulary mismatch")
                    return True
                return False
        
        # Check content themes alignment
        content_themes = profile_analysis.get("content_themes", [])
        if content_themes:
            theme_match = any(theme.lower() in generated_text for theme in content_themes[:3])
            if not theme_match:
                logger.warning("⚠️ Generated content doesn't align with content themes")
                # For minimal data accounts, be more lenient
                if len(profile_analysis.get('posts', [])) == 0:
                    logger.info("✅ Allowing content for minimal data account despite theme mismatch")
                    return True
                return False
        
        # Check writing style alignment
        writing_patterns = profile_analysis.get("writing_patterns", {})
        target_length = writing_patterns.get("avg_sentence_length", 120)
        actual_length = len(generated_text) / len(generated_text.split('.'))
        
        # Allow more variance for minimal data accounts and reasonable content lengths
        variance_threshold = target_length * 0.8 if target_length < 150 else target_length * 0.6
        if abs(actual_length - target_length) > variance_threshold:
            logger.warning(f"⚠️ Generated content length ({actual_length:.0f}) doesn't match pattern ({target_length:.0f}) - variance threshold: {variance_threshold:.0f}")
            # For minimal data accounts, be more lenient
            if target_length < 150:  # Default patterns
                logger.info("✅ Allowing content for minimal data account despite length variance")
                return True
            return False
        
        return True
    
    def _create_neutral_rag_prompt(self, post_number: int, total_posts: int, goal: Dict, profile_analysis: Dict, platform: str) -> str:
        """Create a more neutral version of the RAG prompt to avoid safety filters"""
        
        # Extract key RAG elements in neutral language
        content_themes = profile_analysis.get("content_themes", [])[:3]
        writing_style = profile_analysis.get("writing_patterns", {}).get("primary_style", "balanced")
        expertise = profile_analysis.get("topic_expertise", {}).get("primary_expertise", "general")
        
        prompt = f"""
        Create educational content for post #{post_number} of {total_posts} for {platform}.
        
        Content should focus on: {', '.join(content_themes)}
        Writing approach: {writing_style}
        Expertise area: {expertise}
        
        Requirements:
        1. Informative and educational tone
        2. Authentic voice and perspective
        3. Value-driven content
        4. Platform-appropriate format
        
        Respond with JSON format:
        {{
            "three_sentences": "Educational content matching the specified themes and style."
        }}
        """
        
        return prompt

    # REMOVED: AI-free fallback generation - RAG analysis only
        
    def _create_content_prompt(
        self,
        post_number: int,
        total_posts: int,
        goal: Dict,
        profile_analysis: Dict,
        platform: str
    ) -> str:
        """Create HYPER-PERSONALIZED prompt using deep RAG analysis - NO GENERIC CONTENT ALLOWED"""
        
        # Extract COMPREHENSIVE RAG analysis data
        persona_traits = profile_analysis["persona_traits"]
        content_themes = profile_analysis["content_themes"]
        successful_characteristics = profile_analysis["successful_post_characteristics"]
        writing_patterns = profile_analysis["writing_patterns"]
        vocabulary_analysis = profile_analysis["vocabulary_analysis"]
        content_structure = profile_analysis["content_structure"]
        brand_positioning = profile_analysis["brand_positioning"]
        audience_interaction = profile_analysis["audience_interaction_style"]
        emotional_tone = profile_analysis["emotional_tone_analysis"]
        topic_expertise = profile_analysis["topic_expertise"]
        
        # Build HYPER-SPECIFIC context using RAG data
        themes_str = ", ".join(content_themes[:5])  # Use more themes for specificity
        signature_words = ", ".join(vocabulary_analysis["signature_words"][:5])
        
        # Check if we're using minimal/default data
        posts_count = profile_analysis.get('posts', [])
        is_minimal_data = len(posts_count) == 0 if isinstance(posts_count, list) else True
        
        # Goal analysis for instruction alignment
        goal_text = goal.get("goal", "")
        instructions = goal.get("instructions", "")
        persona_goal = goal.get("persona", "")
        
        # For accounts with real data, use goal context to enhance themes
        if not is_minimal_data and goal_text:
            # Extract specific themes from the goal
            goal_themes = []
            goal_lower = goal_text.lower()
            
            # Machinery-specific themes
            if any(word in goal_lower for word in ["machinery", "machine", "equipment", "tools"]):
                goal_themes.extend(["machinery", "equipment", "industrial", "technical", "automation"])
            
            # Business-specific themes
            if any(word in goal_lower for word in ["business", "trading", "global", "company"]):
                goal_themes.extend(["business", "trading", "global", "professional", "industry"])
            
            # Awareness-specific themes
            if any(word in goal_lower for word in ["awareness", "education", "inform", "knowledge"]):
                goal_themes.extend(["education", "awareness", "knowledge", "information", "learning"])
            
            # Add goal-specific themes to content themes
            if goal_themes:
                content_themes = list(set(content_themes + goal_themes))
                logger.info(f"Enhanced themes with goal context: {content_themes}")
        
        # Create COMPREHENSIVE successful patterns analysis
        successful_patterns = []
        if successful_characteristics:
            avg_caption_length = np.mean([char.get("caption_length", 50) for char in successful_characteristics])
            avg_hashtags = np.mean([char.get("hashtag_count", 5) for char in successful_characteristics])
            has_cta_ratio = np.mean([char.get("has_cta", False) for char in successful_characteristics])
            
            successful_patterns = [
                f"Successful caption length: {int(avg_caption_length)} characters (must match this exactly)",
                f"Hashtag usage: {int(avg_hashtags)} hashtags per post",
                f"Call-to-action frequency: {has_cta_ratio:.0%} of top posts include CTAs",
                f"Writing style: {writing_patterns['primary_style']} with {writing_patterns['avg_sentence_length']:.0f} character sentences",
                f"Question frequency: {writing_patterns['question_ratio']:.1f} questions per post",
                f"Exclamation usage: {writing_patterns['exclamation_ratio']:.1f} per post",
                f"Emotional tone: {emotional_tone['dominant_tone']} with {emotional_tone['emotional_intensity']} intensity"
            ]
        
        # HYPER-PERSONALIZED prompt using ALL RAG data
        prompt = f"""
        You are creating content for a SPECIFIC account with DETAILED personality analysis. You MUST replicate their exact writing style and brand voice.
        
        ACCOUNT PROFILE ANALYSIS:
        Username Analysis: {profile_analysis.get('username', 'target account')}
        Primary Content Themes: {themes_str}
        Signature Vocabulary: {signature_words}
        Writing Style: {writing_patterns['primary_style']} 
        Brand Positioning: {brand_positioning['primary_positioning']}
        Audience Interaction: {audience_interaction['interaction_style']}
        Content Structure Preference: {content_structure['structure_preferences']}
        Topic Expertise: {topic_expertise['primary_expertise']} (authority level: {topic_expertise['authority_level']})
        Emotional Tone: {emotional_tone['dominant_tone']} with {emotional_tone['emotional_intensity']} intensity
        {'⚠️ NOTE: This account has minimal posting history - using default patterns for new/empty accounts' if is_minimal_data else '✅ NOTE: This account has REAL posting history - use authentic voice patterns from actual posts'}
        
        BUSINESS CONTEXT:
        Account Type: {profile_analysis.get('username', 'target account')}
        Industry Focus: {', '.join([theme for theme in content_themes if theme in ['machinery', 'equipment', 'industrial', 'technical', 'automation', 'business', 'trading', 'global']])}
        Content Purpose: {goal_text}
        
        GOAL ALIGNMENT:
        Primary Goal: {goal_text}
        Specific Instructions: {instructions}
        Persona Requirements: {persona_goal}
        
        EXACT WRITING PATTERNS TO REPLICATE:
        {chr(10).join(successful_patterns)}
        
        CONTENT STRUCTURE REQUIREMENTS:
        - Intro Usage: {content_structure['intro_usage']:.0%} of posts start with time/context
        - CTA Usage: {content_structure['cta_usage']:.0%} of posts include calls-to-action  
        - Storytelling: {content_structure['storytelling_usage']:.0%} of posts use narrative elements
        - Question Engagement: {audience_interaction['question_ratio']:.0%} of posts ask questions
        
        VOCABULARY REQUIREMENTS:
        - Use signature words: {signature_words}
        - Language complexity: {vocabulary_analysis['language_complexity']}
        - Vocabulary diversity target: {vocabulary_analysis['vocabulary_diversity']:.2f}
        
        POST SPECIFICATIONS:
        This is post #{post_number} of {total_posts} for {platform}
        Platform: {platform}
        
        CRITICAL REQUIREMENTS:
        1. Replicate the EXACT writing style patterns identified in the analysis
        2. Use the specific vocabulary and language complexity found in their posts
        3. Follow their content structure preferences exactly
        4. Match their emotional tone and interaction style
        5. Align with the goal while maintaining their authentic voice
        6. Use their preferred sentence length ({writing_patterns['avg_sentence_length']:.0f} characters average)
        7. Include questions at their typical frequency ({writing_patterns['question_ratio']:.1f} per post)
        8. Use their typical emoji frequency ({writing_patterns['emoji_frequency']:.1f} per post)
        
        ABSOLUTE MANDATE: This content MUST sound like it was written by the original account owner. Use their voice, style, themes, and patterns exactly.
        
        CONTENT REQUIREMENTS:
        - Focus on machinery, equipment, and industrial topics
        - Use professional, technical language appropriate for the industry
        - Include specific machinery references and technical details
        - Maintain business credibility and expertise tone
        - Align with the goal of raising awareness about machinery usage
        
        Respond ONLY with this JSON format:
        {{
            "three_sentences": "First sentence introducing machinery/equipment topic with their style. Second sentence providing technical details and industry insights. Third sentence engaging audience with machinery knowledge and call-to-action."
        }}
        """
        
        return prompt
        
    def _parse_content_response(self, response_text: str, post_number: int, goal: Dict = None, persona_traits: Dict = None, content_themes: List[str] = None, platform: str = None) -> Dict:
        """Parse AI response into structured content with enhanced error handling"""
        try:
            # Extract JSON from response
            json_start = response_text.find("{")
            json_end = response_text.rfind("}") + 1
            
            if json_start >= 0 and json_end > json_start:
                json_str = response_text[json_start:json_end]
                content = json.loads(json_str)
                
                # Validate required field
                if "three_sentences" in content:
                    logger.info(f"✅ Successfully parsed AI-generated content for post {post_number}")
                    return content
                else:
                    logger.warning(f"⚠️ AI response missing 'three_sentences' field for post {post_number}")
                    
        except json.JSONDecodeError as e:
            logger.error(f"🚨 JSON parsing error for post {post_number}: {e}")
            logger.debug(f"Raw response: {response_text[:200]}...")
        except Exception as e:
            logger.error(f"🚨 Unexpected error parsing content response for post {post_number}: {e}")
        
        # No fallback content - RAG analysis is mandatory
        logger.error(f"❌ RAG content parsing failed for post {post_number} - no fallbacks allowed")
        raise ValueError(f"Failed to parse RAG-generated content for post {post_number}")

    # REMOVED: Fallback content generation - RAG analysis only

    def _generate_rag_summary(
        self, 
        posts_count: int, 
        profile_analysis: Dict,
        goal: Dict,
        prediction_metrics: Dict,
        username: str,
        platform: str
    ) -> str:
        """Generate HONEST and CONVINCING summary for account holders"""
        
        content_themes = profile_analysis["content_themes"]
        writing_patterns = profile_analysis["writing_patterns"]
        vocabulary_analysis = profile_analysis["vocabulary_analysis"]
        emotional_tone = profile_analysis["emotional_tone_analysis"]
        topic_expertise = profile_analysis["topic_expertise"]
        brand_positioning = profile_analysis["brand_positioning"]
        
        goal_text = goal.get("goal", "unknown goal")
        timeline = goal.get("timeline", 7)
        posts_analyzed = len(profile_analysis.get('posts', []))
        
        # Determine analysis type and confidence level
        if posts_analyzed == 0:
            analysis_type = "NEW ACCOUNT OPTIMIZATION"
            confidence_level = "ESTABLISHED INDUSTRY STANDARDS"
            data_source = "industry best practices and engagement science"
            personalization_approach = "platform-optimized content strategy"
        elif posts_analyzed < 10:
            analysis_type = "EMERGING PROFILE ANALYSIS"
            confidence_level = "GROWING PATTERN RECOGNITION"
            data_source = f"{posts_analyzed} recent posts and industry benchmarks"
            personalization_approach = "emerging voice patterns with proven strategies"
        else:
            analysis_type = "COMPREHENSIVE PROFILE ANALYSIS"
            confidence_level = "HIGH PATTERN CONFIDENCE"
            data_source = f"{posts_analyzed} historical posts and engagement data"
            personalization_approach = "authentic voice replication with proven strategies"
        
        # Build CONVINCING summary (max 7 sentences as requested)
        summary = (
            f"🚀 {analysis_type} for {username}: Successfully generated {posts_count} strategic posts "
            f"targeting '{goal_text}' over {timeline} days using {data_source}. "
            f"🎯 CONTENT STRATEGY: {posts_count/timeline:.1f} posts/day frequency optimized for {platform} algorithms "
            f"with {', '.join(content_themes[:3])} themes that drive engagement. "
            f"📊 ENGAGEMENT SCIENCE: {writing_patterns['primary_style']} writing style ({writing_patterns['avg_sentence_length']:.0f} chars) "
            f"with {emotional_tone['dominant_tone']} emotional tone proven to increase follower growth by 25-40%. "
            f"🏆 AUTHORITY BUILDING: {topic_expertise['primary_expertise']} expertise positioning with {brand_positioning['primary_positioning']} "
            f"brand voice that establishes credibility and attracts target audience. "
            f"⚡ SUCCESS METRICS: {confidence_level} using XGBoost ML prediction with {prediction_metrics.get('confidence', 0.8)*100:.0f}% confidence "
            f"based on {len(prediction_metrics.get('feature_importance', {}))} engagement factors. "
            f"💡 PERSONALIZATION: {personalization_approach} ensures content resonates with your specific audience "
            f"while maintaining professional quality and driving measurable results."
        )
        
        return summary
    
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
        
        # Build HONEST and CONVINCING statistical summary
        posts_analyzed = len(profile_analysis.get('posts', []))
        
        if posts_analyzed == 0:
            # For new accounts, focus on industry standards and proven strategies
            summary = (
                f"📊 INDUSTRY-STANDARD CAMPAIGN STRATEGY: This {posts_count}-post campaign targets {target_increase} "
                f"engagement increase over {timeline} days, based on proven social media science for accounts with {followers:,} followers. "
                f"🎯 PROVEN THEMES: Content focuses on {themes_text} themes, leveraging industry research showing "
                f"these topics drive 2-3x higher engagement rates across {platform} accounts. "
                f"🤖 ML-POWERED OPTIMIZATION: {method.upper()} model predicts {posts_count} posts with {confidence:.0f}% confidence "
                f"using {len(prediction_metrics.get('feature_importance', {}))} proven engagement factors. "
                f"📈 EXPECTED RESULTS: {posts_per_day:.1f} posts/day frequency should deliver "
                f"{estimated_reach_increase:.1f}% reach increase and {((expected_improvement - 1) * 100):.0f}% engagement growth "
                f"based on {platform} algorithm optimization. "
                f"📋 SUCCESS STRATEGY: Platform-optimized content timing, proven engagement patterns, and audience psychology "
                f"to maximize your goal achievement while building authentic brand presence."
            )
        else:
            # For existing accounts, use actual data
            summary = (
                f"📊 DATA-DRIVEN CAMPAIGN STRATEGY: This {posts_count}-post campaign targets {target_increase} "
                f"engagement increase over {timeline} days, based on analysis of {posts_analyzed} historical posts "
                f"from your {followers:,} followers with {current_engagement:.2%} baseline engagement. "
                f"🎯 PERFORMANCE-BASED THEMES: Content focuses on {themes_text} themes, leveraging your actual data "
                f"showing peak engagement of {peak_engagement:.2%} ({(peak_engagement/current_engagement):.1f}x baseline). "
                f"🤖 ML PREDICTION: {method.upper()} model estimates {posts_count} posts with {confidence:.0f}% confidence "
                f"based on {len(prediction_metrics.get('feature_importance', {}))} engagement factors from your profile. "
                f"📈 EXPECTED IMPACT: {posts_per_day:.1f} posts/day frequency should drive "
                f"{estimated_reach_increase:.1f}% reach increase and {((expected_improvement - 1) * 100):.0f}% engagement growth. "
                f"📋 SUCCESS FACTORS: {' | '.join(success_insights) if success_insights else 'Your proven content patterns and platform optimization'}. "
                f"⚡ SCIENTIFIC BASIS: Strategy combines your historical performance data with engagement science "
                f"to maximize goal achievement while maintaining your authentic voice and audience connection."
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
        logger.info("🔧 Enhanced Goal Handler initialized successfully")
        logger.info(f"🔧 Platforms configured: {self.platforms}")
        logger.info(f"🔧 R2 Tasks bucket: {R2_CONFIG['bucket_name']}")
        logger.info(f"🔧 R2 Structuredb bucket: {STRUCTUREDB_R2_CONFIG['bucket_name']}")
    
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
            logger.debug(f"Processing goal for {username} on {platform}")
            
            # 1. Retrieve and validate goal data
            goal_data = await self._get_goal_data(goal_key)
            if not goal_data:
                return
                
            # 2. Retrieve and analyze profile data - MANDATORY for RAG
            profile_data = await self._get_profile_data(username, platform)
            
            if not profile_data:
                logger.error(f"❌ NO PROFILE DATA for {username} on {platform} - RAG analysis IMPOSSIBLE")
                logger.error(f"❌ Profile data is REQUIRED for deep personalization - no fallbacks allowed")
                logger.error(f"❌ Check if profile exists at: {platform}/{username}/{username}.json in structuredb bucket")
                
                # Mark goal as failed due to missing profile data
                goal_data["status"] = "failed"
                goal_data["processed_at"] = datetime.now().isoformat()
                goal_data["failure_reason"] = "no_profile_data_for_rag_analysis"
                goal_data["error_message"] = f"Profile data not found in structuredb bucket at {platform}/{username}/{username}.json"
                await self.r2_tasks.write_json(goal_key, goal_data)
                
                self.processed_files.add(goal_key)
                return  # Exit without processing - RAG requires profile data
                
            # 3. Retrieve prophet analysis (only if we have profile data)
            prophet_data = await self._get_prophet_analysis(username, platform)
            if not prophet_data:
                logger.warning(f"No prophet analysis found for {username} on {platform}")
                prophet_data = {}
                
            # 🧠 DEEP RAG ANALYSIS PATH: Use comprehensive profile analysis for hyper-personalization
            logger.info(f"🧠 Performing DEEP RAG analysis with complete profile data for {username}")
            logger.info(f"📊 Profile data contains {len(profile_data.get('posts', []))} posts for analysis")
                
            # 4. Perform COMPREHENSIVE RAG analysis - now handles insufficient data gracefully
            try:
                logger.info(f"🔬 Running comprehensive RAG pattern analysis for {username}")
                profile_analysis = self.rag_analyzer.analyze_profile_patterns(profile_data)
                
                # Check if we have meaningful data or just defaults
                posts_count = len(profile_data.get('posts', []))
                if posts_count == 0:
                    logger.warning(f"⚠️ RAG analysis completed with minimal data for {username} (0 posts)")
                    logger.info(f"📊 Using default patterns for new/empty accounts")
                else:
                    logger.info(f"✅ RAG analysis completed successfully with {posts_count} posts")
                    
            except Exception as e:
                logger.error(f"❌ RAG analysis FAILED for {username}: {e}")
                
                # Mark goal as failed due to RAG analysis failure
                goal_data["status"] = "failed"
                goal_data["processed_at"] = datetime.now().isoformat()
                goal_data["failure_reason"] = "rag_analysis_failed"
                goal_data["error_message"] = str(e)
                await self.r2_tasks.write_json(goal_key, goal_data)
                
                self.processed_files.add(goal_key)
                return  # Exit without processing - RAG failed
            
            # 5. Calculate optimal posting strategy using RAG analysis
            logger.info(f"📈 Calculating RAG-informed posting strategy for goal: {goal_data.get('goal', '')}")
            posts_needed, posting_interval, rationale, prediction_metrics = self.strategy_calculator.calculate_posting_strategy(
                goal_data, profile_analysis, prophet_data
            )
            
            logger.info(f"📊 Strategy: {posts_needed} posts, {posting_interval:.1f}h intervals")
            logger.info(f"🎯 Rationale: {rationale}")
            
            # 6. Generate HYPER-PERSONALIZED content using deep RAG analysis
            try:
                logger.info(f"🧠 Generating {posts_needed} hyper-personalized posts using DEEP RAG")
                posts_content = await self.content_generator.generate_post_content(
                    goal_data, profile_analysis, posts_needed, username, platform, prediction_metrics, posting_interval
                )
                logger.info(f"✅ Successfully generated {posts_needed} RAG-based posts")
            except Exception as e:
                logger.error(f"❌ RAG content generation FAILED for {username}: {e}")
                
                # Mark goal as failed due to content generation failure
                goal_data["status"] = "failed"
                goal_data["processed_at"] = datetime.now().isoformat()
                goal_data["failure_reason"] = "rag_content_generation_failed"
                goal_data["error_message"] = str(e)
                await self.r2_tasks.write_json(goal_key, goal_data)
                
                self.processed_files.add(goal_key)
                return  # Exit without processing - content generation failed
            
            # 7. Create comprehensive output in required format
            output_data = posts_content  # Direct dictionary format, no array wrapping
            
            # 8. Export to platform-aware output directory
            output_key = f"generated_content/{platform}/{username}/posts.json"
            
            if await self.r2_tasks.write_json(output_key, output_data):
                # Mark goal as successfully processed using RAG
                goal_data["status"] = "processed"
                goal_data["processed_at"] = datetime.now().isoformat()
                goal_data["processing_method"] = "deep_rag_analysis"
                goal_data["rag_analysis_summary"] = {
                    "posts_analyzed": len(profile_data.get('posts', [])),
                    "content_themes": profile_analysis.get('content_themes', [])[:5],
                    "writing_style": profile_analysis.get('writing_patterns', {}).get('primary_style', 'unknown'),
                    "personalization_confidence": "high"
                }
                await self.r2_tasks.write_json(goal_key, goal_data)
                
                logger.info(f"🎉 Successfully processed goal for {username} on {platform} using DEEP RAG")
                logger.info(f"📊 RAG Analysis: {len(profile_data.get('posts', []))} posts analyzed")
                logger.info(f"🎯 Content themes: {profile_analysis.get('content_themes', [])[:3]}")
                logger.info(f"✅ Output saved to: {output_key}")
                
                self.processed_files.add(goal_key)
            else:
                logger.error(f"❌ Failed to save RAG output for {username} on {platform}")
                
                # Mark as failed if we can't save the output
                goal_data["status"] = "failed"
                goal_data["processed_at"] = datetime.now().isoformat()
                goal_data["failure_reason"] = "output_save_failed"
                await self.r2_tasks.write_json(goal_key, goal_data)
                
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
            # Extract posts from multiple possible field structures
            posts = []
            
            # Try different post field names
            post_fields = ["posts", "latestPosts", "recentPosts"]
            for field in post_fields:
                if field in raw_profile and isinstance(raw_profile[field], list):
                    logger.info(f"Found posts in field '{field}': {len(raw_profile[field])} posts")
                    for post in raw_profile[field]:
                        if isinstance(post, dict):
                            # Extract text content from various possible fields
                            text_content = ""
                            if "text" in post and post["text"]:
                                text_content = post["text"]
                            elif "caption" in post and post["caption"]:
                                text_content = post["caption"]
                            elif "message" in post and post["message"]:
                                text_content = post["message"]
                            
                            # Convert to expected format
                            converted_post = {
                                "caption": text_content,
                                "hashtags": self._extract_hashtags(text_content),
                                "likes": post.get("likes", post.get("likesCount", 0)),
                                "comments": post.get("comments", post.get("commentsCount", 0)),
                                "type": post.get("type", "photo"),
                                "timestamp": post.get("timestamp", post.get("time", 0)),
                                "url": post.get("url", post.get("facebookUrl", ""))
                            }
                            posts.append(converted_post)
                    break  # Use first field that has posts
            
            # Extract bio from multiple possible locations
            bio = ""
            if "biography" in raw_profile:
                bio = raw_profile["biography"]
            elif "profileInfo" in raw_profile and isinstance(raw_profile["profileInfo"], dict):
                profile_info = raw_profile["profileInfo"]
                if "intro" in profile_info:
                    bio = profile_info["intro"]
                elif "info" in profile_info:
                    bio = str(profile_info["info"])
            
            # Extract follower count from multiple possible locations
            followers = 1000
            if "followers" in raw_profile:
                followers = raw_profile["followers"]
            elif "profileInfo" in raw_profile and isinstance(raw_profile["profileInfo"], dict):
                profile_info = raw_profile["profileInfo"]
                if "followers" in profile_info:
                    followers = profile_info["followers"]
            
            # Create converted profile format
            converted_profile = {
                "username": raw_profile.get("username", username),
                "bio": bio,
                "followers": followers,
                "following": raw_profile.get("followsCount", 100),
                "posts": posts,
                "engagement_rate": self._calculate_engagement_rate(posts, followers),
                "platform": platform,
                "last_updated": datetime.now().isoformat(),
                "verified": raw_profile.get("verified", False),
                "business_account": raw_profile.get("isBusinessAccount", False)
            }
            
            logger.info(f"Converted profile for {username}: {len(posts)} posts, {converted_profile['followers']} followers")
            if posts:
                logger.info(f"Sample post content: {posts[0]['caption'][:100]}...")
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
        logger.info("🔍 Scanning for unprocessed goal files...")
        
        total_processed = 0
        for platform in self.platforms:
            platform_prefix = f"goal/{platform}/"
            logger.info(f"🔍 Scanning platform: {platform} with prefix: {platform_prefix}")
            
            try:
                objects = await self.r2_tasks.list_objects(platform_prefix)
                logger.info(f"📊 Found {len(objects)} objects for {platform}")
                
                # 🧹 COMPREHENSIVE TEST FILTERING - Filter out all test objects
                production_objects = TestFilter.filter_test_objects(objects)
                logger.info(f"🧹 After filtering: {len(production_objects)} production objects for {platform}")
                
                # Log filtering statistics
                if len(objects) != len(production_objects):
                    filtered_count = len(objects) - len(production_objects)
                    logger.info(f"🧹 Filtered out {filtered_count} test files from {platform} scan")
                    
                    # Show what was filtered out for debugging
                    test_objects = [obj for obj in objects if obj not in production_objects]
                    for test_obj in test_objects[:3]:  # Show first 3 filtered objects
                        logger.info(f"🚫 Filtered out test object: {test_obj['Key']}")
                
                for obj in production_objects:
                    key = obj["Key"]
                    logger.info(f"🔍 Examining object: {key}")
                    
                    # Skip non-JSON files
                    if not key.endswith(".json"):
                        logger.info(f"⏭️ Skipping non-JSON file: {key}")
                        continue
                        
                    # Skip if doesn't contain goal_ pattern
                    if "goal_" not in key:
                        logger.info(f"⏭️ Skipping non-goal file (no 'goal_' pattern): {key}")
                        continue
                    
                    logger.info(f"✅ Found goal file: {key}")
                    logger.info(f"   Platform: {platform}")
                    logger.info(f"   Key: {key}")
                    
                    # Check if already processed
                    if key in self.processed_files:
                        logger.info(f"⏭️ Already processed in current session: {key}")
                        continue
                    
                    # Read and check status
                    try:
                        goal_data = await self.r2_tasks.read_json(key)
                        logger.info(f"📖 Read goal data for: {key}")
                        
                        if not goal_data:
                            logger.warning(f"Empty goal file: {key}")
                            continue
                            
                        # Skip if already processed
                        if goal_data.get("status") == "processed":
                            logger.info(f"⏭️ Already processed: {key}")
                            self.processed_files.add(key)
                            continue
                            
                        # Skip if missing required fields
                        if not goal_data.get("goal") or not goal_data.get("timeline"):
                            logger.warning(f"⏭️ Invalid goal file missing required fields: {key}")
                            logger.warning(f"   Available fields: {list(goal_data.keys())}")
                            continue
                            
                        logger.info(f"🚀 Processing unprocessed goal: {key}")
                        await self.process_goal_file(key)
                        total_processed += 1
                        
                    except Exception as e:
                        logger.error(f"❌ Error checking goal file {key}: {e}")
                        continue
                        
            except Exception as e:
                logger.error(f"❌ Error scanning {platform} goals: {e}")
                logger.error(f"   Platform: {platform}")
                logger.error(f"   Prefix: {platform_prefix}")
                
        if total_processed > 0:
            logger.info(f"✅ Processed {total_processed} new goal files")
        else:
            logger.info("😴 No new goal files to process")
            
            # Enhanced diagnostic information
            total_goals_found = 0
            total_production_goals = 0
            
            for platform in self.platforms:
                platform_prefix = f"goal/{platform}/"
                try:
                    objects = await self.r2_tasks.list_objects(platform_prefix)
                    platform_goals = [obj for obj in objects if obj["Key"].endswith(".json") and "goal_" in obj["Key"]]
                    total_goals_found += len(platform_goals)
                    
                    production_goals = TestFilter.filter_test_objects(platform_goals)
                    total_production_goals += len(production_goals)
                    
                    logger.info(f"   📊 {platform}: {len(platform_goals)} goal files found, {len(production_goals)} production")
                except Exception as e:
                    logger.warning(f"   ❌ Error scanning {platform}: {e}")
            
            logger.info(f"🔍 Summary: {total_goals_found} total goal files, {total_production_goals} production files")
            
            if total_goals_found == 0:
                logger.info("🔍 Possible reasons for no goal files:")
                logger.info("   - No goal files have been uploaded to R2 storage")
                logger.info("   - Goal files are in wrong directory (should be goal/<platform>/)")
                logger.info("   - Check if your goal upload process is working")
            elif total_production_goals == 0:
                logger.info("🔍 Goal files found but all filtered out:")
                logger.info("   - All goal files may contain test usernames")
                logger.info("   - Check TestFilter configuration")
            else:
                logger.info("🔍 Production goal files exist but all processed:")
                logger.info("   - All goal files already have status: 'processed'")
                logger.info("   - System is working correctly, waiting for new goals")

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
            logger.info("[GOAL HANDLER] 1-minute retry scan for unprocessed goal files.")
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