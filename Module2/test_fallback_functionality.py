#!/usr/bin/env python3
"""
Test script to demonstrate the new fallback functionality for private/new accounts
"""

import asyncio
import json
from goal_rag_handler import EnhancedGoalHandler, ContentGenerator, DeepRAGAnalyzer

async def test_fallback_functionality():
    """Test the new fallback content generation for private/new accounts"""
    
    print("🧪 Testing Fallback Functionality for Private/New Accounts")
    print("=" * 60)
    
    # Initialize components
    rag_analyzer = DeepRAGAnalyzer()
    content_generator = ContentGenerator(rag_analyzer)
    
    # Sample goal data (what would be in a goal.json file)
    sample_goal = {
        "goal": "Increase engagement by 50% and build brand awareness",
        "timeline": 7,
        "persona": "Professional yet approachable business coach",
        "instructions": "Focus on providing value and building trust with new audience"
    }
    
    username = "new_business_coach"
    platform = "instagram"
    
    print(f"📋 Testing for: {username} on {platform}")
    print(f"🎯 Goal: {sample_goal['goal']}")
    print(f"⏰ Timeline: {sample_goal['timeline']} days")
    print(f"👤 Persona: {sample_goal['persona']}")
    print()
    
    # Generate content using the fallback method
    print("🔒 Generating content without profile data (fallback method)...")
    try:
        posts_content = await content_generator.generate_content_without_profile(
            sample_goal, username, platform
        )
        
        print("✅ Successfully generated content!")
        print()
        print("📊 Generated Content Structure:")
        print(f"   - Total posts: {len([k for k in posts_content.keys() if k.startswith('Post_')])}")
        print(f"   - Timeline: {posts_content.get('Timeline', 'N/A')} hours between posts")
        print(f"   - Summary included: {'Yes' if 'Summary' in posts_content else 'No'}")
        print()
        
        # Display sample posts
        post_keys = [k for k in posts_content.keys() if k.startswith('Post_')]
        for i, post_key in enumerate(post_keys[:2]):  # Show first 2 posts
            print(f"📝 {post_key}:")
            content = posts_content[post_key].get('content', 'No content')
            print(f"   {content}")
            print(f"   Status: {posts_content[post_key].get('status', 'N/A')}")
            print()
        
        if len(post_keys) > 2:
            print(f"... and {len(post_keys) - 2} more posts")
            print()
        
        # Display summary
        print("📋 Summary:")
        summary = posts_content.get('Summary', 'No summary available')
        # Wrap long summary for better readability
        if len(summary) > 100:
            words = summary.split(' ')
            lines = []
            current_line = []
            for word in words:
                if len(' '.join(current_line + [word])) > 80:
                    lines.append('   ' + ' '.join(current_line))
                    current_line = [word]
                else:
                    current_line.append(word)
            if current_line:
                lines.append('   ' + ' '.join(current_line))
            print('\n'.join(lines))
        else:
            print(f"   {summary}")
        print()
        
        # Verify required elements
        print("🔍 Verification Checks:")
        summary = posts_content.get('Summary', '')
        checks = [
            ("Private/new account mentioned", any(phrase in summary.lower() for phrase in ['private account', 'new account', 'private/new'])),
            ("Posts estimation mentioned", 'posts' in summary.lower()),
            ("Limited confidence mentioned", any(phrase in summary.lower() for phrase in ['limited confidence', 'confidence', 'estimated'])),
            ("Timeline field present", 'Timeline' in posts_content),
            ("All posts have hashtags", all('#' in posts_content[key].get('content', '') for key in post_keys)),
            ("All posts have status", all('status' in posts_content[key] for key in post_keys))
        ]
        
        for check_name, check_result in checks:
            status = "✅ PASS" if check_result else "❌ FAIL"
            print(f"   {status} - {check_name}")
        
        print()
        print("🎉 Fallback functionality test completed!")
        
        # Save test output for review
        with open('/home/komail/Miners-1/Module2/test_fallback_output.json', 'w') as f:
            json.dump(posts_content, f, indent=2)
        print("📁 Test output saved to: test_fallback_output.json")
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_fallback_functionality())
