#!/usr/bin/env python3
"""
Export content plan sections according to the new format and structure.
This module handles exporting:
1. Recommendation module (including competitive_intelligence, tactical_recommendations, threat_assessment)
2. Next post prediction module
3. Competitor analysis modules (one per competitor)
"""

import json
import os
import logging
import io
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('export_content_plan')

class ContentPlanExporter:
    def __init__(self, r2_storage):
        """Initialize the exporter with R2 storage instance"""
        self.r2_storage = r2_storage
        
    def export_content_plan(self, content_plan):
        """Export content plan sections according to the new format"""
        try:
            # Extract key information
            primary_username = content_plan.get('primary_username')
            platform = content_plan.get('platform')
            
            if not primary_username or not platform:
                logger.error("Missing required fields: primary_username or platform")
                return False
                
            # Create base directories
            base_dirs = {
                'recommendations': f"recommendations/{platform}/{primary_username}/",
                'next_post': f"next_post/{platform}/{primary_username}/",
                'competitor_analysis': f"competitor_analysis/{platform}/{primary_username}/"
            }
            
            # Ensure directories exist
            for directory in base_dirs.values():
                self._ensure_directory_exists(directory)
            
            # Track export results
            export_results = {}
            
            # 1. Export Recommendation Module
            if 'recommendation' in content_plan:
                recommendation_data = content_plan['recommendation']
                
                # Get next file number for recommendation
                file_num = self._get_next_file_number(base_dirs['recommendations'], "recommendation")
                recommendation_path = f"{base_dirs['recommendations']}recommendation_{file_num}.json"
                
                # Format recommendation data
                recommendation_export = {
                    "module_type": "recommendation",
                    "platform": platform,
                    "primary_username": primary_username,
                    "timestamp": datetime.now().isoformat(),
                    "data": {
                        "competitive_intelligence": recommendation_data.get('competitive_intelligence', {}),
                        "tactical_recommendations": recommendation_data.get('tactical_recommendations', []),
                        "threat_assessment": recommendation_data.get('threat_assessment', {})
                    }
                }
                
                # Upload recommendation
                recommendation_result = self.r2_storage.upload_file(
                    key=recommendation_path,
                    file_obj=io.BytesIO(json.dumps(recommendation_export, indent=2).encode('utf-8')),
                    bucket='tasks'
                )
                
                export_results['recommendation'] = recommendation_result
                logger.info(f"Exported recommendation module: {recommendation_path}")
            
            # 2. Export Next Post Prediction
            if 'next_post_prediction' in content_plan:
                next_post_data = content_plan['next_post_prediction']
                
                # Get next file number for next post
                file_num = self._get_next_file_number(base_dirs['next_post'], "post")
                next_post_path = f"{base_dirs['next_post']}post_{file_num}.json"
                
                # Format next post data
                next_post_export = {
                    "module_type": "next_post_prediction",
                    "platform": platform,
                    "primary_username": primary_username,
                    "timestamp": datetime.now().isoformat(),
                    "data": next_post_data
                }
                
                # Upload next post
                next_post_result = self.r2_storage.upload_file(
                    key=next_post_path,
                    file_obj=io.BytesIO(json.dumps(next_post_export, indent=2).encode('utf-8')),
                    bucket='tasks'
                )
                
                export_results['next_post'] = next_post_result
                logger.info(f"Exported next post prediction: {next_post_path}")
            
            # 3. Export Competitor Analysis Modules
            if ('recommendation' in content_plan and 
                'threat_assessment' in content_plan['recommendation'] and
                'competitor_analysis' in content_plan['recommendation']['threat_assessment']):
                
                competitor_analysis = content_plan['recommendation']['threat_assessment']['competitor_analysis']
                
                for competitor, analysis in competitor_analysis.items():
                    # Create competitor directory
                    competitor_dir = f"{base_dirs['competitor_analysis']}{competitor}/"
                    self._ensure_directory_exists(competitor_dir)
                    
                    # Get next file number for competitor analysis
                    file_num = self._get_next_file_number(f"competitor_analysis/{platform}", f"{primary_username}/{competitor}", "analysis")
                    analysis_path = f"{competitor_dir}analysis_{file_num}.json"
                    
                    # Format competitor analysis data
                    competitor_export = {
                        "module_type": "competitor_analysis",
                        "platform": platform,
                        "primary_username": primary_username,
                        "competitor_username": competitor,
                        "timestamp": datetime.now().isoformat(),
                        "data": analysis
                    }
                    
                    # Upload competitor analysis
                    competitor_result = self.r2_storage.upload_file(
                        key=analysis_path,
                        file_obj=io.BytesIO(json.dumps(competitor_export, indent=2).encode('utf-8')),
                        bucket='tasks'
                    )
                    
                    if 'competitor_analysis' not in export_results:
                        export_results['competitor_analysis'] = {}
                    export_results['competitor_analysis'][competitor] = competitor_result
                    
                    logger.info(f"Exported competitor analysis for {competitor}: {analysis_path}")
            
            logger.info("✅ Successfully exported all content plan sections")
            return export_results
            
        except Exception as e:
            logger.error(f"Error exporting content plan: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return False
    
    def _ensure_directory_exists(self, directory):
        """Ensure a directory exists in R2 storage"""
        try:
            # Create a dummy file to ensure directory exists
            dummy_path = f"{directory}.keep"
            self.r2_storage.upload_file(
                key=dummy_path,
                file_obj=io.BytesIO(b""),
                bucket='tasks'
            )
            return True
        except Exception as e:
            logger.error(f"Error ensuring directory exists: {str(e)}")
            return False
    
    def _get_next_file_number(self, base_path, username, prefix):
        """Get the next available file number for a given path and prefix"""
        try:
            # List existing files
            existing_files = self.r2_storage.list_files(
                prefix=f"{base_path}/{username}/{prefix}_",
                bucket='tasks'
            )
            
            # Extract numbers from existing files
            numbers = []
            for file in existing_files:
                try:
                    # Extract number from filename (e.g., "recommendation_1.json" -> 1)
                    num = int(file.split('_')[-1].split('.')[0])
                    numbers.append(num)
                except (ValueError, IndexError):
                    continue
            
            # Return next available number
            return max(numbers) + 1 if numbers else 1
            
        except Exception as e:
            logger.error(f"Error getting next file number: {str(e)}")
            return 1  # Default to 1 if there's an error 