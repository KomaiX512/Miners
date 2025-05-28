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
        self.embedding_dimension = 384  # Fixed embedding dimension for consistency
        self.collection = self._get_or_create_collection()
        self.vectorizer = TfidfVectorizer(max_features=self.embedding_dimension)
        self.fitted = False
        
    def _get_or_create_collection(self):
        """Get or create a collection in the vector database."""
        try:
            collection = self.client.get_or_create_collection(
                name=self.config['collection_name']
            )
            logger.info(f"Initialized collection: {self.config['collection_name']} with embedding dimension: {self.embedding_dimension}")
            return collection
        except Exception as e:
            logger.error(f"Error initializing collection: {str(e)}")
            raise
    
    def _get_embeddings(self, texts):
        """Generate embeddings for the given texts using TF-IDF with fixed dimensionality."""
        try:
            if not texts or all(not text.strip() for text in texts):
                logger.warning("No valid text provided for embeddings")
                # Return zero vector of correct dimension instead of empty list
                return np.zeros((1, self.embedding_dimension)).tolist()
            
            # Get raw embeddings with max_features limiting dimension
            if not self.fitted:
                # Make sure the vectorizer is initialized with correct dimensions
                self.vectorizer = TfidfVectorizer(max_features=self.embedding_dimension)
                embeddings = self.vectorizer.fit_transform(texts).toarray()
                self.fitted = True
            else:
                embeddings = self.vectorizer.transform(texts).toarray()
            
            # Ensure consistent dimension (handle case where actual dimension is less than target)
            current_dim = embeddings.shape[1]
            if current_dim < self.embedding_dimension:
                logger.info(f"Padding embeddings from {current_dim} to {self.embedding_dimension} dimensions")
                padding = np.zeros((embeddings.shape[0], self.embedding_dimension - current_dim))
                embeddings = np.hstack((embeddings, padding))
            elif current_dim > self.embedding_dimension:
                logger.info(f"Truncating embeddings from {current_dim} to {self.embedding_dimension} dimensions")
                embeddings = embeddings[:, :self.embedding_dimension]
            
            # Normalize embeddings
            norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
            norms[norms == 0] = 1  # Avoid division by zero
            normalized_embeddings = embeddings / norms
            
            logger.info(f"Generated embeddings with shape: {normalized_embeddings.shape} for {len(texts)} texts")
            return normalized_embeddings.tolist()
        except Exception as e:
            logger.error(f"Error generating embeddings: {str(e)}")
            # Return zero vectors of correct dimension as fallback
            return np.zeros((len(texts), self.embedding_dimension)).tolist()
    
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
        """Query for similar documents with enhanced context retrieval and optional username filter."""
        try:
            if not query_text.strip():
                logger.warning("Empty query text provided")
                return {'documents': [[]], 'metadatas': [[]], 'distances': [[]]}
            
            # Generate embedding for query
            query_embedding = self._get_embeddings([query_text])
            if not query_embedding or len(query_embedding) == 0:
                logger.error("Failed to generate embedding for query")
                return {'documents': [[]], 'metadatas': [[]], 'distances': [[]]}
                
            # Make sure we're using the first (and only) embedding
            query_vector = query_embedding[0]
            
            # Check embedding dimensions
            if len(query_vector) != self.embedding_dimension:
                logger.warning(f"Query embedding dimension {len(query_vector)} doesn't match expected {self.embedding_dimension}")
                # Fix dimension issue by padding or truncating
                if len(query_vector) < self.embedding_dimension:
                    query_vector = query_vector + [0] * (self.embedding_dimension - len(query_vector))
                else:
                    query_vector = query_vector[:self.embedding_dimension]
            
            # Increase n_results for better context if no filter is applied
            if not filter_username:
                # For general queries, get more results for richer context
                enhanced_n_results = min(n_results * 2, 20)
            else:
                # For username-specific queries, get more results for that user's context
                enhanced_n_results = min(n_results * 3, 25)
            
            # Set up query parameters
            query_params = {
                'query_embeddings': [query_vector],
                'n_results': enhanced_n_results
            }
            
            # Add username filter if provided
            if filter_username:
                query_params['where'] = {'username': filter_username}
                logger.info(f"Querying for {enhanced_n_results} results filtered by username: {filter_username}")
            else:
                logger.info(f"Querying for {enhanced_n_results} results across all users")
            
            # Execute query
            results = self.collection.query(**query_params)
            
            # Handle empty results
            if not results['documents'] or not results['documents'][0]:
                logger.info(f"No similar documents found for query: {query_text[:50]}...")
                return {'documents': [[]], 'metadatas': [[]], 'distances': [[]]}
            
            # Enhanced result processing for better theme alignment
            documents = results['documents'][0]
            metadatas = results['metadatas'][0]
            distances = results.get('distances', [[]])[0] if results.get('distances') else [0] * len(documents)
            
            # Sort by relevance (lower distance = more similar) and engagement
            doc_metadata_distance = list(zip(documents, metadatas, distances))
            
            # Apply intelligent ranking: combine similarity and engagement for better results
            def intelligent_ranking(item):
                doc, meta, distance = item
                engagement = meta.get('engagement', 0)
                
                # Normalize engagement (0-1 scale) - higher is better
                max_engagement = max(m.get('engagement', 0) for _, m, _ in doc_metadata_distance) or 1
                normalized_engagement = engagement / max_engagement
                
                # Normalize distance (0-1 scale) - lower is better
                max_distance = max(distances) if distances else 1
                if max_distance > 0:
                    normalized_distance = 1 - (distance / max_distance)
                else:
                    normalized_distance = 1
                
                # Combine similarity (40%) and engagement (60%) for theme-aligned results
                combined_score = (0.4 * normalized_distance) + (0.6 * normalized_engagement)
                return combined_score
            
            # Sort by intelligent ranking (highest score first)
            ranked_results = sorted(doc_metadata_distance, key=intelligent_ranking, reverse=True)
            
            # Take the top n_results after intelligent ranking
            final_results = ranked_results[:n_results]
            
            # Separate back into documents, metadatas, and distances
            final_documents = [item[0] for item in final_results]
            final_metadatas = [item[1] for item in final_results]
            final_distances = [item[2] for item in final_results]
            
            # Add ranking score to metadata for transparency
            for i, meta in enumerate(final_metadatas):
                if isinstance(meta, dict):
                    doc, meta_orig, distance = final_results[i]
                    ranking_score = intelligent_ranking((doc, meta_orig, distance))
                    meta['ranking_score'] = round(ranking_score, 3)
                    meta['similarity_distance'] = round(distance, 3)
            
            enhanced_results = {
                'documents': [final_documents],
                'metadatas': [final_metadatas],
                'distances': [final_distances]
            }
            
            logger.info(f"Enhanced query returned {len(final_documents)} intelligently ranked results for better theme alignment")
            return enhanced_results
            
        except Exception as e:
            logger.error(f"Error in enhanced query for similar documents: {str(e)}")
            # Return empty result structure instead of raising
            return {'documents': [[]], 'metadatas': [[]], 'distances': [[]]}
    
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
                # Handle different field names between Instagram and Twitter
                if 'caption' in post:
                    text = post.get('caption', '').strip()  # Instagram format
                elif 'text' in post:
                    text = post.get('text', '').strip()     # Twitter format
                else:
                    text = ''  # No text content found
                
                # Skip empty posts
                if not text:
                    continue
                
                # Get engagement metrics with fallbacks for different formats
                engagement = post.get('engagement', 0)
                if engagement == 0:
                    # Fallback: calculate from individual metrics
                    likes = post.get('likes', 0)
                    comments = post.get('comments', 0)
                    shares = post.get('shares', 0)
                    retweets = post.get('retweets', 0)
                    replies = post.get('replies', 0)
                    quotes = post.get('quotes', 0)
                    
                    # Sum available metrics based on platform type
                    engagement = likes + comments + shares + retweets + replies + quotes
                
                # Get timestamp with fallback
                timestamp = post.get('timestamp', '')
                if not timestamp and 'created_at' in post:
                    timestamp = post.get('created_at', '')  # Twitter format
                
                # Get username with fallback to primary_username
                username = post.get('username', primary_username)
                # Remove @ symbol if present (for Twitter)
                if username and username.startswith('@'):
                    username = username[1:]
                
                # Create document and metadata
                documents.append(text)
                
                # Use stable ID generation for consistency
                if 'id' in post:
                    post_id = f"{username}_{post['id']}"
                else:
                    # Create a deterministic ID from content
                    post_id = f"{username}_{abs(hash(text + timestamp))}"
                
                ids.append(post_id)
                
                metadata = {
                    "username": username,
                    "primary_username": primary_username,
                    "engagement": engagement,
                    "timestamp": timestamp,
                    "platform": post.get('platform', 'instagram')  # Default to Instagram if not specified
                }
                
                # Add platform-specific metadata
                if 'retweets' in post or 'replies' in post:
                    metadata['platform'] = 'twitter'
                    metadata['retweets'] = post.get('retweets', 0)
                    metadata['replies'] = post.get('replies', 0)
                    metadata['quotes'] = post.get('quotes', 0)
                
                metadatas.append(metadata)
                post_count += 1
            
            if post_count > 0:
                # Generate embeddings and add to collection
                embeddings = self._get_embeddings(documents)
                
                self.collection.add(
                    documents=documents,
                    embeddings=embeddings,
                    ids=ids,
                    metadatas=metadatas
                )
                logger.info(f"Indexed {post_count} posts with usernames for {primary_username}")
            else:
                logger.warning(f"No valid posts found to index for {primary_username}")
                
            return post_count
        except Exception as e:
            logger.error(f"Error adding posts to vector DB: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return 0
    
    def clear_collection(self):
        """Clear all documents from the collection."""
        try:
            count_before = self.get_count()
            self.client.delete_collection(self.config['collection_name'])
            self.collection = self._get_or_create_collection()
            self.vectorizer = TfidfVectorizer(max_features=self.embedding_dimension)
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
        query = "What's trending in makeup?"
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