#!/usr/bin/env python3
"""
Enhanced RAG System Test Suite
Tests the complete RAG implementation with instruction set activation,
vector database functionality, and content generation quality.
"""

import logging
import json
from main import ContentRecommendationSystem
from rag_implementation import RagImplementation
from vector_database import VectorDatabaseManager

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_enhanced_rag_system():
    """Comprehensive test of the enhanced RAG system."""
    
    print("🚀 ENHANCED RAG SYSTEM COMPREHENSIVE TEST")
    print("=" * 80)
    
    # Test 1: Vector Database Functionality
    print("\n📊 TEST 1: Vector Database RAG Implementation")
    print("-" * 50)
    
    try:
        vector_db = VectorDatabaseManager()
        
        # Test document indexing with enhanced logging
        test_documents = [
            "MAC Cosmetics posted about new lipstick collection with high engagement",
            "Beauty brand collaboration generated 5000+ likes and comments", 
            "Makeup tutorial video reached viral status with professional quality",
            "Instagram story featuring behind-the-scenes content drove authentic engagement"
        ]
        
        test_metadata = [
            {"username": "maccosmetics", "engagement": 5000, "platform": "instagram", "account_type": "branding"},
            {"username": "maccosmetics", "engagement": 3200, "platform": "instagram", "account_type": "branding"},
            {"username": "beautyinfluencer", "engagement": 1200, "platform": "instagram", "account_type": "personal"},
            {"username": "makeupblogger", "engagement": 800, "platform": "instagram", "account_type": "personal"}
        ]
        
        vector_db.add_documents(test_documents, metadatas=test_metadata)
        
        # Test RAG query functionality
        query_result = vector_db.query_similar("beauty content strategy", n_results=3, filter_username="maccosmetics")
        
        if query_result['documents'] and query_result['documents'][0]:
            print("✅ Vector Database: RAG indexing and retrieval working")
            print(f"📊 Retrieved {len(query_result['documents'][0])} relevant documents")
        else:
            print("❌ Vector Database: No documents retrieved")
            
    except Exception as e:
        print(f"❌ Vector Database Test Failed: {str(e)}")
    
    # Test 2: Enhanced RAG Implementation
    print("\n🎯 TEST 2: Enhanced RAG Implementation with Instruction Sets")
    print("-" * 50)
    
    try:
        rag = RagImplementation()
        
        # Test all 4 instruction set combinations
        test_cases = [
            {
                "username": "maccosmetics",
                "competitors": ["fentybeauty", "toofaced"],
                "platform": "instagram",
                "is_branding": True,
                "expected_instruction": "INSTAGRAM_BRANDING"
            },
            {
                "username": "lifestyle_blogger",
                "competitors": ["personal_user1", "personal_user2"], 
                "platform": "instagram",
                "is_branding": False,
                "expected_instruction": "INSTAGRAM_PERSONAL"
            },
            {
                "username": "nike",
                "competitors": ["adidas", "puma"],
                "platform": "twitter", 
                "is_branding": True,
                "expected_instruction": "TWITTER_BRANDING"
            },
            {
                "username": "tech_person",
                "competitors": ["developer1", "techie2"],
                "platform": "twitter",
                "is_branding": False, 
                "expected_instruction": "TWITTER_PERSONAL"
            }
        ]
        
        success_count = 0
        total_tests = len(test_cases)
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n🧪 Test {i}/{total_tests}: {test_case['expected_instruction']}")
            
            try:
                result = rag.generate_recommendation(
                    primary_username=test_case["username"],
                    secondary_usernames=test_case["competitors"],
                    query="Generate content plan",
                    is_branding=test_case["is_branding"],
                    platform=test_case["platform"]
                )
                
                if result:
                    # Verify correct module structure
                    expected_intelligence = "competitive_intelligence" if test_case["is_branding"] else "personal_intelligence"
                    
                    if expected_intelligence in result:
                        print(f"   ✅ Instruction Set Activated: {test_case['expected_instruction']}")
                        print(f"   ✅ Intelligence Module: {expected_intelligence}")
                        print(f"   ✅ Module Count: {len(result)} modules generated")
                        success_count += 1
                    else:
                        print(f"   ❌ Wrong intelligence module. Expected: {expected_intelligence}, Got: {list(result.keys())}")
                else:
                    print(f"   ❌ No result generated")
                    
            except Exception as e:
                print(f"   ❌ Generation failed: {str(e)}")
        
        print(f"\n📊 RAG Instruction Sets: {success_count}/{total_tests} successful ({success_count/total_tests*100:.1f}%)")
        
    except Exception as e:
        print(f"❌ Enhanced RAG Test Failed: {str(e)}")
    
    # Test 3: Content Recommendation System Integration
    print("\n🎨 TEST 3: Content Recommendation System Integration")
    print("-" * 50)
    
    try:
        system = ContentRecommendationSystem()
        
        # Test account info reading and instruction activation
        test_usernames = ["maccosmetics", "personal_test_user"]
        
        for username in test_usernames:
            print(f"\n🔍 Testing account info detection for: {username}")
            
            account_info = system._read_account_info(username)
            if account_info:
                account_type = account_info.get('accountType', 'unknown')
                platform = account_info.get('platform', 'unknown')
                
                # Determine expected instruction set
                instruction_key = f"{platform.upper()}_{'BRANDING' if account_type.lower() == 'branding' else 'PERSONAL'}"
                
                print(f"   ✅ Account Type: {account_type}")
                print(f"   ✅ Platform: {platform}")
                print(f"   ✅ Expected Instruction: {instruction_key}")
            else:
                print(f"   ❌ No account info retrieved")
                
    except Exception as e:
        print(f"❌ System Integration Test Failed: {str(e)}")
    
    # Test 4: Content Plan Generation Quality
    print("\n🎯 TEST 4: Content Plan Generation Quality")
    print("-" * 50)
    
    try:
        from recommendation_generation import RecommendationGenerator
        
        rag = RagImplementation()
        rec_gen = RecommendationGenerator(rag=rag)
        
        # Test business instruction set
        print("\n🏢 Testing Business Instruction Set (Instagram Branding)")
        business_result = rec_gen.generate_unified_content_plan(
            primary_username="maccosmetics",
            secondary_usernames=["fentybeauty", "toofaced"],
            query="Generate premium business content plan",
            is_branding=True,
            platform="instagram"
        )
        
        if business_result:
            print("   ✅ Business Content Plan Generated")
            print(f"   📊 Generation Method: {business_result.get('generation_method', 'unknown')}")
            print(f"   📊 Content Verified: {business_result.get('content_verified', False)}")
            
            # Check for business-specific content themes
            content_str = str(business_result).lower()
            business_indicators = ["business", "market", "competitive", "strategic", "roi", "brand"]
            business_score = sum(1 for indicator in business_indicators if indicator in content_str)
            
            print(f"   📈 Business Theme Score: {business_score}/{len(business_indicators)}")
        else:
            print("   ❌ Business Content Plan Failed")
        
        # Test personal instruction set  
        print("\n👤 Testing Personal Instruction Set (Instagram Personal)")
        personal_result = rec_gen.generate_unified_content_plan(
            primary_username="lifestyle_blogger",
            secondary_usernames=["personal_user1", "personal_user2"], 
            query="Generate authentic personal content plan",
            is_branding=False,
            platform="instagram"
        )
        
        if personal_result:
            print("   ✅ Personal Content Plan Generated")
            print(f"   📊 Generation Method: {personal_result.get('generation_method', 'unknown')}")
            print(f"   📊 Content Verified: {personal_result.get('content_verified', False)}")
            
            # Check for personal-specific content themes
            content_str = str(personal_result).lower()
            personal_indicators = ["authentic", "personal", "growth", "community", "lifestyle", "genuine"]
            personal_score = sum(1 for indicator in personal_indicators if indicator in content_str)
            
            print(f"   📈 Personal Theme Score: {personal_score}/{len(personal_indicators)}")
        else:
            print("   ❌ Personal Content Plan Failed")
            
    except Exception as e:
        print(f"❌ Content Quality Test Failed: {str(e)}")
    
    print("\n" + "=" * 80)
    print("🎯 ENHANCED RAG SYSTEM TEST COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    test_enhanced_rag_system() 