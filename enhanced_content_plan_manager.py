#!/usr/bin/env python3
"""
Enhanced Content Plan Manager
This module provides comprehensive content plan management with:
1. Automatic content plan saving and updating
2. Verification of generated content
3. Export tracking and validation
4. Backup and recovery capabilities
"""

import json
import os
import logging
import shutil
from datetime import datetime
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('enhanced_content_plan_manager')

class EnhancedContentPlanManager:
    def __init__(self, base_filename='content_plan.json'):
        """Initialize the enhanced content plan manager."""
        self.base_filename = base_filename
        self.backup_dir = 'content_plan_backups'
        self.ensure_backup_directory()
        
    def ensure_backup_directory(self):
        """Ensure the backup directory exists."""
        Path(self.backup_dir).mkdir(exist_ok=True)
        
    def save_content_plan_with_verification(self, content_plan, filename=None):
        """Save content plan with comprehensive verification and backup."""
        if filename is None:
            filename = self.base_filename
            
        try:
            logger.info(f"💾 Enhanced content plan save: {filename}")
            
            # Create backup before overwriting
            self._create_backup(filename)
            
            # Validate content plan structure
            validation_result = self._validate_content_plan(content_plan)
            if not validation_result['valid']:
                logger.error(f"❌ Content plan validation failed: {validation_result['errors']}")
                return False
                
            # Save the content plan
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(content_plan, f, indent=2, ensure_ascii=False)
                
            logger.info(f"✅ Successfully saved content plan to {filename}")
            
            # Verify the saved file
            verification_result = self._verify_saved_file(filename, content_plan)
            if not verification_result['verified']:
                logger.error(f"❌ File verification failed: {verification_result['errors']}")
                return False
                
            # Generate comprehensive summary
            summary = self._generate_content_summary(content_plan)
            logger.info(f"📊 Content Plan Summary: {json.dumps(summary, indent=2)}")
            
            # Create verification report
            self._create_verification_report(content_plan, filename)
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error saving content plan: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return False
            
    def _create_backup(self, filename):
        """Create a backup of the existing file."""
        if os.path.exists(filename):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"{self.backup_dir}/content_plan_backup_{timestamp}.json"
            shutil.copy2(filename, backup_filename)
            logger.info(f"📦 Created backup: {backup_filename}")
            
    def _validate_content_plan(self, content_plan):
        """Validate the content plan structure."""
        errors = []
        required_fields = ['primary_username', 'platform', 'timestamp']
        
        # Check required fields
        for field in required_fields:
            if field not in content_plan:
                errors.append(f"Missing required field: {field}")
                
        # Check data types
        if 'primary_username' in content_plan and not isinstance(content_plan['primary_username'], str):
            errors.append("primary_username must be a string")
            
        if 'platform' in content_plan and not isinstance(content_plan['platform'], str):
            errors.append("platform must be a string")
            
        # Check for JSON serializable content
        try:
            json.dumps(content_plan)
        except (TypeError, ValueError) as e:
            errors.append(f"Content not JSON serializable: {str(e)}")
            
        return {
            'valid': len(errors) == 0,
            'errors': errors
        }
        
    def _verify_saved_file(self, filename, original_content):
        """Verify that the saved file matches the original content."""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                saved_content = json.load(f)
                
            # Check if all keys from original are in saved
            for key in original_content:
                if key not in saved_content:
                    return {
                        'verified': False,
                        'errors': [f"Missing key in saved file: {key}"]
                    }
                    
            # Check file size is reasonable
            file_size = os.path.getsize(filename)
            if file_size < 100:  # Too small
                return {
                    'verified': False,
                    'errors': [f"File too small: {file_size} bytes"]
                }
                
            return {'verified': True, 'errors': []}
            
        except Exception as e:
            return {
                'verified': False,
                'errors': [f"Error reading saved file: {str(e)}"]
            }
            
    def _generate_content_summary(self, content_plan):
        """Generate a comprehensive content summary."""
        summary = {
            'timestamp': datetime.now().isoformat(),
            'file_updated': True,
            'content_analysis': {}
        }
        
        # Analyze recommendations
        recommendations_count = 0
        if 'recommendation' in content_plan:
            rec = content_plan['recommendation']
            if isinstance(rec, dict):
                if 'tactical_recommendations' in rec and isinstance(rec['tactical_recommendations'], list):
                    recommendations_count = len(rec['tactical_recommendations'])
                    
        summary['content_analysis']['recommendations_count'] = recommendations_count
        
        # Analyze next post
        next_post_included = 'next_post_prediction' in content_plan
        summary['content_analysis']['next_post_included'] = next_post_included
        
        if next_post_included:
            next_post = content_plan['next_post_prediction']
            if isinstance(next_post, dict):
                summary['content_analysis']['next_post_has_text'] = 'tweet_text' in next_post or 'caption' in next_post
                summary['content_analysis']['next_post_has_hashtags'] = 'hashtags' in next_post
                
        # Analyze competitor analysis
        competitor_count = 0
        if 'competitor_analysis' in content_plan:
            comp_analysis = content_plan['competitor_analysis']
            if isinstance(comp_analysis, dict):
                competitor_count = len(comp_analysis)
                
        summary['content_analysis']['competitor_analysis_count'] = competitor_count
        
        # Basic info
        summary['content_analysis']['username'] = content_plan.get('primary_username', 'unknown')
        summary['content_analysis']['platform'] = content_plan.get('platform', 'unknown')
        summary['content_analysis']['account_type'] = content_plan.get('account_type', 'unknown')
        
        return summary
        
    def _create_verification_report(self, content_plan, filename):
        """Create a detailed verification report."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_filename = f"{self.backup_dir}/verification_report_{timestamp}.json"
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'filename': filename,
            'file_size': os.path.getsize(filename) if os.path.exists(filename) else 0,
            'content_plan_keys': list(content_plan.keys()),
            'summary': self._generate_content_summary(content_plan),
            'validation': self._validate_content_plan(content_plan)
        }
        
        with open(report_filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)
            
        logger.info(f"📋 Created verification report: {report_filename}")
        
    def load_content_plan(self, filename=None):
        """Load content plan with error handling."""
        if filename is None:
            filename = self.base_filename
            
        try:
            if not os.path.exists(filename):
                logger.warning(f"Content plan file {filename} not found")
                return None
                
            with open(filename, 'r', encoding='utf-8') as f:
                content_plan = json.load(f)
                
            logger.info(f"✅ Successfully loaded content plan from {filename}")
            return content_plan
            
        except Exception as e:
            logger.error(f"❌ Error loading content plan: {str(e)}")
            return None
            
    def get_content_plan_status(self, filename=None):
        """Get the current status of the content plan file."""
        if filename is None:
            filename = self.base_filename
            
        status = {
            'file_exists': os.path.exists(filename),
            'filename': filename,
            'timestamp': None,
            'file_size': 0,
            'is_valid_json': False,
            'content_summary': None
        }
        
        if status['file_exists']:
            # Get file info
            stat = os.stat(filename)
            status['timestamp'] = datetime.fromtimestamp(stat.st_mtime).isoformat()
            status['file_size'] = stat.st_size
            
            # Check if valid JSON
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    content_plan = json.load(f)
                status['is_valid_json'] = True
                status['content_summary'] = self._generate_content_summary(content_plan)
            except Exception as e:
                status['json_error'] = str(e)
                
        return status
        
    def list_backups(self):
        """List all available backups."""
        if not os.path.exists(self.backup_dir):
            return []
            
        backups = []
        for file in os.listdir(self.backup_dir):
            if file.startswith('content_plan_backup_') and file.endswith('.json'):
                file_path = os.path.join(self.backup_dir, file)
                stat = os.stat(file_path)
                backups.append({
                    'filename': file,
                    'path': file_path,
                    'timestamp': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    'size': stat.st_size
                })
                
        return sorted(backups, key=lambda x: x['timestamp'], reverse=True)
        
    def restore_from_backup(self, backup_filename):
        """Restore content plan from a backup."""
        backup_path = os.path.join(self.backup_dir, backup_filename)
        
        if not os.path.exists(backup_path):
            logger.error(f"Backup file not found: {backup_path}")
            return False
            
        try:
            # Create backup of current file
            if os.path.exists(self.base_filename):
                self._create_backup(self.base_filename)
                
            # Restore from backup
            shutil.copy2(backup_path, self.base_filename)
            logger.info(f"✅ Restored content plan from backup: {backup_filename}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error restoring from backup: {str(e)}")
            return False

def test_enhanced_content_plan_manager():
    """Test the enhanced content plan manager."""
    logger.info("🧪 Testing Enhanced Content Plan Manager...")
    
    manager = EnhancedContentPlanManager()
    
    # Test 1: Create a test content plan
    test_content_plan = {
        "primary_username": "testuser",
        "platform": "twitter",
        "timestamp": datetime.now().isoformat(),
        "account_type": "personal",
        "posting_style": "casual",
        "total_posts_analyzed": 10,
        "competitors": ["competitor1", "competitor2"],
        "recommendation": {
            "personal_intelligence": {
                "account_analysis": "Test account analysis",
                "content_strategy": "Test content strategy"
            },
            "tactical_recommendations": [
                "Test recommendation 1",
                "Test recommendation 2"
            ]
        },
        "next_post_prediction": {
            "tweet_text": "Test tweet content",
            "hashtags": ["#Test", "#Content"],
            "call_to_action": "Test CTA"
        },
        "competitor_analysis": {
            "competitor1": {
                "overview": "Test competitor overview",
                "strengths": ["Test strength"],
                "vulnerabilities": ["Test vulnerability"]
            }
        }
    }
    
    # Test 2: Save with enhanced manager
    save_result = manager.save_content_plan_with_verification(test_content_plan, 'test_enhanced_content_plan.json')
    
    if save_result:
        logger.info("✅ Enhanced save successful")
        
        # Test 3: Check status
        status = manager.get_content_plan_status('test_enhanced_content_plan.json')
        logger.info(f"📊 Status: {json.dumps(status, indent=2)}")
        
        # Test 4: List backups
        backups = manager.list_backups()
        logger.info(f"📦 Found {len(backups)} backups")
        
        # Clean up
        if os.path.exists('test_enhanced_content_plan.json'):
            os.remove('test_enhanced_content_plan.json')
            
        return True
    else:
        logger.error("❌ Enhanced save failed")
        return False

if __name__ == "__main__":
    test_enhanced_content_plan_manager() 