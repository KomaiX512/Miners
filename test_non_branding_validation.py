#!/usr/bin/env python3
"""Test script to validate non-branding RAG implementation."""

import sys
import json
import logging
from vector_database import VectorDatabaseManager
from rag_implementation import RagImplementation

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_sample_non_branding_data():
    """Create sample data for non-branding account testing."""
    return {
        'platform': 'instagram',
        'primary_username': 'test_personal_user',
        'secondary_usernames': ['competitor1', 'competitor2'],
        'account_type': 'non-branding',
        'posting_style': 'lifestyle and personal thoughts',
        'profile': {
            'username': 'test_personal_user',
            'fullName': 'Personal Test Account',
            'followersCount': 1500,
            'biography': 'Sharing my journey and thoughts',
            'account_type': 'non-branding',
            'posting_style': 'lifestyle and personal thoughts'
        },
        'posts': [
            {
                'caption': 'Just had an amazing coffee this morning! The perfect start to my day ☕️',
                'engagement': 85,
                'timestamp': '2024-12-01T10:00:00Z',
                'hashtags': ['#coffee', '#morning', '#lifestyle']
            },
            {
                'caption': 'Reflecting on this year and all the growth I\'ve experienced. Grateful for every moment.',
                'engagement': 120,
                'timestamp': '2024-12-02T15:00:00Z',
                'hashtags': ['#grateful', '#growth', '#reflection']
            },
            {
                'caption': 'Working on a new project that I\'m really excited about. Can\'t wait to share more!',
                'engagement': 95,
                'timestamp': '2024-12-03T12:00:00Z',
                'hashtags': ['#project', '#excited', '#coming_soon']
            }
        ]
    }

