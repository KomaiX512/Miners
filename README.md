# Social Media Content Recommendation System

A comprehensive system that analyzes social media data and generates content recommendations using time series forecasting and RAG patterns.

## Key Components
1. **Data Collection**
   - Instagram scraping via Apify API
   - Cloudflare R2 storage integration
2. **Core Pipeline**
   - Time series analysis with Prophet
   - Vector embeddings with TF-IDF/ChromaDB
   - RAG implementation using Google Gemini
3. **API Layer**
   - Flask-based REST API
   - CORS-enabled endpoints
   - Async processing support
4. **Recommendation Engine**
   - Content type analysis
   - Engagement pattern detection
   - AI-generated suggestions

## Enhanced System Architecture

```
API Layer (Flask)
│
├── Scraper Service → R2 Storage
│
└── Analysis Pipeline:
    R2 (Raw Data) → Data Cleaning → Prophet → ChromaDB → Gemini (RAG) → Content Plan Generator
```

## Prerequisites

- Python 3.9+
- Access to Cloudflare R2 storage
- Downloaded Llama-3 model (or it will fall back to template-based generation)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/social-media-content-recommendation.git
cd social-media-content-recommendation
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Download the Llama-3 model:
```bash
# Go to https://huggingface.co/TheBloke/Llama-3-8B-GGUF and download the quantized model
# Save it in the project directory as "llama-3-8b.Q4_K_M.gguf"
```

## Configuration

The R2 credentials are already configured in `config.py`. If you need to update them, edit the file:

```python
R2_CONFIG = {
    'endpoint_url': f'https://51abf57b5c6f9b6cf2f91cc87e0b9ffe.r2.cloudflarestorage.com',
    'aws_access_key_id': '2093fa05ee0323bb39de512a19638e78',
    'aws_secret_access_key': 'e9e7173d1ee514b452b3a3eb7cef6fb57a248423114f1f949d71dabd34eee04f',
    'bucket_name': 'structuredb'
}
```

## Usage

### Running the Complete Pipeline

To run the complete pipeline:

```bash
python main.py
```

This will:
1. Connect to R2 storage
2. Retrieve social media data
3. Index posts in ChromaDB
4. Analyze engagement patterns
5. Generate content recommendations
6. Save the content plan to `content_plan.json`

### Testing Individual Components

Each component has its own test function:

```bash
# Test data retrieval from R2
python data_retrieval.py

# Test time series analysis
python time_series_analysis.py

# Test vector database operations
python vector_database.py

# Test RAG implementation
python rag_implementation.py

# Test recommendation generation
python recommendation_generation.py
```

