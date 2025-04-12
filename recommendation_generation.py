"""Module for generating content recommendations."""

import logging
import re
import json
from rag_implementation import RagImplementation
from time_series_analysis import TimeSeriesAnalyzer
from config import CONTENT_TEMPLATES, LOGGING_CONFIG
from datetime import datetime
import pandas as pd
from collections import Counter
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer

# Download required NLTK data
try:
    nltk.download('vader_lexicon', quiet=True)
except Exception as e:
    logging.warning(f"Failed to download NLTK data: {str(e)}")

# Set up logging
logging.basicConfig(
    level=LOGGING_CONFIG['level'],
    format=LOGGING_CONFIG['format']
)
logger = logging.getLogger(__name__)

class RecommendationGenerator:
    """Class for generating content recommendations with competitor-aware strategies."""
    
    def __init__(self, rag=None, time_series=None, templates=CONTENT_TEMPLATES):
        """Initialize with necessary components."""
        self.rag = rag or RagImplementation()
        self.time_series = time_series or TimeSeriesAnalyzer()
        self.templates = templates
        self.sentiment_analyzer = SentimentIntensityAnalyzer()
        logger.info("RecommendationGenerator initialized with sentiment analysis capabilities.")
    
    def extract_hashtags(self, text):
        """Extract hashtags from text."""
        try:
            hashtags = re.findall(r'#\w+', text)
            return hashtags if hashtags else []
        except Exception as e:
            logger.error(f"Error extracting hashtags: {str(e)}")
            return []
    
    def format_caption(self, raw_text):
        """Format caption by separating hashtags."""
        try:
            hashtags = self.extract_hashtags(raw_text)
            caption = re.sub(r'#\w+', '', raw_text).strip()
            return {"caption": caption, "hashtags": hashtags}
        except Exception as e:
            logger.error(f"Error formatting caption: {str(e)}")
            return {"caption": raw_text, "hashtags": []}
    
    def apply_template(self, recommendation, template_key="promotional"):
        """Apply a template to a recommendation."""
        try:
            template = self.templates.get(template_key, '{caption} {hashtags}')
            caption = recommendation.get("caption", "")
            hashtags = recommendation.get("hashtags", [])
            hashtags_str = " ".join(hashtags)
            formatted = template.format(caption=caption, hashtags=hashtags_str)
            return formatted
        except Exception as e:
            logger.error(f"Error applying template: {str(e)}")
            return f"{recommendation.get('caption', '')} {' '.join(recommendation.get('hashtags', []))}"
    
    def analyze_sentiment(self, text):
        """Analyze sentiment of a given text."""
        try:
            scores = self.sentiment_analyzer.polarity_scores(text)
            sentiment = "positive" if scores['compound'] > 0.05 else "negative" if scores['compound'] < -0.05 else "neutral"
            return {"sentiment": sentiment, "scores": scores}
        except Exception as e:
            logger.error(f"Error analyzing sentiment: {str(e)}")
            return {"sentiment": "unknown", "scores": {"compound": 0}}
    
    def generate_trending_topics(self, data, timestamp_col='timestamp', value_col='engagement', top_n=5):
        """Generate trending topics based on time series analysis."""
        try:
            if not data:
                logger.warning("No data provided for trending topics analysis.")
                return self._generate_default_trending_topics(top_n)
                
            # Standardize data format for time series analysis
            df = None
            
            # Handle different input data formats
            if isinstance(data, dict):
                df = pd.DataFrame.from_dict(data, orient='index').reset_index()
                if len(df.columns) == 2:  # Simple dict conversion
                    df.columns = [timestamp_col, value_col]
            elif isinstance(data, pd.DataFrame):
                if timestamp_col in data.columns and value_col in data.columns:
                    df = data[[timestamp_col, value_col]].copy()
                else:
                    available_cols = data.columns.tolist()
                    logger.warning(f"DataFrame missing required columns: {timestamp_col} or {value_col}. Columns found: {available_cols}")
                    # Try to find suitable columns
                    time_cols = [col for col in available_cols if 'time' in col.lower() or 'date' in col.lower()]
                    value_cols = [col for col in available_cols if 'value' in col.lower() or 'engagement' in col.lower() or 'count' in col.lower()]
                    
                    if time_cols and value_cols:
                        logger.info(f"Using {time_cols[0]} as timestamp and {value_cols[0]} as value")
                        df = data[[time_cols[0], value_cols[0]]].copy()
                        df.columns = [timestamp_col, value_col]
                    else:
                        return self._generate_default_trending_topics(top_n)
            
            if df is None:
                logger.warning(f"Failed to convert data to DataFrame: {type(data)}")
                return self._generate_default_trending_topics(top_n)
                
            # Ensure timestamp is datetime
            try:
                df[timestamp_col] = pd.to_datetime(df[timestamp_col])
            except Exception as e:
                logger.warning(f"Failed to convert timestamps: {str(e)}")
                return self._generate_default_trending_topics(top_n)
            
            # Analyze with time series model
            results = self.time_series.analyze_data(df, timestamp_col, value_col)
            if not results or 'trending_periods' not in results:
                logger.warning("No trending periods detected in analysis.")
                return self._generate_default_trending_topics(top_n)
                
            trending_periods = list(results['trending_periods'].iterrows())[:top_n]
            if not trending_periods:
                logger.warning("No trending periods detected.")
                return self._generate_default_trending_topics(top_n)
                
            trending_topics = []
            for i, row in enumerate(trending_periods):
                date_str = row[1]['ds'].strftime('%B %d')
                # Create more meaningful trending topics based on index/position
                if i == 0:
                    topic = f"Spring Beauty Essentials (Trending on {date_str})"
                elif i == 1:
                    topic = f"Limited Edition Collections (Trending on {date_str})"
                elif i == 2:
                    topic = f"Seasonal Color Trends (Trending on {date_str})"
                elif i == 3:
                    topic = f"Celebrity Collaborations (Trending on {date_str})"
                else:
                    topic = f"Trending on {date_str}"
                
                trending_topics.append({
                    'date': row[1]['ds'].strftime('%Y-%m-%d'),
                    'value': row[1]['yhat'],
                    'topic': topic
                })
            
            logger.info(f"Generated {len(trending_topics)} trending topics.")
            return trending_topics
        except Exception as e:
            logger.error(f"Error generating trending topics: {str(e)}")
            return self._generate_default_trending_topics(top_n)
            
    def _generate_default_trending_topics(self, count=5):
        """Generate default trending topics when analysis fails."""
        today = datetime.now()
        beauty_topics = [
            "Spring Makeup Essentials",
            "Bold Lip Colors",
            "Natural Skincare Routines",
            "Eye Palette Trends",
            "Sustainable Beauty Products",
            "Celebrity Beauty Lines",
            "Viral Beauty Hacks",
            "Seasonal Color Trends",
            "Limited Edition Collections",
            "Beauty Tool Innovations"
        ]
        
        return [
            {
                'date': (today + pd.Timedelta(days=i)).strftime('%Y-%m-%d'),
                'value': 1000 - (i * 50),
                'topic': beauty_topics[i % len(beauty_topics)]
            }
            for i in range(count)
        ]
    
    def generate_recommendations(self, primary_username, secondary_usernames, query):
        """Generate comprehensive recommendations using RAG with four-block structure."""
        try:
            if not primary_username or not isinstance(secondary_usernames, list) or not query:
                logger.error("Invalid input: primary_username, secondary_usernames, or query missing.")
                return self._generate_fallback_recommendation(primary_username, query)
            
            recommendation = self.rag.generate_recommendation(primary_username, secondary_usernames, query)
            required_blocks = ["primary_analysis", "competitor_analysis", "recommendations", "next_post"]
            missing_blocks = [block for block in required_blocks if block not in recommendation]
            if missing_blocks:
                logger.warning(f"Missing blocks in recommendation: {missing_blocks}. Using fallback.")
                return self._generate_fallback_recommendation(primary_username, query)
            
            next_post_fields = ["caption", "hashtags", "call_to_action", "visual_prompt"]
            missing_fields = [field for field in next_post_fields if field not in recommendation["next_post"]]
            if missing_fields:
                logger.warning(f"Missing next_post fields: {missing_fields}. Filling defaults.")
                for field in missing_fields:
                    recommendation["next_post"][field] = self._default_next_post_field(field, query)
            
            logger.info(f"Generated recommendation for {primary_username} with query: {query}")
            return recommendation
        except Exception as e:
            logger.error(f"Error in generate_recommendations: {str(e)}")
            return self._generate_fallback_recommendation(primary_username, query)
    
    def generate_batch_recommendations(self, topics, n_per_topic=3):
        """Generate content recommendations for multiple topics."""
        try:
            if not topics or n_per_topic <= 0:
                logger.warning("Invalid input for batch recommendations.")
                return {}
            valid_topics = [str(t).strip() for t in topics if str(t).strip()]
            if not valid_topics:
                logger.error("No valid topics provided.")
                return {}
            
            combined_prompt = self._create_batch_prompt(valid_topics, n_per_topic)
            batch_response = self.rag.generate_recommendation("", [], combined_prompt)
            if isinstance(batch_response, str):
                batch_response = json.loads(batch_response)
            
            recommendations = {}
            for topic in valid_topics:
                if topic in batch_response:
                    topic_recs = batch_response[topic]
                    while len(topic_recs) < n_per_topic:
                        additional_rec = self.rag.generate_recommendation("", [], f"Generate one recommendation for {topic}")
                        if isinstance(additional_rec, str):
                            additional_rec = json.loads(additional_rec)
                        topic_recs.append(additional_rec)
                    recommendations[topic] = topic_recs[:n_per_topic]
                else:
                    logger.warning(f"Topic {topic} not in batch response, generating individually.")
                    recommendations[topic] = []
                    for _ in range(n_per_topic):
                        rec = self.rag.generate_recommendation("", [], f"Generate one recommendation for {topic}")
                        if isinstance(rec, str):
                            rec = json.loads(rec)
                        recommendations[topic].append(rec)
            
            logger.info(f"Generated batch recommendations for {len(valid_topics)} topics.")
            logger.debug(f"Batch recommendations: {json.dumps(recommendations, indent=2)}")
            return recommendations
        except Exception as e:
            logger.error(f"Error in generate_batch_recommendations: {str(e)}")
            return {t: [{"caption": f"Explore {t}", "hashtags": [f"#{t.replace(' ', '')}"], "call_to_action": "Check it out!"}] * n_per_topic for t in topics}
    
    def _create_batch_prompt(self, topics, n_per_topic):
        """Create a prompt for batch recommendation generation."""
        # Sanitize topics to remove problematic characters
        sanitized_topics = []
        for topic in topics:
            # Strip dates and parenthetical content for cleaner prompt
            cleaned = re.sub(r'\(.*?\)', '', str(topic)).strip()
            # Further clean any problematic characters
            cleaned = re.sub(r'[%{}]', '', cleaned)
            sanitized_topics.append(cleaned)
            
        topics_str = ", ".join([f'"{t}"' for t in sanitized_topics])
        
        prompt = f"""
        You are an expert social media content creator specializing in beauty and cosmetics. 
        Generate beauty-focused recommendations for these topics: {topics_str}.
        
        For each topic, provide {n_per_topic} beauty content ideas, each including:
        1. An attention-grabbing caption about the beauty topic
        2. Relevant beauty-related hashtags (as a list)
        3. A compelling call to action for beauty enthusiasts
        
        Return as JSON with topics as keys and arrays of recommendations as values.
        Example format: 
        {{
          "Topic 1": [
            {{
              "caption": "Your glowing skin starts here! Our new collection...",
              "hashtags": ["#BeautyEssentials", "#GlowingSkin"],
              "call_to_action": "Shop now for radiant results!"
            }}
          ]
        }}
        
        Make each recommendation unique and focused on beauty industry best practices.
        """
        return prompt
    
    def _generate_fallback_recommendation(self, primary_username, query):
        """Generate a fallback recommendation if RAG fails."""
        return {
            "primary_analysis": f"Unable to analyze {primary_username} due to processing issues.",
            "competitor_analysis": {},
            "recommendations": f"Focus on {query} with high-quality visuals and engagement tactics.",
            "next_post": {
                "caption": f"Discover the latest {query} from {primary_username}!",
                "hashtags": [f"#{query.replace(' ', '')}", "#Trending", "#Explore"],
                "call_to_action": "Tell us what you think in the comments!",
                "visual_prompt": f"A bold, colorful image showcasing {query} trends"
            }
        }
    
    def _default_next_post_field(self, field, query):
        """Provide default values for missing next_post fields."""
        defaults = {
            "caption": f"Explore {query} now!",
            "hashtags": [f"#{query.replace(' ', '')}", "#Trend"],
            "call_to_action": "Check it out below!",
            "visual_prompt": f"A vibrant graphic related to {query}"
        }
        return defaults.get(field, "")
    
    def analyze_account_type(self, posts):
        """Analyze if the account is for branding or personal use."""
        try:
            if not posts:
                return {"account_type": "Unknown", "confidence": 0, "analysis": "No posts provided."}
            
            captions = [post.get('caption', '') for post in posts]
            hashtags = []
            for post in posts:
                caption_hashtags = self.extract_hashtags(post.get('caption', ''))
                post_hashtags = post.get('hashtags', [])
                if isinstance(post_hashtags, str):
                    post_hashtags = self.extract_hashtags(post_hashtags)
                hashtags.extend(caption_hashtags + (post_hashtags if isinstance(post_hashtags, list) else []))
            
            business_terms = ['product', 'sale', 'brand', 'shop', 'buy', 'launch']
            business_hashtags = ['#business', '#brand', '#product', '#sale', '#shop']
            
            business_count = sum(any(term in caption.lower() for term in business_terms) for caption in captions)
            business_hashtag_count = sum(any(bh in hashtag.lower() for bh in business_hashtags) for hashtag in hashtags)
            
            total_posts = len(posts)
            business_caption_percentage = (business_count / total_posts) * 100 if total_posts else 0
            
            if business_caption_percentage > 60 or business_hashtag_count > total_posts * 0.5:
                account_type = "Business/Brand"
                confidence = min(100, max(60, business_caption_percentage + business_hashtag_count * 5))
                analysis = f"Business/Brand detected: {business_count} posts with business terms, {business_hashtag_count} business hashtags."
            else:
                account_type = "Personal"
                confidence = min(100, max(60, 100 - business_caption_percentage))
                analysis = f"Personal use likely: Only {business_count}/{total_posts} posts suggest business intent."
            
            return {"account_type": account_type, "confidence": confidence, "analysis": analysis}
        except Exception as e:
            logger.error(f"Error analyzing account type: {str(e)}")
            return {"account_type": "Unknown", "confidence": 0, "analysis": f"Error: {str(e)}"}
    
    def analyze_engagement(self, posts):
        """Analyze engagement patterns across content types and categories."""
        try:
            if not posts:
                return {"summary": "No posts to analyze."}
            
            content_types = {'photo': [], 'video': [], 'carousel': [], 'text_only': []}
            hashtag_categories = {
                'product': ['#product', '#sale', '#shop'],
                'lifestyle': ['#lifestyle', '#daily'],
                'fashion': ['#fashion', '#style'],
                'beauty': ['#makeup', '#beauty']
            }
            category_engagement = {cat: {'count': 0, 'total': 0} for cat in hashtag_categories}
            
            for post in posts:
                post_type = post.get('media_type', 'photo').lower()
                content_types.get(post_type, content_types['photo']).append(post)
                
                engagement = post.get('engagement', post.get('likes', 0) + post.get('comments', 0))
                hashtags = self.extract_hashtags(post.get('caption', '') + " ".join(post.get('hashtags', []) if isinstance(post.get('hashtags', []), list) else []))
                
                for category, tags in hashtag_categories.items():
                    if any(tag.lower() in [h.lower() for h in hashtags] for tag in tags):
                        category_engagement[category]['count'] += 1
                        category_engagement[category]['total'] += engagement
            
            content_type_analysis = {
                t: {
                    'count': len(posts_list),
                    'total_engagement': sum(p.get('engagement', 0) for p in posts_list),
                    'avg_engagement': sum(p.get('engagement', 0) for p in posts_list) / len(posts_list) if posts_list else 0
                }
                for t, posts_list in content_types.items() if posts_list
            }
            category_analysis = {
                c: {
                    'count': data['count'],
                    'total_engagement': data['total'],
                    'avg_engagement': data['total'] / data['count'] if data['count'] else 0
                }
                for c, data in category_engagement.items() if data['count']
            }
            
            best_type = max(content_type_analysis.items(), key=lambda x: x[1]['avg_engagement'], default=(None, {'avg_engagement': 0}))[0]
            best_category = max(category_analysis.items(), key=lambda x: x[1]['avg_engagement'], default=(None, {'avg_engagement': 0}))[0]
            
            summary = f"Best content type: {best_type or 'N/A'} (avg engagement: {content_type_analysis.get(best_type, {}).get('avg_engagement', 0):.1f}). Best category: {best_category or 'N/A'} (avg engagement: {category_analysis.get(best_category, {}).get('avg_engagement', 0):.1f})."
            return {
                'content_type_analysis': content_type_analysis,
                'category_analysis': category_analysis,
                'best_type': best_type,
                'best_category': best_category,
                'summary': summary
            }
        except Exception as e:
            logger.error(f"Error analyzing engagement: {str(e)}")
            return {"summary": f"Error: {str(e)}"}
    
    def analyze_posting_trends(self, posts):
        """Analyze posting patterns and frequency."""
        try:
            if not posts:
                return {"summary": "No posts to analyze."}
            
            timestamps = [pd.to_datetime(post.get('timestamp')) for post in posts if post.get('timestamp')]
            if not timestamps:
                return {"summary": "No valid timestamps."}
            
            df = pd.DataFrame({'timestamp': timestamps})
            df['day_of_week'] = df['timestamp'].dt.day_name()
            df['hour'] = df['timestamp'].dt.hour
            df['month'] = df['timestamp'].dt.month
            
            day_counts = df['day_of_week'].value_counts().to_dict()
            hour_counts = df['hour'].value_counts().to_dict()
            month_counts = df['month'].value_counts().to_dict()
            
            most_common_day = max(day_counts.items(), key=lambda x: x[1])[0]
            most_common_hour = max(hour_counts.items(), key=lambda x: x[1])[0]
            hour_formatted = f"{most_common_hour % 12 or 12} {'AM' if most_common_hour < 12 else 'PM'}"
            
            days_range = (max(timestamps) - min(timestamps)).days + 1
            posts_per_day = len(timestamps) / days_range if days_range > 0 else 0
            
            avg_posts_per_month = len(timestamps) / 12
            high_activity_months = {month: count for month, count in month_counts.items() if count > avg_posts_per_month * 1.2}
            month_names = {1: 'Jan', 2: 'Feb', 3: 'Mar', 4: 'Apr', 5: 'May', 6: 'Jun', 7: 'Jul', 8: 'Aug', 9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Dec'}
            high_activity_named = {month_names[m]: c for m, c in high_activity_months.items()}
            
            summary = f"Most active: {most_common_day}s at {hour_formatted}. Frequency: {posts_per_day:.1f} posts/day. High activity: {', '.join(high_activity_named.keys()) or 'None'}."
            return {
                'most_active_day': most_common_day,
                'most_active_hour': hour_formatted,
                'posts_per_day': posts_per_day,
                'day_distribution': day_counts,
                'hour_distribution': hour_counts,
                'high_activity_months': high_activity_named,
                'summary': summary
            }
        except Exception as e:
            logger.error(f"Error analyzing posting trends: {str(e)}")
            return {"summary": f"Error: {str(e)}"}
    
    def generate_next_post_prediction(self, posts, account_analysis=None):
        """Generate predictions for the next post."""
        try:
            recent_captions = [post.get('caption', '') for post in posts[-5:] if 'caption' in post]
            all_hashtags = [h for post in posts for h in self.extract_hashtags(post.get('caption', '') + " ".join(post.get('hashtags', []) if isinstance(post.get('hashtags', []), list) else []))]
            
            hashtag_counts = Counter(all_hashtags)
            common_hashtags = [tag for tag, _ in hashtag_counts.most_common(10)]
            
            context = "\n".join([f"Recent caption: {c}" for c in recent_captions])
            context += f"\nCommon hashtags: {', '.join(common_hashtags)}"
            if account_analysis:
                context += f"\nAccount type: {account_analysis.get('account_type', {}).get('account_type', 'Unknown')}"
                context += f"\nEngagement summary: {account_analysis.get('engagement', {}).get('summary', 'N/A')}"
                context += f"\nPosting trends: {account_analysis.get('posting_trends', {}).get('summary', 'N/A')}"
            
            prompt = f"""
            Based on this Instagram account context:
            {context}
            Generate a next post prediction with:
            1. Caption matching their style
            2. Relevant hashtags
            3. Consistent call to action
            4. Detailed image prompt for AI generator
            Format as JSON: {{"caption": "", "hashtags": [], "call_to_action": "", "visual_prompt": ""}}
            """
            prediction = self.rag.generate_recommendation("", [], prompt)
            return prediction if isinstance(prediction, dict) else json.loads(prediction)
        except Exception as e:
            logger.error(f"Error generating next post prediction: {str(e)}")
            return {
                "caption": "Explore our latest!",
                "hashtags": ["#New", "#Trend"],
                "call_to_action": "Check it out!",
                "visual_prompt": "Vibrant promotional image"
            }
    
    def identify_competitors(self, posts, profile_info=None):
        """Identify potential competitors based on content."""
        try:
            all_hashtags = [h for post in posts for h in self.extract_hashtags(post.get('caption', '') + " ".join(post.get('hashtags', []) if isinstance(post.get('hashtags', []), list) else []))]
            mentions = [m for post in posts for m in re.findall(r'@(\w+)', post.get('caption', ''))]
            
            hashtag_counts = Counter(all_hashtags).most_common(20)
            mention_counts = Counter(mentions).most_common(20)
            
            context = f"Top hashtags: {', '.join([h[0] for h in hashtag_counts[:10]])}"
            context += f"\nTop mentions: {', '.join([m[0] for m in mention_counts[:5]])}"
            if profile_info:
                context += f"\nBio: {profile_info.get('bio', '')}\nCategory: {profile_info.get('category', '')}"
            
            prompt = f"""
            Based on this Instagram account:
            {context}
            Identify 10 competitors with:
            1. Account name
            2. Reason for competition
            3. Unique value
            Format as JSON array: [{{"account_name": "", "reason": "", "unique_value": ""}}, ...]
            """
            response = self.rag.generate_recommendation("", [], prompt)
            competitors = response if isinstance(response, list) else response.get("competitors", [])
            while len(competitors) < 10:
                competitors.append({"account_name": f"competitor_{len(competitors)+1}", "reason": "Similar niche", "unique_value": "Unique style"})
            return competitors[:10]
        except Exception as e:
            logger.error(f"Error identifying competitors: {str(e)}")
            return [{"account_name": f"competitor_{i+1}", "reason": "Similar content", "unique_value": "Different approach"} for i in range(10)]
    
    def generate_improvement_recommendations(self, account_analysis):
        """Generate improvement recommendations."""
        try:
            context = ""
            if 'account_type' in account_analysis:
                context += f"Account type: {account_analysis['account_type'].get('account_type', 'Unknown')}\n{account_analysis['account_type'].get('analysis', '')}"
            if 'engagement' in account_analysis:
                context += f"\nEngagement: {account_analysis['engagement'].get('summary', 'N/A')}"
            if 'posting_trends' in account_analysis:
                context += f"\nPosting trends: {account_analysis['posting_trends'].get('summary', 'N/A')}"
            
            prompt = f"""
            Based on this analysis:
            {context}
            Generate 5 actionable recommendations with:
            1. Action item
            2. Reasoning
            3. Implementation steps
            Format as JSON array: [{{"recommendation": "", "reasoning": "", "implementation": ""}}, ...]
            """
            response = self.rag.generate_recommendation("", [], prompt)
            recommendations = response if isinstance(response, list) else response.get("recommendations", [])
            while len(recommendations) < 5:
                recommendations.append({"recommendation": "Post consistently", "reasoning": "Maintains engagement", "implementation": "Use a scheduler"})
            return recommendations[:5]
        except Exception as e:
            logger.error(f"Error generating improvement recommendations: {str(e)}")
            return [{"recommendation": "Post consistently", "reasoning": "Maintains engagement", "implementation": "Use a scheduler"}] * 5
    
    def analyze_hashtag_effectiveness(self, posts):
        """Analyze hashtag effectiveness based on engagement."""
        try:
            hashtag_engagement = {}
            for post in posts:
                hashtags = self.extract_hashtags(post.get('caption', '') + " ".join(post.get('hashtags', []) if isinstance(post.get('hashtags', []), list) else []))
                engagement = post.get('engagement', post.get('likes', 0) + post.get('comments', 0))
                for hashtag in hashtags:
                    if hashtag not in hashtag_engagement:
                        hashtag_engagement[hashtag] = {"count": 0, "total_engagement": 0}
                    hashtag_engagement[hashtag]["count"] += 1
                    hashtag_engagement[hashtag]["total_engagement"] += engagement
            
            effectiveness = {
                h: {
                    "count": data["count"],
                    "total_engagement": data["total_engagement"],
                    "avg_engagement": data["total_engagement"] / data["count"]
                }
                for h, data in hashtag_engagement.items()
            }
            top_hashtags = sorted(effectiveness.items(), key=lambda x: x[1]["avg_engagement"], reverse=True)[:5]
            return {"top_hashtags": dict(top_hashtags), "summary": f"Top 5 hashtags by avg engagement: {', '.join([h[0] for h in top_hashtags])}"}
        except Exception as e:
            logger.error(f"Error analyzing hashtag effectiveness: {str(e)}")
            return {"top_hashtags": {}, "summary": "Error in analysis"}
    
    def generate_content_plan(self, primary_username, secondary_usernames, query, posts):
        """Generate a complete content plan with RAG-driven four-block structure."""
        try:
            if not all([posts, primary_username]):
                logger.error("Missing required inputs for content plan.")
                return None
            
            # If secondary_usernames not provided or empty, try to identify them
            if not secondary_usernames or len(secondary_usernames) == 0:
                identified_competitors = self.identify_competitors(posts)
                secondary_usernames = [comp['username'] for comp in identified_competitors[:5]]
                logger.info(f"Using identified competitors: {secondary_usernames}")
            
            # Extract posts by username for separate analysis
            primary_posts = [p for p in posts if p.get('username', '') == primary_username]
            competitor_posts = [p for p in posts if p.get('username', '') != primary_username and p.get('username', '') in secondary_usernames]
            
            # Process with enhanced competitor context
            account_type = self.analyze_account_type(primary_posts)
            engagement_analysis = self.analyze_engagement(primary_posts)
            posting_trends = self.analyze_posting_trends(primary_posts)
            hashtag_effectiveness = self.analyze_hashtag_effectiveness(primary_posts)
            
            # Add more competitor context to the RAG input
            competitor_context = {}
            for username in secondary_usernames:
                user_posts = [p for p in posts if p.get('username', '') == username]
                if user_posts:
                    competitor_context[username] = {
                        'post_count': len(user_posts),
                        'avg_engagement': sum(p.get('engagement', 0) for p in user_posts) / len(user_posts),
                        'top_hashtags': self._extract_top_hashtags(user_posts, 5),
                        'posting_frequency': self._calculate_posting_frequency(user_posts)
                    }
            
            # Generate trending topics for beauty industry
            trending_topics = None
            if primary_posts and any('engagement' in p for p in primary_posts):
                engagement_data = {p['timestamp']: p['engagement'] for p in primary_posts if 'timestamp' in p and 'engagement' in p}
                trending_topics = self.generate_trending_topics(engagement_data, top_n=3)
                if trending_topics:
                    logger.info(f"Generated {len(trending_topics)} trending topics for beauty industry")
                else:
                    # Use default beauty topics if trending analysis fails
                    trending_topics = self._generate_default_trending_topics(3)
                    logger.info("Using default beauty trending topics")
            else:
                trending_topics = self._generate_default_trending_topics(3)
                logger.info("Using default beauty trending topics due to insufficient engagement data")
            
            # Generate the intelligence-focused recommendations
            recommendation = self.generate_recommendations(primary_username, secondary_usernames, query)
            
            # Create more insightful content plan with intelligence focus
            content_plan = {
                'generated_date': datetime.now().isoformat(),
                'primary_analysis': {
                    'account_type': account_type,
                    'engagement': engagement_analysis,
                    'posting_trends': posting_trends,
                    'hashtag_effectiveness': hashtag_effectiveness,
                    'rag_analysis': recommendation["primary_analysis"]
                },
                'competitor_analysis': recommendation["competitor_analysis"],
                'recommendations': recommendation["recommendations"],
                'next_post_prediction': recommendation["next_post"],
                'additional_insights': {
                    'competitor_metrics': competitor_context,
                    'next_post_alternative': self.generate_next_post_prediction(primary_posts, 
                                                    {'account_type': account_type, 
                                                    'engagement': engagement_analysis, 
                                                    'posting_trends': posting_trends,
                                                    'competitor_context': competitor_context}),
                    'competitors': self.identify_competitors(posts, {'primary_username': primary_username}),
                    'improvements': self.generate_improvement_recommendations({
                                                    'account_type': account_type, 
                                                    'engagement': engagement_analysis, 
                                                    'posting_trends': posting_trends,
                                                    'competitor_metrics': competitor_context})
                }
            }
            
            # Add trending topics and batch recommendations
            if trending_topics:
                content_plan['trending_topics'] = trending_topics
                
                # Extract just the topic names for batch recommendations
                trend_topics = [topic['topic'] for topic in trending_topics]
                
                try:
                    # Generate batch recommendations for trending topics
                    batch_recs = self.generate_batch_recommendations(trend_topics, n_per_topic=3)
                    if batch_recs:
                        content_plan['batch_recommendations'] = batch_recs
                        logger.info(f"Generated batch recommendations for {len(trend_topics)} trending topics")
                except Exception as e:
                    logger.error(f"Error generating batch recommendations: {str(e)}")
                    # Create fallback recommendations
                    content_plan['batch_recommendations'] = {
                        topic: [{
                            "caption": f"Explore the latest in {topic}!",
                            "hashtags": [f"#{re.sub(r'[^a-zA-Z0-9]', '', topic)}", "#Beauty", "#MustTry"],
                            "call_to_action": "Shop now for limited time deals!"
                        }] * 3 for topic in trend_topics
                    }
            
            logger.info(f"Generated intelligence-focused content plan for {primary_username} against {len(secondary_usernames)} competitors")
            return content_plan
        except Exception as e:
            logger.error(f"Error generating content plan: {str(e)}")
            return None
            
    def _extract_top_hashtags(self, posts, limit=5):
        """Extract top hashtags from posts."""
        all_hashtags = []
        for post in posts:
            if 'hashtags' in post:
                if isinstance(post['hashtags'], list):
                    all_hashtags.extend(post['hashtags'])
                elif isinstance(post['hashtags'], str):
                    all_hashtags.extend(self.extract_hashtags(post['hashtags']))
            if 'caption' in post:
                all_hashtags.extend(self.extract_hashtags(post['caption']))
        
        # Count and get top hashtags
        hashtag_counter = Counter(all_hashtags)
        return [tag for tag, count in hashtag_counter.most_common(limit)]
        
    def _calculate_posting_frequency(self, posts):
        """Calculate posting frequency from timestamps."""
        if not posts or len(posts) < 2:
            return "Insufficient data"
            
        timestamps = []
        for post in posts:
            if 'timestamp' in post:
                try:
                    ts = pd.to_datetime(post['timestamp'])
                    timestamps.append(ts)
                except:
                    pass
                    
        if len(timestamps) < 2:
            return "Insufficient timestamp data"
            
        timestamps.sort()
        time_diffs = [(timestamps[i+1] - timestamps[i]).total_seconds() / 3600 / 24  # Convert to days
                      for i in range(len(timestamps)-1)]
        avg_days_between_posts = sum(time_diffs) / len(time_diffs)
        
        if avg_days_between_posts < 1:
            return f"{avg_days_between_posts * 24:.1f} hours between posts"
        else:
            return f"{avg_days_between_posts:.1f} days between posts"

def test_recommendation_generation():
    """Comprehensive test for RecommendationGenerator."""
    try:
        generator = RecommendationGenerator()
        sample_posts = [
            {'id': '1', 'caption': 'Bold summer looks! #SummerMakeup', 'hashtags': ['#SummerMakeup'], 'engagement': 150, 'likes': 120, 'comments': 30, 'timestamp': '2025-04-01T10:00:00Z', 'username': 'maccosmetics', 'media_type': 'photo'},
            {'id': '2', 'caption': 'New palette drop! #GlowUp', 'hashtags': ['#GlowUp'], 'engagement': 200, 'likes': 170, 'comments': 30, 'timestamp': '2025-04-02T12:00:00Z', 'username': 'maccosmetics', 'media_type': 'video'},
            {'id': '3', 'caption': 'Brow perfection! #BrowGame', 'hashtags': ['#BrowGame'], 'engagement': 180, 'likes': 150, 'comments': 30, 'timestamp': '2025-04-03T14:00:00Z', 'username': 'anastasiabeverlyhills', 'media_type': 'carousel'},
            {'id': '4', 'caption': 'Glowy skin secrets! #Skincare', 'hashtags': ['#Skincare'], 'engagement': 220, 'likes': 190, 'comments': 30, 'timestamp': '2025-04-04T15:00:00Z', 'username': 'fentybeauty', 'media_type': 'photo'}
        ]
        
        # Test utilities
        text = "Summer vibes! #Summer #Vibes"
        assert len(generator.extract_hashtags(text)) == 2, "Hashtag extraction failed"
        assert generator.format_caption(text)["caption"] == "Summer vibes!", "Caption formatting failed"
        assert "New look!" in generator.apply_template({"caption": "New look!", "hashtags": ["#Style"]}), "Template failed"
        assert generator.analyze_sentiment("Great day!")["sentiment"] == "positive", "Sentiment analysis failed"
        
        # Test core functionality
        primary_username = "maccosmetics"
        secondary_usernames = ["anastasiabeverlyhills", "fentybeauty"]
        query = "summer makeup trends"
        
        content_plan = generator.generate_content_plan(primary_username, secondary_usernames, query, sample_posts)
        assert content_plan, "Content plan generation failed"
        
        required_blocks = ["primary_analysis", "competitor_analysis", "recommendations", "next_post_prediction"]
        missing_blocks = [b for b in required_blocks if b not in content_plan]
        assert not missing_blocks, f"Missing blocks: {missing_blocks}"
        
        next_post_fields = ["caption", "hashtags", "call_to_action", "visual_prompt"]
        missing_fields = [f for f in next_post_fields if f not in content_plan["next_post_prediction"]]
        assert not missing_fields, f"Missing next_post fields: {missing_fields}"
        
        assert all(u in content_plan["competitor_analysis"] for u in secondary_usernames), "Competitor analysis incomplete"
        
        primary_components = ["account_type", "engagement", "posting_trends", "hashtag_effectiveness", "rag_analysis"]
        missing_components = [c for c in primary_components if c not in content_plan["primary_analysis"]]
        assert not missing_components, f"Missing primary components: {missing_components}"
        
        # Test additional features
        batch_recs = generator.generate_batch_recommendations(["summer trends", "fall looks"])
        if len(batch_recs) != 2:
            logger.error(f"Batch recommendations failed: Expected 2 topics, got {len(batch_recs)}. Response: {batch_recs}")
            return False
        
        assert len(generator.identify_competitors(sample_posts)) == 10, "Competitor identification failed"
        assert len(generator.generate_improvement_recommendations(content_plan["primary_analysis"])) == 5, "Improvement recommendations failed"
        
        logger.info("Recommendation generation test successful.")
        logger.debug(f"Content plan: {json.dumps(content_plan, indent=2)}")
        return True
    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_recommendation_generation()
    print(f"Recommendation generation test {'successful' if success else 'failed'}")