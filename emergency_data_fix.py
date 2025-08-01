#!/usr/bin/env python3
"""
EMERGENCY DATA MIGRATION & POPULATION SCRIPT
Fixes schema locations and populates vector database immediately
"""

import sys
import logging
from main import ContentRecommendationSystem

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def emergency_data_fix():
    """Execute emergency data migration and vector database population"""
    print("🚨 EMERGENCY DATA MIGRATION & POPULATION")
    print("=" * 60)
    
    try:
        # Initialize the system
        system = ContentRecommendationSystem()
        logger.info("✅ System initialized successfully")
        
        # Step 1: Data Migration for Wrong Schema Locations
        print("\n🔄 STEP 1: DATA MIGRATION TO CORRECT SCHEMA")
        print("-" * 50)
        
        migration_tasks = [
            {
                "source": "twitter/elonmusk/elonmusk.json",
                "target": "twitter/geoffreyhinton/elonmusk.json",
                "description": "elonmusk competitor data for geoffreyhinton"
            },
            {
                "source": "facebook/redbull/redbull.json", 
                "target": "facebook/netflix/redbull.json",
                "description": "redbull competitor data for netflix"
            }
        ]
        
        migrations_completed = 0
        for task in migration_tasks:
            try:
                # Get source data
                source_data = system.data_retriever.get_json_data(task["source"])
                if source_data:
                    # Upload to correct location
                    system.r2_storage.upload_json(task["target"], source_data)
                    print(f"✅ Migrated {task['description']}: {task['source']} → {task['target']}")
                    migrations_completed += 1
                else:
                    print(f"❌ Source data not found: {task['source']}")
            except Exception as e:
                print(f"❌ Migration failed for {task['description']}: {str(e)[:50]}")
        
        print(f"📊 Migrations completed: {migrations_completed}/{len(migration_tasks)}")
        
        # Step 2: Emergency Vector Database Population
        print("\n🔄 STEP 2: EMERGENCY VECTOR DATABASE POPULATION")
        print("-" * 50)
        
        # All test cases with corrected data
        population_cases = [
            ("twitter", "geoffreyhinton", ["elonmusk", "ylecun", "sama"]),
            ("instagram", "maccosmetics", ["fentybeauty", "narsissist", "toofaced"]),
            ("facebook", "netflix", ["cocacola", "redbull", "nike"])
        ]
        
        total_indexed = 0
        total_competitors_indexed = 0
        
        for platform, primary_user, competitors in population_cases:
            print(f"\n📊 Populating {platform.upper()}: {primary_user}")
            
            # Index primary user data
            try:
                primary_data = system.data_retriever.get_json_data(f"{platform}/{primary_user}/{primary_user}.json")
                if primary_data:
                    posts = primary_data if isinstance(primary_data, list) else primary_data.get('posts', [])
                    if posts:
                        system.vector_db.add_posts(posts, primary_user, is_competitor=False)
                        print(f"  ✅ Indexed PRIMARY {primary_user}: {len(posts)} posts")
                        total_indexed += len(posts)
                    else:
                        print(f"  ⚠️ PRIMARY {primary_user}: No posts found")
                else:
                    print(f"  ❌ PRIMARY {primary_user}: No data found")
            except Exception as e:
                print(f"  ❌ PRIMARY {primary_user}: Error - {str(e)[:50]}")
            
            # Index competitor data
            for competitor in competitors:
                try:
                    competitor_data = system.data_retriever.get_json_data(f"{platform}/{primary_user}/{competitor}.json")
                    if competitor_data:
                        posts = competitor_data if isinstance(competitor_data, list) else competitor_data.get('posts', [])
                        if posts:
                            system.vector_db.add_posts(posts, competitor, is_competitor=True)
                            print(f"    ✅ Indexed COMPETITOR {competitor}: {len(posts)} posts")
                            total_indexed += len(posts)
                            total_competitors_indexed += len(posts)
                        else:
                            print(f"    ⚠️ COMPETITOR {competitor}: No posts found")
                    else:
                        print(f"    ❌ COMPETITOR {competitor}: No data found")
                except Exception as e:
                    print(f"    ❌ COMPETITOR {competitor}: Error - {str(e)[:50]}")
        
        # Step 3: Verification
        print(f"\n🔍 STEP 3: VECTOR DATABASE VERIFICATION")
        print("-" * 50)
        
        try:
            # Check final database state
            count = system.vector_db.collection.count()
            print(f"Total documents indexed: {count}")
            
            if count > 0:
                # Get sample data to verify
                sample = system.vector_db.collection.get(limit=20)
                usernames = set()
                competitor_count = 0
                
                for metadata in sample['metadatas']:
                    if 'username' in metadata:
                        usernames.add(metadata['username'])
                    if metadata.get('is_competitor'):
                        competitor_count += 1
                
                print(f"Unique usernames: {sorted(list(usernames))}")
                print(f"Competitor documents: {competitor_count}")
                print(f"Non-competitor documents: {len(sample['metadatas']) - competitor_count}")
                
                # Test competitor retrieval
                print(f"\n🧪 Testing competitor retrieval:")
                test_competitors = ["elonmusk", "ylecun", "sama", "fentybeauty", "narsissist"]
                for competitor in test_competitors[:3]:  # Test first 3
                    try:
                        results = system.vector_db.query_similar(
                            f"{competitor} competitive analysis",
                            n_results=5,
                            filter_username=competitor,
                            is_competitor=True
                        )
                        doc_count = len(results.get('documents', [[]])[0]) if results else 0
                        print(f"  {competitor}: {doc_count} documents retrievable")
                    except Exception as e:
                        print(f"  {competitor}: Query failed - {str(e)[:30]}")
                
        except Exception as e:
            print(f"❌ Verification failed: {str(e)}")
        
        # Final Summary
        print(f"\n🎯 EMERGENCY FIX SUMMARY")
        print("=" * 40)
        print(f"Data migrations completed: {migrations_completed}")
        print(f"Total documents indexed: {total_indexed}")
        print(f"Competitor documents indexed: {total_competitors_indexed}")
        print(f"Vector database populated: {'✅ YES' if count > 0 else '❌ NO'}")
        
        if count > 0 and total_competitors_indexed > 0:
            print("\n🚀 SUCCESS: Emergency fix completed!")
            print("✅ Vector database is populated with competitor data")
            print("✅ RAG functionality should now work correctly")
            print("\nNEXT ACTION: Run comprehensive vulnerability test to verify fixes")
        else:
            print("\n❌ FAILURE: Emergency fix incomplete")
            print("❌ Vector database still not properly populated")
            print("\nNEXT ACTION: Debug data indexing process")
    
    except Exception as e:
        logger.error(f"❌ Emergency fix failed: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    emergency_data_fix()
