import requests
import os
import time
import asyncio
import json
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from utils.r2_client import R2Client
from utils.logging import logger
from config import R2_CONFIG

# API endpoint where the query processor is running
QUERY_PROCESSOR_URL = os.environ.get("QUERY_PROCESSOR_URL", "http://localhost:8000")

class R2FileEventHandler:
    """Handles events for when files are uploaded to R2 bucket"""
    
    def __init__(self):
        self.r2_client = R2Client(config=R2_CONFIG)
        self.input_prefix = "queries/"
        self.last_scanned_files = set()
        
    async def scan_for_new_queries(self):
        """Scan R2 bucket for new query files and trigger processing for each"""
        try:
            objects = await self.r2_client.list_objects(self.input_prefix)
            current_files = set()
            
            for obj in objects:
                key = obj["Key"]
                if key.endswith(".json") and "query_" in key:
                    current_files.add(key)
                    
            # Find files that weren't in the last scan
            new_files = current_files - self.last_scanned_files
            
            if new_files:
                logger.info(f"Found {len(new_files)} new query files")
                for key in new_files:
                    self.trigger_processing(key)
            
            # Update the set of scanned files
            self.last_scanned_files = current_files
            
        except Exception as e:
            logger.error(f"Error scanning for new queries: {e}")
    
    def trigger_processing(self, key):
        """Trigger the query processor to handle a specific query file"""
        try:
            response = requests.post(
                f"{QUERY_PROCESSOR_URL}/process-query",
                json={"key": key},
                timeout=5
            )
            if response.status_code == 200:
                logger.info(f"Successfully triggered processing for {key}")
            else:
                logger.error(f"Failed to trigger processing for {key}: {response.text}")
        except Exception as e:
            logger.error(f"Error triggering processing for {key}: {e}")

class LocalFileEventHandler(FileSystemEventHandler):
    """Handles file system events for a local directory that syncs with R2"""
    
    def __init__(self, r2_handler, watch_dir):
        self.r2_handler = r2_handler
        self.watch_dir = watch_dir
        
    def on_created(self, event):
        if not event.is_directory and event.src_path.endswith(".json") and "query_" in event.src_path:
            file_name = os.path.basename(event.src_path)
            key = f"queries/{file_name}"
            logger.info(f"New query file detected: {file_name}")
            self.r2_handler.trigger_processing(key)

async def run_r2_monitor():
    """Run the R2 monitoring service"""
    r2_handler = R2FileEventHandler()
    
    # Do initial scan
    await r2_handler.scan_for_new_queries()
    
    # Check for new files periodically, but much less frequently than before
    while True:
        await asyncio.sleep(60)  # Check every minute instead of every 10 seconds
        await r2_handler.scan_for_new_queries()

def setup_local_file_watcher(watch_dir):
    """Set up a local file system watcher"""
    r2_handler = R2FileEventHandler()
    event_handler = LocalFileEventHandler(r2_handler, watch_dir)
    observer = Observer()
    observer.schedule(event_handler, watch_dir, recursive=True)
    observer.start()
    return observer

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--watch-local":
        # Watch a local directory
        if len(sys.argv) < 3:
            print("Error: Please specify a directory to watch")
            sys.exit(1)
            
        watch_dir = sys.argv[2]
        print(f"Watching directory: {watch_dir}")
        observer = setup_local_file_watcher(watch_dir)
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            observer.stop()
        observer.join()
    else:
        # Monitor R2 bucket
        print("Starting R2 bucket monitor")
        asyncio.run(run_r2_monitor()) 