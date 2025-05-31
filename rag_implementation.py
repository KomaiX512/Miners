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
🎯 ACCOUNT MANAGEMENT BRIEFING - EXECUTIVE LEVEL 🎯

ACCOUNT UNDER MANAGEMENT: @{primary_username}
COMPETITIVE LANDSCAPE: {', '.join(secondary_usernames)}
MISSION: Deliver executive-level account management insights with actionable intelligence
ANALYSIS DATE: {datetime.now().strftime('%B %d, %Y')}

=== 📊 YOUR ACCOUNT'S RECENT PERFORMANCE INTELLIGENCE ===
        {engagement_insights}

=== 📋 COMPLETE CONTENT ANALYSIS ===
        {primary_context if primary_context else "Limited post data available - focusing on strategic recommendations"}

=== 🔍 COMPETITIVE LANDSCAPE ANALYSIS ===
        {competitive_intel if competitive_intel else "Competitor data being analyzed through alternative methods"}

=== 🎯 EXECUTIVE ACCOUNT MANAGER PROTOCOL ===

You are the ELITE ACCOUNT MANAGER for @{primary_username}. You have complete access to all performance data, competitor intelligence, and market analytics. Your role is to provide executive-level strategic guidance with the following deliverables:

**MODULE 1: 📈 STRATEGIC RECOMMENDATIONS**
Provide a comprehensive account performance briefing including:
• 🎯 **Recent Activity Analysis**: Detail @{primary_username}'s latest engagement patterns, top-performing content themes, and audience response metrics
• 📊 **Performance Dashboard**: Include specific engagement statistics, growth trajectories, and content performance indicators  
• 🔥 **Competitor Activity Intel**: Analyze competitors' recent successful campaigns, engagement spikes, and strategic moves with specific examples
• ⚡ **Tactical Advantage Strategies**: Provide 3-5 specific actions to outperform competitors based on identified gaps and opportunities
• 🚀 **Future Content Roadmap**: Strategic recommendations for upcoming content that will maximize engagement and market positioning

**MODULE 2: 🔍 COMPETITIVE INTELLIGENCE REPORT**
Deliver detailed competitor analysis featuring:
• 📊 **Competitor Performance Metrics**: Specific engagement data, successful post examples, and performance patterns for each competitor
• 🎯 **Content Strategy Analysis**: Break down competitors' winning content formulas with specific posts, engagement numbers, and success factors
• ⚖️ **Head-to-Head Comparison**: Direct performance comparisons between @{primary_username} and each competitor with statistical backing
• 🔥 **Competitive Advantages**: Identify specific areas where @{primary_username} can outperform based on competitor weaknesses
• 💡 **Market Opportunity Map**: Strategic gaps in competitor coverage that @{primary_username} can exploit

**MODULE 3: 🎨 NEXT POST STRATEGIC CREATION**
Generate the optimal next post with:
• ✨ **Theme-Aligned Content**: Perfect alignment with @{primary_username}'s successful content patterns and brand voice
• 📝 **Engagement-Optimized Caption**: Crafted based on analysis of @{primary_username}'s highest-performing posts
• 🏷️ **Strategic Hashtag Selection**: Research-based hashtag strategy that matches @{primary_username}'s successful patterns
• 🎨 **Creative Visual Direction**: Detailed image prompt for maximum visual impact and brand consistency
• 🎯 **Engagement Catalyst**: Call-to-action designed to maximize audience interaction based on performance data

=== 📋 EXECUTIVE REPORTING FORMAT ===

Structure your analysis using this EXACT format with engaging presentation:

