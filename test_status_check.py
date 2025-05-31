import asyncio
import sys
sys.path.append('Module2')
from utils.r2_client import R2Client
from utils.status_manager import StatusManager
from config import R2_CONFIG

async def test_status_check():
    # Test the new status checking logic
    tasks_config = {
        'endpoint_url': R2_CONFIG['endpoint_url'],
        'aws_access_key_id': R2_CONFIG['aws_access_key_id'],
        'aws_secret_access_key': R2_CONFIG['aws_secret_access_key'],
        'bucket_name': 'tasks'
    }
    
    status_manager = StatusManager()
    status_manager.r2_client = R2Client(config=tasks_config)
    
    # Test a few files
    test_files = [
        'next_posts/instagram/fentybeauty/post_1.json',
        'next_posts/twitter/NASA/post_1.json'
    ]
    
    for file_key in test_files:
        is_pending = await status_manager.is_pending(file_key)
        print(f'{file_key}: pending={is_pending}')

if __name__ == "__main__":
    asyncio.run(test_status_check()) 