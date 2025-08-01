#!/usr/bin/env python3
"""
Test script for Enhanced Goal Handler and Query Handler modules
Demonstrates the new platform-aware schema and RAG implementation
"""

import asyncio
import json
import os
from datetime import datetime
from utils.r2_client import R2Client
from utils.logging import logger
from config import R2_CONFIG, STRUCTUREDB_R2_CONFIG

async def create_test_goal_file(platform: str, username: str):
    """Create a test goal file in the new schema format"""
    
    r2_client = R2Client(config=R2_CONFIG)
    
    # Sample goal data in new format
    goal_data = {
        "persona": "Professional beauty influencer with authentic, engaging voice that educates and inspires",
        "timeline": 30,
        "goal": "Double engagement rate from current 5% to 10% within 30 days by creating more interactive content",
        "instructions": "Focus on educational content about makeup techniques, maintain premium brand image, avoid controversial topics",
        "status": "pending",
        "created_at": datetime.now().isoformat(),
        "platform": platform,
        "username": username
    }
    
    # New schema path: tasks/goal/<platform>/<username>/goal_*.json
    goal_key = f"tasks/goal/{platform}/{username}/goal_1.json"
    
    success = await r2_client.write_json(goal_key, goal_data)
    if success:
        logger.info(f"✅ Created test goal file: {goal_key}")
        logger.info(f"Goal: {goal_data['goal']}")
        logger.info(f"Timeline: {goal_data['timeline']} days")
        logger.info(f"Persona: {goal_data['persona']}")
    else:
        logger.error(f"❌ Failed to create test goal file: {goal_key}")
    
    return success

async def create_test_profile_data(platform: str, username: str):
    """Create test profile data in structuredb"""
    
    r2_structuredb = R2Client(config=STRUCTUREDB_R2_CONFIG)
    
    # Sample profile data with posts for analysis
    profile_data = {
        "username": username,
        "bio": "Professional makeup artist & beauty educator ✨ Sharing tips & tutorials 💄 DM for collaborations",
        "followers": 15000,
        "following": 800,
        "posts": [
            {
                "caption": "New tutorial on creating the perfect smoky eye! What's your favorite eyeshadow technique? 💫",
                "hashtags": ["#MakeupTutorial", "#SmokyEye", "#BeautyTips", "#MUA", "#EyeshadowLook"],
                "likes": 850,
                "comments": 47,
                "type": "video"
            },
            {
                "caption": "Fresh face Friday! Sometimes less is more. Natural beauty shines through ✨",
                "hashtags": ["#NaturalBeauty", "#FreshFace", "#SkinCare", "#Minimal", "#GlowUp"],
                "likes": 1200,
                "comments": 65,
                "type": "photo"
            },
            {
                "caption": "Behind the scenes of today's photoshoot. The power of good lighting and the right products! What's your favorite makeup brand?",
                "hashtags": ["#BTS", "#Photoshoot", "#MakeupArtist", "#Professional", "#Beauty"],
                "likes": 950,
                "comments": 38,
                "type": "carousel"
            },
            {
                "caption": "Quick morning routine for busy days! 5 minutes to look polished 💄 Save this post for later!",
                "hashtags": ["#QuickMakeup", "#MorningRoutine", "#BeautyHacks", "#TimesSaver", "#Minimal"],
                "likes": 1400,
                "comments": 82,
                "type": "video"
            },
            {
                "caption": "Color theory in makeup - warm vs cool tones can completely change your look! Which do you prefer?",
                "hashtags": ["#ColorTheory", "#MakeupScience", "#BeautyEducation", "#WarmTones", "#CoolTones"],
                "likes": 750,
                "comments": 29,
                "type": "photo"
            }
        ],
        "engagement_rate": 0.05,
        "platform": platform,
        "last_updated": datetime.now().isoformat()
    }
    
    # New schema path: platform/username/username.json
    profile_key = f"{platform}/{username}/{username}.json"
    
    success = await r2_structuredb.write_json(profile_key, profile_data)
    if success:
        logger.info(f"✅ Created test profile data: {profile_key}")
        logger.info(f"Followers: {profile_data['followers']}")
        logger.info(f"Engagement Rate: {profile_data['engagement_rate']:.1%}")
        logger.info(f"Total Posts: {len(profile_data['posts'])}")
    else:
        logger.error(f"❌ Failed to create test profile data: {profile_key}")
    
    return success