{{
    "primary_analysis": "🎯 **@{primary_username} ACCOUNT PERFORMANCE ANALYSIS**\n\n📊 **Recent Activity Dashboard:**\n• [Include specific metrics and performance data from actual posts]\n• [Engagement trends and patterns analysis]\n• [Top-performing content theme identification]\n\n🔥 **Content Success Patterns:**\n• [List successful content themes with exact engagement data]\n• [Audience response analysis with metrics]\n• [Growth trajectory insights with statistics]\n\n💡 **Strategic Positioning:**\n• [Account's unique competitive advantages]\n• [Market positioning opportunities]\n• [Brand voice and aesthetic consistency analysis]",
    
            "competitor_analysis": {{
        "{secondary_usernames[0] if secondary_usernames else 'competitor1'}": "🔍 **{secondary_usernames[0].upper() if secondary_usernames else 'COMPETITOR1'} INTELLIGENCE REPORT**\n\n📊 **Performance Metrics:**\n• **Average Engagement**: [Specific number based on scraped data]\n• **Top Performing Post**: [Quote specific post with engagement number]\n• **Success Formula**: [Analyze why their content works]\n• **Posting Frequency**: [Pattern analysis]\n\n🎯 **Content Strategy Breakdown:**\n• [Their winning content themes with examples]\n• [Visual style and aesthetic analysis]\n• [Audience engagement tactics they use]\n\n⚖️ **Competitive Comparison:**\n• [Direct performance vs @{primary_username}]\n• [Areas where @{primary_username} can outperform]\n• [Specific vulnerabilities to exploit]",
        
        "{secondary_usernames[1] if len(secondary_usernames) > 1 else 'competitor2'}": "🔍 **{secondary_usernames[1].upper() if len(secondary_usernames) > 1 else 'COMPETITOR2'} INTELLIGENCE REPORT**\n\n📊 **Performance Analysis:**\n• [Detailed performance metrics based on scraped data]\n• [Successful content examples with engagement numbers]\n• [Strategic positioning in market]\n\n🎯 **Strategic Intelligence:**\n• [Content approach analysis]\n• [Audience targeting strategy]\n• [Opportunities for @{primary_username} to outmaneuver]",
        
        "{secondary_usernames[2] if len(secondary_usernames) > 2 else 'competitor3'}": "🔍 **{secondary_usernames[2].upper() if len(secondary_usernames) > 2 else 'COMPETITOR3'} INTELLIGENCE REPORT**\n\n📈 **Market Position Analysis:**\n• [Performance assessment based on actual data]\n• [Content strategy evaluation]\n• [Specific tactics @{primary_username} should deploy to dominate this competitor]"
    }},
    
    "recommendations": "🚀 **STRATEGIC ACTION PLAN FOR @{primary_username}**\n\n⚡ **IMMEDIATE PRIORITY ACTIONS:**\n• 🎯 **[Action 1]**: [Specific tactical recommendation with expected engagement boost and timeline]\n• 📊 **[Action 2]**: [Data-driven content strategy based on competitor analysis]\n• 🔥 **[Action 3]**: [Engagement optimization tactic based on successful patterns]\n• 💡 **[Action 4]**: [Market positioning move to exploit competitor weaknesses]\n• 🚀 **[Action 5]**: [Future content roadmap for sustained growth]\n\n📈 **PERFORMANCE OPTIMIZATION:**\n• [Specific metrics to track and improve]\n• [Content themes to prioritize based on data]\n• [Posting timing and frequency recommendations]\n\n🎯 **COMPETITIVE ADVANTAGE EXECUTION:**\n• [Strategies to outperform each identified competitor]\n• [Unique positioning opportunities to capture]\n• [Market gaps to fill for maximum impact]",
    
            "next_post": {{
        "caption": "[Craft an engaging caption that perfectly matches @{primary_username}'s successful style, incorporates trending elements, and targets competitor weak spots while maintaining authentic brand voice]",
        "hashtags": ["#strategic", "#hashtags", "#based", "#on", "#analysis"],
        "call_to_action": "[Engagement prompt specifically designed for @{primary_username}'s audience based on their highest-performing posts and audience response patterns]",
        "visual_prompt": "🎨 **CREATIVE VISUAL DIRECTION**: [Detailed, innovative image prompt for maximum visual impact. Include: specific composition style, color palette, visual elements, lighting, mood, props, and design details that align perfectly with @{primary_username}'s successful aesthetic patterns. Make it comprehensive enough for an AI image generator to create stunning, on-brand visuals that will outperform competitor content.]"
    }}
}}

=== 🎯 ACCOUNT MANAGER EXCELLENCE STANDARDS ===

✅ **INTELLIGENCE REQUIREMENTS:**
- Every insight backed by specific performance data from scraped content analysis
- Competitor analysis includes exact engagement numbers and successful post examples
- All recommendations target measurable engagement improvements
- Strategic positioning based on real competitive gaps identified in data

✅ **PROFESSIONAL PRESENTATION:**
- Use emojis strategically for visual engagement and information hierarchy
- Implement bullet points and structured formatting for executive consumption
- Include specific statistics, metrics, and data points throughout analysis
- Maintain highly professional tone while being engaging and actionable

✅ **STRATEGIC DEPTH:**
- Provide actionable intelligence that @{primary_username} can implement immediately
- Connect all recommendations to competitive advantages and market opportunities
- Base all tactical suggestions on proven performance patterns from actual data
- Deliver insights demonstrating deep understanding of @{primary_username}'s brand, audience, and market position

