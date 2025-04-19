# Module for generating content recommendations.
"""Module for generating content recommendations."""

import logging
import re
import json
from rag_implementation import RagImplementation
from time_series_analysis import TimeSeriesAnalyzer
from config import CONTENT_TEMPLATES, LOGGING_CONFIG
from datetime import datetime
import pandas as pd

# Set up logging
logging.basicConfig(
    level=LOGGING_CONFIG['level'],
    format=LOGGING_CONFIG['format']
)
logger = logging.getLogger(__name__)

class RecommendationGenerator:
    """Class for generating content recommendations."""
    
    def __init__(self, rag=None, time_series=None, templates=CONTENT_TEMPLATES):
        """Initialize with necessary components."""
        self.rag = rag or RagImplementation()
        self.time_series = time_series or TimeSeriesAnalyzer()
        self.templates = templates
    
    def extract_hashtags(self, text):
        """
        Extract hashtags from text.
        
        Args:
            text: Text containing hashtags
            
        Returns:
            List of hashtags
        """
        hashtags = re.findall(r'#\w+', text)
        return hashtags
    
    def format_caption(self, raw_text):
        """
        Format caption by removing hashtags.
        
        Args:
            raw_text: Raw text with hashtags
            
        Returns:
            Dictionary with formatted caption and hashtags
        """
        hashtags = self.extract_hashtags(raw_text)
        caption = re.sub(r'#\w+', '', raw_text).strip()
        
        return {
            "caption": caption,
            "hashtags": hashtags
        }
    
    def apply_template(self, recommendation, template_key="promotional"):
        """
        Apply a template to the recommendation.
        
        Args:
            recommendation: Dictionary with recommendation details
            template_key: Key of template to apply
            
        Returns:
            Formatted string
        """
        try:
            template = self.templates.get(template_key, self.templates["promotional"])
            
            caption = recommendation.get("caption", "")
            hashtags = recommendation.get("hashtags", [])
            hashtags_str = " ".join(hashtags)
            
            formatted = template.format(caption=caption, hashtags=hashtags_str)
            return formatted
            
        except Exception as e:
            logger.error(f"Error applying template: {str(e)}")
            return f"{recommendation.get('caption', '')} {' '.join(recommendation.get('hashtags', []))}"
    
    def generate_trending_topics(self, data, timestamp_col='timestamp', value_col='engagement', top_n=3):
        """
        Generate trending topics based on time series analysis.
        
        Args:
            data: Dictionary or DataFrame with time series data
            timestamp_col: Column name for timestamps
            value_col: Column name for values
            top_n: Number of trending topics to return
            
        Returns:
            List of trending topics with periods
        """
        try:
            # Analyze data
            results = self.time_series.analyze_data(data, timestamp_col, value_col)
            
            # Get trending periods
            trending_periods = list(results.get('trending_periods', pd.DataFrame()).iterrows())[:top_n]
            
            if trending_periods is None or len(trending_periods) == 0:
                logger.warning("No trending periods detected")
                return []
            
            # Format trending periods
            trending_topics = []
            for _, row in trending_periods:
                trending_topics.append({
                    'date': row['ds'].strftime('%Y-%m-%d'),
                    'value': row['yhat'],
                    'topic': f"Trending on {row['ds'].strftime('%B %d')}"
                })
            
            logger.info(f"Generated {len(trending_topics)} trending topics")
            return trending_topics
            
        except Exception as e:
            logger.error(f"Error generating trending topics: {str(e)}")
            return []
    
    def generate_recommendations(self, topics, n_per_topic=3):
        """
        Generate content recommendations for multiple topics.
        
        Args:
            topics: List of topics to generate recommendations for
            n_per_topic: Number of recommendations per topic
            
        Returns:
            Dictionary with recommendations by topic
        """
        try:
            if not topics or n_per_topic <= 0:
                logger.warning("Invalid input for generate_recommendations")
                return {}

            # Validate topic types
            if not all(isinstance(topic, (str, dict)) for topic in topics):
                logger.error("Invalid topic format - must be strings or dictionaries")
                return {}

            # Convert dictionary topics to strings if needed
            topic_strings = []
            for topic in topics:
                if isinstance(topic, dict):
                    topic_str = topic.get('topic', '').strip() or str(topic)
                    topic_strings.append(topic_str)
                else:
                    topic_strings.append(str(topic).strip())

            # Remove empty topics
            valid_topics = [t for t in topic_strings if t]
            if not valid_topics:
                logger.error("No valid topics provided for recommendations")
                return {}
            
            # Use default primary_username and secondary_usernames if not available
            primary_username = "user"
            secondary_usernames = []
            
            # Batch all topics into a single RAG request
            combined_prompt = self._create_batch_prompt(valid_topics)
            
            # Generate a single response for all topics
            try:
                # First try with the full API parameters
                batch_response = self.rag.generate_batch_recommendations(combined_prompt, valid_topics)
            except Exception as e:
                logger.warning(f"Error in batch recommendations with original API: {str(e)}")
                # Create a fallback response structure
                batch_response = {}
                for topic in valid_topics:
                    try:
                        topic_recs = []
                        # Generate individual recommendations for each topic
                        for i in range(n_per_topic):
                            rec = self.rag.generate_recommendation(
                                primary_username=primary_username,
                                secondary_usernames=secondary_usernames,
                                query=f"recommendation for {topic}"
                            )
                            if isinstance(rec, dict) and 'next_post' in rec:
                                rec = rec['next_post']  # Extract next_post if that's the structure
                            topic_recs.append(rec)
                        batch_response[topic] = topic_recs
                    except Exception as inner_e:
                        logger.error(f"Error generating recommendations for topic {topic}: {str(inner_e)}")
                        batch_response[topic] = [{"caption": f"Recommendation for {topic}", "hashtags": [f"#{topic.replace(' ', '')}"]}]
            
            # Process the batch response into individual recommendations
            recommendations = {}
            
            for topic in valid_topics:
                if topic in batch_response:
                    topic_recs = batch_response[topic]
                    # Ensure we have the requested number of recommendations
                    while len(topic_recs) < n_per_topic:
                        # Generate additional recommendations if needed
                        try:
                            additional_rec = self.rag.generate_recommendation(
                                primary_username=primary_username,
                                secondary_usernames=secondary_usernames,
                                query=f"recommendation for {topic}"
                            )
                            if isinstance(additional_rec, dict) and 'next_post' in additional_rec:
                                additional_rec = additional_rec['next_post']
                            topic_recs.append(additional_rec)
                        except Exception as e:
                            # Add a simple fallback
                            topic_recs.append({
                                "caption": f"Engaging content about {topic}",
                                "hashtags": [f"#{topic.replace(' ', '')}"]
                            })
                    
                    # Store recommendations for this topic
                    recommendations[topic] = topic_recs[:n_per_topic]
                else:
                    # Generate recommendations individually if not in batch response
                    logger.warning(f"Topic {topic} not found in batch response, generating individually")
                    topic_recs = []
                    for i in range(n_per_topic):
                        try:
                            rec = self.rag.generate_recommendation(
                                primary_username=primary_username,
                                secondary_usernames=secondary_usernames,
                                query=f"recommendation for {topic}"
                            )
                            if isinstance(rec, dict) and 'next_post' in rec:
                                rec = rec['next_post']
                            topic_recs.append(rec)
                        except Exception as e:
                            # Add a simple fallback
                            topic_recs.append({
                                "caption": f"Engaging content about {topic}",
                                "hashtags": [f"#{topic.replace(' ', '')}"]
                            })
                    recommendations[topic] = topic_recs
            
            logger.info(f"Generated recommendations for {len(valid_topics)} topics")
            return recommendations
        except Exception as e:
            logger.error(f"Critical error in generate_recommendations: {str(e)}")
            return {}
    
    def _create_batch_prompt(self, topics):
        """Create a prompt for batch recommendation generation."""
        topics_str = ", ".join([f'"{topic}"' for topic in topics])
        
        prompt = f"""
        You are an expert social media content creator. I need you to generate content recommendations 
        for the following topics: {topics_str}.
        
        For each topic, provide 3 different content ideas. Each idea should include:
        1. An attention-grabbing caption
        2. Relevant hashtags
        3. A call to action
        
        Format your response as a JSON object with topics as keys and arrays of recommendations as values:
        
        {{
            "topic1": [
                {{
                    "caption": "Caption for first recommendation",
                    "hashtags": ["#Hashtag1", "#Hashtag2"],
                    "call_to_action": "Call to action text"
                }},
                // More recommendations...
            ],
            "topic2": [
                // Recommendations for topic 2...
            ]
        }}
        
        Be creative and engaging. Use the specific topic keywords in your recommendations.
        """
        
        return prompt
    
    def analyze_account_type(self, posts):
        """
        Analyze posts to determine if the account is for branding or personal use.
        
        Args:
            posts: List of post dictionaries
            
        Returns:
            Dictionary with account type analysis
        """
        try:
            # Extract captions and hashtags
            captions = [post.get('caption', '') for post in posts if 'caption' in post]
            all_hashtags = []
            for post in posts:
                if 'hashtags' in post:
                    if isinstance(post['hashtags'], list):
                        all_hashtags.extend(post['hashtags'])
                    elif isinstance(post['hashtags'], str):
                        extracted = self.extract_hashtags(post['hashtags'])
                        all_hashtags.extend(extracted)
            
            # Count business-related terms in captions
            business_terms = ['product', 'sale', 'discount', 'offer', 'brand', 'business', 
                             'shop', 'store', 'buy', 'purchase', 'collection', 'launch']
            
            business_count = sum(1 for caption in captions 
                               if any(term in caption.lower() for term in business_terms))
            
            # Count business-related hashtags
            business_hashtags = ['#business', '#brand', '#product', '#sale', '#shop', 
                                '#store', '#entrepreneur', '#marketing']
            
            business_hashtag_count = sum(1 for hashtag in all_hashtags 
                                      if any(bh.lower() in hashtag.lower() for bh in business_hashtags))
            
            # Calculate percentages
            total_posts = len(posts)
            if total_posts == 0:
                return {
                    'account_type': 'Unknown',
                    'confidence': 0,
                    'analysis': 'Insufficient data to determine account type'
                }
            
            business_caption_percentage = (business_count / total_posts) * 100
            
            # Determine account type
            if business_caption_percentage > 60 or business_hashtag_count > total_posts * 0.5:
                account_type = 'Business/Brand'
                confidence = min(100, max(60, business_caption_percentage))
                analysis = f"Account appears to be for business/branding purposes with {confidence:.1f}% confidence. Found {business_count} posts with business-related terms and {business_hashtag_count} business-related hashtags."
            else:
                account_type = 'Personal'
                confidence = min(100, max(60, 100 - business_caption_percentage))
                analysis = f"Account appears to be for personal use with {confidence:.1f}% confidence. Only {business_count} out of {total_posts} posts contain business-related terms."
            
            return {
                'account_type': account_type,
                'confidence': confidence,
                'analysis': analysis
            }
            
        except Exception as e:
            logger.error(f"Error analyzing account type: {str(e)}")
            return {
                'account_type': 'Unknown',
                'confidence': 0,
                'analysis': f"Error during analysis: {str(e)}"
            }
    
    def analyze_engagement(self, posts):
        """
        Analyze which types of posts have the most engagement.
        
        Args:
            posts: List of post dictionaries
            
        Returns:
            Dictionary with engagement analysis
        """
        try:
            # Group posts by content type
            content_types = {
                'photo': [],
                'video': [],
                'carousel': [],
                'text_only': []
            }
            
            # Categorize posts by hashtags
            hashtag_categories = {
                'product': ['#product', '#sale', '#shop', '#store', '#buy'],
                'lifestyle': ['#lifestyle', '#life', '#daily', '#everyday'],
                'motivation': ['#motivation', '#inspire', '#success', '#goals'],
                'fashion': ['#fashion', '#style', '#outfit', '#clothing'],
                'food': ['#food', '#recipe', '#cooking', '#foodie'],
                'travel': ['#travel', '#vacation', '#trip', '#adventure'],
                'fitness': ['#fitness', '#workout', '#gym', '#health']
            }
            
            category_engagement = {category: {'count': 0, 'total_engagement': 0} 
                                for category in hashtag_categories.keys()}
            
            # Process each post
            for post in posts:
                # Get post type
                post_type = post.get('media_type', 'photo').lower()
                if post_type in content_types:
                    content_types[post_type].append(post)
                else:
                    content_types['photo'].append(post)
                
                # Get engagement
                engagement = post.get('engagement', 0)
                if not engagement and 'likes' in post:
                    # Calculate engagement from likes and comments if available
                    likes = post.get('likes', 0)
                    comments = post.get('comments', 0)
                    engagement = likes + comments
                
                # Categorize by hashtags
                post_hashtags = []
                if 'hashtags' in post:
                    if isinstance(post['hashtags'], list):
                        post_hashtags = post['hashtags']
                    elif isinstance(post['hashtags'], str):
                        post_hashtags = self.extract_hashtags(post['hashtags'])
                
                # Check which categories the hashtags belong to
                for category, category_tags in hashtag_categories.items():
                    if any(ht.lower() in [t.lower() for t in post_hashtags] for ht in category_tags):
                        category_engagement[category]['count'] += 1
                        category_engagement[category]['total_engagement'] += engagement
            
            # Calculate average engagement by content type
            content_type_analysis = {}
            for content_type, type_posts in content_types.items():
                if type_posts:
                    total_engagement = sum(post.get('engagement', 0) for post in type_posts)
                    avg_engagement = total_engagement / len(type_posts) if len(type_posts) > 0 else 0
                    content_type_analysis[content_type] = {
                        'count': len(type_posts),
                        'total_engagement': total_engagement,
                        'average_engagement': avg_engagement
                    }
            
            # Calculate average engagement by category
            category_analysis = {}
            for category, data in category_engagement.items():
                if data['count'] > 0:
                    avg_engagement = data['total_engagement'] / data['count']
                    category_analysis[category] = {
                        'count': data['count'],
                        'total_engagement': data['total_engagement'],
                        'average_engagement': avg_engagement
                    }
            
            # Find best performing content type and category
            best_content_type = max(content_type_analysis.items(), 
                                  key=lambda x: x[1]['average_engagement'], 
                                  default=(None, {'average_engagement': 0}))
            
            best_category = max(category_analysis.items(), 
                              key=lambda x: x[1]['average_engagement'], 
                              default=(None, {'average_engagement': 0}))
            
            # Generate summary
            if best_content_type[0] and best_category[0]:
                summary = f"The account performs best with {best_content_type[0]} content about {best_category[0]}. " \
                         f"Average engagement for {best_content_type[0]} content is {best_content_type[1]['average_engagement']:.1f}, " \
                         f"and for {best_category[0]} content is {best_category[1]['average_engagement']:.1f}."
            else:
                summary = "Insufficient data to determine best performing content."
            
            return {
                'content_type_analysis': content_type_analysis,
                'category_analysis': category_analysis,
                'best_performing_content': best_content_type[0],
                'best_performing_category': best_category[0],
                'summary': summary
            }
            
        except Exception as e:
            logger.error(f"Error analyzing engagement: {str(e)}")
            return {
                'summary': f"Error during engagement analysis: {str(e)}"
            }
    
    def analyze_posting_trends(self, posts):
        """
        Analyze posting patterns related to product trends and events.
        
        Args:
            posts: List of post dictionaries
            
        Returns:
            Dictionary with posting trend analysis
        """
        try:
            # Extract timestamps and convert to datetime
            timestamps = []
            for post in posts:
                if 'timestamp' in post:
                    try:
                        timestamps.append(pd.to_datetime(post['timestamp']))
                    except:
                        continue
            
            if not timestamps:
                return {
                    'summary': "Insufficient timestamp data to analyze posting trends."
                }
            
            # Create DataFrame with timestamps
            df = pd.DataFrame({'timestamp': timestamps})
            
            # Extract day of week and hour
            df['day_of_week'] = df['timestamp'].dt.day_name()
            df['hour'] = df['timestamp'].dt.hour
            
            # Count posts by day of week
            day_counts = df['day_of_week'].value_counts().to_dict()
            
            # Count posts by hour
            hour_counts = df['hour'].value_counts().to_dict()
            
            # Find most common posting days and times
            most_common_day = max(day_counts.items(), key=lambda x: x[1], default=(None, 0))
            most_common_hour = max(hour_counts.items(), key=lambda x: x[1], default=(None, 0))
            
            # Format hour in 12-hour format
            hour_formatted = f"{most_common_hour[0] % 12 or 12} {'AM' if most_common_hour[0] < 12 else 'PM'}"
            
            # Calculate posting frequency
            date_range = max(timestamps) - min(timestamps)
            days_range = date_range.days + 1  # Add 1 to include both start and end dates
            posts_per_day = len(timestamps) / days_range if days_range > 0 else 0
            
            # Check for seasonal patterns
            df['month'] = df['timestamp'].dt.month
            month_counts = df['month'].value_counts().to_dict()
            
            # Identify months with higher posting frequency
            avg_posts_per_month = len(timestamps) / 12  # Simple average
            high_activity_months = {month: count for month, count in month_counts.items() 
                                  if count > avg_posts_per_month * 1.2}  # 20% above average
            
            month_names = {
                1: 'January', 2: 'February', 3: 'March', 4: 'April', 
                5: 'May', 6: 'June', 7: 'July', 8: 'August',
                9: 'September', 10: 'October', 11: 'November', 12: 'December'
            }
            
            high_activity_months_named = {month_names[month]: count 
                                        for month, count in high_activity_months.items()}
            
            # Generate summary
            if most_common_day[0] and most_common_hour[0] is not None:
                posting_pattern = f"Posts most frequently on {most_common_day[0]}s at around {hour_formatted}."
            else:
                posting_pattern = "No clear posting pattern detected."
            
            if high_activity_months_named:
                seasonal_pattern = f"Higher posting activity during: {', '.join(high_activity_months_named.keys())}."
            else:
                seasonal_pattern = "No clear seasonal posting pattern detected."
            
            summary = f"{posting_pattern} Average posting frequency is {posts_per_day:.1f} posts per day. {seasonal_pattern}"
            
            return {
                'most_active_day': most_common_day[0],
                'most_active_hour': most_common_hour[0],
                'hour_formatted': hour_formatted,
                'posts_per_day': posts_per_day,
                'day_distribution': day_counts,
                'hour_distribution': hour_counts,
                'high_activity_months': high_activity_months_named,
                'summary': summary
            }
            
        except Exception as e:
            logger.error(f"Error analyzing posting trends: {str(e)}")
            return {
                'summary': f"Error during posting trend analysis: {str(e)}"
            }
    
    def generate_next_post_prediction(self, posts, account_analysis=None):
        """
        Generate predictions for the next post.
        
        Args:
            posts: List of post dictionaries
            account_analysis: Optional dictionary with account analysis results
            
        Returns:
            Dictionary with next post prediction
        """
        try:
            # Extract username information
            primary_username = account_analysis.get('username', 'user')
            secondary_usernames = account_analysis.get('competitors', [])
            
            # Extract recent captions and hashtags for context
            recent_captions = [post.get('caption', '') for post in posts[-5:] if 'caption' in post]
            
            all_hashtags = []
            for post in posts:
                if 'hashtags' in post:
                    if isinstance(post['hashtags'], list):
                        all_hashtags.extend(post['hashtags'])
                    elif isinstance(post['hashtags'], str):
                        extracted = self.extract_hashtags(post['hashtags'])
                        all_hashtags.extend(extracted)
            
            # Count hashtag frequency
            from collections import Counter
            hashtag_counts = Counter(all_hashtags)
            common_hashtags = [tag for tag, count in hashtag_counts.most_common(10)]
            
            # Build query/context for recommendation
            query = "next post prediction based on account history"
            context = "\n".join([
                f"Recent caption: {caption}" for caption in recent_captions
            ])
            
            context += "\nCommonly used hashtags: " + ", ".join(common_hashtags)
            
            if account_analysis:
                if isinstance(account_analysis, dict) and 'account_type' in account_analysis:
                    context += f"\nAccount type: {account_analysis['account_type']}"
                
            # Use RAG to generate the prediction with all required parameters
            prediction = self.rag.generate_recommendation(
                primary_username=primary_username,
                secondary_usernames=secondary_usernames,
                query=query + " " + context
            )
            
            # Extract the next_post field if it exists
            if isinstance(prediction, dict) and 'next_post' in prediction:
                next_post = prediction['next_post']
                
                # Handle the case where visual_prompt is called image_prompt
                if 'visual_prompt' in next_post and 'image_prompt' not in next_post:
                    next_post['image_prompt'] = next_post['visual_prompt']
                elif 'image_prompt' not in next_post and 'visual_prompt' not in next_post:
                    next_post['image_prompt'] = "A high-quality, professional image that matches the caption and hashtags."
            
            return next_post
            
            # Check if prediction is already in the right format
            if isinstance(prediction, dict) and 'caption' in prediction:
                # Add image_prompt if missing
                if 'image_prompt' not in prediction and 'visual_prompt' in prediction:
                    prediction['image_prompt'] = prediction['visual_prompt']
                elif 'image_prompt' not in prediction and 'visual_prompt' not in prediction:
                    prediction['image_prompt'] = "A high-quality, professional image that matches the caption and hashtags."
                
                return prediction
            
            # Ensure all required fields are present in the fallback
            return {
                'caption': "Check out our latest updates!",
                'hashtags': ["#New", "#Update"],
                'call_to_action': "Visit our profile for more",
                'image_prompt': "A high-quality, professional image that matches the caption and hashtags."
            }
            
        except Exception as e:
            logger.error(f"Error generating next post prediction: {str(e)}")
            return {
                'caption': "Error generating prediction",
                'hashtags': ["#error"],
                'call_to_action': "Please try again later",
                'image_prompt': "Error generating image prompt"
            }
    
    def identify_competitors(self, posts, profile_info=None):
        """
        Identify potential competitors based on content and hashtags.
        
        Args:
            posts: List of post dictionaries
            profile_info: Optional dictionary with profile information
            
        Returns:
            List of potential competitors with analysis
        """
        try:
            # Extract username information from posts or profile
            primary_username = None
            if posts and len(posts) > 0 and 'username' in posts[0]:
                primary_username = posts[0]['username']
            elif profile_info and 'username' in profile_info:
                primary_username = profile_info['username']
            else:
                primary_username = 'user'
                
            # Use any existing competitors from profile if available
            secondary_usernames = []
            if profile_info and 'competitors' in profile_info and isinstance(profile_info['competitors'], list):
                secondary_usernames = profile_info['competitors']
                
            # Extract all hashtags and mentions
            all_hashtags = []
            all_mentions = []
            
            for post in posts:
                # Extract hashtags
                if 'hashtags' in post:
                    if isinstance(post['hashtags'], list):
                        all_hashtags.extend(post['hashtags'])
                    elif isinstance(post['hashtags'], str):
                        extracted = self.extract_hashtags(post['hashtags'])
                        all_hashtags.extend(extracted)
                
                # Extract mentions from captions
                if 'caption' in post:
                    mentions = re.findall(r'@(\w+)', post['caption'])
                    all_mentions.extend(mentions)
            
            # Count frequency
            from collections import Counter
            hashtag_counts = Counter(all_hashtags)
            mention_counts = Counter(all_mentions)
            
            # Get top hashtags and mentions
            top_hashtags = [tag for tag, _ in hashtag_counts.most_common(20)]
            top_mentions = [mention for mention, _ in mention_counts.most_common(20)]
            
            # Create context for RAG
            context = ""
            if profile_info:
                if 'biography' in profile_info:
                    context += f"Account bio: {profile_info['biography']}\n"
                if 'account_type' in profile_info:
                    context += f"Account category: {profile_info['account_type']}\n"
            
            context += f"Top hashtags used: {', '.join(top_hashtags[:10])}\n"
            context += f"Accounts frequently mentioned: {', '.join(top_mentions[:5])}\n"
            
            # Use RAG to identify competitors with required parameters
            query = f"identify competitors for {primary_username}: {context}"
            
            # Use RAG to generate competitors
            response = self.rag.generate_recommendation(
                primary_username=primary_username,
                secondary_usernames=secondary_usernames,
                query=query
            )
            
            # Extract competitors from response
            competitors = []
            if isinstance(response, dict) and 'competitors' in response:
                competitors = response['competitors']
            elif isinstance(response, list):
                competitors = response
            else:
                # Create a basic list if the response format is unexpected
                competitors = [
                    {
                        "account_name": f"competitor_{i+1}",
                        "reason": "Similar content and audience",
                        "unique_value": "Different approach to similar topics"
                    }
                    for i in range(10)
                ]
            
            # Ensure we have at least 10 competitors
            while len(competitors) < 10:
                competitors.append({
                    "account_name": f"suggested_account_{len(competitors)+1}",
                    "reason": "Similar content and target audience",
                    "unique_value": "Different perspective on similar topics"
                })
            
            return competitors[:10]  # Return exactly 10 competitors
            
        except Exception as e:
            logger.error(f"Error identifying competitors: {str(e)}")
            # Return a basic list of 10 competitors
            return [
                {
                    "account_name": f"competitor_{i+1}",
                    "reason": "Similar content and audience",
                    "unique_value": "Different approach to similar topics"
                }
                for i in range(10)
            ]
    
    def generate_improvement_recommendations(self, account_analysis):
        """
        Generate personalized improvement recommendations based on account analysis.
        
        Args:
            account_analysis: Dictionary with account analysis results
            
        Returns:
            Dictionary with improvement recommendations
        """
        try:
            # Ensure account_analysis is properly formatted
            if not isinstance(account_analysis, dict):
                logger.warning("Invalid account analysis format - using fallback")
                return [{"recommendation": "Post more consistently"}]

            # Extract username information
            primary_username = account_analysis.get('username', 'user')
            secondary_usernames = account_analysis.get('competitors', [])

            # Safely extract account type with fallbacks
            account_type = account_analysis.get('account_type', 'Unknown')
            if not isinstance(account_type, str):  # Handle unexpected types
                account_type = str(account_type)

            # Extract relevant information from account analysis
            context = ""
            
            if isinstance(account_analysis, dict):
                if 'account_type' in account_analysis:
                    context += f"Account type: {account_analysis['account_type']}\n"
                if 'analysis' in account_analysis:
                    context += f"Account analysis: {account_analysis['analysis']}\n"
            
            # Use RAG to generate recommendations with required parameters
            prompt = f"improvement recommendations for {account_type} account: {context}"
            
            # Use RAG to generate recommendations
            response = self.rag.generate_recommendation(
                primary_username=primary_username,
                secondary_usernames=secondary_usernames,
                query=prompt
            )
            
            # Extract recommendations from response
            recommendations = []
            if isinstance(response, dict) and 'recommendations' in response:
                recommendations = response['recommendations']
            elif isinstance(response, list):
                recommendations = response
            else:
                # Create basic recommendations if the response format is unexpected
                recommendations = [
                    {
                        "recommendation": "Post more consistently",
                        "reasoning": "Regular posting helps maintain audience engagement",
                        "implementation": "Create a content calendar and schedule posts in advance"
                    },
                    {
                        "recommendation": "Engage more with followers",
                        "reasoning": "Higher engagement leads to better reach and loyalty",
                        "implementation": "Respond to comments and messages promptly"
                    },
                    {
                        "recommendation": "Use more relevant hashtags",
                        "reasoning": "Proper hashtags increase discoverability",
                        "implementation": "Research trending hashtags in your niche"
                    },
                    {
                        "recommendation": "Improve visual consistency",
                        "reasoning": "Consistent aesthetics create a recognizable brand",
                        "implementation": "Use similar filters and color schemes across posts"
                    },
                    {
                        "recommendation": "Collaborate with similar accounts",
                        "reasoning": "Collaborations expose your account to new audiences",
                        "implementation": "Reach out to complementary accounts for partnership opportunities"
                    }
                ]
            
            # Ensure we have at least 5 recommendations
            while len(recommendations) < 5:
                recommendations.append({
                    "recommendation": f"Generic recommendation {len(recommendations)+1}",
                    "reasoning": "This will help improve your account performance",
                    "implementation": "Follow best practices for Instagram growth"
                })
            
            return recommendations[:5]  # Return exactly 5 recommendations
            
        except Exception as e:
            logger.error(f"Error generating improvement recommendations: {str(e)}")
            # Return basic recommendations
            return [
                {
                    "recommendation": "Post more consistently",
                    "reasoning": "Regular posting helps maintain audience engagement",
                    "implementation": "Create a content calendar and schedule posts in advance"
                },
                {
                    "recommendation": "Engage more with followers",
                    "reasoning": "Higher engagement leads to better reach and loyalty",
                    "implementation": "Respond to comments and messages promptly"
                },
                {
                    "recommendation": "Use more relevant hashtags",
                    "reasoning": "Proper hashtags increase discoverability",
                    "implementation": "Research trending hashtags in your niche"
                },
                {
                    "recommendation": "Improve visual consistency",
                    "reasoning": "Consistent aesthetics create a recognizable brand",
                    "implementation": "Use similar filters and color schemes across posts"
                },
                {
                    "recommendation": "Collaborate with similar accounts",
                    "reasoning": "Collaborations expose your account to new audiences",
                    "implementation": "Reach out to complementary accounts for partnership opportunities"
                }
            ]
    
    def generate_content_plan(self, data):
        """Generate complete content plan with all recommendations."""
        try:
            # Extract data from the new format if needed
            posts = data.get('posts', [])
            primary_username = data.get('primary_username', '')
            secondary_usernames = data.get('secondary_usernames', [])
            query = data.get('query', '')
            
            if not posts:
                logger.error("Cannot generate content plan - no posts in data")
                return None
            
            engagement_data = data.get('engagement_history', [])
            
            # 1. Perform account analysis
            account_analysis = self.analyze_account_type(posts)
            if not account_analysis:
                logger.warning("Failed to generate account analysis")
                account_analysis = {'account_type': 'Unknown'}  # Add default
            
            # Add primary username to account analysis
            if primary_username:
                account_analysis['username'] = primary_username
                
            # Store secondary usernames as competitors
            if secondary_usernames:
                account_analysis['competitors'] = secondary_usernames
            
            # 2. Analyze engagement patterns
            engagement_analysis = self.analyze_engagement(posts)
            if not engagement_analysis:
                logger.warning("Failed to generate engagement analysis")
                engagement_analysis = {'summary': 'No engagement analysis available'}  # Add default
            
            # 3. Analyze posting trends
            posting_trends = self.analyze_posting_trends(posts)
            if not posting_trends:
                logger.warning("Failed to analyze posting trends")
                posting_trends = {'summary': 'No posting trend analysis available'}  # Add default
            
            # Determine if this is a branding or non-branding account
            # Respect any explicit account_type setting from the data parameter
            if 'account_type' in data and data['account_type']:
                is_branding = data['account_type'].lower() == 'branding'
                logger.info(f"Using provided account_type from data: {'branding' if is_branding else 'non-branding'}")
            else:
                # If not explicitly provided, determine from account_analysis
                account_type = account_analysis.get('account_type', 'Unknown')
                is_branding = False
                if isinstance(account_type, str) and account_type.lower() == 'business/brand':
                    is_branding = True
                elif isinstance(account_type, str) and 'business' in account_type.lower():
                    is_branding = True
                
            logger.info(f"Account type identified as {'branding' if is_branding else 'non-branding'}")
            
            # 4. Generate content based on account type
            content_plan = {}
            
            # Basic common elements for both account types
            content_plan = {
                'generated_date': datetime.now().isoformat(),
                'profile_analysis': account_analysis,
                'engagement_analysis': engagement_analysis,
                'posting_trends': posting_trends
            }
            
            # Add trending topics if available for both account types
            if engagement_data:
                trending = self.generate_trending_topics(engagement_data)
                if trending:
                    content_plan['trending_topics'] = trending
            
            if is_branding:
                # BRANDING ACCOUNT FLOW
                # For branding accounts, use the existing RAG implementation
                # Generate RAG analysis with primary, competitor, and recommendations
                rag_output = self.rag.generate_recommendation(
                    primary_username=primary_username,
                    secondary_usernames=secondary_usernames,
                    query=query
                )
                
                # Extract primary and competitor analysis from RAG output
                primary_analysis = rag_output.get('primary_analysis', 'No primary analysis available')
                competitor_analysis = rag_output.get('competitor_analysis', {})
                recommendations = rag_output.get('recommendations', 'No recommendations available')
                
                # Generate next post prediction for branding
                next_post = self.generate_next_post_prediction(posts, account_analysis)
                if not next_post:  # Add fallback if prediction fails
                    logger.warning("Using fallback next post prediction")
                    next_post = {
                        "caption": "Check out our latest updates!",
                        "hashtags": ["#New", "#Update"],
                        "call_to_action": "Visit our profile for more",
                        "image_prompt": "Modern lifestyle image with vibrant colors"
                    }
                    
                # If rag_output has next_post with visual_prompt, use that instead
                if isinstance(rag_output, dict) and 'next_post' in rag_output and 'visual_prompt' in rag_output['next_post']:
                    logger.info("Using RAG visual prompt for next post")
                    if 'visual_prompt' not in next_post:
                        next_post['visual_prompt'] = rag_output['next_post'].get('visual_prompt')
                    else:
                        # If there's an image_prompt but no visual_prompt, rename it
                        if 'image_prompt' in next_post and 'visual_prompt' not in next_post:
                            next_post['visual_prompt'] = next_post.pop('image_prompt')
                
                # Generate improvement recommendations
                improvement_recs = self.generate_improvement_recommendations(account_analysis)
                if not improvement_recs:  # Add fallback
                    improvement_recs = [{"recommendation": "Post more consistently"}]
                
                # Identify competitors
                competitors = self.identify_competitors(posts, data.get('profile'))
                if not competitors:  # Add default
                    competitors = {"similar_accounts": []}
                
                # Add branding-specific elements to content plan
                content_plan.update({
                    'next_post_prediction': next_post,
                    'primary_analysis': primary_analysis,
                    'competitor_analysis': competitor_analysis,
                    'recommendations': recommendations,
                    'improvement_recommendations': improvement_recs,
                    'competitors': competitors,
                    'account_type': 'branding'  # Explicitly set account_type
                })
            else:
                # NON-BRANDING ACCOUNT FLOW
                # For non-branding accounts, incorporate news API data
                from news_api import NewsAPIClient
                
                # Get posting style from the account data if available
                posting_style = data.get('posting_style', 'informative')
                account_type_for_news = data.get('account_type', '')
                
                if not account_type_for_news and 'profile' in data:
                    account_type_for_news = data.get('profile', {}).get('account_type', '')
                
                # If still no account type, use a generic one
                if not account_type_for_news:
                    account_type_for_news = "general"
                
                # Fetch relevant news articles
                news_client = NewsAPIClient()
                news_articles = news_client.get_news_for_account(account_type_for_news, posting_style, limit=5)
                
                # Generate audience engagement strategies
                engagement_strategies = self._generate_engagement_strategies(posts, posting_style)
                
                # Generate next post prediction with news context
                next_post_with_news = self._generate_news_based_post(
                    primary_username, 
                    account_type_for_news, 
                    posting_style, 
                    news_articles[:1] if news_articles else []
                )
                
                # Generate RAG recommendations (no competitor analysis for non-branding)
                rag_output = self.rag.generate_recommendation(
                    primary_username=primary_username,
                    secondary_usernames=secondary_usernames,
                    query=query
                )
                
                # Extract primary analysis and recommendations from RAG output
                primary_analysis = rag_output.get('primary_analysis', 'No primary analysis available')
                recommendations = rag_output.get('recommendations', 'No recommendations available')
                
                # Add non-branding specific elements to content plan
                content_plan.update({
                    'next_post_prediction': next_post_with_news,
                    'primary_analysis': primary_analysis,
                    'recommendations': recommendations,
                    'news_articles': news_articles,
                    'engagement_strategies': engagement_strategies,
                    'account_type': 'non-branding'  # Explicitly set account_type
                })
            
            logger.info(f"Generated content plan for {'branding' if is_branding else 'non-branding'} account type")
            return content_plan
            
        except Exception as e:
            logger.error(f"Error generating content plan: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return None
    
    def _generate_engagement_strategies(self, posts, posting_style):
        """Generate audience engagement strategies for non-branding accounts.
        
        Args:
            posts: List of post dictionaries
            posting_style: Style of posting
            
        Returns:
            List of engagement strategies
        """
        try:
            # Analyze existing engagement patterns
            top_posts = sorted(posts, key=lambda x: x.get('engagement', 0), reverse=True)[:5]
            
            # Extract common elements from successful posts
            common_themes = []
            common_hashtags = set()
            
            for post in top_posts:
                # Extract hashtags
                if 'hashtags' in post:
                    if isinstance(post['hashtags'], list):
                        common_hashtags.update(post['hashtags'])
                    elif isinstance(post['hashtags'], str):
                        extracted = self.extract_hashtags(post['hashtags'])
                        common_hashtags.update(extracted)
        
            # Default strategies
            default_strategies = [
                {
                    "strategy": "Ask thought-provoking questions",
                    "implementation": "End posts with questions that prompt reflection or discussion",
                    "example": "What's your perspective on this? Share your thoughts below!"
                },
                {
                    "strategy": "Create interactive polls and quizzes",
                    "implementation": "Use platform features to poll your audience on relevant topics",
                    "example": "Which of these topics would you like to learn more about? Vote in our poll!"
                },
                {
                    "strategy": "Share behind-the-scenes content",
                    "implementation": "Give glimpses into your process to build authenticity",
                    "example": "Here's how I researched and prepared for this post on [topic]"
                },
                {
                    "strategy": "Respond to comments promptly",
                    "implementation": "Set aside time daily to engage with your audience's comments",
                    "example": "Thank you for sharing your perspective! That's an interesting point about..."
                },
                {
                    "strategy": "Create themed series",
                    "implementation": "Develop content series that followers can look forward to",
                    "example": "#MondayMotivation: Start each week with inspiring stories"
                }
            ]
            
            # Style-specific strategies
            style_specific = {
                "educational": [
                    {
                        "strategy": "Host Q&A sessions",
                        "implementation": "Schedule regular live Q&A sessions to address audience questions",
                        "example": "Join our monthly Q&A this Friday where I'll answer your questions about [topic]"
                    },
                    {
                        "strategy": "Create step-by-step tutorials",
                        "implementation": "Break down complex processes into easy-to-follow steps",
                        "example": "Here's a 5-step guide to understanding [concept]"
                    }
                ],
                "storytelling": [
                    {
                        "strategy": "Use narrative arcs",
                        "implementation": "Structure content with clear beginnings, middles, and ends",
                        "example": "When I first started [activity], I never imagined where it would lead..."
                    },
                    {
                        "strategy": "Invite audience stories",
                        "implementation": "Encourage followers to share their related experiences",
                        "example": "What's your story with [topic]? Share in the comments!"
                    }
                ],
                "informative": [
                    {
                        "strategy": "Share data visualizations",
                        "implementation": "Present complex information in visual formats",
                        "example": "This graph shows the trends in [topic] over the past decade"
                    },
                    {
                        "strategy": "Debunk myths",
                        "implementation": "Address common misconceptions in your field",
                        "example": "Contrary to popular belief, [fact] is actually [correction]"
                    }
                ]
            }
            
            # Combine default strategies with style-specific ones
            strategies = default_strategies.copy()
            
            posting_style_lower = posting_style.lower() if posting_style else ""
            for style, style_strategies in style_specific.items():
                if style in posting_style_lower:
                    strategies.extend(style_strategies)
                    break
            
            # Ensure we have exactly 5 strategies
            if len(strategies) > 5:
                strategies = strategies[:5]
            while len(strategies) < 5:
                strategies.append({
                    "strategy": f"Engage with related content",
                    "implementation": "Comment on and share content from related accounts",
                    "example": "Check out this great perspective from @related_account"
                })
            
            return strategies
            
        except Exception as e:
            logger.error(f"Error generating engagement strategies: {str(e)}")
            return [
                {
                    "strategy": "Ask questions to encourage comments",
                    "implementation": "End posts with a question related to the content",
                    "example": "What do you think about this? Share in the comments!"
                }
            ] * 5  # Return 5 copies of the same basic strategy as fallback

    def _generate_news_based_post(self, username, account_type, posting_style, news_articles):
        """Generate a post based on news for non-branding accounts.
        
        Args:
            username: Account username
            account_type: Type of account
            posting_style: Style of posting
            news_articles: List of news articles
            
        Returns:
            Dictionary with next post prediction
        """
        try:
            if not news_articles:
                # Fallback if no news articles are available
                return {
                    "caption": f"Stay updated on the latest in {account_type.replace('_', ' ')}!",
                    "hashtags": [f"#{account_type.replace('_', '')}", "#LatestNews", "#StayInformed"],
                    "call_to_action": "What topics would you like to see covered next? Let us know in the comments!",
                    "image_prompt": f"A visually engaging image related to {account_type.replace('_', ' ')} with modern design elements"
                }
            
            # Use the first news article as the basis for the post
            article = news_articles[0]
            title = article.get('title', '')
            
            # Create a hashtag from the account type
            account_hashtag = f"#{account_type.replace('_', '')}"
            
            # Extract potential hashtags from the title
            words = re.findall(r'\b[A-Za-z]{4,}\b', title)
            topic_hashtags = [f"#{word}" for word in words[:3]]
            
            # Add generic hashtags
            generic_hashtags = ["#News", "#Update", "#LatestTrends"]
            
            # Combine all hashtags and take up to 5
            all_hashtags = [account_hashtag] + topic_hashtags + generic_hashtags
            unique_hashtags = []
            for tag in all_hashtags:
                if tag not in unique_hashtags:
                    unique_hashtags.append(tag)
            hashtags = unique_hashtags[:5]
            
            # Create caption based on posting style
            posting_style_lower = posting_style.lower() if posting_style else ""
            
            if "educational" in posting_style_lower:
                caption = f"📚 Learning opportunity: {title} Here's what you need to know about this development."
                call_to_action = "What aspects of this topic would you like to learn more about? Let me know in the comments!"
            elif "storytelling" in posting_style_lower:
                caption = f"📖 Here's an interesting story: {title} This caught my attention because of its significance."
                call_to_action = "Have you had any experiences related to this? Share your story in the comments!"
            elif "informative" in posting_style_lower:
                caption = f"📣 Important update: {title} Here are the key facts you should be aware of."
                call_to_action = "What are your thoughts on this development? Share your perspective below!"
            else:
                caption = f"📲 Trending now: {title} I thought this was worth sharing with you all."
                call_to_action = "What do you think about this? Drop your comments below!"
            
            # Add the link to the original article
            if article.get('link'):
                caption += f" Read more at the link in bio!"
            
            return {
                "caption": caption,
                "hashtags": hashtags,
                "call_to_action": call_to_action,
                "image_prompt": f"A high-quality image representing {title}",
                "source_article": article
            }
            
        except Exception as e:
            logger.error(f"Error generating news-based post: {str(e)}")
            return {
                "caption": "Check out this interesting development in our field!",
                "hashtags": ["#News", "#Update", "#StayInformed"],
                "call_to_action": "What topics would you like to see covered next?",
                "image_prompt": "A modern, professional image related to the topic"
            }
    
    def generate_batch_recommendations(self, topics, n_per_topic=3):
        """
        Generate batch recommendations for multiple topics.
        
        Args:
            topics: List of topics to generate recommendations for
            n_per_topic: Number of recommendations per topic
            
        Returns:
            Dictionary with recommendations by topic
        """
        try:
            return self.generate_recommendations(topics, n_per_topic)
        except Exception as e:
            logger.error(f"Error generating batch recommendations: {str(e)}")
            return {}


# Test function
def test_recommendation_generation():
    """Test the recommendation generation functionality."""
    try:
        # Create generator
        generator = RecommendationGenerator()
        
        # Test hashtag extraction
        text = "Check out our summer sale! #SummerSale #Discount"
        hashtags = generator.extract_hashtags(text)
        if len(hashtags) != 2:
            logger.warning(f"Expected 2 hashtags, got {len(hashtags)}")
        
        # Test caption formatting
        formatted = generator.format_caption(text)
        if formatted["caption"] != "Check out our summer sale!":
            logger.warning(f"Caption formatting issue: {formatted['caption']}")
        
        # Test template application
        recommendation = {
            "caption": "New summer collection available now!",
            "hashtags": ["#Summer", "#NewCollection"]
        }
        formatted = generator.apply_template(recommendation, "promotional")
        if "New summer collection available now!" not in formatted:
            logger.warning(f"Template application issue: {formatted}")
        
        # Test recommendation generation
        topics = ["summer fashion", "fall trends"]
        recommendations = generator.generate_recommendations(topics)
        
        if len(recommendations) == len(topics):
            logger.info("Recommendation generation test successful")
            return True
        else:
            logger.warning("Recommendation count mismatch")
            return False
            
    except Exception as e:
        logger.error(f"Recommendation generation test failed: {str(e)}")
        return False


if __name__ == "__main__":
    # Test recommendation generation
    success = test_recommendation_generation()
    print(f"Recommendation generation test {'successful' if success else 'failed'}")