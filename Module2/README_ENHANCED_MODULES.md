# Enhanced Goal Handler & Query Handler Modules

## Overview

This document outlines the enhanced Goal Handler and Query Handler modules that implement a new platform-aware schema with robust RAG (Retrieval-Augmented Generation) capabilities for deep analysis of scraped profile data and prophet analytics. These modules generate accurate, theme-aligned content to achieve user-defined goals.

## Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Goal Handler   │───▶│  Query Handler  │───▶│ Image Generator │
│                 │    │                 │    │                 │
│ • Deep RAG      │    │ • Genius RAG    │    │ • Image Ready   │
│ • Strategy      │    │ • Transformation│    │ • Posts         │
│ • Content Gen   │    │ • Theme Align   │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         ▲                        ▲                        ▲
         │                        │                        │
   ┌─────────┐              ┌─────────┐              ┌─────────┐
   │Profile  │              │Generated│              │Image    │
   │Data &   │              │Content  │              │Ready    │
   │Prophet  │              │         │              │Posts    │
   │Analysis │              │         │              │         │
   └─────────┘              └─────────┘              └─────────┘
```

## Platform-Aware Schema

### New Directory Structure

```
tasks/
├── goal/
│   ├── instagram/
│   │   └── username/
│   │       └── goal_*.json
│   └── twitter/
│       └── username/
│           └── goal_*.json
├── prophet_analysis/
│   ├── instagram/
│   │   └── username/
│   │       └── analysis_*.json
│   └── twitter/
│       └── username/
│           └── analysis_*.json
└── rules/
    ├── instagram/
    │   └── username/
    │       └── rules.json
    └── twitter/
        └── username/
            └── rules.json

structuredb/
├── instagram/
│   └── username/
│       └── username.json
└── twitter/
    └── username/
        └── username.json

generated_content/
├── instagram/
│   └── username/
│       └── posts.json
└── twitter/
    └── username/
        └── posts.json

image_ready_content/
├── instagram/
│   └── username/
│       └── image_ready_posts.json
└── twitter/
    └── username/
        └── image_ready_posts.json
