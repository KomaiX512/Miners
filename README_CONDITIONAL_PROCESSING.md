# Conditional Social Media Processing Guide

This guide explains how to use the conditional processing functionality for Instagram and Twitter in the MinerAb system.

## Overview

The system now supports processing data from multiple social media platforms:
- Instagram (original functionality)
- Twitter/X (new functionality)

Each platform has its own processing pipeline with platform-specific storage paths and processing logic, while maintaining consistent output formats.

## Command-Line Usage

### Process an Instagram Account

```bash
python main.py --instagram <instagram_username>
```
Example:
```bash
python main.py --instagram maccosmetics
```

### Process a Twitter Account

```bash
python main.py --twitter <twitter_username>
```
Example:
```bash
python main.py --twitter elonmusk
```

### Combined Mode - Process Either Platform

```bash
python main.py --platform <instagram|twitter> <username>
```
Example:
```bash
python main.py --platform twitter elonmusk
python main.py --platform instagram maccosmetics
```

### Backward Compatibility

The original command still works but defaults to Instagram:
```bash
python main.py process_username <instagram_username>
```

### Automated Processing

Run both Instagram and Twitter scrapers with content processor in automated mode:
```bash
python main.py run_automated
```

Run all systems simultaneously (Instagram scraper, Twitter scraper, content processor, and Module2):
```bash
python main.py run_all
```

## File Structure Changes

### Platform-Specific Path Structure

All output files now follow a platform-specific path structure:

```
tasks/
├── recommendations/
│   ├── instagram/
│   │   └── <username>/
│   │       └── recommendation_1.json
│   └── twitter/
│       └── <username>/
│           └── recommendation_1.json
├── competitor_analysis/
│   ├── instagram/
│   │   └── <username>/
│   │       └── <competitor>/
│   │           └── analysis_1.json
│   └── twitter/
│       └── <username>/
│           └── <competitor>/
│               └── analysis_1.json
├── next_posts/
│   ├── instagram/
│   │   └── <username>/
│   │       └── post_1.json
│   └── twitter/
│       └── <username>/
│           └── post_1.json
└── engagement_strategies/
    ├── instagram/
    │   └── <username>/
    │       └── strategies_1.json
    └── twitter/
        └── <username>/
            └── strategies_1.json
```

### Profile Info Storage

- Instagram profile info: `ProfileInfo/<username>.json`
- Twitter profile info: `ProfileInfo/twitter/<username>/profileinfo.json`

## Platform Differences

| Feature | Instagram | Twitter |
|---------|----------|---------|
| Data Source | Actor: `apify/instagram-profile-scraper` | Actor: `memo23/apify-twitter-profile-scraper` |
| API Token | `[REDACTED - Use your own token]` | `[REDACTED - Use your own token]` |
| Storage Path | `<username>/<username>.json` | `twitter/<username>/<username>.json` |
| Trigger File | `tasks/AccountInfo/<username>/info.json` | `tasks/ProfileInfo/twitter/<username>/profileinfo.json` |
| Output Structure | Contains user posts with engagement metrics | Contains user tweets with engagement metrics |
| Engagement Metrics | Likes, Comments | Likes, Retweets, Replies, Quotes |
| Recommendations | Post captions, hashtags, call to action | Tweet text, hashtags, media suggestions, follow-up tweets |

## Adding Support for a New Platform

To add support for a new social media platform:

1. Create a new scraper class similar to `InstagramScraper` and `TwitterScraper`
2. Implement platform-specific methods for extracting profile info
3. Update `process_social_data()` to detect the new platform
4. Implement a `process_<platform>_data()` method 
5. Add a platform-specific command-line argument
6. Ensure all export methods use the platform-specific paths

## Troubleshooting

### Common Errors

**Invalid Platform Error**:
```
❌ Invalid platform: facebook. Use 'instagram' or 'twitter'
```
Solution: Use only 'instagram' or 'twitter' as platform names.

**Import Error for Twitter**:
```
❌ Error in Twitter-only mode: No module named 'twitter_scraper'
```
Solution: Ensure twitter_scraper.py is in the same directory as main.py.

**Failed to scrape profile**:
```
❌ Failed to process Twitter user <username>: Failed to scrape Twitter profile: <username>
```
Solution: Check that the username exists and is publicly accessible.

### Platform-Specific Notes

**Twitter**:
- The Twitter scraper supports both `@username` and `username` formats
- Handle rate limiting by adding delays between requests
- Twitter usernames are case-sensitive

**Instagram**:
- Some Instagram accounts may be private and inaccessible
- Rate limiting may affect scraping multiple accounts quickly

## Advanced Usage

### Processing Files Directly

You can process existing data files directly:

**Twitter**:
```bash
python3 -c "from main import ContentRecommendationSystem; system = ContentRecommendationSystem(); system.run_pipeline('twitter/elonmusk/elonmusk.json')"
```

**Instagram**:
```bash
python3 -c "from main import ContentRecommendationSystem; system = ContentRecommendationSystem(); system.run_pipeline('maccosmetics/maccosmetics.json')"
```

### Continuous Processing

For production environments, use the continuous processing mode:
```bash
python main.py run_automated
```

This will:
1. Start the Instagram scraper to process `tasks/AccountInfo/<username>/info.json` files
2. Start the Twitter scraper to process `tasks/ProfileInfo/twitter/<username>/profileinfo.json` files
3. Process both types of content as they become available 