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
        - Be highly specific to the beauty industry and these exact accounts
        - Reference concrete examples from the post data, not general marketing advice
        - Include actual metrics and specific strategies observed in the data
        - Provide actionable recommendations that directly counter competitor advantages
        - Format all output as properly escaped JSON with the following structure:

        {{
            "primary_analysis": "Detailed intelligence on primary account strengths and weaknesses",
            "competitor_analysis": {{
                "competitor1": "Detailed intelligence on their specific strategies and vulnerabilities",
                "competitor2": "Detailed intelligence on their specific strategies and vulnerabilities"
            }},
            "recommendations": "Actionable strategic advantages to exploit, with direct reference to competitor weaknesses",
            "next_post": {{
                "caption": "Strategically crafted caption",
                "hashtags": ["#strategic", "#hashtags"],
                "call_to_action": "Compelling CTA that outperforms competitors",
                "visual_prompt": "Detailed visual concept that positions against competitor aesthetics"
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
    
    def generate_recommendation(self, primary_username, secondary_usernames, query, n_context=3):
        """Generate a comprehensive content recommendation and strategy."""
        try:
            if not self.client:
                logger.error("Gemini API not initialized.")
                return self._generate_fallback_response(query)
            
            prompt = self._construct_enhanced_prompt(primary_username, secondary_usernames, query)
            response = self.client.models.generate_content(model=self.model, contents=prompt)
            response_text = response.text.strip()
            
            # Log raw response for debugging
            logger.debug(f"Raw Gemini response: {response_text}")
            
            # Attempt JSON parsing with multiple strategies
            try:
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    recommendation = json.loads(json_match.group(0))
                else:
                    recommendation = json.loads(response_text)
                logger.info(f"Generated recommendation for {primary_username}")
                return recommendation
            except json.JSONDecodeError as e:
                logger.warning(f"JSON parsing failed: {str(e)}. Attempting repair.")
                # Try fixing common JSON issues (e.g., missing commas)
                fixed_text = re.sub(r'}(\s*"[^"]+":)', r'},\1', response_text)  # Add missing commas
                try:
                    recommendation = json.loads(fixed_text)
                    logger.info(f"Repaired and parsed JSON for {primary_username}")
                    return recommendation
                except json.JSONDecodeError as e2:
                    logger.error(f"Repair failed: {str(e2)}. Raw text: {response_text}")
                    return self._extract_recommendation_from_text(response_text, query)
        except Exception as e:
            logger.error(f"Error generating recommendation: {str(e)}")
            return self._generate_fallback_response(query)
    
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
            {text}
            
            Return ONLY the JSON object, ensuring proper syntax.
            """
            if self.client:
                response = self.client.models.generate_content(model=self.model, contents=format_prompt)
                response_text = response.text.strip()
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group(0))
            
            # Manual extraction as fallback
            lines = text.split('\n')
            caption = next((line for line in lines if len(line) > 20), f"Explore {query}!")
            hashtags = re.findall(r'#\w+', text) or [f"#{query.replace(' ', '')}", "#Trend"]
            cta = next((line for line in lines if any(p in line.lower() for p in ["click", "check", "visit"])), 
                      "Join the conversation!")
            return {
                "primary_analysis": text[:200] if text else "No analysis available.",
                "competitor_analysis": {},
                "recommendations": text[200:400] if len(text) > 400 else "Use engaging visuals.",
                "next_post": {
                    "caption": caption,
                    "hashtags": hashtags,
                    "call_to_action": cta,
                    "visual_prompt": f"Bold graphic for {query}"
                }
            }
        except Exception as e:
            logger.error(f"Error extracting recommendation: {str(e)}")
            return self._generate_fallback_response(query)
    
    def generate_batch_recommendations(self, prompt, topics):
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
            
            enhanced_prompt = self._enhance_batch_prompt(prompt, all_context)
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
    
    def _enhance_batch_prompt(self, prompt, context_by_topic):
        """Enhance the batch prompt with context for each topic."""
        context_section = "\n".join([f"Context for '{topic}':\n{' '.join(docs)}" 
                                   for topic, docs in context_by_topic.items()])
        return f"{prompt}\n\nUse the following context:\n{context_section}\n\nFormat as JSON with topics as keys."

def test_rag_implementation():
    """Test the enhanced RAG implementation with multi-user data."""
    try:
        vector_db = VectorDatabaseManager()
        vector_db.clear_collection()
        
        sample_posts = [
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
             'username': 'fentybeauty'}
        ]
        vector_db.add_posts(sample_posts, 'maccosmetics')
        
        rag = RagImplementation(vector_db=vector_db)
        primary_username = "maccosmetics"
        secondary_usernames = ["anastasiabeverlyhills", "fentybeauty"]
        query = "summer makeup trends"
        
        recommendation = rag.generate_recommendation(primary_username, secondary_usernames, query)
        
        required_blocks = ["primary_analysis", "competitor_analysis", "recommendations", "next_post"]
        next_post_fields = ["caption", "hashtags", "call_to_action", "visual_prompt"]
        
        missing_blocks = [block for block in required_blocks if block not in recommendation]
        missing_fields = [field for field in next_post_fields if field not in recommendation.get("next_post", {})]
        
        # Fail the test if we hit the fallback due to an error
        if "due to API issues" in recommendation["primary_analysis"] or missing_blocks or missing_fields:
            logger.error(f"Test failed: Missing blocks: {missing_blocks}, Missing fields: {missing_fields}, Used fallback: {recommendation['primary_analysis']}")
            return False
        
        logger.info("Test successful: All blocks and fields present.")
        logger.info(f"Recommendation:\n{json.dumps(recommendation, indent=2)}")
        return True
    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_rag_implementation()
    print(f"Enhanced RAG implementation test {'successful' if success else 'failed'}")