```

## Goal Handler Module

### Purpose
Monitors for new goal files and generates strategic content plans using deep RAG analysis of profile data and prophet analytics.

### Input Schema

**Goal File Structure** (`tasks/goal/<platform>/<username>/goal_*.json`):
```json
{
  "persona": "Target persona to mimic for content creation",
  "timeline": 30,
  "goal": "Specific objective (e.g., 'Double engagement rate from 5% to 10%')",
  "instructions": "Additional guidelines and precautions",
  "status": "pending",
  "created_at": "2024-01-01T00:00:00",
  "platform": "instagram",
  "username": "username"
}
```

### Core Components

#### 1. DeepRAGAnalyzer
- **Purpose**: Performs advanced analysis of profile data to extract patterns
- **Key Methods**:
  - `analyze_profile_patterns()`: Extract posting frequency, engagement patterns, content themes
  - `_analyze_voice_characteristics()`: Determine tone, formality, enthusiasm level
  - `_analyze_hashtag_patterns()`: Strategic hashtag analysis with performance metrics
  - `_identify_engagement_drivers()`: What specifically drives engagement for this account

#### 2. StrategyCalculator
- **Purpose**: Calculates optimal posting strategy based on goals and analysis
- **Key Methods**:
  - `calculate_posting_strategy()`: Determine posts needed and intervals
  - `_parse_goal_requirements()`: Extract numeric requirements from goal text
  - `_calculate_posts_needed()`: Account for goal difficulty and consistency

#### 3. ContentGenerator
- **Purpose**: Generates theme-aligned content using RAG insights
- **Key Methods**:
  - `generate_post_content()`: Create posts aligned with strategy
  - `_generate_single_post()`: Individual post generation with context

### Output Schema

**Generated Content** (`generated_content/<platform>/<username>/posts.json`):
```json
{
  "goal_analysis": { "original goal data" },
  "strategy": {
    "posts_needed": 15,
    "posting_interval_hours": 48.0,
    "rationale": "Strategy explanation",
    "timeline_days": 30
  },
  "profile_insights": {
    "voice_characteristics": { "tone analysis" },
    "hashtag_patterns": { "strategic hashtag insights" },
    "engagement_drivers": ["factors that drive engagement"]
  },
  "posts": [
    {
      "post_id": 1,
      "content": ["Sentence 1", "Sentence 2", "Sentence 3"],
      "image_hint": "Visual description for image generator",
      "caption": "Concise caption",
      "theme": "Post theme"
    }
  ],
  "summary": {
    "content_created_reason": "Why content was created this way",
    "goal_alignment": "How content aligns with goal",
    "prophet_integration": "How prophet analysis was used"
  }
}
```

### Key Features

1. **Deep Profile Analysis**: Extracts 8 different types of insights from profile data
2. **Smart Strategy Calculation**: Considers goal difficulty, account consistency, and engagement patterns
3. **Theme-Aligned Content**: Generates content that matches successful posting patterns
4. **Comprehensive Rationale**: Explains every decision made in the strategy

## Query Handler Module

### Purpose
Processes Goal Handler output and transforms posts into image-ready format using Genius-Level RAG analysis.

### Core Components

#### 1. GeniusRAGEngine
- **Purpose**: Advanced RAG implementation for deep theme analysis and content transformation
- **Key Analysis Areas**:
  - Voice characteristics (tone, formality, enthusiasm)
  - Hashtag patterns (performance-based strategy)
  - Content style preferences
  - Engagement drivers (what specifically works)
  - Visual themes and aesthetic preferences
  - CTA patterns and effectiveness
  - Audience preferences

#### 2. Enhanced Transformation Pipeline
- **Input**: Goal Handler's 3-sentence posts with themes
- **Process**: Genius-level analysis and transformation
- **Output**: Image-ready posts with optimized content

### Transformation Process

1. **Profile Insight Extraction**: Deep analysis of account patterns
2. **Content Transformation**: Convert 3 sentences to 1-2 optimized sentences
3. **Strategic Hashtag Generation**: Based on performance analysis
4. **CTA Optimization**: Match preferred engagement style
5. **Image Prompt Enhancement**: Align with visual themes

### Output Schema

**Image-Ready Content** (`image_ready_content/<platform>/<username>/image_ready_posts.json`):
```json
{
  "posts": [
    {
      "post_id": 1,
      "text": "Optimized 1-2 sentence post body",
      "hashtags": ["#strategic", "#hashtags", "#based", "#on", "#analysis"],
      "cta": "Compelling call-to-action matching preferred style",
      "image_prompt": "Detailed image description aligned with visual themes"
    }
  ],
  "profile_insights": {
    "voice_characteristics": { "detailed voice analysis" },
    "hashtag_patterns": { "performance-based hashtag strategy" },
    "engagement_drivers": ["specific engagement factors"]
  },
  "transformation_metadata": {
    "processed_at": "timestamp",
    "platform": "instagram",
    "username": "username",
    "total_posts": 15,
    "rag_version": "genius_level_v1",
    "theme_alignment": "high"
  }
}
```

## RAG Implementation Details

### Deep Profile Analysis (Goal Handler)

The Goal Handler performs 8 types of analysis:

1. **Posting Frequency**: Historical patterns, consistency scoring
2. **Engagement Patterns**: Rate analysis, trend detection, peak performance factors
3. **Content Themes**: TF-IDF extraction of dominant themes
4. **Successful Post Characteristics**: Analysis of top-performing content
5. **Persona Traits**: Voice, tone, personality extraction
6. **Optimal Timing**: Best posting times and frequency
7. **Visual Themes**: Aesthetic preferences from content analysis
8. **CTA Patterns**: Effectiveness analysis of different call-to-action styles

### Genius-Level Transformation (Query Handler)

The Query Handler's RAG engine analyzes:

1. **Voice Characteristics**: 
   - Dominant tone (casual/professional/playful)
   - Formality level and sentence structure
   - Enthusiasm indicators

2. **Strategic Hashtag Analysis**:
   - Performance correlation analysis
   - Optimal hashtag count calculation
   - Brand vs community hashtag categorization

3. **Content Style Preferences**:
   - Caption length optimization
   - Question usage patterns
   - Emoji style analysis
   - Storytelling style identification

4. **Engagement Driver Identification**:
   - What specifically drives engagement
   - Personal touch indicators
   - Trend awareness patterns

## Usage Instructions

### 1. Setup Test Data
```bash
cd Module2
python3 test_enhanced_modules.py
```

### 2. Run Goal Handler
```bash
python3 goal_rag_handler.py
```

### 3. Run Query Handler
```bash
python3 query_handler.py
```

### 4. Check Results
```bash
python3 test_enhanced_modules.py --check-only
```

## API Endpoints

### Goal Handler
- Runs as file watcher monitoring `tasks/goal/` directory
- Processes files automatically when detected

### Query Handler
- **Port**: 8001
- **Endpoints**:
  - `POST /process-posts`: Process specific user posts
  - `POST /scan-new-posts`: Scan for new Goal Handler outputs

## Error Handling

Both modules implement comprehensive error handling:

1. **Data Validation**: Strict schema validation for all inputs
2. **Fallback Systems**: Intelligent fallbacks when AI generation fails
3. **Retry Logic**: Automatic retry with exponential backoff
4. **Logging**: Detailed logging for debugging and monitoring

## Performance Optimizations

1. **Parallel Processing**: Multiple independent operations run concurrently
2. **Caching**: Profile insights cached to avoid recomputation
3. **Rate Limiting**: Built-in delays to respect API limits
4. **Memory Management**: Efficient data handling for large datasets

## Dependencies

```python
# Core
asyncio
json
re
datetime