async def create_test_prophet_analysis(platform: str, username: str):
    """Create test prophet analysis data"""
    
    r2_client = R2Client(config=R2_CONFIG)
    
    # Sample prophet analysis data
    prophet_data = {
        "username": username,
        "platform": platform,
        "analysis_date": datetime.now().isoformat(),
        "primary_analysis": {
            "engagement": {
                "average_engagement_rate": 0.05,
                "best_performing_content": "video",
                "content_type_analysis": {
                    "video": {"average_engagement": 0.08, "count": 15},
                    "photo": {"average_engagement": 0.04, "count": 25},
                    "carousel": {"average_engagement": 0.06, "count": 8}
                }
            },
            "posting_trends": {
                "most_active_day": "Friday",
                "hour_formatted": "6 PM",
                "optimal_posting_frequency": "daily",
                "content_consistency": 0.75
            },
            "audience_insights": {
                "peak_engagement_times": ["6PM", "8PM", "12PM"],
                "preferred_content_types": ["tutorials", "tips", "behind_scenes"],
                "interaction_patterns": "high_comments_to_likes_ratio"
            }
        },
        "growth_predictions": {
            "follower_growth_rate": 0.03,
            "engagement_trend": "increasing",
            "projected_30_day_growth": 450
        }
    }
    
    # New schema path: prophet_analysis/platform/username/analysis_*.json
    prophet_key = f"prophet_analysis/{platform}/{username}/analysis_1.json"
    
    success = await r2_client.write_json(prophet_key, prophet_data)
    if success:
        logger.info(f"✅ Created test prophet analysis: {prophet_key}")
        logger.info(f"Avg Engagement: {prophet_data['primary_analysis']['engagement']['average_engagement_rate']:.1%}")
        logger.info(f"Best Content: {prophet_data['primary_analysis']['engagement']['best_performing_content']}")
    else:
        logger.error(f"❌ Failed to create test prophet analysis: {prophet_key}")
    
    return success

async def create_test_rules(platform: str, username: str):
    """Create test rules data"""
    
    r2_client = R2Client(config=R2_CONFIG)
    
    # Sample rules data
    rules_data = {
        "content_guidelines": {
            "allowed_topics": ["makeup tutorials", "beauty tips", "product reviews", "skincare advice"],
            "prohibited_topics": ["political content", "controversial subjects", "competitor promotion"],
            "tone_requirements": "professional yet approachable, educational, inspiring"
        },
        "brand_voice": {
            "personality": "expert educator",
            "communication_style": "friendly professional",
            "key_values": ["authenticity", "education", "empowerment", "quality"]
        },
        "engagement_rules": {
            "response_style": "thoughtful and helpful",
            "cta_preferences": "questions and educational prompts",
            "hashtag_limits": {"min": 3, "max": 8}
        },
        "visual_guidelines": {
            "aesthetic": "clean and professional",
            "color_palette": ["neutrals", "soft pinks", "gold accents"],
            "style": "high-quality photography with good lighting"
        }
    }
    
    # New schema path: rules/platform/username/rules.json
    rules_key = f"rules/{platform}/{username}/rules.json"
    
    success = await r2_client.write_json(rules_key, rules_data)
    if success:
        logger.info(f"✅ Created test rules: {rules_key}")
    else:
        logger.error(f"❌ Failed to create test rules: {rules_key}")
    
    return success