EXECUTE ELITE ACCOUNT MANAGEMENT ANALYSIS:
        """
        return prompt
    
    def _construct_twitter_enhanced_prompt(self, primary_username, secondary_usernames, query):
        """Construct a Twitter-specific intelligent prompt for branding accounts with REAL competitor intelligence."""
        # Get comprehensive Twitter data about the primary account
        primary_data = self.vector_db.query_similar(query, n_results=15, filter_username=primary_username)
        
        # 🔥 CRITICAL: Get REAL competitor data from vector database for each competitor
        individual_competitor_intel = {}
        competitor_performance_data = {}
        
        for competitor_username in secondary_usernames[:3]:  # Analyze top 3 competitors max
            competitor_data = self.vector_db.query_similar(query, n_results=10, filter_username=competitor_username)
            individual_competitor_intel[competitor_username] = competitor_data
            
            # 🔥 ENHANCED: Calculate real competitor performance metrics
            if competitor_data and 'documents' in competitor_data and competitor_data['documents'][0]:
                competitor_posts = list(zip(competitor_data['documents'][0], competitor_data['metadatas'][0]))
                
                # Real performance analysis
                engagements = [meta['engagement'] for doc, meta in competitor_posts if 'engagement' in meta]
                total_engagement = sum(engagements) if engagements else 0
                avg_engagement = total_engagement / len(engagements) if engagements else 0
                max_engagement = max(engagements) if engagements else 0
                
                # Content theme analysis
                top_content = sorted(competitor_posts, key=lambda x: x[1].get('engagement', 0), reverse=True)[:3]
                content_themes = [doc[:80] + "..." for doc, meta in top_content]
                
                competitor_performance_data[competitor_username] = {
                    'avg_engagement': avg_engagement,
                    'max_engagement': max_engagement,
                    'total_posts': len(competitor_posts),
                    'top_content': content_themes,
                    'performance_level': 'HIGH' if avg_engagement > 1000 else 'MEDIUM' if avg_engagement > 100 else 'LOW'
                }
                
                logger.info(f"🔥 REAL COMPETITOR DATA: {competitor_username} - Avg: {avg_engagement:.0f}, Posts: {len(competitor_posts)}")
        
        # Extract comprehensive engagement intelligence for PRIMARY account
        primary_context = ""
        viral_intelligence = ""
        engagement_patterns = []
        strategic_themes = []
        viral_tweets = []
        high_engagement = []
        avg_top_engagement = 0
        
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
            else:
                viral_intelligence = f"🎯 PRIMARY ACCOUNT INTELLIGENCE: {primary_username}\n"
                viral_intelligence += f"• Total tweets analyzed: {len(tweets_with_meta)}\n"
                viral_intelligence += f"• No viral content (>1000 engagement) identified in current dataset\n"
                viral_intelligence += f"• Analysis based on available content patterns\n"
        
        # 🔥 ENHANCED: Build DETAILED competitive intelligence with REAL scraped data
        detailed_competitor_intel = ""
        competitive_advantage_analysis = ""
        
        if competitor_performance_data:
            detailed_competitor_intel += f"\n🔥 REAL COMPETITOR INTELLIGENCE (SCRAPED DATA ANALYSIS):\n"
        
            for competitor_username, perf_data in competitor_performance_data.items():
                detailed_competitor_intel += f"\n📊 {competitor_username.upper()} - PERFORMANCE BREAKDOWN:\n"
                detailed_competitor_intel += f"• Performance Level: {perf_data['performance_level']}\n"
                detailed_competitor_intel += f"• Average Engagement: {perf_data['avg_engagement']:.0f}\n"
                detailed_competitor_intel += f"• Peak Engagement: {perf_data['max_engagement']}\n"
                detailed_competitor_intel += f"• Content Volume: {perf_data['total_posts']} posts analyzed\n"
                
                if perf_data['top_content']:
                    detailed_competitor_intel += f"• TOP PERFORMING CONTENT:\n"
                    for i, content in enumerate(perf_data['top_content'], 1):
                        detailed_competitor_intel += f"  {i}. {content}\n"
                
                # Strategic insights based on real data
                if perf_data['avg_engagement'] > 1000:
                    detailed_competitor_intel += f"• THREAT LEVEL: HIGH - Strong engagement performance\n"
                    detailed_competitor_intel += f"• VULNERABILITY: May be over-reliant on high-engagement content themes\n"
                elif perf_data['avg_engagement'] < 100:
                    detailed_competitor_intel += f"• OPPORTUNITY: Weak engagement - easy to outperform\n"
                    detailed_competitor_intel += f"• STRATEGY: Target their audience with superior content\n"
            
            # Competitive advantage analysis
            primary_avg = avg_top_engagement if viral_tweets or high_engagement else 0
            competitive_advantage_analysis = f"\n🎯 COMPETITIVE ADVANTAGE ANALYSIS:\n"
            competitive_advantage_analysis += f"• {primary_username} average: {primary_avg:.0f}\n"
            
            for comp_name, comp_data in competitor_performance_data.items():
                advantage = primary_avg - comp_data['avg_engagement']
                if advantage > 0:
                    competitive_advantage_analysis += f"• ADVANTAGE vs {comp_name}: +{advantage:.0f} engagement\n"
                else:
                    competitive_advantage_analysis += f"• DEFICIT vs {comp_name}: {advantage:.0f} engagement (IMPROVE NEEDED)\n"
            
            detailed_competitor_intel = f"\n🔍 COMPETITIVE SURVEILLANCE: {', '.join(secondary_usernames)}\n"
            detailed_competitor_intel += "• Real-time data collection and analysis in progress\n"
            detailed_competitor_intel += "• Strategic positioning analysis framework deployed\n"
            detailed_competitor_intel += "• Market gap identification protocol active\n"
        
        prompt = f"""
🎯 ACCOUNT MANAGEMENT BRIEFING - EXECUTIVE LEVEL 🎯

ACCOUNT UNDER MANAGEMENT: @{primary_username}
COMPETITIVE LANDSCAPE: {', '.join(secondary_usernames)}
MISSION: Deliver executive-level account management insights with actionable intelligence

=== 📊 YOUR ACCOUNT'S RECENT PERFORMANCE INTELLIGENCE ===
{viral_intelligence}

=== 🔍 COMPETITIVE LANDSCAPE ANALYSIS ===
{detailed_competitor_intel}

=== ⚖️ STRATEGIC POSITIONING MATRIX ===
{competitive_advantage_analysis}

