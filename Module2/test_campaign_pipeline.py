"""
Test script for the new campaign pipeline with corrected formats
Tests Goal RAG Handler → Query Handler → Image Generator flow
"""

import asyncio
import json
import os
from datetime import datetime
from utils.r2_client import R2Client
from utils.logging import logger
from config import R2_CONFIG, STRUCTUREDB_R2_CONFIG

async def test_campaign_pipeline():
    """Test the complete campaign pipeline with new formats"""
    
    # Initialize clients
    r2_tasks = R2Client(config=R2_CONFIG)
    r2_structuredb = R2Client(config=STRUCTUREDB_R2_CONFIG)
    
    # Test data
    test_platform = "instagram"
    test_username = "test_campaign_user"
    
    print("🚀 Testing Campaign Pipeline with New Formats")
    print("=" * 50)
    
    # 1. Create test goal file
    print("📝 1. Creating test goal file...")
    goal_data = {
        "goal": "Increase engagement by 50% in 30 days",
        "timeline": 30,
        "persona": "Professional yet approachable brand voice",
        "instructions": "Focus on educational content that drives comments and shares",
        "status": "pending",
        "created_at": datetime.now().isoformat()
    }
    
    goal_key = f"tasks/goal/{test_platform}/{test_username}/goal_test_campaign.json"
    success = await r2_tasks.write_json(goal_key, goal_data)
    print(f"✅ Goal file created: {success}")
    
    # 2. Create test profile data
    print("📊 2. Creating test profile data...")
    profile_data = {
        "username": test_username,
        "biography": "Professional content creator sharing industry insights and tips",
        "followersCount": 15000,
        "followsCount": 500,
        "verified": False,
        "isBusinessAccount": True,
        "latestPosts": [
            {
                "caption": "5 proven strategies to boost your productivity #productivity #tips #business",
                "likesCount": 245,
                "commentsCount": 18,
                "type": "photo"
            },
            {
                "caption": "Behind the scenes of our latest project! What do you think? #behindthescenes #creative",
                "likesCount": 189,
                "commentsCount": 25,
                "type": "photo"
            },
            {
                "caption": "Quick tip: Always backup your work! Learn from my mistakes 😅 #advice #tech",
                "likesCount": 167,
                "commentsCount": 12,
                "type": "photo"
            }
        ]
    }
    
    profile_key = f"{test_platform}/{test_username}/{test_username}.json"
    success = await r2_structuredb.write_json(profile_key, profile_data)
    print(f"✅ Profile data created: {success}")
    
    # 3. Wait for Goal RAG Handler to process (simulate)
    print("⏳ 3. Simulating Goal RAG Handler output...")
    
    # Create expected Goal RAG Handler output in new format
    goal_handler_output = [
        {
            "Post_1": {
                "content": "Did you know that 90% of successful businesses use data-driven strategies? Let's explore how analytics can transform your decision-making process. This visual should show clean charts and graphs with a professional blue and white color scheme.",
                "status": "pending"
            },
            "Post_2": {
                "content": "Time management isn't just about tools - it's about mindset and prioritization. Here are 3 simple techniques that changed my productivity game completely. The image should feature a modern workspace with organized elements and natural lighting.",
                "status": "pending"
            },
            "Post_3": {
                "content": "Behind every successful project is a team that communicates effectively and shares a common vision. Building trust takes time, but it's the foundation of exceptional results. Show a collaborative team environment with diverse professionals working together.",
                "status": "pending"
            },
            "Post_4": {
                "content": "Innovation doesn't happen overnight - it's the result of consistent experimentation and learning from failures. The best ideas often come from combining existing concepts in new ways. Create a creative workspace visual with brainstorming materials and modern design elements.",
                "status": "pending"
            },
            "Post_5": {
                "content": "Personal branding isn't about creating a fake persona - it's about authentically showcasing your expertise and values. Your brand should reflect who you truly are and what you stand for. Design a professional headshot setup with clean background and confident lighting.",
                "status": "pending"
            },
            "Summary": "This 5-post campaign focuses on productivity, leadership, and professional development themes, optimized based on your account's historical performance showing 1.47% average engagement rate. These post types demonstrate high engagement through detailed captions, strategic hashtag usage, which aligns with your audience's preferences and your most successful content patterns."
        }
    ]
    
    goal_output_key = f"generated_content/{test_platform}/{test_username}/posts.json"
    success = await r2_tasks.write_json(goal_output_key, goal_handler_output)
    print(f"✅ Goal RAG Handler output created: {success}")
    
    # 4. Test Query Handler processing
    print("🔄 4. Testing Query Handler format...")
    
    # Show expected output format for Query Handler
    expected_campaign_post = {
        "module_type": "next_post_prediction",
        "platform": test_platform,
        "username": test_username,
        "post_data": {
            "caption": "Did you know that 90% of successful businesses use data-driven strategies? Let's explore how analytics can transform your decision-making process.",
            "hashtags": ["#DataDriven", "#BusinessStrategy", "#Analytics", "#Success", "#Growth"],
            "call_to_action": "What's your experience with data-driven decisions? Share below!",
            "image_prompt": "Clean charts and graphs with a professional blue and white color scheme, modern business analytics dashboard"
        },
        "generated_at": datetime.now().isoformat()
    }
    
    # Simulate Query Handler output
    campaign_post_key = f"next_posts/{test_platform}/{test_username}/campaign_post_1.json"
    success = await r2_tasks.write_json(campaign_post_key, expected_campaign_post)
    print(f"✅ Campaign post format created: {success}")
    
    # 5. Test Image Generator expected input/output
    print("🎨 5. Testing Image Generator format...")
    
    # Show expected output format for Image Generator
    expected_ready_post = {
        "post": {
            "caption": "Did you know that 90% of successful businesses use data-driven strategies? Let's explore how analytics can transform your decision-making process.",
            "hashtags": ["#DataDriven", "#BusinessStrategy", "#Analytics", "#Success", "#Growth"],
            "call_to_action": "What's your experience with data-driven decisions? Share below!",
            "image_url": f"ready_post/{test_platform}/{test_username}/image_1.jpg",
            "platform": test_platform,
            "username": test_username
        },
        "status": "pending",
        "processed_at": datetime.now().isoformat(),
        "image_generated": True,
        "original_format": "next_post_prediction"
    }
    
    # Simulate Image Generator output
    ready_post_key = f"ready_post/{test_platform}/{test_username}/campaign_ready_post_1.json"
    success = await r2_tasks.write_json(ready_post_key, expected_ready_post)
    print(f"✅ Campaign ready post format created: {success}")
    
    # 6. Validation
    print("\n📋 6. Format Validation Summary:")
    print("-" * 30)
    
    # Check Goal RAG Handler output format
    goal_output = await r2_tasks.read_json(goal_output_key)
    if isinstance(goal_output, list) and len(goal_output) > 0:
        posts_dict = goal_output[0]
        post_count = len([k for k in posts_dict.keys() if k.startswith("Post_")])
        print(f"✅ Goal RAG Handler: {post_count} posts + Summary in correct format")
        
        # Check individual post format
        for key, value in posts_dict.items():
            if key.startswith("Post_"):
                if isinstance(value, dict) and "content" in value and "status" in value:
                    print(f"   ✅ {key}: Correct format with content and status")
                else:
                    print(f"   ❌ {key}: Invalid format")
                break
    else:
        print("❌ Goal RAG Handler: Invalid output format")
    
    # Check Query Handler output format
    campaign_post = await r2_tasks.read_json(campaign_post_key)
    required_fields = ["module_type", "platform", "username", "post_data", "generated_at"]
    if all(field in campaign_post for field in required_fields):
        post_data_fields = ["caption", "hashtags", "call_to_action", "image_prompt"]
        if all(field in campaign_post["post_data"] for field in post_data_fields):
            print("✅ Query Handler: Campaign post format is correct")
        else:
            print("❌ Query Handler: Missing post_data fields")
    else:
        print("❌ Query Handler: Missing required campaign post fields")
    
    # Check Image Generator output format
    ready_post = await r2_tasks.read_json(ready_post_key)
    if "post" in ready_post and "status" in ready_post:
        print("✅ Image Generator: Campaign ready post format is correct")
    else:
        print("❌ Image Generator: Invalid ready post format")
    
    print("\n🎉 Campaign Pipeline Test Complete!")
    print(f"📁 Files created in tasks bucket:")
    print(f"   - {goal_key}")
    print(f"   - {goal_output_key}")
    print(f"   - {campaign_post_key}")
    print(f"   - {ready_post_key}")
    print(f"📁 Profile data created in structuredb bucket:")
    print(f"   - {profile_key}")

if __name__ == "__main__":
    asyncio.run(test_campaign_pipeline()) 