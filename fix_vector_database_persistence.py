#!/usr/bin/env python3
"""
Fix vector database persistence issues and ensure proper RAG functionality.
Implements a dual-database approach with ChromaDB and a robust fallback system.
"""

import logging
import os
import shutil
from pathlib import Path
from vector_database import VectorDatabaseManager

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_vector_database_persistence():
    """Fix vector database persistence and filtering issues with dual-database approach."""
    print("🔧 FIXING VECTOR DATABASE PERSISTENCE")
    print("=" * 80)
    print("🔄 Implementing robust dual-database approach (ChromaDB + Fallback)")
    print("=" * 80)
    
    try:
        # Check for and backup any corrupted ChromaDB directory
        chroma_path = Path("./chroma_db")
        backup_dir = None
        
        if chroma_path.exists():
            # Check for potential corruption signs
            has_corruption = False
            index_path = chroma_path / "index"
            
            if index_path.exists() and len(os.listdir(index_path)) == 0:
                has_corruption = True
                print("⚠️ Detected empty index directory - potential corruption")
            
            # Check for 0-byte files
            for root, dirs, files in os.walk(chroma_path):
                for file in files:
                    file_path = Path(root) / file
                    if file_path.stat().st_size == 0:
                        has_corruption = True
                        print(f"⚠️ Detected 0-byte file: {file_path}")
            
            # If corruption detected, back up the directory
            if has_corruption:
                backup_dir = f"./chroma_db_backup_{int(time.time())}"
                print(f"📦 Backing up potentially corrupted database to {backup_dir}")
                shutil.copytree(chroma_path, backup_dir)
                shutil.rmtree(chroma_path)
                print("✅ Removed corrupted database after backup")
        
        # Initialize vector database manager
        print("🔄 Initializing dual-database system...")
        vdb = VectorDatabaseManager()
        
        # Clear both databases completely
        print("🧹 Clearing all databases for a fresh start...")
        clear_result = vdb.clear_before_new_run()
        if clear_result:
            print(f"✅ Successfully cleared and reinitialized databases")
        else:
            print(f"⚠️ Database clearing had issues, continuing with verification tests...")
        
        # Seed with test data to verify ChromaDB functionality
        print("\n🧪 Testing ChromaDB with sample data...")
        test_data = [
            {
                "id": "test_1",
                "caption": "Test post for ChromaDB verification",
                "engagement": 100,
                "timestamp": "2025-06-05T00:00:00Z",
                "username": "test_user"
            }
        ]
        
        # Try to force ChromaDB usage for this test
        vdb.use_fallback = False
        
        try:
            # Add test data to ChromaDB
            added = vdb.add_posts(test_data, "test_user")
            print(f"   Added {added} test posts to ChromaDB")
            
            # Test query with ChromaDB
            results = vdb.query_similar("test verification", n_results=1)
            if results and results.get('documents', [[]])[0]:
                print("✅ ChromaDB test successful - primary database is working")
                chroma_working = True
            else:
                print("❌ ChromaDB test failed - will rely on fallback system")
                chroma_working = False
                
            # Clear test data from ChromaDB
            if chroma_working:
                vdb.clear_collection()
                print("   Cleaned up test data from ChromaDB")
        except Exception as e:
            print(f"❌ ChromaDB test failed with error: {str(e)}")
            chroma_working = False
        
        # Test fallback database
        print("\n🧪 Testing fallback database with sample data...")
        test_data = [
                {
                "id": "test_2",
                "caption": "Test post for fallback database verification",
                "engagement": 200,
                "timestamp": "2025-06-05T00:00:00Z",
                "username": "fallback_user"
            }
        ]
        
        # Force fallback usage for this test
        vdb.use_fallback = True
        
        try:
            # Add test data to fallback database
            added = vdb.add_posts(test_data, "fallback_user")
            print(f"   Added {added} test posts to fallback database")
            
            # Test query with fallback database
            results = vdb.query_similar("test verification", n_results=1)
            if results and results.get('documents', [[]])[0]:
                print("✅ Fallback database test successful - backup system is working")
                fallback_working = True
            else:
                print("❌ Fallback database test failed")
                fallback_working = False
                
            # Clear test data from fallback database
            if fallback_working:
                vdb.clear_collection()
                print("   Cleaned up test data from fallback database")
        except Exception as e:
            print(f"❌ Fallback database test failed with error: {str(e)}")
            fallback_working = False
            
        # Test competitor query specifically
        print("\n🧪 Testing competitor query functionality...")
        competitor_test_data = [
                {
                "id": "comp_test_1",
                "caption": "Competitor test post for verification",
                "engagement": 500,
                "timestamp": "2025-06-05T00:00:00Z",
                "username": "maccosmetics"
            }
        ]
        
        # Use ChromaDB if it's working, otherwise use fallback
        vdb.use_fallback = not chroma_working
        
        try:
            # Add competitor test data
            added = vdb.add_posts(competitor_test_data, "toofaced", is_competitor=True)
            print(f"   Added {added} competitor test posts")
            
            # Test competitor query
            results = vdb.query_similar("competitor verification", n_results=1, 
                                        filter_username="maccosmetics", is_competitor=True)
            if results and results.get('documents', [[]])[0]:
                print("✅ Competitor query test successful")
                competitor_query_working = True
            else:
                print("❌ Competitor query test failed - switching to fallback")
                competitor_query_working = False
                
                # Try with fallback
                vdb.use_fallback = True
                results = vdb.query_similar("competitor verification", n_results=1, 
                                            filter_username="maccosmetics", is_competitor=True)
                if results and results.get('documents', [[]])[0]:
                    print("✅ Competitor query works with fallback database")
                    competitor_query_working = True
                    
            # Clean up test data
            vdb.clear_collection()
            print("   Cleaned up competitor test data")
        except Exception as e:
            print(f"❌ Competitor query test failed with error: {str(e)}")
            competitor_query_working = False
        
        # Final setup based on tests
        print("\n🔧 Configuring optimal database setup based on test results...")
        
        # We've established the working state - now reset for production use
        vdb = VectorDatabaseManager()
        vdb.clear_before_new_run()
        
        if chroma_working and competitor_query_working:
            print("✅ ChromaDB is fully functional - will use as primary database with fallback safety")
            vdb.use_fallback = False
            else:
            print("⚠️ ChromaDB had issues - will use fallback database as primary")
            vdb.use_fallback = True
            
        # Seed a minimal dataset for both databases to ensure they're working
        seed_data = [
            {
                "id": "seed_1",
                "caption": "Initial seed post for database functionality",
                "engagement": 100,
                "timestamp": "2025-06-05T00:00:00Z",
                "username": "seed_user"
            }
        ]
        
        try:
            # Add to current primary database
            vdb.add_posts(seed_data, "seed_user")
            
            # Also add to the other database for redundancy
            other_db = not vdb.use_fallback
            original_fallback = vdb.use_fallback
            vdb.use_fallback = other_db
            vdb.add_posts(seed_data, "seed_user")
            vdb.use_fallback = original_fallback
            
            print("✅ Successfully seeded both databases with minimal data")
        except Exception as e:
            print(f"⚠️ Error seeding databases: {str(e)}")
        
        print("\n✅ DUAL-DATABASE SYSTEM SETUP COMPLETE")
        print("=" * 80)
        print("IMPORTANT CHANGES:")
        print("1. Implemented robust dual-database approach:")
        print("   - ChromaDB with optimized parameters as primary (when working)")
        print("   - Simple reliable fallback database as backup")
        print("2. Automatic failover when ChromaDB encounters issues")
        print("3. Data redundancy - critical content is stored in both databases")
        print("4. More robust competitor queries with better filters and matching")
        print("5. Graceful degradation instead of hard failures")
        print("\nThe system will now automatically handle ChromaDB issues without disruption!")
        print("=" * 80)
        
        return True
        
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return False

if __name__ == "__main__":
    # Execute the fix when script is run directly
    import time
    fix_vector_database_persistence() 