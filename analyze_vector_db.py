#!/usr/bin/env python3
"""
Script to analyze vector database contents and identify RAG issues.
"""

from vector_database import VectorDatabaseManager

def analyze_vector_db():
    print("🔍 ANALYZING VECTOR DATABASE")
    print("=" * 50)
    
    try:
        vdb = VectorDatabaseManager()
        
        # Get total count
        total_docs = vdb.get_count()
        print(f"📊 Total documents in database: {total_docs}")
        
        if total_docs == 0:
            print("❌ DATABASE IS EMPTY - This explains why RAG is not working!")
            return
        
        # Get all documents
        all_docs = vdb.collection.get()
        
        # Analyze usernames
        usernames = set()
        engagements = {}
        
        for metadata in all_docs['metadatas']:
            if metadata and 'username' in metadata:
                username = metadata['username']
                usernames.add(username)
                
                if username not in engagements:
                    engagements[username] = []
                engagements[username].append(metadata.get('engagement', 0))
        
        print(f"👥 Usernames indexed: {sorted(usernames)}")
        print()
        
        # Show detailed breakdown per user
        for username in sorted(usernames):
            user_docs = vdb.collection.get(where={'username': username})
            doc_count = len(user_docs['ids'])
            avg_engagement = sum(engagements[username]) / len(engagements[username]) if engagements[username] else 0
            
            print(f"📄 {username}:")
            print(f"   - Documents: {doc_count}")
            print(f"   - Avg Engagement: {avg_engagement:.1f}")
            
            # Show sample content
            if user_docs['documents'] and len(user_docs['documents']) > 0:
                sample_doc = user_docs['documents'][0][:100] + "..." if len(user_docs['documents'][0]) > 100 else user_docs['documents'][0]
                print(f"   - Sample: {sample_doc}")
            print()
        
        # Check for missing competitors
        expected_competitors = ['narsissist', 'fentybeauty', 'toofaced']
        missing_competitors = [comp for comp in expected_competitors if comp not in usernames]
        
        if missing_competitors:
            print("❌ MISSING COMPETITORS:")
            for comp in missing_competitors:
                print(f"   - {comp}: No data indexed")
            print()
            print("💡 SOLUTION: Need to scrape and index competitor data first!")
        
        print("🔍 TESTING RAG QUERIES:")
        print("-" * 30)
        
        # Test query for existing user
        if 'maccosmetics' in usernames:
            results = vdb.query_similar("maccosmetics content strategy", n_results=3, filter_username='maccosmetics')
            print(f"✅ maccosmetics query: Found {len(results['documents'][0])} results")
        
        # Test query for missing competitor
        if 'narsissist' in missing_competitors:
            results = vdb.query_similar("narsissist competitive analysis", n_results=3, filter_username='narsissist')
            print(f"❌ narsissist query: Found {len(results['documents'][0])} results (should be 0)")
        
    except Exception as e:
        print(f"❌ Error analyzing vector database: {e}")

if __name__ == "__main__":
    analyze_vector_db() 