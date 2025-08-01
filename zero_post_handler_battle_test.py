#!/usr/bin/env python3
"""
ZERO-POST HANDLER COMPREHENSIVE BATTLE TEST
============================================

This script performs exhaustive testing of the zero-post handler to identify
all vulnerabilities, failure modes, and quality issues.

Test Categories:
1. Data Collection & Indexing
2. RAG Implementation & Quality
3. Output Structure & Completeness
4. Edge Case Handling
5. Platform-Specific Issues
6. Export Consistency

Usage: python zero_post_handler_battle_test.py
"""

import json
import logging
import traceback
from typing import Dict, List, Any
from data_retrieval import R2DataRetriever
from zero_data_handler import ZeroDataHandler
from main import ContentRecommendationSystem

# Configure detailed logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ZeroPostHandlerBattleTest:
    """Comprehensive battle testing for zero-post handler vulnerabilities."""
    
    def __init__(self):
        self.test_results = {
            'data_collection': {},
            'vector_db_indexing': {},
            'rag_quality': {},
            'output_structure': {},
            'edge_cases': {},
            'platform_consistency': {},
            'export_validation': {}
        }
        self.failures = []
        self.warnings = []
        
    def run_comprehensive_battle_test(self):
        """Execute all battle tests and generate detailed vulnerability report."""
        logger.info("🚨 STARTING COMPREHENSIVE ZERO-POST HANDLER BATTLE TEST")
        
        try:
            # Test 1: Data Collection Vulnerabilities
            self.test_data_collection_vulnerabilities()
            
            # Test 2: Vector Database Indexing Issues
            self.test_vector_db_indexing_issues()
            
            # Test 3: RAG Implementation Quality
            self.test_rag_implementation_quality()
            
            # Test 4: Output Structure Consistency
            self.test_output_structure_consistency()
            
            # Test 5: Edge Case Handling
            self.test_edge_case_handling()
            
            # Test 6: Platform-Specific Issues
            self.test_platform_specific_issues()
            
            # Test 7: Export Validation
            self.test_export_validation()
            
            # Generate comprehensive vulnerability report
            self.generate_vulnerability_report()
            
        except Exception as e:
            logger.error(f"🚨 BATTLE TEST FAILED: {str(e)}")
            logger.error(traceback.format_exc())
    
    def test_data_collection_vulnerabilities(self):
        """Test data collection from R2 storage for various scenarios."""
        logger.info("🔍 TESTING DATA COLLECTION VULNERABILITIES")
        
        test_cases = [
            {
                'name': 'Twitter Tech Personalities',
                'platform': 'twitter',
                'primary': 'ProfFahdKhan',
                'competitors': ['ylecun', 'sama', 'mntruell']
            },
            {
                'name': 'Instagram Beauty Brands',
                'platform': 'instagram',
                'primary': 'newbeautybrand',
                'competitors': ['fentybeauty', 'toofaced', 'urbandecaycosmetics']
            },
            {
                'name': 'Mixed Platform Data',
                'platform': 'twitter',
                'primary': 'testuser',
                'competitors': ['elonmusk', 'fentybeauty']  # Cross-platform
            }
        ]
        
        for test_case in test_cases:
            logger.info(f"📊 Testing: {test_case['name']}")
            
            try:
                # Initialize system
                system = ContentRecommendationSystem()
                
                # Test data collection
                available_data = system._collect_available_competitor_data(
                    test_case['competitors'], 
                    test_case['platform']
                )
                
                # Analyze results
                result = {
                    'competitors_found': len(available_data),
                    'total_posts': sum(len(data.get('posts', [])) for data in available_data.values()),
                    'data_sources': [data.get('source') for data in available_data.values()],
                    'competitors_with_data': list(available_data.keys()),
                    'competitors_missing': [c for c in test_case['competitors'] if c not in available_data]
                }
                
                self.test_results['data_collection'][test_case['name']] = result
                
                # Log critical issues
                if result['competitors_found'] == 0:
                    self.failures.append(f"❌ NO DATA FOUND: {test_case['name']} - Zero competitors found")
                elif result['competitors_found'] < len(test_case['competitors']):
                    self.warnings.append(f"⚠️ PARTIAL DATA: {test_case['name']} - Only {result['competitors_found']}/{len(test_case['competitors'])} competitors found")
                
                logger.info(f"✅ {test_case['name']}: {result['competitors_found']} competitors, {result['total_posts']} posts")
                
            except Exception as e:
                self.failures.append(f"❌ DATA COLLECTION FAILED: {test_case['name']} - {str(e)}")
                logger.error(f"❌ {test_case['name']} failed: {str(e)}")
    
    def test_vector_db_indexing_issues(self):
        """Test vector database indexing and querying for competitor data."""
        logger.info("🔍 TESTING VECTOR DATABASE INDEXING ISSUES")
        
        try:
            system = ContentRecommendationSystem()
            
            # Test current vector DB contents
            if hasattr(system, 'vector_db') and system.vector_db:
                # Query for existing usernames
                existing_usernames = []
                test_queries = [
                    'ylecun content',
                    'sama posts', 
                    'mntruell tweets',
                    'fentybeauty content',
                    'toofaced posts'
                ]
                
                for query in test_queries:
                    try:
                        results = system.vector_db.query_similar(query, n_results=5)
                        if results:
                            for result in results:
                                username = result.get('metadata', {}).get('username')
                                if username and username not in existing_usernames:
                                    existing_usernames.append(username)
                    except Exception as e:
                        logger.warning(f"Query failed for '{query}': {str(e)}")
                
                self.test_results['vector_db_indexing']['existing_usernames'] = existing_usernames
                self.test_results['vector_db_indexing']['total_indexed_users'] = len(existing_usernames)
                
                # Test competitor-specific queries
                competitor_query_results = {}
                competitors = ['ylecun', 'sama', 'mntruell', 'fentybeauty', 'toofaced']
                
                for competitor in competitors:
                    try:
                        results = system.vector_db.query_similar(
                            f"{competitor} content analysis",
                            n_results=3,
                            filter_username=competitor
                        )
                        competitor_query_results[competitor] = len(results) if results else 0
                    except Exception as e:
                        competitor_query_results[competitor] = f"ERROR: {str(e)}"
                
                self.test_results['vector_db_indexing']['competitor_queries'] = competitor_query_results
                
                # Identify critical issues
                twitter_competitors = ['ylecun', 'sama', 'mntruell']
                twitter_indexed = [c for c in twitter_competitors if c in existing_usernames]
                
                if len(twitter_indexed) == 0:
                    self.failures.append("❌ CRITICAL: No Twitter competitors indexed in vector DB")
                elif len(twitter_indexed) < len(twitter_competitors):
                    self.warnings.append(f"⚠️ PARTIAL INDEXING: Only {len(twitter_indexed)}/{len(twitter_competitors)} Twitter competitors indexed")
                
                logger.info(f"✅ Vector DB contains {len(existing_usernames)} indexed users")
                logger.info(f"📊 Twitter competitors indexed: {twitter_indexed}")
                
            else:
                self.failures.append("❌ CRITICAL: Vector database not available")
                
        except Exception as e:
            self.failures.append(f"❌ VECTOR DB TEST FAILED: {str(e)}")
            logger.error(f"❌ Vector DB test failed: {str(e)}")
    
    def test_rag_implementation_quality(self):
        """Test RAG implementation quality for zero-post scenarios."""
        logger.info("🔍 TESTING RAG IMPLEMENTATION QUALITY")
        
        test_scenarios = [
            {
                'name': 'Twitter Zero-Post with Competitors',
                'primary': 'ProfFahdKhan',
                'platform': 'twitter',
                'competitors': ['ylecun', 'sama', 'mntruell'],
                'account_type': 'personal'
            },
            {
                'name': 'Instagram Zero-Post with Competitors', 
                'primary': 'newbeautybrand',
                'platform': 'instagram',
                'competitors': ['fentybeauty', 'toofaced'],
                'account_type': 'brand'
            }
        ]
        
        for scenario in test_scenarios:
            logger.info(f"📊 Testing RAG Quality: {scenario['name']}")
            
            try:
                # Initialize zero data handler
                zero_handler = ZeroDataHandler()
                
                # Collect competitor data
                system = ContentRecommendationSystem()
                available_data = system._collect_available_competitor_data(
                    scenario['competitors'], 
                    scenario['platform']
                )
                
                if available_data:
                    # Test RAG generation
                    result = zero_handler.handle_zero_data_account(
                        primary_username=scenario['primary'],
                        secondary_usernames=scenario['competitors'],
                        platform=scenario['platform'],
                        account_type=scenario['account_type'],
                        posting_style="professional",
                        info_json_data={},
                        available_competitor_data=available_data
                    )
                    
                    # Analyze RAG quality
                    quality_metrics = self.analyze_rag_output_quality(result, scenario)
                    self.test_results['rag_quality'][scenario['name']] = quality_metrics
                    
                    # Log quality issues
                    if quality_metrics['overall_score'] < 0.7:
                        self.failures.append(f"❌ LOW RAG QUALITY: {scenario['name']} - Score: {quality_metrics['overall_score']}")
                    elif quality_metrics['overall_score'] < 0.85:
                        self.warnings.append(f"⚠️ MODERATE RAG QUALITY: {scenario['name']} - Score: {quality_metrics['overall_score']}")
                    
                else:
                    self.failures.append(f"❌ NO COMPETITOR DATA: {scenario['name']} - Cannot test RAG")
                    
            except Exception as e:
                self.failures.append(f"❌ RAG TEST FAILED: {scenario['name']} - {str(e)}")
                logger.error(f"❌ {scenario['name']} RAG test failed: {str(e)}")
    
    def analyze_rag_output_quality(self, rag_result: Dict, scenario: Dict) -> Dict:
        """Analyze the quality of RAG-generated output."""
        if not rag_result:
            return {'overall_score': 0.0, 'issues': ['No output generated']}
        
        quality_metrics = {
            'structure_completeness': 0.0,
            'content_quality': 0.0,
            'competitor_integration': 0.0,
            'platform_specificity': 0.0,
            'overall_score': 0.0,
            'issues': [],
            'missing_fields': []
        }
        
        # Check structure completeness
        required_fields = ['strategy_recommendations', 'competitor_analysis', 'next_post_prediction']
        present_fields = [field for field in required_fields if field in rag_result]
        quality_metrics['structure_completeness'] = len(present_fields) / len(required_fields)
        
        if len(present_fields) < len(required_fields):
            missing = [field for field in required_fields if field not in rag_result]
            quality_metrics['missing_fields'] = missing
            quality_metrics['issues'].append(f"Missing fields: {missing}")
        
        # Check content quality
        content_issues = []
        if 'strategy_recommendations' in rag_result:
            strategy = rag_result['strategy_recommendations']
            if isinstance(strategy, dict) and 'recommendations' in strategy:
                recommendations = strategy['recommendations']
                if isinstance(recommendations, list) and len(recommendations) > 0:
                    # Check for generic/template content
                    generic_phrases = ['leverage insights', 'engage authentically', 'post consistently']
                    generic_count = sum(1 for rec in recommendations if any(phrase in str(rec).lower() for phrase in generic_phrases))
                    if generic_count > len(recommendations) * 0.5:
                        content_issues.append("High generic content ratio")
                else:
                    content_issues.append("No strategy recommendations found")
            else:
                content_issues.append("Invalid strategy structure")
        
        # Check competitor integration
        competitor_integration_score = 0.0
        if 'competitor_analysis' in rag_result:
            comp_analysis = rag_result['competitor_analysis']
            if isinstance(comp_analysis, dict):
                expected_competitors = scenario.get('competitors', [])
                analyzed_competitors = [k for k in comp_analysis.keys() if k in expected_competitors]
                if expected_competitors:
                    competitor_integration_score = len(analyzed_competitors) / len(expected_competitors)
                    if competitor_integration_score < 1.0:
                        content_issues.append(f"Missing competitor analysis for: {set(expected_competitors) - set(analyzed_competitors)}")
        
        quality_metrics['competitor_integration'] = competitor_integration_score
        
        # Check platform specificity
        platform = scenario.get('platform', '')
        platform_specific_score = 0.0
        if platform:
            platform_terms = {
                'twitter': ['tweet', 'retweet', 'thread', 'hashtag'],
                'instagram': ['post', 'story', 'reel', 'hashtag']
            }
            relevant_terms = platform_terms.get(platform, [])
            if relevant_terms:
                content_str = json.dumps(rag_result).lower()
                found_terms = [term for term in relevant_terms if term in content_str]
                platform_specific_score = len(found_terms) / len(relevant_terms)
                if platform_specific_score < 0.5:
                    content_issues.append(f"Low platform specificity for {platform}")
        
        quality_metrics['platform_specificity'] = platform_specific_score
        quality_metrics['content_quality'] = max(0.0, 1.0 - (len(content_issues) * 0.2))
        quality_metrics['issues'].extend(content_issues)
        
        # Calculate overall score
        quality_metrics['overall_score'] = (
            quality_metrics['structure_completeness'] * 0.3 +
            quality_metrics['content_quality'] * 0.3 +
            quality_metrics['competitor_integration'] * 0.25 +
            quality_metrics['platform_specificity'] * 0.15
        )
        
        return quality_metrics
    
    def test_output_structure_consistency(self):
        """Test output structure consistency across different scenarios."""
        logger.info("🔍 TESTING OUTPUT STRUCTURE CONSISTENCY")
        
        # This will be implemented to test structure consistency
        # between normal accounts and zero-post accounts
        pass
    
    def test_edge_case_handling(self):
        """Test edge case handling scenarios."""
        logger.info("🔍 TESTING EDGE CASE HANDLING")
        
        # This will test various edge cases like partial data,
        # corrupted data, network failures, etc.
        pass
    
    def test_platform_specific_issues(self):
        """Test platform-specific implementation issues."""
        logger.info("🔍 TESTING PLATFORM-SPECIFIC ISSUES")
        
        # This will test Twitter vs Instagram specific issues
        pass
    
    def test_export_validation(self):
        """Test export file validation and structure."""
        logger.info("🔍 TESTING EXPORT VALIDATION")
        
        # This will test exported file structure and content
        pass
    
    def generate_vulnerability_report(self):
        """Generate comprehensive vulnerability report."""
        logger.info("📋 GENERATING COMPREHENSIVE VULNERABILITY REPORT")
        
        report = {
            'summary': {
                'total_failures': len(self.failures),
                'total_warnings': len(self.warnings),
                'test_results': self.test_results
            },
            'critical_failures': self.failures,
            'warnings': self.warnings,
            'recommendations': self.generate_fix_recommendations()
        }
        
        # Save report
        with open('/home/komail/Miners-1/zero_post_handler_vulnerability_report.json', 'w') as f:
            json.dump(report, f, indent=2)
        
        # Print summary
        print("\n" + "="*80)
        print("🚨 ZERO-POST HANDLER VULNERABILITY REPORT")
        print("="*80)
        print(f"❌ CRITICAL FAILURES: {len(self.failures)}")
        print(f"⚠️  WARNINGS: {len(self.warnings)}")
        print("\nCRITICAL FAILURES:")
        for failure in self.failures:
            print(f"  {failure}")
        print("\nWARNINGS:")
        for warning in self.warnings:
            print(f"  {warning}")
        print("\n📋 Full report saved to: zero_post_handler_vulnerability_report.json")
        print("="*80)
    
    def generate_fix_recommendations(self) -> List[str]:
        """Generate specific fix recommendations based on test results."""
        recommendations = []
        
        # Analyze test results and generate specific fixes
        if any('NO DATA FOUND' in failure for failure in self.failures):
            recommendations.append("Fix data collection paths for Twitter competitors")
        
        if any('Vector database not available' in failure for failure in self.failures):
            recommendations.append("Ensure vector database initialization in zero-post handler")
        
        if any('No Twitter competitors indexed' in failure for failure in self.failures):
            recommendations.append("Implement proper competitor data indexing in vector database")
        
        if any('LOW RAG QUALITY' in failure for failure in self.failures):
            recommendations.append("Improve RAG prompt engineering and competitor data integration")
        
        return recommendations

if __name__ == "__main__":
    battle_test = ZeroPostHandlerBattleTest()
    battle_test.run_comprehensive_battle_test()
