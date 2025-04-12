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