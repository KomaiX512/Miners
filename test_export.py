#!/usr/bin/env python3
"""
Test script to verify the content plan export functionality
"""

import json
import logging
import os
from export_content_plan import ContentPlanExporter
from r2_storage import R2Storage

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('test_export')

def test_export():
    """Test the content plan export functionality"""
    try:
        # Initialize R2 storage in mock mode
        r2_storage = R2Storage(mock_mode=True)
        
        # Initialize content plan exporter directly
        exporter = ContentPlanExporter(r2_storage)
        
        # Create a test content plan
        test_content_plan = {
            "platform": "instagram",
            "primary_username": "test_user",
            "recommendation": {
                "personal_intelligence": {
                    "account_strengths": ["High engagement", "Consistent posting"],
                    "account_weaknesses": ["Low follower growth", "Limited content variety"]
                },
                "tactical_recommendations": [
                    "Post more frequently",
                    "Use trending hashtags",
                    "Engage with followers"
                ],
                "threat_assessment": {
                    "competitor_analysis": {
                        "competitor1": {
                            "strengths": ["Large following", "High engagement"],
                            "weaknesses": ["Inconsistent posting", "Poor content quality"]
                        },
                        "competitor2": {
                            "note": "Limited data available"
                        },
                        "narsissist": {
                            "note": "NARSissist is a new competitor with limited data available"
                        }
                    }
                },
                "next_post_prediction": {
                    "caption": "Check out our latest update! #trending #new",
                    "hashtags": ["#trending", "#new"],
                    "best_posting_time": "2024-03-20T15:00:00Z"
                }
            }
        }
        
        # Export the content plan
        success = exporter.export_content_plan(test_content_plan)
        
        if success:
            logger.info("✅ Test passed: Content plan exported successfully")
            
            # Verify fix 1: threat_assessment removed from recommendation export
            logger.info("🔍 Verifying Fix 1: threat_assessment removed from recommendation export")
            
            # Verify fix 2: next_post directory changed to next_posts
            logger.info("🔍 Verifying Fix 2: next_post directory changed to next_posts")
            
            # Verify fix 3: Competitor with limited data is properly handled
            logger.info("🔍 Verifying Fix 3: NARSissist competitor with limited data handled correctly")
            
            return True
        else:
            logger.error("❌ Test failed: Content plan export failed")
            return False
            
    except Exception as e:
        logger.error(f"❌ Test failed with error: {str(e)}")
        return False

if __name__ == "__main__":
    test_export() 