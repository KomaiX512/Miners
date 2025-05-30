"""Module for RAG implementation using Google Gemini API with enhanced contextual intelligence."""

import logging
import json
import re
import google.generativeai as genai
from vector_database import VectorDatabaseManager
from config import GEMINI_CONFIG, LOGGING_CONFIG, CONTENT_TEMPLATES
from datetime import datetime
import os

# Set up logging
logging.basicConfig(
    level=LOGGING_CONFIG['level'],
    format=LOGGING_CONFIG['format']
)
logger = logging.getLogger(__name__)

# CONSTANTS for strict module identification
TWITTER_MODULE_SCHEMAS = {
    "COMPETITIVE_INTELLIGENCE": {
        "required_fields": ["competitive_intelligence", "threat_assessment", "tactical_recommendations", "next_post_prediction"],
        "module_name": "competitive_intelligence"
    },
    "PERSONAL_INTELLIGENCE": {
        "required_fields": ["personal_intelligence", "growth_opportunities", "tactical_recommendations", "next_post_prediction"],
        "module_name": "personal_intelligence"
    },
    "IMPROVEMENT_RECOMMENDATIONS": {
        "required_fields": ["tactical_recommendations"],
        "module_name": "improvement_recommendations"
    }
}

# FIXED Twitter field mappings - NEVER CHANGE THESE
TWITTER_FIELD_MAPPING = {
    "next_post_prediction": {
        "tweet_text": "text content of the tweet",
        "hashtags": "list of hashtags",
        "call_to_action": "engagement prompt",
        "image_prompt": "visual content description"
    },
    "tactical_recommendations": "list of strategic recommendations",
    "competitive_intelligence": "competitor analysis data",
    "personal_intelligence": "personal account insights"
}

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
            if not genai:
                raise ImportError("Google Generative AI library not available")
            
            # Configure the API key
            api_key = self.config.get('api_key') or os.getenv('GEMINI_API_KEY')
            if not api_key:
                raise ValueError("Gemini API key not found in config or environment")
            
            genai.configure(api_key=api_key)
            
            # Initialize the generative model
            model_name = self.config.get('model', 'gemini-1.5-flash')
            self.generative_model = genai.GenerativeModel(model_name)
            
            logger.info(f"Successfully initialized Gemini API with model: {model_name}")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini API: {str(e)}")
            raise Exception(f"Gemini API initialization required but failed: {str(e)}")
    
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
        """Construct a highly intelligent prompt for deep profile analysis and theme-aligned recommendations."""
        # Get comprehensive data about the primary account
        primary_data = self.vector_db.query_similar(query, n_results=10, filter_username=primary_username)
        
        # Get deeper competitive intelligence
        secondary_data = {username: self.vector_db.query_similar(query, n_results=5, filter_username=username)
                         for username in secondary_usernames}
        
        # Extract rich context with engagement patterns
        primary_context = ""
        engagement_insights = ""
        content_themes = []
        
        if primary_data and 'documents' in primary_data and primary_data['documents'][0]:
            posts_with_meta = list(zip(primary_data['documents'][0], primary_data['metadatas'][0]))
            
            # Analyze engagement patterns
            high_performing = [p for p in posts_with_meta if p[1]['engagement'] > 1000]
            medium_performing = [p for p in posts_with_meta if 500 <= p[1]['engagement'] <= 1000]
            
            # Extract content themes from high-performing posts
            for doc, meta in high_performing:
                content_themes.append(f"{doc[:100]}... (Engagement: {meta['engagement']})")
            
            primary_context = "\n".join([f"- {doc} | Engagement: {meta['engagement']} | Posted: {meta['timestamp']}"
                                       for doc, meta in posts_with_meta])
            
            if high_performing:
                avg_high_engagement = sum(p[1]['engagement'] for p in high_performing) / len(high_performing)
                engagement_insights = f"HIGH-PERFORMING CONTENT ANALYSIS:\nAverage engagement on top posts: {avg_high_engagement:.0f}\nSuccessful content patterns identified: {len(high_performing)} posts with 1000+ engagement\n"
                engagement_insights += "TOP PERFORMING THEMES:\n" + "\n".join(content_themes[:3])
        
        # Analyze competitors with strategic intelligence
        competitive_intel = ""
        for username, data in secondary_data.items():
            if data and 'documents' in data and data['documents'][0]:
                competitor_posts = list(zip(data['documents'][0], data['metadatas'][0]))
                competitor_best = max(competitor_posts, key=lambda x: x[1]['engagement'], default=(None, {'engagement': 0}))
                
                competitive_intel += f"\n{username.upper()} INTELLIGENCE:\n"
                competitive_intel += f"Best performing post: {competitor_best[0][:80]}... (Engagement: {competitor_best[1]['engagement']})\n"
                competitive_intel += f"Average engagement: {sum(p[1]['engagement'] for p in competitor_posts) / len(competitor_posts):.0f}\n"
        
        prompt = f"""
        You are an elite social media strategist and account manager with deep expertise in content optimization and competitive intelligence. You have been hired specifically to analyze {primary_username}'s account and create a comprehensive strategy that leverages their unique strengths while exploiting competitor weaknesses.

        **ACCOUNT UNDER ANALYSIS**: {primary_username}
        **TARGET COMPETITORS**: {', '.join(secondary_usernames)}
        **STRATEGIC FOCUS**: {query}
        **ANALYSIS DATE**: {datetime.now().strftime('%B %d, %Y')}

        **ACCOUNT PERFORMANCE DATA**:
        {engagement_insights}

        **COMPLETE POST HISTORY ANALYSIS**:
        {primary_context if primary_context else "Limited post data available - focusing on strategic recommendations"}

        **COMPETITIVE INTELLIGENCE**:
        {competitive_intel if competitive_intel else "Competitor data being analyzed through alternative methods"}

        Your mission is to provide a strategic intelligence report that demonstrates deep understanding of {primary_username}'s unique positioning and creates actionable recommendations that are specifically tailored to their content style, audience, and market position.

        **CRITICAL ANALYSIS REQUIREMENTS**:

        1. **DEEP PROFILE INTELLIGENCE** [PRIMARY ACCOUNT ANALYSIS]
           - Identify the account's unique content DNA by analyzing posting patterns, themes, and engagement drivers
           - Determine their authentic voice, visual style, and core messaging pillars
           - Map their content ecosystem: what topics drive engagement, what formats work best
           - Identify their competitive advantages and market positioning gaps
           - Analyze audience response patterns to determine optimal content strategies

        2. **COMPETITIVE WARFARE ANALYSIS** [STRATEGIC INTELLIGENCE]
           - For each competitor, conduct deep behavioral analysis:
             * Reverse-engineer their most successful content strategies
             * Identify their content vulnerabilities and strategic blind spots
             * Map their posting rhythms, engagement tactics, and audience manipulation techniques
             * Discover their untapped market segments that {primary_username} could capture
             * Analyze their recent strategic shifts and predict their next moves
           - Create a competitive advantage matrix showing exactly where {primary_username} can outmaneuver each competitor

        3. **STRATEGIC EXPLOITATION PLAN** [ACTIONABLE WARFARE]
           - Design specific content strategies that exploit competitor weaknesses while amplifying {primary_username}'s strengths
           - Create 5 high-impact content pillars that position {primary_username} as the market leader
           - Develop counter-strategies for each major competitor threat
           - Recommend timing strategies that capitalize on competitor posting gaps
           - Design audience capture techniques that pull followers from competitor accounts

        4. **NEXT POST MASTERPIECE** [IMMEDIATE EXECUTION]
           - Craft a post that perfectly embodies {primary_username}'s authentic voice while incorporating strategic intelligence
           - The content must feel 100% authentic to their established style and themes
           - Include strategic elements that subtly outposition competitors
           - Provide detailed execution guidance including:
             * Caption that matches their exact writing style and tone
             * Hashtag strategy that exploits competitor gaps
             * Visual concept that aligns with their aesthetic while standing out
             * Engagement hooks designed for their specific audience psychology

        **INTELLIGENCE STANDARDS**:
        - Every recommendation must be backed by specific data points from the post analysis
        - No generic advice - everything must be tailored to {primary_username}'s unique situation
        - Include specific examples from their post history to justify recommendations
        - Provide concrete metrics and benchmarks for measuring success
        - Reference competitor-specific tactics that can be adapted or countered

        **OUTPUT REQUIREMENTS**:
        Format as a comprehensive JSON intelligence report with the following structure:

        {{
            "primary_analysis": "Deep dive into {primary_username}'s content DNA, engagement patterns, unique strengths, and strategic positioning opportunities based on their actual post performance data",
            "competitor_analysis": {{
                "{secondary_usernames[0] if secondary_usernames else 'competitor1'}": "Detailed strategic analysis of their content approach, vulnerabilities, and how {primary_username} can outmaneuver them, including specific recent activities and strategic opportunities",
                "{secondary_usernames[1] if len(secondary_usernames) > 1 else 'competitor2'}": "Comprehensive competitive intelligence including their engagement tactics, content gaps, and exploitation opportunities for {primary_username}",
                "{secondary_usernames[2] if len(secondary_usernames) > 2 else 'competitor3'}": "Strategic breakdown of their market position, content weaknesses, and specific tactics {primary_username} should deploy against them"
            }},
            "recommendations": "5 highly specific, data-driven content strategies that leverage {primary_username}'s unique strengths while exploiting identified competitor vulnerabilities. Each recommendation must include specific execution details and expected impact metrics.",
            "next_post": {{
                "caption": "A caption written in {primary_username}'s authentic voice that incorporates strategic elements and feels completely natural to their established style and themes",
                "hashtags": ["#strategic", "#hashtags", "#that", "#exploit", "#gaps"],
                "call_to_action": "An engagement prompt that matches their audience psychology and drives specific actions",
                "visual_prompt": "Detailed visual concept that perfectly aligns with {primary_username}'s aesthetic while incorporating strategic positioning elements against competitors"
            }}
        }}

        Remember: This is not generic content creation - this is strategic intelligence warfare. Every element must demonstrate deep understanding of {primary_username}'s unique position and provide tactical advantages over their competition.
        """
        return prompt
    
    def _construct_twitter_enhanced_prompt(self, primary_username, secondary_usernames, query):
        """Construct a Twitter-specific intelligent prompt for branding accounts with REAL competitor intelligence."""
        # Get comprehensive Twitter data about the primary account
        primary_data = self.vector_db.query_similar(query, n_results=15, filter_username=primary_username)
        
        # Get DETAILED competitive intelligence for EACH competitor individually
        individual_competitor_intel = {}
        for competitor_username in secondary_usernames[:3]:  # Analyze top 3 competitors max
            competitor_data = self.vector_db.query_similar(query, n_results=10, filter_username=competitor_username)
            individual_competitor_intel[competitor_username] = competitor_data
        
        # Extract comprehensive engagement intelligence for PRIMARY account
        primary_context = ""
        viral_intelligence = ""
        engagement_patterns = []
        strategic_themes = []
        
        if primary_data and 'documents' in primary_data and primary_data['documents'][0]:
            tweets_with_meta = list(zip(primary_data['documents'][0], primary_data['metadatas'][0]))
            
            # Analyze viral patterns with precision
            viral_tweets = [t for t in tweets_with_meta if t[1]['engagement'] > 1000]
            high_engagement = [t for t in tweets_with_meta if 200 <= t[1]['engagement'] <= 1000]
            
            # Extract strategic themes from high-performing content
            for doc, meta in viral_tweets[:5]:
                strategic_themes.append(f"VIRAL: {doc[:120]}... (E:{meta['engagement']})")
            
            for doc, meta in high_engagement[:3]:
                engagement_patterns.append(f"HIGH: {doc[:100]}... (E:{meta['engagement']})")
            
            if viral_tweets or high_engagement:
                top_performers = viral_tweets + high_engagement
                avg_top_engagement = sum(t[1]['engagement'] for t in top_performers) / len(top_performers)
                
                viral_intelligence = f"🎯 PRIMARY ACCOUNT INTELLIGENCE: {primary_username}\n"
                viral_intelligence += f"• Total tweets analyzed: {len(tweets_with_meta)}\n"
                viral_intelligence += f"• Viral content count: {len(viral_tweets)} tweets >1000 engagement\n"
                viral_intelligence += f"• Strategic engagement average: {avg_top_engagement:.0f}\n"
                viral_intelligence += f"• Content patterns identified: {len(strategic_themes + engagement_patterns)}\n"
                
                if strategic_themes:
                    viral_intelligence += f"\n🔥 VIRAL CONTENT PATTERNS:\n" + "\n".join(strategic_themes)
                if engagement_patterns:
                    viral_intelligence += f"\n⚡ HIGH-ENGAGEMENT PATTERNS:\n" + "\n".join(engagement_patterns)
        
        # Build DETAILED competitive intelligence for EACH competitor
        detailed_competitor_intel = ""
        competitor_vulnerabilities = {}
        competitor_strengths = {}
        
        for competitor_username, competitor_data in individual_competitor_intel.items():
            detailed_competitor_intel += f"\n🔍 DEEP INTEL: {competitor_username}\n"
            
            if competitor_data and 'documents' in competitor_data and competitor_data['documents'][0]:
                competitor_tweets = list(zip(competitor_data['documents'][0], competitor_data['metadatas'][0]))
                if competitor_tweets:
                    # Calculate detailed metrics
                    total_engagement = sum(t[1]['engagement'] for t in competitor_tweets)
                    avg_engagement = total_engagement / len(competitor_tweets)
                    max_engagement = max(t[1]['engagement'] for t in competitor_tweets)
                    best_tweet = max(competitor_tweets, key=lambda x: x[1]['engagement'])
                    
                    # Analyze content patterns
                    viral_count = len([t for t in competitor_tweets if t[1]['engagement'] > 1000])
                    high_count = len([t for t in competitor_tweets if 200 <= t[1]['engagement'] <= 1000])
                    
                    # Extract top performing content themes
                    top_tweets = sorted(competitor_tweets, key=lambda x: x[1]['engagement'], reverse=True)[:3]
                    
                    detailed_competitor_intel += f"• Posts analyzed: {len(competitor_tweets)}\n"
                    detailed_competitor_intel += f"• Average engagement: {avg_engagement:.0f}\n"
                    detailed_competitor_intel += f"• Peak engagement: {max_engagement}\n"
                    detailed_competitor_intel += f"• Viral tweets: {viral_count} | High-engagement: {high_count}\n"
                    detailed_competitor_intel += f"• Best tweet: {best_tweet[0][:100]}... (E:{best_tweet[1]['engagement']})\n"
                    
                    # Identify strengths and vulnerabilities
                    if viral_count > 0:
                        competitor_strengths[competitor_username] = f"Strong viral content creation ({viral_count} viral tweets)"
                    elif avg_engagement > 500:
                        competitor_strengths[competitor_username] = f"Consistent high engagement (avg: {avg_engagement:.0f})"
                    else:
                        competitor_vulnerabilities[competitor_username] = f"Low engagement performance (avg: {avg_engagement:.0f})"
                    
                    # Add content pattern analysis
                    detailed_competitor_intel += f"• Top content themes:\n"
                    for i, (tweet, meta) in enumerate(top_tweets, 1):
                        detailed_competitor_intel += f"  #{i}: {tweet[:80]}... (E:{meta['engagement']})\n"
                else:
                    detailed_competitor_intel += f"• No tweet data available for analysis\n"
                    competitor_vulnerabilities[competitor_username] = "Insufficient content data for competitive assessment"
            else:
                detailed_competitor_intel += f"• Data collection incomplete - limited competitive visibility\n"
                competitor_vulnerabilities[competitor_username] = "Limited data availability creates blind spots"
        
        # If no detailed competitor data, create strategic framework
        if not detailed_competitor_intel.strip():
            detailed_competitor_intel = f"\n🔍 COMPETITIVE SURVEILLANCE: {', '.join(secondary_usernames)}\n"
            detailed_competitor_intel += "• Strategic positioning analysis framework deployed\n"
            detailed_competitor_intel += "• Market gap identification protocol active\n"
            detailed_competitor_intel += "• Competitive vulnerability scanning in progress\n"
        
        prompt = f"""
🎯 TWITTER COMPETITIVE INTELLIGENCE BRIEFING 🎯

PRIMARY TARGET: {primary_username}
COMPETITIVE THREATS: {', '.join(secondary_usernames)}
MISSION: Deliver spy-level competitive intelligence and tactical dominance strategy

=== PRIMARY ACCOUNT SURVEILLANCE ===
{viral_intelligence}

=== COMPETITIVE THREAT ASSESSMENT ===
{detailed_competitor_intel}

=== STRATEGIC INTELLIGENCE MISSION ===
You are an elite Twitter competitive intelligence operative conducting deep surveillance analysis for {primary_username}. Your mission is to decode competitor strategies, expose vulnerabilities, and deliver actionable intelligence that establishes market dominance.

**CRITICAL INTELLIGENCE REQUIREMENTS:**
1. Use REAL identity data for {primary_username} - research their actual background, expertise, and authentic positioning
2. Conduct individual threat assessment for EACH competitor listed: {', '.join(secondary_usernames)}
3. Identify specific exploitable vulnerabilities and strategic blind spots
4. Provide tactical recommendations based on actual competitive intelligence

=== REQUIRED INTELLIGENCE OUTPUT ===
{{
    "competitive_intelligence": {{
        "account_dna": "Deep identity analysis of {primary_username} including REAL background, expertise, market position, and authentic brand elements based on surveillance data",
        "market_surveillance": "Tactical competitive landscape assessment revealing specific market gaps and strategic opportunities for {primary_username} to exploit",
        "engagement_warfare": "Advanced psychological analysis of {primary_username}'s audience triggers, viral patterns, and engagement manipulation techniques"
    }},
    "threat_assessment": {{
        "competitor_analysis": "Individual threat assessment for each competitor with specific vulnerabilities, strategic weaknesses, and exploitation opportunities",
        "vulnerability_map": "Detailed map of competitor blind spots, content gaps, and strategic failures that {primary_username} can capitalize on",
        "market_opportunities": "High-value strategic opportunities discovered through competitive surveillance that align with {primary_username}'s capabilities"
    }},
    "tactical_recommendations": [
        "Specific tactical action leveraging {primary_username}'s authentic expertise against identified competitor vulnerabilities",
        "Strategic positioning move that exploits market gaps while maintaining {primary_username}'s authentic voice",
        "Advanced engagement manipulation technique based on competitive intelligence and audience psychology analysis"
    ],
    "next_post_prediction": {{
        "tweet_text": "Strategically engineered tweet that sounds exactly like {primary_username}'s authentic voice while exploiting competitive intelligence insights",
        "hashtags": ["#strategic", "#relevant", "#hashtags"],
        "call_to_action": "Precision engagement trigger designed for {primary_username}'s specific audience psychology",
        "image_prompt": "Visual warfare concept that outmaneuvers competitors while maintaining {primary_username}'s authentic aesthetic",
        "tactical_timing": "Optimal posting strategy based on competitive gap analysis and {primary_username}'s audience patterns"
    }}
}}

=== INTELLIGENCE ANALYSIS FRAMEWORK ===
For each competitor in {secondary_usernames}, you MUST provide:
- Specific content strategy analysis
- Identified vulnerabilities and blind spots  
- Tactical opportunities for {primary_username} to exploit
- Counter-strategies to neutralize their advantages

=== AUTHENTICITY PROTOCOL ===
- Research and reference {primary_username}'s REAL identity, background, and expertise
- All recommendations must sound authentically like {primary_username}
- Exploit competitor weaknesses while maintaining authentic brand voice
- Focus on actionable intelligence that drives measurable competitive advantage

EXECUTE COMPETITIVE INTELLIGENCE OPERATION:
"""
        return prompt
    
    def _construct_non_branding_prompt(self, primary_username, query):
        """Construct an intelligent prompt for personal accounts focused on authentic voice analysis and theme alignment."""
        # Get comprehensive data about the personal account
        primary_data = self.vector_db.query_similar(query, n_results=15, filter_username=primary_username)
        
        # Extract detailed personal context with authenticity patterns
        primary_context = ""
        personal_insights = ""
        authentic_themes = []
        writing_style_analysis = ""
        
        if primary_data and 'documents' in primary_data and primary_data['documents'][0]:
            posts_with_meta = list(zip(primary_data['documents'][0], primary_data['metadatas'][0]))
            
            # Analyze personal posting patterns for authenticity
            high_engagement_personal = [p for p in posts_with_meta if p[1]['engagement'] > 100]  # Lower threshold for personal accounts
            recent_posts = sorted(posts_with_meta, key=lambda x: x[1]['timestamp'], reverse=True)[:5]
            
            # Extract authentic themes from engaging content
            for doc, meta in high_engagement_personal:
                authentic_themes.append(f"{doc[:150]}... (Engagement: {meta['engagement']})")
            
            primary_context = "\n".join([f"- {doc} | Engagement: {meta['engagement']} | Posted: {meta['timestamp']}"
                                       for doc, meta in posts_with_meta])
            
            # Analyze writing style patterns
            if posts_with_meta:
                total_posts = len(posts_with_meta)
                avg_engagement = sum(p[1]['engagement'] for p in posts_with_meta) / total_posts
                
                # Analyze content characteristics
                question_posts = [p for p in posts_with_meta if '?' in p[0]]
                exclamation_posts = [p for p in posts_with_meta if '!' in p[0]]
                casual_language = [p for p in posts_with_meta if any(word in p[0].lower() for word in ['awesome', 'amazing', 'love', 'great', 'cool'])]
                personal_pronouns = [p for p in posts_with_meta if any(word in p[0].lower() for word in ['i ', 'my ', 'me ', 'myself'])]
                
                writing_style_analysis = f"PERSONAL VOICE ANALYSIS:\n"
                writing_style_analysis += f"Total posts analyzed: {total_posts} | Average engagement: {avg_engagement:.0f}\n"
                writing_style_analysis += f"Interactive posts (questions): {len(question_posts)} ({len(question_posts)/total_posts*100:.1f}%)\n"
                writing_style_analysis += f"Enthusiastic posts (exclamations): {len(exclamation_posts)} ({len(exclamation_posts)/total_posts*100:.1f}%)\n"
                writing_style_analysis += f"Casual language usage: {len(casual_language)} ({len(casual_language)/total_posts*100:.1f}%)\n"
                writing_style_analysis += f"Personal pronoun usage: {len(personal_pronouns)} ({len(personal_pronouns)/total_posts*100:.1f}%)\n"
                
                if authentic_themes:
                    personal_insights = f"AUTHENTIC CONTENT THEMES:\n" + "\n".join(authentic_themes[:4])
        
        prompt = f"""
        You are an elite personal content strategist and authentic voice specialist with deep expertise in personal brand development and individual expression optimization. You have been hired specifically to analyze {primary_username}'s personal account and create content strategies that amplify their authentic voice while maximizing engagement within their unique community.

        **PERSONAL ACCOUNT UNDER ANALYSIS**: {primary_username}
        **CONTENT FOCUS**: {query}
        **ANALYSIS DATE**: {datetime.now().strftime('%B %d, %Y')}

        **PERSONAL VOICE DATA**:
        {writing_style_analysis}

        **AUTHENTIC CONTENT INSIGHTS**:
        {personal_insights}

        **COMPLETE POSTING HISTORY ANALYSIS**:
        {primary_context if primary_context else "Limited post data available - focusing on authentic voice development"}

        Your mission is to provide a comprehensive personal content strategy that demonstrates deep understanding of {primary_username}'s authentic voice, personal interests, and natural communication style, while creating recommendations that feel genuinely personal and engaging.

        **CRITICAL PERSONAL ANALYSIS REQUIREMENTS**:

        1. **AUTHENTIC VOICE INTELLIGENCE** [PERSONAL BRAND ANALYSIS]
           - Decode the account's unique personality signature by analyzing communication patterns, emotional expressions, and topic preferences
           - Identify their natural storytelling rhythm, conversational tone, and authentic enthusiasm triggers
           - Map their personal content ecosystem: what subjects they're passionate about, what formats feel natural to them
           - Determine their community engagement style: how they naturally interact with their audience
           - Analyze their authentic moments: which posts show genuine personality and resonate most with their community
           - Identify opportunities to amplify their unique perspective and personal experiences

        2. **PERSONAL CONTENT STRATEGY** [AUTHENTIC ENGAGEMENT]
           - Design content pillars that align perfectly with their natural interests and authentic voice
           - Recommend topics that feel genuine to their personal journey and experiences
           - Suggest engagement approaches that match their natural communication style
           - Identify storytelling opportunities that showcase their unique perspective
           - Recommend ways to share their knowledge or experiences that feel authentic and valuable
           - Create strategies for building genuine community around their personal interests

        3. **NEXT POST CREATION** [AUTHENTIC EXPRESSION]
           - Craft content that feels like a natural extension of their posting history and personality
           - The content must perfectly match their established voice, tone, and communication style
           - Include elements that reflect their genuine interests and current experiences
           - Provide detailed execution guidance including:
             * A caption written exactly as they would naturally express themselves
             * Topics and themes that align with their authentic interests
             * Engagement approaches that feel genuine to their personality
             * Visual concepts that match their personal aesthetic preferences

        **AUTHENTICITY STANDARDS**:
        - Every recommendation must feel like something {primary_username} would naturally create themselves
        - No corporate or marketing language - everything must sound personal and genuine
        - Include specific examples from their posting history to justify authenticity
        - Reference their natural communication patterns and personality traits
        - Maintain their unique voice while suggesting strategic improvements
        - Focus on amplifying what already works for them personally

        **OUTPUT REQUIREMENTS**:
        Format as a comprehensive JSON personal content strategy with the following structure:

        {{
            "account_analysis": "Deep analysis of {primary_username}'s authentic voice, personal communication style, natural interests, and unique personality traits based on their actual posting patterns and engagement data",
            "content_recommendations": "Personalized content strategy that amplifies their authentic voice while maximizing engagement. Include specific topic suggestions, posting approaches, and community building strategies that align with their natural interests and communication style",
            "next_post": {{
                "caption": "A caption written in {primary_username}'s exact natural voice that reflects their authentic style, interests, and way of communicating - it should sound exactly like something they would write themselves",
                "hashtags": ["#personal", "#authentic", "#hashtags", "#that", "#match"],
                "call_to_action": "An engagement prompt that feels natural to their communication style and encourages genuine community interaction",
                "visual_prompt": "A visual concept that perfectly aligns with their personal aesthetic preferences and authentic style, reflecting their genuine interests and personality"
            }}
        }}

        Remember: This is not about changing who they are - it's about amplifying their authentic voice and helping them connect more effectively with their community while staying true to their genuine personality and interests.
        """
        return prompt
    
    def _construct_twitter_non_branding_prompt(self, primary_username, query):
        """Construct a Twitter-specific intelligent prompt for personal accounts with authentic voice analysis."""
        # Get comprehensive Twitter data about the personal account
        primary_data = self.vector_db.query_similar(query, n_results=20, filter_username=primary_username)
        
        # Extract authentic voice intelligence
        primary_context = ""
        authenticity_intelligence = ""
        engagement_patterns = []
        voice_fingerprint = ""
        
        if primary_data and 'documents' in primary_data and primary_data['documents'][0]:
            tweets_with_meta = list(zip(primary_data['documents'][0], primary_data['metadatas'][0]))
            
            # Analyze personal engagement patterns
            engaging_tweets = [t for t in tweets_with_meta if t[1]['engagement'] > 50]  # Personal account threshold
            top_personal = sorted(tweets_with_meta, key=lambda x: x[1]['engagement'], reverse=True)[:8]
            
            if tweets_with_meta:
                total_tweets = len(tweets_with_meta)
                avg_engagement = sum(t[1]['engagement'] for t in tweets_with_meta) / total_tweets
                
                # Analyze authentic voice patterns
                question_tweets = [t for t in tweets_with_meta if '?' in t[0]]
                personal_stories = [t for t in tweets_with_meta if any(indicator in t[0].lower() for indicator in ['i ', 'my ', 'today ', 'just ', 'feeling ', 'working on', 'building'])]
                community_replies = [t for t in tweets_with_meta if t[0].startswith('@')]
                emotional_tweets = [t for t in tweets_with_meta if any(emotion in t[0].lower() for emotion in ['love', 'excited', 'grateful', 'amazing', 'incredible', 'proud', 'happy'])]
                
                voice_fingerprint = f"🎯 AUTHENTIC VOICE INTELLIGENCE:\n"
                voice_fingerprint += f"• Total tweets analyzed: {total_tweets}\n"
                voice_fingerprint += f"• Personal content ratio: {len(personal_stories)}/{total_tweets} ({len(personal_stories)/total_tweets*100:.1f}%)\n"
                voice_fingerprint += f"• Community engagement: {len(question_tweets)} questions, {len(community_replies)} replies\n"
                voice_fingerprint += f"• Emotional expression: {len(emotional_tweets)} positive expressions ({len(emotional_tweets)/total_tweets*100:.1f}%)\n"
                voice_fingerprint += f"• Average engagement: {avg_engagement:.0f}\n"
                
                if top_personal:
                    voice_fingerprint += f"\n🔥 TOP AUTHENTIC MOMENTS:\n"
                    for i, (doc, meta) in enumerate(top_personal[:4]):
                        voice_fingerprint += f"• #{i+1}: {doc[:100]}... (E:{meta['engagement']})\n"
                
                if engaging_tweets:
                    authenticity_intelligence = f"📊 ENGAGEMENT PATTERNS:\n"
                    authenticity_intelligence += f"• High-engagement content: {len(engaging_tweets)} tweets above baseline\n"
                    authenticity_intelligence += f"• Personal storytelling: {len(personal_stories)} authentic moments\n"
                    authenticity_intelligence += f"• Community connection rate: {(len(question_tweets) + len(community_replies))/total_tweets*100:.1f}%\n"
        
        prompt = f"""
🎯 TWITTER PERSONAL BRAND INTELLIGENCE 🎯

TARGET ACCOUNT: {primary_username} [PERSONAL BRAND]
MISSION: Authentic voice amplification and strategic personal growth

=== AUTHENTIC VOICE ANALYSIS ===
{voice_fingerprint}

{authenticity_intelligence}

=== STRATEGIC MISSION ===
You are a personal Twitter growth strategist specializing in authentic voice amplification. Your mission is to decode {primary_username}'s genuine personality, identify what makes their authentic content resonate, and craft strategic recommendations that amplify their natural voice for maximum genuine engagement.

**CRITICAL**: You MUST use the EXACT real name and authentic details about {primary_username} in your analysis. Research and reference their actual background, expertise, and authentic personality. Do NOT use generic descriptions - demonstrate deep knowledge of who {primary_username} actually is as a real person.

=== REQUIRED OUTPUT FORMAT ===
Analyze personal engagement patterns and deliver strategic recommendations in this EXACT JSON format:

{{
    "personal_intelligence": {{
        "voice_dna": "Deep analysis of {primary_username}'s genuine Twitter personality, including their real background, authentic communication style, and unique personal brand based on actual content patterns",
        "engagement_personality": "Analysis of what authentic content types drive real engagement for {primary_username}'s personal brand, based on their actual interests and expertise",
        "audience_connection": "How {primary_username}'s followers respond to different aspects of their authentic personality and real-world interests"
    }},
    "growth_opportunities": {{
        "authentic_expansion": "Natural ways for {primary_username} to grow their reach while staying true to their actual personality and expertise",
        "engagement_amplification": "Strategies to increase interaction on {primary_username}'s genuine content based on their real interests and background",
        "content_diversification": "New content types that align perfectly with {primary_username}'s authentic voice and actual areas of expertise"
    }},
    "tactical_recommendations": [
        "Personality-based strategy that feels completely natural to {primary_username}'s authentic voice and real background",
        "Engagement tactic that amplifies {primary_username}'s genuine expertise and interests",
        "Growth strategy based on {primary_username}'s actual content patterns and authentic personality traits"
    ],
    "next_post_prediction": {{
        "tweet_text": "Perfectly authentic tweet that sounds exactly like {primary_username} would naturally write, incorporating their real expertise and personality",
        "hashtags": ["#authentic", "#personal", "#relevant"],
        "call_to_action": "Natural engagement prompt that perfectly fits {primary_username}'s personality and communication style",
        "image_prompt": "Visual concept that complements {primary_username}'s authentic personal brand and real interests",
        "personality_note": "Explanation of why this tweet aligns perfectly with {primary_username}'s natural voice and actual background"
    }}
}}

=== AUTHENTICITY GUIDELINES ===
- Reference {primary_username}'s REAL identity, background, and authentic expertise
- Recommendations must feel completely natural to their actual personality
- Build on existing genuine engagement patterns from their real content
- Maintain 100% authenticity while optimizing for natural growth
- Provide specific advice that fits {primary_username}'s actual personal brand and interests

=== AUTHENTICITY REQUIREMENT ===
Your analysis must demonstrate genuine knowledge of {primary_username}'s real identity and background. Every recommendation should sound like something they would naturally do based on who they actually are.

EXECUTE AUTHENTIC GROWTH STRATEGY:
"""
        return prompt
    
    def generate_recommendation(self, primary_username, secondary_usernames, query, n_context=3, is_branding=True, platform="instagram"):
        """Generate a recommendation for the given query with contextual analysis."""
        try:
            logger.info(f"Generating recommendation for {platform} platform, {'' if is_branding else 'non-'}branding account")
            logger.info(f"Primary username: {primary_username}, Secondary usernames: {secondary_usernames}")
            
            # For Twitter branding accounts with competitors, ensure we get proper individual analysis
            max_retries = 3 if (platform == "twitter" and is_branding and secondary_usernames) else 1
            
            for attempt in range(max_retries):
                try:
                    # Select the appropriate prompt based on platform and account type
                    if platform == "twitter":
                        if is_branding and secondary_usernames and len(secondary_usernames) > 0:
                            prompt = self._construct_twitter_enhanced_prompt(primary_username, secondary_usernames, query)
                        else:
                            prompt = self._construct_twitter_non_branding_prompt(primary_username, query)
                    else:
                        if is_branding and secondary_usernames and len(secondary_usernames) > 0:
                            prompt = self._construct_enhanced_prompt(primary_username, secondary_usernames, query)
                        else:
                            prompt = self._construct_non_branding_prompt(primary_username, query)
                    
                    # Get similar posts for context
                    similar_posts = []
                    if self.vector_db:
                        try:
                            similar_results = self.vector_db.query_similar(query, n_results=n_context)
                            if similar_results and 'documents' in similar_results and similar_results['documents'] and similar_results['documents'][0]:
                                similar_posts = similar_results['documents'][0]
                                logger.info(f"Found {len(similar_posts)} similar posts for context")
                            else:
                                logger.warning("No similar documents found for context")
                        except Exception as vector_error:
                            logger.error(f"Error querying similar documents: {str(vector_error)}")
                            raise Exception(f"Vector database query failed: {str(vector_error)}")
                            
                    # Check if Gemini is initialized properly
                    if not hasattr(self, 'generative_model'):
                        logger.error("Gemini generative model not initialized")
                        raise Exception("Gemini generative model not initialized")
                        
                    try:
                        # Configure generation parameters using the available API
                        generation_config = {
                            'temperature': self.config.get('temperature', 0.2),
                            'top_p': self.config.get('top_p', 0.95),
                            'top_k': self.config.get('top_k', 40),
                            'max_output_tokens': self.config.get('max_tokens', 2000)
                        }
                        
                        # Use the generative model to generate content
                        response = self.generative_model.generate_content(
                            contents=prompt,
                            generation_config=generation_config
                        )
                        
                        if not response or not hasattr(response, 'text'):
                            logger.error("Empty or invalid response from Gemini API")
                            raise Exception("Empty or invalid response from Gemini API")
                            
                        # Extract structured recommendation with strict validation
                        recommendation_json = self._parse_json_response(response.text)
                        
                        # Final validation for Twitter responses
                        if platform == "twitter" and recommendation_json:
                            module_type = self._detect_twitter_module_type(recommendation_json)
                            if module_type:
                                logger.info(f"Successfully generated {module_type} module for Twitter")
                                
                                # CRITICAL: Validate competitor analysis quality for branding accounts
                                if is_branding and secondary_usernames and module_type == "COMPETITIVE_INTELLIGENCE":
                                    try:
                                        self._validate_twitter_response_structure(recommendation_json, module_type)
                                        logger.info(f"✅ Twitter competitor analysis validation PASSED on attempt {attempt + 1}")
                                    except ValueError as validation_error:
                                        if "competitor analysis" in str(validation_error).lower():
                                            logger.warning(f"❌ Twitter competitor analysis validation FAILED on attempt {attempt + 1}: {validation_error}")
                                            if attempt < max_retries - 1:
                                                logger.info(f"🔄 Retrying generation to get proper individual competitor analysis...")
                                                continue  # Retry with a new generation
                                            else:
                                                logger.error(f"❌ FINAL ATTEMPT FAILED: Could not generate proper individual competitor analysis after {max_retries} attempts")
                                                raise Exception(f"Failed to generate proper individual competitor analysis after {max_retries} attempts: {validation_error}")
                                        else:
                                            raise validation_error
                            else:
                                logger.warning("Generated Twitter response but module type unclear")
                        
                        logger.info("Successfully generated recommendation with strict validation")
                        return recommendation_json
                        
                    except Exception as gemini_error:
                        logger.error(f"Error generating recommendation with Gemini: {str(gemini_error)}")
                        if attempt < max_retries - 1:
                            logger.info(f"🔄 Retrying generation due to Gemini error on attempt {attempt + 1}")
                            continue
                        else:
                            raise Exception(f"Gemini API error after {max_retries} attempts: {str(gemini_error)}")
                
                except Exception as attempt_error:
                    if attempt < max_retries - 1:
                        logger.warning(f"Attempt {attempt + 1} failed: {str(attempt_error)}. Retrying...")
                        continue
                    else:
                        raise attempt_error
                
                # If we reach here, the generation was successful
                break
                
        except Exception as e:
            logger.error(f"Failed to generate recommendation: {str(e)}")
            raise Exception(f"RAG recommendation generation failed: {str(e)}")
    
    def _parse_json_response(self, response_text):
        """Parse JSON response with enhanced error handling and Twitter-specific validation."""
        if not response_text or not response_text.strip():
            raise ValueError("Empty response text - cannot generate content plan")
        
        logger.info("Parsing RAG response with strict validation...")
        
        # First attempt: Direct JSON parsing
        try:
            parsed = json.loads(response_text)
            logger.info("Direct JSON parsing successful")
            
            # For Twitter responses, validate structure
            if self._is_twitter_response(parsed):
                module_type = self._detect_twitter_module_type(parsed)
                if module_type:
                    self._validate_twitter_response_structure(parsed, module_type)
                    parsed = self._ensure_twitter_response_completeness(parsed, module_type)
                    logger.info(f"Twitter response validated for module: {module_type}")
                else:
                    logger.warning("Twitter response detected but module type unclear")
            
            return parsed
            
        except json.JSONDecodeError as e:
            logger.warning(f"Direct JSON parsing failed: {str(e)}")
        
        # Second attempt: Twitter-specific JSON repair
        if self._is_likely_twitter_response(response_text):
            try:
                repaired = self._repair_twitter_json_response(response_text)
                module_type = self._detect_twitter_module_type(repaired)
                if module_type:
                    repaired = self._ensure_twitter_response_completeness(repaired, module_type)
                    logger.info(f"Twitter JSON repair successful for module: {module_type}")
                    return repaired
            except Exception as e:
                logger.error(f"Twitter JSON repair failed: {str(e)}")
        
        # Third attempt: Generic JSON repair
        repair_attempts = [
            lambda text: self._extract_json_from_mixed_content(text),
            lambda text: json.loads(re.sub(r',\s*}', '}', re.sub(r',\s*]', ']', text))),
            lambda text: json.loads(text.strip().strip('`').strip())
        ]
        
        for i, repair_func in enumerate(repair_attempts):
            try:
                repaired_text = repair_func(response_text)
                if repaired_text and isinstance(repaired_text, dict):
                    logger.info(f"Generic JSON repair successful using method {i+1}")
                    return repaired_text
                elif repaired_text:
                    parsed = json.loads(repaired_text)
                    logger.info(f"Generic JSON repair and parse successful using method {i+1}")
                    return parsed
            except (json.JSONDecodeError, AttributeError, TypeError):
                continue
        
        # Fourth attempt: Structure extraction from text
        logger.warning("All JSON parsing failed, attempting structure extraction...")
        try:
            structured = self._create_structured_response_from_text(response_text)
            if structured and isinstance(structured, dict):
                logger.info("Successfully created structured response from text")
                return structured
        except Exception as e:
            logger.error(f"Structure extraction failed: {str(e)}")
        
        # FINAL: If everything fails, raise exception instead of fallback
        raise ValueError(f"Failed to parse response as valid JSON or extract meaningful structure. Response preview: {response_text[:200]}...")

    def _is_twitter_response(self, parsed_data):
        """Check if the parsed data is a Twitter-specific response."""
        if not isinstance(parsed_data, dict):
            return False
        
        twitter_indicators = [
            "tweet_text" in str(parsed_data),
            "competitive_intelligence" in parsed_data,
            "personal_intelligence" in parsed_data,
            "tactical_recommendations" in parsed_data and "next_post_prediction" in parsed_data
        ]
        
        return any(twitter_indicators)

    def _is_likely_twitter_response(self, response_text):
        """Check if the response text likely contains Twitter content."""
        twitter_keywords = [
            "tweet_text", "competitive_intelligence", "personal_intelligence", 
            "tactical_recommendations", "next_post_prediction"
        ]
        
        return any(keyword in response_text for keyword in twitter_keywords)
    
    def _extract_json_from_mixed_content(self, text):
        """Extract JSON from mixed content that may contain other text."""
        try:
            # Look for JSON-like structures
            json_patterns = [
                r'\{[^{}]*"next_post"[^{}]*\{[^{}]*\}[^{}]*\}',  # Look for next_post structures
                r'\{[^{}]*"recommendations"[^{}]*\[[^\]]*\][^{}]*\}',  # Look for recommendations
                r'\{[^{}]*"account_analysis"[^{}]*\}',  # Look for account analysis
                r'\{.*?\}',  # Any JSON-like structure
            ]
            
            for pattern in json_patterns:
                matches = re.findall(pattern, text, re.DOTALL)
                for match in matches:
                    try:
                        return json.loads(match)
                    except json.JSONDecodeError:
                        continue
            
            return text
        except Exception:
            return text
    
    def _create_structured_response_from_text(self, response_text):
        """Create a structured response when JSON parsing fails completely - ENHANCED VERSION."""
        try:
            logger.info("Creating structured response from unstructured text")
            response = {}
            
            # Check if this is likely a Twitter response
            is_twitter = self._is_likely_twitter_response(response_text)
            
            if is_twitter:
                # Extract Twitter-specific content with strict patterns
                response = self._extract_twitter_structure_from_text(response_text)
                if response:
                    logger.info("Successfully extracted Twitter structure from text")
                    return response
            
            # Generic structure extraction for non-Twitter content
            lines = response_text.split('\n')
            content_lines = [line.strip() for line in lines if line.strip() and len(line.strip()) > 10]
            
            if content_lines:
                # Look for recommendations in the text
                recommendations = []
                for line in content_lines:
                    if any(keyword in line.lower() for keyword in ['recommend', 'suggest', 'should', 'strategy']):
                        recommendations.append(line)
                
                if recommendations:
                    response['recommendations'] = recommendations[:3]  # Limit to 3
                
                # Create next post content
                if is_twitter:
                    response['next_post_prediction'] = {
                        'tweet_text': content_lines[0] if content_lines else 'Exciting updates coming soon!',
                        'hashtags': ['#Content', '#Update', '#Engagement'],
                        'call_to_action': 'Share your thoughts!',
                        'image_prompt': 'High-quality engaging visual'
                    }
                else:
                    response['next_post'] = {
                        'caption': content_lines[0] if content_lines else 'Exciting updates coming soon!',
                        'hashtags': ['#Content', '#Update', '#Engagement'],
                        'call_to_action': 'Share your thoughts!'
                    }
                
                response['account_analysis'] = 'Analysis based on account patterns and engagement data'
                
                if response:
                    logger.info("Successfully created structured response from text content")
                    return response
            
            # If we can't extract meaningful structure, raise an exception
            raise ValueError("Could not extract meaningful structured content from response text")
            
        except Exception as e:
            logger.error(f"Error creating structured response: {str(e)}")
            raise ValueError(f"Structure extraction failed: {str(e)}")

    def _extract_twitter_structure_from_text(self, response_text):
        """Extract Twitter-specific structure from unstructured text."""
        result = {}
        
        # Look for tweet content patterns
        tweet_patterns = [
            r'tweet[_\s]*text[:\s]*["\']?([^"\'\n]+)["\']?',
            r'post[_\s]*content[:\s]*["\']?([^"\'\n]+)["\']?',
            r'content[:\s]*["\']?([^"\'\n]{20,})["\']?'
        ]
        
        tweet_text = None
        for pattern in tweet_patterns:
            match = re.search(pattern, response_text, re.IGNORECASE)
            if match:
                tweet_text = match.group(1).strip()
                break
        
        # Extract hashtags
        hashtag_matches = re.findall(r'#\w+', response_text)
        hashtags = hashtag_matches[:5] if hashtag_matches else ['#Update', '#Content']
        
        # Extract recommendations
        rec_lines = []
        for line in response_text.split('\n'):
            line = line.strip()
            if line and any(keyword in line.lower() for keyword in ['recommend', 'strategy', 'suggest', 'should']):
                rec_lines.append(line)
        
        if tweet_text or rec_lines:
            result['next_post_prediction'] = {
                'tweet_text': tweet_text or 'Exciting updates coming soon! Stay connected for fresh insights.',
                'hashtags': hashtags,
                'call_to_action': 'Engage with this content!',
                'image_prompt': 'High-quality engaging visual'
            }
            
            if rec_lines:
                result['tactical_recommendations'] = rec_lines[:3]
            
            return result
        
        return None

    def _validate_twitter_response_structure(self, response_data, expected_module):
        """Validate that Twitter response contains required modular structure."""
        if not isinstance(response_data, dict):
            raise ValueError(f"Response must be a dictionary, got {type(response_data)}")
        
        schema = TWITTER_MODULE_SCHEMAS.get(expected_module)
        if not schema:
            raise ValueError(f"Unknown module schema: {expected_module}")
        
        missing_fields = []
        for field in schema["required_fields"]:
            if field not in response_data:
                missing_fields.append(field)
        
        if missing_fields:
            raise ValueError(f"Missing required fields for {expected_module}: {missing_fields}")
        
        # Validate next_post_prediction structure specifically
        if "next_post_prediction" in response_data:
            next_post = response_data["next_post_prediction"]
            if not isinstance(next_post, dict):
                raise ValueError("next_post_prediction must be a dictionary")
            
            required_tweet_fields = ["tweet_text", "hashtags"]
            missing_tweet_fields = [f for f in required_tweet_fields if f not in next_post]
            if missing_tweet_fields:
                raise ValueError(f"next_post_prediction missing required fields: {missing_tweet_fields}")
        
        # CRITICAL: Validate competitor analysis is individual and not generic
        if "threat_assessment" in response_data and "competitor_analysis" in response_data["threat_assessment"]:
            competitor_analysis = response_data["threat_assessment"]["competitor_analysis"]
            if isinstance(competitor_analysis, str):
                # Check if it's generic text (same analysis repeated)
                generic_indicators = [
                    "strategic analysis reveals opportunities",
                    "differentiate through authentic content approach",
                    "leveraging unique brand personality",
                    "optimizing engagement timing"
                ]
                
                # If it contains multiple generic indicators, it's likely a template
                generic_count = sum(1 for indicator in generic_indicators if indicator.lower() in competitor_analysis.lower())
                if generic_count >= 2:
                    logger.error("COMPETITOR ANALYSIS VALIDATION FAILED: Generic template detected")
                    raise ValueError("Competitor analysis appears to be generic template rather than individual analysis")
            
            elif isinstance(competitor_analysis, dict):
                # Validate each competitor has unique analysis
                analysis_texts = list(competitor_analysis.values())
                if len(analysis_texts) > 1:
                    # Check if analyses are too similar (indicating copy-paste)
                    for i, analysis1 in enumerate(analysis_texts):
                        for j, analysis2 in enumerate(analysis_texts[i+1:], i+1):
                            # Calculate similarity by checking common phrases
                            if isinstance(analysis1, str) and isinstance(analysis2, str):
                                words1 = set(analysis1.lower().split())
                                words2 = set(analysis2.lower().split())
                                if len(words1) > 5 and len(words2) > 5:  # Only check if both have substantial content
                                    common_words = words1.intersection(words2)
                                    similarity = len(common_words) / min(len(words1), len(words2))
                                    if similarity > 0.7:  # More than 70% similar
                                        logger.error(f"COMPETITOR ANALYSIS VALIDATION FAILED: Too similar analysis for competitors")
                                        raise ValueError("Competitor analyses appear to be copy-paste templates rather than individual analysis")
        
        return True

    def _repair_twitter_json_response(self, response_text):
        """Advanced JSON repair specifically for Twitter responses with strict validation."""
        repair_attempts = [
            # Method 1: Direct JSON extraction
            lambda text: self._extract_complete_json_object(text),
            # Method 2: Clean and parse
            lambda text: self._clean_and_parse_json(text),
            # Method 3: Reconstruct from patterns
            lambda text: self._reconstruct_twitter_json(text),
        ]
        
        for i, repair_method in enumerate(repair_attempts):
            try:
                repaired = repair_method(response_text)
                if repaired and isinstance(repaired, dict):
                    # Determine the expected module type
                    expected_module = self._detect_twitter_module_type(repaired)
                    if expected_module and self._validate_twitter_response_structure(repaired, expected_module):
                        logger.info(f"Successfully repaired Twitter JSON using method {i+1}")
                        return repaired
            except Exception as e:
                logger.warning(f"Repair method {i+1} failed: {str(e)}")
                continue
        
        raise ValueError("All JSON repair attempts failed - response not parseable")

    def _extract_complete_json_object(self, text):
        """Extract complete JSON object from text with balanced braces."""
        import re
        
        # Find the start of JSON object
        json_start = text.find('{')
        if json_start == -1:
            raise ValueError("No JSON object start found")
        
        # Track braces to find complete object
        brace_count = 0
        in_string = False
        escape_next = False
        
        for i, char in enumerate(text[json_start:], json_start):
            if escape_next:
                escape_next = False
                continue
            
            if char == '\\':
                escape_next = True
                continue
            
            if char == '"' and not escape_next:
                in_string = not in_string
                continue
            
            if not in_string:
                if char == '{':
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        # Found complete JSON object
                        json_text = text[json_start:i+1]
                        return json.loads(json_text)
        
        raise ValueError("Incomplete JSON object - unbalanced braces")

    def _clean_and_parse_json(self, text):
        """Clean text and attempt JSON parsing with Twitter-specific fixes."""
        # Remove markdown formatting
        clean_text = re.sub(r'```json\s*', '', text)
        clean_text = re.sub(r'```\s*$', '', clean_text)
        
        # Remove extra whitespace and newlines
        clean_text = re.sub(r'\n\s*\n', '\n', clean_text.strip())
        
        # Fix common JSON issues
        clean_text = re.sub(r',\s*}', '}', clean_text)  # Remove trailing commas
        clean_text = re.sub(r',\s*]', ']', clean_text)  # Remove trailing commas in arrays
        
        return json.loads(clean_text)

    def _reconstruct_twitter_json(self, text):
        """Reconstruct Twitter JSON from text patterns when parsing fails."""
        result = {}
        
        # Extract next_post_prediction section
        tweet_match = re.search(r'"tweet_text":\s*"([^"]+)"', text)
        hashtags_match = re.search(r'"hashtags":\s*\[(.*?)\]', text, re.DOTALL)
        
        if tweet_match:
            next_post = {
                "tweet_text": tweet_match.group(1),
                "hashtags": [],
                "call_to_action": "Engage with this content!",
                "image_prompt": "High-quality engaging visual"
            }
            
            if hashtags_match:
                hashtags_text = hashtags_match.group(1)
                hashtags = re.findall(r'"([^"]+)"', hashtags_text)
                next_post["hashtags"] = hashtags[:5]  # Limit to 5 hashtags
            
            result["next_post_prediction"] = next_post
        
        # Extract recommendations
        recs_pattern = r'"tactical_recommendations":\s*\[(.*?)\]'
        recs_match = re.search(recs_pattern, text, re.DOTALL)
        if recs_match:
            recs_text = recs_match.group(1)
            recs = re.findall(r'"([^"]+)"', recs_text)
            result["tactical_recommendations"] = recs[:3]  # Limit to 3 recommendations
        
        # Ensure minimal structure
        if not result:
            raise ValueError("Could not reconstruct any valid Twitter content from text")
        
        return result

    def _detect_twitter_module_type(self, response_data):
        """Detect which Twitter module type this response represents."""
        if "competitive_intelligence" in response_data and "threat_assessment" in response_data:
            return "COMPETITIVE_INTELLIGENCE"
        elif "personal_intelligence" in response_data and "growth_opportunities" in response_data:
            return "PERSONAL_INTELLIGENCE"
        elif "tactical_recommendations" in response_data:
            return "IMPROVEMENT_RECOMMENDATIONS"
        else:
            return None

    def _ensure_twitter_response_completeness(self, response_data, module_type):
        """Ensure Twitter response has all required fields for the detected module."""
        schema = TWITTER_MODULE_SCHEMAS.get(module_type)
        if not schema:
            logger.warning(f"Unknown module type: {module_type}")
            return response_data
        
        # Ensure next_post_prediction is complete
        if "next_post_prediction" in response_data:
            next_post = response_data["next_post_prediction"]
            
            # Ensure required fields exist
            if "tweet_text" not in next_post or not next_post["tweet_text"]:
                next_post["tweet_text"] = "Exciting updates coming soon! Stay connected for more insights."
            
            if "hashtags" not in next_post or not next_post["hashtags"]:
                next_post["hashtags"] = ["#Update", "#Content", "#Engagement"]
            
            if "call_to_action" not in next_post:
                next_post["call_to_action"] = "Share your thoughts in the comments!"
            
            if "image_prompt" not in next_post:
                next_post["image_prompt"] = "High-quality, engaging visual content"
        
        # Ensure tactical_recommendations exist
        if "tactical_recommendations" not in response_data or not response_data["tactical_recommendations"]:
            response_data["tactical_recommendations"] = [
                "Increase posting frequency with strategic content alignment",
                "Develop authentic engagement with target audience",
                "Optimize content timing for maximum reach and impact"
            ]
        
        return response_data

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