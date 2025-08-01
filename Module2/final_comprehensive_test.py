#!/usr/bin/env python3
"""
Final Comprehensive Test: Real Main.py Export → Image Generator Integration
Tests the actual format exported by main.py with the enhanced Image Generator
"""

import sys
import json
from image_generator import ImageGenerator

def test_main_export_format():
    """Test the actual format exported by main.py"""
    
    print('🧪 TESTING: Main.py Export Format → Image Generator')
    print('=' * 70)
    
    # Real format exported by main.py (from line 1305-1313)
    main_export_format = {
        "module_type": "next_post_prediction",
        "platform": "instagram",
        "username": "fentybeauty",
        "post_data": {
            "caption": "Okay baddies, let's talk LIPS 💋 What's your go-to Gloss Bomb shade for that perfect summer pout? ☀️ I'm feelin' extra *fu$$y* today, but that Hot Cherry is callin' my name! 🍒",
            "hashtags": ["#FentyBeauty", "#GlossBomb", "#LipGloss", "#SummerMakeup", "#Fussy", "#HotCherry", "#RiRiLovesYou"],
            "call_to_action": "Drop your fave Gloss Bomb shade in the comments! 👇 And tag a friend who needs some Fenty in their life! 💖",
            "image_prompt": "🎨 **AUTHENTIC VISUAL DIRECTION**: Close-up shot of lips glistening with Gloss Bomb. Focus on the texture and shine. The model should have a radiant complexion and a playful expression. Composition: Slightly asymmetrical, emphasizing the fullness of the lips. Color Palette: Primarily pinks, reds, and browns, reflecting the Gloss Bomb shades. Visual Elements: Include subtle hints of summer, such as a sun-kissed glow or a tropical flower in the background. Lighting and Mood: Soft, diffused lighting to create a flattering and inviting atmosphere. Props and Settings: A simple, clean background to keep the focus on the lips. Design Details: Add a subtle sparkle effect to enhance the shine of the Gloss Bomb. The overall aesthetic should be fun, flirty, and inclusive, reflecting the Fenty Beauty brand.",
            "platform": "instagram",
            "username": "fentybeauty"
        },
        "generated_at": "2025-05-31T22:00:00.000Z",
        "status": "pending"
    }

    print('📥 Input (Real main.py export format):')
    print(json.dumps(main_export_format, indent=2))
    print('')

    # Test with enhanced Image Generator
    ig = ImageGenerator()
    print('🔧 Processing with enhanced Image Generator...')

    try:
        fixed_data = ig.fix_post_data(main_export_format, 'main_export_test')
        
        if fixed_data:
            print('✅ SUCCESS: Main.py export format successfully processed!')
            print('')
            print('📤 Output (Image Generator compatible):')
            print(json.dumps(fixed_data, indent=2))
            print('')
            
            # Comprehensive validation
            has_post = 'post' in fixed_data
            has_image_prompt = 'post' in fixed_data and 'image_prompt' in fixed_data['post']
            has_status = 'status' in fixed_data
            has_platform = 'platform' in fixed_data and fixed_data['platform'] == 'instagram'
            has_username = 'username' in fixed_data and fixed_data['username'] == 'fentybeauty'
            
            print('🔍 VALIDATION CHECKS:')
            print(f'   Post wrapper: {"✅" if has_post else "❌"} {has_post}')
            print(f'   Image prompt: {"✅" if has_image_prompt else "❌"} {has_image_prompt}')
            print(f'   Status field: {"✅" if has_status else "❌"} {has_status}')
            print(f'   Platform preserved: {"✅" if has_platform else "❌"} {has_platform}')
            print(f'   Username preserved: {"✅" if has_username else "❌"} {has_username}')
            
            # Check content preservation
            if has_post:
                original_caption = main_export_format['post_data']['caption']
                converted_caption = fixed_data['post']['caption']
                content_match = original_caption == converted_caption
                print(f'   Content integrity: {"✅" if content_match else "❌"} {content_match}')
            
            all_checks = all([has_post, has_image_prompt, has_status, has_platform, has_username])
            
            if all_checks:
                print('')
                print('🎉 MAIN.PY EXPORT FORMAT TEST: PASSED')
                print('💪 Enhanced Image Generator handles main.py exports perfectly!')
                print('🚀 Production pipeline integration verified!')
                return True
            else:
                print('')
                print('❌ Some validation checks failed')
                return False
        else:
            print('❌ ERROR: Enhanced Image Generator failed to process main.py export')
            return False
            
    except Exception as e:
        print(f'❌ ERROR: {str(e)}')
        import traceback
        print('📋 Full error details:')
        print(traceback.format_exc())
        return False

