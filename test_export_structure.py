#!/usr/bin/env python3
"""
Simple test to verify that our export modifications removed metadata correctly.
"""

import sys
import os

def test_export_code_structure():
    """Test that export code no longer includes metadata wrapping."""
    
    print("🔍 Testing export_content_plan.py for clean export structure...")
    
    # Read export_content_plan.py and check for metadata patterns
    with open('/home/komail/Miners-1/export_content_plan.py', 'r') as f:
        content = f.read()
    
    # Patterns that indicate metadata wrapping was removed
    good_patterns = [
        'return competitor_analysis',  # Direct return without wrapping
        'return recommendation',       # Direct return without wrapping
        'return next_post_data'        # Direct return without wrapping
    ]
    
    # Patterns that would indicate old metadata wrapping
    bad_patterns = [
        '"module_type": "competitor_analysis"',
        '"module_type": "recommendation"', 
        '"module_type": "next_post"',
        '"platform": platform',
        '"timestamp": datetime'
    ]
    
    print("✅ Checking for clean export patterns:")
    good_found = 0
    for pattern in good_patterns:
        if pattern in content:
            good_found += 1
            print(f"  ✅ Found: {pattern}")
        else:
            print(f"  ⚠️  Not found: {pattern}")
    
    print("❌ Checking for old metadata patterns:")
    bad_found = 0
    for pattern in bad_patterns:
        if pattern in content:
            bad_found += 1
            print(f"  ❌ Found unwanted: {pattern}")
            # Find the line number
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if pattern in line:
                    print(f"    Line {i+1}: {line.strip()}")
        else:
            print(f"  ✅ Good - not found: {pattern}")
    
    if bad_found == 0:
        print("\n🎉 All metadata patterns successfully removed!")
        success = True
    else:
        print(f"\n💥 Found {bad_found} unwanted metadata patterns")
        success = False
    
    print(f"\n📊 Summary: {good_found} good patterns, {bad_found} bad patterns")
    return success

def main():
    """Run the export structure test."""
    print("🧪 Starting export structure test")
    print("=" * 60)
    
    try:
        success = test_export_code_structure()
        
        print("=" * 60)
        if success:
            print("🎉 EXPORT STRUCTURE TEST PASSED: Clean exports implemented!")
        else:
            print("💥 EXPORT STRUCTURE TEST FAILED: Metadata still present")
            
        return success
        
    except Exception as e:
        print(f"💥 TEST ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
