#!/usr/bin/env python3
"""
Test the export_content_plan.py module functionality.
"""

import json
import os
import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime

from export_content_plan import ContentPlanExporter

class TestContentPlanExporter(unittest.TestCase):
    def setUp(self):
        """Set up test environment"""
        self.r2_storage = MagicMock()
        self.exporter = ContentPlanExporter(self.r2_storage)
        
        # Sample content plan for testing
        self.sample_content_plan = {
            "primary_username": "test_user",
            "platform": "instagram",
            "timestamp": datetime.now().isoformat(),
            "account_type": "branding",
            "posting_style": "professional",
            "total_posts_analyzed": 10,
            "competitors": ["competitor1", "competitor2"],
            "recommendation": {
                "competitive_intelligence": {
                    "account_analysis": "Test account analysis",
                    "brand strategy, market positioning, competitive analysis": "Test strategy",
                    "strategic_positioning": "Test positioning",
                    "competitive_analysis": "Test competitive analysis"
                },
                "tactical_recommendations": [
                    "Tactical recommendation 1",
                    "Tactical recommendation 2"
                ],
                "threat_assessment": {
                    "competitor_analysis": {
                        "competitor1": {
                            "overview": "Test overview for competitor1",
                            "strengths": ["Strength 1", "Strength 2"],
                            "vulnerabilities": ["Vulnerability 1", "Vulnerability 2"],
                            "recommended_counter_strategies": ["Strategy 1", "Strategy 2"]
                        },
                        "competitor2": {
                            "overview": "Test overview for competitor2",
                            "strengths": ["Strength 1", "Strength 2"],
                            "vulnerabilities": ["Vulnerability 1", "Vulnerability 2"],
                            "recommended_counter_strategies": ["Strategy 1", "Strategy 2"]
                        }
                    }
                }
            },
            "next_post_prediction": {
                "caption": "Test caption",
                "hashtags": ["#test1", "#test2"],
                "call_to_action": "Test CTA",
                "image_prompt": "Test image prompt"
            }
        }
        
    def test_export_content_plan_success(self):
        """Test successful export of all content plan sections"""
        # Mock R2 storage methods
        self.r2_storage.upload_file.return_value = {"success": True}
        self.r2_storage.list_files.return_value = []
        
        # Export content plan
        result = self.exporter.export_content_plan(self.sample_content_plan)
        
        # Verify results
        self.assertIsNotNone(result)
        self.assertIn('recommendation', result)
        self.assertIn('next_post', result)
        self.assertIn('competitor_analysis', result)
        self.assertEqual(len(result['competitor_analysis']), 2)
        
        # Verify R2 storage calls
        self.assertTrue(self.r2_storage.upload_file.call_count > 0)
        
    def test_export_content_plan_missing_fields(self):
        """Test export with missing required fields"""
        # Remove required fields
        invalid_content_plan = self.sample_content_plan.copy()
        del invalid_content_plan['primary_username']
        
        # Export content plan
        result = self.exporter.export_content_plan(invalid_content_plan)
        
        # Verify result
        self.assertFalse(result)
        
    def test_export_content_plan_no_recommendation(self):
        """Test export with no recommendation section"""
        # Remove recommendation section
        content_plan = self.sample_content_plan.copy()
        del content_plan['recommendation']
        
        # Export content plan
        result = self.exporter.export_content_plan(content_plan)
        
        # Verify results
        self.assertIsNotNone(result)
        self.assertNotIn('recommendation', result)
        self.assertIn('next_post', result)
        
    def test_export_content_plan_no_next_post(self):
        """Test export with no next post prediction"""
        # Remove next post prediction
        content_plan = self.sample_content_plan.copy()
        del content_plan['next_post_prediction']
        
        # Export content plan
        result = self.exporter.export_content_plan(content_plan)
        
        # Verify results
        self.assertIsNotNone(result)
        self.assertIn('recommendation', result)
        self.assertNotIn('next_post', result)
        
    def test_export_content_plan_no_competitor_analysis(self):
        """Test export with no competitor analysis"""
        # Remove competitor analysis
        content_plan = self.sample_content_plan.copy()
        del content_plan['recommendation']['threat_assessment']['competitor_analysis']
        
        # Export content plan
        result = self.exporter.export_content_plan(content_plan)
        
        # Verify results
        self.assertIsNotNone(result)
        self.assertIn('recommendation', result)
        self.assertNotIn('competitor_analysis', result)
        
    def test_get_next_file_number(self):
        """Test getting next file number"""
        # Mock existing files
        self.r2_storage.list_files.return_value = [
            "recommendations/instagram/test_user/recommendation_1.json",
            "recommendations/instagram/test_user/recommendation_2.json"
        ]
        
        # Get next file number
        next_num = self.exporter._get_next_file_number(
            "recommendations/instagram",
            "test_user",
            "recommendation"
        )
        
        # Verify result
        self.assertEqual(next_num, 3)
        
    def test_ensure_directory_exists(self):
        """Test ensuring directory exists"""
        # Mock R2 storage
        self.r2_storage.upload_file.return_value = {"success": True}
        
        # Ensure directory exists
        result = self.exporter._ensure_directory_exists("test/directory/")
        
        # Verify result
        self.assertTrue(result)
        self.r2_storage.upload_file.assert_called_once()

if __name__ == '__main__':
    unittest.main() 