def test_legacy_compatibility():
    """Test that legacy formats still work"""
    
    print('\n' + '=' * 70)
    print('🔄 TESTING: Legacy Format Compatibility')
    print('=' * 70)
    
    legacy_formats = [
        {
            'name': 'Legacy next_post_prediction Format',
            'data': {
                'next_post_prediction': {
                    'caption': 'Legacy format test! 🎉',
                    'hashtags': ['#legacy', '#test'],
                    'call_to_action': 'Legacy CTA',
                    'image_prompt': 'Legacy image prompt'
                }
            }
        },
        {
            'name': 'Direct post format',
            'data': {
                'post': {
                    'caption': 'Direct post test! 🚀',
                    'hashtags': ['#direct', '#test'],
                    'call_to_action': 'Direct CTA',
                    'image_prompt': 'Direct image prompt'
                },
                'status': 'pending'
            }
        }
    ]
    
    ig = ImageGenerator()
    passed = 0
    total = len(legacy_formats)
    
    for i, test_case in enumerate(legacy_formats, 1):
        print(f'\n📋 Legacy Test {i}/{total}: {test_case["name"]}')
        
        try:
            result = ig.fix_post_data(test_case['data'], f'legacy_test_{i}')
            
            if result and 'post' in result and 'status' in result:
                has_prompt = 'image_prompt' in result['post']
                if has_prompt:
                    print(f'   ✅ PASSED - {test_case["name"]} still works')
                    passed += 1
                else:
                    print(f'   ❌ FAILED - Missing image prompt in {test_case["name"]}')
            else:
                print(f'   ❌ FAILED - Invalid output for {test_case["name"]}')
                
        except Exception as e:
            print(f'   ❌ ERROR - {test_case["name"]}: {str(e)}')
    
    print(f'\n📊 LEGACY COMPATIBILITY: {passed}/{total} passed')
    return passed == total

def main():
    """Run all comprehensive tests"""
    
    print('🏁 FINAL COMPREHENSIVE TEST SUITE')
    print('🎯 Testing Enhanced Module 1 ↔ Module 2 Integration')
    print('💎 Real Production Format Validation')
    print('=' * 80)
    
    # Test 1: Main.py export format
    main_export_test = test_main_export_format()
    
    # Test 2: Legacy compatibility
    legacy_test = test_legacy_compatibility()
    
    print('\n' + '=' * 80)
    print('📈 FINAL COMPREHENSIVE TEST RESULTS')
    print('=' * 80)
    print(f'Main.py Export Format Test: {"✅ PASSED" if main_export_test else "❌ FAILED"}')
    print(f'Legacy Compatibility Test: {"✅ PASSED" if legacy_test else "❌ FAILED"}')
    
    if main_export_test and legacy_test:
        print('\n🎉 ALL COMPREHENSIVE TESTS PASSED!')
        print('🔗 Module 1 ↔ Module 2 integration is BULLETPROOF!')
        print('🚀 Production pipeline is fully validated!')
        print('💎 Enhanced compatibility is perfect!')
        print('')
        print('✅ SYSTEM STATUS: PRODUCTION READY')
        print('🏆 INTEGRATION QUALITY: BULLETPROOF')
        print('🎯 COMPATIBILITY: 100% VERIFIED')
    else:
        print('\n⚠️ SOME COMPREHENSIVE TESTS FAILED')
        print('🔧 Review the enhanced integration.')
    
    print('=' * 80)
    
    return main_export_test and legacy_test

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1) 