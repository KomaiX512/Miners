"""Module for RAG implementation using Google Gemini API with enhanced contextual intelligence."""

import logging
import json
import re
from google import genai
from vector_database import VectorDatabaseManager
from config import GEMINI_CONFIG, LOGGING_CONFIG, CONTENT_TEMPLATES

# Set up logging
logging.basicConfig(
    level=LOGGING_CONFIG['level'],
    format=LOGGING_CONFIG['format']
)
logger = logging.getLogger(__name__)

class RagImplementation:
    """Class for RAG implementation using Google Gemini API with multi-user analysis."""
    
    def __init__(self, config=GEMINI_CONFIG, vector_db=None):
        """Initialize with configuration and vector database."""
        self.config = config
        self.vector_db = vector_db or VectorDatabaseManager()
        self._initialize_gemini()
    
    def _initialize_gemini(self):
        """Initialize the Gemini API client."""
        try:
            self.client = genai.Client(api_key=self.config['api_key'])
            self.model = self.config['model']
            logger.info(f"Successfully initialized Gemini API with model: {self.model}")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini API: {str(e)}")
            logger.warning("Proceeding without Gemini capabilities - responses will be limited")
            self.client = None
    
    def _construct_basic_prompt(self, query, context_docs):
        """Construct a basic prompt for simple post generation."""
        context_text = "\n".join([f"- {doc}" for doc in context_docs])
        return f"""
        You are an expert social media content creator. Based on the following context from successful posts:
        
        {context_text}
        
        Generate a creative and engaging social media post about {query}.
        
        Include:
        1. An attention-grabbing caption
        2. Relevant hashtags 
        3. A call to action
        
        Output format should be JSON with the following fields:
        {{
            "caption": "Your creative caption here",
            "hashtags": ["#hashtag1", "#hashtag2"],
            "call_to_action": "Your call to action here"
        }}
        
        Ensure your response is only the JSON object, nothing else.
        """
    
    def _construct_enhanced_prompt(self, primary_username, secondary_usernames, query):
        """Construct a detailed prompt for comprehensive analysis and recommendations."""
        primary_data = self.vector_db.query_similar(query, n_results=5, filter_username=primary_username)
        secondary_data = {username: self.vector_db.query_similar(query, n_results=3, filter_username=username)
                         for username in secondary_usernames}
        
        primary_context = "\n".join([f"- {doc} (Engagement: {meta['engagement']}, Timestamp: {meta['timestamp']})"
                                   for doc, meta in zip(primary_data['documents'][0], primary_data['metadatas'][0])])
        secondary_context = {username: "\n".join([f"- {doc} (Engagement: {meta['engagement']}, Timestamp: {meta['timestamp']})"
                                                for doc, meta in zip(data['documents'][0], data['metadatas'][0])])
                            for username, data in secondary_data.items()}
        
        prompt = f"""
        You are a professional social media intelligence analyst with expertise in competitor research for the beauty industry. Your mission is to provide {primary_username} with detailed, actionable intelligence and recommendations to outperform their competitors in the beauty market.

        **Primary Account**: {primary_username}
        **Competitors Being Analyzed**: {', '.join(secondary_usernames)}
        **Topic Focus**: {query}
        **Current Date**: April 11, 2025

        The following data represents actual social media content from these accounts, including engagement metrics:

        **PRIMARY ACCOUNT POSTS**: {primary_username}
        {primary_context if primary_context else "No recent posts available."}

        **COMPETITOR POSTS**:
        {chr(10).join([f"---{username}---{chr(10)}{context if context else 'No recent posts available.'}" for username, context in secondary_context.items()])}

        Your task is to provide an intelligence report with four distinct sections:

        1. **Primary Account Analysis** [CONFIDENTIAL]
           - Analyze posting patterns and identify content themes that perform well
           - Assess hashtag strategy effectiveness by comparing engagement across posts
           - Identify content gaps and missed opportunities compared to competitors
           - Highlight unique strengths or brand positioning advantages

        2. **Competitor Intelligence Report** [TOP SECRET]
           - For each competitor, analyze:
             * Their most successful content formats and topics (based on engagement metrics)
             * The specific tactics they use to drive engagement (e.g., contests, aesthetics, CTAs)
             * Their posting frequency and optimal posting times
             * Any noticeable strategic shifts in their content approach
             * Their unique value proposition and how they differentiate themselves
           - Identify "spy intel" - specific competitor techniques {primary_username} could adapt

        3. **Strategic Advantage Plan** [ACTIONABLE INTEL]
           - Recommend specific content strategies to exploit weaknesses in competitor approaches
           - Suggest unique ways to differentiate from competitors while targeting similar audiences 
           - Provide 3-5 specific post ideas that directly counter competitor strengths
           - For each recommendation, explicitly cite why you're suggesting it based on competitor behavior (e.g., "Competitor X is seeing 40% higher engagement when they post Y, so you should adapt this by...")
           - Include optimal timing recommendations based on engagement patterns

        4. **Next Post Blueprint** [IMMEDIATE ACTION REQUIRED]
           - Design a specific post that directly capitalizes on intelligence gathered from competitor analysis
           - Include:
             * A detailed caption that leverages the most successful elements from competitor strategies
             * Strategic hashtags that competitors are under-utilizing but show high potential
             * A compelling call to action that outperforms typical CTAs used by competitors
             * A detailed visual concept description that specifically positions against competitor visuals

        Format your response as a valid JSON object with these four main keys. For competitors, use a nested object with each competitor username as a key. Ensure all analysis directly references specific examples from the posts provided.

        The intelligence report must:
        - Be highly specific to catagory in which primery usernames and Comeptitors are abouts. 
        - Reference concrete examples from the post data, not general marketing advice. Competitors 
        - Include actual metrics and specific strategies observed in the data
        - Provide actionable recommendations that directly counter competitor advantages
        - Format all output as properly escaped JSON with the following structure:

        {{
            "primary_analysis": "Detailed intelligence on primary account strengths and weaknesses",
            "competitor_analysis": {{
                "competitor1": "Detailed intelligence on their specific strategies and vulnerabilities, And 2 sentences About recent activities they did",
                "competitor2": "Detailed intelligence on their specific strategies and vulnerabilities, And 2 sentences About recent activities they did",
                "competitor3": "Detailed intelligence on their specific strategies and vulnerabilities, And 2 sentences About recent activities they did",
                "competitor4": "Detailed intelligence on their specific strategies and vulnerabilities, And 2 sentences About recent activities they did",
                "competitor5": "Detailed intelligence on their specific strategies and vulnerabilities, And 2 sentences About recent activities they did",
            }},
            "recommendations": "Actionable strategic advantages to exploit, with direct reference to competitor weaknesses",
            "next_post": {{
                "caption": "Strategically crafted caption that should matches with our own primary accounts captions patterns and styles.",
                "hashtags": ["#strategic", "#hashtags"],
                "call_to_action": "Compelling CTA that outperforms competitors",
                "visual_prompt": "Detailed Graphical visual concept that positions against competitor aesthetics but consistent with the our primary account posts theme and its color themes. Shape meaningful concept in Graphical Viusals image prompt. And it shouldbe relevant with what caption ahs been written."
            }}
        }}
        """
        return prompt
    
    def _construct_non_branding_prompt(self, primary_username, query):
        """Construct a prompt for non-branding accounts focused on personal posting history."""
        primary_data = self.vector_db.query_similar(query, n_results=10, filter_username=primary_username)
        
        # Safely handle empty or missing results
        primary_context = ""
        if primary_data and 'documents' in primary_data and len(primary_data['documents']) > 0:
            try:
                primary_context = "\n".join([f"- {doc} (Engagement: {meta['engagement']}, Timestamp: {meta['timestamp']})"
                                   for doc, meta in zip(primary_data['documents'][0], primary_data['metadatas'][0])])
            except Exception as e:
                logger.warning(f"Error creating primary context: {str(e)}")
                primary_context = "No recent posts available."
        else:
            primary_context = "No recent posts available."
        
        prompt = f"""
        You are a creative social media content specialist for personal and non-brand accounts. Your task is to analyze the posting history of {primary_username} and generate an authentic, personalized content recommendation that matches their unique style and themes.

        **Account**: {primary_username}
        **Topic Focus**: {query}
        **Current Date**: April 11, 2025

        The following data represents the account's previous posts, including engagement metrics:

        **ACCOUNT POSTING HISTORY**: {primary_username}
        {primary_context}

        Your task is to provide a content recommendation with these sections:

        1. **Account Analysis** [PERSONAL INSIGHTS]
           - Analyze posting patterns, themes, and topics that appear frequently
           - Identify the unique voice and style used in captions
           - Determine the typical tone (casual, formal, humorous, inspirational, etc.)
           - Note any recurring visual elements mentioned in posts

        2. **Content Recommendations** [PERSONALIZED STRATEGY]
           - Suggest content ideas that align perfectly with the account's established themes
           - Recommend topics that would resonate with their audience based on past engagement
           - Suggest posting frequency and timing based on observed patterns
           - Identify hashtag strategies that have worked well in the past

        3. **Next Post Creation** [AUTHENTIC CONTENT]
           - Design a next post that feels like a natural extension of their content history
           - Include:
             * A caption that matches their writing style and tone perfectly
             * Hashtags that they typically use, plus a few strategic new ones
             * A call to action that fits their usual engagement approach
             * A visual concept that aligns with their aesthetic preferences

        Format your response as a valid JSON object with these three main keys. Ensure all analysis directly references specific examples from the post history provided.

        Your response must:
        - Maintain the account holder's authentic voice - it should sound like them, not like marketing
        - Reference concrete examples from the post data, not generic advice
        - Not fabricate information - only use what can be inferred from the data
        - Format all output as properly escaped JSON with the following structure:

        {{
            "account_analysis": "Detailed analysis of the account's posting history, themes, and style",
            "content_recommendations": "Personalized content strategy suggestions based on posting history",
            "next_post": {{
                "caption": "A caption written in the account's authentic voice and style",
                "hashtags": ["#UsualHashtag", "#TheirStyle"],
                "call_to_action": "Engagement prompt that matches their typical approach",
                "visual_prompt": "Visual concept that aligns with their aesthetic preferences"
            }}
        }}
        """
        return prompt
    
    def _generate_fallback_response(self, query):
        """Generate a fallback response when Gemini is unavailable."""
        try:
            topic = query.lower()
            hashtags = ['#Trending', '#MustSee', f"#{topic.replace(' ', '')}"]
            return {
                "primary_analysis": f"Unable to analyze {topic} due to API issues.",
                "competitor_analysis": {},
                "recommendations": f"Focus on {topic} with engaging visuals and strong CTAs.",
                "next_post": {
                    "caption": f"Unlock the latest in {topic}!",
                    "hashtags": hashtags,
                    "call_to_action": "Share your thoughts below!",
                    "visual_prompt": f"A vibrant graphic showcasing {topic} trends"
                }
            }
        except Exception as e:
            logger.error(f"Error in fallback response: {str(e)}")
            return {
                "primary_analysis": "Analysis unavailable.",
                "competitor_analysis": {},
                "recommendations": "Post regularly about trending topics.",
                "next_post": {
                    "caption": "Stay tuned for more!",
                    "hashtags": ["#Trending"],
                    "call_to_action": "Check back soon!",
                    "visual_prompt": "Generic promotional image"
                }
            }
    
    def generate_recommendation(self, primary_username, secondary_usernames, query, n_context=3, is_branding=True):
        """Generate a comprehensive content recommendation and strategy."""
        try:
            if not self.client:
                logger.error("Gemini API not initialized.")
                return self._generate_fallback_response(query)
            
            # Select the appropriate prompt based on account type
            if is_branding:
                prompt = self._construct_enhanced_prompt(primary_username, secondary_usernames, query)
            else:
                prompt = self._construct_non_branding_prompt(primary_username, query)
            
            try:
                response = self.client.models.generate_content(model=self.model, contents=prompt)
                response_text = response.text.strip()
            except Exception as api_e:
                logger.error(f"Gemini API call failed: {str(api_e)}")
                return self._generate_fallback_response(query)
            
            # Check if response is empty
            if not response_text:
                logger.error("Empty response from Gemini API")
                return self._generate_fallback_response(query)
            
            # Log raw response for debugging
            logger.debug(f"Raw Gemini response: {response_text[:500]}...")
            
            # Attempt JSON parsing with multiple strategies
            recommendation = self._parse_and_repair_json(response_text, primary_username, query)
            if recommendation:
                return recommendation
            
            # If all parsing attempts fail, use text extraction
            logger.warning(f"All JSON parsing attempts failed. Falling back to text extraction.")
            return self._extract_recommendation_from_text(response_text, query)
            
        except Exception as e:
            logger.error(f"Error generating recommendation: {str(e)}")
            return self._generate_fallback_response(query)
    
    def _parse_and_repair_json(self, text, primary_username, query):
        """Parse and repair JSON from text with multiple fallback strategies."""
        if not text or not text.strip():
            logger.error("Empty text provided to JSON parser")
            return None
            
        # First attempt: extract JSON within triple backticks if present
        try:
            json_block_match = re.search(r'```(?:json)?\s*(\{[\s\S]*?\})\s*```', text, re.DOTALL)
            if json_block_match:
                json_text = json_block_match.group(1).strip()
                if json_text:
                    try:
                        recommendation = json.loads(json_text)
                        logger.info(f"Successfully parsed JSON from code block for {primary_username}")
                        return recommendation
                    except json.JSONDecodeError as e:
                        logger.warning(f"Failed to parse JSON from code block: {str(e)}")
        except Exception as e:
            logger.warning(f"Error in backtick extraction: {str(e)}")
        
        # Second attempt: find JSON object with regex
        try:
            json_match = re.search(r'\{[\s\S]*?\}', text, re.DOTALL)
            if json_match:
                json_text = json_match.group(0).strip()
                if json_text:
                    try:
                        recommendation = json.loads(json_text)
                        logger.info(f"Successfully parsed JSON with regex for {primary_username}")
                        return recommendation
                    except json.JSONDecodeError as e:
                        logger.warning(f"Failed to parse JSON with regex: {str(e)}")
        except Exception as e:
            logger.warning(f"Error in JSON regex extraction: {str(e)}")
        
        # Third attempt: find any JSON-like structure with more flexible regex
        try:
            json_like_match = re.search(r'\{[\s\S]*\}', text, re.DOTALL)
            if json_like_match:
                json_text = json_like_match.group(0).strip()
                if json_text:
                    try:
                        # Apply basic fixes before attempting to parse
                        fixed_text = self._apply_basic_json_fixes(json_text)
                        recommendation = json.loads(fixed_text)
                        logger.info(f"Successfully parsed JSON with basic fixes for {primary_username}")
                        return recommendation
                    except json.JSONDecodeError as e:
                        logger.warning(f"Failed to parse JSON with basic fixes: {str(e)}")
        except Exception as e:
            logger.warning(f"Error in flexible JSON extraction: {str(e)}")
        
        # Advanced JSON repair strategies
        try:
            # Safety check - don't try to repair an empty string
            if not text.strip():
                logger.error("Empty text for repair")
                return None
                
            fixed_text = self._apply_advanced_json_repairs(text)
            
            # Try parsing the fixed JSON
            try:
                recommendation = json.loads(fixed_text)
                logger.info(f"Repaired and parsed JSON for {primary_username}")
                return recommendation
            except json.JSONDecodeError as e:
                logger.warning(f"Advanced repair attempt failed: {str(e)}")
            
            # If full repair fails, try extracting and repairing just the next_post part
            recommendation = self._extract_next_post_section(fixed_text, query)
            if recommendation:
                return recommendation
                
        except Exception as repair_e:
            logger.error(f"Repair failed: {str(repair_e)}. Raw text sample: {text[:100]}...")
        
        return None
    
    def _apply_basic_json_fixes(self, text):
        """Apply basic fixes to potentially invalid JSON."""
        if not text:
            return "{}"
            
        # Replace None with null, True with true, False with false
        text = re.sub(r'\bNone\b', 'null', text)
        text = re.sub(r'\bTrue\b', 'true', text)
        text = re.sub(r'\bFalse\b', 'false', text)
        
        # Replace single quotes with double quotes
        text = re.sub(r'\'([^\']+)\'', r'"\1"', text)
        
        # Fix unquoted property names
        text = re.sub(r'([{,]\s*)(\w+)(\s*:)', r'\1"\2"\3', text)
        
        return text
    
    def _apply_advanced_json_repairs(self, text):
        """Apply advanced repairs to invalid JSON."""
        if not text:
            return "{}"
            
        # Make a copy of the text for repair attempts
        fixed_text = text
        
        # Strategy 1: Fix missing commas between key-value pairs
        fixed_text = re.sub(r'}(\s*"[^"]+":)', r'},\1', fixed_text)
        
        # Strategy 2: Fix unquoted property names (more comprehensive)
        fixed_text = re.sub(r'([{,]\s*)(\w+)(\s*:)', r'\1"\2"\3', fixed_text)
        
        # Strategy 3: Fix trailing commas in arrays/objects
        fixed_text = re.sub(r',(\s*[}\]])', r'\1', fixed_text)
        
        # Strategy 4: Fix missing quotes around string values
        fixed_text = re.sub(r':\s*([^"{}\[\],\d][^,}\]]*?)(\s*[,}\]])', r': "\1"\2', fixed_text)
        
        # Strategy 5: Fix single quotes used instead of double quotes
        fixed_text = re.sub(r'\'([^\']+)\'', r'"\1"', fixed_text)
        
        # Strategy 6: Fix JavaScript-style comments
        fixed_text = re.sub(r'//.*?\n', r' ', fixed_text)
        fixed_text = re.sub(r'/\*.*?\*/', r' ', fixed_text, flags=re.DOTALL)
        
        # Strategy 7: Fix Python literal values
        fixed_text = re.sub(r'\bNone\b', 'null', fixed_text)
        fixed_text = re.sub(r'\bTrue\b', 'true', fixed_text)
        fixed_text = re.sub(r'\bFalse\b', 'false', fixed_text)
        
        # Strategy 8: Fix improper escaping in strings
        fixed_text = re.sub(r'(["])([^"\\]*(?:\\.[^"\\]*)*)\\([^\\])', r'\1\2\\\\\3', fixed_text)
        
        # Strategy 9: Remove extraneous text outside the JSON structure
        json_match = re.search(r'(\{[\s\S]*\})', fixed_text, re.DOTALL)
        if json_match:
            fixed_text = json_match.group(1)
        
        return fixed_text
    
    def _extract_next_post_section(self, text, query):
        """Extract and repair just the next_post section."""
        try:
            # Find the next_post section
            next_post_match = re.search(r'"next_post"[^{]*?({[^{}]*(?:{[^{}]*})*[^{}]*})', text, re.DOTALL)
            if next_post_match:
                next_post_text = next_post_match.group(1).strip()
                if next_post_text:
                    try:
                        # Apply all repairs to the next_post section
                        next_post_text = self._apply_advanced_json_repairs(next_post_text)
                        
                        # Handle list items in hashtags that might be malformed
                        hashtags_match = re.search(r'"hashtags"\s*:\s*\[\s*([^\]]*)\s*\]', next_post_text, re.DOTALL)
                        if hashtags_match:
                            hashtags_content = hashtags_match.group(1).strip()
                            if hashtags_content:
                                # Properly format hashtags with double quotes and commas
                                fixed_hashtags = []
                                for tag in re.findall(r'[^",\s]+', hashtags_content):
                                    fixed_hashtags.append(f'"{tag}"')
                                fixed_hashtags_str = ", ".join(fixed_hashtags)
                                next_post_text = re.sub(r'"hashtags"\s*:\s*\[\s*([^\]]*)\s*\]', 
                                                   f'"hashtags": [{fixed_hashtags_str}]', 
                                                   next_post_text)
                        
                        logger.debug(f"Attempting to parse next_post: {next_post_text}")
                        next_post = json.loads(next_post_text)
                        
                        # Create a complete recommendation with the extracted next_post
                        recommendation = self._generate_fallback_response(query)
                        recommendation["next_post"] = next_post
                        logger.info(f"Extracted and repaired next_post section")
                        return recommendation
                    except json.JSONDecodeError as e:
                        logger.warning(f"Failed to repair next_post section: {str(e)}")
                    except Exception as e:
                        logger.warning(f"Error in next_post extraction: {str(e)}")
            
            # Special case: If we have raw caption and hashtags, create a minimal structure
            try:
                caption_match = re.search(r'"caption"\s*:\s*"([^"]+)"', text, re.DOTALL)
                hashtags_match = re.search(r'"hashtags"\s*:\s*\[\s*([^\]]*)\s*\]', text, re.DOTALL)
                
                if caption_match:
                    caption = caption_match.group(1).strip()
                    hashtags = []
                    
                    if hashtags_match:
                        hashtags_content = hashtags_match.group(1).strip()
                        hashtags = re.findall(r'"([^"]+)"', hashtags_content)
                    
                    if not hashtags:
                        hashtags = [f"#{word.capitalize()}" for word in query.split() if len(word) > 3]
                        hashtags.append("#Trending")
                    
                    recommendation = self._generate_fallback_response(query)
                    recommendation["next_post"]["caption"] = caption
                    recommendation["next_post"]["hashtags"] = hashtags
                    logger.info("Created recommendation from raw caption and hashtags")
                    return recommendation
            except Exception as e:
                logger.warning(f"Failed to extract caption and hashtags: {str(e)}")
                
        except Exception as e:
            logger.warning(f"Error extracting next_post: {str(e)}")
        
        return None
    
    def apply_template(self, recommendation, template_type):
        """Apply a template to a recommendation."""
        try:
            template = CONTENT_TEMPLATES.get(template_type, '{caption} {hashtags}')
            hashtags_str = ' '.join(recommendation.get('hashtags', []))
            formatted = template.format(
                caption=recommendation.get('caption', ''),
                hashtags=hashtags_str
            )
            return formatted
        except Exception as e:
            logger.error(f"Error applying template: {str(e)}")
            return f"{recommendation.get('caption', '')} {' '.join(recommendation.get('hashtags', []))}"
    
    def _extract_recommendation_from_text(self, text, query):
        """Extract recommendation components from unstructured text response."""
        try:
            # If text is empty, return a fallback response immediately
            if not text or not text.strip():
                logger.error("Empty text provided to extract_recommendation")
                return self._generate_fallback_response(query)
                
            # Try to extract structured data using Gemini's help
            if self.client:
                try:
                    format_prompt = f"""
                    Convert this text into a valid JSON object with the structure:
                    {{
                        "primary_analysis": "Text",
                        "competitor_analysis": {{}},
                        "recommendations": "Text",
                        "next_post": {{
                            "caption": "Text",
                            "hashtags": ["#tag1"],
                            "call_to_action": "Text",
                            "visual_prompt": "Text"
                        }}
                    }}
                    
                    Text:
                    {text[:2000]}
                    
                    Return ONLY the JSON object with valid syntax. No markdown formatting, no backticks.
                    """
                    
                    response = self.client.models.generate_content(model=self.model, contents=format_prompt)
                    response_text = response.text.strip()
                    
                    # Check if response is empty
                    if not response_text:
                        logger.error("Empty response from formatting request")
                        raise ValueError("Empty response from formatting request")
                    
                    # Parse with the main parser which already has all repair strategies
                    recommendation = self._parse_and_repair_json(response_text, "extraction", query)
                    if recommendation:
                        logger.info("Successfully extracted structured data using Gemini")
                        return recommendation
                        
                except Exception as e:
                    logger.error(f"Error in reformatting with Gemini: {str(e)}")
            
            # Manual extraction as fallback
            logger.info("Using manual text extraction as fallback")
            
            # Extract caption - find a sentence of reasonable length
            caption_candidates = re.findall(r'([A-Z][^.!?]{15,100}[.!?])', text)
            caption = caption_candidates[0] if caption_candidates else f"Discover the latest in {query}!"
            
            # Extract hashtags - find all hashtags or create from keywords
            hashtags = re.findall(r'#\w+', text)
            if not hashtags:
                # Create hashtags from keywords in the query
                keywords = [word for word in query.split() if len(word) > 3]
                hashtags = [f"#{word.capitalize()}" for word in keywords] or [f"#{query.replace(' ', '')}"]
                hashtags.extend(["#Trending", "#MustSee"])
            
            # Extract call to action - find sentences with action verbs
            cta_patterns = [
                r'([^.!?]*(?:click|tap|share|comment|follow|subscribe|check|visit|explore|discover|join|shop)[^.!?]*[.!?])',
                r'([^.!?]*(?:what|how|who|when)[^.!?]*\?)'
            ]
            
            cta = None
            for pattern in cta_patterns:
                cta_matches = re.findall(pattern, text, re.IGNORECASE)
                if cta_matches:
                    cta = cta_matches[0].strip()
                    break
            
            if not cta:
                cta = f"Share your thoughts on {query} below!"
            
            # Find any visual description
            visual_prompt = None
            visual_patterns = [
                r'(?:visual|image|photo|picture|graphic)(?:[^.!?]*)[.!?]',
                r'[^.!?]*(?:showing|featuring|displaying|with)[^.!?]*[.!?]'
            ]
            
            for pattern in visual_patterns:
                visual_matches = re.findall(pattern, text, re.IGNORECASE)
                if visual_matches:
                    visual_prompt = visual_matches[0].strip()
                    break
            
            if not visual_prompt:
                visual_prompt = f"High-quality image related to {query} with vibrant colors and professional composition."
            
            # Construct the best structured response we can
            return {
                "primary_analysis": text[:250] if text else f"Analysis of {query} content strategy.",
                "competitor_analysis": {},
                "recommendations": text[250:500] if len(text) > 500 else f"Focus on {query} with engaging visuals.",
                "next_post": {
                    "caption": caption,
                    "hashtags": hashtags[:5],  # Limit to 5 hashtags
                    "call_to_action": cta,
                    "visual_prompt": visual_prompt
                }
            }
        except Exception as e:
            logger.error(f"Error extracting recommendation: {str(e)}")
            return self._generate_fallback_response(query)
    
    def generate_batch_recommendations(self, prompt, topics, is_branding=True):
        """Generate recommendations for multiple topics in a single API call."""
        try:
            all_context = {}
            for topic in topics:
                similar_docs = self.vector_db.query_similar(topic, n_results=3)
                all_context[topic] = similar_docs['documents'][0] if similar_docs and similar_docs['documents'][0] else [
                    f"Engage with {topic} content",
                    f"{topic} posts with CTAs perform well",
                    f"Visuals boost {topic} engagement"
                ]
                logger.info(f"Context prepared for topic: {topic}")
            
            enhanced_prompt = self._enhance_batch_prompt(prompt, all_context, is_branding)
            response = self.client.models.generate_content(model=self.model, contents=enhanced_prompt)
            response_text = response.text.strip()
            
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                recommendations = json.loads(json_match.group(0))
                logger.info(f"Generated batch recommendations for {len(topics)} topics")
                return recommendations
            return {}
        except Exception as e:
            logger.error(f"Error in batch recommendations: {str(e)}")
            return {}
    
    def _enhance_batch_prompt(self, prompt, context_by_topic, is_branding=True):
        """Enhance the batch prompt with context for each topic."""
        context_section = "\n".join([f"Context for '{topic}':\n{' '.join(docs)}" 
                                   for topic, docs in context_by_topic.items()])
        
        # Adjust prompt based on account type
        if is_branding:
            return f"{prompt}\n\nUse the following context:\n{context_section}\n\nFor each topic, include competitive analysis and brand positioning. Format as JSON with topics as keys."
        else:
            return f"{prompt}\n\nUse the following context:\n{context_section}\n\nFor each topic, focus on personal style consistency and authentic voice. Format as JSON with topics as keys."

