"""
Fix test goals by marking them as processed
"""

import asyncio
from utils.r2_client import R2Client
from utils.logging import logger
from config import R2_CONFIG

async def fix_test_goals():
    """Mark test goals as processed to stop reprocessing"""
    r2 = R2Client(config=R2_CONFIG)
    
    test_goals = [
        'goal/instagram/testuser/goal_1748723521680.json',
        'goal/twitter/twitteruser/goal_1748723551732.json',
        'goal/instagram/test_campaign_user/goal_test_campaign.json'
    ]
    
    for goal_key in test_goals:
        try:
            goal_data = await r2.read_json(goal_key)
            if goal_data:
                goal_data['status'] = 'processed'
                goal_data['processed_at'] = '2025-06-01T06:15:00Z'
                goal_data['note'] = 'Marked as processed - test goal'
                
                success = await r2.write_json(goal_key, goal_data)
                if success:
                    print(f'✅ Fixed: {goal_key}')
                else:
                    print(f'❌ Failed to fix: {goal_key}')
            else:
                print(f'⚠️ No data found: {goal_key}')
                
        except Exception as e:
            print(f'❌ Error fixing {goal_key}: {e}')
    
    print('🎉 Test goals marked as processed')

if __name__ == "__main__":
    asyncio.run(fix_test_goals()) 