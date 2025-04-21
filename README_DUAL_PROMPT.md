# Dual-Prompt System for Content Recommendations

This document outlines the implementation of a dual-prompt system for content recommendations, specifically tailored for:
1. Branding accounts (business/commercial accounts)
2. Non-branding accounts (personal/individual accounts)

## Overview

The system intelligently detects account type and activates different instruction sets based on account classification:

- **Branding accounts**: Uses the enhanced competitive analysis prompt that focuses on industry competitors, market positioning, and brand strategy
- **Non-branding accounts**: Uses a personalized content prompt that emphasizes the account's authentic voice, posting history, and personal style

## Key Components

### 1. Account Type Detection

The system detects account type through:
- Analysis of post content, looking for business-related terminology
- Evaluation of hashtag patterns (business vs. personal)
- Explicit account type settings when available

### 2. Branding Account Prompt

For business and brand accounts, the system:
- Analyzes competitor accounts and strategies
- Identifies market positioning opportunities
- Generates content that strategically outperforms competitors
- Provides visual concepts that differentiate from competitor aesthetics

### 3. Non-Branding Account Prompt

For personal accounts, the system:
- Analyzes personal posting history, themes and voice
- Maintains the account holder's authentic style and tone
- Generates content that feels like a natural extension of existing content
- Leverages news API integration for relevant trending topics (when appropriate)

### 4. News API Integration

- News API is only used for non-branding accounts
- Fetches current news relevant to the account's interests and content themes
- Helps personal accounts stay current with trending topics

## Implementation Details

The dual-prompt system is implemented in:

1. `rag_implementation.py`:
   - `_construct_enhanced_prompt()` - For branding accounts
   - `_construct_non_branding_prompt()` - For personal accounts
   - `generate_recommendation()` - Main entry point that selects appropriate prompt

2. `recommendation_generation.py`:
   - `generate_content_plan()` - Detects account type and routes processing
   - `generate_next_post_prediction()` - Account-aware post generation
   - `generate_recommendations()` - Batch recommendations with account awareness

## Usage Guide

The system automatically determines account type, but you can also explicitly specify it:

```python
# Let the system determine account type automatically
content_plan = recommendation_engine.generate_content_plan(data)

# Explicitly specify account type
data['account_type'] = 'branding'  # or 'non-branding'
content_plan = recommendation_engine.generate_content_plan(data)
```

## Expected Response Structures

### Branding Account Response

```json
{
    "primary_analysis": "Analysis of brand positioning and strategy",
    "competitor_analysis": {
        "competitor1": "Analysis of competitor strategy",
        "competitor2": "Analysis of competitor strategy"
    },
    "recommendations": "Strategic recommendations for brand positioning",
    "next_post": {
        "caption": "Strategic brand-aligned caption",
        "hashtags": ["#BrandHashtag1", "#BrandHashtag2"],
        "call_to_action": "Brand-aligned CTA",
        "visual_prompt": "Brand-aligned visual concept"
    }
}
```

### Non-Branding Account Response

```json
{
    "account_analysis": "Analysis of personal posting style and themes",
    "content_recommendations": "Authentic content suggestions matching personal style",
    "next_post": {
        "caption": "Personal authentic caption matching user's voice",
        "hashtags": ["#PersonalStyle", "#AuthenticVoice"],
        "call_to_action": "Personal engagement prompt",
        "visual_prompt": "Visual concept aligned with personal aesthetic"
    }
}
```

## Testing

The system includes comprehensive tests for both account types in `rag_implementation.py`. Run the tests with:

```bash
python rag_implementation.py
``` 