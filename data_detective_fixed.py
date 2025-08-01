#!/usr/bin/env python3

"""
Data Structure Detective: Find Competitor Data (Fixed)
======================================================

Quick investigation to find where competitor data is actually stored
and fix the path structure issue that's preventing quality analysis.
"""

import sys
import json
import os

def find_competitor_data():
    """Find where competitor data is actually stored."""
    
    print("🔍 DETECTING COMPETITOR DATA STORAGE STRUCTURE")
    print("=" * 50)
    
    try:
        sys.path.append('/home/komail/Miners-1')
        from data_retrieval import R2DataRetriever
        
        # Create retriever
        retriever = R2DataRetriever()
        
        # Get all objects from R2
        print("📁 Listing R2 objects...")
        objects = retriever.list_objects(prefix='')
        print(f"Total objects found: {len(objects)}")
        
        # Convert to simple list of keys
        object_keys = [obj['Key'] if isinstance(obj, dict) else str(obj) for obj in objects]
        
        # Search for competitor data patterns
        competitors = ['nike', 'redbull', 'netflix']
        
        print("\n🎯 COMPETITOR DATA SEARCH:")
        for competitor in competitors:
            print(f"\n--- {competitor.upper()} ---")
            
            # Find all objects containing this competitor name
            comp_objects = [obj for obj in object_keys if competitor in obj.lower()]
            
            if comp_objects:
                print(f"✅ Found {len(comp_objects)} objects with '{competitor}':")
                for obj in comp_objects[:5]:  # Show first 5
                    print(f"  📄 {obj}")
                    
                    # Try to get the data to see if it's valid
                    try:
                        data = retriever.get_json_data(obj)
                        if data:
                            if isinstance(data, list):
                                print(f"    ✅ Valid data: {len(data)} posts")
                            elif isinstance(data, dict):
                                posts = data.get('posts', [])
                                print(f"    ✅ Valid data: {len(posts)} posts")
                            else:
                                print(f"    ⚠️ Unexpected data type: {type(data)}")
                            break  # Found valid data, move to next competitor
                        else:
                            print(f"    ❌ Empty or invalid data")
                    except Exception as e:
                        print(f"    ❌ Error reading data: {str(e)}")
            else:
                print(f"❌ No objects found for '{competitor}'")
        
        # Check for alternative storage patterns
        print("\n🔍 PLATFORM FOLDER STRUCTURE:")
        
        # Group by platform
        platforms = ['instagram', 'facebook', 'twitter']
        for platform in platforms:
            platform_objects = [obj for obj in object_keys if obj.startswith(f'{platform}/')]
            print(f"\n{platform.upper()}: {len(platform_objects)} objects")
            
            # Extract user folders
            user_folders = set()
            for obj in platform_objects:
                parts = obj.split('/')
                if len(parts) >= 2:
                    user_folders.add(parts[1])
            
            print(f"  User folders: {len(user_folders)}")
            for folder in sorted(list(user_folders))[:10]:
                folder_objects = [obj for obj in platform_objects if obj.startswith(f'{platform}/{folder}/')]
                print(f"    📁 {platform}/{folder}/ ({len(folder_objects)} files)")
                
                # Check for competitor files in this folder
                competitor_files = []
                for comp in competitors:
                    comp_files = [obj for obj in folder_objects if comp in obj.lower()]
                    competitor_files.extend(comp_files)
                
                if competitor_files:
                    print(f"      🎯 Competitor data: {competitor_files}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error investigating data structure: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_data_retrieval_methods():
    """Test different methods to retrieve competitor data."""
    
    print("\n🧪 TESTING DATA RETRIEVAL METHODS")
    print("=" * 50)
    
    try:
        sys.path.append('/home/komail/Miners-1')
        from data_retrieval import R2DataRetriever
        
        retriever = R2DataRetriever()
        competitors = ['nike', 'redbull', 'netflix']
        platforms = ['instagram', 'facebook', 'twitter']
        
        for platform in platforms:
            print(f"\n--- {platform.upper()} ---")
            for competitor in competitors:
                try:
                    data = retriever.get_social_media_data(competitor, platform=platform)
                    if data:
                        if isinstance(data, list):
                            print(f"✅ {competitor}: {len(data)} posts from {platform}")
                        elif isinstance(data, dict) and 'posts' in data:
                            posts = data['posts']
                            print(f"✅ {competitor}: {len(posts)} posts from {platform}")
                        else:
                            print(f"⚠️ {competitor}: Unexpected data format from {platform}")
                    else:
                        print(f"❌ {competitor}: No data from {platform}")
                except Exception as e:
                    print(f"❌ {competitor}: Error from {platform} - {str(e)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing retrieval methods: {str(e)}")
        return False

def main():
    """Main function to run data detective work."""
    
    print("🕵️ DATA STRUCTURE DETECTIVE")
    print("Investigating competitor data storage and retrieval issues...")
    print()
    
    # Step 1: Find where data is stored
    storage_found = find_competitor_data()
    
    # Step 2: Test retrieval methods
    retrieval_tested = test_data_retrieval_methods()
    
    print("\n" + "=" * 50)
    print("🎯 DETECTIVE SUMMARY:")
    print(f"  Storage Investigation: {'✅' if storage_found else '❌'}")
    print(f"  Retrieval Testing: {'✅' if retrieval_tested else '❌'}")
    
    if storage_found and retrieval_tested:
        print("\n🎉 Investigation complete! Check output above for data locations.")
        return 0
    else:
        print("\n💥 Investigation failed! Check errors above.")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