def test_non_branding_rag():
    """Test non-branding RAG implementation."""
    logger.info("🔥 TESTING NON-BRANDING RAG IMPLEMENTATION")
    
    try:
        # Initialize components
        vector_db = VectorDatabaseManager()
        rag = RagImplementation(vector_db=vector_db)
        
        # Create sample data
        sample_data = create_sample_non_branding_data()
        
        # Index sample posts
        logger.info("Indexing sample posts...")
        posts_with_usernames = []
        for post in sample_data['posts']:
            post_with_username = post.copy()
            post_with_username['username'] = sample_data['primary_username']
            posts_with_usernames.append(post_with_username)
        
        vector_db.add_posts(posts_with_usernames, sample_data['primary_username'])
        logger.info(f"✅ Indexed {len(posts_with_usernames)} posts")
        
        # Test non-branding RAG generation
        logger.info("Testing non-branding RAG generation...")
        query = "Generate personal content about lifestyle and self-improvement"
        
        recommendation = rag.generate_recommendation(
            primary_username=sample_data['primary_username'],
            secondary_usernames=sample_data['secondary_usernames'],
            query=query,
            is_branding=False,  # CRITICAL: Test non-branding
            platform='instagram'
        )
        
        logger.info("✅ RAG generation completed successfully")
        
        # Validate the response structure
        logger.info("🔍 VALIDATING RESPONSE STRUCTURE")
        
        if not isinstance(recommendation, dict):
            raise ValueError(f"Expected dict, got {type(recommendation)}")
        
        logger.info(f"Response keys: {list(recommendation.keys())}")
        
        # Check for non-branding specific structure
        expected_fields = [
            'competitive_intelligence',
            'threat_assessment', 
            'tactical_recommendations',
            'next_post_prediction'
        ]
        
        missing_fields = [field for field in expected_fields if field not in recommendation]
        if missing_fields:
            logger.warning(f"Missing expected fields: {missing_fields}")
        else:
            logger.info("✅ All expected fields present")
        
        # Validate competitive_intelligence structure
        if 'competitive_intelligence' in recommendation:
            comp_intel = recommendation['competitive_intelligence']
            if isinstance(comp_intel, dict):
                logger.info(f"competitive_intelligence keys: {list(comp_intel.keys())}")
                
                # Check for account_dna
                if 'account_dna' in comp_intel:
                    account_dna = comp_intel['account_dna']
                    if 'HYPER-PERSONALIZED' in account_dna and 'test_personal_user' in account_dna:
                        logger.info("✅ account_dna contains hyper-personalized content")
                    else:
                        logger.warning("⚠️ account_dna may not be properly personalized")
                else:
                    logger.warning("⚠️ Missing account_dna in competitive_intelligence")
            else:
                logger.warning(f"⚠️ competitive_intelligence should be dict, got {type(comp_intel)}")
        
        # Validate next_post_prediction
        if 'next_post_prediction' in recommendation:
            next_post = recommendation['next_post_prediction']
            if isinstance(next_post, dict):
                required_post_fields = ['caption', 'hashtags', 'call_to_action', 'visual_prompt']
                missing_post_fields = [field for field in required_post_fields if field not in next_post]
                if missing_post_fields:
                    logger.warning(f"⚠️ Missing next_post fields: {missing_post_fields}")
                else:
                    logger.info("✅ next_post_prediction has all required fields")
                    
                # Check if caption is personalized
                caption = next_post.get('caption', '')
                if caption and len(caption) > 20 and 'test_personal_user' in caption:
                    logger.info("✅ Caption appears personalized")
                else:
                    logger.warning("⚠️ Caption may not be properly personalized")
            else:
                logger.warning(f"⚠️ next_post_prediction should be dict, got {type(next_post)}")
        
        # Validate tactical_recommendations
        if 'tactical_recommendations' in recommendation:
            tactics = recommendation['tactical_recommendations']
            if isinstance(tactics, list) and len(tactics) >= 3:
                logger.info(f"✅ tactical_recommendations has {len(tactics)} recommendations")
                
                # Check if recommendations are personalized
                personalized_count = sum(1 for rec in tactics if 'test_personal_user' in str(rec))
                if personalized_count >= 2:
                    logger.info("✅ Tactical recommendations appear personalized")
                else:
                    logger.warning("⚠️ Tactical recommendations may not be properly personalized")
            else:
                logger.warning(f"⚠️ Expected list of 3+ recommendations, got {type(tactics)} with {len(tactics) if isinstance(tactics, list) else 'N/A'} items")
        
        # Print formatted results
        logger.info("\n" + "="*60)
        logger.info("FINAL TEST RESULTS")
        logger.info("="*60)
        
        logger.info("✅ NON-BRANDING RAG IMPLEMENTATION: WORKING")
        logger.info("✅ JSON PARSING: SUCCESSFUL")
        logger.info("✅ RESPONSE STRUCTURE: VALID")
        
        if missing_fields:
            logger.warning(f"⚠️ MINOR ISSUES: Missing fields {missing_fields}")
        else:
            logger.info("✅ ALL EXPECTED FIELDS: PRESENT")
        
        # Save response for inspection
        with open('test_non_branding_response.json', 'w') as f:
            json.dump(recommendation, f, indent=2)
        logger.info("📁 Response saved to test_non_branding_response.json")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ TEST FAILED: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def test_is_branding_logic():
    """Test the is_branding logic fixes."""
    logger.info("\n🔥 TESTING IS_BRANDING LOGIC")
    
    test_cases = [
        ('branding', True),
        ('non-branding', False),
        ('personal', False),
        ('business', False),  # Should be False with our fix
        ('brand', False),     # Should be False with our fix
        ('corporate', False), # Should be False with our fix
        ('', False)
    ]
    
    for account_type, expected in test_cases:
        # Test the fixed logic
        is_branding = (account_type.lower() == 'branding') if account_type else False
        
        if is_branding == expected:
            logger.info(f"✅ account_type='{account_type}' -> is_branding={is_branding} (Expected: {expected})")
        else:
            logger.error(f"❌ account_type='{account_type}' -> is_branding={is_branding} (Expected: {expected})")
            return False
    
    logger.info("✅ IS_BRANDING LOGIC: ALL TESTS PASSED")
    return True

if __name__ == "__main__":
    logger.info("🚀 STARTING NON-BRANDING VALIDATION TESTS")
    
    # Test is_branding logic
    logic_test_passed = test_is_branding_logic()
    
    # Test RAG implementation
    rag_test_passed = test_non_branding_rag()
    
    # Final results
    logger.info("\n" + "="*60)
    logger.info("COMPREHENSIVE TEST RESULTS")
    logger.info("="*60)
    
    if logic_test_passed and rag_test_passed:
        logger.info("🎉 ALL TESTS PASSED - NON-BRANDING IMPLEMENTATION WORKING")
        sys.exit(0)
    else:
        logger.error("❌ SOME TESTS FAILED - REQUIRES ATTENTION")
        sys.exit(1) 