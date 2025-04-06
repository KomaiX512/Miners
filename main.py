"""Main module for the social media content recommendation system."""

import logging
import json
import os
import io  # <-- Added import for io module
from datetime import datetime
from data_retrieval import R2DataRetriever
from time_series_analysis import TimeSeriesAnalyzer
from vector_database import VectorDatabaseManager
from rag_implementation import RagImplementation
from recommendation_generation import RecommendationGenerator
from config import R2_CONFIG, LOGGING_CONFIG, GEMINI_CONFIG
import pandas as pd
from r2_storage_manager import R2StorageManager

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
        
        # Initialize components
        self.data_retriever = R2DataRetriever()
        self.vector_db = VectorDatabaseManager()
        self.time_series = TimeSeriesAnalyzer()
        self.rag = RagImplementation(vector_db=self.vector_db)
        self.recommendation_generator = RecommendationGenerator(
            rag=self.rag,
            time_series=self.time_series
        )
    
    def process_social_data(self, data_key):
        """
        Process social media data from R2.
        
        Args:
            data_key: Key of the data file in R2
            
        Returns:
            Dictionary with processed data or None if processing fails
        """
        try:
            logger.info(f"Processing social data from {data_key}")
            
            # Get data from R2
            raw_data = self.data_retriever.get_json_data(data_key)
            
            # Check if we have data
            if not raw_data:
                logger.error(f"No data found at {data_key}")
                return None
            
            # Process Instagram data structure
            if 'humansofny' in data_key:
                data = self.process_instagram_data(raw_data)
                if data:
                    logger.info("Successfully processed Instagram data")
                    return data
                else:
                    logger.error("Failed to process Instagram data")
                    return None
            else:
                logger.error(f"Unsupported data format in {data_key}")
                return None
                
        except Exception as e:
            logger.error(f"Error processing social data: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return None

    def process_instagram_data(self, raw_data):
        """
        Process Instagram data format into the expected structure.
        
        Args:
            raw_data: Raw Instagram JSON data
            
        Returns:
            Dictionary with processed data in the expected format
        """
        try:
            # Check if data is in the expected Instagram format
            if not isinstance(raw_data, list) or not raw_data:
                logger.warning("Invalid Instagram data format")
                return None
            
            # Extract account data
            account_data = raw_data[0]
            
            # Debug the structure
            logger.info(f"Instagram data keys: {list(account_data.keys())}")
            
            # Extract posts from latestPosts field
            posts = []
            engagement_history = []
            
            # Check if latestPosts exists in the account data
            if 'latestPosts' in account_data and isinstance(account_data['latestPosts'], list):
                instagram_posts = account_data['latestPosts']
                logger.info(f"Found {len(instagram_posts)} posts in latestPosts")
                
                for post in instagram_posts:
                    # Some posts might have childPosts (carousel posts)
                    if 'childPosts' in post and post['childPosts']:
                        logger.info(f"Post {post.get('id', '')} has {len(post['childPosts'])} child posts")
                    
                    # Create post object with required fields
                    post_obj = {
                        'id': post.get('id', ''),
                        'caption': post.get('caption', ''),
                        'hashtags': post.get('hashtags', []),
                        'engagement': 0,  # Will calculate below
                        'likes': 0,
                        'comments': post.get('commentsCount', 0),
                        'timestamp': post.get('timestamp', ''),
                        'url': post.get('url', ''),
                        'type': post.get('type', '')
                    }
                    
                    # Handle likes which might be null
                    if post.get('likesCount') is not None:
                        post_obj['likes'] = post['likesCount']
                        
                    # Calculate engagement
                    post_obj['engagement'] = post_obj['likes'] + post_obj['comments']
                    
                    # Only add posts with captions
                    if post_obj['caption']:
                        posts.append(post_obj)
                        
                        # Add to engagement history if timestamp exists
                        if post.get('timestamp'):
                            engagement_record = {
                                'timestamp': post.get('timestamp'),
                                'engagement': post_obj['engagement']
                            }
                            engagement_history.append(engagement_record)
            
            # Log post count for debugging
            logger.info(f"Processed {len(posts)} posts from Instagram data")
            
            # If no posts were processed, handle this case
            if not posts:
                logger.warning("No posts extracted from Instagram data")
                # Create synthetic timestamps and engagement if needed for time series
                now = datetime.now()
                for i in range(3):
                    timestamp = (now - pd.Timedelta(days=i)).strftime('%Y-%m-%dT%H:%M:%S.000Z')
                    engagement = 1000 - (i * 100)  # Decreasing engagement
                    engagement_history.append({
                        'timestamp': timestamp,
                        'engagement': engagement
                    })
                logger.info(f"Created {len(engagement_history)} synthetic engagement records for time series")
            
            # Sort engagement history by timestamp
            engagement_history.sort(key=lambda x: x['timestamp'])
            
            # Create processed data structure
            processed_data = {
                'posts': posts,
                'engagement_history': engagement_history,
                'profile': {
                    'username': account_data.get('username', ''),
                    'fullName': account_data.get('fullName', ''),
                    'followersCount': account_data.get('followersCount', 0),
                    'followsCount': account_data.get('followsCount', 0),
                    'biography': account_data.get('biography', '')
                }
            }
            
            return processed_data
        
        except Exception as e:
            logger.error(f"Error processing Instagram data: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return None

    def index_posts(self, posts):
        """
        Index posts in the vector database.
        
        Args:
            posts: List of post dictionaries
            
        Returns:
            Number of posts indexed
        """
        try:
            logger.info(f"Indexing {len(posts)} posts")
            
            # Add posts to vector DB
            count = self.vector_db.add_posts(posts)
            
            logger.info(f"Successfully indexed {count} posts")
            return count
            
        except Exception as e:
            logger.error(f"Error indexing posts: {str(e)}")
            return 0
    
    def analyze_engagement(self, data):
        """
        Analyze engagement data.
        
        Args:
            data: Dictionary with engagement data
            
        Returns:
            Analysis results
        """
        try:
            logger.info("Analyzing engagement data")
            
            # Prepare engagement data
            if not data or not data.get('engagement_history'):
                logger.warning("No engagement data found")
                return None
            
            engagement_data = data['engagement_history']
            
            # Analyze with time series
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
    
    def generate_content_plan(self, topics=None, n_recommendations=3):
        """
        Generate a content plan for given topics.
        
        Args:
            topics: List of topics (if None, detect trending)
            n_recommendations: Number of recommendations per topic
            
        Returns:
            Dictionary with content plan
        """
        try:
            logger.info("Generating content plan")
            
            # If no topics provided, use trending topics
            if not topics:
                data = self.process_social_data()
                if data and data.get('engagement_history'):
                    trending = self.recommendation_generator.generate_trending_topics(
                        data['engagement_history'],
                        top_n=3
                    )
                    topics = [trend['topic'] for trend in trending]
                
                # Fallback topics if no trending detected
                if not topics:
                    topics = ["summer fashion", "product promotion", "customer engagement"]
            
            # Generate recommendations
            recommendations = self.recommendation_generator.generate_recommendations(
                topics,
                n_recommendations=n_recommendations
            )
            
            # Create content plan
            content_plan = {
                'generated_date': datetime.now().strftime('%Y-%m-%d'),
                'topics': topics,
                'recommendations': recommendations
            }
            
            logger.info(f"Successfully generated content plan with {len(topics)} topics")
            return content_plan
            
        except Exception as e:
            logger.error(f"Error generating content plan: {str(e)}")
            return None
    
    def save_content_plan(self, content_plan, filename='content_plan.json'):
        """
        Save content plan to a file.
        
        Args:
            content_plan: Dictionary with content plan
            filename: Output filename
            
        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info(f"Saving content plan to {filename}")
            
            with open(filename, 'w') as f:
                json.dump(content_plan, f, indent=2)
            
            logger.info(f"Successfully saved content plan to {filename}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving content plan: {str(e)}")
            return False
    
    def run_pipeline(self, data_key):
        """
        Run the complete pipeline.
        
        Args:
            data_key: Key of the data file in R2
            
        Returns:
            Dictionary with results
        """
        logger.info("Starting complete pipeline")
        
        results = {
            'success': False,
            'data_retrieved': False,
            'posts_indexed': 0,
            'engagement_analyzed': False,
            'plan_generated': False,
            'plan_saved': False
        }
        
        try:
            # Process social data
            data = self.process_social_data(data_key)
            
            # Validate data structure
            if data and self.validate_data_structure(data):
                results['data_retrieved'] = True
                
                # Index posts
                posts_indexed = self.index_posts(data['posts'])
                results['posts_indexed'] = posts_indexed
                
                # Analyze engagement
                engagement_results = self.analyze_engagement(data)
                results['engagement_analyzed'] = engagement_results is not None
                
                # Generate content plan
                plan = self.recommendation_generator.generate_enhanced_content_plan(
                    data['posts'], 
                    data.get('profile', {})
                )
                
                results['plan_generated'] = plan is not None
                
                # Save content plan
                results['plan_saved'] = self.save_content_plan(plan)
                
                # Overall success
                results['success'] = all([
                    results['data_retrieved'],
                    results['posts_indexed'] > 0,
                    results['plan_generated'],
                    results['plan_saved']
                ])
                
                logger.info(f"Pipeline completed successfully with {posts_indexed} posts indexed")
            else:
                logger.error("Failed to retrieve valid data - stopping pipeline")
                results['success'] = False
        
        except Exception as e:
            logger.error(f"Error in pipeline: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
        
        logger.info(f"Pipeline completed with status: {results['success']}")
        return results

    def ensure_sample_data_in_r2(self):
        """Ensure sample data exists in R2 storage."""
        try:
            # Check if social_data.json exists in the bucket
            objects = self.data_retriever.list_objects()
            file_exists = any(obj['Key'] == 'social_data.json' for obj in objects)
            
            if not file_exists:
                logger.info("social_data.json not found in R2, creating and uploading sample data")
                
                # Create sample data in memory (set use_file=False so that we get generated data)
                sample_data = self.create_sample_data(use_file=False)
                
                # Convert sample data to a bytes buffer so it can be uploaded
                file_obj = io.BytesIO(json.dumps(sample_data).encode('utf-8'))
                
                if self.data_retriever.upload_file('social_data.json', file_obj):
                    logger.info("Successfully uploaded sample data to R2")
                    return True
                else:
                    logger.error("Failed to upload sample data to R2")
                    return False
            else:
                logger.info("social_data.json already exists in R2")
                return True
                
        except Exception as e:
            logger.error(f"Error ensuring sample data in R2: {str(e)}")
            return False

    def validate_data_structure(self, data):
        """
        Validate that the data structure contains the required fields.
        
        Args:
            data: Processed data dictionary
            
        Returns:
            Boolean indicating whether the data is valid
        """
        try:
            # Check for required top-level keys
            if not all(key in data for key in ['posts', 'engagement_history']):
                missing_keys = [key for key in ['posts', 'engagement_history'] if key not in data]
                logger.warning(f"Missing required top-level keys in data: {missing_keys}")
                return False
            
            # Check if posts array is populated
            if not data['posts'] or not isinstance(data['posts'], list):
                if not data['posts']:
                    logger.warning("Posts array is empty")
                else:
                    logger.warning(f"Posts is not a list but a {type(data['posts'])}")
                return False
            
            # Check if engagement_history is populated
            if not data['engagement_history'] or not isinstance(data['engagement_history'], list):
                if not data['engagement_history']:
                    logger.warning("Engagement history is empty")
                else:
                    logger.warning(f"Engagement history is not a list but a {type(data['engagement_history'])}")
                return False
            
            # Check at least one post has required fields
            required_post_fields = ['id', 'caption', 'engagement']
            if not any(all(field in post for field in required_post_fields) for post in data['posts']):
                logger.warning("No posts with all required fields")
                # Log what fields are missing from each post
                for i, post in enumerate(data['posts']):
                    missing = [field for field in required_post_fields if field not in post]
                    if missing:
                        logger.warning(f"Post {i} missing fields: {missing}")
                return False
            
            # Check engagement history has required fields
            required_history_fields = ['timestamp', 'engagement']
            if not all(all(field in record for field in required_history_fields) for record in data['engagement_history']):
                logger.warning("Engagement history missing required fields")
                return False
            
            logger.info("Data structure validation passed")
            return True
            
        except Exception as e:
            logger.error(f"Error validating data structure: {str(e)}")
            return False

    def create_sample_data(self, use_file=False):
        """
        Create sample data when real data isn't available.
        
        Args:
            use_file: Whether to load from a sample file
            
        Returns:
            Dictionary with sample data
        """
        try:
            logger.info("Creating sample data")
            
            if use_file:
                # Try to load from a sample file - implementation depends on your system
                pass
            
            # Create synthetic data
            now = datetime.now()
            # Generate few sample posts
            posts = [
                {
                    'id': '1',
                    'caption': 'Summer fashion trends for 2025 #SummerFashion #Trending',
                    'hashtags': ['#SummerFashion', '#Trending'],
                    'engagement': 1200,
                    'likes': 1000,
                    'comments': 200,
                    'timestamp': now.strftime('%Y-%m-%dT%H:%M:%S.000Z'),
                    'url': 'https://example.com/post1',
                    'type': 'Image'
                },
                {
                    'id': '2',
                    'caption': 'Exciting new product launch! #NewProduct #Promotion',
                    'hashtags': ['#NewProduct', '#Promotion'],
                    'engagement': 800,
                    'likes': 700,
                    'comments': 100,
                    'timestamp': (now - pd.Timedelta(days=1)).strftime('%Y-%m-%dT%H:%M:%S.000Z'),
                    'url': 'https://example.com/post2',
                    'type': 'Image'
                },
                {
                    'id': '3',
                    'caption': 'Engaging with our community. Thank you for your support! #Community #Engagement',
                    'hashtags': ['#Community', '#Engagement'],
                    'engagement': 1500,
                    'likes': 1300,
                    'comments': 200,
                    'timestamp': (now - pd.Timedelta(days=2)).strftime('%Y-%m-%dT%H:%M:%S.000Z'),
                    'url': 'https://example.com/post3',
                    'type': 'Image'
                }
            ]
            
            # Create engagement history
            engagement_history = [
                {
                    'timestamp': (now - pd.Timedelta(days=2)).strftime('%Y-%m-%dT%H:%M:%S.000Z'),
                    'engagement': 1500
                },
                {
                    'timestamp': (now - pd.Timedelta(days=1)).strftime('%Y-%m-%dT%H:%M:%S.000Z'),
                    'engagement': 800
                },
                {
                    'timestamp': now.strftime('%Y-%m-%dT%H:%M:%S.000Z'),
                    'engagement': 1200
                }
            ]
            
            # Create sample profile
            profile = {
                'username': 'sample_user',
                'fullName': 'Sample User',
                'followersCount': 10000,
                'followsCount': 500,
                'biography': 'This is a sample profile for testing purposes.'
            }
            
            # Combine into data structure
            data = {
                'posts': posts,
                'engagement_history': engagement_history,
                'profile': profile
            }
            
            logger.info(f"Created sample data with {len(posts)} posts")
            return data
            
        except Exception as e:
            logger.error(f"Error creating sample data: {str(e)}")
            # Return minimal data structure
            return {
                'posts': [],
                'engagement_history': [],
                'profile': {}
            }

    def process_instagram_username(self, username, results_limit=10):
        """
        Process Instagram username by scraping, uploading, and analyzing.
        
        Args:
            username (str): Instagram username to process
            results_limit (int): Maximum number of results to fetch
            
        Returns:
            dict: Result with success status and content plan
        """
        try:
            logger.info(f"Processing Instagram username: {username}")
            
            # Create scraper
            from instagram_scraper import InstagramScraper
            scraper = InstagramScraper()
            
            # Scrape and upload
            scrape_result = scraper.scrape_and_upload(username, results_limit)
            
            if not scrape_result["success"]:
                logger.warning(f"Failed to scrape profile for {username}: {scrape_result['message']}")
                return {"success": False, "message": scrape_result['message']}
            
            # Run pipeline with the uploaded object key
            object_key = scrape_result["object_key"]
            pipeline_result = self.run_pipeline(object_key)
            
            if not pipeline_result["success"]:
                logger.warning(f"Failed to generate recommendations for {username}")
                return {
                    "success": False, 
                    "message": "Failed to generate recommendations",
                    "details": pipeline_result
                }
            
            # Return success with content plan
            return {
                "success": True,
                "message": "Successfully generated recommendations",
                "details": pipeline_result,
                "content_plan_file": "content_plan.json"
            }
            
        except Exception as e:
            logger.error(f"Error processing Instagram username {username}: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return {"success": False, "message": str(e)}


def main():
    """Main function to run the system."""
    try:
        logger.info("Starting Social Media Content Recommendation System")
        
        # Create system
        system = ContentRecommendationSystem()
        
        # Check if R2 is accessible
        try:
            system.data_retriever.list_objects()
            use_r2 = True
            logger.info("R2 storage is accessible")
            
            # Ensure sample data exists in R2
            system.ensure_sample_data_in_r2()
            
        except Exception as e:
            logger.error(f"R2 storage is not accessible: {str(e)}")
            logger.error("Cannot proceed without R2 access")
            return False
        
        logger.info("Starting complete pipeline")
        # Change the data_key below to the correct key that was uploaded
        results = system.run_pipeline(data_key='social_data.json')
        
        # Print results
        print("\n" + "="*50)
        print("CONTENT RECOMMENDATION SYSTEM RESULTS")
        print("="*50)
        print(f"Pipeline success: {results['success']}")
        print(f"Data retrieved: {results['data_retrieved']}")
        print(f"Posts indexed: {results['posts_indexed']}")
        print(f"Engagement analyzed: {results['engagement_analyzed']}")
        print(f"Plan generated: {results['plan_generated']}")
        print(f"Plan saved: {results['plan_saved']}")
        
        if results['success']:
            print("\nContent plan saved to content_plan.json")
        else:
            print("\nPipeline failed - no valid content plan generated")
        
        print("="*50)
        
        return results['success']
        
    except Exception as e:
        logger.error(f"Error in main: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)