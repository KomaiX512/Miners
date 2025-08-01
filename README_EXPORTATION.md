# Content Plan Exportation Module

This module handles the exportation of content plan sections according to the new format and structure. It ensures that all modules are exported correctly to their respective locations in R2 storage.

## Module Structure

The exportation module consists of two main files:

1. `export_content_plan.py` - Main exportation module
2. `test_export_content_plan.py` - Test suite for the exportation module

## Exportation Structure

The module exports content plan sections to the following locations:

1. **Recommendation Module**
   - Path: `recommendations/<platform>/<primary_username>/recommendation_*.json`
   - Contains:
     - competitive_intelligence
     - tactical_recommendations
     - threat_assessment

2. **Next Post Prediction**
   - Path: `next_post/<platform>/<primary_username>/post_*.json`
   - Contains:
     - caption
     - hashtags
     - call_to_action
     - image_prompt

3. **Competitor Analysis**
   - Path: `competitor_analysis/<platform>/<primary_username>/<competitor>/analysis_*.json`
   - One file per competitor containing:
     - overview
     - strengths
     - vulnerabilities
     - recommended_counter_strategies

## File Naming Convention

Files are named with incremental numbers to maintain order:
- `recommendation_1.json`, `recommendation_2.json`, etc.
- `post_1.json`, `post_2.json`, etc.
- `analysis_1.json`, `analysis_2.json`, etc.

## Exportation Process

1. **Initialization**
   - Create necessary directories in R2 storage
   - Verify required fields in content plan

2. **Recommendation Export**
   - Extract recommendation data from content plan
   - Format data according to schema
   - Upload to R2 storage

3. **Next Post Export**
   - Extract next post prediction data
   - Format data according to schema
   - Upload to R2 storage

4. **Competitor Analysis Export**
   - Extract competitor analysis data for each competitor
   - Create competitor-specific directories
   - Format and upload individual analysis files

## Data Schema

### Recommendation Module
```json
{
    "module_type": "recommendation",
    "platform": "<platform>",
    "primary_username": "<username>",
    "timestamp": "<ISO timestamp>",
    "data": {
        "competitive_intelligence": {
            "account_analysis": "...",
            "brand strategy, market positioning, competitive analysis": "...",
            "strategic_positioning": "...",
            "competitive_analysis": "..."
        },
        "tactical_recommendations": [...],
        "threat_assessment": {...}
    }
}
```

### Next Post Prediction
```json
{
    "module_type": "next_post_prediction",
    "platform": "<platform>",
    "primary_username": "<username>",
    "timestamp": "<ISO timestamp>",
    "data": {
        "caption": "...",
        "hashtags": [...],
        "call_to_action": "...",
        "image_prompt": "..."
    }
}
```

### Competitor Analysis
```json
{
    "module_type": "competitor_analysis",
    "platform": "<platform>",
    "primary_username": "<username>",
    "competitor_username": "<competitor>",
    "timestamp": "<ISO timestamp>",
    "data": {
        "overview": "...",
        "strengths": [...],
        "vulnerabilities": [...],
        "recommended_counter_strategies": [...]
    }
}
```

## Error Handling

The module includes comprehensive error handling:
- Validates required fields before export
- Handles missing sections gracefully
- Logs all exportation steps and errors
- Returns detailed export results

## Testing

The test suite verifies:
- Successful export of all sections
- Handling of missing fields
- Directory creation
- File numbering
- Error conditions

Run tests with:
```bash
python3 -m unittest test_export_content_plan.py
```

## Usage

```python
from export_content_plan import ContentPlanExporter

# Initialize exporter with R2 storage
exporter = ContentPlanExporter(r2_storage)

# Export content plan
results = exporter.export_content_plan(content_plan)

# Check results
if results:
    print("Export successful")
    print(f"Exported {len(results['competitor_analysis'])} competitor analyses")
else:
    print("Export failed")
``` 