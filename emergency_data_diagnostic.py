#!/usr/bin/env python3
"""
EMERGENCY DATA DIAGNOSTIC
Investigates the critical competitor data availability issue
"""

import sys
import logging
from main import ContentRecommendationSystem

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def diagnose_data_pipeline():
    """Emergency diagnostic of data pipeline and competitor data availability"""
    print("🚨 EMERGENCY DATA DIAGNOSTIC")
    print("=" * 60)
    
    try:
        # Initialize the system
        system = ContentRecommendationSystem()
        logger.info("✅ System initialized successfully")
        
        # Test cases from vulnerability report - CORRECTED INSTAGRAM MAPPING
        test_cases = [
            ("twitter", "geoffreyhinton", ["elonmusk", "ylecun", "sama"]),
            ("instagram", "maccosmetics", ["fentybeauty", "narsissist", "toofaced"]),  # CORRECTED
            ("facebook", "netflix", ["cocacola", "redbull", "nike"])
        ]
        
        total_competitors_found = 0
        total_competitors_expected = 0
        
        for platform, primary_user, competitors in test_cases:
            print(f"\n🔍 TESTING {platform.upper()}: {primary_user}")
            print("-" * 40)
            
            total_competitors_expected += len(competitors)
            
            # Test primary user data first
            try:
                primary_data = system.data_retriever.get_json_data(f"{platform}/{primary_user}/{primary_user}.json")
                if primary_data:
                    posts_count = len(primary_data) if isinstance(primary_data, list) else len(primary_data.get('posts', []))
                    print(f"✅ PRIMARY USER {primary_user}: {posts_count} posts")
                else:
                    print(f"❌ PRIMARY USER {primary_user}: No data found")
            except Exception as e:
                print(f"❌ PRIMARY USER {primary_user}: Error - {str(e)[:50]}")
            
            # Test competitor data
            competitors_found_for_platform = 0
            for competitor in competitors:
                try:
                    # Test the correct schema path first
                    competitor_path = f"{platform}/{primary_user}/{competitor}.json"
                    competitor_data = system.data_retriever.get_json_data(competitor_path)
                    
                    if competitor_data:
                        posts_count = len(competitor_data) if isinstance(competitor_data, list) else len(competitor_data.get('posts', []))
                        print(f"  ✅ {competitor}: {posts_count} posts ({competitor_path})")
                        competitors_found_for_platform += 1
                        total_competitors_found += 1
                    else:
                        # Try alternative paths
                        alt_paths = [
                            f"{platform}/{competitor}/{competitor}.json",
                            f"{platform}/{competitor}.json",
                            f"ProfileInfo/{platform}/{competitor}.json"
                        ]
                        
                        found_alternative = False
                        for alt_path in alt_paths:
                            try:
                                alt_data = system.data_retriever.get_json_data(alt_path)
                                if alt_data:
                                    posts_count = len(alt_data) if isinstance(alt_data, list) else len(alt_data.get('posts', []))
                                    print(f"  ⚠️ {competitor}: {posts_count} posts (WRONG SCHEMA: {alt_path})")
                                    found_alternative = True
                                    break
                            except:
                                continue
                        
                        if not found_alternative:
                            print(f"  ❌ {competitor}: No data found anywhere")
                
                except Exception as e:
                    print(f"  ❌ {competitor}: Error - {str(e)[:50]}")
            
            print(f"📊 Platform {platform}: {competitors_found_for_platform}/{len(competitors)} competitors found")
        
        # Summary
        print(f"\n📈 OVERALL SUMMARY")
        print("=" * 40)
        print(f"Total competitors expected: {total_competitors_expected}")
        print(f"Total competitors found: {total_competitors_found}")
        print(f"Data availability: {(total_competitors_found/total_competitors_expected)*100:.1f}%")
        
        if total_competitors_found == 0:
            print("\n🚨 CRITICAL: NO COMPETITOR DATA FOUND")
            print("ROOT CAUSE: Data collection pipeline has not populated competitor data")
            print("NEXT ACTION: Run data collection process to scrape and store competitor data")
        elif total_competitors_found < total_competitors_expected:
            print(f"\n⚠️ PARTIAL DATA LOSS: Missing {total_competitors_expected - total_competitors_found} competitors")
            print("ROOT CAUSE: Incomplete data collection or data corruption")
            print("NEXT ACTION: Re-run data collection for missing competitors")
        else:
            print("\n✅ ALL COMPETITOR DATA AVAILABLE")
            print("ROOT CAUSE: Data exists but vector database indexing issue")
            print("NEXT ACTION: Force re-index vector database with competitor data")
        
        # Test vector database state
        print(f"\n🔍 VECTOR DATABASE DIAGNOSTIC")
        print("-" * 40)
        
        try:
            # Check vector database content
            count = system.vector_db.collection.count()
            print(f"Total documents in vector DB: {count}")
            
            if count > 0:
                # Get sample data to check usernames
                sample = system.vector_db.collection.get(limit=50)
                usernames = set()
                competitor_count = 0
                
                for metadata in sample['metadatas']:
                    if 'username' in metadata:
                        usernames.add(metadata['username'])
                    if metadata.get('is_competitor'):
                        competitor_count += 1
                
                print(f"Unique usernames in DB: {sorted(list(usernames))}")
                print(f"Competitor documents: {competitor_count}")
                print(f"Non-competitor documents: {len(sample['metadatas']) - competitor_count}")
                
                if competitor_count == 0:
                    print("🚨 CRITICAL: Vector DB has no competitor documents")
                    print("SOLUTION: Re-run data indexing with competitor flag properly set")
        except Exception as e:
            print(f"❌ Vector DB diagnostic failed: {str(e)}")
    
    except Exception as e:
        logger.error(f"❌ Emergency diagnostic failed: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    diagnose_data_pipeline()