async def check_goal_handler_output(platform: str, username: str):
    """Check if Goal Handler generated output"""
    
    r2_client = R2Client(config=R2_CONFIG)
    
    # Expected output path: generated_content/platform/username/posts.json
    output_key = f"generated_content/{platform}/{username}/posts.json"
    
    logger.info(f"🔍 Checking Goal Handler output at: {output_key}")
    
    output_data = await r2_client.read_json(output_key)
    if output_data:
        logger.info(f"✅ Goal Handler output found!")
        logger.info(f"Posts generated: {len(output_data.get('posts', []))}")
        logger.info(f"Strategy: {output_data.get('strategy', {})}")
        
        # Show sample post
        posts = output_data.get('posts', [])
        if posts:
            sample_post = posts[0]
            logger.info(f"Sample post content: {sample_post.get('content', [])}")
            logger.info(f"Sample theme: {sample_post.get('theme', 'N/A')}")
            
        return True
    else:
        logger.warning(f"⚠️ No Goal Handler output found yet")
        return False

async def check_query_handler_output(platform: str, username: str):
    """Check if Query Handler generated image-ready output"""
    
    r2_client = R2Client(config=R2_CONFIG)
    
    # Expected output path: image_ready_content/platform/username/image_ready_posts.json
    output_key = f"image_ready_content/{platform}/{username}/image_ready_posts.json"
    
    logger.info(f"🔍 Checking Query Handler output at: {output_key}")
    
    output_data = await r2_client.read_json(output_key)
    if output_data:
        logger.info(f"✅ Query Handler output found!")
        logger.info(f"Image-ready posts: {len(output_data.get('posts', []))}")
        
        # Show sample transformed post
        posts = output_data.get('posts', [])
        if posts:
            sample_post = posts[0]
            logger.info(f"Sample transformed text: {sample_post.get('text', 'N/A')}")
            logger.info(f"Sample hashtags: {sample_post.get('hashtags', [])}")
            logger.info(f"Sample CTA: {sample_post.get('cta', 'N/A')}")
            logger.info(f"Sample image prompt: {sample_post.get('image_prompt', 'N/A')[:100]}...")
            
        return True
    else:
        logger.warning(f"⚠️ No Query Handler output found yet")
        return False

async def main():
    """Main test function"""
    
    # Test configuration
    platform = "instagram"
    username = "beautyexpert_test"
    
    logger.info("🚀 Starting Enhanced Modules Test")
    logger.info(f"Platform: {platform}")
    logger.info(f"Username: {username}")
    logger.info("=" * 60)
    
    # Step 1: Create test data
    logger.info("📝 Step 1: Creating test data...")
    
    goal_created = await create_test_goal_file(platform, username)
    profile_created = await create_test_profile_data(platform, username)
    prophet_created = await create_test_prophet_analysis(platform, username)
    rules_created = await create_test_rules(platform, username)
    
    if not all([goal_created, profile_created]):
        logger.error("❌ Failed to create required test data. Exiting.")
        return
    
    logger.info("✅ Test data created successfully!")
    logger.info("=" * 60)
    
    # Step 2: Instructions for running modules
    logger.info("📋 Step 2: Manual Module Execution")
    logger.info("To test the enhanced modules:")
    logger.info("")
    logger.info("1. Run Goal Handler:")
    logger.info("   python3 goal_rag_handler.py")
    logger.info("")
    logger.info("2. Wait for processing to complete, then run Query Handler:")
    logger.info("   python3 query_handler.py")
    logger.info("")
    logger.info("3. Run this test script again to check outputs:")
    logger.info("   python3 test_enhanced_modules.py --check-only")
    logger.info("")
    
    # Step 3: Check if running in check-only mode
    import sys
    if "--check-only" in sys.argv:
        logger.info("🔍 Step 3: Checking outputs...")
        
        goal_output = await check_goal_handler_output(platform, username)
        await asyncio.sleep(1)
        query_output = await check_query_handler_output(platform, username)
        
        if goal_output and query_output:
            logger.info("🎉 SUCCESS: Both modules have produced expected outputs!")
            logger.info("✅ Enhanced Goal Handler and Query Handler are working correctly")
        elif goal_output:
            logger.info("⏳ Goal Handler completed, waiting for Query Handler...")
        else:
            logger.info("⏳ Waiting for Goal Handler to process the goal file...")
    
    logger.info("=" * 60)
    logger.info("🏁 Test script completed")

if __name__ == "__main__":
    asyncio.run(main()) 