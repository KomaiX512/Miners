import asyncio
import sys
sys.path.append('Module2')
from utils.r2_client import R2Client
from utils.logging import logger

async def check_file_status():
    r2_client = R2Client()
    
    # Check a few sample files
    sample_files = [
        'next_posts/instagram/fentybeauty/post_1.json',
        'next_posts/instagram/fentybeauty/post_2.json',
        'next_posts/twitter/NASA/post_1.json'
    ]
    
    for file_key in sample_files:
        try:
            data = await r2_client.read_json(file_key)
            if data:
                status = data.get('status', 'NO_STATUS_FIELD')
                print(f'File: {file_key}')
                print(f'Status: {status}')
                print(f'Keys: {list(data.keys())}')
                print('---')
            else:
                print(f'File: {file_key} - Could not read data')
        except Exception as e:
            print(f'File: {file_key} - Error: {e}')

if __name__ == "__main__":
    asyncio.run(check_file_status()) 