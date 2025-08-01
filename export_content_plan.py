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
                
                # Format recommendation data - CLEAN EXPORT without metadata
                recommendation_export = {
                    "personal_intelligence": recommendation_data.get('personal_intelligence', {}),
                    "tactical_recommendations": recommendation_data.get('tactical_recommendations', [])
                }
                
                # Include content_intelligence if available in the main content plan
                if 'content_intelligence' in content_plan:
                    recommendation_export['content_intelligence'] = content_plan.get('content_intelligence', {})
                
                # Upload recommendation
                recommendation_result = self.r2_storage.upload_file(
                    key=recommendation_path,
                    file_obj=io.BytesIO(json.dumps(recommendation_export, indent=2).encode('utf-8')),
                    bucket='tasks'
                )
                
                export_results['recommendation'] = recommendation_result
                logger.info(f"Exported recommendation module: {recommendation_path}")
            
            # 2. Export Next Post Prediction - FIXED: Only check top-level location (dedicated module)
            next_post_data = None
            
            # 🚨 CRITICAL FIX: Only use top-level next_post_prediction from dedicated module
            # Recommendation module should NOT contain next_post_prediction to prevent contamination
            if 'next_post_prediction' in content_plan:
                next_post_data = content_plan['next_post_prediction']
                logger.info("✅ Found next_post_prediction at content_plan top level (dedicated module)")
            else:
                logger.warning("⚠️ No next_post_prediction found at top level - dedicated module may have failed")
            
            if next_post_data:
                # Get next file number for next post
                file_num = self._get_next_file_number(base_dirs['next_posts'], "campaign_next_post")
                next_post_path = f"{base_dirs['next_posts']}campaign_next_post_{file_num}.json"
                
                # Format next post data - CLEAN EXPORT without metadata
                next_post_export = next_post_data
                
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
            
            # 3. Export Competitor Analysis – support multiple possible locations
            # Legacy (normal pipeline): recommendation -> threat_assessment -> competitor_analysis
            # Zero-post handler (enhanced): recommendation -> competitive_analysis  OR top-level competitor_analysis
            competitor_analysis = None
            if 'recommendation' in content_plan:
                rec = content_plan['recommendation']
                # Preferred: threat_assessment.competitor_analysis
                if (isinstance(rec, dict) and 'threat_assessment' in rec and 
                    isinstance(rec['threat_assessment'], dict) and 
                    'competitor_analysis' in rec['threat_assessment']):
                    competitor_analysis = rec['threat_assessment']['competitor_analysis']
                # Fallback: competitive_analysis directly under recommendation
                elif 'competitive_analysis' in rec:
                    competitor_analysis = rec['competitive_analysis']
            # Final fallback: competitor_analysis at the root of the content plan
            if competitor_analysis is None and 'competitor_analysis' in content_plan:
                competitor_analysis = content_plan['competitor_analysis']
            
            if competitor_analysis:
                for competitor, analysis in competitor_analysis.items():
                    # Skip non-competitor keys (status messages, limitations, etc.)
                    if competitor.startswith('📋') or competitor in ['status', 'export_note']:
                        logger.info(f"Skipping non-competitor key: {competitor}")
                        continue
                    
                    # Ensure we have a valid competitor username (no special characters at start)
                    if not competitor or not competitor.replace('_', '').replace('-', '').isalnum():
                        logger.warning(f"Skipping invalid competitor key: {competitor}")
                        continue
                    
                    # Create competitor directory: competitor_analysis/platform/primary_username/competitor_username/
                    competitor_dir = f"{base_dirs['competitor_analysis']}{competitor}/"
                    # Get next file number for this competitor
                    file_num = self._get_next_file_number(competitor_dir, "analysis")
                    analysis_path = f"{competitor_dir}analysis_{file_num}.json"
                    
                    # Check if we have enough data for this competitor
                    has_limited_data = False
                    if isinstance(analysis, dict) and len(analysis.keys()) <= 2:
                        has_limited_data = True
                        logger.warning(f"Limited data available for competitor {competitor}")
                    
                    # Format competitor analysis data - CLEAN EXPORT without metadata
                    competitor_export = analysis  # Direct export of analysis data only
                    
                    # Add data availability warning if needed
                    if has_limited_data:
                        if "note" not in competitor_export:
                            competitor_export["note"] = f"{competitor} has limited data available. Analysis may not be comprehensive."
                    
                    # Upload competitor analysis
                    competitor_result = self.r2_storage.upload_file(
                        key=analysis_path,
                        file_obj=io.BytesIO(json.dumps(competitor_export, indent=2).encode('utf-8')),
                        bucket='tasks'
                    )
                    
                    export_results[f'competitor_{competitor}'] = competitor_result
                    logger.info(f"Exported competitor analysis for {competitor}: {analysis_path}")
            
            # 4. Export full content_plan.json for downstream integrity checks
            content_plan_path = f"content_plans/{platform}/{primary_username}/content_plan.json"
            try:
                content_plan_result = self.r2_storage.upload_file(
                    key=content_plan_path,
                    file_obj=io.BytesIO(json.dumps(content_plan, indent=2).encode('utf-8')),
                    bucket='tasks'
                )
                export_results['content_plan'] = content_plan_result
                logger.info(f"Exported master content plan: {content_plan_path}")
            except Exception as e:
                export_results['content_plan'] = False
                logger.error(f"Failed to export master content plan: {str(e)}")
            
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