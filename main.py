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
        self.storage_manager = R2StorageManager()

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

            processed_data = {
                'posts': posts,
                'engagement_history': engagement_history,
                'profile': {
                    'username': account_data.get('username', ''),
                    'fullName': account_data.get('fullName', ''),
                    'followersCount': account_data.get('followersCount', 0),
                    'followsCount': account_data.get('followsCount', 0),
                    'biography': account_data.get('biography', ''),
                    'account_type': account_data.get('account_type', 'unknown')
                }
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
        """Analyze engagement data."""
        try:
            logger.info("Analyzing engagement data")
            if not data or not data.get('engagement_history'):
                logger.warning("No engagement data found")
                return None

            engagement_data = pd.DataFrame(data['engagement_history'])
            results = self.time_series.analyze_data(
                engagement_data,
                timestamp_col='timestamp',
                value_col='engagement'
            )
            logger.info("Successfully analyzed engagement data")
            return results
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

            content_plan = self.recommendation_generator.generate_content_plan(
                data={
                    'posts': all_posts,
                    'primary_username': primary_username,
                    'secondary_usernames': secondary_usernames,
                    'query': query
                }
            )

            if not content_plan:
                logger.error("Failed to generate content plan")
                return None

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

    def export_content_plan_sections(self, content_plan):
        """Export content plan sections to R2 with enhanced competitor analysis structure."""
        try:
            logger.info("Starting enhanced content plan export")

            if not content_plan:
                logger.error("Cannot export empty content plan")
                return False

            # Get primary username
            username = content_plan.get('profile_analysis', {}).get('username')
            if not username:
                logger.error("Cannot export - username not found in content plan")
                return False

            # Create directory markers
            self._ensure_directory_exists('recommendations')
            self._ensure_directory_exists(f'recommendations/{username}')

            self._ensure_directory_exists('competitor_analysis')
            self._ensure_directory_exists(f'competitor_analysis/{username}')

            self._ensure_directory_exists('next_posts')
            self._ensure_directory_exists(f'next_posts/{username}')

            # Set up the export paths based on the three main directories
            results = {}

            # 1. Enhanced Recommendations section with competitor insights
            recommendations_data = {
                'recommendations': content_plan.get('recommendations', ''),
                'primary_analysis': content_plan.get('primary_analysis', {}),
                'additional_insights': content_plan.get('additional_insights', {}),
                'competitive_advantage': {
                    'strengths': self._extract_competitive_strengths(content_plan),
                    'opportunities': self._extract_competitive_opportunities(content_plan)
                },
                'status': 'pending'  # Add status field
            }
            # Find the next available file number
            recommendation_file_number = self._get_next_file_number('recommendations', username, 'recommendation')
            recommendations_path = f'recommendations/{username}/recommendation_{recommendation_file_number}.json'
            recommendations_file = io.BytesIO(json.dumps(recommendations_data, indent=2).encode('utf-8'))

            # Upload recommendations file
            rec_success = self.storage_manager.upload_file(
                key=recommendations_path,
                file_obj=recommendations_file,
                bucket='tasks'
            )
            results['recommendations'] = rec_success
            logger.info(f"Enhanced recommendations export {'successful' if rec_success else 'failed'} to {recommendations_path}")

            # 2. Enhanced Competitor analysis directory with strategic insights
            if 'competitor_analysis' in content_plan:
                competitor_analysis = content_plan.get('competitor_analysis', {})
                competitor_results = {}

                for competitor_name, analysis in competitor_analysis.items():
                    # Skip if competitor name is empty
                    if not competitor_name:
                        continue

                    # Create competitor directory
                    competitor_dir = f'competitor_analysis/{username}/{competitor_name}'
                    self._ensure_directory_exists(competitor_dir)

                    # Prepare enhanced competitor data with strategic insights
                    # Extract metrics from additional_insights if available
                    competitor_metrics = content_plan.get('additional_insights', {}).get(
                        'competitor_metrics', {}).get(competitor_name, {})

                    # Prepare enhanced competitor intelligence data
                    competitor_data = {
                        'analysis': analysis,
                        'metrics': competitor_metrics,
                        'strategic_intel': {
                            'strengths': self._extract_competitor_strengths(analysis, competitor_name),
                            'weaknesses': self._extract_competitor_weaknesses(analysis, competitor_name),
                            'opportunities': self._extract_exploitation_opportunities(analysis, content_plan.get('recommendations', ''))
                        },
                        'recommended_counter_tactics': self._extract_counter_tactics(competitor_name, content_plan),
                        'status': 'pending'
                    }

                    # Find the next available file number for this competitor
                    comp_file_number = self._get_next_file_number('competitor_analysis', f'{username}/{competitor_name}', 'analysis')
                    competitor_path = f'{competitor_dir}/analysis_{comp_file_number}.json'
                    competitor_file = io.BytesIO(json.dumps(competitor_data, indent=2).encode('utf-8'))

                    # Upload enhanced competitor analysis file
                    comp_success = self.storage_manager.upload_file(
                        key=competitor_path,
                        file_obj=competitor_file,
                        bucket='tasks'
                    )
                    competitor_results[competitor_name] = comp_success
                    logger.info(f"Enhanced competitor analysis for {competitor_name} {'successful' if comp_success else 'failed'} to {competitor_path}")

                results['competitor_analyses'] = all(competitor_results.values())

            # 3. Enhanced Next posts directory with competitive positioning
            if 'next_post_prediction' in content_plan:
                # Get competitor context to enhance post positioning
                competitor_context = {
                    name: analysis 
                    for name, analysis in content_plan.get('competitor_analysis', {}).items()
                }

                next_post_data = {
                    'post': content_plan.get('next_post_prediction', {}),
                    'competitive_positioning': {
                        'differentiation': self._extract_differentiation_factors(content_plan),
                        'counter_strategies': self._extract_counter_strategies(content_plan)
                    },
                    'status': 'pending'
                }

                # Find the next available file number
                post_file_number = self._get_next_file_number('next_posts', username, 'post')
                next_post_path = f'next_posts/{username}/post_{post_file_number}.json'
                next_post_file = io.BytesIO(json.dumps(next_post_data, indent=2).encode('utf-8'))

                # Upload enhanced next post file
                post_success = self.storage_manager.upload_file(
                    key=next_post_path,
                    file_obj=next_post_file,
                    bucket='tasks'
                )
                results['next_post'] = post_success
                logger.info(f"Enhanced next post export {'successful' if post_success else 'failed'} to {next_post_path}")

            # Check overall success
            if all(results.values()):
                logger.info("All enhanced content plan sections exported successfully")
                return True

            logger.error(f"Partial export failure: {[k for k, v in results.items() if not v]}")
            return False
        except Exception as e:
            logger.error(f"Export failed: {str(e)}")
            return False

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
            objects = self.storage_manager.list_objects(prefix=directory_path)
            if objects:
                logger.info(f"Directory {directory_path} already exists")
                return True

            # Create directory marker
            success = self.storage_manager.put_object(directory_path)
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
            objects = self.storage_manager.list_objects(prefix=prefix)

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
        """Run the complete pipeline for content recommendation with optional in-memory data."""
        try:
            logger.info("Starting pipeline")

            if object_key and data is None:
                # Handle both direct key names and directory structures
                # Fix: The issue was that object_key was sometimes just a directory name (e.g., "maccosmetics")
                # but the actual data is stored in a JSON file with a specific path structure (e.g., "maccosmetics/maccosmetics.json")
                # This conditional logic handles both cases.
                if '/' not in object_key and not object_key.endswith('.json'):
                    # This is a directory name like 'maccosmetics', convert to file path
                    corrected_key = f"{object_key}/{object_key}.json"
                    logger.info(f"Converting directory name to file path: {corrected_key}")
                    data = self.process_social_data(corrected_key)
                
                else:
                    # Use key as provided
                    data = self.process_social_data(object_key)

                if data is None:
                    logger.error(f"Failed to retrieve or process data from {object_key}")
                    return {
                        "success": False,
                        "message": f"No data available at {object_key}",
                        "data_retrieved": False,
                        "posts_indexed": 0,
                        "engagement_analyzed": False,
                        "plan_generated": False,
                        "plan_saved": False
                    }
            elif data is None:
                logger.error("No data or object_key provided")
                return {
                    "success": False,
                    "message": "No data provided",
                    "data_retrieved": False,
                    "posts_indexed": 0,
                    "engagement_analyzed": False,
                    "plan_generated": False,
                    "plan_saved": False
                }

            if not data.get('posts'):
                logger.info(f"No posts found in data, checking account type...")
                account_type = data.get('profile', {}).get('account_type', 'unknown')
                if account_type == 'business_no_posts':
                    logger.info("Generating initial content suggestions for business account")
                    return self.handle_new_business_account(data)
                elif account_type == 'private_account':
                    logger.warning("Skipping private account analysis")
                    return {"success": False, "message": "Private account cannot be analyzed"}

            primary_username = data.get('profile', {}).get('username', '')
            if not primary_username:
                logger.error("No primary username available for indexing")
                return {
                    "success": False,
                    "message": "No primary username provided",
                    "data_retrieved": True,
                    "posts_indexed": 0,
                    "engagement_analyzed": False,
                    "plan_generated": False,
                    "plan_saved": False
                }

            # Index primary posts
            primary_posts_indexed = self.index_posts(data['posts'], primary_username)
            if primary_posts_indexed == 0:
                logger.error("Pipeline failed: No primary posts indexed")
                return {
                    "success": False,
                    "message": "Failed to index posts",
                    "data_retrieved": True,
                    "posts_indexed": 0,
                    "engagement_analyzed": False,
                    "plan_generated": False,
                    "plan_saved": False
                }

            # Index competitor posts if available
            competitor_posts_indexed = 0
            if 'competitor_posts' in data and data['competitor_posts']:
                logger.info(f"Indexing {len(data['competitor_posts'])} competitor posts")
                # Group posts by username
                competitor_posts_by_username = {}
                for post in data['competitor_posts']:
                    username = post.get('username', '')
                    if username and username != primary_username:
                        if username not in competitor_posts_by_username:
                            competitor_posts_by_username[username] = []
                        competitor_posts_by_username[username].append(post)

                # Index each competitor's posts
                for competitor_username, posts in competitor_posts_by_username.items():
                    if posts:
                        indexed = self.index_posts(posts, competitor_username)
                        competitor_posts_indexed += indexed
                        logger.info(f"Indexed {indexed} posts for competitor {competitor_username}")

            total_posts_indexed = primary_posts_indexed + competitor_posts_indexed
            logger.info(f"Total posts indexed: {total_posts_indexed} (Primary: {primary_posts_indexed}, Competitors: {competitor_posts_indexed})")

            engagement_analysis = self.analyze_engagement(data)
            if engagement_analysis is None:
                logger.error("Pipeline failed: Engagement analysis failed")
                return {
                    "success": False,
                    "message": "Engagement analysis failed",
                    "data_retrieved": True,
                    "posts_indexed": total_posts_indexed,
                    "engagement_analyzed": False,
                    "plan_generated": False,
                    "plan_saved": False
                }

            content_plan = self.generate_content_plan(data)
            if content_plan is None:
                logger.error("Pipeline failed: Content plan generation failed")
                return {
                    "success": False,
                    "message": "Content plan generation failed",
                    "data_retrieved": True,
                    "posts_indexed": total_posts_indexed,
                    "engagement_analyzed": True,
                    "plan_generated": False,
                    "plan_saved": False
                }

            plan_saved = self.save_content_plan(content_plan)
            if not plan_saved:
                logger.error("Pipeline failed: Content plan save failed")
                return {
                    "success": False,
                    "message": "Content plan save failed",
                    "data_retrieved": True,
                    "posts_indexed": total_posts_indexed,
                    "engagement_analyzed": True,
                    "plan_generated": True,
                    "plan_saved": False
                }

            exported = self.export_content_plan_sections(content_plan)

            logger.info("Pipeline completed successfully")
            return {
                "success": True,
                "message": "Content plan generated successfully",
                "data_retrieved": True,
                "posts_indexed": total_posts_indexed,
                "engagement_analyzed": True,
                "plan_generated": True,
                "plan_saved": True,
                "exported_plan_sections": exported,
                "content_plan": content_plan
            }
        except Exception as e:
            logger.error(f"Error in pipeline: {str(e)}")
            return {"success": False, "message": str(e)}

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
        """Extract competitive strengths from content plan."""
        try:
            if isinstance(content_plan, str):
                try:
                    content_plan = json.loads(content_plan)
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse content_plan as JSON: {str(e)}")
                    return []
            # Now proceed with dictionary operations
            recommendations = content_plan.get('recommendations', [])
            strengths = []

            # Extract from RAG analysis
            rag_analysis = content_plan.get('primary_analysis', {}).get('rag_analysis', '')
            if isinstance(rag_analysis, str):
                # Look for strength indicators in the text
                strength_markers = ['strength', 'advantage', 'excel', 'outperform', 'unique']
                for marker in strength_markers:
                    # Find sentences containing the marker
                    sentences = re.findall(r'[^.!?]*(?<=[.!?\s])' + marker + r'[^.!?]*[.!?]', rag_analysis, re.IGNORECASE)
                    strengths.extend(sentences)

            # Get engagement strengths
            engagement = content_plan.get('primary_analysis', {}).get('engagement', {})
            if engagement and isinstance(engagement, dict):
                if engagement.get('avg_engagement', 0) > 0:
                    strengths.append(f"Average engagement of {engagement.get('avg_engagement')} per post")

            # Limit to top 5 strengths
            return strengths[:5] if strengths else ["No clear competitive strengths identified"]
        except Exception as e:
            logger.error(f"Error extracting competitive strengths: {str(e)}")
            return ["Error analyzing competitive strengths"]

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
    """Generate and save a comprehensive content plan to content_plan.json in the current directory.
    
    This function creates a complete content plan by processing Instagram data for the primary
    account and its competitors, analyzing posts, calculating engagement metrics, and generating
    recommendations.
    
    Returns:
        dict: The generated content plan on success, None on failure
    """
    try:
        import os
        import json
        import logging
        from main import ContentRecommendationSystem
        
        # Set up logging
        logging.basicConfig(level=logging.INFO, 
                           format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        logger = logging.getLogger(__name__)
        
        logger.info("Starting comprehensive content plan generation")
        
        # Initialize the system
        system = ContentRecommendationSystem()
        
        # Check if we need sample data
        if not os.path.exists('maccosmetics/maccosmetics.json'):
            logger.info("Creating sample data since no real data exists")
            data = system.create_sample_data()
        else:
            # Process real data if available
            logger.info("Processing real data from maccosmetics directory")
            data = system.process_social_data('maccosmetics/maccosmetics.json')
            
        if not data:
            logger.error("Failed to acquire data for content plan generation")
            return None
            
        # Add competitors if available
        competitor_list = [
            'anastasiabeverlyhills', 'fentybeauty', 'narsissist', 
            'toofaced', 'urbandecaycosmetics'
        ]
        
        # Load competitor data if available
        for competitor in competitor_list:
            competitor_file = f'maccosmetics/{competitor}.json'
            if os.path.exists(competitor_file):
                logger.info(f"Loading competitor data for {competitor}")
                competitor_data = system.process_social_data(competitor_file)
                if competitor_data and 'posts' in competitor_data:
                    if 'competitor_posts' not in data:
                        data['competitor_posts'] = []
                    data['competitor_posts'].extend(competitor_data['posts'])
        
        # Index posts for better vector search
        if 'posts' in data:
            primary_username = data.get('profile', {}).get('username', 'maccosmetics')
            system.index_posts(data['posts'], primary_username)
            
            # Index competitor posts if available
            if 'competitor_posts' in data:
                for post in data['competitor_posts']:
                    if 'username' in post:
                        system.index_posts([post], post['username'])
        
        # Generate the content plan
        logger.info("Generating comprehensive content plan")
        content_plan = system.generate_content_plan(data)
        
        if content_plan:
            # Save the content plan
            with open('content_plan.json', 'w') as f:
                json.dump(content_plan, f, indent=2)
            logger.info("Successfully saved comprehensive content plan to content_plan.json")
            
            # Export content plan sections to R2 if needed
            system.export_content_plan_sections(content_plan)
            
            return content_plan
        else:
            logger.error("Failed to generate comprehensive content plan")
            return None
            
    except Exception as e:
        logger.error(f"Error generating comprehensive content plan: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return None

def main():
    """Main function to run the system."""
    try:
        logger.info("Starting Social Media Content Recommendation System")

        scraper = InstagramScraper()
        system = ContentRecommendationSystem()
        try:
            system.data_retriever.list_objects()
            logger.info("R2 storage is accessible")
        except Exception as e:
            logger.error(f"R2 storage not accessible: {str(e)}")
                # Quick test for content plan export functionality
        if os.path.exists('content_plan.json'):
            try:
                logger.info("Testing content plan export functionality with existing content_plan.json")
                with open('content_plan.json', 'r') as f:
                    content_plan = json.load(f)

                if 'profile_analysis' not in content_plan and 'profile' in content_plan:
                    # Rename profile to profile_analysis for compatibility
                    content_plan['profile_analysis'] = content_plan['profile']

                export_result = system.export_content_plan_sections(content_plan)
                logger.info(f"Content plan export test result: {export_result}")
            except Exception as e:
                logger.error(f"Error testing content plan export: {str(e)}")
            
        # Process usernames sequentially from the queue
        logger.info("Starting sequential queue processing")
        all_processed_usernames = []

               # Process one username at a time until there are no more pending usernames
        while True:
            # Retrieve and process ONE username from the queue
            processed_object_keys = scraper.retrieve_and_process_usernames()
            logger.info(f"Retrieved from queue: {processed_object_keys}")

            if not processed_object_keys:
                logger.info("No more pending usernames in queue to process")
                break

            all_processed_usernames.extend(processed_object_keys)

            # Process this username through the pipeline
            # Use the processed_object_keys directly if they are full paths, otherwise construct them
            if isinstance(processed_object_keys, str):
                object_keys = [processed_object_keys]  # Single key case
            elif isinstance(processed_object_keys, list) and all(isinstance(k, str) for k in processed_object_keys):
                object_keys = processed_object_keys  # Already a list of keys
            else:
                # Just use the parent usernames and let run_pipeline() handle the path construction
                object_keys = processed_object_keys if isinstance(processed_object_keys, list) else []

            logger.info(f"Object keys to process in this iteration: {object_keys}")

            if not object_keys:
                logger.warning("No valid object keys to process in this iteration; continuing to next username")
                continue

            for object_key in object_keys:
                logger.info(f"Processing scraped data: {object_key}")
                result = system.run_pipeline(object_key=object_key)

                print("\n" + "="*50)
                print(f"PROCESSING RESULTS FOR {object_key}")
                print("="*50)
                if result['success']:
                    print(f"Success: {result.get('message', 'Operation completed')}")
                    print(f"Posts analyzed: {result.get('posts_indexed', 0)}")
                    print(f"Recommendations generated: {len(result.get('content_plan', {}).get('recommendations', []))}")
                else:
                    print(f"Failed: {result.get('message', 'Unknown error')}")

            logger.info(f"Completed processing username {object_keys[0] if object_keys else 'unknown'}")
            logger.info("Checking for next username in queue...")

        # If no usernames were processed, use sample data
        if not all_processed_usernames:
            logger.info("No usernames were processed, using sample data")
            sample_data = system.create_sample_data()
            if system.validate_data_structure(sample_data):
                result = system.run_pipeline(data=sample_data)  # Pass sample data directly
                if result['success']:
                    logger.info("Processed sample data successfully")
                    print("\n" + "="*50)
                    print("PROCESSING RESULTS FOR SAMPLE DATA")
                    print("="*50)
                    print(f"Success: {result.get('message')}")
                    print(f"Posts analyzed: {result.get('posts_indexed', 0)}")
                    print(f"Recommendations generated: {len(result.get('content_plan', {}).get('recommendations', []))}")
                else:
                    logger.error(f"Failed to process sample data: {result.get('message')}")
                    print("\n" + "="*50)
                    print("PROCESSING RESULTS FOR SAMPLE DATA")
                    print("="*50)
                    print(f"Failed: {result.get('message', 'Unknown error')}")
            else:
                logger.error("Sample data validation failed")

        logger.info(f"Total usernames processed in this run: {len(all_processed_usernames)}")
        return True
    except Exception as e:
        logger.error(f"Error in main function: {str(e)}")
        return False

if __name__ == "__main__":
    import sys
    
    # Check for specific command to generate just the content plan
    if len(sys.argv) > 1 and sys.argv[1] == "create_content_plan":
        content_plan = create_content_plan()
        sys.exit(0 if content_plan else 1)
    else:
        # Regular main function execution
        main()