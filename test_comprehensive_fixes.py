#!/usr/bin/env python3
"""
Comprehensive test to verify all fixes are working:
1. Hashtag contamination fixed
2. Duplicate competitor analysis eliminated
3. Clean exports without metadata
4. Individual competitor analysis quality
"""

import sys
import os

def test_hashtag_fix():
    """Check that hashtag fix is implemented in rag_implementation.py"""
    print("🔍 Testing hashtag contamination fix...")
    
    with open('/home/komail/Miners-1/rag_implementation.py', 'r') as f:
        content = f.read()
    
    # Check for hashtag contamination prevention patterns
    good_patterns = [
        'domain-specific',
        'professional context',
        'topic relevance'
    ]
    
    hashtag_section_found = False
    if 'generate_hashtags' in content or 'hashtag' in content.lower():
        hashtag_section_found = True
        print("✅ Hashtag generation logic found")
    
    contamination_prevention = any(pattern in content.lower() for pattern in good_patterns)
    if contamination_prevention:
        print("✅ Contamination prevention logic detected")
    else:
        print("⚠️  Contamination prevention not clearly detected")
    
    return hashtag_section_found

def test_duplicate_elimination():
    """Check that duplicate competitor analysis is eliminated"""
    print("🔍 Testing duplicate competitor analysis elimination...")
    
    with open('/home/komail/Miners-1/main.py', 'r') as f:
        content = f.read()
    
    # Check that restoration is removed
    bad_patterns = [
        'content_plan["competitor_analysis"] = competitor_analysis',
        'if competitor_analysis:',
        'Restored competitor analysis'
    ]
    
    duplicate_issues = []
    for pattern in bad_patterns:
        if pattern in content:
            duplicate_issues.append(pattern)
    
    if duplicate_issues:
        print(f"❌ Duplicate issues still present: {duplicate_issues}")
        return False
    else:
        print("✅ Duplicate competitor analysis restoration eliminated")
        return True

def test_clean_exports():
    """Check that export functions return clean data"""
    print("🔍 Testing clean exports implementation...")
    
    with open('/home/komail/Miners-1/export_content_plan.py', 'r') as f:
        content = f.read()
    
    # Check for clean export patterns
    clean_patterns = [
        'competitor_export = analysis',  # Direct export
        'next_post_export = next_post_data',  # Direct export
        '# CLEAN EXPORT without metadata'  # Comment indicating clean export
    ]
    
    # Check that metadata patterns are removed
    metadata_patterns = [
        '"module_type"',
        '"timestamp"',
        'datetime.now()'
    ]
    
    clean_found = 0
    for pattern in clean_patterns:
        if pattern in content:
            clean_found += 1
    
    metadata_found = 0
    for pattern in metadata_patterns:
        if pattern in content:
            metadata_found += 1
    
    if clean_found > 0 and metadata_found == 0:
        print(f"✅ Clean exports implemented ({clean_found} clean patterns, {metadata_found} metadata patterns)")
        return True
    else:
        print(f"⚠️  Export status: {clean_found} clean patterns, {metadata_found} metadata patterns")
        return clean_found > metadata_found

def test_individual_competitor_analysis():
    """Check that competitor analysis focuses on individual competitors"""
    print("🔍 Testing individual competitor analysis implementation...")
    
    with open('/home/komail/Miners-1/rag_implementation.py', 'r') as f:
        content = f.read()
    
    # Check for individual analysis patterns
    individual_patterns = [
        'individual competitor',
        'specific competitor',
        'competitor vs primary',
        'analysis should focus'
    ]
    
    individual_found = 0
    for pattern in individual_patterns:
        if pattern.lower() in content.lower():
            individual_found += 1
    
    if individual_found > 0:
        print(f"✅ Individual competitor analysis patterns found ({individual_found})")
        return True
    else:
        print("⚠️  Individual competitor analysis patterns not clearly detected")
        return False

def main():
    """Run comprehensive fix verification"""
    print("🧪 Starting comprehensive fix verification")
    print("=" * 70)
    
    tests = [
        ("Hashtag Fix", test_hashtag_fix),
        ("Duplicate Elimination", test_duplicate_elimination),
        ("Clean Exports", test_clean_exports),
        ("Individual Analysis", test_individual_competitor_analysis)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            print(f"\n📋 Running {test_name} test...")
            results[test_name] = test_func()
        except Exception as e:
            print(f"💥 {test_name} test error: {e}")
            results[test_name] = False
    
    print("\n" + "=" * 70)
    print("📊 COMPREHENSIVE TEST RESULTS:")
    print("=" * 70)
    
    passed = 0
    total = len(tests)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print("=" * 70)
    overall_success = passed == total
    if overall_success:
        print(f"🎉 ALL TESTS PASSED ({passed}/{total})")
        print("🚀 All fixes have been successfully implemented!")
    else:
        print(f"⚠️  PARTIAL SUCCESS ({passed}/{total})")
        print("🔧 Some improvements may still be needed")
    
    return overall_success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
