# Competitor Analysis Fix

## Overview
This repository contains fixes for the competitor analysis issue in content_plan.json. The main error was related to missing 'strategies' and 'weaknesses' fields in competitor data, causing errors in the processing pipeline.

## Solution Components
1. **fix_competitor_analysis.py**: Main script for fixing competitor analysis data from threat_assessment
2. **ensure_ai_competitor_analysis.py**: Script that checks for proper AI-generated competitor analysis and fixes if needed
3. **process_with_ai_competitors.py**: Complete pipeline script that runs main content generation and ensures competitor analysis is properly included
4. **test_competitor_analysis.py**: Test script that verifies the 'strategies' field handling

## Common Issues Fixed
- Missing 'strategies' field in competitor analysis
- Missing 'weaknesses' field in competitor analysis
- Placeholder competitor analysis data
- Error handling for competitor data extraction

## How to Run
Simply run the process_with_ai_competitors.py script, which will:
1. Run the main content generation pipeline
2. Check and fix competitor analysis data
3. Verify all required fields are present

```bash
python process_with_ai_competitors.py
```

You can also run the ensure_ai_competitor_analysis.py script directly to fix issues in an existing content_plan.json:

```bash
python ensure_ai_competitor_analysis.py
```

To force a fix even if no issues are detected, use:

```bash
python ensure_ai_competitor_analysis.py --force
```

## Verification
Run the check_competitor_fields.py script to verify the structure of competitor data:

```bash
python check_competitor_fields.py
``` 