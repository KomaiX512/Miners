# Environment Setup Guide

## Overview
This project uses environment variables to securely manage API tokens and configuration. **Never commit API tokens to git.**

## Quick Setup

### 1. Copy Environment Template
```bash
cp .env.example .env
```

### 2. Edit .env File
```bash
# Open .env and add your actual tokens
APIFY_API_TOKEN=your_actual_apify_token_here
```

### 3. Verify Setup
```bash
python test_env_setup.py
```

## Current Configuration

### ✅ Secured Files
- `facebook_scraper.py` - Uses `os.getenv("APIFY_API_TOKEN")`
- `instagram_scraper.py` - Uses `os.getenv("APIFY_API_TOKEN")`  
- `twitter_scraper.py` - Uses `os.getenv("APIFY_API_TOKEN")`

### ✅ Security Features
- `.env` files are in `.gitignore` (never committed)
- All scrapers use `load_dotenv()` to read environment variables
- Fallback values provided for development

### ✅ Dependencies
- `python-dotenv>=0.19.0` in requirements.txt
- All scrapers import and call `load_dotenv()`

## Production Deployment

### Docker
```dockerfile
ENV APIFY_API_TOKEN=your_token_here
```

### Server
```bash
export APIFY_API_TOKEN=your_token_here
```

### Cloud Platforms
Set environment variables in your platform's configuration:
- AWS: Lambda/ECS environment variables
- Heroku: Config vars
- Railway: Variables tab

## Troubleshooting

### Token Not Found
```bash
# Check if .env exists
ls -la .env

# Check if token is in .env
grep APIFY_API_TOKEN .env

# Test loading
python -c "from dotenv import load_dotenv; import os; load_dotenv(); print(os.getenv('APIFY_API_TOKEN'))"
```

### Import Errors
```bash
# Install dependencies
pip install -r requirements.txt
```

## Security Best Practices

1. **Never commit .env files**
2. **Use different tokens for dev/prod**
3. **Rotate tokens regularly**
4. **Use least-privilege access**
5. **Monitor token usage**

## File Structure
```
project/
├── .env                 # Your actual tokens (never commit)
├── .env.example         # Template (safe to commit)
├── .gitignore          # Excludes .env
├── requirements.txt    # Includes python-dotenv
└── test_env_setup.py   # Verification script
```
