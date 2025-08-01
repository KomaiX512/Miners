#!/usr/bin/env python3
"""
Simple test to verify the duplicate competitor analysis fix by checking the main.py logic.
"""

import sys
import os

def test_main_py_logic():
    """Test that main.py no longer has duplicate competitor analysis restoration."""
    
    print("🔍 Testing main.py for duplicate competitor analysis logic...")
    
    # Read main.py and check for the problematic restoration
    with open('/home/komail/Miners-1/main.py', 'r') as f:
        content = f.read()
    
    # Check that competitor analysis restoration is removed
    restoration_patterns = [
        'content_plan["competitor_analysis"] = competitor_analysis',
        'if competitor_analysis:',
        'Restored competitor analysis'
    ]
    
    issues_found = []
    
    for pattern in restoration_patterns:
        if pattern in content:
            # Find the line number
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if pattern in line:
                    issues_found.append(f"Line {i+1}: {line.strip()}")
    
    if issues_found:
        print("❌ Found potential duplicate restoration logic:")
        for issue in issues_found:
            print(f"  {issue}")
        return False
    else:
        print("✅ No duplicate competitor analysis restoration found in main.py")
        
        # Also check that the backup logic is updated
        if 'competitor_analysis = content_plan.get("competitor_analysis"' not in content:
            print("✅ Competitor analysis backup logic also removed")
        else:
            print("⚠️  Competitor analysis backup logic still present (but unused)")
        
        return True

def main():
    """Run the simple logic test."""
    print("🧪 Starting simple duplicate competitor analysis logic test")
    print("=" * 60)
    
    try:
        success = test_main_py_logic()
        
        print("=" * 60)
        if success:
            print("🎉 LOGIC TEST PASSED: Duplicate competitor analysis restoration removed!")
        else:
            print("💥 LOGIC TEST FAILED: Duplicate restoration logic still present")
            
        return success
        
    except Exception as e:
        print(f"💥 TEST ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
