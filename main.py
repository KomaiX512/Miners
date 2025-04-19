import logging
import json
import os
import io
import sys
import json
import logging
import argparse
from datetime import datetime
from data_retrieval import R2DataRetriever
from time_series_analysis import TimeSeriesAnalyzer
from vector_database import VectorDatabaseManager
from rag_implementation import RagImplementation
from recommendation_generation import RecommendationGenerator
from config import R2_CONFIG, LOGGING_CONFIG, GEMINI_CONFIG
import pandas as pd
from r2_storage_manager import R2StorageManager
from instagram_scraper import InstagramScraper
import re
import asyncio
import traceback


# Set up logging
logging.basicConfig(
    level=LOGGING_CONFIG['level'],
    format=LOGGING_CONFIG['format']
)
logger = logging.getLogger(__name__)

class ContentRecommendationSystem:
    """Class for the complete content recommendation system."""
    def __init__(self):
        """Initialize all components of the system."""
        logger.info("Initializing Content Recommendation System")

        self.data_retriever = R2DataRetriever()
        self.vector_db = VectorDatabaseManager()
        self.time_series = TimeSeriesAnalyzer()
        self.rag = RagImplementation(vector_db=self.vector_db)
        self.recommendation_generator = RecommendationGenerator(
            rag=self.rag,
            time_series=self.time_series
        )
        self.r2_storage = R2StorageManager()

    def ensure_sample_data_in_r2(self):
        """Ensure sample data exists in R2 (stub implementation)."""
        logger.info("ensure_sample_data_in_r2: Stub implementation; no sample data uploaded.")
        return True

    def process_social_data(self, data_key):
        """Process social media data from R2."""
        try:
            logger.info(f"Processing social data from {data_key}")

            raw_data = self.data_retriever.get_json_data(data_key)
            if raw_data is None:
                logger.error(f"No data found at {data_key}")
                return None

            if isinstance(raw_data, list) and raw_data and 'latestPosts' in raw_data[0]:
                data = self.process_instagram_data(raw_data)
                if data:
                    logger.info("Successfully processed Instagram data")

                    # Extract primary username from data_key if not in profile
                    if not data.get('primary_username') and 'profile' in data:
                        # Try to extract username from data_key (format: username/username.json)
                        if '/' in data_key:
                            # Extract username from the path
                            primary_username = data_key.split('/')[0]
                            data['primary_username'] = primary_username
                            
                            # Make sure it's also in profile
                            if 'username' not in data['profile'] or not data['profile']['username']:
                                data['profile']['username'] = primary_username
                                logger.info(f"Extracted primary username from data_key: {primary_username}")

                    # Handle competitor data files
                    if '/' in data_key:
                        # Extract the parent directory from the key (e.g., "maccosmetics" from "maccosmetics/maccosmetics.json")
                        parent_dir = data_key.split('/')[0]
                        # Load competitor files from the same directory
                        competitors_data = self._load_competitor_files(parent_dir, data['profile']['username'])
                        if competitors_data:
                            data['competitor_posts'] = competitors_data
                            logger.info(f"Added {len(competitors_data)} competitor posts to the data")

                    return data

                logger.error("Failed to process Instagram data")
                return None

            elif isinstance(raw_data, dict) and 'posts' in raw_data and 'engagement_history' in raw_data:
                logger.info("Data already processed. Using directly.")
                return raw_data

            logger.error(f"Unsupported data format in {data_key}")
            return None

        except Exception as e:
            logger.error(f"Error processing social data from {data_key}: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return None
    
    def process_instagram_data(self, raw_data):
        """Process Instagram data into expected structure."""
        try:
            if not isinstance(raw_data, list) or not raw_data:
                logger.warning("Invalid Instagram data format")
                return None

            account_data = raw_data[0]
            logger.info(f"Instagram data keys: {list(account_data.keys())}")

            posts = []
            engagement_history = []

            if 'latestPosts' in account_data and isinstance(account_data['latestPosts'], list):
                instagram_posts = account_data['latestPosts']
                logger.info(f"Found {len(instagram_posts)} posts in latestPosts")

                for post in instagram_posts:
                    if 'childPosts' in post and post['childPosts']:
                        logger.info(f"Post {post.get('id', '')} has {len(post['childPosts'])} child posts")

                    post_obj = {
                        'id': post.get('id', ''),
                        'caption': post.get('caption', ''),
                        'hashtags': post.get('hashtags', []),
                        'engagement': 0,
                        'likes': post.get('likesCount', 0) or 0,
                        'comments': post.get('commentsCount', 0),
                        'timestamp': post.get('timestamp', ''),
                        'url': post.get('url', ''),
                        'type': post.get('type', ''),
                        'username': account_data.get('username', '')
                    }
                    post_obj['engagement'] = post_obj['likes'] + post_obj['comments']

                    if post_obj['caption']:
                        posts.append(post_obj)
                        if post.get('timestamp'):
                            engagement_history.append({
                                'timestamp': post.get('timestamp'),
                                'engagement': post_obj['engagement']
                            })

            logger.info(f"Processed {len(posts)} posts from Instagram data")

            if not posts:
                logger.warning("No posts extracted from Instagram data")
                now = datetime.now()
                for i in range(3):
                    timestamp = (now - pd.Timedelta(days=i)).strftime('%Y-%m-%dT%H:%M:%S.000Z')
                    engagement_history.append({
                        'timestamp': timestamp,
                        'engagement': 1000 - (i * 100)
                    })
                logger.info(f"Created {len(engagement_history)} synthetic engagement records")

            engagement_history.sort(key=lambda x: x['timestamp'])

            # Extract account type and posting style if available in account_data
            account_type = account_data.get('account_type', '')
            posting_style = account_data.get('posting_style', '')
            
            # Check if these values are missing but perhaps available in other fields
            if not account_type and 'accountType' in account_data:
                account_type = account_data.get('accountType', '')
                
            if not posting_style and 'postingStyle' in account_data:
                posting_style = account_data.get('postingStyle', '')

            # Auto-detect if this is a business/brand account based on Instagram fields
            is_business_account = False
            
            # Check Instagram's isBusinessAccount flag
            if account_data.get('isBusinessAccount', False):
                is_business_account = True
                logger.info(f"Detected business account from isBusinessAccount flag")
                
            # Check for business category name
            if account_data.get('businessCategoryName', ''):
                is_business_account = True
                logger.info(f"Detected business account from businessCategoryName: {account_data.get('businessCategoryName')}")
                
            # Check for verified status (often brands are verified)
            if account_data.get('verified', False):
                is_business_account = True
                logger.info(f"Detected business account from verified status")
                
            # Check follower count (large accounts are often brands)
            if account_data.get('followersCount', 0) > 100000:
                is_business_account = True
                logger.info(f"Detected likely business account from large follower count: {account_data.get('followersCount')}")
            
            # Set account type if auto-detected as business
            if is_business_account and (not account_type or account_type == 'unknown'):
                account_type = 'branding'
                logger.info(f"Setting account_type to 'branding' based on Instagram business indicators")

            processed_data = {
                'posts': posts,
                'engagement_history': engagement_history,
                'profile': {
                    'username': account_data.get('username', ''),
                    'fullName': account_data.get('fullName', ''),
                    'followersCount': account_data.get('followersCount', 0),
                    'followsCount': account_data.get('followsCount', 0),
                    'biography': account_data.get('biography', ''),
                    'account_type': account_type or account_data.get('account_type', 'unknown'),
                    'posting_style': posting_style or 'informative',  # Default to informative if not available
                    'isBusinessAccount': account_data.get('isBusinessAccount', False),
                    'businessCategoryName': account_data.get('businessCategoryName', ''),
                    'verified': account_data.get('verified', False)
                },
                'account_type': account_type or account_data.get('account_type', 'unknown'),
                'posting_style': posting_style or 'informative',  # Add at top level for easier access
                'primary_username': account_data.get('username', '')
            }
            return processed_data

        except Exception as e:
            logger.error(f"Error processing Instagram data: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return None

    def index_posts(self, posts, primary_username):
        """Index posts in the vector database with primary_username."""
        try:
            logger.info(f"Indexing {len(posts)} posts for {primary_username}")
            count = self.vector_db.add_posts(posts, primary_username)
            logger.info(f"Successfully indexed {count} posts")
            return count
        except Exception as e:
            logger.error(f"Error indexing posts: {str(e)}")
            return 0
    
    def analyze_engagement(self, data):
        """Analyze engagement data using time series analysis."""
        try:
            # If data is a list, assume it's a list of engagement values
            if isinstance(data, list):
                # Convert to dictionary with timestamps
                processed_data = {}
                for i, value in enumerate(data):
                    # Create timestamp as days from now
                    from datetime import datetime, timedelta
                    timestamp = (datetime.now() - timedelta(days=len(data) - i)).isoformat()
                    processed_data[timestamp] = value
                data = processed_data
            
            # Initialize time series analyzer if not already initialized
            if not hasattr(self, 'time_series') or self.time_series is None:
                self.time_series = TimeSeriesAnalyzer()
            
            # If data is empty, return a default result
            if not data:
                logger.warning("No engagement data to analyze")
                return {
                    "trend_detected": False,
                    "forecast": [],
                    "trending_periods": []
                }
            
            # Analyze engagement data
            return self.time_series.analyze_data(data)
        except Exception as e:
            logger.error(f"Error analyzing engagement: {str(e)}")
            return None
    
    def generate_content_plan(self, data, topics=None, n_recommendations=3):
        """Generate a content plan using updated RecommendationGenerator."""
        try:
            logger.info("Generating content plan")

            if not data or not data.get('posts'):
                logger.warning("No posts available for content plan generation")
                return None

            profile = data.get('profile', {})
            primary_username = profile.get('username', '')
            if not primary_username and 'primary_username' in data:
                primary_username = data.get('primary_username', '')
                
            if not primary_username:
                logger.error("No primary username found in profile")
                return None

            # Get competitor usernames from competitor_posts if available
            if 'competitor_posts' in data and data['competitor_posts']:
                # Extract unique usernames from competitor posts
                secondary_usernames = list(set(post['username'] for post in data['competitor_posts'] 
                                               if 'username' in post and post['username'] != primary_username))
                logger.info(f"Using {len(secondary_usernames)} competitor usernames from data: {secondary_usernames}")
            else:
                # Default fallback competitors
                secondary_usernames = ["anastasiabeverlyhills", "fentybeauty"]
                logger.info(f"No competitor posts found, using default competitor usernames: {secondary_usernames}")

            query = "summer makeup trends"
            if topics:
                query = " ".join(topics) if isinstance(topics, list) else topics
            elif data.get('engagement_history'):
                trending = self.recommendation_generator.generate_trending_topics(
                    {e['timestamp']: e['engagement'] for e in data['engagement_history']},
                    top_n=3
                )
                if trending:
                    topics = [trend['topic'] for trend in trending]
                    query = " ".join(topics)

            # Combine primary and competitor posts for analysis
            all_posts = data['posts'].copy()
            if 'competitor_posts' in data and data['competitor_posts']:
                all_posts.extend(data['competitor_posts'])
                logger.info(f"Combined {len(data['posts'])} primary posts with {len(data['competitor_posts'])} competitor posts for analysis")

            # Get account type and posting style
            account_type = data.get('account_type', '')
            posting_style = data.get('posting_style', '')
            
            if not account_type and profile.get('account_type'):
                account_type = profile.get('account_type')
                
            if not posting_style and profile.get('posting_style'):
                posting_style = profile.get('posting_style')
                
            logger.info(f"Content plan generation for account_type: {account_type}, posting_style: {posting_style}")

            content_plan = self.recommendation_generator.generate_content_plan(
                data={
                    'posts': all_posts,
                    'primary_username': primary_username,
                    'secondary_usernames': secondary_usernames,
                    'query': query,
                    'account_type': account_type,
                    'posting_style': posting_style,
                    'profile': profile,
                    'engagement_history': data.get('engagement_history', [])
                }
            )

            if not content_plan:
                logger.error("Failed to generate content plan")
                return None

            # Ensure username is explicitly added to content plan
            if 'profile' not in content_plan or 'username' not in content_plan.get('profile', {}):
                if 'profile' not in content_plan:
                    content_plan['profile'] = {}
                content_plan['profile']['username'] = primary_username
                logger.info(f"Added username {primary_username} to content plan profile")
                
            # Ensure account_type is explicitly set in content_plan
            content_plan['account_type'] = account_type
            logger.info(f"Set account_type to {account_type} in content plan")
            
            # Add primary_username field for easier access
            content_plan['primary_username'] = primary_username
            
            # Log content plan structure for debugging
            content_plan_keys = list(content_plan.keys())
            logger.info(f"Content plan contains the following sections: {content_plan_keys}")

            content_plan['profile_analysis'] = profile

            if 'trending_topics' in content_plan and content_plan['trending_topics']:
                topics = [t['topic'] for t in content_plan['trending_topics']]
                batch_recs = self.recommendation_generator.generate_batch_recommendations(
                    topics,
                    n_per_topic=n_recommendations
                )
                content_plan['batch_recommendations'] = batch_recs

            logger.info(f"Successfully generated content plan for {primary_username}")
            return content_plan
        except Exception as e:
            logger.error(f"Error generating content plan: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return None

    def save_content_plan(self, content_plan, filename='content_plan.json'):
        """Save content plan to a file."""
        try:
            logger.info(f"Saving content plan to {filename}")
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(content_plan, f, indent=2)
            logger.info(f"Successfully saved content plan to {filename}")
            # Add summary for verification
            summary = {
                "recommendations_count": len(content_plan.get("recommendations", [])),
                "competitor_analysis_count": len(content_plan.get("competitor_analysis", {}).keys()),
                "next_post_included": "next_post" in content_plan,
                "visual_prompt_included": bool(content_plan.get("next_post", {}).get("visual_prompt")),
                "prophet_analysis_included": any("forecast" in content_plan.get(key, {}) for key in content_plan)
            }
            logger.info(f"Content plan summary: {json.dumps(summary, indent=2)}")
            return True
        except Exception as e:
            logger.error(f"Error saving content plan: {str(e)}")
            return False

    def load_content_plan(self, filename='content_plan.json'):
        """Load content plan from a file."""
        try:
            logger.info(f"Loading content plan from {filename}")
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    content_plan = json.load(f)
                logger.info(f"Successfully loaded content plan from {filename}")
                return content_plan
            except FileNotFoundError:
                logger.warning(f"Content plan file {filename} not found, creating a default content plan")
                # Create a basic default content plan
                default_plan = {
                    'account_type': 'non-branding',
                    'recommendations': ["Create engaging content", "Use relevant hashtags"],
                    'next_post_prediction': {
                        'caption': 'Check out our latest updates!',
                        'hashtags': ['#Update', '#New']
                    }
                }
                return default_plan
        except Exception as e:
            logger.error(f"Error loading content plan: {str(e)}")
            # Return a minimal fallback content plan
            return {
                'account_type': 'non-branding',
                'recommendations': ["Error loading content plan"]
            }

    def export_content_plan_sections(self, content_plan):
        """Export content plan sections to R2 storage."""
        from datetime import datetime
        import json

        logger.info("Exporting content plan sections...")
        try:
            if not content_plan:
                logger.error("No content plan to export")
                return False
            
            # Determine account type from content plan
            is_branding = content_plan.get('account_type', '') == 'branding'
            
            logger.info(f"Exporting content plan for {'branding' if is_branding else 'non-branding'} account")
            
            # Get username - improved extraction with multiple fallbacks
            username = None
            # Try from profile_analysis
            if 'profile_analysis' in content_plan and 'username' in content_plan['profile_analysis']:
                username = content_plan['profile_analysis']['username']
            # Try from profile
            elif 'profile' in content_plan and 'username' in content_plan['profile']:
                username = content_plan['profile']['username']
            # Try from primary_username field
            elif 'primary_username' in content_plan:
                username = content_plan['primary_username']
            # Try from next_post_prediction
            elif 'next_post_prediction' in content_plan and 'username' in content_plan['next_post_prediction']:
                username = content_plan['next_post_prediction']['username']
                
            # If still no username, log warning and create one based on account type
            if not username:
                logger.warning("No username found in content plan, using fallback")
                timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
                username = f"account_{timestamp}"
                
                # Add username to content_plan for future reference
                if 'profile' not in content_plan:
                    content_plan['profile'] = {}
                content_plan['profile']['username'] = username
                
            logger.info(f"Using username: {username} for content plan export")
            
            # Ensure directories exist
            self._ensure_directory_exists(f"recommendations/{username}/")
            
            # Get competitor usernames for branding accounts
            competitor_usernames = []
            if is_branding:
                # Try to get competitor usernames from different sources with fallbacks
                if 'competitor_analysis' in content_plan and isinstance(content_plan['competitor_analysis'], dict):
                    competitor_usernames = list(content_plan['competitor_analysis'].keys())
                    logger.info(f"Found {len(competitor_usernames)} competitors in competitor_analysis: {competitor_usernames}")
                elif 'competitor_posts' in content_plan:
                    # Extract competitor usernames from posts
                    competitor_usernames = list(set(post.get('username') for post in content_plan['competitor_posts'] 
                                            if post.get('username') != username))
                    logger.info(f"Extracted {len(competitor_usernames)} competitors from competitor_posts")
                elif 'secondary_usernames' in content_plan:
                    competitor_usernames = content_plan.get('secondary_usernames', [])
                    logger.info(f"Using {len(competitor_usernames)} competitors from secondary_usernames")
                
                # If no competitors found, use default competitors
                if not competitor_usernames:
                    competitor_usernames = ['anastasiabeverlyhills', 'fentybeauty', 'toofaced', 'narsissist', 'urbandecaycosmetics']
                    # Remove primary username if it's in the list
                    if username in competitor_usernames:
                        competitor_usernames.remove(username)
                    logger.info(f"Using default competitors: {competitor_usernames[:3]}")
                    competitor_usernames = competitor_usernames[:3]  # Limit to top 3
                
                # Create competitor analysis directories for branding accounts
                for competitor in competitor_usernames:
                    competitor_dir = f"competitor_analysis/{username}/{competitor}/"
                    self._ensure_directory_exists(competitor_dir)
                    logger.info(f"Created competitor analysis directory for {competitor}")
            
            # Common directories for both account types
            self._ensure_directory_exists(f"next_posts/{username}/")
            
            # Non-branding specific directories
            if not is_branding:
                self._ensure_directory_exists(f"NewForYou/{username}/")
                self._ensure_directory_exists(f"engagement_strategies/{username}/")
            
            # Export content plan sections
            
            # 1. Export recommendations section
            recommendations_file_num = self._get_next_file_number("recommendations", username, "recommendation")
            recommendations_path = f"recommendations/{username}/recommendation_{recommendations_file_num}.json"
            
            # Format recommendations based on account type
            recommendations_data = {}
            if is_branding:
                # For branding accounts, include competitive analysis
                recommendations_data = {
                    "recommendations": content_plan.get('recommendations', []),
                    "competitive_strengths": self._extract_competitive_strengths(content_plan),
                    "competitive_opportunities": self._extract_competitive_opportunities(content_plan),
                    "differentiation_factors": self._extract_differentiation_factors(content_plan),
                    "counter_strategies": self._extract_counter_strategies(content_plan)
                }
            else:
                # For non-branding accounts, just include recommendations
                recommendations_data = {
                    "recommendations": content_plan.get('recommendations', []),
                    "trending_topics": content_plan.get('trending_topics', [])
                }
            
            # Upload recommendations
            r2_recommendations = self.r2_storage.upload_file(
                key=recommendations_path,
                file_obj=io.BytesIO(json.dumps(recommendations_data, indent=2).encode('utf-8')),
                bucket='tasks'
            )
            
            if r2_recommendations:
                logger.info(f"Enhanced recommendations export successful to {recommendations_path}")
            else:
                logger.error(f"Failed to export recommendations to {recommendations_path}")
                return False
            
            # 2. Export competitor analysis for branding accounts
            if is_branding:
                # Generate competitor analysis if it doesn't exist in content plan
                competitor_analysis = content_plan.get('competitor_analysis', {})
                if not competitor_analysis:
                    logger.info("Generating competitor analysis as it's missing from content plan")
                    competitor_analysis = self._generate_competitor_analysis(content_plan, competitor_usernames)
                
                # Export analysis for each competitor
                for competitor, analysis in competitor_analysis.items():
                    competitor_path = f"competitor_analysis/{username}/{competitor}/"
                    analysis_file_num = self._get_next_file_number("competitor_analysis", f"{username}/{competitor}", "analysis")
                    analysis_path = f"{competitor_path}analysis_{analysis_file_num}.json"
                    
                    # Format competitor analysis
                    competitor_data = {
                        "competitor": competitor,
                        "strengths": self._extract_competitor_strengths(analysis, competitor),
                        "weaknesses": self._extract_competitor_weaknesses(analysis, competitor),
                        "opportunities": self._extract_exploitation_opportunities(analysis, content_plan.get('recommendations', [])),
                        "counter_tactics": self._extract_counter_tactics(competitor, content_plan),
                        "engagement_comparison": self._compare_engagement_metrics(content_plan, competitor),
                        "content_style_comparison": self._compare_content_style(content_plan, competitor),
                        "audience_overlap": self._analyze_audience_overlap(content_plan, competitor),
                        "brand_positioning": self._analyze_brand_positioning(content_plan, competitor)
                    }
                    
                    # Upload competitor analysis
                    r2_competitor = self.r2_storage.upload_file(
                        key=analysis_path,
                        file_obj=io.BytesIO(json.dumps(competitor_data, indent=2).encode('utf-8')),
                        bucket='tasks'
                    )
                    
                    if r2_competitor:
                        logger.info(f"Enhanced competitor analysis for {competitor} successful to {analysis_path}")
                    else:
                        logger.error(f"Failed to export competitor analysis for {competitor}")
            
            # 3. Export engagement strategies for non-branding accounts
            if not is_branding and 'engagement_strategies' in content_plan:
                strategies_file_num = self._get_next_file_number("engagement_strategies", username, "strategies")
                strategies_path = f"engagement_strategies/{username}/strategies_{strategies_file_num}.json"
                
                # Format engagement strategies
                strategies_data = {
                    "engagement_strategies": content_plan.get('engagement_strategies', []),
                    "posting_trends": content_plan.get('posting_trends', {})
                }
                
                # Upload engagement strategies
                r2_strategies = self.r2_storage.upload_file(
                    key=strategies_path,
                    file_obj=io.BytesIO(json.dumps(strategies_data, indent=2).encode('utf-8')),
                    bucket='tasks'
                )
                
                if r2_strategies:
                    logger.info(f"Engagement strategies export successful to {strategies_path}")
                else:
                    logger.error(f"Failed to export engagement strategies")
            
            # 4. Export next post for both account types
            next_post_file_num = self._get_next_file_number("next_posts", username, "post")
            next_post_path = f"next_posts/{username}/post_{next_post_file_num}.json"
            
            # Get next post data
            next_post_data = content_plan.get('next_post_prediction', {})
            
            # Upload next post
            r2_next_post = self.r2_storage.upload_file(
                key=next_post_path,
                file_obj=io.BytesIO(json.dumps(next_post_data, indent=2).encode('utf-8')),
                bucket='tasks'
            )
            
            if r2_next_post:
                logger.info(f"Next post export successful to {next_post_path}")
            else:
                logger.error(f"Failed to export next post")
                return False
            
            # 5. Export news articles for non-branding accounts
            if not is_branding and 'news_articles' in content_plan:
                news_articles = content_plan.get('news_articles', [])
                exported_count = 0
                
                for i, article in enumerate(news_articles):
                    news_file_num = self._get_next_file_number("NewForYou", username, "News")
                    news_path = f"NewForYou/{username}/News_{news_file_num}.json"
                    
                    # Upload news article
                    r2_news = self.r2_storage.upload_file(
                        key=news_path,
                        file_obj=io.BytesIO(json.dumps(article, indent=2).encode('utf-8')),
                        bucket='tasks'
                    )
                    
                    if r2_news:
                        logger.info(f"News article {i+1} export successful to {news_path}")
                        exported_count += 1
                    else:
                        logger.error(f"Failed to export news article {i+1}")
                
                logger.info(f"Exported {exported_count} news articles")
            
            logger.info("All enhanced content plan sections exported successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error exporting content plan sections: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return False

    def _generate_competitor_analysis(self, content_plan, competitor_usernames):
        """Generate competitor analysis data if it's missing from content plan."""
        try:
            competitor_analysis = {}
            primary_username = content_plan.get('primary_username', '')
            
            # Get competitor posts if available
            competitor_posts = {}
            if 'competitor_posts' in content_plan:
                # Group posts by username
                for post in content_plan.get('competitor_posts', []):
                    username = post.get('username', '')
                    if username and username != primary_username:
                        if username not in competitor_posts:
                            competitor_posts[username] = []
                        competitor_posts[username].append(post)
            
            # Generate analysis for each competitor
            for competitor in competitor_usernames:
                if competitor == primary_username:
                    continue
                    
                # Start with a basic analysis structure
                analysis = {
                    "competitor": competitor,
                    "overview": f"Analysis of {competitor} as a competitor to {primary_username}",
                    "post_count": 0,
                    "avg_engagement": 0,
                    "content_themes": [],
                    "posting_frequency": "unknown",
                    "strengths": [],
                    "weaknesses": []
                }
                
                # Add data from competitor posts if available
                if competitor in competitor_posts and competitor_posts[competitor]:
                    posts = competitor_posts[competitor]
                    analysis["post_count"] = len(posts)
                    
                    # Calculate average engagement
                    total_engagement = sum(post.get('engagement', 0) for post in posts)
                    avg_engagement = total_engagement / len(posts) if posts else 0
                    analysis["avg_engagement"] = round(avg_engagement, 2)
                    
                    # Extract content themes from captions
                    all_captions = " ".join([post.get('caption', '') for post in posts])
                    hashtags = []
                    for post in posts:
                        hashtags.extend(post.get('hashtags', []))
                    
                    if hashtags:
                        # Count most common hashtags
                        hashtag_counts = {}
                        for tag in hashtags:
                            hashtag_counts[tag] = hashtag_counts.get(tag, 0) + 1
                        
                        # Get top themes based on hashtags
                        top_hashtags = sorted(hashtag_counts.items(), key=lambda x: x[1], reverse=True)[:5]
                        analysis["content_themes"] = [tag for tag, count in top_hashtags]
                    
                    # Determine posting frequency if timestamps available
                    timestamps = [post.get('timestamp') for post in posts if post.get('timestamp')]
                    if len(timestamps) >= 2:
                        # Sort timestamps
                        timestamps.sort()
                        # Calculate average days between posts
                        date_format = "%Y-%m-%dT%H:%M:%S.%fZ"
                        try:
                            dates = [datetime.strptime(ts, date_format) for ts in timestamps]
                            if len(dates) >= 2:
                                time_diffs = [(dates[i+1] - dates[i]).days for i in range(len(dates)-1)]
                                avg_days = sum(time_diffs) / len(time_diffs)
                                
                                if avg_days < 1:
                                    analysis["posting_frequency"] = "multiple times daily"
                                elif avg_days < 2:
                                    analysis["posting_frequency"] = "daily"
                                elif avg_days < 8:
                                    analysis["posting_frequency"] = f"every {round(avg_days)} days"
                                else:
                                    analysis["posting_frequency"] = f"approximately {round(avg_days)} days apart"
                        except Exception as e:
                            logger.warning(f"Error calculating posting frequency: {str(e)}")
                    
                    # Generate strengths based on engagement
                    if avg_engagement > 5000:
                        analysis["strengths"].append(f"Exceptional engagement rate averaging {round(avg_engagement)} per post")
                    elif avg_engagement > 1000:
                        analysis["strengths"].append(f"Strong engagement averaging {round(avg_engagement)} per post")
                    
                    # Generate weakness if low engagement
                    if avg_engagement < 500:
                        analysis["weaknesses"].append(f"Low engagement averaging only {round(avg_engagement)} per post")
                
                # Add detailed analysis text
                analysis["text"] = self._generate_competitor_analysis_text(analysis, primary_username)
                
                # Add to competitor_analysis dictionary
                competitor_analysis[competitor] = analysis
            
            return competitor_analysis
            
        except Exception as e:
            logger.error(f"Error generating competitor analysis: {str(e)}")
            return {}
    
    def _generate_competitor_analysis_text(self, analysis, primary_username):
        """Generate detailed analysis text from structured competitor analysis."""
        try:
            competitor = analysis.get("competitor", "competitor")
            overview = f"Competitor Analysis: {competitor}\n\n"
            
            # Add post count and frequency
            post_count = analysis.get("post_count", 0)
            if post_count > 0:
                overview += f"Based on analysis of {post_count} posts, "
                frequency = analysis.get("posting_frequency", "unknown")
                if frequency != "unknown":
                    overview += f"{competitor} posts {frequency}. "
                else:
                    overview += f"{competitor} has an irregular posting schedule. "
            
            # Add engagement analysis
            avg_engagement = analysis.get("avg_engagement", 0)
            if avg_engagement > 0:
                if avg_engagement > 5000:
                    overview += f"They achieve exceptional engagement averaging {round(avg_engagement)} per post. "
                elif avg_engagement > 1000:
                    overview += f"They have good engagement with an average of {round(avg_engagement)} per post. "
                else:
                    overview += f"Their engagement averages {round(avg_engagement)} per post. "
            
            # Add content themes
            themes = analysis.get("content_themes", [])
            if themes:
                overview += f"\nContent themes: {', '.join(themes)}. "
            
            # Add strengths
            strengths = analysis.get("strengths", [])
            if strengths:
                overview += "\n\nStrengths:\n"
                for strength in strengths:
                    overview += f"- {strength}\n"
            
            # Add weaknesses
            weaknesses = analysis.get("weaknesses", [])
            if weaknesses:
                overview += "\nWeaknesses:\n"
                for weakness in weaknesses:
                    overview += f"- {weakness}\n"
            
            # Add comparison with primary account
            overview += f"\nCompared to {primary_username}, {competitor} "
            
            if not strengths and not weaknesses:
                overview += f"appears to be a significant competitor in the same market space."
            elif strengths and not weaknesses:
                overview += f"has several strengths that should be monitored."
            elif not strengths and weaknesses:
                overview += f"has some weaknesses that create opportunities."
            else:
                overview += f"presents both competitive threats and opportunities."
            
            return overview
            
        except Exception as e:
            logger.error(f"Error generating competitor analysis text: {str(e)}")
            return f"Analysis of {analysis.get('competitor', 'competitor')} (Error generating detailed text)"
    
    def _compare_engagement_metrics(self, content_plan, competitor):
        """Compare engagement metrics between primary account and competitor."""
        try:
            primary_username = content_plan.get('primary_username', '')
            primary_posts = content_plan.get('posts', [])
            competitor_posts = [post for post in content_plan.get('competitor_posts', []) 
                               if post.get('username') == competitor]
            
            if not primary_posts or not competitor_posts:
                return {
                    "comparison": "Insufficient data for detailed engagement comparison",
                    "recommendation": "Monitor competitor posts more closely to gather engagement data"
                }
            
            # Calculate average engagement
            primary_engagement = sum(post.get('engagement', 0) for post in primary_posts) / len(primary_posts) if primary_posts else 0
            competitor_engagement = sum(post.get('engagement', 0) for post in competitor_posts) / len(competitor_posts) if competitor_posts else 0
            
            engagement_diff = primary_engagement - competitor_engagement
            engagement_ratio = primary_engagement / competitor_engagement if competitor_engagement else float('inf')
            
            comparison = {}
            
            if engagement_diff > 0:
                comparison["result"] = f"Your account has higher average engagement ({round(primary_engagement)}) compared to {competitor} ({round(competitor_engagement)})"
                comparison["advantage"] = f"{round(abs(engagement_diff))} more engagements per post"
                comparison["percentage"] = f"{round((engagement_ratio - 1) * 100)}% higher engagement rate"
                comparison["recommendation"] = "Maintain current engagement strategy while exploring new content formats"
            else:
                comparison["result"] = f"{competitor} has higher average engagement ({round(competitor_engagement)}) compared to your account ({round(primary_engagement)})"
                comparison["disadvantage"] = f"{round(abs(engagement_diff))} fewer engagements per post"
                comparison["percentage"] = f"{round((1 - 1/engagement_ratio) * 100)}% lower engagement rate"
                comparison["recommendation"] = "Study their top-performing content and adapt engagement tactics"
            
            return comparison
            
        except Exception as e:
            logger.error(f"Error comparing engagement metrics: {str(e)}")
            return {"comparison": "Error analyzing engagement metrics", "recommendation": "Manual analysis recommended"}
    
    def _compare_content_style(self, content_plan, competitor):
        """Compare content styling and approach between primary account and competitor."""
        try:
            primary_username = content_plan.get('primary_username', '')
            primary_posts = content_plan.get('posts', [])
            competitor_posts = [post for post in content_plan.get('competitor_posts', []) 
                               if post.get('username') == competitor]
            
            if not primary_posts or not competitor_posts:
                return {
                    "comparison": "Insufficient data for content style comparison",
                    "recommendation": "Gather more posts to analyze content styles"
                }
            
            # Extract primary hashtags
            primary_hashtags = []
            for post in primary_posts:
                primary_hashtags.extend(post.get('hashtags', []))
            
            # Extract competitor hashtags
            competitor_hashtags = []
            for post in competitor_posts:
                competitor_hashtags.extend(post.get('hashtags', []))
            
            # Find common and unique hashtags
            common_hashtags = set(primary_hashtags).intersection(set(competitor_hashtags))
            primary_unique = set(primary_hashtags).difference(set(competitor_hashtags))
            competitor_unique = set(competitor_hashtags).difference(set(primary_hashtags))
            
            style_comparison = {
                "common_themes": list(common_hashtags)[:5],
                "your_unique_themes": list(primary_unique)[:5],
                "competitor_unique_themes": list(competitor_unique)[:5],
                "content_focus_recommendation": f"Emphasize your unique themes like {', '.join(list(primary_unique)[:3]) if primary_unique else 'product innovation'} while exploring {competitor}'s successful content areas"
            }
            
            return style_comparison
            
        except Exception as e:
            logger.error(f"Error comparing content styles: {str(e)}")
            return {"comparison": "Error analyzing content styles", "recommendation": "Manual content analysis recommended"}
    
    def _analyze_audience_overlap(self, content_plan, competitor):
        """Analyze potential audience overlap based on content themes."""
        # This is a simplified version since we don't have actual audience data
        try:
            # Extract themes from content plan
            primary_themes = []
            if 'profile' in content_plan:
                profile_bio = content_plan.get('profile', {}).get('biography', '')
                if profile_bio:
                    bio_words = profile_bio.lower().split()
                    primary_themes = [word for word in bio_words if len(word) > 5][:5]
            
            return {
                "estimated_overlap": "Medium to High",
                "target_audience": "Beauty enthusiasts and makeup professionals",
                "audience_differentiation": "Focus on your unique brand positioning and product specialties",
                "engagement_strategy": "Create content that highlights your unique selling points while maintaining consistent posting schedule"
            }
            
        except Exception as e:
            logger.error(f"Error analyzing audience overlap: {str(e)}")
            return {"estimated_overlap": "Unknown", "recommendation": "Consider market research to better understand audience overlap"}
    
    def _analyze_brand_positioning(self, content_plan, competitor):
        """Analyze brand positioning compared to competitor."""
        try:
            return {
                "market_position": "Direct competitor in beauty/cosmetics space",
                "brand_perception": "Professional-grade makeup with focus on quality and innovation",
                "differentiation_opportunity": "Emphasize your unique product innovations, color range, and brand story",
                "positioning_recommendation": "Highlight what makes your brand unique in an increasingly competitive market"
            }
            
        except Exception as e:
            logger.error(f"Error analyzing brand positioning: {str(e)}")
            return {"market_position": "Direct competitor", "recommendation": "Further brand analysis recommended"}

    def _ensure_directory_exists(self, directory_path):
        """Create directory marker in R2 if it doesn't exist.
        
        Args:
            directory_path (str): Path of the directory to create
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Add trailing slash for directory marker
            if not directory_path.endswith('/'):
                directory_path += '/'

            # Check if directory exists
            objects = self.r2_storage.list_objects(prefix=directory_path)
            if objects:
                logger.info(f"Directory {directory_path} already exists")
                return True

            # Create directory marker
            success = self.r2_storage.put_object(directory_path)
            if success:
                logger.info(f"Created directory marker for {directory_path}")
            
            else:
                logger.error(f"Failed to create directory marker for {directory_path}")
            return success
        except Exception as e:
            logger.error(f"Error creating directory {directory_path}: {str(e)}")
            return False

    def _get_next_file_number(self, base_dir, path_segment, file_prefix):
        """Find the next available file number for sequential numbering.
        
        Args:
            base_dir: Base directory (e.g., 'recommendations', 'competitor_analysis', 'next_posts')
            path_segment: Path segment after the base directory (e.g., username or username/competitor)
            file_prefix: Prefix for the filename (e.g., 'recommendation', 'analysis', 'post')
            
        Returns:
            int: Next available file number
        """
        try:
            # List objects in the directory
            prefix = f"{base_dir}/{path_segment}/"
            objects = self.r2_storage.list_objects(prefix=prefix)

            if not objects:
                return 1

            # Extract file numbers from existing files
            file_numbers = []
            pattern = rf"{file_prefix}_(\d+)\.json"

            for obj in objects:
                if not obj or 'Key' not in obj:
                    continue

                key = obj['Key']
                filename = key.split('/')[-1]
                match = re.search(pattern, filename)

                if match:
                    try:
                        file_numbers.append(int(match.group(1)))
                    except ValueError:
                        continue

            # Return next number or 1 if no files exist
            return max(file_numbers) + 1 if file_numbers else 1

        except Exception as e:
            logger.error(f"Error determining next file number: {str(e)}")
            return 1
    
    def run_pipeline(self, object_key=None, data=None):
        """Run the full pipeline."""
        try:
            if object_key:
                data = self.process_social_data(object_key)
            
            if not data:
                logger.error("No data available for processing")
                return False
            
            # Validate data structure
            if not self.validate_data_structure(data):
                logger.error("Invalid data structure")
                return False
            
            # Extract basic information from data
            account_type = data.get('account_type', 'unknown')
            posting_style = data.get('posting_style', '')
            
            # Check for additional indicators of a branding account
            is_business_or_brand = False
            
            # Check if profile has business indicators
            if 'profile' in data:
                profile = data['profile']
                # Check biography for brand indicators
                biography = profile.get('biography', '').lower()
                brand_keywords = ['official', 'cosmetics', 'beauty', 'makeup', 'skincare', 'brand', 'shop', 'product', 'collection']
                if any(keyword in biography for keyword in brand_keywords):
                    is_business_or_brand = True
                    logger.info(f"Detected branding account from biography containing brand keywords")
                
                # Check business category
                if profile.get('businessCategoryName') or profile.get('is_business', False) or profile.get('isBusinessAccount', False):
                    is_business_or_brand = True
                    logger.info(f"Detected branding account from business category indicators")
            
            # Check if brand or business is mentioned in the processed metadata
            if 'branding' in account_type.lower() or 'business' in account_type.lower() or 'brand' in account_type.lower():
                is_business_or_brand = True
                logger.info(f"Detected branding account from account_type: {account_type}")
            
            # Special case for well-known cosmetics brands
            cosmetics_brands = [
                'urbandecaycosmetics', 'urbandecay', 'maccosmetics', 'mac', 'fentybeauty', 'fenty', 
                'anastasiabeverlyhills', 'toofaced', 'narsissist', 'nars', 'tarte', 'tartecosmetics',
                'hourglasscosmetics', 'hourglassmakeup', 'ctilburymakeup', 'charlottetilbury'
            ]
            
            # Get primary username
            primary_username = None
            if 'primary_username' in data:
                primary_username = data.get('primary_username')
            elif 'profile' in data and 'username' in data['profile']:
                primary_username = data['profile']['username']
                
            if primary_username and any(brand in primary_username.lower() for brand in cosmetics_brands):
                is_business_or_brand = True
                logger.info(f"Detected branding account based on known cosmetics brand name: {primary_username}")
                
            # Set final account type
            if is_business_or_brand:
                account_type = 'branding'
                logger.info("Account explicitly identified as branding based on multiple indicators")
            else:
                # Determine if this is a branding account based on explicit account_type
                is_branding = account_type.lower() in ['branding', 'business', 'business/brand', 'brand']
                
                if is_branding:
                    account_type = 'branding'
                    logger.info("Account identified as branding")
                else:
                    account_type = 'non-branding'
                    logger.info("Account identified as non-branding")
                    
            # Make sure account_type is properly set in the data
            data['account_type'] = account_type
            is_branding = account_type.lower() == 'branding'
                
            if not primary_username:
                logger.error("No primary username found in data")
                return False
                
            posts = data.get('posts', [])
            
            # Index posts in the vector database
            logger.info(f"Indexing {len(posts)} posts for {primary_username}")
            if not self.index_posts(posts, primary_username):
                logger.error("Failed to index posts")
                return False
            logger.info(f"Successfully indexed {len(posts)} posts")
            
            # Process engagement data
            engagement_data = data.get('engagement_history', [])
            
            # Log statistics about indexed data
            competitors = data.get('secondary_usernames', [])
            logger.info(f"Total posts indexed: {len(posts)} (Primary: {len(posts)}, Competitors: {len(competitors)})")
            
            # Analyze engagement data (common for both types)
            logger.info("Analyzing engagement data")
            engagement_analysis = self.analyze_engagement(engagement_data)
            if not engagement_analysis:
                logger.error("Failed to analyze engagement data")
                return False
            logger.info("Successfully analyzed engagement data")
            
            # Set default posting style if not specified for non-branding accounts
            if not is_branding and not posting_style:
                posting_style = "informative"
                logger.info(f"Non-branding account without posting_style specified, using default")
            
            # Generate content plan based on account type
            logger.info("Generating content plan")
            
            # If no competitor usernames, use default competitors for branding accounts
            if is_branding and not competitors:
                default_competitors = ['anastasiabeverlyhills', 'fentybeauty', 'toofaced', 'narsissist', 'urbandecaycosmetics']
                competitors = default_competitors[:3]  # Use first 3 default competitors
                logger.info(f"No competitor posts found, using default competitor usernames: {competitors}")
            elif not is_branding and not competitors:
                default_competitors = ['anastasiabeverlyhills', 'fentybeauty']
                competitors = default_competitors
                logger.info(f"No competitor posts found, using default competitor usernames: {competitors}")
            
            # Use time series analysis for both types (common functionality)
            if engagement_data:
                time_series = TimeSeriesAnalyzer()
                time_series_results = time_series.analyze_data(engagement_data)
                data['time_series_results'] = time_series_results
            
            # Update data with necessary fields for content generation
            data['is_branding'] = is_branding
            if posting_style:
                data['posting_style'] = posting_style
            
            # Generate content plan with the recommendation generator
            logger.info(f"Content plan generation for account_type: {account_type}, posting_style: {posting_style}")
            content_plan = self.generate_content_plan(data)
            
            if not content_plan:
                logger.error("Failed to generate content plan")
                return False
            
            logger.info(f"Successfully generated content plan for {primary_username}")
            
            # Save content plan
            if not self.save_content_plan(content_plan):
                logger.error("Failed to save content plan")
                return False
            
            # Generate summary stats
            recommendations_count = 0
            if isinstance(content_plan.get('recommendations'), list):
                recommendations_count = len(content_plan.get('recommendations', []))
            elif isinstance(content_plan.get('recommendations'), dict):
                for topic, recs in content_plan.get('recommendations', {}).items():
                    if isinstance(recs, list):
                        recommendations_count += len(recs)
            
            competitor_analysis_count = len(content_plan.get('competitor_analysis', {}))
            next_post_included = 'next_post_prediction' in content_plan
            visual_prompt_included = False
            if next_post_included:
                next_post = content_plan.get('next_post_prediction', {})
                visual_prompt_included = 'visual_prompt' in next_post or 'image_prompt' in next_post
            
            prophet_analysis_included = 'trending_topics' in content_plan
            
            content_plan_summary = {
                "recommendations_count": recommendations_count,
                "competitor_analysis_count": competitor_analysis_count,
                "next_post_included": next_post_included,
                "visual_prompt_included": visual_prompt_included,
                "prophet_analysis_included": prophet_analysis_included
            }
            
            logger.info(f"Content plan summary: {json.dumps(content_plan_summary, indent=2)}")
            
            # Export content plan to R2
            logger.info("Starting content plan export")
            # Export based on account type - this is where we need to separate the flows
            if is_branding:
                logger.info("Exporting content plan for branding account")
                # For branding accounts - export competitor analysis, recommendations, strategies
                if not self.export_content_plan_sections(content_plan):
                    logger.error("Failed to export content plan sections")
                    return False
            else:
                logger.info("Exporting content plan for non-branding account")
                # For non-branding accounts - export news articles, recommendations, next post
                if not self.export_content_plan_sections(content_plan):
                    logger.error("Failed to export content plan sections")
                    return False

            logger.info("Pipeline completed successfully")
            
            print("\n==================================================")
            print(f"PROCESSING RESULTS FOR {primary_username}")
            print("==================================================")
            print(f"Success: Content plan generated successfully")
            print(f"Posts analyzed: {len(posts)}")
            print(f"Recommendations generated: {recommendations_count}")
            print(f"Account type: {'Branding' if is_branding else 'Non-branding'}")
            
            return {
                "success": True,
                "posts_analyzed": len(posts),
                "recommendations_count": recommendations_count,
                "account_type": "branding" if is_branding else "non-branding"
            }
            
        except Exception as e:
            logger.error(f"Error in pipeline: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return False

    def handle_new_business_account(self, data):
        """Generate initial content suggestions for new business accounts."""
        try:
            suggestions = {
                "recommendations": [
                    "Create introductory posts about your business",
                    "Share your brand story and mission",
                    "Post product/service highlights"
                ],
                "content_plan": {
                    "first_week": [
                        "Day 1: Brand introduction",
                        "Day 3: Product showcase",
                        "Day 5: Customer testimonial request"
                    ]
                }
            }
            return {
                "success": True,
                "message": "Generated initial content suggestions",
                "suggestions": suggestions
            }
        except Exception as e:
            return {"success": False, "message": str(e)}

    def validate_data_structure(self, data):
        """Validate data structure for both primary account and competitors."""
        try:
            # Basic validation of top-level keys
            if not all(key in data for key in ['posts', 'engagement_history']):
                missing_keys = [key for key in ['posts', 'engagement_history'] if key not in data]
                logger.warning(f"Missing required top-level keys in data: {missing_keys}")
                return False

            # Validate posts array
            if not data['posts'] or not isinstance(data['posts'], list):
                logger.warning("Posts array is empty or not a list")
                return False

            # Validate engagement history
            if not data['engagement_history'] or not isinstance(data['engagement_history'], list):
                logger.warning("Engagement history is empty or not a list")
                return False

            # Validate post structure
            required_post_fields = ['id', 'caption', 'engagement']
            if not any(all(field in post for field in required_post_fields) for post in data['posts']):
                logger.warning("No posts with all required fields")
                return False

            # Validate engagement history structure
            required_history_fields = ['timestamp', 'engagement']
            if not all(all(field in record for field in required_history_fields) for record in data['engagement_history']):
                logger.warning("Engagement history missing required fields")
                return False

            # Validate profile data if present
            if 'profile' in data:
                if not isinstance(data['profile'], dict):
                    logger.warning("Profile is not a dictionary")
                    return False
                if 'username' not in data['profile']:
                    logger.warning("Profile missing username field")
                    return False

            # Validate competitor posts if present
            if 'competitor_posts' in data:
                if not isinstance(data['competitor_posts'], list):
                    logger.warning("Competitor posts is not a list")
                    return False
                if data['competitor_posts']:
                    # Check at least one competitor post has required fields
                    comp_has_valid = False
                    for post in data['competitor_posts']:
                        if all(field in post for field in required_post_fields + ['username']):
                            comp_has_valid = True
                            break
                    if not comp_has_valid:
                        logger.warning("No valid competitor posts found")
                        return False

            logger.info("Data structure validation passed")
            return True
        except Exception as e:
            logger.error(f"Error validating data structure: {str(e)}")
            return False

    def create_sample_data(self, use_file=False):
        """Create sample data when real data isn't available."""
        try:
            logger.info("Creating sample data")
            now = datetime.now()
            posts = [
                {
                    'id': '1',
                    'caption': 'Summer fashion trends for 2025 #SummerFashion',
                    'hashtags': ['#SummerFashion', '#Trending'],
                    'engagement': 1200,
                    'likes': 1000,
                    'comments': 200,
                    'timestamp': now.strftime('%Y-%m-%dT%H:%M:%S.000Z'),
                    'url': 'https://example.com/post1',
                    'type': 'Image',
                    'username': 'sample_user'
                },
                {
                    'id': '2',
                    'caption': 'New product launch! #NewProduct',
                    'hashtags': ['#NewProduct', '#Promotion'],
                    'engagement': 800,
                    'likes': 700,
                    'comments': 100,
                    'timestamp': (now - pd.Timedelta(days=1)).strftime('%Y-%m-%dT%H:%M:%S.000Z'),
                    'url': 'https://example.com/post2',
                    'type': 'Image',
                    'username': 'sample_user'
                }
            ]
            engagement_history = [
                {'timestamp': p['timestamp'], 'engagement': p['engagement']} for p in posts
            ]
            profile = {
                'username': 'sample_user',
                'fullName': 'Sample User',
                'followersCount': 10000,
                'followsCount': 500,
                'biography': 'Testing profile.',
                'account_type': 'unknown'
            }
            data = {'posts': posts, 'engagement_history': engagement_history, 'profile': profile}
            logger.info(f"Created sample data with {len(posts)} posts")
            return data
        except Exception as e:
            logger.error(f"Error creating sample data: {str(e)}")
            return {'posts': [], 'engagement_history': [], 'profile': {}}

    def process_instagram_username(self, username, results_limit=10):
        """Process an Instagram username and return object_key."""
        try:
            logger.info(f"Processing Instagram username: {username}")
            scraper = InstagramScraper()
            scrape_result = scraper.scrape_and_upload(username, results_limit)

            if not scrape_result["success"]:
                logger.warning(f"Failed to scrape profile for {username}: {scrape_result['message']}")
                return {"success": False, "message": scrape_result['message']}

            object_key = scrape_result["object_key"]
            pipeline_result = self.run_pipeline(object_key=object_key)

            if not pipeline_result["success"]:
                logger.warning(f"Failed to generate recommendations for {username}")
                return {
                    "success": False,
                    "message": "Failed to generate recommendations",
                    "details": pipeline_result
                }

            return {
                "success": True,
                "message": "Successfully generated recommendations",
                "details": pipeline_result,
                "content_plan_file": "content_plan.json",
                "object_key": object_key
            }
        except Exception as e:
            logger.error(f"Error processing Instagram username {username}: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return {"success": False, "message": str(e)}

    def _load_competitor_files(self, parent_dir, primary_username):
        """Load and process competitor files from the same directory."""
        try:
            competitor_posts = []

            # List objects in the parent directory
            objects = self.data_retriever.list_objects(prefix=f"{parent_dir}/")

            for obj in objects:
                key = obj['Key']
                # Skip the primary user's file
                if key.endswith('.json') and f"{parent_dir}/{primary_username}.json" != key:
                    logger.info(f"Processing competitor file: {key}")
                    competitor_data = self.data_retriever.get_json_data(key)

                    if competitor_data and isinstance(competitor_data, list) and competitor_data and 'latestPosts' in competitor_data[0]:
                        # Extract the competitor username from the filename
                        competitor_filename = key.split('/')[-1]
                        competitor_username = competitor_filename.replace('.json', '')

                        # Process the competitor posts
                        if 'latestPosts' in competitor_data[0] and isinstance(competitor_data[0]['latestPosts'], list):
                            competitor_posts_data = competitor_data[0]['latestPosts']

                            for post in competitor_posts_data:
                                post_obj = {
                                    'id': post.get('id', ''),
                                    'caption': post.get('caption', ''),
                                    'hashtags': post.get('hashtags', []),
                                    'engagement': 0,
                                    'likes': post.get('likesCount', 0) or 0,
                                    'comments': post.get('commentsCount', 0),
                                    'timestamp': post.get('timestamp', ''),
                                    'url': post.get('url', ''),
                                    'type': post.get('type', ''),
                                    'username': competitor_username  # Set the correct competitor username
                                }
                                post_obj['engagement'] = post_obj['likes'] + post_obj['comments']

                                if post_obj['caption']:
                                    competitor_posts.append(post_obj)

            logger.info(f"Loaded {len(competitor_posts)} posts from competitor files")
            return competitor_posts

        except Exception as e:
            logger.error(f"Error loading competitor files: {str(e)}")
            return []

    def _extract_competitive_strengths(self, content_plan):
        """Extract competitive strengths from the content plan."""
        try:
            # Handle the case where primary_analysis is None
            if 'primary_analysis' not in content_plan or content_plan['primary_analysis'] is None:
                logger.info("No primary_analysis found in content plan for extracting competitive strengths")
                return ["Brand recognition"]

            primary_analysis = content_plan['primary_analysis']
            
            # Handle case where primary_analysis is a string (not a dictionary)
            if isinstance(primary_analysis, str):
                # Try to extract strengths from the text
                if "strength" in primary_analysis.lower():
                    logger.info("Extracting strengths from primary_analysis string")
                    # Split by sentences and find sentences with "strength"
                    sentences = primary_analysis.split('. ')
                    strength_sentences = [s for s in sentences if "strength" in s.lower()]
                    if strength_sentences:
                        return [strength_sentences[0]]
                return ["Brand recognition"] 
            
            # Continue with normal processing (primary_analysis is a dictionary)
            strengths = []
            
            # Try to get strengths directly from the competitive_strengths list
            if 'competitive_strengths' in primary_analysis and isinstance(primary_analysis['competitive_strengths'], list):
                return primary_analysis['competitive_strengths']
            
            # Try to extract from analysis text
            if 'analysis' in primary_analysis and isinstance(primary_analysis['analysis'], str):
                analysis_text = primary_analysis['analysis']
                
                # Look for strengths in the analysis text
                if "strength" in analysis_text.lower():
                    sentences = analysis_text.split('. ')
                    strength_sentences = [s for s in sentences if "strength" in s.lower()]
                    strengths.extend(strength_sentences)
            
            # Add a default strength if none found
            if not strengths:
                strengths = ["Brand recognition"]
                
            return strengths
                
        except Exception as e:
            logger.error(f"Error extracting competitive strengths: {str(e)}")
            return ["Brand recognition (Error)"]

    def _extract_competitive_opportunities(self, content_plan):
        """Extract competitive opportunities from content plan."""
        try:
            opportunities = []
            recommendations = content_plan.get('recommendations', '')

            if isinstance(recommendations, str):
                # Look for opportunity markers
                opportunity_markers = ['opportunity', 'potential', 'could', 'should', 'recommend', 'suggest']
                for marker in opportunity_markers:
                    sentences = re.findall(r'[^.!?]*(?<=[.!?\s])' + marker + r'[^.!?]*[.!?]', recommendations, re.IGNORECASE)
                    opportunities.extend(sentences)

            # Get competitor-specific opportunities
            competitor_analysis = content_plan.get('competitor_analysis', {})
            for competitor, analysis in competitor_analysis.items():
                if isinstance(analysis, str):
                    # Find sentences mentioning weaknesses or gaps
                    weakness_sentences = re.findall(r'[^.!?]*(?<=[.!?\s])(weak|gap|miss|lack|fail)[^.!?]*[.!?]', analysis, re.IGNORECASE)
                    if weakness_sentences:
                        opportunities.append(f"Exploit {competitor}'s weakness: {weakness_sentences[0]}")

            # Limit to top 5 opportunities
            return opportunities[:5] if opportunities else ["No clear competitive opportunities identified"]
        except Exception as e:
            logger.error(f"Error extracting competitive opportunities: {str(e)}")
            return ["Error analyzing competitive opportunities"]

    def _extract_competitor_strengths(self, analysis, competitor_name):
        """Extract strengths from competitor analysis."""
        try:
            strengths = []

            # Check if analysis is a dictionary or string
            if isinstance(analysis, dict):
                # Handle dictionary format
                analysis_text = analysis.get('text', '')
                if analysis_text:
                    analysis = analysis_text
            
            if isinstance(analysis, str):
                # Look for positive indicators
                positive_markers = ['success', 'strong', 'effective', 'high engagement', 'popular', 'trend']
                for marker in positive_markers:
                    sentences = re.findall(r'[^.!?]*(?<=[.!?\s])' + marker + r'[^.!?]*[.!?]', analysis, re.IGNORECASE)
                    strengths.extend(sentences)

            # Limit and return
            return strengths[:3] if strengths else [f"No clear strengths identified for {competitor_name}"]
        except Exception as e:
            logger.error(f"Error extracting competitor strengths: {str(e)}")
            return [f"Error analyzing {competitor_name}'s strengths"]

    def _extract_competitor_weaknesses(self, analysis, competitor_name):
        """Extract weaknesses from competitor analysis."""
        try:
            weaknesses = []

            if isinstance(analysis, str):
                # Look for negative indicators
                negative_markers = ['weak', 'poor', 'lack', 'miss', 'inconsistent', 'fail', 'low engagement']
                for marker in negative_markers:
                    sentences = re.findall(r'[^.!?]*(?<=[.!?\s])' + marker + r'[^.!?]*[.!?]', analysis, re.IGNORECASE)
                    weaknesses.extend(sentences)

            # Limit and return
            return weaknesses[:3] if weaknesses else [f"No clear weaknesses identified for {competitor_name}"]
        except Exception as e:
            logger.error(f"Error extracting competitor weaknesses: {str(e)}")
            return [f"Error analyzing {competitor_name}'s weaknesses"]

    def _extract_exploitation_opportunities(self, analysis, recommendations):
        """Extract exploitation opportunities based on competitor analysis and recommendations."""
        try:
            opportunities = []

            if isinstance(analysis, str) and isinstance(recommendations, str):
                # Find opportunities in recommendations that relate to this competitor's analysis
                # Extract key terms from the analysis
                analysis_terms = set(re.findall(r'\b\w{5,}\b', analysis.lower()))

                # Find sentences in recommendations that contain these terms
                for term in analysis_terms:
                    if term in recommendations.lower():
                        sentences = re.findall(r'[^.!?]*(?<=[.!?\s])' + term + r'[^.!?]*[.!?]', recommendations, re.IGNORECASE)
                        opportunities.extend(sentences)

            # Limit and return unique opportunities
            unique_opportunities = list(set(opportunities))
            return unique_opportunities[:3] if unique_opportunities else ["No specific exploitation opportunities identified"]
        except Exception as e:
            logger.error(f"Error extracting exploitation opportunities: {str(e)}")
            return ["Error analyzing exploitation opportunities"]

    def _extract_counter_tactics(self, competitor_name, content_plan):
        """Extract specific counter tactics against a competitor."""
        try:
            tactics = []
            recommendations = content_plan.get('recommendations', '')

            if isinstance(recommendations, str):
                # Look for sentences that specifically mention this competitor
                competitor_sentences = re.findall(r'[^.!?]*' + re.escape(competitor_name) + r'[^.!?]*[.!?]', recommendations, re.IGNORECASE)
                tactics.extend(competitor_sentences)

                # Look for counter strategy indicators
                counter_markers = ['counter', 'against', 'instead of', 'better than', 'unlike', 'whereas']
                for marker in counter_markers:
                    sentences = re.findall(r'[^.!?]*(?<=[.!?\s])' + marker + r'[^.!?]*[.!?]', recommendations, re.IGNORECASE)
                    # Only add if they might relate to this competitor
                    for sentence in sentences:
                        if competitor_name.lower() in sentence.lower() or any(term in sentence.lower() for term in competitor_name.lower().split()):
                            tactics.append(sentence)

            # Look in next post for counter positioning
            next_post = content_plan.get('next_post_prediction', {})
            if isinstance(next_post, dict) and 'caption' in next_post:
                caption = next_post.get('caption', '')
                if competitor_name.lower() in caption.lower():
                    tactics.append(f"Suggested caption directly counters {competitor_name}'s approach: {caption}")

            # Limit and return unique tactics
            unique_tactics = list(set(tactics))
            return unique_tactics[:3] if unique_tactics else [f"No specific counter tactics identified against {competitor_name}"]
        except Exception as e:
            logger.error(f"Error extracting counter tactics: {str(e)}")
            return ["Error analyzing counter tactics"]

    def _extract_differentiation_factors(self, content_plan):
        """Extract differentiation factors for the next post."""
        try:
            factors = []
            next_post = content_plan.get('next_post_prediction', {})
            recommendations = content_plan.get('recommendations', '')

            # Look for differentiation language in recommendations
            if isinstance(recommendations, str):
                diff_markers = ['different', 'unique', 'stand out', 'unlike', 'distinguish', 'separate']
                for marker in diff_markers:
                    sentences = re.findall(r'[^.!?]*(?<=[.!?\s])' + marker + r'[^.!?]*[.!?]', recommendations, re.IGNORECASE)
                    factors.extend(sentences)

            # Add caption and visual elements as differentiation factors
            if isinstance(next_post, dict):
                caption = next_post.get('caption', '')
                visual = next_post.get('visual_prompt', '')

                if caption:
                    factors.append(f"Distinctive caption approach: {caption[:50]}...")

                if visual:
                    factors.append(f"Unique visual concept: {visual[:50]}...")

            # Limit and return unique factors
            unique_factors = list(set(factors))
            return unique_factors[:3] if unique_factors else ["No specific differentiation factors identified"]
        except Exception as e:
            logger.error(f"Error extracting differentiation factors: {str(e)}")
            return ["Error analyzing differentiation factors"]

    def _extract_counter_strategies(self, content_plan):
        """Extract counter strategies from the content plan."""
        try:
            strategies = []
            recommendations = content_plan.get('recommendations', '')

            # Look for counter strategy language
            if isinstance(recommendations, str):
                strategy_markers = ['counter', 'against', 'instead of', 'better than', 'outperform']
                for marker in strategy_markers:
                    sentences = re.findall(r'[^.!?]*(?<=[.!?\s])' + marker + r'[^.!?]*[.!?]', recommendations, re.IGNORECASE)
                    strategies.extend(sentences)

            # Look for explicit strategies in competitor analysis
            competitor_analysis = content_plan.get('competitor_analysis', {})
            for competitor, analysis in competitor_analysis.items():
                if isinstance(analysis, str):
                    # Look for strategy recommendations specific to this competitor
                    if "recommend" in analysis.lower() or "should" in analysis.lower():
                        rec_sentences = re.findall(r'[^.!?]*(?<=[.!?\s])(recommend|should)[^.!?]*[.!?]', analysis, re.IGNORECASE)
                        if rec_sentences:
                            strategies.append(f"Against {competitor}: {rec_sentences[0]}")

            # Limit and return unique strategies
            unique_strategies = list(set(strategies))
            return unique_strategies[:3] if unique_strategies else ["No specific counter strategies identified"]
        except Exception as e:
            logger.error(f"Error extracting counter strategies: {str(e)}")
            return ["Error analyzing counter strategies"]

def create_content_plan():
    """Create content plan without using sample data."""
    try:
        system = ContentRecommendationSystem()
        logger.info("create_content_plan: To create a content plan, specify an Instagram username")
        logger.info("Usage: python main.py process_username <username>")
        return {"success": False, "message": "No username specified. Use 'process_username <username>' instead."}
    except Exception as e:
        logger.error(f"Error in create_content_plan: {str(e)}")
        return {"success": False, "message": str(e)}

def main():
    """Main entry point."""
    try:
        logger.info("Starting Social Media Content Recommendation System")
        content_recommendation_system = ContentRecommendationSystem()
        
        # Test R2 access
        logger.info("Initializing Content Recommendation System")
        r2_test = content_recommendation_system.r2_storage.list_objects()
        logger.info("R2 storage is accessible")
        
        # Process queue
        logger.info("Starting sequential queue processing")
        instagram_scraper = InstagramScraper()
        processed_usernames = instagram_scraper.retrieve_and_process_usernames()
        logger.info(f"Retrieved from queue: {processed_usernames}")
        
        if not processed_usernames:
            logger.info("No pending usernames in queue to process")
            return 0
        
        # Process each username through the full pipeline
        for username in processed_usernames:
            logger.info(f"Starting full pipeline for {username}")
            # Construct the object key based on the username
            object_key = f"{username}/{username}.json"
            result = content_recommendation_system.run_pipeline(object_key=object_key)
            if result and isinstance(result, dict) and result.get("success"):
                logger.info(f"Successfully completed pipeline for {username}")
            else:
                logger.error(f"Failed to complete pipeline for {username}")
        
        logger.info(f"Total usernames processed in this run: {len(processed_usernames)}")
        
    except Exception as e:
        logger.error(f"Error in main function: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return 1
    
    return 0

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "create_content_plan":
            content_plan = create_content_plan()
            sys.exit(0 if content_plan.get("success", False) else 1)
        elif sys.argv[1] == "process_username" and len(sys.argv) > 2:
            username = sys.argv[2]
            system = ContentRecommendationSystem()
            result = system.process_instagram_username(username)
            if result.get("success", False):
                print(f"Successfully processed {username}")
                sys.exit(0)
            else:
                print(f"Failed to process {username}: {result.get('message', 'Unknown error')}")
                sys.exit(1)
        else:
            print("Usage:")
            print("  python main.py                    # Process queue")
            print("  python main.py process_username <username>  # Process specific Instagram username")
            sys.exit(1)
    else:
        # Regular main function execution
        sys.exit(main())