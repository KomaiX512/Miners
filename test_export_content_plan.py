#!/usr/bin/env python3
"""
Test suite for the content plan exportation module.
"""

import unittest
import json
import io
from datetime import datetime
from unittest.mock import MagicMock, patch
from export_content_plan import ContentPlanExporter
import os
import logging

class TestContentPlanExporter(unittest.TestCase):
    def setUp(self):
        """Set up test environment"""
        self.r2_storage = MagicMock()
        self.exporter = ContentPlanExporter(self.r2_storage)
        
        # Sample content plan
        self.sample_content_plan = {
            "primary_username": "test_user",
            "platform": "instagram",
            "timestamp": datetime.now().isoformat(),
            "account_type": "branding",
            "posting_style": "professional",
            "total_posts_analyzed": 100,
            "competitors": ["competitor1", "competitor2", "competitor3"],
            "competitor_analysis": {
                "competitor1": {
                    "overview": "Competitive analysis for competitor1",
                    "intelligence_source": "data_source",
                    "strengths": ["Strength 1", "Strength 2"],
                    "vulnerabilities": ["Vulnerability 1", "Vulnerability 2"],
                    "recommended_counter_strategies": [],
                    "top_content_themes": []
                },
                "competitor2": {
                    "overview": "Competitive analysis for competitor2",
                    "intelligence_source": "data_source",
                    "strengths": ["Strength 1", "Strength 2"],
                    "vulnerabilities": ["Vulnerability 1", "Vulnerability 2"],
                    "recommended_counter_strategies": [],
                    "top_content_themes": []
                }
            },
            "recommendation": {
                "competitive_intelligence": {
                    "account_analysis": "Analysis of account",
                    "brand strategy": "Brand strategy recommendations",
                    "strategic_positioning": "Strategic positioning analysis"
                },
                "tactical_recommendations": [
                    "Tactical recommendation 1",
                    "Tactical recommendation 2"
                ],
                "threat_assessment": {
                    "overview": "Threat assessment overview",
                    "key_findings": ["Finding 1", "Finding 2"]
                }
            },
            "next_post_prediction": {
                "caption": "Test caption",
                "hashtags": ["#test1", "#test2"],
                "call_to_action": "Test CTA",
                "image_prompt": "Test image prompt"
            }
        }
        
        # Mock R2 storage responses
        self.r2_storage.list_files.return_value = []
        self.r2_storage.upload_file.return_value = True
        
    def test_export_content_plan_success(self):
        """Test successful export of all content plan sections"""
        result = self.exporter.export_content_plan(self.sample_content_plan)
        self.assertTrue(result)
        
        # Verify recommendation export
        recommendation_calls = [call for call in self.r2_storage.upload_file.call_args_list 
                              if 'recommendation_' in call[1]['key']]
        self.assertEqual(len(recommendation_calls), 1)
        
        # Verify next post export
        next_post_calls = [call for call in self.r2_storage.upload_file.call_args_list 
                          if 'post_' in call[1]['key']]
        self.assertEqual(len(next_post_calls), 1)
        
        # Verify competitor analysis exports
        competitor_calls = [call for call in self.r2_storage.upload_file.call_args_list 
                          if 'analysis_' in call[1]['key']]
        self.assertEqual(len(competitor_calls), 2)  # One for each competitor
        
    def test_export_content_plan_missing_fields(self):
        """Test export with missing required fields"""
        # Test missing primary_username
        content_plan = self.sample_content_plan.copy()
        del content_plan['primary_username']
        result = self.exporter.export_content_plan(content_plan)
        self.assertFalse(result)
        
    def test_export_content_plan_empty(self):
        """Test export with empty content plan"""
        result = self.exporter.export_content_plan({})
        self.assertFalse(result)
        
    def test_export_content_plan_partial(self):
        """Test export with partial content (some sections missing)"""
        # Test with only recommendation section
        content_plan = {
            "primary_username": "test_user",
            "platform": "instagram",
            "recommendation": self.sample_content_plan['recommendation']
        }
        result = self.exporter.export_content_plan(content_plan)
        self.assertTrue(result)
        
        # Verify only recommendation was exported
        recommendation_calls = [call for call in self.r2_storage.upload_file.call_args_list 
                              if 'recommendation_' in call[1]['key']]
        self.assertEqual(len(recommendation_calls), 1)
        
        next_post_calls = [call for call in self.r2_storage.upload_file.call_args_list 
                          if 'post_' in call[1]['key']]
        self.assertEqual(len(next_post_calls), 0)
        
    def test_get_next_file_number(self):
        """Test file number generation"""
        # Test with no existing files
        self.r2_storage.list_files.return_value = []
        number = self.exporter._get_next_file_number("test_dir/", "test")
        self.assertEqual(number, 1)
        
        # Test with existing files
        self.r2_storage.list_files.return_value = [
            "test_dir/test_1.json",
            "test_dir/test_2.json",
            "test_dir/test_3.json"
        ]
        number = self.exporter._get_next_file_number("test_dir/", "test")
        self.assertEqual(number, 4)
        
        # Test with invalid filenames
        self.r2_storage.list_files.return_value = [
            "test_dir/test_invalid.json",
            "test_dir/test_1.json",
            "test_dir/other_1.json"
        ]
        number = self.exporter._get_next_file_number("test_dir/", "test")
        self.assertEqual(number, 2)

    def test_next_post_export_from_content_plan(self):
        """Test exporting next post from content_plan.json."""
        # Load the actual content plan.json from file
        try:
            with open('content_plan.json', 'r', encoding='utf-8') as f:
                content_plan = json.load(f)
        except FileNotFoundError:
            self.skipTest("content_plan.json not found, skipping test")
            return
            
        # Call export function
        result = self.exporter.export_content_plan(content_plan)
        self.assertTrue(result, "Export function should return True on success")
        
        # Verify that the upload_file was called with the next post data
        upload_calls = self.r2_storage.upload_file.call_args_list
        next_post_call = None
        
        for call in upload_calls:
            args, kwargs = call
            key = kwargs.get('key', '')
            if 'next_posts' in key and 'post_' in key:
                next_post_call = call
                break
        
        self.assertIsNotNone(next_post_call, "upload_file should be called with next post data")
        
        if next_post_call:
            # Extract the uploaded JSON data
            file_obj = next_post_call[1]['file_obj']
            file_obj.seek(0)  # Reset pointer to beginning of BytesIO object
            uploaded_data = json.loads(file_obj.read().decode('utf-8'))
            
            # Verify export structure
            self.assertIn('module_type', uploaded_data)
            self.assertEqual(uploaded_data['module_type'], 'next_post_prediction')
            self.assertIn('data', uploaded_data)
            
            # Verify expected fields in the next post data
            next_post_data = uploaded_data['data']
            self.assertIn('caption', next_post_data, "Next post should include a caption")
            self.assertIn('hashtags', next_post_data, "Next post should include hashtags")
            self.assertIn('call_to_action', next_post_data, "Next post should include call_to_action")
            self.assertIn('image_prompt', next_post_data, "Next post should include image_prompt")
            
            # Print out the entire next post data for debugging
            print("\nExported next post data:")
            print(json.dumps(next_post_data, indent=2))
            
            # Verify no data is lost (compare with original)
            original_next_post = None
            if 'recommendation' in content_plan and 'next_post_prediction' in content_plan['recommendation']:
                original_next_post = content_plan['recommendation']['next_post_prediction']
            elif 'next_post_prediction' in content_plan:
                original_next_post = content_plan['next_post_prediction']
                
            self.assertIsNotNone(original_next_post, "Original next post data should exist in content plan")
            
            if original_next_post:
                for key, value in original_next_post.items():
                    self.assertEqual(next_post_data.get(key), value, 
                                    f"Value for {key} in exported data should match original")

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    unittest.main() 