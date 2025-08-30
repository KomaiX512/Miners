"""
RAG Implementation - The ORIGINAL and ONLY RAG file used in the pipeline.
Enhanced with bulletproof JSON parsing to handle production issues.
"""

import json
import re
import logging
from typing import List, Dict, Any, Optional
import time
import google.generativeai as genai
from config import GEMINI_CONFIG

# Set up logging
logger = logging.getLogger(__name__)

class OptimizedRateLimiter:
    """Rate limiter for API calls."""
    
    def __init__(self, requests_per_minute=14):
        self.requests_per_minute = requests_per_minute
        self.min_delay = 60.0 / requests_per_minute
        self.last_request_time = 0
        
    def wait_if_needed(self):
        """Wait if needed to respect rate limits."""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.min_delay:
            sleep_time = self.min_delay - time_since_last
            logger.info(f"🕒 Rate limiting: waiting {sleep_time:.1f}s")
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()

class RagImplementation:
    """The original RAG implementation with bulletproof JSON parsing."""
    
    def __init__(self, vector_db=None):
        """Initialize RAG with vector database."""
        self.vector_db = vector_db
        self.rate_limiter = OptimizedRateLimiter()
        
        # Configure Gemini
        genai.configure(api_key=GEMINI_CONFIG['api_key'])
        self.model = genai.GenerativeModel(GEMINI_CONFIG['model'])
        
        logger.info("✅ RAG Implementation initialized with bulletproof JSON parsing")
    
    def _bulletproof_json_parse(self, response_text):
        """
        BULLETPROOF JSON PARSER - Simple, reliable, never fails on legitimate content.
        Handles common Gemini formatting quirks without complex regex.
        """
        try:
            # Step 1: Basic cleanup - remove code blocks
            text = response_text.strip()
            
            # Remove markdown code blocks (simple approach)
            if text.startswith('```'):
                lines = text.split('\n')
                # Remove first line if it's ```json or ```
                if lines[0].strip().startswith('```'):
                    lines = lines[1:]
                # Remove last line if it's ```
                if lines and lines[-1].strip() == '```':
                    lines = lines[:-1]
                text = '\n'.join(lines)
            
            # Step 2: Find JSON boundaries (simple, reliable)
            start = text.find('{')
            if start == -1:
                raise ValueError("No JSON object found")
            
            # Find matching closing brace by counting
            brace_count = 0
            end = start
            for i, char in enumerate(text[start:], start):
                if char == '{':
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        end = i + 1
                        break
            
            if brace_count != 0:
                # Incomplete JSON - try adding missing braces
                json_text = text[start:] + '}' * brace_count
            else:
                json_text = text[start:end]
            
            # Step 3: Parse JSON with error handling
            try:
                result = json.loads(json_text)
                logger.info("✅ Bulletproof JSON parse successful")
                return result
            except json.JSONDecodeError as e:
                # Last resort: try to fix common issues
                logger.info(f"JSON error at position {e.pos}, attempting repair...")
                
                # Fix unterminated strings by finding the error position
                if 'Unterminated string' in str(e):
                    # Find the unterminated string and close it
                    error_pos = e.pos
                    before_error = json_text[:error_pos]
                    after_error = json_text[error_pos:]
                    
                    # Add closing quote if needed
                    if before_error.count('"') % 2 == 1:  # Odd number of quotes = unterminated
                        repaired = before_error + '"' + after_error
                        result = json.loads(repaired)
                        logger.info("✅ Repaired unterminated string successfully")
                        return result
                
                # If repair fails, raise the original error
                raise e
                
        except Exception as e:
            logger.error(f"❌ Bulletproof JSON parser failed: {str(e)}")
            logger.error(f"Raw text sample: {response_text[:500]}...")
            raise ValueError(f"Could not parse JSON from response: {str(e)}")
    
    def generate_recommendation(self, primary_username, secondary_usernames=None, query=None, 
                              is_branding=False, platform="instagram", username=None, posts=None, 
                              competitor_data=None, account_type="personal"):
        """
        Generate content recommendations with bulletproof JSON parsing.
        Compatible with all existing method signatures.
        """
        try:
            # Handle different parameter combinations for compatibility
            if username and not primary_username:
                primary_username = username
            if not query:
                query = f"Generate content recommendations for {primary_username}"
            
            # Rate limiting
            self.rate_limiter.wait_if_needed()
            
            # Build prompt
            prompt = self._build_recommendation_prompt(
                primary_username, secondary_usernames, query, is_branding, 
                platform, posts, competitor_data, account_type
            )
            
            # Generate with retries
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    logger.info(f"📡 Attempt {attempt + 1}: Sending prompt to Gemini...")
                    
                    response = self.model.generate_content(prompt)
                    
                    if response and response.text:
                        logger.info(f"✅ Received response ({len(response.text)} chars)")
                        
                        # Use bulletproof JSON parser
                        result = self._bulletproof_json_parse(response.text)
                        
                        # Validate response structure
                        if self._validate_response(result):
                            logger.info("🎉 RAG recommendation generated successfully!")
                            return result
                        else:
                            logger.warning("⚠️ Response validation failed, retrying...")
                            continue
                    else:
                        logger.error(f"❌ Empty response on attempt {attempt + 1}")
                        continue
                        
                except Exception as e:
                    logger.error(f"❌ Error on attempt {attempt + 1}: {e}")
                    if attempt == max_retries - 1:
                        raise
                    time.sleep(2)  # Brief delay before retry
            
            # If all attempts fail
            raise Exception(f"Failed to generate recommendation after {max_retries} attempts")
            
        except Exception as e:
            logger.error(f"RAG recommendation generation failed: {str(e)}")
            raise
    
    def _build_recommendation_prompt(self, primary_username, secondary_usernames, query, 
                                   is_branding, platform, posts, competitor_data, account_type):
        """Build comprehensive prompt for content generation."""
        
        prompt = f"""
        Generate comprehensive content recommendations for {primary_username} on {platform}.
        
        Account Details:
        - Username: {primary_username}
        - Platform: {platform}
        - Account Type: {account_type}
        - Is Branding: {is_branding}
        
        Query: {query}
        
        """
        
        if posts and len(posts) > 0:
            prompt += f"\nRecent Posts ({len(posts)}):\n"
            for i, post in enumerate(posts[:5]):  # Limit to 5 posts
                content = post.get('caption', post.get('text', post.get('content', '')))[:200]
                prompt += f"{i+1}. {content}...\n"
        
        if competitor_data:
            prompt += f"\nCompetitor Analysis:\n"
            for comp_name, comp_info in competitor_data.items():
                prompt += f"- {comp_name}: {str(comp_info)[:200]}...\n"
        
        if secondary_usernames:
            prompt += f"\nCompetitors to consider: {', '.join(secondary_usernames)}\n"
        
        # Determine intelligence type based on account type
        intelligence_type = "competitive_intelligence" if is_branding else "personal_intelligence"
        
        prompt += f"""
        
        Use the account's recent content, engagement metrics, and platform-wide trending data to identify up to 3 high-engagement hashtags most relevant to the account's domain.

Respond with a JSON object containing:
        {{
            "tactical_recommendations": ["rec1", "rec2", "rec3"],
            "content_strategy": "strategic advice",
            "engagement_insights": "engagement analysis",
            "trending_hashtags": ["#dynamic_hashtag1", "#dynamic_hashtag2", "#dynamic_hashtag3", "#dynamic_hashtag4", "#dynamic_hashtag5", "#dynamic_hashtag6", "#dynamic_hashtag7", "#dynamic_hashtag8", "#dynamic_hashtag9", "#dynamic_hashtag10"],
            "trending_hashtags_reason": "Sentence 1. Sentence 2.",
            "competitive_advantage": "competitive positioning",
            "{intelligence_type}": {{
                "account_analysis": "Detailed analysis of the account's current state",
                "growth_opportunities": "Specific opportunities for improvement",
                "audience_insights": "Understanding of target audience behavior",
                "performance_optimization": "Strategies to optimize content performance"
            }}
        }}
        
        Ensure the JSON is valid and complete.
        """
        
        return prompt
    
    def _validate_response(self, response):
        """Validate response structure."""
        if not isinstance(response, dict):
            return False
        
        required_fields = ["tactical_recommendations", "trending_hashtags", "trending_hashtags_reason"]
        intelligence_fields = ["personal_intelligence", "competitive_intelligence"]
        
        # All required_fields MUST be present
        has_all_required = all(field in response for field in required_fields)
        # At least one intelligence field must be present
        has_intelligence = any(field in response for field in intelligence_fields)

        # Additional defensive checks – ensure trending_hashtags is a non-empty list
        if has_all_required and isinstance(response.get("trending_hashtags"), list):
            has_hashtags = len(response["trending_hashtags"]) > 0
        else:
            has_hashtags = False
        
        return has_all_required and has_intelligence and has_hashtags