=== 🎯 EXECUTIVE ACCOUNT MANAGER PROTOCOL ===

You are the ELITE ACCOUNT MANAGER for @{primary_username}. You have complete access to all performance data, competitor intelligence, and market analytics. Your role is to provide executive-level strategic guidance with the following deliverables:

**MODULE 1: 📈 STRATEGIC RECOMMENDATIONS**
Provide a comprehensive account performance briefing including:
• 🎯 **Recent Activity Analysis**: Detail @{primary_username}'s latest engagement patterns, top-performing content themes, and audience response metrics
• 📊 **Performance Dashboard**: Include specific engagement statistics, growth trajectories, and content performance indicators
• 🔥 **Competitor Activity Intel**: Analyze competitors' recent successful campaigns, engagement spikes, and strategic moves with specific examples
• ⚡ **Tactical Advantage Strategies**: Provide 3-5 specific actions to outperform competitors based on identified gaps and opportunities
• 🚀 **Future Content Roadmap**: Strategic recommendations for upcoming content that will maximize engagement and market positioning

**MODULE 2: 🔍 COMPETITIVE INTELLIGENCE REPORT**
Deliver detailed competitor analysis featuring:
• 📊 **Competitor Performance Metrics**: Specific engagement data, successful post examples, and performance patterns for each competitor
• 🎯 **Content Strategy Analysis**: Break down competitors' winning content formulas with specific posts, engagement numbers, and success factors
• ⚖️ **Head-to-Head Comparison**: Direct performance comparisons between @{primary_username} and each competitor with statistical backing
• 🔥 **Competitive Advantages**: Identify specific areas where @{primary_username} can outperform based on competitor weaknesses
• 💡 **Market Opportunity Map**: Strategic gaps in competitor coverage that @{primary_username} can exploit

**MODULE 3: 🎨 NEXT POST STRATEGIC CREATION**
Generate the optimal next post with:
• ✨ **Theme-Aligned Content**: Perfect alignment with @{primary_username}'s successful content patterns and brand voice
• 📝 **Engagement-Optimized Caption**: Crafted based on analysis of @{primary_username}'s highest-performing posts
• 🏷️ **Strategic Hashtag Selection**: Research-based hashtag strategy that matches @{primary_username}'s successful patterns
• 🎨 **Creative Visual Direction**: Detailed image prompt for maximum visual impact and brand consistency
• 🎯 **Engagement Catalyst**: Call-to-action designed to maximize audience interaction based on performance data

=== 📋 EXECUTIVE REPORTING FORMAT ===

Structure your analysis using this EXACT format with engaging presentation:

{{
    "competitive_intelligence": {{
        "account_dna": "🎯 **@{primary_username} ACCOUNT PERFORMANCE ANALYSIS**\n\n📊 **Recent Activity Dashboard:**\n• [Include specific metrics and performance data]\n• [Engagement trends and patterns]\n• [Top-performing content analysis]\n\n🔥 **Content Success Patterns:**\n• [List successful content themes with engagement data]\n• [Audience response analysis]\n• [Growth trajectory insights]",
        
        "market_surveillance": "🔍 **COMPETITIVE LANDSCAPE INTELLIGENCE**\n\n📈 **Market Overview:**\n• [Overall competitive performance summary]\n• [Market positioning analysis]\n• [Opportunity identification]\n\n⚡ **Competitor Performance Matrix:**\n{', '.join([f'• **{name}**: [Avg engagement, performance level, strategic position]' for name in secondary_usernames]) if secondary_usernames else '• Analysis across identified competitive accounts'}\n\n🎯 **Strategic Market Gaps:**\n• [Specific opportunities for @{primary_username} to dominate]",
        
        "engagement_warfare": "⚔️ **COMPETITIVE ENGAGEMENT STRATEGY**\n\n🚀 **Tactical Advantages:**\n• [Specific strategies to outperform competitors]\n• [Content approaches that exploit competitor weaknesses]\n• [Timing and positioning recommendations]\n\n📊 **Performance Optimization:**\n• [Data-driven recommendations for engagement growth]\n• [Strategic content themes for maximum impact]\n• [Audience targeting refinements]"
    }},
    
    "threat_assessment": {{
        "competitor_analysis": "🎯 **INDIVIDUAL COMPETITOR BREAKDOWN**\n\n{chr(10).join([f'🔍 **{name.upper()} INTELLIGENCE:**' + chr(10) + f'• **Performance Level**: [HIGH/MEDIUM/LOW based on data]' + chr(10) + f'• **Recent Success**: [Specific high-performing post with engagement numbers]' + chr(10) + f'• **Success Factors**: [Why their content succeeded - specific analysis]' + chr(10) + f'• **Vulnerability**: [Weakness @{primary_username} can exploit]' + chr(10) + f'• **Counter-Strategy**: [Specific approach to outperform them]' + chr(10) for name in secondary_usernames[:3]]) if secondary_usernames else '• **Comprehensive competitor analysis across identified accounts**'}",
        
        "vulnerability_map": "🎯 **COMPETITIVE VULNERABILITY ANALYSIS**\n\n💡 **Exploitable Weaknesses:**\n• [Specific competitor content gaps]\n• [Timing vulnerabilities in posting schedules]\n• [Audience engagement blind spots]\n\n🚀 **Strategic Advantages:**\n• [Areas where @{primary_username} already outperforms]\n• [Unique positioning opportunities]\n• [Content themes competitors are missing]",
        
        "market_opportunities": "🌟 **STRATEGIC MARKET OPPORTUNITIES**\n\n🎯 **High-Impact Opportunities:**\n• [Specific content themes with growth potential]\n• [Underexploited audience segments]\n• [Emerging trends @{primary_username} can lead]\n\n📈 **Growth Accelerators:**\n• [Tactical moves for rapid engagement growth]\n• [Strategic partnerships or collaboration opportunities]\n• [Content formats with untapped potential]"
    }},
    
    "tactical_recommendations": [
        "🚀 **IMMEDIATE ACTION ITEM**: [Specific tactical recommendation with expected outcome and timeline]",
        "📊 **CONTENT STRATEGY**: [Strategic content approach based on competitor analysis and performance data]", 
        "🎯 **ENGAGEMENT OPTIMIZATION**: [Specific tactics to boost engagement based on successful pattern analysis]"
    ],
    
    "next_post_prediction": {{
        "tweet_text": "[Craft a tweet that perfectly embodies @{primary_username}'s successful content style, incorporates trending elements, and targets competitor weak spots - maximum 280 characters]",
        "hashtags": ["#strategic", "#hashtags", "#based", "#on", "#analysis"],
        "call_to_action": "[Engagement prompt designed specifically for @{primary_username}'s audience based on performance data]",
        "image_prompt": "🎨 **CREATIVE VISUAL DIRECTION**: [Detailed, creative image prompt for maximum visual impact. Include: composition style, color scheme, visual elements, mood, and specific design details that align with @{primary_username}'s brand and successful post patterns. Make it detailed enough for an AI image generator to create stunning visuals.]"
    }}
}}

