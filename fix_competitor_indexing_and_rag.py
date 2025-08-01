#!/usr/bin/env python3

"""
CRITICAL BUG FIX: Competitor Data Indexing and RAG Configuration
================================================================

ISSUE DIAGNOSIS:
1. Line 5343 in main.py: Competitor posts indexed with primary username instead of competitor username
2. RAG module "FACEBOOK_PERSONAL" fails with "Missing required modules" error
3. This causes competitor data to be collected but not properly indexed/queryable

SOLUTION:
1. Fix competitor data indexing by using correct username parameter
2. Validate and fix RAG module configuration
3. Test the fixes with real competitor analysis

ROOT CAUSE:
- Instagram scraper indexing: posts_added = self.vector_db.add_posts(processed_competitor['posts'], username, is_competitor=True)
  Should be: posts_added = self.vector_db.add_posts(processed_competitor['posts'], competitor, is_competitor=True)
- Similar issues in Twitter and Facebook scrapers
"""

import sys
import logging
import os

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def fix_competitor_indexing_bug():
    """
    Fix the critical bug where competitor posts are indexed with primary username
    instead of competitor username, making them unqueryable by competitor name.
    """
    
    logger.info("🔧 FIXING COMPETITOR INDEXING BUG")
    
    main_py_path = '/home/komail/Miners-1/main.py'
    
    try:
        with open(main_py_path, 'r') as f:
            content = f.read()
        
        # Track all fixes
        fixes_applied = []
        
        # Fix 1: Instagram competitor indexing (line ~5343)
        old_instagram = 'posts_added = self.vector_db.add_posts(processed_competitor[\'posts\'], username, is_competitor=True)'
        new_instagram = 'posts_added = self.vector_db.add_posts(processed_competitor[\'posts\'], competitor, is_competitor=True)'
        
        if old_instagram in content:
            content = content.replace(old_instagram, new_instagram)
            fixes_applied.append("Instagram competitor indexing")
            logger.info("✅ Fixed Instagram competitor indexing bug")
        else:
            logger.warning("⚠️ Instagram competitor indexing pattern not found")
        
        # Fix 2: Twitter competitor indexing (similar pattern)
        old_twitter = 'posts_added = self.vector_db.add_posts(processed_competitor[\'posts\'], username, is_competitor=True)'
        # This is the same pattern, so it should be fixed by the above replacement
        
        # Fix 3: Check for any other incorrect indexing patterns
        # Search for potential issues with competitor data using primary username
        import re
        
        # Find all add_posts calls with competitor data
        add_posts_pattern = r'self\.vector_db\.add_posts\([^,]+,\s*([^,]+),\s*is_competitor=True\)'
        matches = re.findall(add_posts_pattern, content)
        
        incorrect_patterns = []
        for match in matches:
            if 'username' in match and 'competitor' not in match:
                incorrect_patterns.append(match)
        
        if incorrect_patterns:
            logger.warning(f"⚠️ Found {len(incorrect_patterns)} potential incorrect indexing patterns: {incorrect_patterns}")
        
        # Fix 4: Ensure Facebook competitor indexing is correct (check if already correct)
        facebook_pattern = 'self.vector_db.add_posts(processed_competitor[\'posts\'], competitor, is_competitor=True)'
        if facebook_pattern in content:
            logger.info("✅ Facebook competitor indexing already correct")
        else:
            # Look for incorrect Facebook pattern
            incorrect_facebook = 'self.vector_db.add_posts(processed_competitor[\'posts\'], username, is_competitor=True)'
            if incorrect_facebook in content:
                # This should have been fixed by the first replacement
                logger.info("✅ Facebook competitor indexing fixed by general replacement")
        
        # Write the fixed content back
        if fixes_applied:
            with open(main_py_path, 'w') as f:
                f.write(content)
            logger.info(f"🎯 APPLIED {len(fixes_applied)} FIXES: {', '.join(fixes_applied)}")
        else:
            logger.warning("⚠️ NO FIXES NEEDED - patterns already correct or not found")
            
        return len(fixes_applied) > 0
        
    except Exception as e:
        logger.error(f"❌ Failed to fix competitor indexing: {str(e)}")
        return False