# Compatibility exports for existing imports
UNIFIED_MODULE_STRUCTURE = {
    # Instagram configurations
    "INSTAGRAM_BRANDING": {
        "intelligence_type": "competitive_intelligence",
        "required_fields": {
            "competitive_intelligence": [
                "competitive_analysis",
                "market_opportunities", 
                "strategic_insights",
                "optimization_strategies"
            ]
        }
    },
    "INSTAGRAM_PERSONAL": {
        "intelligence_type": "personal_intelligence",
        "required_fields": {
            "personal_intelligence": [
                "account_analysis",
                "growth_opportunities",
                "audience_insights",
                "performance_optimization"
            ]
        }
    },
    # Twitter configurations  
    "TWITTER_BRANDING": {
        "intelligence_type": "competitive_intelligence",
        "required_fields": {
            "competitive_intelligence": [
                "competitive_analysis",
                "market_opportunities",
                "strategic_insights", 
                "optimization_strategies"
            ]
        }
    },
    "TWITTER_PERSONAL": {
        "intelligence_type": "personal_intelligence",
        "required_fields": {
            "personal_intelligence": [
                "account_analysis",
                "growth_opportunities",
                "audience_insights",
                "performance_optimization"
            ]
        }
    },
    # Facebook configurations
    "FACEBOOK_BRANDING": {
        "intelligence_type": "competitive_intelligence",
        "required_fields": {
            "competitive_intelligence": [
                "competitive_analysis",
                "market_opportunities",
                "strategic_insights",
                "optimization_strategies"
            ]
        }
    },
    "FACEBOOK_PERSONAL": {
        "intelligence_type": "personal_intelligence",
        "required_fields": {
            "personal_intelligence": [
                "account_analysis",
                "growth_opportunities",
                "audience_insights",
                "performance_optimization"
            ]
        }
    }
}

# Test functions removed for production use