=== 🎯 ACCOUNT MANAGER EXCELLENCE STANDARDS ===

✅ **INTELLIGENCE REQUIREMENTS:**
- Every insight backed by specific performance data from scraped content analysis
- Competitor analysis includes exact engagement numbers and successful post examples  
- All recommendations target measurable engagement improvements
- Strategic positioning based on real competitive gaps identified in data

✅ **PROFESSIONAL PRESENTATION:**
- Use emojis strategically for visual engagement and hierarchy
- Implement bullet points and formatting for easy executive consumption
- Include specific statistics and metrics throughout analysis
- Maintain professional tone while being highly engaging and informative

✅ **STRATEGIC DEPTH:**
- Provide actionable intelligence that @{primary_username} can implement immediately
- Connect all recommendations to competitive advantages and market opportunities
- Base all tactical suggestions on proven performance patterns from the data
- Deliver insights that demonstrate deep understanding of @{primary_username}'s brand and audience

EXECUTE ELITE ACCOUNT MANAGEMENT ANALYSIS:
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
🎯 PERSONAL ACCOUNT MANAGEMENT BRIEFING - EXECUTIVE LEVEL 🎯

ACCOUNT UNDER MANAGEMENT: @{primary_username} [PERSONAL BRAND]
STRATEGIC FOCUS: {query}
MISSION: Authentic voice amplification and strategic personal growth
ANALYSIS DATE: {datetime.now().strftime('%B %d, %Y')}

=== 📊 YOUR ACCOUNT'S AUTHENTIC VOICE ANALYSIS ===
        {writing_style_analysis}

=== 🔥 AUTHENTIC CONTENT INTELLIGENCE ===
        {personal_insights}

=== 📋 COMPLETE CONTENT ANALYSIS ===
        {primary_context if primary_context else "Limited post data available - focusing on authentic voice development"}

=== 🎯 EXECUTIVE PERSONAL ACCOUNT MANAGER PROTOCOL ===

You are the ELITE PERSONAL ACCOUNT MANAGER for @{primary_username}. You have complete access to their authentic voice patterns, engagement data, and personal brand analytics. Your role is to provide executive-level strategic guidance that amplifies their authentic voice while maximizing genuine engagement and personal growth.

**MODULE 1: 📈 PERSONAL GROWTH RECOMMENDATIONS**
Provide comprehensive personal brand optimization including:
• 🎯 **Authentic Voice Analysis**: Detail @{primary_username}'s natural communication style, personality traits, and genuine expression patterns
• 📊 **Personal Engagement Dashboard**: Include specific metrics showing which authentic moments drive the highest engagement
• 🔥 **Community Connection Intel**: Analyze how @{primary_username} naturally builds relationships and connects with their audience
• ⚡ **Authentic Growth Strategies**: Provide 3-5 specific tactics to amplify their natural voice and grow genuine engagement
• 🚀 **Personal Content Roadmap**: Strategic recommendations for authentic content that reflects their true personality, interests, and experiences

