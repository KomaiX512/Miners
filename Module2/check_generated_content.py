"""
Check and clean up generated content files
"""

import asyncio
from utils.r2_client import R2Client
from utils.logging import logger
from config import R2_CONFIG

async def check_and_cleanup_content():
    """Check and clean up test content files"""
    r2 = R2Client(config=R2_CONFIG)
    
    try:
        # Check generated content
        objects = await r2.list_objects('generated_content/')
        test_files = [obj for obj in objects if any(test_word in obj['Key'].lower() for test_word in ['test', 'demo', 'sample'])]
        
        if test_files:
            print(f'Found {len(test_files)} test content files:')
            for obj in test_files:
                print(f'  - {obj["Key"]}')
                try:
                    await r2.delete_object(obj["Key"])
                    print(f'    ✅ Deleted')
                except Exception as e:
                    print(f'    ❌ Error deleting: {e}')
        else:
            print('No test content files found')
        
        # Check next_posts for test files
        objects = await r2.list_objects('next_posts/')
        test_files = [obj for obj in objects if any(test_word in obj['Key'].lower() for test_word in ['test', 'demo', 'sample'])]
        
        if test_files:
            print(f'Found {len(test_files)} test next_posts files')
            for obj in test_files[:5]:  # Show first 5
                print(f'  - {obj["Key"]}')
            
            print('Cleaning up test next_posts...')
            for obj in test_files:
                try:
                    await r2.delete_object(obj["Key"])
                except:
                    pass
            print(f'Cleaned up {len(test_files)} test next_posts files')
        
    except Exception as e:
        print(f'Error: {e}')

if __name__ == "__main__":
    asyncio.run(check_and_cleanup_content()) 