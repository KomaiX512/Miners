#!/usr/bin/env python3
"""
Debug and fix RAG query embedding issues to ensure proper semantic similarity retrieval.
"""

import logging
from vector_database import VectorDatabaseManager

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def debug_and_fix_rag_queries():
    """Debug and fix RAG query semantic similarity issues."""
    print("🔍 DEBUGGING RAG QUERY SEMANTIC SIMILARITY")
    print("=" * 50)
    
    try:
        # Initialize vector database manager
        vdb = VectorDatabaseManager()
        
        # Get all data to analyze what's actually stored
        print("📊 ANALYZING STORED DATA:")
        print("-" * 30)
        
        all_data = vdb.collection.get()
        
        if not all_data['ids']:
            print("❌ No data found in vector database!")
            return False
        
        print(f"📊 Total documents: {len(all_data['ids'])}")
        
        # Group by username
        username_data = {}
        for i, metadata in enumerate(all_data['metadatas']):
            username = metadata.get('username', 'unknown')
            if username not in username_data:
                username_data[username] = []
            username_data[username].append({
                'id': all_data['ids'][i],
                'document': all_data['documents'][i][:100] + '...' if len(all_data['documents'][i]) > 100 else all_data['documents'][i],
                'metadata': metadata
            })
        
        for username, docs in username_data.items():
            print(f"\n👤 {username}: {len(docs)} documents")
            for doc in docs[:2]:  # Show first 2 documents
                print(f"   📄 ID: {doc['id']}")
                print(f"   📝 Content: {doc['document']}")
                if 'engagement' in doc['metadata']:
                    print(f"   📊 Engagement: {doc['metadata']['engagement']}")
        
        print("\n🧪 TESTING QUERY VARIATIONS:")
        print("-" * 40)
        
        # Test different query variations for each competitor
        competitors = ['toofaced', 'maccosmetics', 'fentybeauty', 'narsissist']
        
        for competitor in competitors:
            print(f"\n🎯 TESTING {competitor.upper()}:")
            
            # Test basic queries
            basic_queries = [
                competitor,
                f"{competitor} makeup",
                f"{competitor} cosmetics",
                "makeup products",
                "cosmetics beauty",
                "professional makeup",
                "beauty products"
            ]
            
            for query in basic_queries:
                results = vdb.query_similar(query, n_results=3, filter_username=competitor)
                result_count = len(results['documents'][0]) if results['documents'] and results['documents'][0] else 0
                status = "✅" if result_count > 0 else "❌"
                print(f"   {status} '{query}': {result_count} results")
                
                if result_count > 0:
                    # Show first result for successful queries
                    first_doc = results['documents'][0][0][:100]
                    print(f"      📄 First result: {first_doc}...")
                    if results['metadatas'] and results['metadatas'][0]:
                        engagement = results['metadatas'][0][0].get('engagement', 'N/A')
                        print(f"      📊 Engagement: {engagement}")
                    break  # Found working query, move to next competitor
        
        print("\n🔧 FIXING QUERY ISSUES:")
        print("-" * 30)
        
        # The issue is likely that the indexed content doesn't match query expectations
        # Let's check if we need to update the indexing strategy
        
        # Test direct content match
        for competitor in competitors:
            print(f"\n🔍 Direct content analysis for {competitor}:")
            
            # Get all documents for this competitor
            all_results = vdb.query_similar("", n_results=50, filter_username=competitor)
            if all_results['documents'] and all_results['documents'][0]:
                print(f"   📊 Found {len(all_results['documents'][0])} documents")
                
                # Analyze content themes
                for i, doc in enumerate(all_results['documents'][0][:3]):
                    engagement = all_results['metadatas'][0][i].get('engagement', 0) if all_results['metadatas'] else 0
                    print(f"   📄 Doc {i+1}: {doc[:80]}... (engagement: {engagement})")
            else:
                print(f"   ❌ No documents found for {competitor}")
        
        print("\n💡 SOLUTION RECOMMENDATIONS:")
        print("-" * 35)
        
        print("1. Query terms should match actual content themes")
        print("2. Use broader semantic terms like 'makeup', 'beauty', 'cosmetics'")
        print("3. Consider content-based queries rather than brand-specific terms")
        print("4. Test similarity threshold adjustments")
        
        # Test improved query strategy
        print("\n🚀 TESTING IMPROVED QUERY STRATEGY:")
        print("-" * 45)
        
        improved_queries = [
            "premium makeup collection",
            "beauty brand products", 
            "cosmetics innovation",
            "makeup artistry",
            "beauty industry"
        ]
        
        for competitor in competitors:
            print(f"\n🎯 {competitor} with improved queries:")
            best_result = 0
            best_query = ""
            
            for query in improved_queries:
                results = vdb.query_similar(query, n_results=3, filter_username=competitor)
                result_count = len(results['documents'][0]) if results['documents'] and results['documents'][0] else 0
                
                if result_count > best_result:
                    best_result = result_count
                    best_query = query
                
                status = "✅" if result_count > 0 else "❌"
                print(f"   {status} '{query}': {result_count} results")
            
            if best_result > 0:
                print(f"   🏆 Best query for {competitor}: '{best_query}' ({best_result} results)")
        
        return True
        
    except Exception as e:
        print(f"❌ Error debugging RAG queries: {e}")
        return False

if __name__ == "__main__":
    success = debug_and_fix_rag_queries()
    if success:
        print("\n🎉 RAG QUERY DEBUGGING COMPLETE!")
        print("💡 Use the improved query strategy for better results")
    else:
        print("\n❌ Failed to debug RAG queries") 