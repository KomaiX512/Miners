#!/usr/bin/env python3
"""
Test script to verify the export_content_plan module works with the new ContentPlan.json format.
"""

import json
import logging
import io
from unittest.mock import MagicMock
from export_content_plan import ContentPlanExporter

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('test_exporter')

def load_content_plan(file_path='content_plan.json'):
    """Load content plan from file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading content plan: {str(e)}")
        return None

def create_mock_r2_storage():
    """Create a mock R2 storage object for testing"""
    mock_r2 = MagicMock()
    
    # Mock list_files method
    mock_r2.list_files.return_value = []
    
    # Mock upload_file method
    mock_r2.upload_file.return_value = True
    
    # Track uploaded files
    mock_r2.uploaded_files = {}
    
    # Override upload_file to track files
    def mock_upload(key, file_obj, bucket):
        try:
            # Read the file object content
            content = file_obj.read().decode('utf-8')
            # Store the uploaded content
            mock_r2.uploaded_files[key] = json.loads(content)
            logger.info(f"Uploaded to {key}")
            return True
        except Exception as e:
            logger.error(f"Error in mock upload: {str(e)}")
            return False
    
    mock_r2.upload_file = mock_upload
    return mock_r2

def test_exportation():
    """Test the content plan exportation process"""
    logger.info("Starting exportation test")
    
    # Load content plan
    content_plan = load_content_plan()
    if not content_plan:
        logger.error("Failed to load content plan")
        return False
    
    # Create mock R2 storage
    mock_r2 = create_mock_r2_storage()
    
    # Create exporter
    exporter = ContentPlanExporter(mock_r2)
    
    # Export content plan
    result = exporter.export_content_plan(content_plan)
    logger.info(f"Export result: {result}")
    
    # Check exported files
    if hasattr(mock_r2, 'uploaded_files'):
        logger.info(f"Exported {len(mock_r2.uploaded_files)} files:")
        for key, content in mock_r2.uploaded_files.items():
            module_type = content.get('module_type', 'unknown')
            logger.info(f"- {key}: {module_type}")
            
            # Additional validation based on module type
            if module_type == 'recommendation':
                if 'data' in content and 'personal_intelligence' in content['data']:
                    logger.info("  ✅ Recommendation module contains personal_intelligence")
                else:
                    logger.error("  ❌ Recommendation module missing personal_intelligence")
                
                # Check for content_intelligence
                if 'data' in content and 'content_intelligence' in content['data']:
                    logger.info("  ✅ Recommendation module contains content_intelligence")
                    # Print some key data from content_intelligence
                    ci = content['data']['content_intelligence']
                    logger.info(f"  📊 Account Analysis Preview: {ci.get('account_analysis', '')[:50]}...")
                    logger.info(f"  📊 Platform: {ci.get('platform', '')}")
                else:
                    logger.error("  ❌ Recommendation module missing content_intelligence")
                
                # Print module structure
                logger.info("  📋 Recommendation module structure:")
                for key in content['data'].keys():
                    logger.info(f"    - {key}")
                    
            elif module_type == 'next_post_prediction':
                if 'data' in content and 'caption' in content['data']:
                    logger.info("  ✅ Next post prediction contains caption")
                    logger.info(f"  📝 Caption Preview: {content['data'].get('caption', '')[:50]}...")
                else:
                    logger.error("  ❌ Next post prediction missing caption")
                    
            elif module_type == 'competitor_analysis':
                if 'competitor' in content and 'data' in content:
                    logger.info(f"  ✅ Competitor analysis for {content['competitor']}")
                    # Print overview
                    if 'overview' in content['data']:
                        logger.info(f"  📊 Overview Preview: {content['data'].get('overview', '')[:50]}...")
                else:
                    logger.error("  ❌ Competitor analysis missing competitor info")
    else:
        logger.warning("No files were exported")
    
    return result

if __name__ == "__main__":
    success = test_exportation()
    if success:
        logger.info("✅ Export test completed successfully")
    else:
        logger.error("❌ Export test failed") 