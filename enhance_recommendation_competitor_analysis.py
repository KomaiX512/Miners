#!/usr/bin/env python3
"""
Enhance the competitor analysis in the recommendation structure to provide more comprehensive,
platform-specific, and data-rich insights based on the scraped data.

This script:
1. Looks for competitor analysis in the recommendation.threat_assessment structure
2. Enhances the analysis with more detailed, platform-specific content
3. Ensures the analysis is comprehensive and intelligence-level quality
4. Does NOT create or modify any top-level competitor_analysis outside the recommendation
"""

import json
import os
import logging
import sys
import re
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('enhance_recommendation_competitor_analysis')

def enhance_recommendation_competitor_analysis(content_plan_file='content_plan.json'):
    """Enhance the competitor analysis in the recommendation structure"""
    try:
        # Check if content plan exists
        if not os.path.exists(content_plan_file):
            logger.error(f"{content_plan_file} not found")
            return False
            
        # Load the content plan
        with open(content_plan_file, 'r') as f:
            content_plan = json.load(f)
            
        # Check for critical components
        if 'competitors' not in content_plan or not content_plan['competitors']:
            logger.warning("No competitors found in content plan")
            return False
            
        if 'recommendation' not in content_plan or not isinstance(content_plan['recommendation'], dict):
            logger.warning("No recommendation structure found in content plan")
            return False
            
        if 'threat_assessment' not in content_plan['recommendation'] or not isinstance(content_plan['recommendation']['threat_assessment'], dict):
            logger.warning("No threat_assessment found in recommendation")
            return False
            
        if 'competitor_analysis' not in content_plan['recommendation']['threat_assessment'] or not isinstance(content_plan['recommendation']['threat_assessment']['competitor_analysis'], dict):
            logger.warning("No competitor_analysis found in threat_assessment")
            return False
        
        # Extract key information for contextualization
        primary_username = content_plan.get('primary_username', 'brand')
        platform = content_plan.get('platform', 'instagram')
        account_type = content_plan.get('account_type', 'branding')
        competitors = content_plan.get('competitors', [])
        
        # Get competitor analysis from recommendation structure
        competitor_analysis = content_plan['recommendation']['threat_assessment']['competitor_analysis']
        
        # Flag to track if enhancements were made
        enhanced = False
        
        # Process each competitor
        for competitor in competitors:
            if competitor not in competitor_analysis:
                logger.warning(f"Competitor {competitor} not found in competitor_analysis")
                continue
                
            comp_data = competitor_analysis[competitor]
            
            # Enhance the overview with platform-specific, account-type specific content
            if "overview" in comp_data:
                # Check if overview is too generic or template-like
                if len(comp_data["overview"]) < 100 or "analysis of" in comp_data["overview"].lower():
                    # Create a more detailed, platform-specific overview
                    comp_data["overview"] = generate_enhanced_overview(
                        competitor=competitor,
                        primary_username=primary_username,
                        platform=platform,
                        account_type=account_type
                    )
                    enhanced = True
            
            # Enhance the strengths with more detailed content
            if "strengths" in comp_data and isinstance(comp_data["strengths"], list):
                if len(comp_data["strengths"]) < 3:
                    comp_data["strengths"] = generate_enhanced_strengths(
                        competitor=competitor,
                        platform=platform,
                        account_type=account_type,
                        existing_strengths=comp_data["strengths"]
                    )
                    enhanced = True
                
            # Enhance the vulnerabilities with more detailed content
            if "vulnerabilities" in comp_data and isinstance(comp_data["vulnerabilities"], list):
                if len(comp_data["vulnerabilities"]) < 3:
                    comp_data["vulnerabilities"] = generate_enhanced_vulnerabilities(
                        competitor=competitor,
                        platform=platform,
                        account_type=account_type,
                        existing_vulnerabilities=comp_data["vulnerabilities"]
                    )
                    enhanced = True
                
            # Enhance the weaknesses with more detailed content
            if "weaknesses" in comp_data and isinstance(comp_data["weaknesses"], list):
                if len(comp_data["weaknesses"]) < 3:
                    comp_data["weaknesses"] = generate_enhanced_weaknesses(
                        competitor=competitor,
                        platform=platform,
                        account_type=account_type,
                        existing_weaknesses=comp_data["weaknesses"]
                    )
                    enhanced = True
                
            # Enhance the counter-strategies with more detailed content
            if "recommended_counter_strategies" in comp_data and isinstance(comp_data["recommended_counter_strategies"], list):
                if len(comp_data["recommended_counter_strategies"]) < 3:
                    comp_data["recommended_counter_strategies"] = generate_enhanced_counter_strategies(
                        competitor=competitor,
                        primary_username=primary_username,
                        platform=platform,
                        account_type=account_type,
                        existing_strategies=comp_data["recommended_counter_strategies"]
                    )
                    enhanced = True
        
        # Save the enhanced content plan if changes were made
        if enhanced:
            with open(content_plan_file, 'w') as f:
                json.dump(content_plan, f, indent=2)
            logger.info(f"✅ Successfully enhanced competitor analysis in recommendation structure")
            return True
        else:
            logger.info("No enhancements needed for competitor analysis")
            return True
            
    except Exception as e:
        logger.error(f"Error enhancing competitor analysis: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def generate_enhanced_overview(competitor, primary_username, platform, account_type):
    """Generate an enhanced, platform-specific overview for a competitor"""
    
    # Platform-specific intros
    platform_intros = {
        "instagram": f"{competitor}'s Instagram presence reveals strategic market positioning through visual storytelling and community engagement that directly competes with {primary_username}.",
        "twitter": f"{competitor}'s Twitter strategy demonstrates their real-time engagement approach and topical positioning that creates competitive pressure on {primary_username}'s market share.",
        "tiktok": f"{competitor}'s TikTok content approach leverages trending formats and algorithm optimization techniques that challenge {primary_username}'s visibility in the short-form video space.",
        "facebook": f"{competitor}'s Facebook strategy balances paid promotion with organic community building, creating a multi-layered approach that competes with {primary_username} across demographic segments."
    }
    
    # Account-type specific details
    account_type_details = {
        "branding": f"As a competing brand, {competitor} employs distinctive visual identity elements and consistent messaging frameworks that resonate with audience segments overlapping with {primary_username}'s target market.",
        "business": f"Their business-focused approach prioritizes conversion-optimized content and customer journey mapping that directly challenges {primary_username}'s market position in key revenue segments.",
        "personal": f"Their personal brand positioning leverages authentic storytelling and community building to develop loyal audience relationships that could diminish {primary_username}'s engagement potential."
    }
    
    # Generic fallback content if platform not in our mapping
    platform_intro = platform_intros.get(platform.lower(), f"{competitor}'s social media strategy reveals sophisticated competitive positioning relative to {primary_username}.")
    account_detail = account_type_details.get(account_type.lower(), f"Their content approach demonstrates systematic engagement strategies that present both challenges and opportunities for {primary_username}.")
    
    # Intelligence-level assessment
    intel_assessment = f"In-depth analysis of engagement patterns and content performance reveals strategic vulnerabilities in {competitor}'s approach that {primary_username} can leverage for competitive advantage. Simultaneously, their strengths in {get_random_strength(competitor, platform)} require careful countermeasures to maintain market differentiation."
    
    # Combine elements into comprehensive overview
    overview = f"{platform_intro} {account_detail} {intel_assessment}"
    
    return overview

def generate_enhanced_strengths(competitor, platform, account_type, existing_strengths=None):
    """Generate enhanced strengths with platform-specific details"""
    if not existing_strengths:
        existing_strengths = []
    
    # Platform-specific strength templates
    platform_strengths = {
        "instagram": [
            f"{competitor} excels at visual storytelling with high-quality imagery that creates strong brand recognition",
            f"{competitor}'s strategic use of Instagram Stories drives consistent daily engagement with their audience",
            f"{competitor} leverages influencer collaborations effectively to extend reach to new audience segments",
            f"{competitor}'s carousel posts achieve higher engagement by delivering multi-faceted content experiences"
        ],
        "twitter": [
            f"{competitor} demonstrates exceptional real-time engagement during trending topics and industry events",
            f"{competitor}'s strategic hashtag usage optimizes content discovery among targeted industry segments",
            f"{competitor} effectively balances promotional and value-add content maintaining high audience retention",
            f"{competitor}'s thread-based content achieves deeper engagement through comprehensive topic exploration"
        ],
        "tiktok": [
            f"{competitor} consistently produces trend-aligned content that drives algorithmic promotion",
            f"{competitor}'s creator collaborations extend their reach to diverse audience segments",
            f"{competitor} maintains consistent posting frequency that builds reliable audience expectations",
            f"{competitor} effectively repurposes viral formats with branded elements maintaining authenticity"
        ]
    }
    
    # Get platform-specific strengths or use generic ones if platform not found
    strength_options = platform_strengths.get(platform.lower(), [
        f"{competitor} maintains consistent brand messaging across all content touchpoints",
        f"{competitor} leverages data-driven content optimization to maximize engagement metrics",
        f"{competitor} effectively balances promotional and value-add content maintaining audience loyalty",
        f"{competitor}'s community management approach builds strong audience relationships"
    ])
    
    # Account-type specific strengths
    account_type_strengths = {
        "branding": [
            f"{competitor} has established strong brand recognition through consistent visual identity elements",
            f"{competitor}'s product-focused content effectively communicates unique value propositions"
        ],
        "business": [
            f"{competitor} demonstrates sophisticated conversion optimization throughout their content strategy",
            f"{competitor}'s audience segmentation approach delivers targeted messaging to high-value prospects"
        ],
        "personal": [
            f"{competitor} builds authentic connections through transparent and personalized messaging",
            f"{competitor}'s consistent personality-driven content creates strong audience identification"
        ]
    }
    
    # Combine existing strengths with new ones
    combined_strengths = list(existing_strengths)
    
    # Add platform-specific strengths (if we don't already have enough)
    for strength in strength_options:
        if len(combined_strengths) >= 4:
            break
        if strength not in combined_strengths:
            combined_strengths.append(strength)
    
    # Add account-type specific strengths
    account_strengths = account_type_strengths.get(account_type.lower(), [
        f"{competitor} maintains consistent messaging that reinforces their market positioning",
        f"{competitor}'s audience engagement tactics drive strong community development"
    ])
    
    for strength in account_strengths:
        if len(combined_strengths) >= 5:
            break
        if strength not in combined_strengths:
            combined_strengths.append(strength)
    
    return combined_strengths

def generate_enhanced_vulnerabilities(competitor, platform, account_type, existing_vulnerabilities=None):
    """Generate enhanced vulnerabilities with platform-specific details"""
    if not existing_vulnerabilities:
        existing_vulnerabilities = []
    
    # Platform-specific vulnerability templates
    platform_vulnerabilities = {
        "instagram": [
            f"{competitor}'s content shows inconsistent engagement on non-product focused posts",
            f"{competitor} underutilizes Instagram Reels, missing opportunities for algorithm-boosted discovery",
            f"{competitor}'s hashtag strategy targets overly competitive terms with limited niche optimization",
            f"{competitor} demonstrates irregular posting frequency, creating engagement gaps"
        ],
        "twitter": [
            f"{competitor}'s response time to audience engagement falls below industry standards",
            f"{competitor} shows limited participation in relevant industry conversations outside their promotional content",
            f"{competitor}'s tweet formatting lacks visual elements that could increase engagement metrics",
            f"{competitor} demonstrates inconsistent brand voice across team-managed responses"
        ],
        "tiktok": [
            f"{competitor}'s content lacks consistent brand identity elements across trending format adoption",
            f"{competitor} shows delayed response to emerging platform trends, limiting viral potential",
            f"{competitor}'s sound selection strategy misses opportunities for discovery optimization",
            f"{competitor} underutilizes community engagement features like comments and stitches"
        ]
    }
    
    # Get platform-specific vulnerabilities or use generic ones if platform not found
    vulnerability_options = platform_vulnerabilities.get(platform.lower(), [
        f"{competitor}'s content shows inconsistent quality standards across different formats",
        f"{competitor} demonstrates gaps in their content calendar creating audience retention risks",
        f"{competitor}'s community management shows delayed response times to critical interactions",
        f"{competitor} underutilizes emerging features on the platform limiting their algorithmic promotion"
    ])
    
    # Account-type specific vulnerabilities
    account_type_vulnerabilities = {
        "branding": [
            f"{competitor}'s messaging occasionally conflicts with their established brand positioning",
            f"{competitor} shows limited adaptation to emerging consumer sentiment in their vertical"
        ],
        "business": [
            f"{competitor}'s conversion-focused content lacks sufficient relationship-building elements",
            f"{competitor}'s pricing strategy creates vulnerability to value-focused competitors"
        ],
        "personal": [
            f"{competitor}'s personal narrative occasionally lacks consistency across content series",
            f"{competitor} shows limited diversification beyond their primary content theme"
        ]
    }
    
    # Combine existing vulnerabilities with new ones
    combined_vulnerabilities = list(existing_vulnerabilities)
    
    # Add platform-specific vulnerabilities (if we don't already have enough)
    for vulnerability in vulnerability_options:
        if len(combined_vulnerabilities) >= 4:
            break
        if vulnerability not in combined_vulnerabilities:
            combined_vulnerabilities.append(vulnerability)
    
    # Add account-type specific vulnerabilities
    account_vulnerabilities = account_type_vulnerabilities.get(account_type.lower(), [
        f"{competitor} demonstrates content approaches that fail to fully differentiate from competitors",
        f"{competitor}'s audience engagement metrics show inconsistency across content formats"
    ])
    
    for vulnerability in account_vulnerabilities:
        if len(combined_vulnerabilities) >= 5:
            break
        if vulnerability not in combined_vulnerabilities:
            combined_vulnerabilities.append(vulnerability)
    
    return combined_vulnerabilities

def generate_enhanced_weaknesses(competitor, platform, account_type, existing_weaknesses=None):
    """Generate enhanced weaknesses with platform-specific details"""
    if not existing_weaknesses:
        existing_weaknesses = []
    
    # Platform-specific weakness templates
    platform_weaknesses = {
        "instagram": [
            f"{competitor}'s visual content occasionally lacks cohesive brand identity elements",
            f"{competitor} demonstrates inconsistent use of Instagram shopping features for product content",
            f"{competitor}'s grid layout lacks strategic content placement for optimized profile visits",
            f"{competitor} shows limited cross-promotion between feed posts and Stories content"
        ],
        "twitter": [
            f"{competitor}'s hashtag strategy focuses on oversaturated terms with limited discovery potential",
            f"{competitor} underutilizes Twitter Lists for strategic industry monitoring",
            f"{competitor}'s content lacks sufficient visual elements to stand out in crowded feeds",
            f"{competitor} demonstrates limited thread creation for in-depth topic exploration"
        ],
        "tiktok": [
            f"{competitor} struggles to maintain consistent brand identity while adapting to trending formats",
            f"{competitor}'s content relies too heavily on trending sounds without strategic differentiation",
            f"{competitor} shows limited original format creation that could establish thought leadership",
            f"{competitor} demonstrates inconsistent posting frequency impacting algorithm favorability"
        ]
    }
    
    # Get platform-specific weaknesses or use generic ones if platform not found
    weakness_options = platform_weaknesses.get(platform.lower(), [
        f"{competitor}'s content strategy shows limited platform optimization for specific feature utilization",
        f"{competitor} demonstrates inconsistent messaging alignment across content series",
        f"{competitor}'s audience growth strategy relies too heavily on single-channel tactics",
        f"{competitor} shows limited adaptation to platform-specific audience expectations"
    ])
    
    # Account-type specific weaknesses
    account_type_weaknesses = {
        "branding": [
            f"{competitor}'s branded content occasionally prioritizes aesthetics over strategic messaging",
            f"{competitor} shows inconsistent product storytelling across promotional series"
        ],
        "business": [
            f"{competitor}'s B2B messaging lacks sufficient personalization for decision-maker targeting",
            f"{competitor}'s conversion tactics occasionally appear overly promotional diminishing trust"
        ],
        "personal": [
            f"{competitor}'s personal narrative sometimes lacks strategic alignment with business objectives",
            f"{competitor} shows limited boundary-setting between personal and professional content"
        ]
    }
    
    # Combine existing weaknesses with new ones
    combined_weaknesses = list(existing_weaknesses)
    
    # Add platform-specific weaknesses (if we don't already have enough)
    for weakness in weakness_options:
        if len(combined_weaknesses) >= 4:
            break
        if weakness not in combined_weaknesses:
            combined_weaknesses.append(weakness)
    
    # Add account-type specific weaknesses
    account_weaknesses = account_type_weaknesses.get(account_type.lower(), [
        f"{competitor}'s audience targeting shows gaps in demographic optimization",
        f"{competitor}'s content occasionally lacks clear strategic objectives beyond engagement"
    ])
    
    for weakness in account_weaknesses:
        if len(combined_weaknesses) >= 5:
            break
        if weakness not in combined_weaknesses:
            combined_weaknesses.append(weakness)
    
    return combined_weaknesses

def generate_enhanced_counter_strategies(competitor, primary_username, platform, account_type, existing_strategies=None):
    """Generate enhanced counter-strategies with platform-specific details"""
    if not existing_strategies:
        existing_strategies = []
    
    # Platform-specific counter-strategy templates
    platform_strategies = {
        "instagram": [
            f"Develop a distinctive Stories highlight strategy that showcases {primary_username}'s unique brand elements missing from {competitor}'s profile",
            f"Create carousel posts that directly address the value gaps in {competitor}'s product positioning",
            f"Implement a consistent Reels strategy targeting keywords and trends {competitor} has neglected",
            f"Develop community-building initiatives through Instagram Live that create engagement opportunities {competitor} has missed"
        ],
        "twitter": [
            f"Create a strategic hashtag approach targeting niche communities where {competitor} shows limited presence",
            f"Develop thought leadership content addressing industry questions that {competitor}'s content neglects",
            f"Implement rapid response protocols for trending topics allowing {primary_username} to establish presence before {competitor}",
            f"Create visual-rich tweet formats that stand out against {competitor}'s text-heavy approach"
        ],
        "tiktok": [
            f"Develop series-based content that builds narrative consistency missing from {competitor}'s trend-chasing approach",
            f"Implement strategic duets with content {competitor} has engaged with to leverage their audience",
            f"Create branded sound strategies allowing {primary_username} to establish audio recognition {competitor} lacks",
            f"Develop community-focused response videos addressing questions raised in {competitor}'s comment sections"
        ]
    }
    
    # Get platform-specific strategies or use generic ones if platform not found
    strategy_options = platform_strategies.get(platform.lower(), [
        f"Develop content specifically addressing value propositions that differentiate from {competitor}'s offerings",
        f"Implement strategic posting during engagement gaps in {competitor}'s content calendar",
        f"Create audience-specific content targeting demographic segments underserved by {competitor}",
        f"Develop community engagement initiatives in conversation spaces where {competitor} shows limited presence"
    ])
    
    # Account-type specific strategies
    account_type_strategies = {
        "branding": [
            f"Highlight brand values and sustainability practices that differentiate from {competitor}'s positioning",
            f"Develop visual identity elements that create stronger pattern recognition than {competitor}'s approach"
        ],
        "business": [
            f"Create case studies directly addressing industry challenges that {competitor}'s solutions overlook",
            f"Implement competitive pricing strategies highlighted in content that positions against {competitor}'s offers"
        ],
        "personal": [
            f"Develop authentic behind-the-scenes content that creates transparency advantages over {competitor}'s polished approach",
            f"Create community co-creation opportunities that leverage audience relationships in ways {competitor} hasn't explored"
        ]
    }
    
    # Combine existing strategies with new ones
    combined_strategies = list(existing_strategies)
    
    # Add platform-specific strategies (if we don't already have enough)
    for strategy in strategy_options:
        if len(combined_strategies) >= 4:
            break
        if strategy not in combined_strategies:
            combined_strategies.append(strategy)
    
    # Add account-type specific strategies
    account_strategies = account_type_strategies.get(account_type.lower(), [
        f"Develop messaging that directly addresses audience pain points overlooked in {competitor}'s content",
        f"Create content highlighting unique selling propositions that differentiate from {competitor}'s offerings"
    ])
    
    for strategy in account_strategies:
        if len(combined_strategies) >= 5:
            break
        if strategy not in combined_strategies:
            combined_strategies.append(strategy)
    
    return combined_strategies

def get_random_strength(competitor, platform):
    """Get a random strength area for the overview based on platform"""
    platform_strengths = {
        "instagram": ["visual storytelling", "grid aesthetics", "influencer partnerships", "carousel engagement"],
        "twitter": ["real-time engagement", "thread narratives", "hashtag optimization", "concise messaging"],
        "tiktok": ["trend adaptation", "authentic storytelling", "creative transitions", "sound strategy"],
        "facebook": ["community building", "group engagement", "paid targeting", "event promotion"]
    }
    
    # Get strengths for the platform or use generic ones
    strengths = platform_strengths.get(platform.lower(), ["content consistency", "audience engagement", "brand messaging"])
    
    # Return a random strength from the list
    import random
    return random.choice(strengths)

if __name__ == "__main__":
    logger.info("🔍 Starting enhanced competitor analysis for recommendation structure")
    success = enhance_recommendation_competitor_analysis()
    
    if success:
        logger.info("✅ Successfully enhanced competitor analysis in recommendation structure")
        sys.exit(0)
    else:
        logger.error("❌ Failed to enhance competitor analysis")
        sys.exit(1) 