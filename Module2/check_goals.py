"""
Check what goal files exist in the bucket
"""

import asyncio
from utils.r2_client import R2Client
from utils.logging import logger
from config import R2_CONFIG

async def check_goals():
    """Check what goal files exist"""
    r2 = R2Client(config=R2_CONFIG)
    
    try:
        objects = await r2.list_objects('goal/')
        goal_files = [obj for obj in objects if 'goal_' in obj['Key'] and obj['Key'].endswith('.json')]
        
        print(f'Found {len(goal_files)} goal files:')
        
        for obj in goal_files:
            key = obj['Key']
            try:
                goal_data = await r2.read_json(key)
                status = goal_data.get('status', 'unknown') if goal_data else 'empty'
                goal_text = goal_data.get('goal', 'No goal text')[:50] + '...' if goal_data and goal_data.get('goal') else 'No goal'
                print(f'  📄 {key}')
                print(f'     Status: {status}')
                print(f'     Goal: {goal_text}')
                print()
            except Exception as e:
                print(f'  ❌ {key} - Error reading: {e}')
                
    except Exception as e:
        print(f'Error listing goals: {e}')

if __name__ == "__main__":
    asyncio.run(check_goals()) 