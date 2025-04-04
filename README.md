# Social Media Content Recommendation System

A system that analyzes social media data and generates content recommendations based on trending topics and historical engagement patterns.

## Overview

This project implements a pipeline that:
1. Retrieves social media data from Cloudflare R2 storage
2. Analyzes engagement trends using Prophet for time series forecasting
3. Indexes content in a vector database using ChromaDB
4. Implements RAG (Retrieval-Augmented Generation) with Llama-3
5. Generates personalized content recommendations

## System Architecture

```
R2 (Raw Data) → Prophet (Trends) → ChromaDB (Vectors) → Llama-3 (RAG) → Recommendations
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