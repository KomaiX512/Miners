#!/usr/bin/env python3
"""
Export content plan sections according to the new format and structure.
This module handles exporting:
1. Recommendation module (including personal_intelligence, tactical_recommendations, threat_assessment with competitor_analysis)
2. Next post prediction module
3. Competitor analysis modules (one per competitor from within threat_assessment/competitor_analysis)
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
            if not content_plan:
                logger.error("No content plan provided")
                return False
                
            # Get basic info
            platform = content_plan.get('platform', 'instagram').lower()
            primary_username = content_plan.get('primary_username')
            
            if not primary_username:
                logger.error("No primary username found in content plan")
                return False
                
            # Create base directories
            base_dirs = {
                'recommendations': f"recommendations/{platform}/{primary_username}/",
                'next_posts': f"next_posts/{platform}/{primary_username}/",
                'competitor_analysis': f"competitor_analysis/{platform}/{primary_username}/"
            }
            
            # Track export results
            export_results = {}
            
            # 1. Export Recommendation Module
            if 'recommendation' in content_plan:
                recommendation_data = content_plan['recommendation']
                
                # Get next file number for recommendation
                file_num = self._get_next_file_number(base_dirs['recommendations'], "recommendation")
                recommendation_path = f"{base_dirs['recommendations']}recommendation_{file_num}.json"
                
                # Format recommendation data - include personal_intelligence and content_intelligence if available
                recommendation_export = {
                    "module_type": "recommendation",
                    "platform": platform,
                    "primary_username": primary_username,
                    "timestamp": datetime.now().isoformat(),
                    "data": {
                        "personal_intelligence": recommendation_data.get('personal_intelligence', {}),
                        "tactical_recommendations": recommendation_data.get('tactical_recommendations', [])
                    }
                }
                
                # Include content_intelligence if available in the main content plan
                if 'content_intelligence' in content_plan:
                    recommendation_export['data']['content_intelligence'] = content_plan.get('content_intelligence', {})
                
                # Upload recommendation
                recommendation_result = self.r2_storage.upload_file(
                    key=recommendation_path,
                    file_obj=io.BytesIO(json.dumps(recommendation_export, indent=2).encode('utf-8')),
                    bucket='tasks'
                )
                
                export_results['recommendation'] = recommendation_result
                logger.info(f"Exported recommendation module: {recommendation_path}")
            
            # 2. Export Next Post Prediction - FIXED: Check both top-level and nested locations
            next_post_data = None
            
            # First check in recommendation (preferred location)
            if 'recommendation' in content_plan and 'next_post_prediction' in content_plan['recommendation']:
                next_post_data = content_plan['recommendation']['next_post_prediction']
                logger.info("Found next_post_prediction in content_plan['recommendation']")
            
            # If not found, check at top level (alternative location)
            elif 'next_post_prediction' in content_plan:
                next_post_data = content_plan['next_post_prediction']
                logger.info("Found next_post_prediction at content_plan top level")
            
            if next_post_data:
                # Get next file number for next post
                file_num = self._get_next_file_number(base_dirs['next_posts'], "post")
                next_post_path = f"{base_dirs['next_posts']}post_{file_num}.json"
                
                # Format next post data
                next_post_export = {
                    "module_type": "next_post_prediction",
                    "platform": platform,
                    "primary_username": primary_username,
                    "timestamp": datetime.now().isoformat(),
                    "data": next_post_data
                }
                
                # Validate content structure before exporting
                logger.info(f"Next post structure being exported: {json.dumps(next_post_export, indent=2)}")
                
                # Upload next post
                next_post_result = self.r2_storage.upload_file(
                    key=next_post_path,
                    file_obj=io.BytesIO(json.dumps(next_post_export, indent=2).encode('utf-8')),
                    bucket='tasks'
                )
                
                export_results['next_post'] = next_post_result
                logger.info(f"Exported next post prediction: {next_post_path}")
            else:
                logger.warning("No next_post_prediction found in content plan")
            
            # 3. Export Competitor Analysis (from within the recommendation/threat_assessment/competitor_analysis)
            if ('recommendation' in content_plan and 
                'threat_assessment' in content_plan['recommendation'] and 
                'competitor_analysis' in content_plan['recommendation']['threat_assessment']):
                
                competitor_analysis = content_plan['recommendation']['threat_assessment']['competitor_analysis']
                
                for competitor, analysis in competitor_analysis.items():
                    # Create competitor directory
                    competitor_dir = f"{base_dirs['competitor_analysis']}{competitor}/"
                    
                    # Get next file number for this competitor
                    file_num = self._get_next_file_number(competitor_dir, "analysis")
                    analysis_path = f"{competitor_dir}analysis_{file_num}.json"
                    
                    # Check if we have enough data for this competitor
                    has_limited_data = False
                    if isinstance(analysis, dict) and len(analysis.keys()) <= 2:
                        has_limited_data = True
                        logger.warning(f"Limited data available for competitor {competitor}")
                    
                    # Format competitor analysis data
                    competitor_export = {
                        "module_type": "competitor_analysis",
                        "platform": platform,
                        "primary_username": primary_username,
                        "competitor": competitor,
                        "timestamp": datetime.now().isoformat(),
                        "data": analysis
                    }
                    
                    # Add data availability warning if needed
                    if has_limited_data:
                        competitor_export["data_quality"] = "limited"
                        if "note" not in competitor_export["data"]:
                            competitor_export["data"]["note"] = f"{competitor} has limited data available. Analysis may not be comprehensive."
                    
                    # Upload competitor analysis
                    competitor_result = self.r2_storage.upload_file(
                        key=analysis_path,
                        file_obj=io.BytesIO(json.dumps(competitor_export, indent=2).encode('utf-8')),
                        bucket='tasks'
                    )
                    
                    export_results[f'competitor_{competitor}'] = competitor_result
                    logger.info(f"Exported competitor analysis for {competitor}: {analysis_path}")
            
            # Check if all exports were successful
            all_successful = all(export_results.values()) if export_results else False
            if all_successful:
                logger.info("All content plan sections exported successfully")
                return True
            elif not export_results:
                logger.error("No content plan sections were exported")
                return False
            else:
                failed_exports = [k for k, v in export_results.items() if not v]
                logger.error(f"Failed to export sections: {failed_exports}")
                return False
                
        except Exception as e:
            logger.error(f"Error exporting content plan: {str(e)}")
            return False
    
    def _get_next_file_number(self, directory, prefix):
        """Get the next available file number for a given directory and prefix"""
        try:
            # List all files in the directory
            files = self.r2_storage.list_files(directory, bucket='tasks')
            
            # Filter files by prefix
            prefix_files = [f for f in files if f.startswith(f"{directory}{prefix}_")]
            
            if not prefix_files:
                return 1
                
            # Extract numbers from filenames
            numbers = []
            for file in prefix_files:
                try:
                    # Extract number from filename (e.g., "recommendation_1.json" -> 1)
                    num = int(file.split('_')[-1].split('.')[0])
                    numbers.append(num)
                except (ValueError, IndexError):
                    continue
            
            # Return next number
            return max(numbers) + 1 if numbers else 1
            
        except Exception as e:
            logger.error(f"Error getting next file number: {str(e)}")
            return 1  # Default to 1 if there's an error 