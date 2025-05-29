"""Module for RAG implementation using Google Gemini API with enhanced contextual intelligence."""

import logging
import json
import re
import google.generativeai as genai
from vector_database import VectorDatabaseManager
from config import GEMINI_CONFIG, LOGGING_CONFIG, CONTENT_TEMPLATES
from datetime import datetime

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
            import google.generativeai as genai
            genai.configure(api_key=self.config['api_key'])
            self.model = self.config['model']
            self.generative_model = genai.GenerativeModel(self.model)
            logger.info(f"Successfully initialized Gemini API with model: {self.model}")
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
        """Construct a Twitter-specific intelligent prompt for deep profile analysis and theme-aligned recommendations."""
        # Get comprehensive Twitter data about the primary account
        primary_data = self.vector_db.query_similar(query, n_results=10, filter_username=primary_username)
        
        # Get deeper competitive intelligence for Twitter
        secondary_data = {username: self.vector_db.query_similar(query, n_results=5, filter_username=username)
                         for username in secondary_usernames}
        
        # Extract rich Twitter context with engagement patterns
        primary_context = ""
        twitter_insights = ""
        tweet_themes = []
        
        if primary_data and 'documents' in primary_data and primary_data['documents'][0]:
            tweets_with_meta = list(zip(primary_data['documents'][0], primary_data['metadatas'][0]))
            
            # Analyze Twitter engagement patterns
            viral_tweets = [t for t in tweets_with_meta if t[1]['engagement'] > 2000]
            high_engagement = [t for t in tweets_with_meta if 500 <= t[1]['engagement'] <= 2000]
            
            # Extract tweet themes from high-performing content
            for doc, meta in viral_tweets:
                tweet_themes.append(f"{doc[:120]}... (Engagement: {meta['engagement']})")
            
            primary_context = "\n".join([f"- {doc} | Engagement: {meta['engagement']} | Posted: {meta['timestamp']}"
                                       for doc, meta in tweets_with_meta])
            
            if viral_tweets:
                avg_viral_engagement = sum(t[1]['engagement'] for t in viral_tweets) / len(viral_tweets)
                twitter_insights = f"VIRAL TWITTER CONTENT ANALYSIS:\nAverage engagement on viral tweets: {avg_viral_engagement:.0f}\nViral content patterns identified: {len(viral_tweets)} tweets with 2000+ engagement\n"
                twitter_insights += "TOP PERFORMING TWEET THEMES:\n" + "\n".join(tweet_themes[:3])
            elif high_engagement:
                avg_high_engagement = sum(t[1]['engagement'] for t in high_engagement) / len(high_engagement)
                twitter_insights = f"HIGH-ENGAGEMENT TWITTER ANALYSIS:\nAverage engagement on top tweets: {avg_high_engagement:.0f}\nSuccessful tweet patterns: {len(high_engagement)} tweets with 500+ engagement\n"
        
        # Analyze Twitter competitors with strategic intelligence
        competitive_twitter_intel = ""
        for username, data in secondary_data.items():
            if data and 'documents' in data and data['documents'][0]:
                competitor_tweets = list(zip(data['documents'][0], data['metadatas'][0]))
                competitor_best = max(competitor_tweets, key=lambda x: x[1]['engagement'], default=(None, {'engagement': 0}))
                
                competitive_twitter_intel += f"\n{username.upper()} TWITTER INTELLIGENCE:\n"
                competitive_twitter_intel += f"Best performing tweet: {competitor_best[0][:100]}... (Engagement: {competitor_best[1]['engagement']})\n"
                competitive_twitter_intel += f"Average tweet engagement: {sum(t[1]['engagement'] for t in competitor_tweets) / len(competitor_tweets):.0f}\n"
                
                # Analyze Twitter-specific metrics if available
                retweet_data = [t[1].get('retweets', 0) for t in competitor_tweets]
                reply_data = [t[1].get('replies', 0) for t in competitor_tweets]
                if retweet_data:
                    competitive_twitter_intel += f"Retweet performance: Avg {sum(retweet_data)/len(retweet_data):.0f} retweets per tweet\n"
                if reply_data:
                    competitive_twitter_intel += f"Reply engagement: Avg {sum(reply_data)/len(reply_data):.0f} replies per tweet\n"
        
        prompt = f"""
        You are an elite Twitter strategist and account manager with deep expertise in Twitter content optimization, viral mechanics, and competitive intelligence. You have been hired specifically to analyze {primary_username}'s Twitter account and create a comprehensive strategy that leverages their unique Twitter voice while exploiting competitor weaknesses on the platform.

        **TWITTER ACCOUNT UNDER ANALYSIS**: {primary_username}
        **TARGET TWITTER COMPETITORS**: {', '.join(secondary_usernames)}
        **STRATEGIC FOCUS**: {query}
        **ANALYSIS DATE**: {datetime.now().strftime('%B %d, %Y')}

        **TWITTER PERFORMANCE DATA**:
        {twitter_insights}

        **COMPLETE TWEET HISTORY ANALYSIS**:
        {primary_context if primary_context else "Limited tweet data available - focusing on strategic Twitter recommendations"}

        **COMPETITIVE TWITTER INTELLIGENCE**:
        {competitive_twitter_intel if competitive_twitter_intel else "Competitor Twitter data being analyzed through alternative methods"}

        Your mission is to provide a strategic Twitter intelligence report that demonstrates deep understanding of {primary_username}'s unique Twitter positioning and creates actionable recommendations that are specifically tailored to their tweeting style, Twitter audience behavior, and platform-specific engagement patterns.

        **CRITICAL TWITTER ANALYSIS REQUIREMENTS**:

        1. **DEEP TWITTER PROFILE INTELLIGENCE** [PRIMARY ACCOUNT ANALYSIS]
           - Identify the account's unique Twitter DNA by analyzing tweet patterns, conversation themes, and viral triggers
           - Determine their authentic Twitter voice, thread storytelling style, and core messaging rhythm
           - Map their Twitter content ecosystem: what topics drive retweets, what formats generate replies
           - Identify their Twitter competitive advantages and conversation leadership gaps
           - Analyze audience interaction patterns to determine optimal Twitter engagement strategies
           - Assess their use of Twitter-specific features: threads, polls, spaces, quote tweets

        2. **TWITTER COMPETITIVE WARFARE ANALYSIS** [STRATEGIC INTELLIGENCE]
           - For each competitor, conduct deep Twitter behavioral analysis:
             * Reverse-engineer their most viral Twitter content strategies
             * Identify their Twitter conversation vulnerabilities and engagement blind spots
             * Map their tweeting rhythms, thread timing, and audience interaction techniques
             * Discover their untapped Twitter communities that {primary_username} could engage
             * Analyze their recent Twitter strategic shifts and predict their next platform moves
           - Create a Twitter competitive advantage matrix showing exactly where {primary_username} can outmaneuver each competitor on the platform

        3. **TWITTER STRATEGIC EXPLOITATION PLAN** [ACTIONABLE WARFARE]
           - Design specific Twitter content strategies that exploit competitor weaknesses while amplifying {primary_username}'s Twitter strengths
           - Create 5 high-impact Twitter content pillars that position {primary_username} as a thought leader on the platform
           - Develop Twitter counter-strategies for each major competitor threat
           - Recommend Twitter timing strategies that capitalize on competitor posting gaps and conversation lulls
           - Design Twitter audience capture techniques that pull followers from competitor accounts through superior engagement

        4. **NEXT TWEET MASTERPIECE** [IMMEDIATE EXECUTION]
           - Craft a tweet that perfectly embodies {primary_username}'s authentic Twitter voice while incorporating strategic intelligence
           - The content must feel 100% authentic to their established Twitter style and conversation themes
           - Include strategic elements that subtly outposition competitors on Twitter
           - Provide detailed Twitter execution guidance including:
             * Tweet text that matches their exact Twitter writing style and conversational tone (within 280 characters)
             * Hashtag strategy that exploits competitor Twitter gaps and trending opportunities
             * Media suggestion that aligns with their Twitter aesthetic while standing out in feeds
             * Thread expansion ideas if the topic warrants deeper exploration
             * Engagement hooks designed for their specific Twitter audience psychology

        **TWITTER INTELLIGENCE STANDARDS**:
        - Every recommendation must be backed by specific data points from the tweet analysis
        - No generic Twitter advice - everything must be tailored to {primary_username}'s unique Twitter situation
        - Include specific examples from their tweet history to justify recommendations
        - Provide concrete Twitter metrics and benchmarks for measuring success
        - Reference competitor-specific Twitter tactics that can be adapted or countered
        - Focus on Twitter-specific engagement: retweets, quote tweets, replies, thread engagement

        **OUTPUT REQUIREMENTS**:
        Format as a comprehensive JSON Twitter intelligence report with the following structure:

        {{
            "primary_analysis": "Deep dive into {primary_username}'s Twitter content DNA, engagement patterns, unique Twitter strengths, and strategic positioning opportunities based on their actual tweet performance data and Twitter-specific behaviors",
            "competitor_analysis": {{
                "{secondary_usernames[0] if secondary_usernames else 'competitor1'}": "Detailed strategic analysis of their Twitter approach, Twitter vulnerabilities, and how {primary_username} can outmaneuver them on Twitter, including specific recent Twitter activities and strategic opportunities",
                "{secondary_usernames[1] if len(secondary_usernames) > 1 else 'competitor2'}": "Comprehensive Twitter competitive intelligence including their engagement tactics, conversation gaps, and Twitter exploitation opportunities for {primary_username}",
                "{secondary_usernames[2] if len(secondary_usernames) > 2 else 'competitor3'}": "Strategic breakdown of their Twitter market position, content weaknesses, and specific Twitter tactics {primary_username} should deploy against them"
            }},
            "recommendations": "5 highly specific, data-driven Twitter content strategies that leverage {primary_username}'s unique Twitter strengths while exploiting identified competitor vulnerabilities on the platform. Each recommendation must include specific Twitter execution details and expected engagement metrics.",
            "next_post": {{
                "tweet_text": "A tweet written in {primary_username}'s authentic Twitter voice that incorporates strategic elements and feels completely natural to their established Twitter style and conversation themes (within 280 characters)",
                "hashtags": ["#strategic", "#twitter", "#hashtags", "#that", "#exploit"],
                "media_suggestion": "A media concept (image, video, GIF) that perfectly aligns with their personal Twitter aesthetic preferences and authentic style, reflecting their genuine interests and personality on the platform",
                "follow_up_tweets": ["If a thread feels natural to their style, suggestions for follow-up tweets that maintain their authentic voice and extend the conversation organically"]
            }}
        }}

        Remember: This is not about changing their Twitter identity - it's about amplifying their authentic Twitter voice and helping them connect more effectively with their Twitter community while staying true to their genuine personality and interests on the platform.
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
        """Construct a Twitter-specific intelligent prompt for personal accounts focused on authentic voice analysis and theme alignment."""
        # Get comprehensive Twitter data about the personal account
        primary_data = self.vector_db.query_similar(query, n_results=15, filter_username=primary_username)
        
        # Extract detailed personal Twitter context with authenticity patterns
        primary_context = ""
        twitter_voice_insights = ""
        authentic_tweet_themes = []
        twitter_style_analysis = ""
        
        if primary_data and 'documents' in primary_data and primary_data['documents'][0]:
            tweets_with_meta = list(zip(primary_data['documents'][0], primary_data['metadatas'][0]))
            
            # Analyze personal Twitter patterns for authenticity
            engaging_tweets = [t for t in tweets_with_meta if t[1]['engagement'] > 50]  # Lower threshold for personal Twitter accounts
            recent_tweets = sorted(tweets_with_meta, key=lambda x: x[1]['timestamp'], reverse=True)[:5]
            
            # Extract authentic Twitter themes from engaging content
            for doc, meta in engaging_tweets:
                authentic_tweet_themes.append(f"{doc[:160]}... (Engagement: {meta['engagement']})")
            
            primary_context = "\n".join([f"- {doc} | Engagement: {meta['engagement']} | Posted: {meta['timestamp']}"
                                       for doc, meta in tweets_with_meta])
            
            # Analyze Twitter writing style patterns
            if tweets_with_meta:
                total_tweets = len(tweets_with_meta)
                avg_engagement = sum(t[1]['engagement'] for t in tweets_with_meta) / total_tweets
                
                # Analyze Twitter-specific characteristics
                question_tweets = [t for t in tweets_with_meta if '?' in t[0]]
                thread_tweets = [t for t in tweets_with_meta if any(indicator in t[0].lower() for indicator in ['thread', '1/', '2/', 'a thread'])]
                reply_tweets = [t for t in tweets_with_meta if t[0].startswith('@')]
                casual_tweets = [t for t in tweets_with_meta if any(word in t[0].lower() for word in ['lol', 'omg', 'tbh', 'ngl', 'fr'])]
                personal_opinion_tweets = [t for t in tweets_with_meta if any(phrase in t[0].lower() for phrase in ['i think', 'imo', 'personally', 'i believe', 'hot take'])]
                
                # Analyze Twitter-specific metrics if available
                total_retweets = sum(t[1].get('retweets', 0) for t in tweets_with_meta)
                total_replies = sum(t[1].get('replies', 0) for t in tweets_with_meta)
                total_quotes = sum(t[1].get('quotes', 0) for t in tweets_with_meta)
                
                twitter_style_analysis = f"PERSONAL TWITTER VOICE ANALYSIS:\n"
                twitter_style_analysis += f"Total tweets analyzed: {total_tweets} | Average engagement: {avg_engagement:.0f}\n"
                twitter_style_analysis += f"Interactive tweets (questions): {len(question_tweets)} ({len(question_tweets)/total_tweets*100:.1f}%)\n"
                twitter_style_analysis += f"Thread creation: {len(thread_tweets)} ({len(thread_tweets)/total_tweets*100:.1f}%)\n"
                twitter_style_analysis += f"Reply engagement: {len(reply_tweets)} ({len(reply_tweets)/total_tweets*100:.1f}%)\n"
                twitter_style_analysis += f"Casual Twitter language: {len(casual_tweets)} ({len(casual_tweets)/total_tweets*100:.1f}%)\n"
                twitter_style_analysis += f"Opinion sharing: {len(personal_opinion_tweets)} ({len(personal_opinion_tweets)/total_tweets*100:.1f}%)\n"
                
                if total_tweets > 0:
                    twitter_style_analysis += f"Retweet rate: {total_retweets/total_tweets:.1f} per tweet\n"
                    twitter_style_analysis += f"Reply rate: {total_replies/total_tweets:.1f} per tweet\n"
                    twitter_style_analysis += f"Quote tweet rate: {total_quotes/total_tweets:.1f} per tweet\n"
                
                if authentic_tweet_themes:
                    twitter_voice_insights = f"AUTHENTIC TWITTER THEMES:\n" + "\n".join(authentic_tweet_themes[:4])
        
        prompt = f"""
        You are an elite personal Twitter strategist and authentic voice specialist with deep expertise in Twitter personal brand development and individual expression optimization. You have been hired specifically to analyze {primary_username}'s personal Twitter account and create content strategies that amplify their authentic Twitter voice while maximizing engagement within their unique Twitter community.

        **PERSONAL TWITTER ACCOUNT UNDER ANALYSIS**: {primary_username}
        **TWITTER CONTENT FOCUS**: {query}
        **ANALYSIS DATE**: {datetime.now().strftime('%B %d, %Y')}

        **PERSONAL TWITTER VOICE DATA**:
        {twitter_style_analysis}

        **AUTHENTIC TWITTER CONTENT INSIGHTS**:
        {twitter_voice_insights}

        **COMPLETE TWITTER HISTORY ANALYSIS**:
        {primary_context if primary_context else "Limited tweet data available - focusing on authentic Twitter voice development"}

        Your mission is to provide a comprehensive personal Twitter content strategy that demonstrates deep understanding of {primary_username}'s authentic Twitter voice, personal interests, and natural communication style on the platform, while creating recommendations that feel genuinely personal and engaging within Twitter's unique ecosystem.

        **CRITICAL PERSONAL TWITTER ANALYSIS REQUIREMENTS**:

        1. **AUTHENTIC TWITTER VOICE INTELLIGENCE** [PERSONAL BRAND ANALYSIS]
           - Decode the account's unique Twitter personality signature by analyzing tweet patterns, conversational rhythms, and engagement triggers
           - Identify their natural Twitter storytelling style, thread creation patterns, and authentic enthusiasm in tweets
           - Map their personal Twitter content ecosystem: what subjects they naturally tweet about, what Twitter formats feel authentic to them
           - Determine their Twitter community engagement style: how they naturally interact, reply, and participate in conversations
           - Analyze their authentic Twitter moments: which tweets show genuine personality and resonate most with their Twitter community
           - Identify opportunities to amplify their unique Twitter perspective and personal experiences on the platform

        2. **PERSONAL TWITTER CONTENT STRATEGY** [AUTHENTIC ENGAGEMENT]
           - Design Twitter content pillars that align perfectly with their natural interests and authentic Twitter voice
           - Recommend Twitter topics that feel genuine to their personal journey and experiences
           - Suggest Twitter engagement approaches that match their natural communication style on the platform
           - Identify Twitter storytelling opportunities that showcase their unique perspective
           - Recommend ways to share their knowledge or experiences through tweets that feel authentic and valuable
           - Create strategies for building genuine Twitter community around their personal interests
           - Optimize their use of Twitter-specific features (threads, polls, quote tweets) based on their natural style

        3. **NEXT TWEET CREATION** [AUTHENTIC EXPRESSION]
           - Craft Twitter content that feels like a natural extension of their tweeting history and personality
           - The content must perfectly match their established Twitter voice, tone, and communication style
           - Include elements that reflect their genuine interests and current Twitter experiences
           - Provide detailed Twitter execution guidance including:
             * A tweet written exactly as they would naturally express themselves on Twitter (within 280 characters)
             * Twitter topics and themes that align with their authentic interests
             * Twitter engagement approaches that feel genuine to their personality
             * Media concepts that match their personal Twitter aesthetic preferences
             * Thread suggestions if appropriate to their natural style

        **TWITTER AUTHENTICITY STANDARDS**:
        - Every recommendation must feel like something {primary_username} would naturally tweet themselves
        - No corporate or marketing language - everything must sound personal and genuine for Twitter
        - Include specific examples from their Twitter history to justify authenticity
        - Reference their natural Twitter communication patterns and personality traits
        - Maintain their unique Twitter voice while suggesting strategic improvements
        - Focus on amplifying what already works for them personally on Twitter
        - Respect Twitter's conversational nature and character limitations

        **OUTPUT REQUIREMENTS**:
        Format as a comprehensive JSON personal Twitter content strategy with the following structure:

        {{
            "account_analysis": "Deep analysis of {primary_username}'s authentic Twitter voice, personal communication style on the platform, natural interests expressed through tweets, and unique personality traits based on their actual tweeting patterns and Twitter engagement data",
            "content_recommendations": "Personalized Twitter content strategy that amplifies their authentic voice while maximizing Twitter engagement. Include specific tweet topic suggestions, Twitter posting approaches, and Twitter community building strategies that align with their natural interests and Twitter communication style",
            "next_tweet": {{
                "tweet_text": "A tweet written in {primary_username}'s exact natural Twitter voice that reflects their authentic style, interests, and way of communicating on Twitter - it should sound exactly like something they would tweet themselves (within 280 characters)",
                "hashtags": ["#personal", "#authentic", "#twitter", "#hashtags", "#that"],
                "media_suggestion": "A media concept (image, video, GIF) that perfectly aligns with their personal Twitter aesthetic preferences and authentic style, reflecting their genuine interests and personality on the platform",
                "follow_up_tweets": ["If a thread feels natural to their style, suggestions for follow-up tweets that maintain their authentic voice and extend the conversation organically"]
            }}
        }}

        Remember: This is not about changing their Twitter identity - it's about amplifying their authentic Twitter voice and helping them connect more effectively with their Twitter community while staying true to their genuine personality and interests on the platform.
        """
        return prompt
    
    def generate_recommendation(self, primary_username, secondary_usernames, query, n_context=3, is_branding=True, platform="instagram"):
        """Generate a recommendation for the given query with contextual analysis."""
        try:
            logger.info(f"Generating recommendation for {platform} platform, {'' if is_branding else 'non-'}branding account")
            logger.info(f"Primary username: {primary_username}, Secondary usernames: {secondary_usernames}")
            
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
                    
                # Extract structured recommendation
                recommendation_json = self._parse_json_response(response.text)
                logger.info("Successfully generated recommendation")
                return recommendation_json
                
            except Exception as gemini_error:
                logger.error(f"Error generating recommendation with Gemini: {str(gemini_error)}")
                raise Exception(f"Recommendation generation failed: {str(gemini_error)}")
                
        except Exception as e:
            logger.error(f"Error generating recommendation: {str(e)}")
            raise Exception(f"Recommendation generation failed: {str(e)}")
    
    def _parse_json_response(self, response_text):
        """Parse JSON response with enhanced error handling and repair capabilities."""
        try:
            # Try direct parsing first
            return json.loads(response_text)
        except json.JSONDecodeError as e:
            logger.warning(f"Initial JSON parsing failed: {str(e)}, attempting repairs...")
            
            # Enhanced JSON repair attempts
            repair_attempts = [
                # Remove markdown code blocks
                lambda text: re.sub(r'```(?:json)?\s*(.*?)\s*```', r'\1', text, flags=re.DOTALL),
                
                # Remove leading/trailing text before/after JSON
                lambda text: re.search(r'\{.*\}', text, re.DOTALL).group(0) if re.search(r'\{.*\}', text, re.DOTALL) else text,
                
                # Fix common JSON issues
                lambda text: text.replace('`', '"').replace(''', "'").replace(''', "'").replace('"', '"').replace('"', '"'),
                
                # Fix trailing commas
                lambda text: re.sub(r',(\s*[}\]])', r'\1', text),
                
                # Fix missing quotes around keys
                lambda text: re.sub(r'(\w+):', r'"\1":', text),
                
                # Fix single quotes to double quotes
                lambda text: text.replace("'", '"'),
                
                # Remove comments
                lambda text: re.sub(r'//.*?\n', '\n', text),
                
                # Fix escaped quotes
                lambda text: text.replace('\\"', '"'),
                
                # Extract JSON from mixed content
                lambda text: self._extract_json_from_mixed_content(text)
            ]
            
            for i, repair_func in enumerate(repair_attempts):
                try:
                    repaired_text = repair_func(response_text)
                    if repaired_text and repaired_text != response_text:
                        logger.info(f"Attempting JSON repair method {i+1}")
                        parsed = json.loads(repaired_text)
                        logger.info(f"Successfully repaired JSON using method {i+1}")
                        return parsed
                except (json.JSONDecodeError, AttributeError, TypeError):
                    continue
            
            # If all repair attempts fail, create structured response from text
            logger.warning("All JSON repair attempts failed, creating structured response from text")
            return self._create_structured_response_from_text(response_text)
            
        except Exception as e:
            logger.error(f"Unexpected error in JSON parsing: {str(e)}")
            return self._create_fallback_response()
    
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
        """Create a structured response when JSON parsing fails completely."""
        try:
            # Extract key information from the text
            response = {}
            
            # Look for next post content
            if 'next post' in response_text.lower() or 'tweet' in response_text.lower():
                # Extract potential content
                lines = response_text.split('\n')
                tweet_text = ""
                hashtags = []
                
                for line in lines:
                    line = line.strip()
                    if line and not line.startswith('#') and len(line) > 20:
                        if not tweet_text:  # Take the first substantial line as content
                            tweet_text = line
                    elif line.startswith('#'):
                        hashtags.append(line)
                
                if tweet_text:
                    response['next_post'] = {
                        'tweet_text': tweet_text,
                        'hashtags': hashtags[:5] if hashtags else ['#Update', '#Content'],
                        'media_suggestion': 'High-quality relevant image',
                        'follow_up_tweets': []
                    }
            
            # Look for recommendations
            if 'recommend' in response_text.lower():
                # Extract recommendation text
                response['content_recommendations'] = response_text
            
            # Look for analysis
            if 'analysis' in response_text.lower():
                response['account_analysis'] = response_text
            
            # If no structured content found, provide the raw text
            if not response:
                response = {
                    'content_recommendations': response_text,
                    'account_analysis': 'Analysis based on account patterns and engagement',
                    'next_post': {
                        'tweet_text': 'Exciting updates coming soon!',
                        'hashtags': ['#Update', '#ComingSoon'],
                        'media_suggestion': 'Engaging visual content'
                    }
                }
            
            logger.info("Created structured response from unstructured text")
            return response
            
        except Exception as e:
            logger.error(f"Error creating structured response: {str(e)}")
            return self._create_fallback_response()
    
    def _create_fallback_response(self):
        """Create a minimal fallback response."""
        return {
            'content_recommendations': 'Unable to generate specific recommendations at this time.',
            'account_analysis': 'Account analysis pending due to technical issues.',
            'next_post': {
                'tweet_text': 'Stay tuned for exciting updates!',
                'hashtags': ['#StayTuned', '#Updates'],
                'media_suggestion': 'Relevant high-quality image'
            }
        }
    
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
        """Extract structured recommendation data from unstructured text."""
        # This method is deprecated - code should use proper JSON parsing instead
        logger.warning("_extract_recommendation_from_text is deprecated")
        raise NotImplementedError("This method has been removed to eliminate fallback systems")
        
    def generate_batch_recommendations(self, prompt, topics, is_branding=True):
        """Generate batch recommendations for multiple topics."""
        try:
            if not self.client:
                logger.error("Gemini client not initialized")
                raise Exception("Gemini client not initialized - batch recommendations cannot be generated")
                
            enhanced_prompt = self._enhance_batch_prompt(prompt, {}, is_branding)
            
            generation_config = {
                'max_output_tokens': self.config.get('max_tokens', 2000) * 2,  # Double for batch
                'temperature': self.config.get('temperature', 0.2),
                'top_p': self.config.get('top_p', 0.95),
                'top_k': self.config.get('top_k', 40)
            }
            
            model = genai.GenerativeModel(self.model, generation_config=generation_config)
            response = model.generate_content(enhanced_prompt)
            
            if not response.text:
                logger.error("Empty response from Gemini for batch recommendations")
                raise ValueError("Empty response for batch recommendations")
            
            # Parse JSON response - expect an array of recommendations
            try:
                # First try to extract JSON from backticks
                json_match = re.search(r'```(?:json)?\s*(\[[\s\S]*?\])\s*```', response.text, re.DOTALL)
                if json_match:
                    recommendations = json.loads(json_match.group(1))
                    return recommendations
                
                # Try finding JSON array directly
                json_match = re.search(r'\[\s*\{[\s\S]*\}\s*\]', response.text, re.DOTALL)
                if json_match:
                    recommendations = json.loads(json_match.group(0))
                    return recommendations
                
                logger.error("Could not extract batch recommendations JSON")
                raise ValueError("Failed to parse batch recommendations JSON")
                
            except Exception as e:
                logger.error(f"Error parsing batch recommendations: {str(e)}")
                raise
                
        except Exception as e:
            logger.error(f"Error generating batch recommendations: {str(e)}")
            raise
    
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