#!/usr/bin/env python3
"""
Integration Test: NextPost → Image Generator Pipeline
Tests the enhanced compatibility solution between Module 1 and Module 2
"""

import sys
import json
import os

print('🔧 Setting up import paths...')
print(f'Current working directory: {os.getcwd()}')

# Check if we're in the main directory, if so change to Module2
if os.path.basename(os.getcwd()) != 'Module2':
    if os.path.exists('./Module2'):
        os.chdir('./Module2')
        print('📁 Changed to Module2 directory')
    else:
        print('❌ Module2 directory not found')
        sys.exit(1)

# Now import from the current directory
try:
    from image_generator import ImageGenerator
    print('✅ Successfully imported ImageGenerator')
except ImportError as e:
    print(f"❌ ERROR: Could not import ImageGenerator: {e}")
    print("🔧 Make sure you're running from the Module2 directory")
    sys.exit(1)

def test_nextpost_integration():
    """Test NextPost module output compatibility with Image Generator"""
    
    # Simulate NextPost module output
    nextpost_output = {
        'next_post_prediction': {
            'caption': 'Transform your morning routine with this amazing productivity hack! ✨',
            'hashtags': ['#productivity', '#morningroutine', '#lifestyle'],
            'call_to_action': 'What is your favorite morning routine tip? Share below! 👇',
            'image_prompt': '🎨 **AUTHENTIC VISUAL DIRECTION**: Close-up shot of organized desk with coffee, journal, and morning light streaming through window'
        }
    }

    print('🧪 TESTING: NextPost → Image Generator Integration')
    print('=' * 60)
    print('📥 Input (NextPost output):')
    print(json.dumps(nextpost_output, indent=2))
    print('')

    # Initialize Image Generator
    ig = ImageGenerator()

    # Test the enhanced compatibility
    print('🔧 Processing with enhanced Image Generator...')
    try:
        fixed_data = ig.fix_post_data(nextpost_output, 'integration_test')
        print('✅ SUCCESS: Data successfully normalized!')
        print('')
        print('📤 Output (Image Generator compatible):')
        print(json.dumps(fixed_data, indent=2))
        print('')
        
        # Verify required fields
        has_post = 'post' in fixed_data
        has_image_prompt = 'post' in fixed_data and ('image_prompt' in fixed_data['post'] or 'visual_prompt' in fixed_data['post'])
        has_status = 'status' in fixed_data
        
        print('🔍 VALIDATION CHECKS:')
        print(f'   Post wrapper present: {"✅" if has_post else "❌"} {has_post}')
        print(f'   Image prompt present: {"✅" if has_image_prompt else "❌"} {has_image_prompt}')
        print(f'   Status field present: {"✅" if has_status else "❌"} {has_status}')
        
        if has_post and has_image_prompt and has_status:
            print('')
            print('🎉 INTEGRATION TEST: PASSED')
            print('💡 NextPost → Image Generator pipeline is working correctly!')
            return True
        else:
            print('')
            print('❌ INTEGRATION TEST: FAILED')
            print('⚠️ Missing required fields for Image Generator')
            return False
            
    except Exception as e:
        print(f'❌ ERROR: {str(e)}')
        print('🚨 Integration test failed!')
        return False

def test_multiple_formats():
    """Test multiple input formats to ensure robustness"""
    
    print('\n🔄 TESTING: Multiple Format Compatibility')
    print('=' * 60)
    
    ig = ImageGenerator()
    test_cases = [
        {
            'name': 'Standard NextPost Format',
            'data': {
                'next_post_prediction': {
                    'caption': 'Amazing content here!',
                    'hashtags': ['#test', '#example'],
                    'call_to_action': 'Like and share!',
                    'image_prompt': 'Beautiful landscape photography'
                }
            }
        },
        {
            'name': 'Twitter Format',
            'data': {
                'tweet': {
                    'content': 'Check out this cool tech update!',
                    'hashtags': ['#tech', '#innovation'],
                    'visual_prompt': 'Modern technology interface screenshot'
                }
            }
        },
        {
            'name': 'Direct Post Format',
            'data': {
                'post': {
                    'caption': 'Direct post content',
                    'hashtags': ['#direct'],
                    'image_prompt': 'Clean minimalist design'
                },
                'status': 'pending'
            }
        }
    ]
    
    passed = 0
    total = len(test_cases)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f'\n📋 Test {i}/{total}: {test_case["name"]}')
        try:
            result = ig.fix_post_data(test_case['data'], f'test_{i}')
            if result and 'post' in result and 'status' in result:
                has_prompt = 'image_prompt' in result['post'] or 'visual_prompt' in result['post']
                if has_prompt:
                    print(f'   ✅ PASSED - Successfully normalized {test_case["name"]}')
                    passed += 1
                else:
                    print(f'   ❌ FAILED - Missing image prompt in {test_case["name"]}')
            else:
                print(f'   ❌ FAILED - Invalid output structure for {test_case["name"]}')
        except Exception as e:
            print(f'   ❌ ERROR - {test_case["name"]}: {str(e)}')
    
    print(f'\n📊 MULTI-FORMAT TEST RESULTS: {passed}/{total} passed')
    return passed == total

if __name__ == '__main__':
    print('🚀 COMPREHENSIVE INTEGRATION TEST SUITE')
    print('🎯 Testing NextPost → Image Generator Enhanced Compatibility')
    print('=' * 80)
    
    # Run primary integration test
    primary_test = test_nextpost_integration()
    
    # Run multi-format compatibility test
    multi_format_test = test_multiple_formats()
    
    print('\n' + '=' * 80)
    print('📈 FINAL INTEGRATION TEST SUMMARY')
    print('=' * 80)
    print(f'Primary Integration Test: {"✅ PASSED" if primary_test else "❌ FAILED"}')
    print(f'Multi-Format Test: {"✅ PASSED" if multi_format_test else "❌ FAILED"}')
    
    if primary_test and multi_format_test:
        print('\n🎉 ALL INTEGRATION TESTS PASSED!')
        print('💪 NextPost → Image Generator pipeline is bulletproof!')
        print('🚀 System is ready for production use!')
    else:
        print('\n⚠️ SOME TESTS FAILED')
        print('🔧 Review the enhanced compatibility implementation.')
    
    print('=' * 80) 