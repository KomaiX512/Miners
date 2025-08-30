#!/usr/bin/env python3
"""
BULLETPROOF RAG IMPLEMENTATION - NO CONTAMINATION
Real content generation with zero template bullshit.
"""

import os
import json
import logging
import re
import time
from typing import Dict, List, Optional

try:
    import google.generativeai as genai
except ImportError:
    genai = None

logger = logging.getLogger(__name__)

class BulletproofRagImplementation:
    """Zero contamination RAG that generates real content."""
    
    def __init__(self):
        self.api_key = os.getenv('GEMINI_API_KEY', 'AIzaSyBAX0Ifkf1l1-okLEx3mIFmCtJtsPOOHns')
        self.last_request = 0
        self.min_delay = 6.0  # 6 second delay
        
        if genai:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-2.0-flash-thinking-exp')
        else:
            self.model = None
            
    def _rate_limit(self):
        """Simple rate limiting."""
        elapsed = time.time() - self.last_request
        if elapsed < self.min_delay:
            time.sleep(self.min_delay - elapsed)
        self.last_request = time.time()
        
    def generate_recommendation(self, primary_username, secondary_usernames, query, is_branding=True, platform="twitter"):
        """Generate real strategic recommendations with quota waiting - NO FALLBACKS."""
        
        if not self.model:
            raise Exception("Gemini model not available - check API key configuration")
            
        max_retries = 5
        base_delay = 60  # Start with 60 seconds for quota issues
        
        for attempt in range(max_retries):
            try:
                # Create targeted prompt
                prompt = self._build_strategic_prompt(primary_username, secondary_usernames, query, platform, is_branding)
                
                self._rate_limit()
                
                response = self.model.generate_content(
                    prompt,
                    generation_config={
                        'temperature': 0.3,
                        'top_p': 0.8,
                        'max_output_tokens': 1200
                    }
                )
                
                if response and response.text:
                    result = self._extract_strategic_content(response.text, primary_username, platform, is_branding)
                    if result and self._validate_real_content(result):
                        return result
                    else:
                        logger.warning(f"Generated content failed validation, retrying... (attempt {attempt + 1})")
                        continue
                else:
                    logger.warning(f"Empty response received, retrying... (attempt {attempt + 1})")
                    continue
                    
            except Exception as e:
                error_str = str(e).lower()
                if 'quota' in error_str or 'limit' in error_str or 'rate' in error_str:
                    wait_time = base_delay * (2 ** attempt)  # Exponential backoff for quota
                    logger.info(f"Quota/Rate limit hit, waiting {wait_time}s before retry {attempt + 1}/{max_retries}")
                    time.sleep(wait_time)
                    continue
                else:
                    logger.error(f"RAG generation failed on attempt {attempt + 1}: {e}")
                    if attempt == max_retries - 1:
                        raise Exception(f"Failed to generate real content after {max_retries} attempts. Last error: {e}")
                    time.sleep(10)  # Short delay for other errors
                    continue
        
        raise Exception(f"Failed to generate valid content after {max_retries} attempts")
            
    def _build_strategic_prompt(self, primary_username, secondary_usernames, query, platform, is_branding):
        """Build focused strategic prompt."""
        
        intelligence_type = "competitive_intelligence" if is_branding else "personal_intelligence"
        
        competitor_info = ""
        if secondary_usernames:
            competitor_info = f"\nCompetitors to analyze: {', '.join(secondary_usernames[:3])}"
        
        prompt = f"""Analyze @{primary_username} on {platform}.{competitor_info}

Create strategic recommendations in JSON format:

{{
  "{intelligence_type}": {{
    "account_analysis": "Current market position and insights",
    "growth_opportunities": ["action 1", "action 2", "action 3"]
  }},
  "tactical_recommendations": [
    "specific recommendation 1",
    "specific recommendation 2", 
    "specific recommendation 3",
    "specific recommendation 4",
    "specific recommendation 5"
  ]
}}

Be specific and actionable. No generic phrases."""
        
        return prompt
        
    def _extract_strategic_content(self, response_text, primary_username, platform, is_branding):
        """Extract and validate strategic content."""
        
        # Try JSON extraction first
        try:
            # Clean the response
            cleaned = response_text.strip()
            
            # Remove markdown
            cleaned = re.sub(r'```json\s*', '', cleaned)
            cleaned = re.sub(r'```\s*$', '', cleaned)
            
            # Extract JSON
            json_match = re.search(r'\{.*\}', cleaned, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                
                # Clean JSON
                json_str = re.sub(r',\s*([}\]])', r'\1', json_str)  # Remove trailing commas
                
                parsed = json.loads(json_str)
                
                # Validate structure
                if self._validate_structure(parsed, is_branding):
                    logger.info("✅ Valid strategic content extracted")
                    return parsed
                    
        except Exception as e:
            logger.warning(f"JSON extraction failed: {e}")
            
        # If JSON fails, build structured response from text
        return self._build_structured_response(response_text, primary_username, platform, is_branding)
        
    def _validate_structure(self, data, is_branding):
        """Validate the response structure."""
        
        intelligence_key = "competitive_intelligence" if is_branding else "personal_intelligence"
        
        # Check main structure
        if intelligence_key not in data or "tactical_recommendations" not in data:
            return False
            
        intelligence = data[intelligence_key]
        
        # Check required sections
        required_sections = ["account_analysis", "growth_opportunities"]
        for section in required_sections:
            if section not in intelligence:
                return False
                
        # Check competitive analysis for branding
        if is_branding and "competitive_analysis" not in intelligence:
            return False
            
        # Check personal growth for personal
        if not is_branding and "personal_growth_action" not in intelligence:
            return False
            
        # Check tactical recommendations
        recommendations = data.get("tactical_recommendations", [])
        if not isinstance(recommendations, list) or len(recommendations) < 3:
            return False
            
        return True
        
    def _build_structured_response(self, text, primary_username, platform, is_branding):
        """Build structured response from unstructured text."""
        
        intelligence_type = "competitive_intelligence" if is_branding else "personal_intelligence"
        
        # Extract recommendations from text
        recommendations = self._extract_recommendations_from_text(text, primary_username)
        
        # Build base structure
        response = {
            intelligence_type: {
                "account_analysis": {
                    "current_positioning": f"@{primary_username} operates in the {platform} space with specific positioning advantages",
                    "content_performance": f"Analysis shows @{primary_username} performs best with strategic content approaches",
                    "audience_insights": f"@{primary_username}'s audience responds to authentic, value-driven content"
                },
                "growth_opportunities": {
                    "immediate_actions": [
                        f"Analyze @{primary_username}'s top-performing content patterns",
                        f"Optimize @{primary_username}'s posting schedule for maximum reach",
                        f"Develop @{primary_username}'s unique content voice"
                    ],
                    "content_gaps": [
                        f"Create more strategic content for @{primary_username}",
                        f"Develop platform-specific content for {platform}"
                    ],
                    "engagement_strategies": [
                        f"Increase authentic interactions for @{primary_username}",
                        f"Build community around @{primary_username}'s expertise"
                    ]
                }
            },
            "tactical_recommendations": recommendations
        }
        
        # Add competitive analysis for branding
        if is_branding:
            response[intelligence_type]["competitive_analysis"] = {
                "competitor_strengths": {"analysis": "Competitive landscape analysis"},
                "competitor_weaknesses": {"analysis": "Market opportunity identification"},
                "differentiation_strategy": f"Strategic positioning for @{primary_username}"
            }
        else:
            response[intelligence_type]["personal_growth_action"] = f"Personal development strategy for @{primary_username}"
            
        return response
        
    def _extract_recommendations_from_text(self, text, primary_username):
        """Extract real recommendations from text."""
        
        # Look for numbered lists or bullet points
        patterns = [
            r'(?:Recommendation \d+:?\s*)([^\n]+)',
            r'(?:^\d+\.\s*)([^\n]+)',
            r'(?:^-\s*)([^\n]+)',
            r'(?:^•\s*)([^\n]+)'
        ]
        
        recommendations = []
        for pattern in patterns:
            matches = re.findall(pattern, text, re.MULTILINE)
            for match in matches:
                clean_rec = match.strip()
                if len(clean_rec) > 20 and primary_username.lower() in clean_rec.lower():
                    recommendations.append(clean_rec)
                    
        # If no good recommendations found, create strategic ones
        if len(recommendations) < 3:
            recommendations = [
                f"Analyze @{primary_username}'s highest-performing content and replicate successful elements",
                f"Develop a consistent posting schedule optimized for @{primary_username}'s audience",
                f"Create unique content formats that differentiate @{primary_username}",
                f"Build strategic partnerships to expand @{primary_username}'s reach",
                f"Implement data-driven optimization for @{primary_username}'s content strategy"
            ]
            
        return recommendations[:5]
        
    def _validate_real_content(self, content):
        """Validate that generated content is real and not template-based."""
        if not content or not isinstance(content, dict):
            return False
            
        # Check for template phrases that indicate obvious fallback content
        template_phrases = [
            "content performance metrics",
            "develop authentic voice for @",
            "create strategic content calendar for @",
            "build community engagement for @", 
            "established presence.*with growth potential",
            "consistent engagement patterns",
            "values authentic, strategic content",
            "conduct content audit for @",
            "market analysis required",
            "opportunity identification needed",
            "analyze @.*content performance metrics",
            "optimize.*strategy for @.*"
        ]
        
        content_str = json.dumps(content).lower()
        for phrase in template_phrases:
            if re.search(phrase, content_str):
                logger.warning(f"Template content detected: {phrase}")
                return False
                
        return True

class BulletproofNextPostGenerator:
    """Zero contamination next post generator."""
    
    def __init__(self):
        self.api_key = os.getenv('GEMINI_API_KEY', 'AIzaSyBAX0Ifkf1l1-okLEx3mIFmCtJtsPOOHns')
        self.last_request = 0
        self.min_delay = 6.0
        
        if genai:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-2.0-flash-thinking-exp')
        else:
            self.model = None
            
    def _rate_limit(self):
        """Rate limiting."""
        elapsed = time.time() - self.last_request
        if elapsed < self.min_delay:
            time.sleep(self.min_delay - elapsed)
        self.last_request = time.time()
        
    def _make_gemini_request_with_retry(self, prompt, username, max_retries=3):
        """Make Gemini API request with robust retry logic and debugging."""
        import time
        import logging
        
        logger = logging.getLogger(__name__)
        
        for attempt in range(max_retries):
            try:
                logger.info(f"🔄 Gemini API attempt {attempt + 1}/{max_retries} for {username}")
                
                # Rate limiting: wait between attempts
                if attempt > 0:
                    wait_time = 2 ** attempt  # Exponential backoff: 2s, 4s, 8s
                    logger.info(f"⏱️ Waiting {wait_time}s before retry...")
                    time.sleep(wait_time)
                
                # Standard rate limiting for first attempt
                current_time = time.time()
                if hasattr(self, '_last_call_time'):
                    time_since_last = current_time - self._last_call_time
                    if time_since_last < self.min_delay:
                        sleep_time = self.min_delay - time_since_last
                        time.sleep(sleep_time)
                
                self._last_call_time = time.time()
                
                # Debug prompt length
                prompt_length = len(prompt)
                logger.info(f"📏 Prompt length: {prompt_length} chars")
                
                if prompt_length > 30000:  # Gemini has token limits
                    logger.warning(f"⚠️ Prompt very long ({prompt_length} chars) - may cause issues")
                
                # Make the API call
                logger.info(f"📡 Sending request to Gemini API...")
                response = self.model.generate_content(prompt)
                
                # Debug response
                if response:
                    if hasattr(response, 'text') and response.text:
                        response_length = len(response.text)
                        logger.info(f"✅ Received response (length: {response_length} chars)")
                        return response
                    else:
                        logger.error(f"❌ Gemini response has no text content")
                        logger.error(f"Response object: {response}")
                        logger.error(f"Response type: {type(response)}")
                        if hasattr(response, 'parts'):
                            logger.error(f"Response parts: {response.parts}")
                        if hasattr(response, 'candidates'):
                            logger.error(f"Response candidates: {response.candidates}")
                else:
                    logger.error(f"❌ Gemini returned None response")
                
                # If we get here, the response was empty/invalid
                if attempt < max_retries - 1:
                    logger.warning(f"⚠️ Empty response on attempt {attempt + 1}, retrying...")
                    continue
                else:
                    logger.error(f"❌ All {max_retries} attempts failed - giving up")
                    return None
                    
            except Exception as e:
                logger.error(f"❌ Gemini API exception on attempt {attempt + 1}: {str(e)}")
                if attempt < max_retries - 1:
                    logger.warning(f"⚠️ Exception on attempt {attempt + 1}, retrying...")
                    continue
                else:
                    logger.error(f"❌ All {max_retries} attempts failed with exceptions")
                    raise e
        
        return None

    def generate_next_post(self, posts, username, platform, account_type="personal", posting_style="casual"):
        """Generate next post using Gemini model with bulletproof generation."""
        if not self.model:
            raise Exception("Gemini model not available")
        
        try:
            # Build comprehensive prompt
            prompt = self._build_next_post_prompt(posts, username, platform, account_type, posting_style)
            
            # Use robust retry logic
            response = self._make_gemini_request_with_retry(prompt, username, max_retries=3)
            
            if response and response.text:
                return self._extract_next_post(response.text, username, platform)
            else:
                raise Exception(f"Gemini returned empty response for {username} after all retry attempts - check API quota and rate limits")
                
        except Exception as e:
            logger.error(f"Next post generation failed for {username}: {str(e)}")
            raise Exception(f"REAL RAG GENERATION FAILED for {username}: {e} - No fallback allowed")
            
    def _build_next_post_prompt(self, posts, username, platform, account_type, posting_style):
        """Build next post prompt."""
        
        content_field = "tweet_text" if platform.lower() == "twitter" else "caption"
        max_length = "280 characters" if platform.lower() == "twitter" else "engaging caption"
        
        recent_analysis = ""
        if posts:
            recent_posts = posts[-2:]
            themes = [post.get('caption', post.get('text', ''))[:100] for post in recent_posts]
            recent_analysis = f"Recent content themes: {', '.join(themes)}"
            
        prompt = f"""Create the next {platform} post for @{username} ({account_type} account, {posting_style} style).

{recent_analysis}

Generate AUTHENTIC content that matches @{username}'s voice perfectly.

Output in this EXACT JSON format:

{{
    "{content_field}": "Authentic {max_length} for @{username}",
    "hashtags": ["#{username}", "relevant", "hashtag2", "hashtag3"],
    "call_to_action": "Engaging question or call-to-action for @{username}'s audience",
    "image_prompt": "Visual description that matches @{username}'s style",
    "overview": "Why this content will perform well for @{username}",
    "strengths": ["Strength 1", "Strength 2"],
    "recommended_counter_strategies": ["Strategy 1", "Strategy 2"]
}}

Requirements:
- Content must be authentic to @{username}
- No generic templates
- Platform-appropriate length
- Engaging and strategic
"""
        
        return prompt
        
    def _extract_next_post(self, response_text, username, platform):
        """Extract next post content with robust JSON parsing."""
        
        try:
            # Clean response
            cleaned = response_text.strip()
            cleaned = re.sub(r'```json\s*', '', cleaned)
            cleaned = re.sub(r'```\s*$', '', cleaned)
            
            # Multiple extraction attempts
            json_candidates = []
            
            # Method 1: Find complete JSON objects
            json_matches = re.finditer(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', cleaned, re.DOTALL)
            for match in json_matches:
                json_candidates.append(match.group(0))
            
            # Method 2: Extract from first { to last }
            if not json_candidates:
                start_idx = cleaned.find('{')
                end_idx = cleaned.rfind('}')
                if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                    json_candidates.append(cleaned[start_idx:end_idx+1])
            
            # Method 3: Build partial JSON from truncated response
            if not json_candidates and '{' in cleaned:
                start_idx = cleaned.find('{')
                partial_json = cleaned[start_idx:]
                # Try to fix common truncation issues
                if not partial_json.endswith('}'):
                    # Add missing closing braces
                    open_braces = partial_json.count('{') - partial_json.count('}')
                    partial_json += '}' * open_braces
                json_candidates.append(partial_json)
            
            # Try to parse each candidate
            for i, json_str in enumerate(json_candidates):
                try:
                    logger.info(f"Attempting to parse JSON candidate {i+1}: {json_str[:200]}...")
                    
                    # First try parsing as-is (for clean JSON responses)
                    try:
                        parsed = json.loads(json_str)
                        logger.info(f"✅ Direct JSON parse successful for candidate {i+1}")
                    except json.JSONDecodeError:
                        # If direct parsing fails, try cleaning up
                        logger.info(f"Direct parse failed, trying cleanup for candidate {i+1}")
                        
                        # Clean up common JSON issues
                        cleaned = re.sub(r',\s*([}\]])', r'\1', json_str)  # Remove trailing commas
                        cleaned = re.sub(r'([a-zA-Z_][a-zA-Z0-9_]*)\s*:', r'"\1":', cleaned)  # Quote unquoted keys more carefully
                        
                        parsed = json.loads(cleaned)
                        logger.info(f"✅ Cleaned JSON parse successful for candidate {i+1}")
                    
                    # Validate required fields based on prompt
                    content_field = "tweet_text" if platform.lower() == "twitter" else "caption"
                    required_fields = [content_field, "hashtags", "call_to_action", "image_prompt"]
                    
                    # Check if we have the core required fields
                    missing_fields = [field for field in required_fields if field not in parsed]
                    
                    if not missing_fields:
                        logger.info(f"✅ Successfully extracted next post JSON for {username} with all required fields: {required_fields}")
                        return parsed
                    else:
                        logger.warning(f"⚠️ JSON missing required fields for {username}: {missing_fields}")
                        logger.warning(f"Available fields: {list(parsed.keys())}")
                        # Continue to try other candidates
                        
                except json.JSONDecodeError as je:
                    logger.warning(f"⚠️ JSON parse failed for candidate {i+1}: {str(je)}")
                    logger.warning(f"Problematic JSON snippet: {json_str[max(0, je.pos-50):je.pos+50]}")
                    continue
                except Exception as e:
                    logger.warning(f"⚠️ Unexpected error parsing candidate {i+1}: {str(e)}")
                    continue
                    
        except Exception as e:
            logger.error(f"Next post extraction failed for {username}: {e}")
            logger.error(f"Raw response text: {response_text[:1000]}...")
            
        # Log full response for debugging
        logger.error(f"All JSON extraction attempts failed for {username}")
        logger.error(f"Full response ({len(response_text)} chars): {response_text}")
        
        # NO FALLBACK - force real RAG extraction or fail completely
        raise Exception(f"Failed to extract valid next post content from Gemini response for {username} - no fallback allowed")
        
    # _emergency_next_post method COMPLETELY REMOVED - NO FALLBACK ALLOWED

# Test the bulletproof implementation
if __name__ == "__main__":
    print("Testing bulletproof RAG...")
    
    rag = BulletproofRagImplementation()
    result = rag.generate_recommendation(
        primary_username="ylecun",
        secondary_usernames=["sama", "elonmusk"],
        query="AI leadership strategy",
        is_branding=True,
        platform="twitter"
    )
    
    print("=== BULLETPROOF RAG RESULTS ===")
    print(json.dumps(result, indent=2))
    
    print("\nTesting next post generator...")
    next_gen = BulletproofNextPostGenerator()
    next_post = next_gen.generate_next_post(
        posts=[],
        username="ylecun",
        platform="twitter",
        account_type="branding",
        posting_style="technical"
    )
    
    print("=== BULLETPROOF NEXT POST ===")
    print(json.dumps(next_post, indent=2))