def test_rag_implementation():
    """Test the enhanced RAG implementation with multi-user data."""
    try:
        vector_db = VectorDatabaseManager()
        vector_db.clear_collection()
        
        # Sample branding account posts
        branding_posts = [
            {'id': '1', 'caption': 'Bold summer looks! #SummerMakeup', 'hashtags': ['#SummerMakeup'], 
             'engagement': 150, 'likes': 120, 'comments': 30, 'timestamp': '2025-04-01T10:00:00Z', 
             'username': 'maccosmetics'},
            {'id': '2', 'caption': 'New palette drop! #GlowUp', 'hashtags': ['#GlowUp'], 
             'engagement': 200, 'likes': 170, 'comments': 30, 'timestamp': '2025-04-02T12:00:00Z', 
             'username': 'maccosmetics'},
            {'id': '3', 'caption': 'Brow perfection! #BrowGame', 'hashtags': ['#BrowGame'], 
             'engagement': 180, 'likes': 150, 'comments': 30, 'timestamp': '2025-04-03T14:00:00Z', 
             'username': 'anastasiabeverlyhills'},
            {'id': '4', 'caption': 'Glowy skin secrets! #Skincare', 'hashtags': ['#Skincare'], 
             'engagement': 220, 'likes': 190, 'comments': 30, 'timestamp': '2025-04-04T15:00:00Z', 
             'username': 'fentybeauty'},
        ]
        
        # Sample personal account posts
        personal_posts = [
            {'id': '5', 'caption': 'My summer adventure begins! #SummerVibes', 'hashtags': ['#SummerVibes'], 
             'engagement': 120, 'likes': 100, 'comments': 20, 'timestamp': '2025-04-01T11:00:00Z', 
             'username': 'personal_user'},
            {'id': '6', 'caption': 'Beach day with friends! #BeachDay', 'hashtags': ['#BeachDay'], 
             'engagement': 140, 'likes': 110, 'comments': 30, 'timestamp': '2025-04-02T13:00:00Z', 
             'username': 'personal_user'},
            {'id': '7', 'caption': 'Sunset views from my hike today. So peaceful! #Nature #Hiking', 
             'hashtags': ['#Nature', '#Hiking'], 'engagement': 160, 'likes': 130, 'comments': 30, 
             'timestamp': '2025-04-03T18:00:00Z', 'username': 'personal_user'},
            {'id': '8', 'caption': 'Making memories on my vacation. Can\'t believe how beautiful this place is! #Travel #Vacation', 
             'hashtags': ['#Travel', '#Vacation'], 'engagement': 180, 'likes': 150, 'comments': 30, 
             'timestamp': '2025-04-04T09:00:00Z', 'username': 'personal_user'},
            {'id': '9', 'caption': 'Found this amazing local cafe. The coffee is incredible! #CoffeeTime #LocalGem', 
             'hashtags': ['#CoffeeTime', '#LocalGem'], 'engagement': 130, 'likes': 100, 'comments': 30, 
             'timestamp': '2025-04-05T10:00:00Z', 'username': 'personal_user'},
        ]
        
        # Add posts to vector database
        vector_db.add_posts(branding_posts, 'maccosmetics')
        vector_db.add_posts(personal_posts, 'personal_user')
        
        rag = RagImplementation(vector_db=vector_db)
        
        # Test 1: Branding account test
        logger.info("Testing branding account recommendation...")
        primary_username = "maccosmetics"
        secondary_usernames = ["anastasiabeverlyhills", "fentybeauty"]
        query = "summer makeup trends"
        
        branding_recommendation = rag.generate_recommendation(
            primary_username=primary_username,
            secondary_usernames=secondary_usernames,
            query=query,
            is_branding=True
        )
        
        branding_required_blocks = ["primary_analysis", "competitor_analysis", "recommendations", "next_post"]
        branding_next_post_fields = ["caption", "hashtags", "call_to_action", "visual_prompt"]
        
        branding_missing_blocks = [block for block in branding_required_blocks if block not in branding_recommendation]
        branding_missing_fields = [field for field in branding_next_post_fields if field not in branding_recommendation.get("next_post", {})]
        
        # Test 2: Non-branding account test
        logger.info("Testing non-branding account recommendation...")
        personal_username = "personal_user"
        query = "summer vacation ideas"
        
        non_branding_recommendation = rag.generate_recommendation(
            primary_username=personal_username,
            secondary_usernames=[],
            query=query,
            is_branding=False
        )
        
        non_branding_required_blocks = ["account_analysis", "content_recommendations", "next_post"]
        non_branding_next_post_fields = ["caption", "hashtags", "call_to_action", "visual_prompt"]
        
        non_branding_missing_blocks = [block for block in non_branding_required_blocks if block not in non_branding_recommendation]
        non_branding_missing_fields = [field for field in non_branding_next_post_fields if field not in non_branding_recommendation.get("next_post", {})]
        
        # Fail the test if we hit the fallback due to an error in either test
        if ("due to API issues" in branding_recommendation.get("primary_analysis", "") or 
            branding_missing_blocks or branding_missing_fields or
            "due to API issues" in non_branding_recommendation.get("account_analysis", "") or 
            non_branding_missing_blocks or non_branding_missing_fields):
            
            logger.error(f"Branding test: Missing blocks: {branding_missing_blocks}, Missing fields: {branding_missing_fields}")
            logger.error(f"Non-branding test: Missing blocks: {non_branding_missing_blocks}, Missing fields: {non_branding_missing_fields}")
            return False
        
        logger.info("Test successful: All blocks and fields present for both account types.")
        logger.info(f"Branding recommendation structure: {list(branding_recommendation.keys())}")
        logger.info(f"Non-branding recommendation structure: {list(non_branding_recommendation.keys())}")
        return True
    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    success = test_rag_implementation()
    print(f"Enhanced RAG implementation test {'successful' if success else 'failed'}")