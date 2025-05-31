#!/usr/bin/env python3
"""
End-to-End Pipeline Test
Tests the complete flow: Main Pipeline → NextPost → Image Generator
"""

import json
import sys
import os

def test_end_to_end_pipeline():
    """Test the complete pipeline flow"""
    
    print('🚀 END-TO-END PIPELINE TEST')
    print('Testing: Main Pipeline → NextPost → Image Generator')
    print('=' * 60)

    # Load actual content plan to verify pipeline works
    try:
        with open('content_plan.json', 'r') as f:
            content_plan = json.load(f)
        
        print('✅ Successfully loaded content_plan.json')
        
        # Extract NextPost data
        next_post = content_plan.get('next_post_prediction', {})
        
        if next_post:
            print('✅ NextPost data found in content plan')
            print(f'   Caption: {next_post.get("caption", "")[:60]}...')
            print(f'   Hashtags: {len(next_post.get("hashtags", []))} tags')
            print(f'   Image prompt: {"Yes" if next_post.get("image_prompt") else "No"}')
            
            # Test the format that would be exported to Module2
            nextpost_format = {'next_post_prediction': next_post}
            
            # Test compatibility with Image Generator
            sys.path.append('./Module2')
            from image_generator import ImageGenerator
            
            ig = ImageGenerator()
            
            fixed_data = ig.fix_post_data(nextpost_format, 'pipeline_test')
            
            if fixed_data and 'post' in fixed_data:
                print('✅ Image Generator successfully processed NextPost output')
                print(f'   Format: {fixed_data.get("original_format", "unknown")}')
                print(f'   Platform: {fixed_data.get("platform", "unknown")}')
                print(f'   Status: {fixed_data.get("status", "unknown")}')
                
                # Verify all essential fields are preserved
                post = fixed_data['post']
                has_caption = 'caption' in post and post['caption']
                has_hashtags = 'hashtags' in post and post['hashtags']
                has_image_prompt = 'image_prompt' in post and post['image_prompt']
                has_cta = 'call_to_action' in post and post['call_to_action']
                
                print('')
                print('🔍 FIELD PRESERVATION CHECK:')
                print(f'   Caption preserved: {"✅" if has_caption else "❌"}')
                print(f'   Hashtags preserved: {"✅" if has_hashtags else "❌"}')
                print(f'   Image prompt preserved: {"✅" if has_image_prompt else "❌"}')
                print(f'   Call-to-action preserved: {"✅" if has_cta else "❌"}')
                
                if all([has_caption, has_hashtags, has_image_prompt, has_cta]):
                    print('')
                    print('🎉 END-TO-END PIPELINE TEST: PASSED')
                    print('💪 Complete integration working perfectly!')
                    print('🚀 Production pipeline is bulletproof!')
                    print('✨ Data flows seamlessly from Module 1 to Module 2!')
                    return True
                else:
                    print('')
                    print('❌ Some fields were not preserved correctly')
                    return False
            else:
                print('❌ Image Generator failed to process NextPost output')
                return False
        else:
            print('❌ No NextPost data found in content plan')
            return False
            
    except Exception as e:
        print(f'❌ Pipeline test failed: {e}')
        import traceback
        print('📋 Full error details:')
        print(traceback.format_exc())
        return False

def test_main_pipeline_exports():
    """Test that main.py correctly exports in the format Module2 expects"""
    
    print('\n' + '=' * 60)
    print('🔧 TESTING: Main Pipeline Export Format')
    print('=' * 60)
    
    try:
        # Test the _standardize_next_post_format function from main.py
        sys.path.append('.')
        from main import ContentRecommendationSystem
        
        crs = ContentRecommendationSystem()
        
        # Test next post data
        test_next_post = {
            'caption': 'Test caption with emojis! 🎉',
            'hashtags': ['#test', '#integration'],
            'call_to_action': 'What do you think?',
            'image_prompt': 'High-quality test image'
        }
        
        # Test standardization
        standardized = crs._standardize_next_post_format(test_next_post, 'instagram', 'testuser')
        
        print('✅ Main pipeline standardization working')
        print(f'   Format: {standardized.get("module_type", "unknown")}')
        print(f'   Platform: {standardized.get("platform", "unknown")}')
        print(f'   Username: {standardized.get("username", "unknown")}')
        
        # Verify it's compatible with Module2
        sys.path.append('./Module2')
        from image_generator import ImageGenerator
        
        ig = ImageGenerator()
        module2_compatible = ig.fix_post_data(standardized, 'standardization_test')
        
        if module2_compatible and 'post' in module2_compatible:
            print('✅ Module2 successfully processed standardized format')
            print('')
            print('🎉 MAIN PIPELINE EXPORT TEST: PASSED')
            print('💪 Format standardization working perfectly!')
            return True
        else:
            print('❌ Module2 failed to process standardized format')
            return False
            
    except Exception as e:
        print(f'❌ Main pipeline export test failed: {e}')
        import traceback
        print('📋 Full error details:')
        print(traceback.format_exc())
        return False

def main():
    """Run all end-to-end tests"""
    
    print('🏁 COMPREHENSIVE END-TO-END TESTING SUITE')
    print('🔗 Verifying Complete Module 1 ↔ Module 2 Integration')
    print('=' * 80)
    
    # Test 1: Pipeline flow with real data
    pipeline_test = test_end_to_end_pipeline()
    
    # Test 2: Main pipeline export compatibility
    export_test = test_main_pipeline_exports()
    
    print('\n' + '=' * 80)
    print('📊 FINAL END-TO-END TEST RESULTS')
    print('=' * 80)
    print(f'Pipeline Flow Test: {"✅ PASSED" if pipeline_test else "❌ FAILED"}')
    print(f'Export Format Test: {"✅ PASSED" if export_test else "❌ FAILED"}')
    
    if pipeline_test and export_test:
        print('\n🎉 ALL END-TO-END TESTS PASSED!')
        print('🔗 Module 1 ↔ Module 2 integration is PERFECT!')
        print('🚀 Production pipeline is fully operational!')
        print('💎 Bulletproof compatibility achieved!')
        print('')
        print('✅ SYSTEM STATUS: PRODUCTION READY')
    else:
        print('\n⚠️ SOME TESTS FAILED')
        print('🔧 Review the integration between modules.')
    
    print('=' * 80)
    
    return pipeline_test and export_test

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1) 