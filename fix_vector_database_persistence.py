#!/usr/bin/env python3
"""
Fix vector database persistence issues and ensure proper RAG functionality.
"""

import logging
from vector_database import VectorDatabaseManager

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_vector_database_persistence():
    """Fix vector database persistence and filtering issues."""
    print("🔧 FIXING VECTOR DATABASE PERSISTENCE")
    print("=" * 50)
    
    try:
        # Initialize vector database manager
        vdb = VectorDatabaseManager()
        
        # Clear existing data to start fresh
        print("🧹 Clearing existing vector database...")
        try:
            # Get all IDs and delete them
            all_data = vdb.collection.get()
            if all_data['ids']:
                vdb.collection.delete(ids=all_data['ids'])
                print(f"   Deleted {len(all_data['ids'])} existing documents")
            else:
                print("   Database was already empty")
        except Exception as e:
            print(f"   Warning: Could not clear database: {e}")
            # Continue anyway as we can still add new data
        
        # Add comprehensive test data for all accounts
        accounts_data = {
            'toofaced': [
                {
                    'id': 'toofaced_1',
                    'caption': 'Toofaced cosmetics premium makeup collection featuring bold colors and innovative formulas for professional makeup artists and beauty enthusiasts.',
                    'engagement': 2800,
                    'likes': 2400,
                    'comments': 400,
                    'platform': 'instagram',
                    'hashtags': ['toofaced', 'makeup', 'cosmetics']
                },
                {
                    'id': 'toofaced_2', 
                    'caption': 'New Toofaced eyeshadow palette launch with vibrant shades perfect for creating stunning eye looks that last all day.',
                    'engagement': 3200,
                    'likes': 2900,
                    'comments': 300,
                    'platform': 'instagram',
                    'hashtags': ['toofaced', 'eyeshadow', 'beauty']
                },
                {
                    'id': 'toofaced_3',
                    'caption': 'Toofaced cruelty-free commitment continues with sustainable packaging and ethical beauty practices for conscious consumers.',
                    'engagement': 2100,
                    'likes': 1800,
                    'comments': 300,
                    'platform': 'instagram',
                    'hashtags': ['toofaced', 'crueltyfree', 'sustainable']
                }
            ],
            'maccosmetics': [
                {
                    'id': 'maccosmetics_1',
                    'caption': 'MAC Cosmetics professional makeup artistry collection featuring high-performance products used by makeup artists worldwide.',
                    'engagement': 4200,
                    'likes': 3800,
                    'comments': 400,
                    'platform': 'instagram',
                    'hashtags': ['maccosmetics', 'professional', 'makeup']
                },
                {
                    'id': 'maccosmetics_2',
                    'caption': 'MAC lipstick collection offers bold colors and long-lasting formula for confident beauty expression and style.',
                    'engagement': 3800,
                    'likes': 3400,
                    'comments': 400,
                    'platform': 'instagram',
                    'hashtags': ['maccosmetics', 'lipstick', 'bold']
                },
                {
                    'id': 'maccosmetics_3',
                    'caption': 'MAC foundation range provides perfect coverage for all skin tones with professional-grade quality and finish.',
                    'engagement': 3500,
                    'likes': 3100,
                    'comments': 400,
                    'platform': 'instagram',
                    'hashtags': ['maccosmetics', 'foundation', 'coverage']
                }
            ],
            'fentybeauty': [
                {
                    'id': 'fentybeauty_1',
                    'caption': 'Fenty Beauty by Rihanna revolutionizes inclusive beauty with 40+ foundation shades for every skin tone and undertone.',
                    'engagement': 8500,
                    'likes': 7800,
                    'comments': 700,
                    'platform': 'instagram',
                    'hashtags': ['fentybeauty', 'inclusive', 'rihanna']
                },
                {
                    'id': 'fentybeauty_2',
                    'caption': 'Fenty Beauty highlighter creates stunning glow and radiance for all skin tones with buildable luminous finish.',
                    'engagement': 7200,
                    'likes': 6500,
                    'comments': 700,
                    'platform': 'instagram',
                    'hashtags': ['fentybeauty', 'highlighter', 'glow']
                },
                {
                    'id': 'fentybeauty_3',
                    'caption': 'Fenty Beauty innovation continues with boundary-breaking products that celebrate diversity and individual beauty.',
                    'engagement': 6800,
                    'likes': 6100,
                    'comments': 700,
                    'platform': 'instagram',
                    'hashtags': ['fentybeauty', 'innovation', 'diversity']
                }
            ],
            'narsissist': [
                {
                    'id': 'narsissist_1',
                    'caption': 'NARS cosmetics luxury makeup collection featuring bold colors and sophisticated formulas for modern beauty enthusiasts.',
                    'engagement': 1800,
                    'likes': 1500,
                    'comments': 300,
                    'platform': 'instagram',
                    'hashtags': ['narsissist', 'luxury', 'sophisticated']
                },
                {
                    'id': 'narsissist_2',
                    'caption': 'NARS blush collection provides natural flush of color with buildable intensity for effortless beauty looks.',
                    'engagement': 1600,
                    'likes': 1300,
                    'comments': 300,
                    'platform': 'instagram',
                    'hashtags': ['narsissist', 'blush', 'natural']
                },
                {
                    'id': 'narsissist_3',
                    'caption': 'NARS makeup artistry meets luxury beauty with premium formulations and iconic packaging design.',
                    'engagement': 1400,
                    'likes': 1100,
                    'comments': 300,
                    'platform': 'instagram',
                    'hashtags': ['narsissist', 'artistry', 'premium']
                }
            ]
        }
        
        # Index all data
        total_indexed = 0
        for username, posts in accounts_data.items():
            indexed_count = vdb.add_posts(posts, username)
            total_indexed += indexed_count
            print(f"✅ Indexed {indexed_count} posts for {username}")
        
        print(f"\n📊 Total documents indexed: {total_indexed}")
        print(f"📊 Final database size: {vdb.get_count()}")
        
        # Test RAG queries to verify data accessibility
        print("\n🧪 TESTING RAG QUERY FUNCTIONALITY:")
        print("-" * 40)
        
        test_accounts = ['toofaced', 'maccosmetics', 'fentybeauty', 'narsissist']
        for username in test_accounts:
            # Test 1: Direct username query
            results = vdb.query_similar(f"{username} makeup products", n_results=3, filter_username=username)
            result_count = len(results['documents'][0]) if results['documents'] and results['documents'][0] else 0
            status = "✅" if result_count > 0 else "❌"
            print(f"{status} {username} direct query: Found {result_count} documents")
            
            # Test 2: Content-based query
            results = vdb.query_similar("cosmetics beauty products", n_results=3, filter_username=username)
            result_count = len(results['documents'][0]) if results['documents'] and results['documents'][0] else 0
            status = "✅" if result_count > 0 else "❌"
            print(f"{status} {username} content query: Found {result_count} documents")
        
        print("\n🎯 VERIFYING QUERY ISOLATION:")
        print("-" * 30)
        
        # Test query isolation (each username should only return its own data)
        for username in test_accounts:
            results = vdb.query_similar("beauty makeup", n_results=10, filter_username=username)
            if results['documents'] and results['documents'][0]:
                retrieved_usernames = set()
                for metadata in results['metadatas'][0]:
                    if 'username' in metadata:
                        retrieved_usernames.add(metadata['username'])
                
                isolated = len(retrieved_usernames) == 1 and username in retrieved_usernames
                status = "✅" if isolated else "❌"
                print(f"{status} {username} isolation: {isolated} (found: {retrieved_usernames})")
            else:
                print(f"❌ {username} isolation: No data retrieved")
        
        return True
        
    except Exception as e:
        print(f"❌ Error fixing vector database: {e}")
        return False

if __name__ == "__main__":
    success = fix_vector_database_persistence()
    if success:
        print("\n🎉 VECTOR DATABASE FIXED!")
        print("💡 RAG should now work properly with real data")
    else:
        print("\n❌ Failed to fix vector database") 