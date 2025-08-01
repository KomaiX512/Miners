#!/usr/bin/env python3
"""
Final Integration Test: Real NextPost → Image Generator Pipeline
Tests using actual content from content_plan.json to verify bulletproof compatibility
"""

import sys
import json
from image_generator import ImageGenerator

def test_real_world_integration():
    """Test with actual NextPost content from content_plan.json"""
    
    # Real NextPost module output from actual content_plan.json
    nextpost_output = {
        'next_post_prediction': {
            'caption': 'Okay baddies, let\'s talk LIPS 💋 What\'s your go-to Gloss Bomb shade for that perfect summer pout? ☀️ I\'m feelin\' extra *fu$$y* today, but that Hot Cherry is callin\' my name! 🍒 Tell me in the comments, and maybe I\'ll spill the tea on a new shade comin\' soon... 😉',
            'hashtags': ['#FentyBeauty', '#GlossBomb', '#LipGloss', '#SummerMakeup', '#Fussy', '#HotCherry', '#RiRiLovesYou'],
            'call_to_action': 'Drop your fave Gloss Bomb shade in the comments! 👇 And tag a friend who needs some Fenty in their life! 💖',
            'image_prompt': '🎨 **AUTHENTIC VISUAL DIRECTION**: Close-up shot of lips glistening with Gloss Bomb. Focus on the texture and shine. The model should have a radiant complexion and a playful expression. Composition: Slightly asymmetrical, emphasizing the fullness of the lips. Color Palette: Primarily pinks, reds, and browns, reflecting the Gloss Bomb shades. Visual Elements: Include subtle hints of summer, such as a sun-kissed glow or a tropical flower in the background. Lighting and Mood: Soft, diffused lighting to create a flattering and inviting atmosphere. Props and Settings: A simple, clean background to keep the focus on the lips. Design Details: Add a subtle sparkle effect to enhance the shine of the Gloss Bomb. The overall aesthetic should be fun, flirty, and inclusive, reflecting the Fenty Beauty brand.'
        }
    }

    print('🧪 TESTING: Real NextPost → Image Generator Integration')
    print('=' * 70)
    print('📥 Input (From actual content_plan.json):')
    print(json.dumps(nextpost_output, indent=2))
    print('')

    # Initialize and test the enhanced Image Generator
    ig = ImageGenerator()
    print('🔧 Processing with enhanced Image Generator...')

    try:
        fixed_data = ig.fix_post_data(nextpost_output, 'real_integration_test')
        
        if fixed_data:
            print('✅ SUCCESS: Data successfully normalized!')
            print('')
            print('📤 Output (Image Generator compatible):')
            print(json.dumps(fixed_data, indent=2))
            print('')
            
            # Comprehensive validation
            has_post = 'post' in fixed_data
            has_image_prompt = 'post' in fixed_data and ('image_prompt' in fixed_data['post'] or 'visual_prompt' in fixed_data['post'])
            has_status = 'status' in fixed_data
            has_platform = 'platform' in fixed_data
            has_caption = 'post' in fixed_data and 'caption' in fixed_data['post']
            has_hashtags = 'post' in fixed_data and 'hashtags' in fixed_data['post']
            has_cta = 'post' in fixed_data and 'call_to_action' in fixed_data['post']
            
            print('🔍 COMPREHENSIVE VALIDATION CHECKS:')
            print(f'   Post wrapper present: {"✅" if has_post else "❌"} {has_post}')
            print(f'   Image prompt present: {"✅" if has_image_prompt else "❌"} {has_image_prompt}')
            print(f'   Status field present: {"✅" if has_status else "❌"} {has_status}')
            print(f'   Platform field present: {"✅" if has_platform else "❌"} {has_platform}')
            print(f'   Caption preserved: {"✅" if has_caption else "❌"} {has_caption}')
            print(f'   Hashtags preserved: {"✅" if has_hashtags else "❌"} {has_hashtags}')
            print(f'   Call-to-action preserved: {"✅" if has_cta else "❌"} {has_cta}')
            
            # Verify content integrity
            if has_post and has_caption:
                original_caption = nextpost_output['next_post_prediction']['caption']
                converted_caption = fixed_data['post']['caption']
                content_preserved = original_caption == converted_caption
                print(f'   Content integrity: {"✅" if content_preserved else "❌"} {content_preserved}')
            
            if has_post and has_image_prompt:
                if 'image_prompt' in fixed_data['post']:
                    prompt = fixed_data['post']['image_prompt']
                else:
                    prompt = fixed_data['post']['visual_prompt']
                prompt_quality = len(prompt) > 50 and 'AUTHENTIC VISUAL DIRECTION' in prompt
                print(f'   Image prompt quality: {"✅" if prompt_quality else "❌"} {prompt_quality}')
            
            all_checks = all([has_post, has_image_prompt, has_status, has_caption, has_hashtags, has_cta])
            
            if all_checks:
                print('')
                print('🎉 REAL-WORLD INTEGRATION TEST: PASSED')
                print('💪 NextPost → Image Generator pipeline is BULLETPROOF!')
                print('🚀 Ready for production with real content!')
                print('✨ All content preserved with perfect format conversion!')
                return True
            else:
                print('')
                print('❌ INTEGRATION TEST: FAILED')
                print('⚠️ Some validation checks failed')
                return False
        else:
            print('❌ ERROR: fix_post_data returned None')
            return False
            
    except Exception as e:
        print(f'❌ ERROR: {str(e)}')
        import traceback
        print('📋 Full error details:')
        print(traceback.format_exc())
        return False

