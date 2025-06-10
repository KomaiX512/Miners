#!/usr/bin/env python3
"""
Test suite for the image generator module with specific focus on preserving 
content from exported next post data.
"""

import unittest
import json
import asyncio
from unittest.mock import MagicMock, patch
from datetime import datetime
import io
import sys
import os

# Mock required modules
sys.modules['utils.r2_client'] = MagicMock()
sys.modules['utils.status_manager'] = MagicMock()
sys.modules['utils.logging'] = MagicMock()
sys.modules['utils.test_filter'] = MagicMock()
sys.modules['config'] = MagicMock()

# Now import the module with mocked dependencies
sys.path.append(os.path.join(os.path.dirname(__file__), "Module2"))
from Module2.image_generator import ImageGenerator

class TestImageGenerator(unittest.TestCase):
    """Test cases for the ImageGenerator class"""
    
    def setUp(self):
        """Set up the test environment"""
        # Create mocks for R2 clients
        self.mock_input_r2 = MagicMock()
        self.mock_output_r2 = MagicMock()
        self.mock_status_manager = MagicMock()
        
        # Create ImageGenerator instance
        with patch('Module2.image_generator.R2Client'), \
             patch('Module2.image_generator.StatusManager'), \
             patch('Module2.image_generator.logger'):
            self.generator = ImageGenerator()
            
        self.generator.input_r2_client = self.mock_input_r2
        self.generator.output_r2_client = self.mock_output_r2
        self.generator.status_manager = self.mock_status_manager
        
        # Sample exported next post data (as would be created by ContentPlanExporter)
        self.sample_exported_post = {
            "module_type": "next_post_prediction",
            "platform": "instagram",
            "primary_username": "narsissist",
            "timestamp": datetime.now().isoformat(),
            "data": {
                "caption": "This is a test caption that should remain unchanged!",
                "hashtags": ["#Test1", "#Test2", "#PreserveThese"],
                "call_to_action": "This call to action should be preserved exactly!",
                "image_prompt": "Test image prompt for AI generation"
            }
        }
        
    def test_convert_nextpost_to_standard_format(self):
        """Test the conversion of exported next post format to standard format"""
        key = "next_posts/instagram/narsissist/post_1.json"
        result = self.generator._convert_nextpost_to_standard_format(self.sample_exported_post, key)
        
        # Verify result structure
        self.assertIsNotNone(result)
        self.assertIn("post", result)
        self.assertIn("status", result)
        self.assertEqual(result["status"], "pending")
        self.assertEqual(result["platform"], "instagram")
        self.assertEqual(result["username"], "narsissist")
        
        # Verify content preservation
        post = result["post"]
        self.assertEqual(post["caption"], self.sample_exported_post["data"]["caption"])
        self.assertEqual(post["hashtags"], self.sample_exported_post["data"]["hashtags"])
        self.assertEqual(post["call_to_action"], self.sample_exported_post["data"]["call_to_action"])
        self.assertEqual(post["image_prompt"], self.sample_exported_post["data"]["image_prompt"])
    
    def test_create_output_post(self):
        """Test that _create_output_post preserves all original content"""
        # First convert to standard format
        key = "next_posts/instagram/narsissist/post_1.json"
        standardized = self.generator._convert_nextpost_to_standard_format(self.sample_exported_post, key)
        
        # Then create output post
        image_key = "ready_post/instagram/narsissist/image_1.jpg"
        output = self.generator._create_output_post(
            standardized["post"], 
            image_key, 
            "instagram", 
            "narsissist", 
            {"original_format": "nextpost_module"}
        )
        
        # Verify output structure
        self.assertIn("post", output)
        self.assertIn("caption", output["post"])
        self.assertIn("hashtags", output["post"])
        self.assertIn("call_to_action", output["post"])
        
        # Verify exact content preservation
        self.assertEqual(output["post"]["caption"], self.sample_exported_post["data"]["caption"])
        self.assertEqual(output["post"]["hashtags"], self.sample_exported_post["data"]["hashtags"])
        self.assertEqual(output["post"]["call_to_action"], self.sample_exported_post["data"]["call_to_action"])

    def test_standardize_post_fields(self):
        """Test that post fields are standardized while preserving content exactly"""
        original_data = self.sample_exported_post["data"]
        result = self.generator._standardize_post_fields(original_data, "test_key")
        
        # Verify all fields are preserved exactly
        self.assertEqual(result["caption"], original_data["caption"])
        self.assertEqual(result["hashtags"], original_data["hashtags"])
        self.assertEqual(result["call_to_action"], original_data["call_to_action"])
        self.assertEqual(result["image_prompt"], original_data["image_prompt"])

    def test_process_nextpost_end_to_end(self):
        """Mock the entire process_post function to verify end-to-end pipeline"""
        # Set up mocks to simulate successful processing
        key = "next_posts/instagram/narsissist/post_1.json"
        
        # Mock the methods that would make external API calls
        self.generator.generate_image = MagicMock(return_value="https://test-image-url.com/image.jpg")
        self.generator.download_image = MagicMock(return_value=b"fake_image_data")
        self.generator.save_image = MagicMock(return_value=True)
        
        # Mock the status manager
        self.generator.status_manager.is_pending = MagicMock(return_value=True)
        self.generator.status_manager.mark_processed = MagicMock()
        
        # Mock the input R2 client to return our sample post
        self.generator.input_r2_client.read_json = MagicMock(return_value=self.sample_exported_post)
        self.generator.output_r2_client.list_objects = MagicMock(return_value=[])
        self.generator.output_r2_client.write_json = MagicMock(return_value=True)
        
        # Create a test coroutine that calls process_post
        async def test_coroutine():
            mock_session = MagicMock()
            await self.generator.process_post(key, mock_session)
            
        # Run the test coroutine
        asyncio.run(test_coroutine())
        
        # Verify the output_r2_client.write_json was called with a post that preserves the original content
        write_json_calls = self.generator.output_r2_client.write_json.call_args_list
        self.assertTrue(len(write_json_calls) > 0)
        
        # Get the output post data from the call
        output_key, output_data = write_json_calls[0][0]
        
        # Verify the output post preserves the original content
        self.assertIn("post", output_data)
        self.assertEqual(output_data["post"]["caption"], self.sample_exported_post["data"]["caption"])
        self.assertEqual(output_data["post"]["hashtags"], self.sample_exported_post["data"]["hashtags"])
        self.assertEqual(output_data["post"]["call_to_action"], self.sample_exported_post["data"]["call_to_action"])

if __name__ == "__main__":
    unittest.main() 