## Key API Endpoints
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/scrape` | POST | Scrape Instagram profile |
| `/posts/<username>` | GET | Retrieve stored posts |
| `/api/analyze` | POST | Full analysis pipeline |
| `/r2/update` | POST | Direct R2 storage update |

## Advanced Usage
1. Run Flask API server:
```bash
gunicorn api:app -b 0.0.0.0:5000
```

2. Process multiple accounts:
```python
from main import ContentRecommendationSystem
system = ContentRecommendationSystem()
system.process_instagram_username("username", results_limit=50)
```

## Content Plan Export Functionality

The system now supports exporting content plan sections to R2 storage with the following directory structure:

### Directory Structure

1. **Competitor Analysis**
   - Path: `competitor_analysis/{primary_username}/{competitor_username}/analysis_{n}.json`
   - Contains competitor analysis for each competitor with sequential numbering
   - Each file includes analysis data and a status field (pending/processed)

2. **Recommendations**
   - Path: `recommendations/{primary_username}/recommendation_{n}.json`
   - Contains content recommendations with sequential numbering
   - Each file includes recommendations, primary analysis, and additional insights with a status field

3. **Next Posts**
   - Path: `next_posts/{primary_username}/post_{n}.json`
   - Contains next post predictions with sequential numbering
   - Each file includes post details (caption, hashtags, visual prompt, etc.) with a status field

### Testing Export Functionality

You can test the export functionality using the provided test script:

```bash
python test_export.py
```

This will export the content plan sections from the existing `content_plan.json` file to R2 storage following the directory structure described above.

# Competitor Analysis Fix

## Problem Summary
The system was encountering errors during the processing of competitor analysis data with error messages:
```
Error extracting detailed insights for narsissist: 'strategies'
Error extracting detailed insights for fentybeauty: 'strategies'
Error extracting detailed insights for maccosmetics: 'strategies'
```

The errors occurred because:
1. The `_extract_detailed_competitor_insights` function in `main.py` was trying to access the 'strategies' field which was missing from the competitor analysis data structure
2. The `fix_competitor_analysis.py` script wasn't properly handling or adding the 'strategies' field

## Solution Implemented

### 1. Enhanced fix_competitor_analysis.py
- Added stronger field validation for both 'strategies' and 'weaknesses' fields
- Improved the field fallback mechanism:
  - Copy from 'recommended_counter_strategies' to 'strategies' when available
  - Copy from 'vulnerabilities' to 'weaknesses' when available
- Added detailed logging to track successful fixes
- Added a verification step to ensure required fields are present

### 2. Created verify_competitor_fields.py
- Made a standalone verification script to check and fix critical fields
- Implements field-specific fixes for missing fields
- Provides detailed output about which fields are present for each competitor
- Can be run independently to verify the data structure

### 3. Created process_with_ai_competitors.py
- Single entry point script that:
  1. Backs up the content plan to prevent data loss
  2. Runs fix_competitor_analysis.py to fix missing fields
  3. Verifies that all competitors have the required fields
  4. Runs the main pipeline
  5. Performs a final verification step

## How to Use

### To fix competitor analysis:
```
python fix_competitor_analysis.py
```

### To verify competitor fields:
```
python verify_competitor_fields.py
```

### To run the complete process:
```
python process_with_ai_competitors.py
```

## Verification Tests
The solution was verified by:
1. Running fix_competitor_analysis.py to fix missing fields
2. Running verify_competitor_fields.py to confirm all required fields are present
3. Re-running the main pipeline to confirm no 'strategies' field errors occur

## Prevention Measures
The improved fix_competitor_analysis.py script now performs more thorough checks and applies more robust fixes, making it much less likely for the 'strategies' field error to occur in the future.

# Vector Database Performance Fix

## Problem
The vector database was experiencing issues with ChromaDB queries failing with the following error:
```
Cannot return the results in a contigious 2D array. Probably ef or M is too small
```

This was causing RAG queries to fail, particularly for competitor analysis.

## Solution
We've implemented several improvements to make the vector database more robust:

1. **Enhanced ChromaDB Parameters**: We've increased the `hnsw:M`, `hnsw:ef_construction`, and `hnsw:ef_search` parameters to handle larger datasets and improve query performance.

2. **Automatic Database Clearing**: The vector database is now cleared automatically at the start of each processing run to prevent issues with accumulated data.

3. **Improved Query Logic**: The query retry mechanism has been enhanced to handle failures more gracefully, with progressive simplification of query parameters.

4. **Post-Query Filtering**: We've implemented more robust post-query filtering instead of relying on complex ChromaDB filters.

## Usage
To ensure the vector database is properly cleared between runs, the system now includes a `clear_before_new_run()` method that can be called at the start of any processing pipeline.

You can also run the `fix_vector_database_persistence.py` script to fix the vector database issues:

```bash
python3 fix_vector_database_persistence.py
```

This script will:
1. Clear the existing vector database
2. Reinitialize it with improved parameters
3. Test the database functionality
4. Provide a summary of the improvements

## Important Notes
- The vector database should be cleared at the start of each processing run to prevent issues
- Large queries should use post-filtering rather than complex ChromaDB filters
- If you encounter persistent issues, try running the fix script before starting your main application

## Content Plan and Image Generation Pipeline

### Pipeline Overview

The system processes content in three main stages:

1. **Content Plan Export:**
   - Exports content_plan.json into modular components
   - Exports the recommendation module
   - Exports the next_post_prediction module
   - Exports competitor analysis modules

2. **Next Post Processing by Image Generator:**
   - Reads exported next post files from tasks bucket
   - Generates images based on image_prompt
   - Preserves original caption, hashtags, and call_to_action

3. **Ready Post Export:**
   - Creates ready post files with generated images
   - Maintains exact original text content from next post
   - Exports with same postfix identifier

### Important Notes

- The content_plan.json format expects next_post_prediction in the recommendation section
- Caption, hashtags and call_to_action are preserved exactly as written in content plan
- The image generator uses image_prompt to create the image but doesn't modify any text content

### Data Flow

```
content_plan.json
    │
    ├── recommendation → recommendations/platform/username/recommendation_X.json
    │
    ├── next_post_prediction → next_posts/platform/username/post_X.json
    │                           │
    │                           ▼
    │                         Image Generator
    │                           │
    │                           ▼
    └── competitor_analysis   ready_post/platform/username/ready_post_X.json
                              ready_post/platform/username/image_X.jpg
```

### Debugging Tips

If you notice issues with the content in the final ready post files:

1. Check that content_plan.json has proper next_post_prediction structure
2. Verify that export_content_plan.py is finding and exporting the next post data
3. Check image generator format detection in the _convert_nextpost_to_standard_format method
4. Ensure _standardize_post_fields and _create_output_post are preserving data exactly

Tests are available to verify each step of the pipeline:
- `test_export_content_plan.py`: Verifies next post export
- `test_image_generator.py`: Verifies preservation of content through image generation