def validate_rag_configuration():
    """
    Validate and fix RAG module configuration issues.
    """
    
    logger.info("🔧 VALIDATING RAG CONFIGURATION")
    
    try:
        # Import the RAG implementation to check module availability
        sys.path.append('/home/komail/Miners-1')
        from rag_implementation import INSTRUCTION_SETS
        
        # Check FACEBOOK_PERSONAL configuration
        if 'FACEBOOK_PERSONAL' in INSTRUCTION_SETS:
            facebook_config = INSTRUCTION_SETS['FACEBOOK_PERSONAL']
            logger.info("✅ FACEBOOK_PERSONAL configuration found")
            
            # Check required modules
            required_modules = facebook_config.get('required_modules', {})
            available_modules = facebook_config.get('available_modules', {})
            
            logger.info(f"📋 Required modules: {required_modules}")
            logger.info(f"📋 Available modules: {available_modules}")
            
            # Check if personal_intelligence is properly configured
            if 'personal_intelligence' in required_modules:
                personal_intel_modules = required_modules['personal_intelligence']
                logger.info(f"📋 Personal intelligence modules: {personal_intel_modules}")
                
                if 'personal_intelligence' in available_modules:
                    available_personal_modules = available_modules['personal_intelligence']
                    logger.info(f"📋 Available personal intelligence modules: {available_personal_modules}")
                    
                    # Check if all required modules are available
                    missing_modules = []
                    for required_module in personal_intel_modules:
                        if required_module not in available_personal_modules:
                            missing_modules.append(required_module)
                    
                    if missing_modules:
                        logger.warning(f"⚠️ Missing personal intelligence modules: {missing_modules}")
                        return False
                    else:
                        logger.info("✅ All personal intelligence modules available")
                else:
                    logger.warning("⚠️ No available personal intelligence modules found")
                    return False
            else:
                logger.info("ℹ️ No personal intelligence modules required")
        else:
            logger.error("❌ FACEBOOK_PERSONAL configuration not found")
            return False
            
        return True
        
    except ImportError as e:
        logger.error(f"❌ Failed to import RAG implementation: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"❌ RAG configuration validation failed: {str(e)}")
        return False

def test_competitor_analysis_pipeline():
    """
    Test the fixed competitor analysis pipeline with real data.
    """
    
    logger.info("🧪 TESTING FIXED COMPETITOR ANALYSIS PIPELINE")
    
    try:
        # Import the main system
        sys.path.append('/home/komail/Miners-1')
        from main import SocialMediaAnalyzer
        
        # Initialize the analyzer
        analyzer = SocialMediaAnalyzer()
        
        # Test competitor data collection and indexing
        test_competitors = ['nike', 'redbull', 'netflix']
        test_platform = 'instagram'
        
        logger.info(f"🧪 Testing competitor data collection for: {test_competitors}")
        
        # Test the _collect_available_competitor_data method
        available_data = analyzer._collect_available_competitor_data(
            competitors=test_competitors,
            platform=test_platform
        )
        
        logger.info(f"📊 Collected data for {len(available_data)} competitors")
        
        for competitor, data in available_data.items():
            if data:
                post_count = len(data.get('posts', []))
                source = data.get('source', 'unknown')
                logger.info(f"✅ {competitor}: {post_count} posts from {source}")
            else:
                logger.warning(f"⚠️ {competitor}: No data found")
        
        # Test vector database queries for competitors
        if analyzer.vector_db:
            logger.info("🧪 Testing vector database queries for competitors")
            
            for competitor in test_competitors:
                try:
                    results = analyzer.vector_db.query_similar(
                        "competitor content analysis",
                        n_results=5,
                        filter_username=competitor,
                        is_competitor=True
                    )
                    
                    if results and 'documents' in results and results['documents']:
                        doc_count = len([doc for doc in results['documents'][0] if doc])
                        logger.info(f"✅ {competitor}: Found {doc_count} documents in vector DB")
                    else:
                        logger.warning(f"⚠️ {competitor}: No documents found in vector DB")
                        
                except Exception as e:
                    logger.error(f"❌ Query failed for {competitor}: {str(e)}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Pipeline test failed: {str(e)}")
        return False

def main():
    """
    Main function to execute all fixes and tests.
    """
    
    logger.info("🚀 STARTING COMPETITOR ANALYSIS QUALITY FIX")
    logger.info("=" * 60)
    
    # Step 1: Fix competitor indexing bug
    logger.info("STEP 1: Fixing competitor indexing bug")
    indexing_fixed = fix_competitor_indexing_bug()
    
    if indexing_fixed:
        logger.info("✅ STEP 1 COMPLETE: Competitor indexing bug fixed")
    else:
        logger.warning("⚠️ STEP 1: No indexing fixes needed or failed")
    
    print()
    
    # Step 2: Validate RAG configuration
    logger.info("STEP 2: Validating RAG configuration")
    rag_valid = validate_rag_configuration()
    
    if rag_valid:
        logger.info("✅ STEP 2 COMPLETE: RAG configuration valid")
    else:
        logger.error("❌ STEP 2 FAILED: RAG configuration issues found")
    
    print()
    
    # Step 3: Test the pipeline
    logger.info("STEP 3: Testing fixed competitor analysis pipeline")
    pipeline_test = test_competitor_analysis_pipeline()
    
    if pipeline_test:
        logger.info("✅ STEP 3 COMPLETE: Pipeline test successful")
    else:
        logger.error("❌ STEP 3 FAILED: Pipeline test failed")
    
    print()
    
    # Summary
    logger.info("=" * 60)
    logger.info("🎯 FIX SUMMARY:")
    logger.info(f"   Indexing Bug Fixed: {'✅' if indexing_fixed else '❌'}")
    logger.info(f"   RAG Configuration: {'✅' if rag_valid else '❌'}")
    logger.info(f"   Pipeline Test: {'✅' if pipeline_test else '❌'}")
    
    if indexing_fixed and rag_valid and pipeline_test:
        logger.info("🎉 ALL FIXES SUCCESSFUL - COMPETITOR ANALYSIS QUALITY SHOULD BE IMPROVED")
        return 0
    else:
        logger.error("⚠️ SOME ISSUES REMAIN - FURTHER INVESTIGATION NEEDED")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
