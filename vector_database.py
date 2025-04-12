"""Module for vector database operations using a simpler embedding approach."""

import logging
import chromadb
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from config import VECTOR_DB_CONFIG, LOGGING_CONFIG

# Set up logging
logging.basicConfig(
    level=LOGGING_CONFIG['level'],
    format=LOGGING_CONFIG['format']
)
logger = logging.getLogger(__name__)

class VectorDatabaseManager:
    """Class to handle vector database operations with username metadata."""
    
    def __init__(self, config=VECTOR_DB_CONFIG):
        """Initialize with vector database configuration."""
        self.config = config
        self.client = chromadb.Client()
        self.collection = self._get_or_create_collection()
        self.vectorizer = TfidfVectorizer()
        self.fitted = False
        
    def _get_or_create_collection(self):
        """Get or create a collection in the vector database."""
        try:
            collection = self.client.get_or_create_collection(
                name=self.config['collection_name']
            )
            logger.info(f"Initialized collection: {self.config['collection_name']}")
            return collection
        except Exception as e:
            logger.error(f"Error initializing collection: {str(e)}")
            raise
    
    def _get_embeddings(self, texts):
        """Generate embeddings for the given texts using TF-IDF."""
        try:
            if not texts or all(not text.strip() for text in texts):
                logger.warning("No valid text provided for embeddings")
                return []
            
            if not self.fitted:
                embeddings = self.vectorizer.fit_transform(texts).toarray()
                self.fitted = True
            else:
                embeddings = self.vectorizer.transform(texts).toarray()
            
            # Normalize embeddings
            norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
            norms[norms == 0] = 1  # Avoid division by zero
            normalized_embeddings = embeddings / norms
            
            logger.info(f"Generated embeddings for {len(texts)} texts")
            return normalized_embeddings.tolist()
        except Exception as e:
            logger.error(f"Error generating embeddings: {str(e)}")
            raise
    
    def add_documents(self, documents, ids=None, metadatas=None):
        """Add documents to the vector database."""
        try:
            if not documents:
                logger.warning("No documents provided to add")
                return
            
            if ids is None:
                ids = [f"doc_{i}" for i in range(len(documents))]
            
            if len(documents) != len(ids) or (metadatas and len(documents) != len(metadatas)):
                logger.error("Mismatch in lengths of documents, ids, and metadatas")
                raise ValueError("Length mismatch in inputs")
            
            embeddings = self._get_embeddings(documents)
            if not embeddings:
                logger.warning("No embeddings generated; skipping add")
                return
            
            self.collection.add(
                documents=documents,
                embeddings=embeddings,
                ids=ids,
                metadatas=metadatas
            )
            logger.info(f"Added {len(documents)} documents to the collection")
        except Exception as e:
            logger.error(f"Error adding documents: {str(e)}")
            raise
    
    def query_similar(self, query_text, n_results=5, filter_username=None):
        """Query for similar documents with optional username filter."""
        try:
            if not query_text.strip():
                logger.warning("Empty query text provided")
                return {'documents': [[]], 'metadatas': [[]], 'distances': [[]]}
            
            query_embedding = self._get_embeddings([query_text])[0]
            query_params = {
                'query_embeddings': [query_embedding],
                'n_results': n_results
            }
            
            if filter_username:
                query_params['where'] = {'username': filter_username}
            
            results = self.collection.query(**query_params)
            logger.info(f"Found {len(results['documents'][0])} similar documents for query")
            return results
        except Exception as e:
            logger.error(f"Error querying similar documents: {str(e)}")
            raise
    
    def get_count(self):
        """Get the number of documents in the collection."""
        try:
            count = self.collection.count()
            logger.info(f"Collection contains {count} documents")
            return count
        except Exception as e:
            logger.error(f"Error getting collection count: {str(e)}")
            return 0
    
    def add_posts(self, posts, primary_username):
        """
        Add social media posts to the vector database with username metadata.
        
        Args:
            posts: List of post dictionaries
            primary_username: Primary username to differentiate posts
            
        Returns:
            int: Number of posts added
        """
        try:
            if not posts:
                logger.warning("No posts provided to add")
                return 0
            
            documents = []
            ids = []
            metadatas = []
            post_count = 0
            
            for post in posts:
                text = post.get('caption', '').strip()
                if not text:
                    logger.debug(f"Skipping post with empty caption: {post.get('id', 'unknown')}")
                    continue
                
                post_id = post.get('id', f"post_{post_count}")
                username = post.get('username', primary_username if 'maccosmetics' in str(post_id) else 'unknown')
                
                documents.append(text)
                ids.append(f"post_{post_id}_{username}")  # Unique ID with username
                
                metadata = {
                    'username': username,
                    'engagement': int(post.get('engagement', 0)),
                    'likes': int(post.get('likes', 0)),
                    'comments': int(post.get('comments', 0)),
                    'timestamp': str(post.get('timestamp', '')),
                }
                
                if 'hashtags' in post:
                    metadata['hashtags'] = ' '.join(post['hashtags']) if isinstance(post['hashtags'], list) else str(post['hashtags'])
                
                metadatas.append(metadata)
                post_count += 1
            
            if documents:
                self.add_documents(documents, ids, metadatas)
                logger.info(f"Indexed {post_count} posts with usernames for {primary_username}")
                return post_count
            else:
                logger.warning("No valid posts to add after filtering")
                return 0
                
        except Exception as e:
            logger.error(f"Error adding posts: {str(e)}")
            return 0
    
    def clear_collection(self):
        """Clear all documents from the collection."""
        try:
            count_before = self.get_count()
            self.client.delete_collection(self.config['collection_name'])
            self.collection = self._get_or_create_collection()
            self.vectorizer = TfidfVectorizer()
            self.fitted = False
            logger.info(f"Cleared collection with {count_before} documents")
            return True
        except Exception as e:
            logger.error(f"Error clearing collection: {str(e)}")
            return False


