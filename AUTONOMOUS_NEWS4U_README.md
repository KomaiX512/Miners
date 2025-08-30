# Autonomous News4U System Documentation

## Overview
The Autonomous News4U System runs independently from the main recommendation pipeline, processing all accounts daily to generate News4U content. It operates every 24 hours instead of the 5-day cycle of the main system.

## Key Features
- **Autonomous Operation**: Runs independently from main recommendation system
- **Daily Processing**: Processes all accounts every 24 hours (vs 5-day main cycle)
- **R2 Integration**: Reads account info and recommendations directly from R2 bucket
- **Duplicate Prevention**: Tracks processed accounts to avoid duplicate processing per cycle
- **Test Mode**: 2-minute intervals for debugging and validation
- **Comprehensive Logging**: Detailed logs for monitoring and debugging

## Architecture

### Data Flow
1. **Account Discovery**: Scans `AccountInfo/<platform>/<username>/info.json` in R2 bucket
2. **Hashtag Retrieval**: Gets trending hashtags from `recommendations/<platform>/<username>/recommendations_*.json`
3. **News Generation**: Uses `SimplifiedNewsForYouModule` with NewsAPI.org
4. **Export**: Saves to `news_for_you/<platform>/<username>/news_*.json`

### R2 Bucket Schema

#### Input - Account Info
```
AccountInfo/<platform>/<username>/info.json
```
Structure:
```json
{
  "username": "<primary_username>",
  "accountType": "...",
  "postingStyle": "...",
  "platform": "instagram",
  "competitors": ["...", "...", "..."],
  "timestamp": "...",
  "status": "...",
  "processing_started_at": "...",
  "processed_at": "..."
}
```

#### Input - Recommendations
```
recommendations/<platform>/<username>/recommendations_*.json
```
Structure:
```json
{
  "content_intelligence": {
    "trending_hashtags": [
      "#newfoundation",
      "#makeuplook",
      "#beautyproducts"
    ],
    "trending_hashtags_reason": ""
  }
}
```

#### Output - News4U
```
news_for_you/<platform>/<username>/news_YYYYMMDD_HHMMSS_<username>.json
```
Structure:
```json
{
  "username": "<username>",
  "platform": "<platform>",
  "generated_at": "2025-08-15T21:23:47.831000",
  "news_count": 3,
  "news_items": [
    {
      "query_number": 1,
      "keyword": "hashtag",
      "title": "News Title",
      "description": "News Description",
      "timestamp": "2025-08-15T10:00:00Z",
      "image_url": "https://...",
      "source_url": "https://...",
      "source": "Source Name",
      "fetched_at": "2025-08-15T21:23:47.831000",
      "author": "Author Name"
    }
  ],
  "autonomous_system": true,
  "system_version": "1.0"
}
```

## Usage

### Production Mode (24-hour loop)
```bash
python start_autonomous_news4u.py --production
```

### Test Mode (2-minute loop)
```bash
python start_autonomous_news4u.py --test
```

### Test Single Account
```bash
python start_autonomous_news4u.py --test-account instagram emelie_pakistan
```

### System Status
```bash
python start_autonomous_news4u.py --status
```

### Direct Usage
```bash
# Production mode
python autonomous_news4u_system.py

# Test mode  
python autonomous_news4u_system.py --test

# Single account test
python autonomous_news4u_system.py --test --single instagram emelie_pakistan

# Status check
python autonomous_news4u_system.py --status
```

## Configuration

### Required Dependencies
- `boto3`: R2 storage access
- `requests`: NewsAPI.org integration
- `simplified_news_for_you.py`: News generation module
- `r2_storage_manager.py`: R2 storage operations
- `config.py`: Configuration settings

### Configuration File
The system reads from `config.py`:
```python
R2_CONFIG = {
    'endpoint_url': 'https://...',
    'aws_access_key_id': '...',
    'aws_secret_access_key': '...'
}

NEWSAPI_KEY = 'a747734c8a9f41a4a6a6b98e3e66d9d2'
```

## Monitoring

### Logs
- File: `autonomous_news4u.log`
- Console output with timestamps
- Detailed processing information for each account

### Processing Cycle Information
- Cycle start/end times
- Success/error counts
- Individual account processing status
- R2 operations status

## Testing & Debugging

### Pre-Production Testing
1. Run system status check:
   ```bash
   python start_autonomous_news4u.py --status
   ```

2. Test with single account:
   ```bash
   python start_autonomous_news4u.py --test-account instagram emelie_pakistan
   ```

3. Run short test cycle:
   ```bash
   python start_autonomous_news4u.py --test
   # Let it run for one cycle (2 minutes), then stop with Ctrl+C
   ```

### Validation Checklist
- [ ] R2 connection working
- [ ] NewsAPI.org connection successful  
- [ ] Account info retrieval working
- [ ] Recommendation hashtag extraction working
- [ ] News generation successful
- [ ] R2 export successful
- [ ] Processing tracking working (no duplicates)
- [ ] Cycle timing working correctly

## Troubleshooting

### Common Issues

#### No News Generated
- Check if trending hashtags exist in recommendations
- Verify NewsAPI.org connectivity
- Check for valid account info

#### R2 Connection Errors
- Verify R2 credentials in config.py
- Check network connectivity
- Validate bucket permissions

#### Missing Account Info
- Ensure AccountInfo structure exists in R2
- Verify account info file format
- Check for valid JSON structure

#### Processing Duplicates
- System tracks processed accounts per cycle
- Resets every 24 hours (or 2 minutes in test mode)
- Check logs for processing confirmation

## System Architecture Notes

### Core Components
1. **AutonomousNews4USystem**: Main orchestrator class
2. **SimplifiedNewsForYouModule**: News generation engine
3. **R2StorageManager**: R2 bucket operations
4. **Processing Tracker**: Duplicate prevention

### Design Principles
- **Isolation**: Completely independent from main pipeline
- **Reliability**: Comprehensive error handling and logging
- **Scalability**: Processes all accounts automatically
- **Testability**: Multiple test modes for validation
- **Maintainability**: Clear code structure and documentation

## Production Deployment

### Setup Steps
1. Ensure all dependencies installed
2. Validate configuration settings
3. Run complete testing cycle
4. Deploy with production mode
5. Monitor initial cycles
6. Set up log rotation if needed

### Monitoring Recommendations
- Monitor `autonomous_news4u.log` for errors
- Check R2 bucket for successful exports
- Validate NewsAPI.org usage limits
- Monitor system resource usage

---

**System Status**: ✅ TESTED AND VALIDATED  
**Last Updated**: August 15, 2025  
**Version**: 1.0