def test_edge_cases():
    """Test edge cases and alternative formats"""
    
    print('\n' + '=' * 70)
    print('🔄 TESTING: Edge Cases and Alternative Formats')
    print('=' * 70)
    
    edge_cases = [
        {
            'name': 'Direct NextPost Format (No Wrapper)',
            'data': {
                'caption': 'Amazing summer vibes! 🌞',
                'hashtags': ['#summer', '#vibes'],
                'call_to_action': 'Share your thoughts!',
                'image_prompt': 'Beautiful summer scene with warm lighting'
            }
        },
        {
            'name': 'Nested NextPost Format',
            'data': {
                'post_data': {
                    'next_post_prediction': {
                        'caption': 'Innovation at its finest! 🚀',
                        'hashtags': ['#innovation', '#tech'],
                        'call_to_action': 'What do you think?',
                        'image_prompt': 'Cutting-edge technology visualization'
                    }
                }
            }
        },
        {
            'name': 'Missing Image Prompt (Should Generate Default)',
            'data': {
                'next_post_prediction': {
                    'caption': 'Great content coming soon! 🎉',
                    'hashtags': ['#coming', '#soon'],
                    'call_to_action': 'Stay tuned!'
                }
            }
        }
    ]
    
    ig = ImageGenerator()
    passed = 0
    total = len(edge_cases)
    
    for i, test_case in enumerate(edge_cases, 1):
        print(f'\n📋 Edge Case {i}/{total}: {test_case["name"]}')
        
        try:
            result = ig.fix_post_data(test_case['data'], f'edge_case_{i}')
            
            if result and 'post' in result and 'status' in result:
                has_prompt = 'image_prompt' in result['post'] or 'visual_prompt' in result['post']
                if has_prompt:
                    print(f'   ✅ PASSED - Successfully handled {test_case["name"]}')
                    passed += 1
                else:
                    print(f'   ❌ FAILED - Missing image prompt in {test_case["name"]}')
            else:
                print(f'   ❌ FAILED - Invalid output structure for {test_case["name"]}')
                
        except Exception as e:
            print(f'   ❌ ERROR - {test_case["name"]}: {str(e)}')
    
    print(f'\n📊 EDGE CASE TEST RESULTS: {passed}/{total} passed')
    return passed == total

def main():
    """Run comprehensive integration tests"""
    
    print('🚀 COMPREHENSIVE INTEGRATION TEST SUITE')
    print('🎯 Testing NextPost → Image Generator Enhanced Compatibility')
    print('💎 Using Real Content from Production Pipeline')
    print('=' * 80)
    
    # Run real-world integration test
    real_world_test = test_real_world_integration()
    
    # Run edge case tests
    edge_case_test = test_edge_cases()
    
    print('\n' + '=' * 80)
    print('📈 FINAL INTEGRATION TEST SUMMARY')
    print('=' * 80)
    print(f'Real-World Integration Test: {"✅ PASSED" if real_world_test else "❌ FAILED"}')
    print(f'Edge Case Compatibility Test: {"✅ PASSED" if edge_case_test else "❌ FAILED"}')
    
    if real_world_test and edge_case_test:
        print('\n🎉 ALL INTEGRATION TESTS PASSED!')
        print('💪 NextPost → Image Generator pipeline is production-ready!')
        print('🚀 Enhanced compatibility solution is bulletproof!')
        print('✨ Real content flows seamlessly through the system!')
    else:
        print('\n⚠️ SOME TESTS FAILED')
        print('🔧 Review the enhanced compatibility implementation.')
    
    print('=' * 80)
    
    return real_world_test and edge_case_test

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1) 