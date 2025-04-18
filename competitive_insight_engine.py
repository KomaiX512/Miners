"""Module for generating competitive insights using time series analysis, RAG, and prompt engineering."""

import logging
import json
import re
from datetime import datetime
import pandas as pd

from recommendation_generation import RecommendationGenerator
from rag_implementation import RagImplementation
from time_series_analysis import TimeSeriesAnalyzer
from vector_database import VectorDatabaseManager
from config import LOGGING_CONFIG

# Set up logging
logging.basicConfig(
    level=LOGGING_CONFIG['level'],
    format=LOGGING_CONFIG['format']
)
logger = logging.getLogger(__name__)

class CompetitiveInsightEngine:
    """Class for generating competitive insights and strategic recommendations."""
    
    def __init__(self, rag=None, time_series=None, vector_db=None):
        """Initialize with necessary components."""
        self.rag = rag or RagImplementation()
        self.time_series = time_series or TimeSeriesAnalyzer()
        self.vector_db = vector_db or VectorDatabaseManager()
        self.recommendation_generator = RecommendationGenerator(self.rag, self.time_series)
        logger.info("CompetitiveInsightEngine initialized with all required components")
    
    def _extract_account_info(self, profile_data):
        """Extract account information from profile data."""
        try:
            # Basic profile information
            info = {
                'username': profile_data.get('username', 'unknown'),
                'followers': profile_data.get('followers', 0),
                'following': profile_data.get('following', 0),
                'bio': profile_data.get('bio', ''),
                'image_url': profile_data.get('profile_pic_url', ''),
                'post_count': profile_data.get('posts_count', 0),
                'category': profile_data.get('category', '')
            }
            
            # Additional metrics if available
            if 'engagement_metrics' in profile_data:
                info.update(profile_data['engagement_metrics'])
            
            # Calculate engagement rate if possible
            if info['followers'] > 0 and 'avg_likes' in info:
                info['engagement_rate'] = (info['avg_likes'] / info['followers']) * 100
                
            return info
        except Exception as e:
            logger.error(f"Error extracting account info: {str(e)}")
            return {
                'username': profile_data.get('username', 'unknown'),
                'followers': 0,
                'following': 0,
                'bio': '',
                'image_url': '',
                'error': str(e)
            }
    
    def _analyze_profit_patterns(self, posts, primary_username=None):
        """Analyze profit patterns from post data."""
        try:
            # Convert engagement to profit proxy
            for post in posts:
                # Use engagement as a proxy for profit if no direct profit data
                if 'profit' not in post and 'engagement' in post:
                    post['profit'] = float(post['engagement']) * 0.1  # Simple proxy calculation
                elif 'profit' not in post:
                    # Estimate from likes and comments
                    likes = float(post.get('likes', 0))
                    comments = float(post.get('comments', 0))
                    post['profit'] = (likes * 0.05) + (comments * 0.2)
            
            # Convert to DataFrame for time series analysis
            df = pd.DataFrame(posts)
            if 'timestamp' not in df.columns:
                logger.warning("No timestamp column found in posts data")
                return None
                
            # Prepare time series data
            ts_data = self.time_series.prepare_data(
                df, 
                timestamp_col='timestamp', 
                value_col='profit',
                primary_username=primary_username
            )
            
            if ts_data is None or ts_data.empty:
                logger.warning("Failed to prepare time series data")
                return None
                
            # Run time series analysis
            analysis_results = self.time_series.analyze_data(
                ts_data,
                timestamp_col='ds',
                value_col='y',
                primary_username=primary_username
            )
            
            # Extract key insights
            insights = {
                'trend_direction': 'up' if analysis_results['forecast']['trend'].mean() > 0 else 'down',
                'trending_periods': [],
                'forecast': []
            }
            
            # Extract trending periods
            if 'trending_periods' in analysis_results and not analysis_results['trending_periods'].empty:
                for _, row in analysis_results['trending_periods'].iterrows():
                    insights['trending_periods'].append({
                        'date': row['ds'].strftime('%Y-%m-%d'),
                        'predicted_profit': float(row['yhat']),
                        'lower_bound': float(row['yhat_lower']),
                        'upper_bound': float(row['yhat_upper'])
                    })
            
            # Extract forecast
            if 'forecast' in analysis_results and not analysis_results['forecast'].empty:
                # Get only future dates
                future_forecast = analysis_results['forecast'][
                    analysis_results['forecast']['ds'] > datetime.now()
                ]
                
                for _, row in future_forecast.iterrows():
                    insights['forecast'].append({
                        'date': row['ds'].strftime('%Y-%m-%d'),
                        'predicted_profit': float(row['yhat']),
                        'lower_bound': float(row['yhat_lower']),
                        'upper_bound': float(row['yhat_upper'])
                    })
            
            return insights
        except Exception as e:
            logger.error(f"Error analyzing profit patterns: {str(e)}")
            return None
    
    def _get_competitor_insights(self, primary_username, competitor_usernames, query):
        """Get insights about competitors using RAG implementation."""
        try:
            # Enhanced prompt for competitor analysis
            competitor_prompt = f"""
            Analyze the social media profiles of these accounts in the beauty industry:
            
            Primary account: {primary_username}
            Competitor accounts: {', '.join(competitor_usernames)}
            
            For each competitor, provide:
            1. Their unique positioning and strategy
            2. Content types that drive highest engagement
            3. How they differentiate from {primary_username}
            
            Format as JSON with competitors as keys, each with an "insights" array containing 3 specific observations.
            """
            
            # Generate insights
            competitor_insights = self.rag.generate_recommendation(
                primary_username,
                competitor_usernames, 
                competitor_prompt
            )
            
            # Transform into expected format if needed
            if isinstance(competitor_insights, dict) and "competitor_analysis" in competitor_insights:
                return competitor_insights["competitor_analysis"]
            elif not isinstance(competitor_insights, dict):
                return {
                    comp: {"insights": [
                        f"No detailed analysis available for {comp}",
                        "Recommend manual review of their content",
                        "Consider comparing engagement metrics directly"
                    ]} for comp in competitor_usernames
                }
            
            return competitor_insights
        except Exception as e:
            logger.error(f"Error getting competitor insights: {str(e)}")
            return {
                comp: {"insights": [
                    f"Analysis failed: {str(e)}",
                    "System could not retrieve insights",
                    "Consider manual review"
                ]} for comp in competitor_usernames
            }
    
    def _generate_strategies(self, primary_username, competitor_insights, profit_analysis):
        """Generate strategic recommendations based on competitor insights and profit analysis."""
        try:
            # Create a detailed prompt for strategy generation
            strategy_prompt = f"""
            Based on comprehensive analysis of {primary_username} and competitors, generate strategic recommendations
            that focus on competitive advantages and profit maximization.
            
            Competitor insights summary:
            {json.dumps(competitor_insights, indent=2)}
            
            Profit trend analysis:
            {json.dumps(profit_analysis, indent=2) if profit_analysis else "No profit analysis available"}
            
            Develop a strategic plan that:
            1. Leverages competitor weaknesses
            2. Capitalizes on profit trend opportunities
            3. Differentiates {primary_username} effectively
            4. Provides concrete action steps for the next 7 days
            
            The response should be one cohesive strategic paragraph with strong reasoning.
            """
            
            # Generate strategy
            strategy_response = self.rag.generate_recommendation(
                primary_username,
                list(competitor_insights.keys()) if isinstance(competitor_insights, dict) else [], 
                strategy_prompt
            )
            
            # Extract or create strategy paragraph
            strategy = ""
            if isinstance(strategy_response, dict) and "recommendations" in strategy_response:
                strategy = strategy_response["recommendations"]
            elif isinstance(strategy_response, dict) and "strategy" in strategy_response:
                strategy = strategy_response["strategy"]
            elif isinstance(strategy_response, str):
                strategy = strategy_response
            else:
                # Fallback strategy
                trend = "upward" if profit_analysis and profit_analysis.get('trend_direction') == 'up' else "varied"
                strategy = f"Implement a differentiation strategy for {primary_username} based on the {trend} profit trend. Focus on creating unique visual aesthetics that contrast with competitors while maintaining consistent posting schedule to build audience anticipation. Leverage user-generated content to increase engagement while reducing content creation costs. Monitor competitor activities daily and adapt quickly to emerging trends while maintaining brand identity."
            
            return strategy
        except Exception as e:
            logger.error(f"Error generating strategies: {str(e)}")
            return f"Strategic focus for {primary_username}: Differentiate content, increase posting consistency, and monitor competitor activities. Adapt to emerging trends while maintaining unique brand identity. Error in detailed strategy generation: {str(e)}"
    
    def _predict_next_post(self, primary_username, competitor_insights, profit_analysis, posts):
        """Predict the next optimal post based on analysis."""
        try:
            # Extract recent posts
            recent_posts = []
            for post in posts[:5]:  # Last 5 posts
                caption = post.get('caption', '')
                hashtags = post.get('hashtags', [])
                if isinstance(hashtags, str):
                    hashtags = re.findall(r'#\w+', hashtags)
                
                recent_posts.append({
                    'caption': caption,
                    'hashtags': hashtags,
                    'engagement': post.get('engagement', 0),
                    'profit': post.get('profit', 0),
                    'likes': post.get('likes', 0),
                    'comments': post.get('comments', 0)
                })
            
            # Create prompt for next post prediction
            post_prompt = f"""
            Based on analysis of {primary_username} and competitors, predict the optimal next post that will maximize engagement and profit.
            
            Recent posts:
            {json.dumps(recent_posts, indent=2)}
            
            Competitor insights:
            {json.dumps(competitor_insights, indent=2)}
            
            Profit analysis:
            {json.dumps(profit_analysis, indent=2) if profit_analysis else "No profit analysis available"}
            
            Create a detailed next post blueprint with:
            1. A visual prompt describing the image in detail (colors, composition, theme)
            2. An engaging caption that resonates with the audience
            3. Strategic hashtags that will increase discoverability
            4. A compelling call to action that drives engagement
            
            Format response as JSON with "visual_prompt", "caption", "hashtags" (array), and "call_to_action" fields.
            """
            
            # Generate next post prediction
            post_prediction = self.rag.generate_recommendation(
                primary_username,
                list(competitor_insights.keys()) if isinstance(competitor_insights, dict) else [], 
                post_prompt
            )
            
            # Extract next post
            if isinstance(post_prediction, dict) and "next_post" in post_prediction:
                return post_prediction["next_post"]
            elif isinstance(post_prediction, dict) and all(k in post_prediction for k in ["caption", "hashtags", "call_to_action"]):
                return post_prediction
            else:
                # Fallback post prediction
                return {
                    "visual_prompt": f"A vibrant, high-contrast image showcasing the latest products from {primary_username} with a clean, minimal background to enhance product visibility. Use soft lighting to create an inviting atmosphere and include subtle brand elements.",
                    "caption": f"Elevate your style with our newest collection. Designed for those who appreciate quality and elegance. ✨ #{primary_username.replace(' ', '')}",
                    "hashtags": ["#NewCollection", "#MustHave", "#StyleInspo", "#TrendAlert", "#LimitedEdition"],
                    "call_to_action": "Double tap if you're loving this look! 💕 Share in comments which item you'd grab first!"
                }
        except Exception as e:
            logger.error(f"Error predicting next post: {str(e)}")
            return {
                "visual_prompt": f"Product showcase image for {primary_username}",
                "caption": "Check out our latest release!",
                "hashtags": ["#New", "#MustHave", "#TrendAlert"],
                "call_to_action": "Shop now while supplies last!"
            }
    
    def analyze_profiles(self, primary_username, secondary_usernames, profile_data, posts, query="competitive analysis"):
        """
        Generate comprehensive competitive insights from profile data.
        
        Args:
            primary_username (str): The primary username to analyze
            secondary_usernames (list): List of competitor usernames
            profile_data (dict): Dictionary mapping usernames to profile data
            posts (list): List of posts from all profiles
            query (str): Query for RAG implementation
            
        Returns:
            dict: Dictionary with four blocks of insights
        """
        try:
            if not primary_username or not secondary_usernames or not profile_data:
                logger.error("Missing required inputs for competitive analysis")
                return None
            
            # Extract account info for all profiles
            account_info = {}
            for username in [primary_username] + secondary_usernames:
                if username in profile_data:
                    account_info[username] = self._extract_account_info(profile_data[username])
                else:
                    logger.warning(f"No profile data for {username}")
                    account_info[username] = {
                        'username': username,
                        'followers': 0,
                        'following': 0,
                        'bio': f"Profile data not available for {username}",
                        'image_url': '',
                        'error': 'Profile data not available'
                    }
            
            # Filter posts by username
            primary_posts = [p for p in posts if p.get('username') == primary_username]
            
            # Analyze profit patterns
            profit_analysis = self._analyze_profit_patterns(primary_posts, primary_username)
            
            # Get competitor insights
            competitor_insights = self._get_competitor_insights(primary_username, secondary_usernames, query)
            
            # Generate strategies
            strategy = self._generate_strategies(primary_username, competitor_insights, profit_analysis)
            
            # Predict next post
            next_post = self._predict_next_post(primary_username, competitor_insights, profit_analysis, primary_posts)
            
            # Compile results into required format
            results = {
                'account_info': account_info,
                'competitor_analysis': competitor_insights,
                'strategies': strategy,
                'next_post': next_post,
                'generated_at': datetime.now().isoformat()
            }
            
            logger.info(f"Successfully generated competitive insights for {primary_username}")
            return results
        except Exception as e:
            logger.error(f"Error analyzing profiles: {str(e)}")
            return None
    
    def load_json_profiles(self, directory_path):
        """
        Load profile data from JSON files in the specified directory.
        
        Args:
            directory_path (str): Path to directory containing JSON profiles
            
        Returns:
            tuple: (profile_data, posts, primary_username, secondary_usernames)
        """
        import os
        try:
            if not os.path.exists(directory_path):
                logger.error(f"Directory not found: {directory_path}")
                return None, None, None, None
            
            profile_data = {}
            all_posts = []
            
            # Get list of JSON files
            json_files = [f for f in os.listdir(directory_path) if f.endswith('.json')]
            if not json_files:
                logger.error(f"No JSON files found in {directory_path}")
                return None, None, None, None
            
            # Load each file
            for json_file in json_files:
                file_path = os.path.join(directory_path, json_file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    # Extract username and profile info
                    username = data.get('username') or json_file.replace('.json', '')
                    
                    # Skip if username already exists (duplicate file)
                    if username in profile_data:
                        continue
                    
                    profile_data[username] = data
                    
                    # Extract posts
                    posts = data.get('posts', data.get('items', []))
                    for post in posts:
                        if 'username' not in post:
                            post['username'] = username
                        all_posts.append(post)
                    
                except Exception as e:
                    logger.error(f"Error loading {file_path}: {str(e)}")
            
            if not profile_data:
                logger.error("No valid profile data loaded")
                return None, None, None, None
            
            # Determine primary and secondary usernames
            # Assuming the first file is the primary account
            usernames = list(profile_data.keys())
            primary_username = usernames[0]
            secondary_usernames = usernames[1:] if len(usernames) > 1 else []
            
            logger.info(f"Loaded {len(profile_data)} profiles and {len(all_posts)} posts")
            logger.info(f"Primary username: {primary_username}")
            logger.info(f"Secondary usernames: {secondary_usernames}")
            
            return profile_data, all_posts, primary_username, secondary_usernames
        except Exception as e:
            logger.error(f"Error loading JSON profiles: {str(e)}")
            return None, None, None, None


def test_competitive_insight_engine():
    """Test the CompetitiveInsightEngine with sample data."""
    try:
        engine = CompetitiveInsightEngine()
        
        # Sample primary and secondary usernames
        primary_username = "maccosmetics"
        secondary_usernames = ["anastasiabeverlyhills", "fentybeauty", "narsissist", "toofaced", "urbandecay"]
        
        # Sample profile data
        profile_data = {
            primary_username: {
                "username": primary_username,
                "followers": 242000,
                "following": 1250,
                "bio": "Professional makeup brand offering the finest quality cosmetics.",
                "profile_pic_url": "https://example.com/profile_pic_mac.jpg",
                "posts_count": 2100,
                "category": "Beauty/Cosmetics"
            }
        }
        
        # Add sample data for secondary usernames
        for i, username in enumerate(secondary_usernames):
            profile_data[username] = {
                "username": username,
                "followers": 200000 - (i * 20000),
                "following": 1000 - (i * 100),
                "bio": f"Beauty brand specializing in {username.split('beauty')[0] if 'beauty' in username else ''} products.",
                "profile_pic_url": f"https://example.com/profile_pic_{username}.jpg",
                "posts_count": 2000 - (i * 200),
                "category": "Beauty/Cosmetics"
            }
        
        # Sample posts
        sample_posts = [
            {'id': '1', 'caption': 'Bold summer looks! #SummerMakeup', 'hashtags': ['#SummerMakeup'], 
             'engagement': 15000, 'likes': 14000, 'comments': 1000, 
             'timestamp': '2025-04-01T10:00:00Z', 'username': primary_username},
            {'id': '2', 'caption': 'New palette drop! #GlowUp', 'hashtags': ['#GlowUp'], 
             'engagement': 20000, 'likes': 18000, 'comments': 2000, 
             'timestamp': '2025-04-02T12:00:00Z', 'username': primary_username},
            {'id': '3', 'caption': 'Brow perfection! #BrowGame', 'hashtags': ['#BrowGame'], 
             'engagement': 18000, 'likes': 16000, 'comments': 2000, 
             'timestamp': '2025-04-03T14:00:00Z', 'username': secondary_usernames[0]},
            {'id': '4', 'caption': 'Glowy skin secrets! #Skincare', 'hashtags': ['#Skincare'], 
             'engagement': 22000, 'likes': 20000, 'comments': 2000, 
             'timestamp': '2025-04-04T15:00:00Z', 'username': secondary_usernames[1]},
            {'id': '5', 'caption': 'Matte lip trend! #MatteLips', 'hashtags': ['#MatteLips'],
             'engagement': 16000, 'likes': 15000, 'comments': 1000,
             'timestamp': '2025-04-05T10:00:00Z', 'username': secondary_usernames[2]}
        ]
        
        # Get competitive insights
        results = engine.analyze_profiles(
            primary_username,
            secondary_usernames,
            profile_data,
            sample_posts
        )
        
        # Check results
        if not results:
            logger.error("Test failed: No results returned")
            return False
            
        # Check all required sections are present
        required_sections = ['account_info', 'competitor_analysis', 'strategies', 'next_post']
        missing_sections = [section for section in required_sections if section not in results]
        if missing_sections:
            logger.error(f"Test failed: Missing sections - {missing_sections}")
            return False
            
        # Check account info
        if primary_username not in results['account_info']:
            logger.error(f"Test failed: Primary username {primary_username} not in account_info")
            return False
            
        # Check competitors
        for username in secondary_usernames:
            if username not in results['account_info']:
                logger.warning(f"Secondary username {username} not in account_info")
        
        # Check next post
        required_post_fields = ['visual_prompt', 'caption', 'hashtags', 'call_to_action']
        missing_post_fields = [field for field in required_post_fields if field not in results['next_post']]
        if missing_post_fields:
            logger.error(f"Test failed: Missing next_post fields - {missing_post_fields}")
            return False
            
        logger.info("Competitive insight engine test successful")
        return True
    except Exception as e:
        logger.error(f"Test failed with exception: {str(e)}")
        return False


if __name__ == "__main__":
    success = test_competitive_insight_engine()
    print(f"CompetitiveInsightEngine test {'successful' if success else 'failed'}")
    
    # Example usage with real files
    # engine = CompetitiveInsightEngine()
    # profile_data, posts, primary, secondary = engine.load_json_profiles("profiles")
    # if profile_data and posts and primary and secondary:
    #     results = engine.analyze_profiles(primary, secondary, profile_data, posts)
    #     print(json.dumps(results, indent=2)) 