**MODULE 2: 🔍 PERSONAL BRAND INTELLIGENCE**
Deliver authentic voice optimization featuring:
• 📊 **Voice Pattern Analysis**: Identify @{primary_username}'s unique communication style, emotional expressions, and authentic storytelling approach
• 🎯 **Engagement Authenticity**: Break down which genuine moments drive highest audience connection with specific examples and metrics
• ⚖️ **Personal Brand Positioning**: Strategic positioning opportunities that align perfectly with @{primary_username}'s authentic personality and interests
• 🔥 **Authentic Advantages**: Identify specific personal qualities, experiences, and perspectives that make @{primary_username} uniquely engaging
• 💡 **Community Growth Map**: Strategies to build genuine connections and foster authentic community while staying true to their voice

**MODULE 3: 🎨 NEXT POST AUTHENTIC CREATION**
Generate the optimal authentic next post with:
• ✨ **Personality-Aligned Content**: Perfect alignment with @{primary_username}'s natural voice, genuine interests, and personal experiences
• 📝 **Authentic Expression**: Crafted based on analysis of @{primary_username}'s most genuine, engaging, and personally resonant posts
• 🏷️ **Natural Hashtag Strategy**: Hashtag approach that matches @{primary_username}'s authentic usage patterns and personal interests
• 🎨 **Personal Visual Direction**: Detailed caption image prompt reflecting @{primary_username}'s authentic aesthetic, lifestyle, and personal brand
• 🎯 **Genuine Engagement**: Call-to-action designed for authentic community interaction based on their natural communication style and interests

=== 📋 EXECUTIVE REPORTING FORMAT ===

Structure your analysis using this EXACT format with engaging presentation:

{{
    "account_analysis": "🎯 **@{primary_username} AUTHENTIC PERSONAL BRAND ANALYSIS**\n\n📊 **Personal Voice Intelligence:**\n• [Detailed analysis of their natural communication style and personality traits]\n• [Authentic expression patterns and emotional storytelling approach]\n• [Personal interests and expertise areas that drive engagement]\n\n🔥 **Genuine Engagement Drivers:**\n• [Specific types of authentic content that resonate with their audience]\n• [Personal stories, experiences, and moments that generate highest engagement]\n• [Natural community building approaches and connection tactics they use]\n\n💡 **Authentic Brand Positioning:**\n• [Their unique personal qualities, perspectives, and experiences]\n• [Areas where their authentic voice and personality stand out]\n• [Personal interests, expertise, and lifestyle elements to amplify]\n\n📈 **Growth Potential Analysis:**\n• [Authentic growth opportunities that align with their personality]\n• [Personal content themes with highest engagement and expansion potential]\n• [Community building strategies that feel natural to their voice]",
    
    "content_recommendations": "🚀 **STRATEGIC PERSONAL CONTENT PLAN FOR @{primary_username}**\n\n⚡ **IMMEDIATE AUTHENTIC ACTIONS:**\n• 🎯 **Personal Story Amplification**: [Specific approach to share their experiences more effectively with expected engagement boost]\n• 📊 **Voice Optimization Strategy**: [Tactical recommendations to enhance their natural communication style]\n• 🔥 **Community Connection Enhancement**: [Specific tactics to build genuine relationships with their audience]\n• 💡 **Interest-Based Content Expansion**: [Strategic content themes based on their authentic interests and expertise]\n• 🚀 **Authentic Growth Acceleration**: [Personal brand development strategies that maintain genuine voice]\n\n📈 **CONTENT OPTIMIZATION ROADMAP:**\n• [Specific content types and themes to prioritize based on their authentic voice]\n• [Personal storytelling approaches that maximize genuine engagement]\n• [Timing and frequency recommendations that align with their natural patterns]\n\n🎯 **AUTHENTIC ENGAGEMENT STRATEGIES:**\n• [Community interaction approaches that feel natural to their personality]\n• [Personal content formats that showcase their unique voice and interests]\n• [Authentic conversation starters and relationship building tactics]\n\n💡 **PERSONAL BRAND EVOLUTION:**\n• [Ways to grow their reach while maintaining authentic personality]\n• [Personal expertise and interest areas to develop and showcase]\n• [Authentic positioning strategies for long-term personal brand growth]",
    
            "next_post": {{
        "caption": "[Craft an engaging caption that sounds exactly like @{primary_username} would naturally write, incorporating their authentic voice, personal interests, genuine personality, and natural communication style]",
        "hashtags": ["#authentic", "#personal", "#genuine", "#interests"],
        "call_to_action": "[Natural engagement prompt that fits perfectly with @{primary_username}'s communication style and encourages genuine community interaction based on their personality]",
        "visual_prompt": "🎨 **AUTHENTIC VISUAL DIRECTION**: [Detailed, creative image prompt that reflects @{primary_username}'s personal aesthetic, lifestyle, interests, and authentic style. Include: composition style that matches their personality, color palette that aligns with their brand, visual elements that represent their interests, lighting and mood that reflects their authentic voice, props and settings that connect to their lifestyle, and design details that showcase their personal brand. Make it comprehensive enough for an AI image generator to create stunning, authentic visuals that truly represent their personal voice and resonate with their genuine audience.]"
    }}
}}

=== 🎯 PERSONAL ACCOUNT MANAGER EXCELLENCE STANDARDS ===

