#!/usr/bin/env python3
"""
BULLETPROOF Pipeline Validation Script
Runs simulations and validates EVERY detail until no issues remain.
Flags any hardcoding, quality issues, or missing modules.
"""

import sys
import os
import json
import logging
from datetime import datetime
import re

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the main system
from main import ContentRecommendationSystem

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class BulletproofValidator:
    def __init__(self):
        """Initialize the bulletproof validator."""
        self.system = ContentRecommendationSystem()
        self.validation_results = {}
        self.issues_found = []
        
    def validate_hashtags_quality(self, hashtags, username):
        """Validate hashtag quality and detect hardcoded patterns."""
        issues = []
        
        if not hashtags or not isinstance(hashtags, list):
            issues.append("Missing or invalid hashtags array")
            return issues
            
        # Check for hardcoded patterns
        hardcoded_patterns = [
            f"#{username.lower()}love",
            f"#{username.lower()}beauty", 
            f"#{username.lower()}style",
            f"#{username}Love",
            f"#{username}Beauty",
            f"#{username}Style"
        ]
        
        for hashtag in hashtags:
            for pattern in hardcoded_patterns:
                if hashtag.lower() == pattern.lower():
                    issues.append(f"HARDCODED HASHTAG DETECTED: {hashtag} (generic pattern)")
                    
        # Check for contextual relevance
        contextual_indicators = [
            "summer", "winter", "spring", "fall", "collection", "new", "trending", 
            "glow", "beauty", "makeup", "skin", "care", "health", "fitness",
            "tech", "ai", "innovation", "research", "science", "data",
            "entertainment", "movie", "show", "series", "film", "content"
        ]
        
        contextual_count = 0
        for hashtag in hashtags:
            if any(indicator in hashtag.lower() for indicator in contextual_indicators):
                contextual_count += 1
                
        if contextual_count == 0 and len(hashtags) > 2:
            issues.append(f"NO CONTEXTUAL HASHTAGS: All hashtags appear generic ({hashtags})")
            
        return issues
    
    def validate_content_quality(self, content_plan):
        """Comprehensive content quality validation."""
        issues = []
        
        # Check next post prediction
        next_post = content_plan.get('next_post_prediction', {})
        if not next_post:
            issues.append("MISSING: next_post_prediction module")
        else:
            # Check caption/tweet_text
            caption = next_post.get('caption') or next_post.get('tweet_text')
            if not caption:
                issues.append("MISSING: next_post caption/tweet_text")
            elif len(caption.strip()) < 10:
                issues.append(f"POOR QUALITY: Caption too short ({len(caption.strip())} chars)")
                
            # Check hashtags
            hashtags = next_post.get('hashtags', [])
            hashtag_issues = self.validate_hashtags_quality(hashtags, content_plan.get('primary_username', ''))
            issues.extend([f"NEXT_POST: {issue}" for issue in hashtag_issues])
            
            # Check image prompt
            if not next_post.get('image_prompt'):
                issues.append("MISSING: next_post image_prompt")
            elif len(next_post.get('image_prompt', '').strip()) < 20:
                issues.append("POOR QUALITY: Image prompt too short")
                
        # Check improvement recommendations
        improvements = content_plan.get('improvement_recommendations', {})
        if not improvements:
            issues.append("MISSING: improvement_recommendations module")
        else:
            recs = improvements.get('recommendations', [])
            if not recs or len(recs) < 3:
                issues.append(f"INSUFFICIENT: Only {len(recs)} recommendations (need at least 3)")
                
            # Check for template/generic recommendations
            for i, rec in enumerate(recs):
                if any(template in rec.lower() for template in ["see some fascinating", "outshine them by", "become the leading voice"]):
                    issues.append(f"TEMPLATE RECOMMENDATION #{i+1}: {rec[:50]}...")
                    
        # Check competitor analysis
        competitor_analysis = content_plan.get('competitor_analysis', {})
        if not competitor_analysis:
            issues.append("MISSING: competitor_analysis module")
        else:
            competitors = content_plan.get('competitors', [])
            if len(competitor_analysis) != len(competitors):
                issues.append(f"MISMATCH: {len(competitor_analysis)} analyzed vs {len(competitors)} competitors listed")
                
            for comp_name, comp_data in competitor_analysis.items():
                if not comp_data.get('overview'):
                    issues.append(f"MISSING: {comp_name} overview")
                if not comp_data.get('strengths'):
                    issues.append(f"MISSING: {comp_name} strengths")
                if not comp_data.get('vulnerabilities'):
                    issues.append(f"MISSING: {comp_name} vulnerabilities")
                    
        # Check main recommendation
        recommendation = content_plan.get('recommendation', {})
        if not recommendation:
            issues.append("MISSING: recommendation module")
        else:
            comp_intel = recommendation.get('competitive_intelligence', {})
            if not comp_intel:
                issues.append("MISSING: competitive_intelligence in recommendation")
                
        return issues
    
    def run_platform_simulation_with_validation(self, platform, username, competitors, max_retries=3):
        """Run simulation with comprehensive validation and retry until perfect."""
        logger.info(f"🔥 BULLETPROOF VALIDATION: {platform.upper()} - {username}")
        logger.info(f"🎯 Competitors: {competitors}")
        logger.info(f"🔄 Max retries: {max_retries}")
        
        for attempt in range(1, max_retries + 1):
            logger.info(f"\n{'='*20} ATTEMPT {attempt}/{max_retries} {'='*20}")
            
            try:
                # Create mock account info
                account_info = {
                    'username': username,
                    'accountType': 'branding',
                    'postingStyle': 'professional',
                    'competitors': competitors,
                    'platform': platform
                }
                
                # Retrieve and process data
                raw_data = None
                if platform == 'twitter':
                    raw_data = self.system.data_retriever.get_twitter_data(username)
                    if raw_data:
                        processed_data = self.system.process_twitter_data(
                            raw_data=raw_data,
                            account_info=account_info,
                            authoritative_primary_username=username
                        )
                elif platform == 'instagram':
                    raw_data = self.system.data_retriever.get_social_media_data(username, platform="instagram")
                    if raw_data:
                        processed_data = self.system.process_instagram_data(
                            raw_data=raw_data,
                            account_info=account_info,
                            authoritative_primary_username=username
                        )
                elif platform == 'facebook':
                    object_key = f"facebook/{username}/{username}.json"
                    raw_data = self.system.data_retriever.get_json_data(object_key)
                    if raw_data:
                        processed_data = self.system.process_facebook_data(
                            raw_data=raw_data,
                            account_info=account_info,
                            authoritative_primary_username=username
                        )
                
                if not raw_data:
                    return self._create_failure_result(platform, username, f"No data found for {username}")
                    
                if not processed_data:
                    return self._create_failure_result(platform, username, f"Data processing failed for {username}")
                
                # Ensure correct data
                processed_data['platform'] = platform
                processed_data['primary_username'] = username
                
                logger.info(f"✅ Data processed: {len(processed_data.get('posts', []))} posts")
                
                # Run pipeline
                result = self.system.run_pipeline(data=processed_data)
                
                if not result:
                    logger.error(f"❌ Pipeline failed on attempt {attempt}")
                    continue
                
                # Read and validate content_plan.json
                try:
                    with open('content_plan.json', 'r') as f:
                        content_plan = json.load(f)
                except Exception as e:
                    logger.error(f"❌ Failed to read content_plan.json: {str(e)}")
                    continue
                
                # Comprehensive validation
                issues = self.validate_content_quality(content_plan)
                
                # Platform-specific validation
                if content_plan.get('platform') != platform:
                    issues.append(f"PLATFORM MISMATCH: Expected {platform}, got {content_plan.get('platform')}")
                    
                if content_plan.get('primary_username') != username:
                    issues.append(f"USERNAME MISMATCH: Expected {username}, got {content_plan.get('primary_username')}")
                    
                competitor_set_match = set(content_plan.get('competitors', [])) == set(competitors)
                if not competitor_set_match:
                    issues.append(f"COMPETITOR MISMATCH: Expected {competitors}, got {content_plan.get('competitors', [])}")
                
                # Log validation results
                if issues:
                    logger.error(f"❌ VALIDATION FAILED ON ATTEMPT {attempt}:")
                    for i, issue in enumerate(issues, 1):
                        logger.error(f"   {i}. {issue}")
                    
                    if attempt < max_retries:
                        logger.warning(f"🔄 RETRYING... ({attempt + 1}/{max_retries})")
                        continue
                    else:
                        logger.error(f"💥 MAX RETRIES REACHED - RETURNING WITH ISSUES")
                        return self._create_failure_result(platform, username, issues)
                else:
                    logger.info(f"🎉 PERFECT! No issues found on attempt {attempt}")
                    return self._create_success_result(platform, username, competitors, content_plan, attempt)
                    
            except Exception as e:
                logger.error(f"❌ Error on attempt {attempt}: {str(e)}")
                if attempt == max_retries:
                    return self._create_failure_result(platform, username, str(e))
                continue
        
        return self._create_failure_result(platform, username, "Max retries exceeded")
    
    def _create_success_result(self, platform, username, competitors, content_plan, attempts_needed):
        """Create a success result structure."""
        next_post = content_plan.get('next_post_prediction', {})
        hashtags = next_post.get('hashtags', [])
        
        return {
            'platform': platform,
            'username': username,
            'competitors': competitors,
            'success': True,
            'attempts_needed': attempts_needed,
            'validation': {
                'overall_status': 'PERFECT',
                'issues_found': [],
                'content_quality': {
                    'next_post_complete': bool(next_post.get('caption') or next_post.get('tweet_text')),
                    'hashtags_count': len(hashtags),
                    'hashtags_contextual': self._check_hashtags_contextual(hashtags, username),
                    'image_prompt_present': bool(next_post.get('image_prompt')),
                    'competitor_analysis_count': len(content_plan.get('competitor_analysis', {})),
                    'recommendations_count': len(content_plan.get('improvement_recommendations', {}).get('recommendations', []))
                }
            },
            'timestamp': datetime.now().isoformat()
        }
    
    def _create_failure_result(self, platform, username, issues):
        """Create a failure result structure."""
        if isinstance(issues, str):
            issues = [issues]
            
        return {
            'platform': platform,
            'username': username,
            'success': False,
            'validation': {
                'overall_status': 'FAILED',
                'issues_found': issues
            },
            'timestamp': datetime.now().isoformat()
        }
    
    def _check_hashtags_contextual(self, hashtags, username):
        """Check if hashtags are contextual rather than hardcoded."""
        if not hashtags:
            return False
            
        hardcoded_patterns = [
            f"#{username.lower()}love",
            f"#{username.lower()}beauty", 
            f"#{username.lower()}style"
        ]
        
        hardcoded_count = 0
        for hashtag in hashtags:
            if any(pattern in hashtag.lower() for pattern in hardcoded_patterns):
                hardcoded_count += 1
                
        # Return True if less than 50% are hardcoded patterns
        return hardcoded_count < len(hashtags) * 0.5
    
    def run_bulletproof_validation(self):
        """Run bulletproof validation for all platforms."""
        logger.info("🔥 STARTING BULLETPROOF VALIDATION")
        logger.info("🎯 ZERO TOLERANCE FOR ISSUES - EVERY DETAIL MUST BE PERFECT")
        logger.info("=" * 80)
        
        test_cases = [
            {
                'platform': 'twitter',
                'username': 'geoffreyhinton', 
                'competitors': ['elonmusk', 'ylecun', 'sama']
            },
            {
                'platform': 'instagram',
                'username': 'fentybeauty',
                'competitors': ['toofaced', 'narsissist', 'maccosmetics']
            },
            {
                'platform': 'facebook',
                'username': 'netflix',
                'competitors': ['cocacola', 'redbull', 'nike']
            }
        ]
        
        all_results = []
        total_attempts = 0
        
        for test_case in test_cases:
            result = self.run_platform_simulation_with_validation(
                platform=test_case['platform'],
                username=test_case['username'],
                competitors=test_case['competitors'],
                max_retries=3
            )
            
            all_results.append(result)
            total_attempts += result.get('attempts_needed', 0)
            
            # Print immediate results
            self._print_platform_result(result)
        
        # Final summary
        self._print_final_summary(all_results, total_attempts)
        
        return all_results
    
    def _print_platform_result(self, result):
        """Print detailed result for one platform."""
        platform = result['platform']
        username = result['username']
        success = result['success']
        
        logger.info(f"\n{'='*60}")
        if success:
            attempts = result.get('attempts_needed', 1)
            quality = result['validation']['content_quality']
            
            logger.info(f"🎉 {platform.upper()} SIMULATION: PERFECT SUCCESS!")
            logger.info(f"   Username: {username}")
            logger.info(f"   Attempts needed: {attempts}")
            logger.info(f"   Next post complete: {quality['next_post_complete']}")
            logger.info(f"   Hashtags count: {quality['hashtags_count']}")
            logger.info(f"   Hashtags contextual: {quality['hashtags_contextual']}")
            logger.info(f"   Image prompt present: {quality['image_prompt_present']}")
            logger.info(f"   Competitors analyzed: {quality['competitor_analysis_count']}")
            logger.info(f"   Recommendations: {quality['recommendations_count']}")
        else:
            issues = result['validation']['issues_found']
            logger.error(f"💥 {platform.upper()} SIMULATION: FAILED")
            logger.error(f"   Username: {username}")
            logger.error(f"   Issues found: {len(issues)}")
            for issue in issues:
                logger.error(f"     • {issue}")
        
        logger.info(f"{'='*60}")
    
    def _print_final_summary(self, all_results, total_attempts):
        """Print comprehensive final summary."""
        successful = [r for r in all_results if r['success']]
        failed = [r for r in all_results if not r['success']]
        
        logger.info(f"\n{'='*80}")
        logger.info(f"🏁 BULLETPROOF VALIDATION COMPLETE")
        logger.info(f"{'='*80}")
        logger.info(f"📊 SUMMARY:")
        logger.info(f"   Total platforms tested: {len(all_results)}")
        logger.info(f"   Successful: {len(successful)}")
        logger.info(f"   Failed: {len(failed)}")
        logger.info(f"   Total attempts needed: {total_attempts}")
        
        if successful:
            logger.info(f"\n✅ SUCCESSFUL PLATFORMS:")
            for result in successful:
                logger.info(f"   • {result['platform'].upper()}: {result['username']}")
        
        if failed:
            logger.error(f"\n❌ FAILED PLATFORMS:")
            for result in failed:
                logger.error(f"   • {result['platform'].upper()}: {result['username']}")
                
        if len(successful) == len(all_results):
            logger.info(f"\n🎉🎉🎉 PERFECT SUCCESS: ALL PLATFORMS WORKING FLAWLESSLY! 🎉🎉🎉")
        else:
            logger.error(f"\n💥 VALIDATION INCOMPLETE: {len(failed)} platforms still have issues")
            
        logger.info(f"{'='*80}")

def main():
    """Main function to run bulletproof validation."""
    logger.info("🔥 Starting Bulletproof Pipeline Validation")
    
    validator = BulletproofValidator()
    results = validator.run_bulletproof_validation()
    
    # Save detailed results
    results_file = f"bulletproof_validation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    logger.info(f"📄 Detailed results saved to: {results_file}")
    
    return results

if __name__ == "__main__":
    main()