# AI/ML
google-generativeai
scikit-learn
numpy
chromadb
langchain

# Infrastructure
aiohttp
fastapi
uvicorn
tenacity
watchdog

# Custom
utils.r2_client
utils.status_manager
utils.logging
config
```

## Configuration

Ensure your `config.py` includes:

```python
GEMINI_CONFIG = {
    "api_key": "your-gemini-api-key",
    "model": "gemini-2.0-flash",
    "max_tokens": 2000,
    "temperature": 0.2,
    "top_p": 0.95,
    "top_k": 40
}

R2_CONFIG = {
    "endpoint_url": "your-r2-endpoint",
    "aws_access_key_id": "your-access-key",
    "aws_secret_access_key": "your-secret-key",
    "bucket_name": "tasks"
}

STRUCTUREDB_R2_CONFIG = {
    "endpoint_url": "your-r2-endpoint",
    "aws_access_key_id": "your-access-key",
    "aws_secret_access_key": "your-secret-key",
    "bucket_name": "structuredb"
}
```

## Monitoring and Debugging

1. **Logs**: Check detailed logs for processing status
2. **Output Validation**: Use test script to verify outputs
3. **Schema Compliance**: All outputs follow strict schemas
4. **Performance Metrics**: Track processing times and success rates

## Future Enhancements

1. **Real-time Processing**: WebSocket support for live updates
2. **Advanced Analytics**: More sophisticated engagement prediction
3. **Multi-language Support**: Content generation in multiple languages
4. **A/B Testing**: Built-in content variation testing
5. **Performance Analytics**: Detailed success metrics tracking

## Troubleshooting

### Common Issues

1. **Missing Dependencies**: Install required packages
2. **API Limits**: Check rate limiting and timeouts
3. **Schema Validation**: Ensure input data follows correct format
4. **File Permissions**: Verify R2 access permissions

### Debug Mode
Set `PYTHONPATH` and run with verbose logging:
```bash
export PYTHONPATH=/path/to/Module2
python3 -m logging.basicConfig level=DEBUG goal_rag_handler.py
```

---

## Summary

The enhanced Goal Handler and Query Handler modules provide:

✅ **Platform-aware schema** with proper directory organization  
✅ **Deep RAG analysis** of profile data and engagement patterns  
✅ **Intelligent strategy calculation** based on goals and analytics  
✅ **Theme-aligned content generation** that matches successful patterns  
✅ **Genius-level content transformation** for image-ready posts  
✅ **Comprehensive error handling** and fallback systems  
✅ **Detailed logging and monitoring** for debugging  
✅ **Scalable architecture** supporting multiple platforms  

These modules represent a significant upgrade in content generation capability, providing sophisticated analysis and strategy development that adapts to each account's unique characteristics and goals. 