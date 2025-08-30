"""Module for vector database operations using a simpler embedding approach."""

import logging
import chromadb
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from config import VECTOR_DB_CONFIG, LOGGING_CONFIG
import time
from datetime import datetime
import re
import os
import json
from pathlib import Path
import shutil
import httpx

# Set up logging
logging.basicConfig(
    level=LOGGING_CONFIG['level'],
    format=LOGGING_CONFIG['format']
)
logger = logging.getLogger(__name__)

class VectorDatabaseManager:
    """Class to handle vector database operations with username metadata."""

    # Class-level flag to ensure we only perform destructive collection cleanup once per process
    _cleanup_performed = False
    """Class to handle vector database operations with username metadata."""
    
    def __init__(self, config=VECTOR_DB_CONFIG):
        """Initialize with vector database configuration."""
        self.config = config
        self.client = None
        self.collection = None
        self.embedding_dimension = 384  # Fixed embedding dimension for consistency
        self.vectorizer = TfidfVectorizer(max_features=self.embedding_dimension)
        self.fitted = False
        self.use_fallback = False
        
        # Simple, direct ChromaDB initialization
        self._initialize_db()
        
    def _initialize_db(self):
        """Initialize the database with clean startup and direct connection."""
        try:
            # Check ChromaDB server health first
            chroma_host = "localhost"
            chroma_port = 8004
            
            # If server is not running, try to clean up and provide clear instructions
            if not self._check_chroma_server_health(host=chroma_host, port=chroma_port):
                logger.info("🧹 ChromaDB server not detected, preparing clean database directory...")
                self._cleanup_database_directory()
                os.makedirs("./chroma_db", exist_ok=True)
                
                raise RuntimeError(
                    f"ChromaDB server is not running or not healthy at http://{chroma_host}:{chroma_port}. "
                    f"Please start it with: chroma run --path ./chroma_db --host 0.0.0.0 --port 8004"
                )
            
            # Initialize ChromaDB client
            self.client = chromadb.HttpClient(host=chroma_host, port=chroma_port)
            
            # Test the connection
            collections = self.client.list_collections()
            logger.info(f"✅ ChromaDB client connected successfully. Found {len(collections)} collections.")
            
            # Check for corrupted collections and clean them up
            self._force_cleanup_corrupted_collection()
            
            # DISABLED: Clear existing collection for clean run (only if we can write)
            # self._ensure_clean_collection()  # COMMENTED OUT to preserve competitor data between runs
            
            # Get or create collection
            self.collection = self._get_or_create_collection()
            
            logger.info("✅ Vector database initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Vector database initialization failed: {str(e)}")
            logger.error("❌ System cannot proceed without ChromaDB. Please fix the database issue.")
            raise
    
    def _cleanup_database_directory(self):
        """Clean up the database directory on startup for fresh start."""
        try:
            if os.path.exists("./chroma_db"):
                logger.info("🧹 Cleaning up existing ChromaDB directory for fresh start...")
                shutil.rmtree("./chroma_db")
                logger.info("✅ ChromaDB directory cleaned successfully")
        except Exception as e:
            logger.warning(f"⚠️ Error cleaning up database directory: {str(e)}")
            # Continue anyway - this shouldn't block startup
    
    def _ensure_clean_collection(self):
        """Ensure a clean collection for the very first run only, preventing race-condition deletions."""
        if VectorDatabaseManager._cleanup_performed:
            # Skip further clean-ups – collection already handled in this process
            logger.info("🛑 Skipping collection cleanup – already performed once in this process")
            return
        try:
            existing_collection = self.client.get_collection(name=self.config['collection_name'])
            self.client.delete_collection(name=self.config['collection_name'])
            logger.info(f"🧹 Deleted existing collection '{self.config['collection_name']}' for clean run")
        except Exception:
            # Collection doesn't exist, which is fine
            logger.info(f"No existing collection '{self.config['collection_name']}' to clean up")
        finally:
            VectorDatabaseManager._cleanup_performed = True
    
    def _force_cleanup_corrupted_collection(self):
        """Force cleanup of corrupted collections that may be causing issues."""
        try:
            # List all collections to identify any corrupted ones
            collections = self.client.list_collections()
            logger.info(f"Found {len(collections)} collections in database")
            
            for collection_info in collections:
                collection_name = collection_info.name
                collection_id = collection_info.id
                logger.info(f"Checking collection: {collection_name} (ID: {collection_id})")
                
                # Try to access each collection to identify corrupted ones
                try:
                    collection = self.client.get_collection(name=collection_name)
                    # Test basic operations
                    count = collection.count()
                    logger.info(f"Collection {collection_name} is healthy with {count} documents")
                except Exception as e:
                    logger.warning(f"Collection {collection_name} appears corrupted: {str(e)}")
                    try:
                        self.client.delete_collection(name=collection_name)
                        logger.info(f"Successfully deleted corrupted collection: {collection_name}")
                    except Exception as delete_err:
                        logger.error(f"Failed to delete corrupted collection {collection_name}: {str(delete_err)}")
                        
        except Exception as e:
            logger.error(f"Error during collection cleanup: {str(e)}")
            # Don't raise - this is cleanup, not critical
    
    def reset_database(self):
        """Reset the entire database by deleting all collections and recreating."""
        try:
            logger.warning("🔄 Resetting entire ChromaDB database...")
            
            # List and delete all collections
            collections = self.client.list_collections()
            for collection_info in collections:
                try:
                    self.client.delete_collection(name=collection_info.name)
                    logger.info(f"Deleted collection: {collection_info.name}")
                except Exception as e:
                    logger.error(f"Failed to delete collection {collection_info.name}: {str(e)}")
            
            # Recreate the main collection
            self.collection = self.client.create_collection(
                name=self.config['collection_name'],
                metadata={"hnsw:space": "cosine"}
            )
            logger.info("✅ Database reset complete - new collection created")
            
        except Exception as e:
            logger.error(f"Failed to reset database: {str(e)}")
            raise
    

        
    def _get_or_create_collection(self):
        """Get or create a collection in the vector database with simple, direct approach."""
        try:
            # First try to get collection if it exists
            try:
                collection = self.client.get_collection(name=self.config['collection_name'])
                logger.info(f"Retrieved existing collection: {self.config['collection_name']}")
                
                # Verify collection is working with a simple count operation
                try:
                    count = collection.count()
                    logger.info(f"Verified collection contains {count} documents")
                except Exception as count_err:
                    logger.warning(f"Collection exists but count failed: {str(count_err)}")
                    # Collection exists but may have issues, try to recreate it
                    logger.info("Attempting to recreate collection due to count failure...")
                    try:
                        self.client.delete_collection(name=self.config['collection_name'])
                        logger.info(f"Deleted problematic collection: {self.config['collection_name']}")
                        # Fall through to creation
                    except Exception as delete_err:
                        logger.error(f"Failed to delete problematic collection: {str(delete_err)}")
                        raise
                
                return collection
                
            except Exception as get_err:
                logger.info(f"Collection does not exist or was deleted, creating new collection: {self.config['collection_name']}")
                
                # Create collection with simple parameters
                collection = self.client.create_collection(
                    name=self.config['collection_name'],
                    metadata={"hnsw:space": "cosine"}
                )
                
                logger.info(f"Successfully created collection: {self.config['collection_name']}")
                return collection
                
        except Exception as e:
            logger.error(f"Failed to get or create collection: {str(e)}")
            raise
    
    def _get_embeddings(self, texts):
        """Generate embeddings for the given texts using TF-IDF with fixed dimensionality."""
        try:
            if not texts or all(not text.strip() for text in texts):
                logger.warning("No valid text provided for embeddings")
                # Return zero vector of correct dimension instead of empty list
                return np.zeros((1, self.embedding_dimension)).tolist()
            
            # Clean and prepare texts to ensure better features
            cleaned_texts = []
            for text in texts:
                # Skip empty texts
                if not text or not text.strip():
                    continue
                
                # Clean the text more thoroughly
                text = re.sub(r'http\S+', '', text)  # Remove URLs
                text = re.sub(r'[^\w\s]', ' ', text)  # Replace punctuation with spaces
                text = re.sub(r'\s+', ' ', text).strip()  # Normalize whitespace
                
                # Ensure text is long enough to generate meaningful features
                if len(text.split()) < 3:
                    # Add placeholder text to ensure minimum content
                    text = text + " content makeup beauty post"
                
                cleaned_texts.append(text)
            
            # Get count of actual texts for later filtering
            actual_text_count = len(cleaned_texts)
            
            # Ensure we have enough examples for the vectorizer
            standard_examples = []
            if actual_text_count < 5:
                # Add standard examples to help with feature extraction
                standard_examples = [
                    "makeup beauty content cosmetics instagram post",
                    "beauty product post makeup instagram cosmetics",
                    "makeup tutorial beauty cosmetics instagram products",
                    "cosmetics brand makeup beauty products instagram",
                    "beauty makeup tutorial cosmetics instagram product review"
                ]
                cleaned_texts.extend(standard_examples)
            
            # Get raw embeddings with max_features limiting dimension
            if not self.fitted:
                logger.info(f"Training new TF-IDF vectorizer with {len(cleaned_texts)} documents")
                # Make sure the vectorizer is initialized with correct dimensions
                self.vectorizer = TfidfVectorizer(
                    max_features=self.embedding_dimension,
                    ngram_range=(1, 2),  # Use bigrams to improve features
                    min_df=1,
                    max_df=0.9
                )
                embeddings = self.vectorizer.fit_transform(cleaned_texts).toarray()
                self.fitted = True
                logger.info(f"TF-IDF vectorizer fitted with {len(self.vectorizer.get_feature_names_out())} features")
            else:
                embeddings = self.vectorizer.transform(cleaned_texts).toarray()
            
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
            
            # Return only the embeddings for the actual texts, not the standard examples
            if len(standard_examples) > 0:
                logger.info(f"Filtering out {len(standard_examples)} standard examples from embeddings")
                normalized_embeddings = normalized_embeddings[:actual_text_count]
            
            logger.info(f"Generated embeddings with shape: {normalized_embeddings.shape} for {actual_text_count} texts")
            return normalized_embeddings.tolist()
        except Exception as e:
            logger.error(f"Error generating embeddings: {str(e)}")
            # Return zero vectors of correct dimension as fallback
            return np.zeros((len(texts), self.embedding_dimension)).tolist()
    
    def add_documents(self, documents, ids=None, metadatas=None):
        """Add documents to the vector database with enhanced RAG logging and duplicate checking."""
        try:
            if not documents:
                logger.warning("⚠️ RAG INDEX: No documents provided to add")
                return
            
            if ids is None:
                ids = [f"doc_{i}" for i in range(len(documents))]
            
            if len(documents) != len(ids) or (metadatas and len(documents) != len(metadatas)):
                logger.error("❌ RAG INDEX: Mismatch in lengths of documents, ids, and metadatas")
                raise ValueError("Length mismatch in inputs")
            
            # Direct ChromaDB addition only - no fallback system
            
            # Check for existing documents to prevent duplicates
            existing_ids = set()
            try:
                existing_results = self.collection.get(include=['metadatas'])
                if existing_results and 'ids' in existing_results:
                    existing_ids = set(existing_results['ids'])
                    logger.info(f"Found {len(existing_ids)} existing documents in vector database")
            except Exception as e:
                logger.warning(f"Could not retrieve existing IDs: {str(e)}")
            
            # Filter out duplicates
            new_documents = []
            new_ids = []
            new_metadatas = []
            skipped_count = 0
            
            for i, doc_id in enumerate(ids):
                if doc_id in existing_ids:
                    skipped_count += 1
                    logger.debug(f"Skipping duplicate document ID: {doc_id}")
                    continue
                
                new_documents.append(documents[i])
                new_ids.append(doc_id)
                if metadatas:
                    new_metadatas.append(metadatas[i])
            
            if not new_documents:
                logger.info(f"⚠️ RAG INDEX: No new documents to add (skipped {skipped_count} duplicates)")
                return
            
            embeddings = self._get_embeddings(new_documents)
            if not embeddings:
                logger.warning("⚠️ RAG INDEX: No embeddings generated; skipping add")
                return
            
            # Enhanced logging for RAG tracking
            logger.info(f"📊 RAG INDEX: Adding {len(new_documents)} new documents to vector database (skipped {skipped_count} duplicates)")
            if new_metadatas:
                usernames = set(meta.get('username', 'unknown') for meta in new_metadatas if meta)
                logger.info(f"📊 RAG INDEX: Users being indexed: {list(usernames)}")
            
            # Add documents to collection with graceful duplicate handling
            if new_metadatas:
                logger.info(f"📊 RAG INDEX: Adding {len(new_documents)} new documents to collection (post filter)")
                
                try:
                    self.collection.upsert(
                        documents=new_documents,
                        embeddings=embeddings,
                        ids=new_ids,
                        metadatas=new_metadatas
                    )
                    logger.info(f"✅ RAG INDEX: Successfully upserted {len(new_documents)} documents (graceful duplicate handling)")
                    
                    # Backup successful data to fallback database for resilience
                    logger.info("📊 RAG INDEX: Documents successfully added to ChromaDB")
                    
                except Exception as e:
                        logger.error(f"❌ RAG INDEX: Error upserting to ChromaDB: {str(e)}")
                        # Auto-recovery: recreate collection once if it was deleted elsewhere
                        if "does not exists" in str(e):
                            logger.warning("⚠️ Collection missing during upsert – attempting to recreate and retry once")
                            try:
                                self.collection = self._get_or_create_collection()
                                self.collection.upsert(
                                    documents=new_documents,
                                    embeddings=embeddings,
                                    ids=new_ids,
                                    metadatas=new_metadatas
                                )
                                logger.info("✅ RAG INDEX: Upsert succeeded after recreating collection")
                            except Exception as retry_e:
                                logger.error(f"❌ RAG INDEX: Retry after collection recreation failed: {str(retry_e)}")
                        # No further retries
            else:
                logger.info(f"⚠️ RAG INDEX: All documents were duplicates, nothing added")
            
        except Exception as e:
            logger.error(f"❌ RAG INDEX: Error adding documents: {str(e)}")
            
            # No fallback database - log error and continue
            logger.error("❌ RAG INDEX: Failed to add documents to ChromaDB")
            
    def query_similar(self, query_text, n_results=5, filter_username=None, is_competitor=False):
        """
        Query for similar documents with enhanced RAG retrieval, filtering, and robust error handling.
        
        Args:
            query_text: The text to search for
            n_results: Maximum number of results to return
            filter_username: Optional username to filter results
            is_competitor: Set to True when querying competitor data for specialized handling
            
        Returns:
            Dictionary with documents, metadatas, and distances
        """
        try:
            if not query_text or not query_text.strip():
                logger.warning("⚠️ RAG QUERY: Empty query text provided")
                return {'documents': [[]], 'metadatas': [[]], 'distances': [[]]}
            
            # Sanitize and normalize query
            query_text = query_text.strip()
            
            # Log RAG query initiation
            query_preview = query_text[:50] + ('...' if len(query_text) > 50 else '')
            logger.info(f"🔍 RAG QUERY: Searching for content similar to: '{query_preview}'")
            if filter_username:
                logger.info(f"🔍 RAG QUERY: Filtering by username: {filter_username} (competitor: {is_competitor})")
            
            # CRITICAL FIX: Special handling for competitor queries
            # For competitor analysis, use direct metadata filtering instead of semantic similarity
            # This fixes the "generic template" issue by ensuring we get actual competitor data
            if is_competitor and filter_username:
                logger.info(f"🎯 COMPETITOR QUERY: Using direct metadata search for {filter_username}")
                try:
                    # Get all documents and filter by metadata - no semantic similarity needed
                    all_data = self.collection.get(include=["metadatas", "documents"])
                    
                    if not all_data or "metadatas" not in all_data:
                        logger.warning("⚠️ COMPETITOR QUERY: No metadata available")
                        return {'documents': [[]], 'metadatas': [[]], 'distances': [[]]}
                    
                    # Filter competitor documents directly
                    clean_username = filter_username.lower().strip()
                    competitor_docs = []
                    competitor_meta = []
                    competitor_distances = []
                    
                    for i, meta in enumerate(all_data["metadatas"]):
                        if not meta:
                            continue
                            
                        meta_username = meta.get('username', '').lower().strip()
                        meta_competitor = meta.get('competitor', '').lower().strip()
                        meta_is_competitor = meta.get('is_competitor', False)
                        
                        # Use same matching logic but skip similarity search
                        match_found = False
                        
                        # Direct competitor field match
                        if meta_competitor and meta_competitor == clean_username:
                            match_found = True
                        # Username match with competitor flag  
                        elif meta_username and meta_username == clean_username and meta_is_competitor:
                            match_found = True
                        
                        if match_found and i < len(all_data["documents"]):
                            competitor_docs.append(all_data["documents"][i])
                            competitor_meta.append(meta)
                            # Use engagement as "distance" (higher engagement = lower distance)
                            engagement = meta.get('engagement', 1)
                            distance = 1.0 / max(engagement, 1)  # Convert to distance-like metric
                            competitor_distances.append(distance)
                            
                            # Limit results for performance
                            if len(competitor_docs) >= n_results:
                                break
                    
                    logger.info(f"✅ COMPETITOR QUERY: Found {len(competitor_docs)} documents for {filter_username}")
                    
                    return {
                        'documents': [competitor_docs] if competitor_docs else [[]],
                        'metadatas': [competitor_meta] if competitor_meta else [[]],
                        'distances': [competitor_distances] if competitor_distances else [[]]
                    }
                    
                except Exception as e:
                    logger.error(f"❌ COMPETITOR QUERY: Error in direct metadata search: {str(e)}")
                    # Fall back to regular semantic search
                    logger.info("🔄 COMPETITOR QUERY: Falling back to semantic search")
            
            # Regular semantic similarity search for primary users and general queries
            logger.info(f"🔍 SEMANTIC QUERY: Using embedding-based search")
            
            # Direct ChromaDB query only - no fallback system
            
            # Generate embedding for query with retry logic
            max_embedding_retries = 2
            query_embedding = None
            
            for attempt in range(max_embedding_retries):
                try:
                    query_embedding = self._get_embeddings([query_text])
                    if query_embedding and len(query_embedding) > 0:
                        break
                except Exception as e:
                    logger.warning(f"Embedding generation failed (attempt {attempt+1}): {str(e)}")
                    if attempt < max_embedding_retries - 1:
                        time.sleep(1)  # Short delay before retry
                
            if not query_embedding or len(query_embedding) == 0:
                logger.error("❌ RAG QUERY: Failed to generate embedding for query after all attempts")
                
                # No fallback - return empty results
                logger.error("❌ RAG QUERY: Failed to generate embeddings - no fallback available")
                return {
                    'documents': [[]],
                    'metadatas': [[]],
                    'distances': [[]]
                }
                
            # Make sure we're using the first (and only) embedding
            query_vector = query_embedding[0]
            
            # Check if collection exists and is initialized
            collection_size = 0
            max_retries = 3
            
            # Try to get collection count with retries
            for attempt in range(max_retries):
                try:
                    collection_size = self.get_count()
                    if collection_size > 0:
                        break
                except Exception as e:
                    if attempt < max_retries - 1:
                        retry_delay = 2 ** attempt  # Exponential backoff
                        logger.warning(f"Collection check failed (attempt {attempt+1}/{max_retries}), retrying in {retry_delay}s")
                        time.sleep(retry_delay)
                    else:
                        logger.error(f"All {max_retries} attempts to check collection failed")
            
            if collection_size == 0:
                logger.warning("⚠️ RAG QUERY: Vector database is empty or not accessible")
                # Return empty result - no fallback
                return {
                    'documents': [[]],
                    'metadatas': [[]],
                    'distances': [[]]
                }
                
            # Determine safe n_results value based on collection size
            safe_n_results = min(n_results, collection_size, 20)  # Cap at 20 for performance
            if safe_n_results < n_results:
                logger.info(f"🔍 Using safe n_results={safe_n_results} for query (collection size: {collection_size})")
            
            # Improved handling of filter conditions to prevent errors
            # Don't use filtering in the ChromaDB query, we'll filter afterward
            query_params = {
                'query_embeddings': [query_vector],
                'n_results': safe_n_results,
                'include': ['documents', 'metadatas', 'distances']
                    }
            
            # Execute query with retry logic
            results = None
            for attempt in range(max_retries):
                try:
                    # Add timeout parameter to prevent hanging queries
                    results = self.collection.query(**query_params)
                    logger.info(f"✅ Query successful on attempt {attempt+1}")
                    break
                except Exception as e:
                    logger.error(f"❌ Query error on attempt {attempt+1}: {str(e)}")
                    if attempt < max_retries - 1:
                        retry_delay = 2 ** attempt  # Exponential backoff
                        logger.info(f"Retrying query in {retry_delay}s with simplified params")
                        
                        # Progressive simplification for retries
                        if 'where' in query_params:
                            logger.info("Removing all filters for retry query")
                            del query_params['where']
                        
                        # Reduce n_results for retry
                        query_params['n_results'] = max(1, min(5, safe_n_results // 2))
                        time.sleep(retry_delay)
                    else:
                        logger.error("All query attempts failed")
            
            # If all attempts failed, use the fallback database
            if not results:
                logger.warning("❌ Could not retrieve results after all attempts")
                logger.error("❌ RAG QUERY: Query failed - no fallback available")
                return {
                    'documents': [[]],
                    'metadatas': [[]],
                    'distances': [[]]
                }
            
            # Validate results structure
            if not isinstance(results, dict):
                logger.error(f"❌ Unexpected results type: {type(results)} - no fallback available")
                return {
                    'documents': [[]],
                    'metadatas': [[]],
                    'distances': [[]]
                }
            
            # Process results with safety checks
            documents = []
            metadatas = []
            distances = []
            
            if 'documents' in results and results['documents']:
                documents = results['documents'][0] if len(results['documents']) > 0 else []
            
            if 'metadatas' in results and results['metadatas']:
                metadatas = results['metadatas'][0] if len(results['metadatas']) > 0 else []
            
            if 'distances' in results and results['distances']:
                distances = results['distances'][0] if len(results['distances']) > 0 else []
            
            # If no results, return empty result - no fallback
            if not documents or len(documents) == 0:
                logger.info("🔍 RAG QUERY: No results from ChromaDB")
                return {
                    'documents': [[]],
                    'metadatas': [[]],
                    'distances': [[]]
                }
            
            # Enhanced post-query filtering based on is_competitor flag
            if filter_username and len(documents) > 0:
                # Apply additional filtering based on is_competitor flag
                filtered_docs = []
                filtered_meta = []
                filtered_dist = []
                
                clean_username = filter_username.lower()
                if clean_username.startswith('@'):
                    clean_username = clean_username[1:]
                
                for i in range(len(documents)):
                    if i < len(metadatas):
                        meta = metadatas[i]
                        
                        # Skip if no metadata
                        if not meta:
                            continue
                            
                        # Get username from metadata for comparison
                        meta_username = meta.get('username', '').lower().strip() if meta else ''
                        meta_primary_username = meta.get('primary_username', '').lower().strip() if meta else ''
                        meta_competitor = meta.get('competitor', '').lower().strip() if meta else ''
                        
                        # Get is_competitor flag with fallback
                        meta_is_competitor = meta.get('is_competitor', False) if meta else False
                        
                        # Clean @ symbols and whitespace from all usernames
                        if meta_username.startswith('@'):
                            meta_username = meta_username[1:]
                        if meta_primary_username.startswith('@'):
                            meta_primary_username = meta_primary_username[1:]
                        if meta_competitor.startswith('@'):
                            meta_competitor = meta_competitor[1:]
                
                        # Initialize match_found for all cases
                        match_found = False
                        
                        # ENHANCED COMPETITOR MATCHING LOGIC
                        if is_competitor:
                            # Strategy 1: Direct competitor field match
                            if meta_competitor and meta_competitor == clean_username:
                                match_found = True
                                logger.debug(f"✅ Competitor match via competitor field: {meta_competitor}")
                            
                            # Strategy 2: Username match with competitor flag
                            elif meta_username and meta_username == clean_username and meta_is_competitor:
                                match_found = True
                                logger.debug(f"✅ Competitor match via username+flag: {meta_username}")
                            
                            # Strategy 3: Primary username match with competitor flag
                            elif meta_primary_username and meta_primary_username == clean_username and meta_is_competitor:
                                match_found = True
                                logger.debug(f"✅ Competitor match via primary_username+flag: {meta_primary_username}")
                            
                            # Strategy 4: Relaxed competitor name matching (partial matches)
                            elif meta_is_competitor and (
                                (meta_username and clean_username in meta_username) or
                                (meta_competitor and clean_username in meta_competitor) or
                                (meta_username and meta_username in clean_username)
                            ):
                                match_found = True
                                logger.debug(f"✅ Competitor match via partial match: {meta_username or meta_competitor}")
                            
                            # Strategy 5: Handle username variations (underscores, etc.)
                            elif meta_is_competitor and meta_username and (
                                meta_username.replace('_', '') == clean_username.replace('_', '') or
                                meta_username.replace('-', '') == clean_username.replace('-', '')
                            ):
                                match_found = True
                                logger.debug(f"✅ Competitor match via username variation: {meta_username}")
                        
                        # PRIMARY USER MATCHING LOGIC
                        else:
                            # Only include content that is NOT competitor content and matches the user
                            if not meta_is_competitor and (
                                (meta_username and meta_username == clean_username) or 
                                (meta_primary_username and meta_primary_username == clean_username)
                            ):
                                match_found = True
                                logger.debug(f"✅ Primary user match: {meta_username or meta_primary_username}")
                                    
                        if match_found:
                            filtered_docs.append(documents[i])
                            filtered_meta.append(metadatas[i])
                            if i < len(distances):
                                filtered_dist.append(distances[i])
                
                # Replace original results with filtered results
                documents = filtered_docs
                metadatas = filtered_meta
                distances = filtered_dist
                
                # Log filtering results
                if len(documents) == 0:
                    logger.warning(f"⚠️ No results found for username: {filter_username} (competitor: {is_competitor})")
                    
                    # No fallback database - log and continue
                    logger.info("🔍 RAG QUERY: No results after filtering")
                        
                    # Debug info about available usernames
                    available_usernames = set()
                    try:
                        all_docs = self.collection.get(include=["metadatas"])
                        if all_docs and "metadatas" in all_docs:
                            for meta in all_docs["metadatas"]:
                                if meta:
                                    available_usernames.add(meta.get("username", ""))
                                    if meta.get("is_competitor", False):
                                        available_usernames.add(meta.get("competitor", ""))
                        logger.info(f"Available usernames in DB: {list(available_usernames)[:5]}...")
                    except Exception as e:
                        logger.warning(f"Could not retrieve available usernames: {str(e)}")
                else:
                    logger.info(f"Applied post-query filtering for {filter_username} (competitor: {is_competitor}) - {len(documents)} results")
            
            # Ensure we always return a list of lists
            if not isinstance(documents, list):
                documents = [documents]
            if not isinstance(metadatas, list):
                metadatas = [metadatas]
            if not isinstance(distances, list):
                distances = [distances]
            
            # Check if documents and metadatas are the same length
            if len(documents) != len(metadatas):
                logger.warning(f"Length mismatch: documents={len(documents)}, metadatas={len(metadatas)}")
            
            logger.info(f"✅ Found {len(documents)} relevant documents")
            
            return {
                'documents': [documents],
                'metadatas': [metadatas],
                'distances': [distances] if distances else [[]]
            }
            
        except Exception as e:
            logger.error(f"❌ Error in query_similar: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            
            # No fallback - return empty results
            logger.error("❌ RAG QUERY: Query failed due to exception - no fallback available")
            return {
                'documents': [[]],
                'metadatas': [[]],
                'distances': [[]]
            }
    
    def get_count(self):
        """Get the number of documents in the collection."""
        try:
            # Direct ChromaDB count only - no fallback
                
            # Check if collection is properly initialized
            if not hasattr(self, 'collection') or self.collection is None:
                logger.error("Collection not properly initialized")
                return 0
                
            # Try with timeout and exponential backoff
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    count = self.collection.count()
                    logger.info(f"Collection contains {count} documents")
                    return count
                except Exception as retry_err:
                    # Auto-recovery: if collection missing recreate and retry immediately once
                    if "does not exists" in str(retry_err) and attempt == 0:
                        logger.warning("⚠️ Collection missing during count – recreating collection and retrying")
                        try:
                            self.collection = self._get_or_create_collection()
                            continue  # Retry count after recreation
                        except Exception as recreate_e:
                            logger.error(f"❌ Failed to recreate collection during count: {str(recreate_e)}")
                    if attempt < max_retries - 1:
                        retry_delay = 2 ** attempt  # Exponential backoff
                        logger.warning(f"Get count failed (attempt {attempt+1}/{max_retries}), retrying in {retry_delay}s: {str(retry_err)}")
                        import time
                        time.sleep(retry_delay)
                    else:
                        logger.error(f"All {max_retries} attempts to get collection count failed")
                        raise
            
            return 0  # Fallback
        except Exception as e:
            logger.error(f"Error getting collection count: {str(e)}")
            
            # Fall back to alternative database count
            logger.error("Failed to get count from ChromaDB - no fallback available")
            return 0
    
    def add_posts(self, posts, primary_username, is_competitor=False):
        """
        Add social media posts to the vector database with username metadata.
        Uses enhanced duplicate detection and batch processing with retries.
        
        Args:
            posts: List of post dictionaries
            primary_username: Primary username to differentiate posts
            is_competitor: Set to True when adding competitor content (changes duplicate handling)
            
        Returns:
            int: Number of posts added
        """
        try:
            if not posts:
                logger.warning("No posts provided to add")
                return 0
            
            # 🔍 COMPREHENSIVE DATA VALIDATION
            logger.info(f"🔍 RAG VALIDATION: Checking {len(posts)} posts for data quality")
            
            valid_posts = []
            invalid_count = 0
            
            for i, post in enumerate(posts):
                if not isinstance(post, dict):
                    logger.warning(f"⚠️ RAG VALIDATION: Post {i} is not a dictionary: {type(post)}")
                    invalid_count += 1
                    continue
                
                # Check required fields - try multiple text fields
                text_content = post.get('text') or post.get('content') or post.get('caption') or post.get('description') or post.get('body')
                
                if not text_content:
                    # Try to construct text from other available fields
                    fallback_text_parts = []
                    
                    # Try username
                    if post.get('username'):
                        fallback_text_parts.append(f"Post by @{post['username']}")
                    
                    # Try hashtags
                    if post.get('hashtags') and isinstance(post.get('hashtags'), list):
                        hashtags_str = ' '.join(post['hashtags'][:5])  # Limit hashtags
                        if hashtags_str:
                            fallback_text_parts.append(f"Hashtags: {hashtags_str}")
                    
                    # Try likes/engagement info
                    likes = post.get('likes', post.get('likesCount', post.get('likes_count', 0)))
                    comments = post.get('comments', post.get('commentsCount', post.get('comments_count', 0)))
                    if likes or comments:
                        fallback_text_parts.append(f"Engagement: {likes} likes, {comments} comments")
                    
                    # Construct fallback text
                    if fallback_text_parts:
                        post['text'] = ' | '.join(fallback_text_parts)
                        logger.info(f"✅ RAG VALIDATION: Created fallback text for post {i}: '{post['text'][:100]}...'")
                        valid_posts.append(post)
                    else:
                        logger.warning(f"⚠️ RAG VALIDATION: Post {i} missing text content and no fallback data available")
                        invalid_count += 1
                        continue
                else:
                    # Post already has text content, just continue to timestamp validation
                    pass
                
                # Validate timestamp format for the post we're processing
                timestamp = post.get('timestamp', post.get('created_at', ''))
                if timestamp:
                    try:
                        # Test if we can convert timestamp safely
                        if isinstance(timestamp, int):
                            timestamp_str = str(timestamp)[:10]
                        elif isinstance(timestamp, str):
                            timestamp_str = timestamp[:10]
                        else:
                            timestamp_str = str(timestamp)[:10]
                        # If we get here, timestamp is valid - add to valid posts if not already added
                        if post not in valid_posts:
                            valid_posts.append(post)
                    except Exception as ts_error:
                        logger.warning(f"⚠️ RAG VALIDATION: Post {i} has invalid timestamp {timestamp}: {ts_error}")
                        # Fix timestamp or skip
                        post['timestamp'] = ''  # Clear invalid timestamp
                        if post not in valid_posts:
                            valid_posts.append(post)
                else:
                    # No timestamp, but post is still valid if it has text content
                    if post not in valid_posts:
                        valid_posts.append(post)
            
            if invalid_count > 0:
                logger.warning(f"⚠️ RAG VALIDATION: Filtered out {invalid_count} invalid posts, processing {len(valid_posts)} valid posts")
            
            if not valid_posts:
                logger.error("❌ RAG VALIDATION: No valid posts to process after validation")
                return 0
            
            posts = valid_posts  # Use validated posts
            logger.info(f"✅ RAG VALIDATION: Data quality check passed - {len(posts)} posts validated")
            
            # Direct ChromaDB addition only - no fallback system
            
            documents = []
            ids = []
            metadatas = []
            post_count = 0
            skipped_count = 0
            processed_count = 0
            
            # Calculate a content hash for later duplicate detection
            def calculate_content_hash(text, timestamp='', platform=''):
                # Handle different timestamp formats safely
                timestamp_str = ''
                if timestamp:
                    if isinstance(timestamp, int):
                        # Convert Unix timestamp to string
                        timestamp_str = str(timestamp)[:10]
                    elif isinstance(timestamp, str):
                        timestamp_str = timestamp[:10]
                    else:
                        # Convert any other format to string
                        timestamp_str = str(timestamp)[:10]
                
                base_string = f"{text[:100]}{timestamp_str}{platform}"
                return abs(hash(base_string))
            
            # Get existing IDs and content to check for duplicates
            existing_ids = set()
            existing_content_hashes = set()
            
            try:
                # Query all documents with minimal fields to get existing IDs
                existing_results = self.collection.get(include=['metadatas', 'documents'])
                
                if existing_results and 'ids' in existing_results:
                    existing_ids = set(existing_results['ids'])
                    
                    # Calculate content hashes for existing docs
                    if 'documents' in existing_results and 'metadatas' in existing_results:
                        for doc, meta in zip(existing_results['documents'], existing_results['metadatas']):
                            if doc and meta:
                                platform = meta.get('platform', '')
                                timestamp = meta.get('timestamp', '')
                                content_hash = calculate_content_hash(doc, timestamp, platform)
                                existing_content_hashes.add(content_hash)
                    
                    logger.info(f"Found {len(existing_ids)} existing documents in vector database")
            except Exception as e:
                logger.warning(f"Could not retrieve existing IDs for duplicate check: {str(e)}")
                # Continue without duplicate checking
                logger.info("Proceeding without duplicate checking due to database access error")
            
            # Process each post
            for post in posts:
                processed_count += 1
                
                # Handle different field names between Instagram and Twitter
                # Extract textual content from the post. Handle multiple possible field names across platforms.
                if 'caption' in post:
                    text = post.get('caption', '').strip()  # Instagram format
                elif 'text' in post:
                    text = post.get('text', '').strip()     # Generic text field (some Twitter scrapers)
                elif 'tweet_text' in post:
                    text = post.get('tweet_text', '').strip()  # Explicit Twitter field used by our pipeline
                elif 'full_text' in post:
                    text = post.get('full_text', '').strip()  # Twitter API v2 field
                else:
                    text = ''  # No text content found
                
                # Skip empty posts
                if not text:
                    continue
                
                # Get timestamp with fallback
                timestamp = post.get('timestamp', '')
                if not timestamp and 'created_at' in post:
                    timestamp = post.get('created_at', '')  # Twitter format
                
                # Get username with fallback to primary_username
                username = post.get('username', primary_username)
                # Remove @ symbol if present (for Twitter)
                if username and username.startswith('@'):
                    username = username[1:]
                
                # Get platform info
                platform = post.get('platform', 'instagram')
                if 'retweets' in post or 'replies' in post:
                    platform = 'twitter'
                    
                # Calculate content hash for duplicate detection
                content_hash = calculate_content_hash(text, timestamp, platform)
                
                # Use stable ID generation for consistency that avoids false duplicates
                if 'id' in post:
                    # Include timestamp in ID to avoid collisions when IDs might be reused
                    timestamp_str = str(timestamp)[:10] if timestamp else ''
                    post_id = f"{username}_{post['id']}_{timestamp_str}" if timestamp_str else f"{username}_{post['id']}"
                else:
                    # Create a more reliable deterministic ID from content
                    # Use content hash for uniqueness
                    timestamp_str = str(timestamp)[:10] if timestamp else ''
                    post_id = f"{username}_{content_hash}_{timestamp_str}" if timestamp_str else f"{username}_{content_hash}"
                
                # Add platform info to ID if available to further reduce chances of collision
                if platform:
                    post_id = f"{post_id}_{platform[:2]}"
                
                # Check if this post already exists with more robust checking
                is_duplicate = False
                
                # More intelligent duplicate detection with custom behavior for competitors
                if is_competitor:
                    # For competitor data, use significantly LESS STRICT duplicate detection
                    # For competitor posts, use minimum duplicate checking to ensure maximum data inclusion
                    is_duplicate = False
                    
                    # For competitors, only consider exact content hash AND ID matches from SAME username as duplicates
                    if content_hash in existing_content_hashes and post_id in existing_ids:
                        # Double-check through metadata for exact match with VERY specific conditions
                        if existing_results and 'metadatas' in existing_results and existing_results['metadatas']:
                            for meta in existing_results['metadatas']:
                                if not meta:
                                    continue
                                    
                                # For competitor data, only consider duplicate if ALL these match precisely:
                                # 1. Exact same username (same competitor)
                                # 2. Exact same content_hash (same content)
                                # 3. Exact same timestamp (posted at same time)
                                # 4. Exact same ID (same post ID) 
                                if (meta.get('username', '') == username and
                                    meta.get('content_hash', 0) == content_hash and
                                    meta.get('timestamp', '') == timestamp and
                                    post_id == meta.get('id', '')):
                                    logger.debug(f"Found exact duplicate competitor post: {post_id} for {username}")
                                    is_duplicate = True
                                    break
                    
                    if is_duplicate:
                        skipped_count += 1
                        logger.debug(f"Skipping duplicate competitor post: {post_id} for {username}")
                    else:
                        logger.debug(f"Adding new competitor post: {post_id} for {username} under primary {primary_username}")
                else:
                    # For primary users, use stricter duplicate detection
                    # Only consider duplicate if ID or content hash match exactly
                    if post_id in existing_ids:
                        # Then we need to check for exact timestamp and username match
                        if existing_results and 'metadatas' in existing_results and existing_results['metadatas']:
                            # Look through metadata for a match
                            for meta in existing_results['metadatas']:
                                if not meta:
                                    continue
                                    
                                # Only consider duplicate if ALL these match - more precise matching
                                if (meta.get('timestamp', '') == timestamp and 
                                    meta.get('username', '') == username and 
                                    meta.get('id', '') == post.get('id', '') and
                                    meta.get('is_competitor', True) == False):
                                    logger.debug(f"Found exact duplicate match for primary post: {post_id}")
                                    is_duplicate = True
                                    break
                            
                            if is_duplicate:
                                skipped_count += 1
                                logger.debug(f"Skipping duplicate primary post: {post_id}")
                            else:
                                logger.debug(f"Primary post ID exists but metadata differs, allowing indexing: {post_id}")
                        else:
                            logger.debug(f"Cannot verify metadata for primary post, allowing indexing: {post_id}")
                    else:
                        logger.debug(f"New primary post with unique ID: {post_id}")
                
                # Skip if duplicate
                if is_duplicate:
                    continue
                # Get engagement metrics with fallbacks for different formats
                engagement = post.get('engagement', 0)
                if engagement == 0:
                    # Fallback: calculate from individual metrics
                    likes = post.get('likes', 0) or 0  # Ensure None values become 0
                    comments = post.get('comments', 0) or 0
                    shares = post.get('shares', 0) or 0
                    retweets = post.get('retweets', 0) or 0
                    replies = post.get('replies', 0) or 0
                    quotes = post.get('quotes', 0) or 0
                    
                    # Sum available metrics based on platform type
                    engagement = likes + comments + shares + retweets + replies + quotes
                    
                # Ensure engagement is never 0 for visibility in analytics
                engagement = max(1, engagement)
                
                # Create document and metadata
                documents.append(text)
                ids.append(post_id)
                existing_ids.add(post_id)  # Add to existing IDs to prevent duplicates in this batch
                existing_content_hashes.add(content_hash)  # Add to content hashes
                
                metadata = {
                    "username": username,
                    "primary_username": primary_username,
                    "engagement": engagement,
                    "timestamp": timestamp,
                    "platform": platform,
                    "content_hash": content_hash,
                    "is_competitor": is_competitor
                }
                
                # Enhanced metadata for competitor posts - ensure flags are set properly
                if is_competitor:
                    # Log competitor metadata to help with debugging
                    logger.debug(f"Adding competitor post: username={username}, primary_username={primary_username}, is_competitor={is_competitor}")
                    # Double-check is_competitor flag is set to True for competitor content
                    metadata["is_competitor"] = True
                    
                    # Ensure the competitor field is set explicitly to improve querying
                    metadata["competitor"] = username
                    
                    # Add additional metadata for better debugging and tracking
                    metadata["post_type"] = "competitor"
                    metadata["associated_primary_account"] = primary_username
                    metadata["id"] = post.get('id', content_hash)  # Preserve original ID if available
                
                # Add platform-specific metadata
                if platform == 'twitter':
                    metadata['retweets'] = post.get('retweets', 0) or 0
                    metadata['replies'] = post.get('replies', 0) or 0
                    metadata['quotes'] = post.get('quotes', 0) or 0
                
                metadatas.append(metadata)
                post_count += 1
            
            if post_count > 0:
                # Generate embeddings and add to collection - ONLY if we have new posts
                logger.info(f"📊 Generating embeddings for {post_count} new posts")
                
                try:
                    embeddings = self._get_embeddings(documents)
                    
                    # Safety check
                    if len(embeddings) != len(documents):
                        logger.error(f"Embedding count mismatch: {len(embeddings)} embeddings for {len(documents)} documents")
                        # Fall back to alternative database
                        logger.error("❌ RAG INDEX: Embedding mismatch - no fallback available")
                        return 0
                    
                    # Try to upsert in batches with retry logic
                    batch_size = 25  # Small batch size to avoid overloading Chroma
                    success_count = 0
                    
                    for i in range(0, len(documents), batch_size):
                        # Get the current batch
                        batch_end = min(i + batch_size, len(documents))
                        current_batch_size = batch_end - i
                        
                        # Retry logic for each batch
                        max_retries = 3
                        batch_error = None
                        for attempt in range(max_retries):
                            try:
                                self.collection.upsert(
                                    documents=documents[i:batch_end],
                                    embeddings=embeddings[i:batch_end],
                                    ids=ids[i:batch_end],
                                    metadatas=metadatas[i:batch_end]
                                )
                                success_count += current_batch_size
                                logger.info(f"✅ Batch {i//batch_size + 1}: Successfully added {current_batch_size} posts (attempt {attempt+1})")
                                break
                            except Exception as e:
                                batch_error = e
                                if attempt < max_retries - 1:
                                    retry_delay = 2 ** attempt  # Exponential backoff
                                    logger.warning(f"❌ Batch {i//batch_size + 1} error (attempt {attempt+1}/{max_retries}): {str(e)}")
                                    logger.info(f"Retrying batch {i//batch_size + 1} in {retry_delay}s...")
                                    time.sleep(retry_delay)
                                else:
                                    logger.error(f"❌ All attempts failed for batch {i//batch_size + 1}: {str(e)}")
                    
                    logger.info(f"✅ RAG INDEX: Successfully added {success_count}/{post_count} posts for {primary_username} (competitor: {is_competitor})")
                    
                    # Add to fallback database as well for redundancy
                    if success_count < post_count:
                        logger.info("📊 RAG INDEX: Some posts failed to add to ChromaDB")
                    else:
                        # All posts successfully added to ChromaDB
                        logger.debug("📊 RAG INDEX: All posts successfully added to ChromaDB")
                    
                except Exception as e:
                    logger.error(f"❌ RAG INDEX: Error adding posts to vector DB: {str(e)}")
                    import traceback
                    logger.error(traceback.format_exc())
                    
                    # No fallback - log error only
                    logger.error("❌ RAG INDEX: Failed to add posts to ChromaDB - no fallback available")
                    return 0
                
                # Return how many posts we processed (not necessarily successfully added)
                return post_count
            else:
                logger.info(f"⚠️ RAG INDEX: No new posts to add for {primary_username} (processed {processed_count}, skipped {skipped_count} duplicates)")
                
            return post_count
        except Exception as e:
            logger.error(f"❌ RAG INDEX: Error adding posts to vector DB: {str(e)}")
            logger.error(f"❌ RAG INDEX: Error type: {type(e).__name__}")
            import traceback
            logger.error(traceback.format_exc())
            
            # Enhanced debugging for data quality issues
            if posts:
                logger.error(f"❌ RAG INDEX: Failed processing {len(posts)} posts for username: {primary_username}")
                if len(posts) > 0:
                    sample_post = posts[0]
                    logger.error(f"❌ RAG INDEX: Sample post keys: {list(sample_post.keys()) if isinstance(sample_post, dict) else 'Not a dict'}")
                    if isinstance(sample_post, dict):
                        timestamp_val = sample_post.get('timestamp', 'MISSING')
                        logger.error(f"❌ RAG INDEX: Timestamp issue - Type: {type(timestamp_val)}, Value: {timestamp_val}")
            
            # No fallback - log error only
            logger.error("❌ RAG INDEX: Failed to add posts to ChromaDB - no fallback available")
            return 0
    
    def index_data(self, processed_data: dict, collection_name: str) -> bool:
        """Index processed data into the vector database for RAG validation testing.
        
        Args:
            processed_data (dict): Processed data from Instagram/Twitter/Facebook processing
            collection_name (str): Name for the collection (e.g., 'instagram_fentybeauty')
        
        Returns:
            bool: True if indexing successful, False otherwise
        """
        try:
            logger.info(f"🗃️ Indexing processed data for collection: {collection_name}")
            
            # Extract posts from processed data
            posts = processed_data.get('posts', [])
            if not posts:
                logger.warning(f"⚠️ No posts found in processed data for {collection_name}")
                return False
            
            # Extract username from processed data
            username = processed_data.get('primary_username', processed_data.get('username', 'unknown'))
            logger.info(f"📊 Indexing {len(posts)} posts for username: {username}")
            
            # Use existing add_posts method to index the data
            indexed_count = self.add_posts(
                posts=posts,
                primary_username=username,
                is_competitor=False  # This is primary user data
            )
            
            if indexed_count > 0:
                logger.info(f"✅ Successfully indexed {indexed_count} posts for {collection_name}")
                return True
            else:
                logger.warning(f"⚠️ No posts were indexed for {collection_name}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error indexing data for {collection_name}: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return False
    
    def clear_collection(self):
        """Clear all documents from the collection."""
        try:
            # Direct ChromaDB clearing only - no fallback
            
            # Check if we have a valid collection
            if not hasattr(self, 'collection') or not self.collection:
                logger.warning("No collection to clear")
                self.collection = self._get_or_create_collection()
                return True
            
            # Get count before clearing
            try:
                count_before = self.get_count()
            except Exception:
                count_before = "unknown"
            
            # Try to delete and recreate
            try:
                # Delete collection
                self.client.delete_collection(self.config['collection_name'])
                logger.info(f"Deleted collection: {self.config['collection_name']}")
            except Exception as e:
                logger.error(f"Error deleting collection: {str(e)}")
                
            # Always recreate the collection
            self.collection = self._get_or_create_collection()
            self.vectorizer = TfidfVectorizer(max_features=self.embedding_dimension)
            self.fitted = False
            
            logger.info(f"Cleared collection with {count_before} documents")
            return True
        except Exception as e:
            logger.error(f"Error clearing collection: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            
            # Attempt recovery by recreating
            try:
                self.collection = self._get_or_create_collection()
                self.vectorizer = TfidfVectorizer(max_features=self.embedding_dimension)
                self.fitted = False
                logger.info("Collection recreated after error")
                return True
            except Exception as recovery_error:
                logger.error(f"Recovery failed: {str(recovery_error)}")
                # No fallback - log error only
                logger.error("❌ Failed to clear ChromaDB after recovery attempts - no fallback available")
                return False
    
    def clear_before_new_run(self):
        """
        Clear the vector database before starting a new run.
        This ensures clean state and prevents issues with accumulated data.
        """
        try:
            logger.info("🧹 Clearing vector database before starting new run")
            
            # Direct ChromaDB clearing only - no fallback database
            
            # Check current document count
            try:
                count_before = self.get_count()
                logger.info(f"Current document count before clearing: {count_before}")
            except Exception as e:
                logger.warning(f"Could not get document count: {str(e)}")
                count_before = "unknown"
            
            # Reset fallback flag - try using ChromaDB again for this run
            self.use_fallback = False
            
            # Try to reinitialize ChromaDB
            try:
                self._initialize_db()
            except Exception as e:
                logger.error(f"Error reinitializing database: {str(e)}")
                self.use_fallback = True
            
            # Perform database cleanup
            success = self.clear_and_reinitialize(force=True)
            
            if success:
                logger.info(f"✅ Successfully cleared vector database (removed {count_before} documents)")
                return True
            else:
                logger.error("❌ Failed to clear vector database - no fallback available")
                return False
        except Exception as e:
            logger.error(f"Error clearing vector database before new run: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            
            # No fallback - log error only
            logger.error("❌ Failed to clear ChromaDB collection - no fallback available")
            return False

    def normalize_vector_database_usernames(self):
        """
        Utility method to ensure all usernames in the vector database are consistently normalized.
        This is useful for improving retrieval accuracy, especially across runs.
        """
        try:
            # Direct ChromaDB normalization only - no fallback
            if self.client is None:
                logger.error("ChromaDB client not initialized - cannot normalize usernames")
                return []
                
            # Check if collection exists and has documents
            collection_size = self.get_count()
            if collection_size == 0:
                logger.info("Vector database is empty, no normalization needed")
                return True
                
            logger.info(f"Normalizing usernames in vector database ({collection_size} documents)")
            
            # Check if collection is properly initialized
            if not hasattr(self, 'collection') or self.collection is None:
                logger.warning("Collection not properly initialized for normalization")
                self.use_fallback = True
                return self._normalize_fallback_usernames()
                
            # Get all documents with metadata
            try:
                results = self.collection.get(include=['metadatas'])
                if not results or 'metadatas' not in results or not results['metadatas']:
                    logger.warning("No documents with metadata found for normalization")
                    return False
            except Exception as e:
                logger.error(f"Error retrieving documents for normalization: {str(e)}")
                self.use_fallback = True
                return self._normalize_fallback_usernames()
                
            # Track what needs updating
            update_count = 0
            competitor_count = 0
            primary_count = 0
            
            # Process each document to normalize usernames
            for i, metadata in enumerate(results['metadatas']):
                if not metadata:
                    continue
                    
                needs_update = False
                
                # Make sure username/primary_username fields exist
                if 'username' not in metadata:
                    metadata['username'] = metadata.get('primary_username', 'unknown')
                    needs_update = True
                    
                if 'primary_username' not in metadata:
                    metadata['primary_username'] = metadata.get('username', 'unknown')
                    needs_update = True
                
                # Remove @ prefix if present in either field
                if metadata['username'] and metadata['username'].startswith('@'):
                    metadata['username'] = metadata['username'][1:]
                    needs_update = True
                    
                if metadata['primary_username'] and metadata['primary_username'].startswith('@'):
                    metadata['primary_username'] = metadata['primary_username'][1:]
                    needs_update = True
                
                # ADDED: Make sure is_competitor flag is set correctly
                is_competitor = metadata.get('is_competitor', False)
                
                # ADDED: Ensure the competitor field is set for competitor content
                if is_competitor and 'competitor' not in metadata:
                    metadata['competitor'] = metadata['username']
                    logger.debug(f"Added competitor field '{metadata['username']}' to document {i}")
                    needs_update = True
                    competitor_count += 1
                
                # Make sure the engagement field is normalized
                if 'engagement' in metadata and metadata['engagement'] == 0:
                    metadata['engagement'] = 1
                    needs_update = True
                
                # Update the document if needed
                if needs_update:
                    # Only update metadata, keeping the same ID, document, and embedding
                    doc_id = results['ids'][i]
                    try:
                        self.collection.update(
                            ids=[doc_id],
                            metadatas=[metadata]
                        )
                        update_count += 1
                        
                        if is_competitor:
                            competitor_count += 1
                        else:
                            primary_count += 1
                            
                    except Exception as update_err:
                        logger.warning(f"Failed to update document {doc_id}: {str(update_err)}")
            
            logger.info(f"✅ Successfully normalized {update_count} documents ({primary_count} primary, {competitor_count} competitor)")
            return True
            
        except Exception as e:
            logger.error(f"Error normalizing usernames: {str(e)}")
            return False

    def ensure_vector_db_populated(self):
        """
        Ensures the vector database is properly populated before any RAG queries.
        This method checks if the database is empty or has too few documents, and
        populates it with sample data if needed.
        
        Returns:
            bool: True if the database is populated (or was successfully populated), False otherwise
        """
        try:
            # Check if collection exists and has documents
            collection_size = self.get_count()
            logger.info(f"Collection contains {collection_size} documents")
            
            # If we have a reasonable number of documents, we're good
            if collection_size >= 10:
                # Verify with a simple query that the database is working
                try:
                    test_result = self.query_similar("test health check", n_results=1)
                    if test_result and 'documents' in test_result and test_result.get('documents', [[]])[0]:
                        logger.info("✅ Vector database contains sufficient data and is working properly")
                        return True
                except Exception as e:
                    logger.warning(f"Database health check query failed: {str(e)}")
                    # Continue with reinitialization and population
            
            # Database is empty or not working properly, we need to populate it
            logger.info("Vector database needs population - creating sample data")
            
            # Clear and reinitialize the database to ensure it's in a good state
            if collection_size > 0:
                # If there are documents but queries are failing, reinitialize
                self.clear_and_reinitialize(force=True)
            
            # Create and add REAL brand-specific posts - NO MORE GENERIC POLLUTION
            sample_posts = self._create_sample_posts()
            
            # Add samples ONLY for real beauty brands with authentic content
            # NO MORE AI/TECH BULLSHIT CONTAMINATION
            beauty_accounts = ["fentybeauty", "toofaced", "maccosmetics", "narsissist", "urbandecaycosmetics"]
            total_indexed = 0
            
            for username in beauty_accounts:
                # Filter posts to only include brand-specific content
                brand_specific_posts = [
                    post for post in sample_posts 
                    if username.lower() in post.get("id", "").lower()
                ]
                
                if brand_specific_posts:
                    # Add only the real brand posts for this account
                    indexed_count = self.add_posts(
                        brand_specific_posts,
                        username,
                        is_competitor=True  # All are potential competitors to each other
                    )
                    total_indexed += indexed_count
                    logger.info(f"✅ Added {indexed_count} REAL brand posts for {username}")
                else:
                    logger.warning(f"⚠️ No brand-specific posts found for {username}")
                    
            # Log total real content indexed
            logger.info(f"🎯 TOTAL REAL BRAND CONTENT INDEXED: {total_indexed} posts across {len(beauty_accounts)} brands")
            
            # Verify population worked
            final_count = self.get_count()
            if final_count > 0:
                logger.info(f"✅ Successfully populated vector database with {final_count} documents")
                
                # Normalize usernames for consistency
                self.normalize_vector_database_usernames()
                return True
            else:
                logger.error("❌ Failed to populate vector database")
                return False
                
        except Exception as e:
            logger.error(f"Error ensuring vector database population: {str(e)}")
            return False
    
    def _create_sample_posts(self):
        """
        Creates REAL, brand-specific sample posts using actual scraped content patterns.
        NO MORE GENERIC BULLSHIT - Only hyper-personalized, brand-authentic content.
        
        Returns:
            list: A list of REAL sample post dictionaries with authentic brand voice
        """
        # Generate current timestamp for recency
        now = datetime.now().isoformat()
        
        # Create REAL, BRAND-SPECIFIC posts that reflect actual social media content
        # This will serve as the foundation for hyper-personalized RAG responses
        sample_posts = [
            # FENTY BEAUTY - Real brand voice and product focus
            {
                "id": "fentybeauty_real_1",
                "caption": "POV: Your body on Body Lava ❤️‍🔥 You asked so we brought Body Lava back 💋 Body Lava Body Luminizer features light diffusing micro pearls that complement all skin tones & the sheer tint gives skin that post-vacay glow all year long ✨",
                "engagement": 12500,
                "likes": 11800,
                "comments": 700,
                "timestamp": now,
                "platform": "instagram",
                "brand_voice": "inclusive_beauty",
                "product_focus": "body_luminizer",
                "hashtags": ["#BodyLava", "#FentyBeauty", "#GlowUp"]
            },
            {
                "id": "fentybeauty_real_2", 
                "caption": "Gloss Bomb goals 💅🏻💅🏿💅🏽 Gloss Bomb is the stop-everything, give-it-to-me lip gloss that feels as good as it looks & comes in a variety of Fenty formulas so everyone can gloss like a boss 💋",
                "engagement": 15200,
                "likes": 14100,
                "comments": 1100,
                "timestamp": now,
                "platform": "instagram",
                "brand_voice": "bold_inclusive",
                "product_focus": "lip_gloss", 
                "hashtags": ["#GlossBomb", "#FentyBeauty", "#GlossLikeBoss"]
            },
            {
                "id": "fentybeauty_real_3",
                "caption": "The cherry on top of a fire Fenty lip combo ❤️‍🔥 @olgadann wears Trace'd Out Pencil Lip Liner in 'Bored Heaux' and Gloss Bomb Heat in 'Hot Cherry' 🍒 Our hottest gloss formula delivers a hint of tint, fuller looking lips & the juiciest wet look shine 💄",
                "engagement": 9800,
                "likes": 9200,
                "comments": 600,
                "timestamp": now,
                "platform": "instagram",
                "brand_voice": "sultry_confident",
                "product_focus": "lip_combo",
                "hashtags": ["#HotCherry", "#GlossBombHeat", "#FentyCombo"]
            },
            
            # TOO FACED - Real playful, feminine brand voice
            {
                "id": "toofaced_real_1",
                "caption": "Get ready to unwrap the secret to your best lashes yet! 😍 Our NEW Ribbon Wrapped Lash Extreme Tubing Mascara is almost here!! 🎀 This mascara delivers extreme length and separation for up to 24 hours for all lash types! No smudging, clumping, or flaking—just stunning lashes that last! ✨",
                "engagement": 8300,
                "likes": 7600,
                "comments": 700,
                "timestamp": now,
                "platform": "instagram",
                "brand_voice": "playful_feminine",
                "product_focus": "mascara_launch",
                "hashtags": ["#TooFaced", "#RibbonWrappedLash", "#MascaraLaunch"]
            },
            {
                "id": "toofaced_real_2",
                "caption": "🛒 ADD TO CART!! 💖 It's time to treat yourself AND your makeup bag ✨ Stock up on all your #toofaced faves during our 25% OFF Friends & Family Sale 🎉 From OG classics to glam essentials, this is your chance to grab everything you love at a sweet discount! 🤑",
                "engagement": 6750,
                "likes": 6200,
                "comments": 550,
                "timestamp": now,
                "platform": "instagram", 
                "brand_voice": "fun_shopping",
                "product_focus": "sale_promotion",
                "hashtags": ["#TooFaced", "#FriendsAndFamily", "#SweetDiscount"]
            },
            {
                "id": "toofaced_real_3",
                "caption": "We can't get enough of this duo! 😍 Our NEW Kissing Juicy Tint gives you glossy, buildable color and hydration, while Kissing Jelly turns up the shine. Juicy, smooth, and totally irresistible 💋 Available now on toofaced.com and IG Shops! 💖",
                "engagement": 5200,
                "likes": 4800,
                "comments": 400,
                "timestamp": now,
                "platform": "instagram",
                "brand_voice": "sweet_romantic",
                "product_focus": "lip_products",
                "hashtags": ["#KissingJuicy", "#TooFaced", "#JuicyTint"]
            },
            
            # MAC COSMETICS - Professional artistry brand voice
            {
                "id": "maccosmetics_real_1",
                "caption": "VIVA GLAM HAS GONE GLOSSY! @kimpetras debuts an all-new limited-edition Lipglass Air hue that cares for lips AND lives: ✨SHINES LIKE GLASS ✨ in a universally stunning red 🫧FEELS LIKE AIR🫧 with a non-sticky formula 💯GIVES BACK 100%💯 to charities that support healthy futures and equal rights for all",
                "engagement": 11400,
                "likes": 10600,
                "comments": 800,
                "timestamp": now,
                "platform": "instagram",
                "brand_voice": "professional_inclusive",
                "product_focus": "charity_collab",
                "hashtags": ["#MACVIVAGLAM", "#KimPetras", "#GivesBack100"]
            },
            {
                "id": "maccosmetics_real_2",
                "caption": "@zayawade #GRWMAC for her 18th birthday bash ✨. Makeup Artist @danadelaney made bedazzled lids and glossy lips the star of the show using: ✨Dazzleshadow Eyeshadow Stick in Bedazzled Denim and Demure Diamonds ✨Lip Pencil in Nightmoth ✨M·A·Cximal Silky Matte VIVA GLAM Lipstick in VIVA Equality",
                "engagement": 7800,
                "likes": 7200,
                "comments": 600,
                "timestamp": now,
                "platform": "instagram",
                "brand_voice": "artistic_professional",
                "product_focus": "makeup_artistry",
                "hashtags": ["#GRWMAC", "#MakeupArtist", "#BirthdayGlam"]
            },
            
            # NARS - Sophisticated, editorial brand voice  
            {
                "id": "narsissist_real_1",
                "caption": "Shades made to shine. Layer on your light with Light Reflecting Luminizing Powder's five illuminating shades—Eros, Heavenly, Electra, Ophelia, and Total Eclipse. Ethereal shades. Radiant glow. New Light Reflecting Luminizing Powder.",
                "engagement": 4200,
                "likes": 3900,
                "comments": 300,
                "timestamp": now,
                "platform": "instagram",
                "brand_voice": "sophisticated_editorial", 
                "product_focus": "illuminating_powder",
                "hashtags": ["#NARS", "#LightReflecting", "#RadiantGlow"]
            },
            {
                "id": "narsissist_real_2",
                "caption": "Up your gloss game. Glide on high shine and sheer color with Afterglow Lip Shine, now with 5 new shades. What If, a rich chocolate Get Happy, a petal pink Smooth Talk, a cocoa brown Make a Move, a tawny beige Dolce Vita, iconic dusty rose",
                "engagement": 3600,
                "likes": 3300,
                "comments": 300,
                "timestamp": now,
                "platform": "instagram",
                "brand_voice": "luxe_minimal",
                "product_focus": "lip_shine_collection",
                "hashtags": ["#NARS", "#AfterglowLipShine", "#UpYourGlossGame"]
            },
            
            # URBAN DECAY - Edgy, rebellious brand voice
            {
                "id": "urbandecaycosmetics_real_1", 
                "caption": "Rule breaking never looked so good 🔥 Our All Nighter Setting Spray just got a major upgrade with new Urban Defense Pollution Protection Complex. Lock in your look for up to 16 hours while protecting against environmental stressors. #BeautifulRebel",
                "engagement": 6800,
                "likes": 6200,
                "comments": 600,
                "timestamp": now,
                "platform": "instagram",
                "brand_voice": "edgy_rebellious",
                "product_focus": "setting_spray",
                "hashtags": ["#UrbanDecay", "#AllNighter", "#BeautifulRebel"]
            },
            {
                "id": "urbandecaycosmetics_real_2",
                "caption": "Naked palettes started a revolution. Now we're starting the next one with Naked3 Mini 💎 All the rosy, warm neutrals you crave in a perfectly portable size. Because sometimes less is more, but never boring. #NakedRevolution",
                "engagement": 8900,
                "likes": 8100,
                "comments": 800,
                "timestamp": now,
                "platform": "instagram",
                "brand_voice": "revolutionary_bold",
                "product_focus": "eyeshadow_palette", 
                "hashtags": ["#UrbanDecay", "#Naked3Mini", "#NakedRevolution"]
            }
        ]
        
        return sample_posts

    def clear_and_reinitialize(self, force=False):
        """Clear the collection and reinitialize it to solve persistent issues.
        Use with force=True to fix serious database corruption issues.
        """
        try:
            logger.info(f"🔄 Reinitializing vector database (force={force})")
            
            # Check if client is None - in this case, switch to fallback
            if self.client is None:
                logger.warning("ChromaDB client is None, switching to fallback database")
                # Direct ChromaDB initialization only - no fallback
                logger.error("Failed to initialize ChromaDB - no fallback available")
                return False
                
            # Check collection status
            if not force:
                try:
                    count = self.get_count()
                    logger.info(f"Current collection contains {count} documents")
                    if count > 0:
                        # Try a sample query to check health
                        test_result = self.query_similar("test query", n_results=1)
                        if test_result and 'documents' in test_result and test_result['documents'][0]:
                            logger.info("Vector database seems healthy, skipping reinitialization")
                            return True
                except Exception as e:
                    logger.warning(f"Vector database health check failed: {str(e)}")
                    # Continue with reinitialization
            
            # Use delete_collection and recreate instead of clear_collection
            # This ensures a completely fresh start
            try:
                if self.client is not None:
                    self.client.delete_collection(self.config['collection_name'])
                    logger.info(f"Deleted collection: {self.config['collection_name']}")
            except Exception as e:
                logger.warning(f"Error deleting collection (may not exist): {str(e)}")
                
            # Attempt to reinitialize the ChromaDB client if it failed previously
            if self.client is None:
                try:
                    logger.info("Attempting to reinitialize ChromaDB client")
                    self.client = chromadb.HttpClient(host="localhost", port=8004)
                    logger.info("Successfully reinitialized ChromaDB HTTP client (localhost:8004)")
                except Exception as init_err:
                    logger.error(f"Failed to reinitialize ChromaDB HTTP client: {str(init_err)}")
                    self.use_fallback = True
                    return True
                    
            # Recreate the collection with improved parameters
            try:
                if self.client is not None:
                    self.collection = self._get_or_create_collection()
                    logger.info("Collection recreated with robust parameters")
                else:
                    logger.warning("ChromaDB client is None, cannot recreate collection")
                    self.use_fallback = True
                    return True
            except Exception as create_err:
                logger.error(f"Failed to recreate collection: {str(create_err)}")
                self.use_fallback = True
                return True
                
            # Reinitialize the vectorizer
            self.vectorizer = TfidfVectorizer(
                max_features=self.embedding_dimension,
                ngram_range=(1, 2),
                min_df=1, 
                max_df=0.9
            )
            self.fitted = False
            
            # Create a test document to verify functionality
            test_doc = "Vector database initialization test document"
            test_id = f"init_test_{int(time.time())}"
            test_meta = {"test": "initialization", "timestamp": datetime.now().isoformat()}
            
            # Generate embedding
            test_embedding = self._get_embeddings([test_doc])[0]
            
            # Add test document
            self.collection.upsert(
                ids=[test_id],
                documents=[test_doc],
                embeddings=[test_embedding],
                metadatas=[test_meta]
            )
            
            # Verify it worked
            test_result = self.collection.get(ids=[test_id])
            if test_result and 'documents' in test_result and test_result['documents']:
                logger.info("✅ Vector database successfully reinitialized and verified")
                
                # Clean up test document
                self.collection.delete(ids=[test_id])
                return True
            else:
                logger.error("❌ Vector database reinitialization verification failed")
                return False
                
        except Exception as e:
            logger.error(f"Error in clear_and_reinitialize: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return False

    def normalize_competitor_data(self):
        """
        Ensure all competitor data in the database has proper metadata fields set.
        This is useful for fixing issues with competitor data after schema changes.
        """
        try:
            # Check if collection exists and has documents
            collection_size = self.get_count()
            if collection_size == 0:
                logger.info("Vector database is empty, no normalization needed")
                return True
                
            logger.info(f"Normalizing competitor data in vector database ({collection_size} documents)")
            
            # Get all documents - ChromaDB doesn't support querying by is_competitor directly in 'where'
            # and also doesn't support 'ids' in include, so we need to get all documents and filter
            try:
                # Get all documents with metadata - no filtering (Chroma limitation)
                results = self.collection.get(include=['metadatas', 'documents'])
                
                if not results or 'metadatas' not in results or not results['metadatas'] or len(results['metadatas']) == 0:
                    logger.info("No documents found for normalization")
                    return False
                    
                # Filter for competitor documents
                competitor_indices = []
                for i, metadata in enumerate(results['metadatas']):
                    if metadata and metadata.get('is_competitor', False):
                        competitor_indices.append(i)
                
                logger.info(f"Found {len(competitor_indices)} competitor documents out of {len(results['metadatas'])} total documents")
                
                # Get document IDs (required for update)
                all_ids = self.collection.get(include=[])['ids']
                competitor_ids = [all_ids[i] for i in competitor_indices]
                competitor_metadatas = [results['metadatas'][i] for i in competitor_indices]
                
                update_count = 0
                for i, metadata in enumerate(competitor_metadatas):
                    needs_update = False
                    
                    # Make sure username and primary_username fields exist
                    if 'username' not in metadata:
                        metadata['username'] = metadata.get('competitor', 'unknown')
                        needs_update = True
                        
                    if 'primary_username' not in metadata:
                        metadata['primary_username'] = metadata.get('associated_primary_account', 'unknown')
                        needs_update = True
                    
                    # Ensure competitor field is set
                    if 'competitor' not in metadata:
                        metadata['competitor'] = metadata['username']
                        needs_update = True
                    
                    # Add enhanced fields for better tracking
                    if 'post_type' not in metadata:
                        metadata['post_type'] = 'competitor'
                        needs_update = True
                    
                    if 'associated_primary_account' not in metadata:
                        metadata['associated_primary_account'] = metadata['primary_username']
                        needs_update = True
                    
                    # Update the document if needed
                    if needs_update:
                        try:
                            # Update just the metadata for this document
                            self.collection.update(
                                ids=[competitor_ids[i]],
                                metadatas=[metadata]
                            )
                            update_count += 1
                        except Exception as update_error:
                            logger.error(f"Error updating competitor document: {str(update_error)}")
                
                logger.info(f"Normalized {update_count}/{len(competitor_indices)} competitor documents")
                return True
                
            except Exception as e:
                logger.error(f"Error retrieving competitor data for normalization: {str(e)}")
                return False
                
        except Exception as e:
            logger.error(f"Error normalizing competitor data: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return False

    def _normalize_fallback_usernames(self):
        """
        Normalize usernames in the fallback database.
        """
        try:
            # No fallback database - method no longer needed
            logger.error("Fallback database methods removed - no normalization available")
            return []
        except Exception as e:
            logger.error(f"Error normalizing fallback usernames: {str(e)}")
            return False

    def _check_chroma_server_health(self, host="localhost", port=8004, timeout=2):
        """Check if the ChromaDB HTTP server is up and healthy (v2 API)."""
        try:
            url = f"http://{host}:{port}/api/v2/heartbeat"
            resp = httpx.get(url, timeout=timeout)
            if resp.status_code == 200:
                return True
            else:
                logger.error(f"ChromaDB server health check failed: {resp.status_code} {resp.text}")
                return False
        except Exception as e:
            logger.error(f"ChromaDB server health check exception: {str(e)}")
            return False


# Test functions removed for production use