✅ **AUTHENTICITY REQUIREMENTS:**
- Every recommendation based on @{primary_username}'s actual authentic voice and genuine personality patterns from their content
- All strategies designed to amplify their natural strengths, real interests, and personal experiences
- Growth tactics that feel completely natural and genuine to their personality and lifestyle
- Content suggestions that perfectly align with their authentic self-expression and personal brand

✅ **PROFESSIONAL PRESENTATION:**
- Use emojis strategically to enhance readability, engagement, and visual hierarchy
- Structure content with bullet points and organized formatting for easy consumption and implementation
- Include specific metrics, examples, and insights from their authentic content patterns and engagement data
- Maintain supportive, encouraging, and empowering tone while providing strategic guidance

✅ **STRATEGIC AUTHENTICITY:**
- Provide growth strategies that enhance and amplify rather than change their authentic voice
- Connect all recommendations to their genuine interests, natural communication style, and personal experiences
- Base all suggestions on proven patterns from their most authentic, engaging, and personally resonant content
- Deliver actionable insights that help them be more effectively themselves while growing their genuine community

EXECUTE AUTHENTIC PERSONAL BRAND MANAGEMENT:
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
🎯 PERSONAL ACCOUNT MANAGEMENT BRIEFING - EXECUTIVE LEVEL 🎯

ACCOUNT UNDER MANAGEMENT: @{primary_username} [PERSONAL BRAND]
MISSION: Authentic voice amplification and strategic personal growth

=== 📊 YOUR ACCOUNT'S AUTHENTIC VOICE ANALYSIS ===
{voice_fingerprint}

=== 📈 ENGAGEMENT INTELLIGENCE ===
{authenticity_intelligence}

=== 🎯 EXECUTIVE PERSONAL ACCOUNT MANAGER PROTOCOL ===

You are the ELITE PERSONAL ACCOUNT MANAGER for @{primary_username}. You have complete access to their authentic voice patterns, engagement data, and personal brand analytics. Your role is to provide executive-level strategic guidance that amplifies their authentic voice while maximizing genuine engagement.

**MODULE 1: 📈 PERSONAL GROWTH RECOMMENDATIONS**
Provide comprehensive personal brand optimization including:
• 🎯 **Authentic Voice Analysis**: Detail @{primary_username}'s natural communication style, personality traits, and authentic expression patterns
• 📊 **Personal Engagement Dashboard**: Include specific metrics showing which authentic moments drive the highest engagement
• 🔥 **Community Connection Intel**: Analyze how @{primary_username} naturally builds relationships and connects with their audience
• ⚡ **Authentic Growth Strategies**: Provide 3-5 specific tactics to amplify their natural voice and grow genuine engagement
• 🚀 **Personal Content Roadmap**: Strategic recommendations for authentic content that reflects their true personality and interests

**MODULE 2: 🔍 PERSONAL BRAND INTELLIGENCE**
Deliver authentic voice optimization featuring:
• 📊 **Voice Pattern Analysis**: Identify @{primary_username}'s unique communication style, emotional expressions, and authentic storytelling approach
• 🎯 **Engagement Authenticity**: Break down which genuine moments drive highest audience connection with specific examples
• ⚖️ **Personal Brand Positioning**: Strategic positioning opportunities that align perfectly with @{primary_username}'s authentic personality
• 🔥 **Authentic Advantages**: Identify specific personal qualities and experiences that make @{primary_username} unique
• 💡 **Community Growth Map**: Strategies to build genuine connections while staying true to their authentic voice

**MODULE 3: 🎨 NEXT POST AUTHENTIC CREATION**
Generate the optimal authentic next post with:
• ✨ **Personality-Aligned Content**: Perfect alignment with @{primary_username}'s natural voice and genuine interests
• 📝 **Authentic Expression**: Crafted based on analysis of @{primary_username}'s most genuine and engaging posts
• 🏷️ **Natural Hashtag Strategy**: Hashtag approach that matches @{primary_username}'s authentic usage patterns and personal interests
• 🎨 **Personal Visual Direction**: Image prompt reflecting @{primary_username}'s authentic aesthetic and interests
• 🎯 **Genuine Engagement**: Call-to-action designed for authentic community interaction based on their natural communication style

=== 📋 EXECUTIVE REPORTING FORMAT ===

Structure your analysis using this EXACT format with engaging presentation:

