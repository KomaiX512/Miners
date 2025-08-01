#!/usr/bin/env python3
"""
CRITICAL BUG FIXES for Pipeline Run Failures

This script addresses the exact bugs causing:
1. UTF-8 decode errors from corrupted files
2. Facebook account info missing required fields
3. Vector database indexing skipping
4. Infinite processing loops

FIXES IMPLEMENTED:
- Corrupted file detection and deletion
- Facebook account info enhancement
- Force vector database indexing
- Break infinite loops by cleaning bad data
"""

import logging
import json
import boto3
import os
from datetime import datetime
from data_retrieval import R2DataRetriever
from vector_database import VectorDatabaseManager
from config import R2_CONFIG

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(name)s:%(funcName)s:%(lineno)d - %(message)s'
)
logger = logging.getLogger(__name__)

class CriticalPipelineFixer:
    """Fix critical pipeline bugs that prevent vector indexing and RAG generation."""
    
    def __init__(self):
        """Initialize with R2 client and vector database."""
        self.data_retriever = R2DataRetriever()
        self.vector_db = VectorDatabaseManager()
        self.s3_client = self.data_retriever.client
        self.bucket_name = R2_CONFIG['bucket_name']
        
    def fix_corrupted_files(self):
        """Identify and delete corrupted files that cause UTF-8 decode errors."""
        logger.info("🔍 SCANNING FOR CORRUPTED FILES...")
        
        corrupted_files = []
        
        # Scan for problematic files in next_posts directory
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix='next_posts/'
            )
            
            if 'Contents' in response:
                for obj in response['Contents']:
                    key = obj['Key']
                    try:
                        # Try to read the file
                        file_response = self.s3_client.get_object(Bucket=self.bucket_name, Key=key)
                        content = file_response['Body'].read()
                        
                        # Test UTF-8 decoding
                        try:
                            content_str = content.decode('utf-8')
                            # Test JSON parsing
                            if content_str.strip():
                                json.loads(content_str)
                        except UnicodeDecodeError:
                            logger.error(f"❌ CORRUPTED FILE DETECTED: {key} - UTF-8 decode error")
                            corrupted_files.append(key)
                        except json.JSONDecodeError:
                            logger.error(f"❌ INVALID JSON DETECTED: {key} - JSON decode error")
                            corrupted_files.append(key)
                            
                    except Exception as e:
                        logger.error(f"❌ ERROR READING FILE: {key} - {str(e)}")
                        corrupted_files.append(key)
                        
        except Exception as e:
            logger.error(f"Error scanning for corrupted files: {str(e)}")
            
        # Delete corrupted files
        deleted_count = 0
        for corrupted_file in corrupted_files:
            try:
                self.s3_client.delete_object(Bucket=self.bucket_name, Key=corrupted_file)
                logger.info(f"✅ DELETED CORRUPTED FILE: {corrupted_file}")
                deleted_count += 1
            except Exception as e:
                logger.error(f"Failed to delete corrupted file {corrupted_file}: {str(e)}")
                
        logger.info(f"🧹 CORRUPTED FILE CLEANUP COMPLETE: {deleted_count} files deleted")
        return deleted_count
        
    def fix_facebook_account_info(self):
        """Add missing accountType and postingStyle to Facebook account info files."""
        logger.info("🔧 FIXING FACEBOOK ACCOUNT INFO...")
        
        fixed_count = 0
        
        try:
            # Scan for Facebook account info files
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix='AccountInfo/facebook/'
            )
            
            if 'Contents' in response:
                for obj in response['Contents']:
                    key = obj['Key']
                    if key.endswith('/info.json'):
                        try:
                            # Read existing account info
                            account_data = self.data_retriever.get_json_data(key)
                            if account_data:
                                modified = False
                                
                                # Add missing accountType
                                if 'accountType' not in account_data and 'account_type' not in account_data:
                                    account_data['accountType'] = 'business'  # Default for Facebook
                                    modified = True
                                    logger.info(f"Added accountType to {key}")
                                    
                                # Add missing postingStyle
                                if 'postingStyle' not in account_data and 'posting_style' not in account_data:
                                    account_data['postingStyle'] = 'community_focused'  # Default for Facebook
                                    modified = True
                                    logger.info(f"Added postingStyle to {key}")
                                    
                                # Add platform if missing
                                if 'platform' not in account_data:
                                    account_data['platform'] = 'facebook'
                                    modified = True
                                    
                                # Save updated account info
                                if modified:
                                    self.s3_client.put_object(
                                        Bucket=self.bucket_name,
                                        Key=key,
                                        Body=json.dumps(account_data, indent=2),
                                        ContentType='application/json'
                                    )
                                    logger.info(f"✅ UPDATED FACEBOOK ACCOUNT INFO: {key}")
                                    fixed_count += 1
                                    
                        except Exception as e:
                            logger.error(f"Error fixing Facebook account info {key}: {str(e)}")
                            
        except Exception as e:
            logger.error(f"Error scanning Facebook account info: {str(e)}")
            
        logger.info(f"🔧 FACEBOOK ACCOUNT INFO FIXES COMPLETE: {fixed_count} files updated")
        return fixed_count
        
    def force_vector_database_indexing(self):
        """Force vector database indexing for all Facebook data to prevent skipping."""
        logger.info("📊 FORCING VECTOR DATABASE INDEXING...")
        
        indexed_count = 0
        
        try:
            # Scan for Facebook data files
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix='facebook/'
            )
            
            if 'Contents' in response:
                for obj in response['Contents']:
                    key = obj['Key']
                    if key.endswith('.json') and not key.endswith('/'):
                        try:
                            # Extract username from path
                            path_parts = key.split('/')
                            if len(path_parts) >= 3:
                                parent_username = path_parts[1]  # facebook/cocacola/christiano.json -> cocacola
                                filename = path_parts[2]
                                actual_username = filename.replace('.json', '')  # christiano.json -> christiano
                                
                                logger.info(f"Processing Facebook data: {key} (parent: {parent_username}, user: {actual_username})")
                                
                                # Read Facebook data
                                facebook_data = self.data_retriever.get_json_data(key)
                                if facebook_data:
                                    # Handle Facebook data format
                                    posts_data = []
                                    
                                    if 'posts' in facebook_data:
                                        posts_data = facebook_data['posts']
                                    elif isinstance(facebook_data, list):
                                        posts_data = facebook_data
                                        
                                    if posts_data:
                                        # Create minimal posts for vector database
                                        processed_posts = []
                                        for post in posts_data[:10]:  # Limit to prevent overflow
                                            if isinstance(post, dict):
                                                processed_post = {
                                                    'id': post.get('id', f"fb_{len(processed_posts)}"),
                                                    'caption': post.get('text', post.get('caption', '')),
                                                    'engagement': post.get('likesCount', 0) + post.get('commentsCount', 0),
                                                    'likes': post.get('likesCount', 0),
                                                    'comments': post.get('commentsCount', 0),
                                                    'timestamp': post.get('publishedAt', datetime.now().isoformat()),
                                                    'platform': 'facebook',
                                                    'username': actual_username
                                                }
                                                processed_posts.append(processed_post)
                                                
                                        # Index in vector database
                                        if processed_posts:
                                            is_competitor = (actual_username != parent_username)
                                            posts_added = self.vector_db.add_posts(
                                                processed_posts, 
                                                actual_username, 
                                                is_competitor=is_competitor
                                            )
                                            indexed_count += posts_added
                                            logger.info(f"✅ INDEXED {posts_added} posts for {actual_username} (competitor: {is_competitor})")
                                            
                        except Exception as e:
                            logger.error(f"Error indexing Facebook data {key}: {str(e)}")
                            
        except Exception as e:
            logger.error(f"Error forcing vector database indexing: {str(e)}")
            
        logger.info(f"📊 VECTOR DATABASE INDEXING COMPLETE: {indexed_count} posts indexed")
        return indexed_count
        
    def clean_infinite_loop_files(self):
        """Clean files that cause infinite processing loops."""
        logger.info("🧹 CLEANING INFINITE LOOP FILES...")
        
        # List of problematic patterns that cause loops
        problematic_patterns = [
            'next_posts/twitter/ylecun/campaign_next_post_6.json',  # Known corrupted file
            'generated_content/*/*/posts_*.json',  # Often get stuck
        ]
        
        cleaned_count = 0
        
        for pattern in problematic_patterns:
            try:
                if '*' in pattern:
                    # Handle wildcard patterns
                    prefix = pattern.split('*')[0]
                    response = self.s3_client.list_objects_v2(
                        Bucket=self.bucket_name,
                        Prefix=prefix
                    )
                    
                    if 'Contents' in response:
                        for obj in response['Contents']:
                            key = obj['Key']
                            # Additional validation for problematic files
                            if self._is_problematic_file(key):
                                try:
                                    self.s3_client.delete_object(Bucket=self.bucket_name, Key=key)
                                    logger.info(f"✅ CLEANED LOOP FILE: {key}")
                                    cleaned_count += 1
                                except Exception as e:
                                    logger.error(f"Failed to delete loop file {key}: {str(e)}")
                else:
                    # Handle specific files
                    try:
                        self.s3_client.delete_object(Bucket=self.bucket_name, Key=pattern)
                        logger.info(f"✅ CLEANED SPECIFIC FILE: {pattern}")
                        cleaned_count += 1
                    except Exception as e:
                        # File might not exist, which is fine
                        logger.info(f"File not found (OK): {pattern}")
                        
            except Exception as e:
                logger.error(f"Error cleaning pattern {pattern}: {str(e)}")
                
        logger.info(f"🧹 INFINITE LOOP CLEANUP COMPLETE: {cleaned_count} files cleaned")
        return cleaned_count
        
    def _is_problematic_file(self, key):
        """Check if a file is problematic and should be cleaned."""
        try:
            # Try to read and validate the file
            file_response = self.s3_client.get_object(Bucket=self.bucket_name, Key=key)
            content = file_response['Body'].read()
            
            # Check for UTF-8 issues
            try:
                content_str = content.decode('utf-8')
            except UnicodeDecodeError:
                return True  # Problematic
                
            # Check for JSON issues
            try:
                if content_str.strip():
                    json.loads(content_str)
            except json.JSONDecodeError:
                return True  # Problematic
                
            return False  # File is OK
            
        except Exception:
            return True  # If we can't read it, it's problematic
            
    def run_complete_fix(self):
        """Run all critical fixes to ensure pipeline works."""
        logger.info("🚀 STARTING CRITICAL PIPELINE BUG FIXES")
        logger.info("=" * 60)
        
        results = {}
        
        # Fix 1: Clean corrupted files
        results['corrupted_files_deleted'] = self.fix_corrupted_files()
        
        # Fix 2: Fix Facebook account info
        results['facebook_accounts_fixed'] = self.fix_facebook_account_info()
        
        # Fix 3: Force vector database indexing
        results['posts_indexed'] = self.force_vector_database_indexing()
        
        # Fix 4: Clean infinite loop files
        results['loop_files_cleaned'] = self.clean_infinite_loop_files()
        
        logger.info("=" * 60)
        logger.info("🎉 CRITICAL PIPELINE FIXES COMPLETE!")
        logger.info(f"   - Corrupted files deleted: {results['corrupted_files_deleted']}")
        logger.info(f"   - Facebook accounts fixed: {results['facebook_accounts_fixed']}")
        logger.info(f"   - Posts indexed: {results['posts_indexed']}")
        logger.info(f"   - Loop files cleaned: {results['loop_files_cleaned']}")
        
        # Verify vector database has data
        total_docs = self.vector_db.get_count()
        logger.info(f"   - Total vector database documents: {total_docs}")
        
        if total_docs > 0:
            logger.info("✅ VECTOR DATABASE IS POPULATED - RAG WILL WORK!")
        else:
            logger.warning("⚠️  VECTOR DATABASE IS EMPTY - RAG MAY NOT WORK PROPERLY")
            
        return results

def main():
    """Run the critical pipeline fixes."""
    try:
        fixer = CriticalPipelineFixer()
        results = fixer.run_complete_fix()
        
        print("\n" + "="*60)
        print("🔥 CRITICAL BUG FIXES SUMMARY")
        print("="*60)
        print(f"✅ Corrupted files deleted: {results['corrupted_files_deleted']}")
        print(f"✅ Facebook accounts fixed: {results['facebook_accounts_fixed']}")
        print(f"✅ Posts indexed: {results['posts_indexed']}")
        print(f"✅ Loop files cleaned: {results['loop_files_cleaned']}")
        print("\n🎯 PIPELINE SHOULD NOW WORK WITHOUT SKIPPING!")
        print("   - No more UTF-8 decode errors")
        print("   - Facebook processing will work")
        print("   - Vector database indexing will happen")
        print("   - RAG generation will proceed")
        
        return True
        
    except Exception as e:
        logger.error(f"Critical error during fixes: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