def test_vector_db_multi_user():
    """Test vector database operations with primary and secondary usernames."""
    try:
        manager = VectorDatabaseManager()
        manager.clear_collection()  # Start fresh
        
        # Simulate posts from provided files
        primary_username = "maccosmetics"
        secondary_usernames = [
            "anastasiabeverlyhills", "fentybeauty", "narsissist", "toofaced",
            "competitor1", "competitor2", "competitor3", "competitor4", "competitor5"
        ]
        
        sample_posts = [
            # Primary posts
            {"id": "1", "caption": "New lipstick launch!", "engagement": 1200, "likes": 1000, "comments": 200, 
             "timestamp": "2025-04-01T10:00:00Z", "username": primary_username},
            {"id": "2", "caption": "Spring collection reveal", "engagement": 1500, "likes": 1300, "comments": 200, 
             "timestamp": "2025-04-02T12:00:00Z", "username": primary_username},
            # Secondary posts
            {"id": "3", "caption": "Bold brows tutorial", "engagement": 800, "likes": 700, "comments": 100, 
             "timestamp": "2025-04-01T14:00:00Z", "username": "anastasiabeverlyhills"},
            {"id": "4", "caption": "Glowy skin promo", "engagement": 900, "likes": 800, "comments": 100, 
             "timestamp": "2025-04-02T15:00:00Z", "username": "fentybeauty"},
            {"id": "5", "caption": "Matte lip trend", "engagement": 700, "likes": 600, "comments": 100, 
             "timestamp": "2025-04-03T09:00:00Z", "username": "narsissist"}
        ]
        
        # Add posts
        added_count = manager.add_posts(sample_posts, primary_username)
        if added_count != len(sample_posts):
            logger.error(f"Expected {len(sample_posts)} posts, added {added_count}")
            return False
        
        # Test querying
        query = "What’s trending in makeup?"
        results_all = manager.query_similar(query, n_results=3)
        results_primary = manager.query_similar(query, n_results=2, filter_username=primary_username)
        results_secondary = manager.query_similar(query, n_results=2, filter_username="fentybeauty")
        
        # Validate results
        if not results_all['documents'][0] or not results_primary['documents'][0] or not results_secondary['documents'][0]:
            logger.error("Query returned empty results")
            return False
        
        logger.info("\nQuery: " + query)
        logger.info("All results:")
        for doc, meta in zip(results_all['documents'][0], results_all['metadatas'][0]):
            logger.info(f"- {doc} (Username: {meta['username']}, Engagement: {meta['engagement']})")
        
        logger.info(f"Primary ({primary_username}) results:")
        for doc, meta in zip(results_primary['documents'][0], results_primary['metadatas'][0]):
            logger.info(f"- {doc} (Engagement: {meta['engagement']})")
        
        logger.info("Secondary (fentybeauty) results:")
        for doc, meta in zip(results_secondary['documents'][0], results_secondary['metadatas'][0]):
            logger.info(f"- {doc} (Engagement: {meta['engagement']})")
        
        if manager.get_count() != added_count:
            logger.error("Collection count mismatch")
            return False
        
        logger.info("Multi-user vector database test successful")
        return True
    except Exception as e:
        logger.error(f"Multi-user test failed: {str(e)}")
        return False


if __name__ == "__main__":
    success = test_vector_db_multi_user()
    print(f"Multi-user vector database test {'successful' if success else 'failed'}")