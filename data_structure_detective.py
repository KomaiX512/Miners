#!/usr/bin/env python3

"""
Data Structure Detective: Find Competitor Data
==============================================

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
        
        # Search for competitor data patterns
        competitors = ['nike', 'redbull', 'netflix']
        
        print("\n🎯 COMPETITOR DATA SEARCH:")
        for competitor in competitors:
            print(f"\n--- {competitor.upper()} ---")
            
            # Find all objects containing this competitor name
            comp_objects = [obj for obj in objects if competitor in obj.lower()]
            
            if comp_objects:
                print(f"✅ Found {len(comp_objects)} objects with '{competitor}':")
                for obj in comp_objects[:5]:  # Show first 5
                    print(f"  📄 {obj}")
                    
                    # Try to get the data to see if it's valid
                    try:
                        # Try to get data using the get_social_media_data method
                        data = retriever.get_social_media_data(competitor, platform="instagram")
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
        print("\n🔍 ALTERNATIVE STORAGE PATTERNS:")
        
        # Pattern 1: Primary username folders containing competitor data
        instagram_folders = set()
        facebook_folders = set()
        
        for obj in objects:
            if obj.startswith('instagram/'):
                parts = obj.split('/')
                if len(parts) >= 2:
                    instagram_folders.add(parts[1])
            elif obj.startswith('facebook/'):
                parts = obj.split('/')
                if len(parts) >= 2:
                    facebook_folders.add(parts[1])
        
        print(f"Instagram user folders: {len(instagram_folders)}")
        for folder in sorted(list(instagram_folders))[:10]:
            print(f"  📁 instagram/{folder}/")
            
            # Check if this folder contains competitor data
            folder_objects = [obj for obj in objects if obj.startswith(f'instagram/{folder}/')]
            competitor_files = []
            for comp in competitors:
                comp_files = [obj for obj in folder_objects if comp in obj.lower()]
                if comp_files:
                    competitor_files.extend(comp_files)
            
            if competitor_files:
                print(f"    🎯 Contains competitor data: {competitor_files}")
        
        print(f"\nFacebook user folders: {len(facebook_folders)}")
        for folder in sorted(list(facebook_folders))[:10]:
            print(f"  📁 facebook/{folder}/")
            
            # Check if this folder contains competitor data
            folder_objects = [obj for obj in objects if obj.startswith(f'facebook/{folder}/')]
            competitor_files = []
            for comp in competitors:
                comp_files = [obj for obj in folder_objects if comp in obj.lower()]
                if comp_files:
                    competitor_files.extend(comp_files)
            
            if competitor_files:
                print(f"    🎯 Contains competitor data: {competitor_files}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error investigating data structure: {str(e)}")
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
        print("\n💥 Investigation failed! No competitor data found.")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
