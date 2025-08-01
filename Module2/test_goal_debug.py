#!/usr/bin/env python3
"""Debug script to test why goal processing is not working"""

import asyncio
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def main():
    print("🔍 DEBUGGING GOAL PROCESSING ISSUE")
    print("=" * 50)
    
    # Test 1: Import TestFilter
    try:
        from utils.test_filter import TestFilter
        print("✅ TestFilter imported successfully")
        
        # Test if elonmusk is being filtered
        username = 'elonmusk'
        platform = 'twitter'
        goal_key = 'goal/twitter/elonmusk/goal_1753186301525.json'
        
        print(f"\n🧪 Testing TestFilter for:")
        print(f"   Username: {username}")
        print(f"   Platform: {platform}")
        print(f"   Goal key: {goal_key}")
        
        should_skip = TestFilter.should_skip_processing(platform, username, goal_key)
        print(f"\n📊 TestFilter.should_skip_processing(): {should_skip}")
        
        if should_skip:
            print("❌ FOUND THE ISSUE: TestFilter is blocking goal processing!")
            print("   The TestFilter is incorrectly identifying this as test data.")
        else:
            print("✅ TestFilter is NOT blocking this goal.")
        
    except Exception as e:
        print(f"❌ Error importing TestFilter: {e}")
        
    # Test 2: R2 Client Access
    try:
        from utils.r2_client import R2Client
        from config import R2_CONFIG
        print(f"\n✅ R2Client imported successfully")
        print(f"   Bucket: {R2_CONFIG.get('bucket_name', 'Unknown')}")
        
        client = R2Client(config=R2_CONFIG)
        goal_key = 'goal/twitter/elonmusk/goal_1753186301525.json'
        
        print(f"\n🌐 Testing R2 access to: {goal_key}")
        goal_data = await client.read_json(goal_key)
        
        if goal_data:
            print("✅ Goal file accessible via R2")
            print(f"   Status: {goal_data.get('status')}")
            print(f"   Goal: {goal_data.get('goal', '')[:50]}...")
        else:
            print("❌ Could not read goal file from R2")
            
    except Exception as e:
        print(f"❌ Error with R2 access: {e}")
        
    # Test 3: Goal Handler Detection
    try:
        from goal_rag_handler import EnhancedGoalHandler
        print(f"\n✅ EnhancedGoalHandler imported successfully")
        
        handler = EnhancedGoalHandler()
        print("✅ Goal handler instance created")
        
        # Check if goal is in processed files
        goal_key = 'goal/twitter/elonmusk/goal_1753186301525.json'
        if goal_key in handler.processed_files:
            print(f"❌ Goal already marked as processed in current session")
        else:
            print(f"✅ Goal NOT in processed files list")
            
    except Exception as e:
        print(f"❌ Error with Goal Handler: {e}")
        
    # Test 4: Manual Goal Processing Test
    try:
        print(f"\n🚀 Testing manual goal processing...")
        handler = EnhancedGoalHandler()
        goal_key = 'goal/twitter/elonmusk/goal_1753186301525.json'
        
        # Try to process the goal manually
        await handler.process_goal_file(goal_key)
        print("✅ Manual goal processing completed")
        
    except Exception as e:
        print(f"❌ Error in manual goal processing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
