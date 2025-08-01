"""Module for fetching and processing news data from newsdata.io."""

import logging
import requests
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from config import LOGGING_CONFIG, R2_CONFIG

# Set up logging
logging.basicConfig(
    level=LOGGING_CONFIG['level'],
    format=LOGGING_CONFIG['format']
)
logger = logging.getLogger(__name__)

class NewsAPIClient:
    """Client for interacting with newsdata.io API."""
    
    def __init__(self, api_key: str = None):
        """Initialize with API key."""
        self.api_key = api_key or R2_CONFIG.get('NEWSDATA_API_KEY')
        self.base_url = "https://newsdata.io/api/1/news"
        
        if not self.api_key:
            logger.error("NewsData API key not provided")
            raise ValueError("NewsData API key is required")
            
        logger.info("NewsData API client initialized")
    
    def build_query_for_account_type(self, account_type: str, posting_style: str) -> str:
        """
        Build a search query based on account type and posting style.
        
        Args:
            account_type: Type of account (e.g., 'science_events', 'lifestyle')
            posting_style: Style of posting (e.g., 'Educational', 'Storytelling')
            
        Returns:
            str: Search query
        """
        account_type = account_type.lower() if account_type else ""
        posting_style = posting_style.lower() if posting_style else ""
        
        # Dictionary mapping account types to query parameters
        account_type_queries = {
            "science_events": "science conference OR research breakthrough OR scientific discovery",
            "tech": "technology innovation OR tech startup OR digital transformation",
            "education": "education reform OR learning innovations OR teaching methods",
            "lifestyle": "lifestyle trends OR wellness tips OR home decor",
            "health": "health research OR medical breakthrough OR wellness trend",
            "travel": "travel destination OR adventure tourism OR cultural experience",
            "food": "food trend OR culinary innovation OR restaurant opening",
            "photography": "photography technique OR camera innovation OR visual arts",
            "art": "art exhibition OR artist spotlight OR creative innovation",
            "music": "music release OR concert announcement OR artist feature",
            "sports": "sports event OR athlete achievement OR team news",
            "finance": "financial markets OR investment trends OR economic forecast",
            "politics": "political development OR policy change OR government decision",
            "environment": "environmental initiative OR climate action OR sustainability",
            "fashion": "fashion trend OR designer collection OR style innovation",
            "beauty": "beauty product OR skincare innovation OR makeup trend",
            "fitness": "fitness routine OR workout trend OR health improvement",
            "parenting": "parenting advice OR child development OR family activities",
            "pet": "pet care OR animal welfare OR veterinary advance",
            "gaming": "game release OR gaming industry OR esports event",
            "book": "book release OR author interview OR literary award"
        }
        
        # Dictionary mapping posting styles to query modifiers
        posting_style_modifiers = {
            "educational": "guide OR tutorial OR explanation OR how-to",
            "informative": "report OR analysis OR insights OR statistics",
            "storytelling": "story OR experience OR journey OR narrative",
            "promotional": "launch OR release OR announcement OR new",
            "inspirational": "inspiring OR motivation OR achievement OR success story",
            "humorous": "funny OR entertaining OR amusing OR comedy",
            "controversial": "debate OR controversy OR discussion OR opinion",
            "personal": "personal experience OR testimonial OR reflection",
            "visual": "visual OR photography OR image OR design",
            "interactive": "poll OR question OR challenge OR participation"
        }
        
        # Get base query from account type or use default
        base_query = ""
        
        # Try exact match first
        if account_type in account_type_queries:
            base_query = account_type_queries[account_type]
        else:
            # Try partial match
            for key, query in account_type_queries.items():
                if key in account_type:
                    base_query = query
                    break
        
        # If no match found, use generic query
        if not base_query:
            base_query = "trending news OR current events OR latest developments"
        
        # Add posting style modifier if available
        style_modifier = ""
        
        # Try exact match first
        if posting_style in posting_style_modifiers:
            style_modifier = posting_style_modifiers[posting_style]
        else:
            # Try partial match
            for key, modifier in posting_style_modifiers.items():
                if key in posting_style:
                    style_modifier = modifier
                    break
        
        # Combine base query and modifier
        final_query = base_query
        if style_modifier:
            final_query = f"{base_query} ({style_modifier})"
        
        logger.info(f"Generated query: {final_query}")
        return final_query
    
    def fetch_news(self, query: str, language: str = 'en', country: Optional[str] = None, 
                  category: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Fetch news articles from newsdata.io API.
        
        Args:
            query: Search query
            language: Language code (default: 'en')
            country: Country code (optional)
            category: News category (optional)
            limit: Maximum number of results to return (default: 10)
            
        Returns:
            List of news articles
        """
        params = {
            'apikey': self.api_key,
            'q': query,
            'language': language
        }
        
        if country:
            params['country'] = country
            
        if category:
            params['category'] = category
            
        try:
            logger.info(f"Fetching news with query: {query}")
            response = requests.get(self.base_url, params=params)
            
            if response.status_code != 200:
                logger.error(f"API request failed with status code {response.status_code}: {response.text}")
                return []
                
            data = response.json()
            
            if 'results' not in data or not data['results']:
                logger.warning(f"No results found for query: {query}")
                return []
                
            # Limit results
            articles = data['results'][:limit]
            logger.info(f"Retrieved {len(articles)} news articles")
            
            return articles
            
        except Exception as e:
            logger.error(f"Error fetching news: {str(e)}")
            return []
    
    def format_article_for_social(self, article: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format a news article for social media consumption.
        
        Args:
            article: Raw news article from API
            
        Returns:
            Formatted article
        """
        try:
            # Extract relevant fields
            title = article.get('title', '')
            description = article.get('description', '')
            content = article.get('content', '')
            source_id = article.get('source_id', '')
            link = article.get('link', '')
            pubDate = article.get('pubDate', '')
            
            # Use content if available, otherwise use description
            text = content if content else description
            
            # Format as social media post
            paragraph = f"{title}. {text}"
            
            # Add source and link
            if source_id:
                paragraph += f" Published by {source_id} on {pubDate}."
                
            if link:
                paragraph += f" Read more: {link}"
                
            return {
                "paragraph": paragraph,
                "title": title,
                "source_id": source_id,
                "pubDate": pubDate,
                "link": link
            }
            
        except Exception as e:
            logger.error(f"Error formatting article: {str(e)}")
            return {"paragraph": "Error retrieving news article", "title": "Error", "link": ""}
    
    def get_news_for_account(self, account_type: str, posting_style: str, 
                           limit: int = 5) -> List[Dict[str, Any]]:
        """
        Get news articles relevant to a specific account type and posting style.
        
        Args:
            account_type: Type of account
            posting_style: Style of posting
            limit: Maximum number of results (default: 5)
            
        Returns:
            List of formatted news articles
        """
        try:
            query = self.build_query_for_account_type(account_type, posting_style)
            articles = self.fetch_news(query, limit=limit)
            
            if not articles:
                logger.warning(f"No articles found for {account_type} with {posting_style} style")
                return []
                
            formatted_articles = [self.format_article_for_social(article) for article in articles]
            logger.info(f"Formatted {len(formatted_articles)} articles for {account_type}")
            
            return formatted_articles
            
        except Exception as e:
            logger.error(f"Error getting news for account: {str(e)}")
            return []


# Test function
def test_news_api():
    """Test the NewsData API implementation."""
    try:
        client = NewsAPIClient()
        
        # Test query building
        query = client.build_query_for_account_type("science_events", "educational")
        if not query:
            logger.error("Failed to build query")
            return False
            
        # Test news fetching
        articles = client.fetch_news(query, limit=2)
        if not articles:
            logger.warning("No articles retrieved (might be API limit)")
            
        # Test article formatting
        if articles:
            formatted = client.format_article_for_social(articles[0])
            if not formatted or 'paragraph' not in formatted:
                logger.error("Failed to format article")
                return False
                
            logger.info(f"Successfully formatted article: {formatted['title']}")
            
        # Test end-to-end function
        news = client.get_news_for_account("tech", "informative", limit=3)
        if news:
            logger.info(f"Retrieved {len(news)} news items for tech account")
            
        return True
        
    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
        return False


if __name__ == "__main__":
    success = test_news_api()
    print(f"NewsData API test {'successful' if success else 'failed'}") 