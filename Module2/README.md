# Optimized Query Processing System

This system has been optimized to process queries in an event-driven manner, significantly reducing CloudFlare R2 bucket operations and costs.

## Components

### 1. Query Handler (query_handler.py)

- Transformed from a polling-based service to an event-driven API service
- Exposes endpoints for processing specific queries
- Only reads from the R2 bucket when explicitly triggered
- Uses FastAPI for efficient request handling

### 2. Query Trigger (query_trigger.py)

Two modes of operation:
- R2 Monitor: Periodically checks for new files (once per minute vs. every 10 seconds)
- Local File Watcher: Can watch a local directory that syncs with R2

## Benefits

- **Reduced R2 Operations**: Instead of checking the bucket every 10 seconds, operations are only performed when needed
- **Cost Efficiency**: Significantly reduces CloudFlare R2 operations costs
- **Flexibility**: Can be triggered by external services via API or run as a standalone service
- **Better Scalability**: Can handle large numbers of queries more efficiently

## Usage

### Start the Query Processor

```bash
python query_handler.py
```

This starts a FastAPI server on port 8000 that listens for query processing requests.

### Start the Query Trigger

Option 1: Monitor R2 bucket periodically (once per minute):
```bash
python query_trigger.py
```

Option 2: Watch a local directory that syncs with R2:
```bash
python query_trigger.py --watch-local /path/to/local/sync/dir
```

### Webhook Integration (Optional)

For complete event-driven processing, configure CloudFlare R2 to send webhook notifications when new files are uploaded. These webhooks can call the `/process-query` endpoint directly.

## Environment Variables

- `QUERY_PROCESSOR_URL`: URL of the query processor API (default: "http://localhost:8000")

## Dependencies

The optimized system requires:
- FastAPI
- Uvicorn
- Watchdog (for local directory monitoring)
- Requests
