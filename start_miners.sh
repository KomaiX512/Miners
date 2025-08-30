#!/bin/bash
# Comprehensive Setup and Run Script for Miners Application

set -e  # Exit on any error

echo "🔧 Setting up Miners Application Environment..."

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
source .venv/bin/activate

echo "📦 Installing Python dependencies..."
pip install --upgrade pip

# Install all required packages
pip install -r requirements.txt
pip install aiobotocore loguru opentelemetry-instrumentation opentelemetry-instrumentation-fastapi

echo "🔧 Checking environment configuration..."
python test_env_setup.py

echo "🗄️ Starting ChromaDB server..."
# Kill any existing ChromaDB processes
pkill -f "uvicorn chromadb.app:app" || true
sleep 2

# Start ChromaDB in background
CHROMA_DB_PATH=./chroma_db nohup uvicorn chromadb.app:app --host 0.0.0.0 --port 8004 > chromadb.log 2>&1 &
CHROMADB_PID=$!
echo "📊 ChromaDB started with PID: $CHROMADB_PID"

# Wait for ChromaDB to be ready
echo "⏳ Waiting for ChromaDB to be ready..."
for i in {1..30}; do
    if curl -s http://localhost:8004/api/v2/heartbeat > /dev/null 2>&1; then
        echo "✅ ChromaDB is ready!"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "❌ ChromaDB failed to start"
        exit 1
    fi
    sleep 1
done

echo "🚀 Starting Miners Application..."
python main.py run_all

# Cleanup on exit
cleanup() {
    echo "🧹 Cleaning up..."
    kill $CHROMADB_PID 2>/dev/null || true
    pkill -f "uvicorn chromadb.app:app" || true
}
trap cleanup EXIT