{{
    "personal_intelligence": {{
        "voice_dna": "🎯 **@{primary_username} AUTHENTIC VOICE ANALYSIS**\n\n📊 **Personal Communication Style:**\n• [Detailed analysis of their natural way of expressing themselves]\n• [Personality traits that shine through in their content]\n• [Authentic storytelling patterns and emotional expressions]\n\n🔥 **Genuine Engagement Drivers:**\n• [Specific types of authentic content that resonate with their audience]\n• [Personal stories and experiences that generate highest engagement]\n• [Natural community building approaches they use]\n\n💡 **Authentic Brand Positioning:**\n• [Their unique personal qualities and perspectives]\n• [Areas where their authentic voice stands out]\n• [Personal interests and expertise areas to amplify]",
        
        "engagement_personality": "📈 **PERSONAL ENGAGEMENT INTELLIGENCE**\n\n🎯 **Authentic Connection Patterns:**\n• [How their genuine personality drives engagement]\n• [Which personal topics and interests resonate most]\n• [Natural conversation starters and community building tactics]\n\n📊 **Voice Authenticity Metrics:**\n• [Engagement levels on personal vs general content]\n• [Audience response to their authentic moments]\n• [Growth patterns when being genuinely themselves]\n\n⚡ **Natural Growth Opportunities:**\n• [Areas to expand while maintaining authenticity]\n• [Personal interests that could drive more engagement]\n• [Authentic story angles to explore]",
        
        "audience_connection": "🤝 **COMMUNITY CONNECTION ANALYSIS**\n\n💬 **Natural Interaction Style:**\n• [How @{primary_username} naturally engages with their audience]\n• [Their authentic response patterns and conversation approach]\n• [Community building tactics that feel genuine to them]\n\n🎯 **Audience Relationship Dynamics:**\n• [What their followers appreciate most about their authentic voice]\n• [Types of content that drive genuine community interaction]\n• [Personal elements that build strongest connections]\n\n🚀 **Authentic Growth Strategies:**\n• [Ways to scale their genuine personality]\n• [Personal content themes with highest growth potential]\n• [Community engagement approaches that feel natural]"
    }},
    
    "growth_opportunities": {{
        "authentic_expansion": "🌟 **NATURAL GROWTH OPPORTUNITIES FOR @{primary_username}**\n\n🎯 **Personality Amplification:**\n• [Specific ways to amplify their natural strengths and interests]\n• [Personal expertise areas to showcase more prominently]\n• [Authentic story angles that could resonate with broader audiences]\n\n📈 **Genuine Reach Extension:**\n• [Strategies to grow while maintaining authentic voice]\n• [Personal content themes with viral potential]\n• [Community collaboration opportunities that align with their interests]",
        
        "engagement_amplification": "🚀 **AUTHENTIC ENGAGEMENT BOOST STRATEGIES**\n\n⚡ **Natural Interaction Enhancement:**\n• [Ways to increase genuine audience interaction]\n• [Personal storytelling approaches for higher engagement]\n• [Authentic conversation starters based on their interests]\n\n🎯 **Voice Optimization:**\n• [Refinements to amplify their natural communication style]\n• [Personal content formats that maximize authentic engagement]\n• [Timing strategies that align with their natural posting patterns]",
        
        "content_diversification": "🎨 **AUTHENTIC CONTENT EXPANSION**\n\n💡 **Personal Interest Exploration:**\n• [New content types that align with their authentic interests]\n• [Personal expertise areas to explore more deeply]\n• [Authentic formats that could showcase their personality]\n\n🔥 **Natural Content Evolution:**\n• [Ways to evolve their content while staying true to themselves]\n• [Personal themes with untapped potential]\n• [Authentic approaches to trending topics]"
    }},
    
    "tactical_recommendations": [
        "🎯 **AUTHENTIC VOICE AMPLIFICATION**: [Specific strategy to enhance their natural communication style with expected engagement impact]",
        "📊 **PERSONAL STORY OPTIMIZATION**: [Tactical approach to share their experiences more effectively for community building]",
        "🚀 **GENUINE GROWTH ACCELERATION**: [Strategic move to expand reach while maintaining authentic personality]"
    ],
    
    "next_post_prediction": {{
        "tweet_text": "[Craft a tweet that sounds exactly like @{primary_username} would naturally write, incorporating their authentic voice, personal interests, and genuine personality - maximum 280 characters]",
        "hashtags": ["#authentic", "#personal", "#genuine"],
        "call_to_action": "[Natural engagement prompt that fits perfectly with @{primary_username}'s communication style and encourages genuine community interaction]",
        "image_prompt": "🎨 **AUTHENTIC VISUAL DIRECTION**: [Detailed image prompt that reflects @{primary_username}'s personal aesthetic, interests, and authentic style. Include: personal elements, mood that matches their personality, visual style that feels genuine to them, and design details that represent their authentic brand. Make it specific enough for creating visuals that truly represent their personal voice.]",
        "personality_note": "[Brief explanation of why this tweet perfectly aligns with @{primary_username}'s authentic voice and natural interests]"
    }}
}}

=== 🎯 PERSONAL ACCOUNT MANAGER EXCELLENCE STANDARDS ===

✅ **AUTHENTICITY REQUIREMENTS:**
- Every recommendation based on @{primary_username}'s actual authentic voice and genuine personality patterns
- All strategies designed to amplify their natural strengths and real interests
- Growth tactics that feel completely natural and genuine to their personality
- Content suggestions that align perfectly with their authentic self-expression

✅ **PROFESSIONAL PRESENTATION:**
- Use emojis strategically to enhance readability and engagement hierarchy
- Structure content with bullet points and formatting for easy consumption
- Include specific metrics and examples from their authentic content patterns
- Maintain supportive, encouraging tone while providing strategic guidance

✅ **STRATEGIC AUTHENTICITY:**
- Provide growth strategies that enhance rather than change their authentic voice
- Connect all recommendations to their genuine interests and natural communication style
- Base all suggestions on proven patterns from their most authentic and engaging content
- Deliver insights that help them be more effectively themselves while growing their community

EXECUTE AUTHENTIC PERSONAL BRAND MANAGEMENT:
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