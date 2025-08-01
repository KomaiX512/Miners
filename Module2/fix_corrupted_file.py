#!/usr/bin/env python3
"""
Script to identify and fix corrupted files causing UTF-8 decode errors
"""

import asyncio
import json
from utils.r2_client import R2Client
from config import R2_CONFIG

async def check_and_fix_corrupted_files():
    """Check for corrupted files and fix them"""
    print("🔍 Checking for corrupted files...")
    
    client = R2Client(config=R2_CONFIG)
    
    # The specific file that's causing issues
    problematic_file = "next_posts/twitter/ylecun/campaign_next_post_6.json"
    
    try:
        # Try to read the file
        print(f"📖 Attempting to read: {problematic_file}")
        data = await client.read_json(problematic_file)
        print("✅ File is readable and not corrupted")
        return True
    except Exception as e:
        print(f"❌ File is corrupted: {e}")
        
        # Delete the corrupted file
        try:
            print(f"🗑️ Deleting corrupted file: {problematic_file}")
            await client.delete_object(problematic_file)
            print("✅ Corrupted file deleted")
            return True
        except Exception as delete_error:
            print(f"❌ Failed to delete corrupted file: {delete_error}")
            return False

async def check_all_potentially_corrupted_files():
    """Check all files in the next_posts directory for corruption"""
    print("🔍 Checking all files for corruption...")
    
    client = R2Client(config=R2_CONFIG)
    
    try:
        # List all objects in next_posts
        objects = await client.list_objects("next_posts/")
        
        corrupted_files = []
        
        for obj in objects:
            key = obj["Key"]
            if key.endswith(".json"):
                try:
                    # Try to read each JSON file
                    data = await client.read_json(key)
                    print(f"✅ {key} - OK")
                except Exception as e:
                    print(f"❌ {key} - CORRUPTED: {e}")
                    corrupted_files.append(key)
        
        if corrupted_files:
            print(f"\n🚨 Found {len(corrupted_files)} corrupted files:")
            for file in corrupted_files:
                print(f"  - {file}")
                
            # Delete corrupted files
            print("\n🗑️ Deleting corrupted files...")
            for file in corrupted_files:
                try:
                    await client.delete_object(file)
                    print(f"✅ Deleted: {file}")
                except Exception as e:
                    print(f"❌ Failed to delete {file}: {e}")
        else:
            print("✅ No corrupted files found")
            
    except Exception as e:
        print(f"❌ Error checking files: {e}")

if __name__ == "__main__":
    print("🧹 Corrupted File Cleanup Tool")
    print("=" * 40)
    
    # First check the specific problematic file
    asyncio.run(check_and_fix_corrupted_files())
    
    print("\n" + "=" * 40)
    
    # Then check all files
    asyncio.run(check_all_potentially_corrupted_files())
    
    print("\n✅ Cleanup complete!") 