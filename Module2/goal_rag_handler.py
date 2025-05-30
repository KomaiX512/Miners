"""
GoalRAGHandler - A module for processing goal files and generating social media posting strategies.
This optimized implementation monitors for new goal files, analyzes user data, and generates
customized posting plans to help users reach their follower growth objectives.
"""

import os
import time
import json
import asyncio
from typing import Dict, Tuple, List, Any, Optional
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from utils.r2_client import R2Client
from utils.logging import logger
from config import R2_CONFIG, STRUCTUREDB_R2_CONFIG, GEMINI_CONFIG
import google.generativeai as genai

# --- Gemini setup ---
genai.configure(api_key=GEMINI_CONFIG["api_key"])
model = genai.GenerativeModel(
    model_name=GEMINI_CONFIG["model"],
    generation_config={
        "max_output_tokens": GEMINI_CONFIG["max_tokens"],
        "temperature": GEMINI_CONFIG["temperature"],
        "top_p": GEMINI_CONFIG["top_p"],
        "top_k": GEMINI_CONFIG["top_k"]
    }
)

class FileDataManager:
    """Handles file operations including retrieval and storage of data files from R2 storage."""
    
    def __init__(self, r2_tasks: R2Client, r2_structuredb: R2Client):
        self.r2_tasks = r2_tasks
        self.r2_structuredb = r2_structuredb
        self.platforms = ["instagram", "twitter"]  # Support both platforms
    
    async def get_latest_file(self, prefix: str, pattern: str, platform: str = None) -> Optional[str]:
        """Get the latest file matching pattern under prefix, optionally filtered by platform."""
        if platform:
            # Use platform-aware prefix
            search_prefix = f"{prefix}{platform}/"
        else:
            search_prefix = prefix
            
        objects = await self.r2_tasks.list_objects(search_prefix)
        candidates = [o["Key"] for o in objects if pattern in o["Key"]]
        if not candidates:
            return None
        # Sort by number in filename (e.g., goal_3.json) - highest first
        candidates.sort(key=lambda x: int(''.join(filter(str.isdigit, x.split('_')[-1])) or 0), reverse=True)
        return candidates[0]
    
    async def get_goal_data(self, goal_key: str) -> Optional[Dict]:
        """Retrieve goal data from R2 and validate it."""
        logger.info(f"Retrieving goal file: {goal_key}")
        goal_data = await self.r2_tasks.read_json(goal_key)
        if not goal_data:
            logger.error(f"Could not read goal file: {goal_key}")
            return None
        if goal_data.get("status") == "processed":
            logger.info(f"Goal file already processed: {goal_key}")
            return None
        return goal_data
    
    async def get_prophet_analysis(self, username: str, platform: str = "instagram") -> Optional[Dict]:
        """Retrieve latest prophet analysis for user with platform awareness."""
        # NEW SCHEMA: prophet_analysis/platform/username/analysis_*.json
        prophet_prefix = f"prophet_analysis/{platform}/{username}/"
        prophet_key = await self.get_latest_file(prophet_prefix, "analysis_", platform=None)  # Already platform-aware
        logger.info(f"Retrieving prophet analysis file: {prophet_key}")
        prophet_data = await self.r2_tasks.read_json(prophet_key) if prophet_key else None
        if not prophet_data:
            logger.error(f"Prophet analysis file missing or unreadable for user: {username} on {platform}")
            return None
        return prophet_data
    
    async def get_recommendations(self, username: str, platform: str = "instagram") -> Dict:
        """Retrieve latest recommendations for user with platform awareness."""
        # NEW SCHEMA: recommendations/platform/username/recommendation_*.json
        rec_prefix = f"recommendations/{platform}/{username}/"
        rec_objects = await self.r2_tasks.list_objects(rec_prefix)
        logger.info(f"Available files in {rec_prefix}: {[o['Key'] for o in rec_objects]}")
        rec_key = await self.get_latest_file(rec_prefix, "recommendation_", platform=None)  # Already platform-aware
        logger.info(f"Retrieving recommendations file: {rec_key}")
        rec_data = await self.r2_tasks.read_json(rec_key) if rec_key else None
        if rec_data is None:
            logger.warning(f"Recommendations file missing or unreadable for user: {username} on {platform}. Proceeding with empty recommendations.")
            rec_data = {}
        return rec_data
    
    async def get_profile_data(self, username: str, platform: str = "instagram") -> Optional[Dict]:
        """Retrieve profile data from structuredb with platform awareness."""
        # NEW SCHEMA: platform/username/username.json
        profile_key = f"{platform}/{username}/{username}.json"
        logger.info(f"Retrieving profile file: {profile_key}")
        profile_data = await self.r2_structuredb.read_json(profile_key)
        if not profile_data:
            logger.error(f"Profile file missing or unreadable for user: {username} on {platform}")
            return None
        return profile_data
    
    async def mark_goal_processed(self, goal_key: str, goal_data: Dict) -> None:
        """Mark goal file as processed."""
        goal_data["status"] = "processed"
        await self.r2_tasks.write_json(goal_key, goal_data)
        logger.info(f"Marked goal file as processed: {goal_key}")
    
    async def upload_posting_delay(self, username: str, delay_hours: float, platform: str = "instagram", only_once: bool = False) -> None:
        """Upload posting delay information with platform awareness."""
        # NEW SCHEMA: time_delay/platform/username/time_delay_*.json
        prefix = f"time_delay/{platform}/{username}/"
        objects = await self.r2_tasks.list_objects(prefix)
        n = len([o for o in objects if "time_delay_" in o["Key"]]) + 1
        if only_once and n > 1:
            logger.info(f"Delay file already exists for {username} on {platform}, skipping export.")
            return
        key = f"{prefix}time_delay_{n}.json"
        data = {"Posting_Delay_Intervals": str(int(delay_hours))}
        await self.r2_tasks.write_json(key, data)
        logger.info(f"Uploaded posting delay for {username} on {platform}: {key}")
    
    async def upload_post_plan(self, username: str, post_number: int, post_data: Dict, platform: str = "instagram") -> None:
        """Upload individual post plan with platform awareness."""
        # NEW SCHEMA: queries/platform/username/query_*.json
        prefix = f"queries/{platform}/{username}/"
        objects = await self.r2_tasks.list_objects(prefix)
        existing = len([o["Key"] for o in objects if "query_" in o["Key"]])
        key = f"{prefix}query_{existing + post_number}.json"
        await self.r2_tasks.write_json(key, post_data)
        logger.info(f"Uploaded post plan {post_number} for {username} on {platform}: {key}")


class RAGPromptManager:
    """Handles creation and processing of RAG prompts for various purposes."""
    
    @staticmethod
    def compose_strategy_prompt(goal: Dict, prophet: Dict, rec: Dict, profile: Dict) -> str:
        """Create comprehensive prompt for generating social media strategy."""
        timeline = goal.get("timeline", 7)
        follower_goal = None
        
        # Extract follower goal from the goal text using a basic text analysis
        goal_text = goal.get("goal", "").lower()
        if "follower" in goal_text and "increase" in goal_text:
            # Try to extract numeric values that might represent follower targets
            import re
            numbers = re.findall(r'\d+', goal_text)
            if numbers:
                follower_goal = max([int(n) for n in numbers])
        
        # Get current stats to inform strategy
        current_followers = profile.get("followers", 0) if isinstance(profile, dict) else 0
        avg_engagement = 0
        if isinstance(prophet, dict) and "primary_analysis" in prophet:
            engagement_data = prophet["primary_analysis"].get("engagement", {})
            if isinstance(engagement_data, dict) and "content_type_analysis" in engagement_data:
                # Calculate average engagement across all content types
                content_analysis = engagement_data["content_type_analysis"]
                total_engagement = sum(content["average_engagement"] for content in content_analysis.values() 
                                    if isinstance(content, dict) and "average_engagement" in content)
                content_count = len(content_analysis)
                avg_engagement = total_engagement / content_count if content_count > 0 else 0
        
        prompt = (
            f"# Social Media Strategy Development\n\n"
            f"## User Goal\n{json.dumps(goal, indent=2, ensure_ascii=False)}\n\n"
            
            f"## Current Stats\n"
            f"- Timeline: {timeline} days\n"
            f"- Current Followers: ~{current_followers}\n"
            f"- Target Growth: {follower_goal if follower_goal else 'Significant increase'}\n"
            f"- Average Engagement: ~{avg_engagement:.2f}\n\n"
            
            f"## Profile Analysis\n"
            f"```json\n{json.dumps(profile, indent=2, ensure_ascii=False)[:1000]}...\n```\n\n"
            
            f"## Engagement History\n"
            f"```json\n{json.dumps(prophet.get('primary_analysis', {}).get('engagement', {}), indent=2, ensure_ascii=False)}\n```\n\n"
            
            f"## Posting Trends\n"
            f"```json\n{json.dumps(prophet.get('primary_analysis', {}).get('posting_trends', {}), indent=2, ensure_ascii=False)}\n```\n\n"
            
            f"## Competitive Recommendations\n"
            f"```json\n{json.dumps(rec, indent=2, ensure_ascii=False)}\n```\n\n"
            
            f"# Your Task\n"
            f"Based on the data above, determine:\n\n"
            
            f"1. Calculate the optimal number of posts needed to achieve the follower growth goal within {timeline} days.\n"
            f"   - Factor in current engagement rates, posting frequency, and follower growth patterns\n"
            f"   - Consider profile themes and content preferences\n\n"
            
            f"2. Determine the ideal posting interval (in hours) to distribute these posts evenly.\n\n"
            
            f"RESPOND ONLY WITH THIS JSON FORMAT:\n"
            f"```json\n"
            f'{{"num_posts": <integer>, "delay_hours": <float>, "rationale": "<brief explanation of your calculation>"}}\n'
            f"```"
        )
        return prompt

    @staticmethod
    def compose_post_prompt(
        goal: Dict, 
        prophet: Dict, 
        rec: Dict, 
        profile: Dict, 
        post_num: int, 
        total_posts: int
    ) -> str:
        """Create detailed prompt for generating a specific post plan."""
        
        # Extract key profile themes
        profile_theme = ""
        profile_bio = ""
        
        if isinstance(profile, dict):
            profile_theme = profile.get("theme", "")
            profile_bio = profile.get("bio", "")
        
        # Get best performing content type
        best_content_type = "photo"  # Default
        if (isinstance(prophet, dict) and "primary_analysis" in prophet and 
            "engagement" in prophet["primary_analysis"]):
            best_content_type = prophet["primary_analysis"]["engagement"].get("best_performing_content", "photo")
        
        # Extract posting patterns
        posting_trends = {}
        if (isinstance(prophet, dict) and "primary_analysis" in prophet and 
            "posting_trends" in prophet["primary_analysis"]):
            posting_trends = prophet["primary_analysis"]["posting_trends"]
        
        # Extract competitive recommendations
        rec_text = ""
        if isinstance(rec, dict):
            if "recommendations" in rec:
                rec_text = rec["recommendations"]
            if "differentiation_factors" in rec and isinstance(rec["differentiation_factors"], list):
                rec_text += "\nDifferentiation factors:\n" + "\n".join(rec["differentiation_factors"])
        
        prompt = (
            f"# Generate Post Plan {post_num} of {total_posts}\n\n"
            
            f"## User Goal\n{goal.get('goal', 'Increase engagement and followers')}\n\n"
            
            f"## Profile Information\n"
            f"- Bio: {profile_bio}\n"
            f"- Theme: {profile_theme}\n"
            f"- Best performing content: {best_content_type}\n"
            f"- Most active day: {posting_trends.get('most_active_day', 'Unknown')}\n"
            f"- Most active hour: {posting_trends.get('hour_formatted', 'Unknown')}\n\n"
            
            f"## Strategic Recommendations\n{rec_text}\n\n"
            
            f"## Instructions\n"
            f"Create a detailed plan for post #{post_num}. Your plan should include:\n"
            f"1. Post content description (topic, message, call-to-action)\n"
            f"2. Visual description (what images/videos should show, style, colors, composition)\n"
            f"3. How this specific post will help achieve the user's goal\n\n"
            
            f"Make sure the post aligns with the profile's existing theme and style while incorporating strategic elements from the recommendations.\n\n"
            
            f"RESPOND ONLY WITH THIS JSON FORMAT:\n"
            f"```json\n"
            f'{{"query": "<detailed post plan with visual description>", "status": "processed", "timestamp": "{datetime.utcnow().isoformat()}Z"}}\n'
            f"```"
        )
        return prompt


class RAGProcessor:
    """Processes RAG requests and generates outputs using AI models."""
    
    @staticmethod
    async def predict_posting_strategy(prompt: str, goal: Dict) -> Tuple[int, float, str]:
        """Predict optimal posting strategy based on goal and analysis data."""
        try:
            response = await asyncio.wait_for(
                model.generate_content_async(prompt),
                timeout=60
            )
            data = RAGProcessor.safe_json_from_text(response.text)
            if data and "num_posts" in data and "delay_hours" in data:
                num_posts = int(data["num_posts"])
                delay_hours = float(data["delay_hours"])
                rationale = data.get("rationale", "Based on engagement patterns and timeline")
                return num_posts, delay_hours, rationale
            
            logger.warning("Failed to parse strategy prediction, using fallback")
        except Exception as e:
            logger.error(f"Error in strategy prediction: {e}")
        
        # Fallback calculation
        timeline = int(goal.get("timeline", 7))
        num_posts = timeline * 2  # Default: 2 posts per day
        delay_hours = (timeline * 24) / num_posts if num_posts > 0 else 12
        return num_posts, delay_hours, "Fallback calculation based on timeline"
    
    @staticmethod
    async def generate_post_plan(prompt: str) -> Dict:
        """Generate a single post plan based on provided context."""
        try:
            response = await asyncio.wait_for(
                model.generate_content_async(prompt),
                timeout=60
            )
            post_data = RAGProcessor.safe_json_from_text(response.text)
            if post_data and "query" in post_data:
                if "status" not in post_data:
                    post_data["status"] = "processed"
                if "timestamp" not in post_data:
                    post_data["timestamp"] = f"{datetime.utcnow().isoformat()}Z"
                return post_data
            
            logger.warning("Failed to parse post plan, using fallback")
        except Exception as e:
            logger.error(f"Error generating post plan: {e}")
        
        # Fallback post data
        return {
            "query": "Create an engaging post aligned with your profile's theme and style to attract new followers.",
            "status": "processed",
            "timestamp": f"{datetime.utcnow().isoformat()}Z"
        }
    
    @staticmethod
    def safe_json_from_text(text: str) -> Dict:
        """Parse JSON from text, with fallback for various formats."""
        if not text:
            return {}
            
        text = text.strip()
        
        # Try direct JSON parsing
        if text.startswith("{") and text.endswith("}"):
            try:
                return json.loads(text)
            except Exception:
                pass
        
        # Try to extract JSON from code block
        import re
        json_matches = re.findall(r'```(?:json)?\s*({.*?})\s*```', text, re.DOTALL)
        if json_matches:
            try:
                return json.loads(json_matches[0])
            except Exception:
                pass
        
        # Try to extract first JSON object anywhere in text
        json_start = text.find("{")
        json_end = text.rfind("}") + 1
        if json_start >= 0 and json_end > json_start:
            try:
                return json.loads(text[json_start:json_end])
            except Exception:
                pass
        
        return {}


class GoalRAGHandler:
    """Main handler class for processing goal files and generating strategies."""
    
    def __init__(self):
        self.r2_tasks = R2Client(config=R2_CONFIG)
        self.r2_structuredb = R2Client(config=STRUCTUREDB_R2_CONFIG)
        self.file_manager = FileDataManager(self.r2_tasks, self.r2_structuredb)
        self.processed_files = set()  # Track processed files
    
    async def process_goal_file(self, goal_key: str) -> None:
        """Process a goal file and generate posting strategy."""
        # Skip if already processed in this session
        if goal_key in self.processed_files:
            return
        self.processed_files.add(goal_key)
        
        try:
            # Extract username and platform from path: goal/platform/username/goal_*.json
            parts = goal_key.split('/')
            if len(parts) < 4:
                logger.error(f"Invalid goal key format for new schema: {goal_key}")
                return
                
            platform = parts[1]  # goal/platform/username/goal_*.json
            username = parts[2]
            logger.info(f"Processing goal for user: {username} on {platform}")
            
            # 1. Fetch and validate all required data with platform awareness
            goal_data = await self.file_manager.get_goal_data(goal_key)
            if not goal_data:
                return
                
            prophet_data = await self.file_manager.get_prophet_analysis(username, platform)
            if not prophet_data:
                return
                
            rec_data = await self.file_manager.get_recommendations(username, platform)
            if isinstance(rec_data, list):
                logger.error(f"Recommendations file is a list, expected dict for user: {username} on {platform}")
                return
                
            profile_data = await self.file_manager.get_profile_data(username, platform)
            if not profile_data:
                return
                
            logger.info(f"All {platform} files retrieved successfully for user: {username}")
            
            # 2. Generate posting strategy
            strategy_prompt = RAGPromptManager.compose_strategy_prompt(
                goal_data, prophet_data, rec_data, profile_data
            )
            
            num_posts, delay_hours, rationale = await RAGProcessor.predict_posting_strategy(
                strategy_prompt, goal_data
            )
            
            logger.info(f"Strategy generated for {username} on {platform}: {num_posts} posts with {delay_hours}h delay. Rationale: {rationale}")
            
            # 3. Upload posting delay information with platform awareness
            await self.file_manager.upload_posting_delay(username, delay_hours, platform, only_once=True)
            
            # 4. Generate and upload individual post plans with platform awareness
            await self.generate_post_plans(username, num_posts, goal_data, prophet_data, rec_data, profile_data, platform)
            
            # 5. Mark goal file as processed
            await self.file_manager.mark_goal_processed(goal_key, goal_data)
            
        except Exception as e:
            logger.error(f"Error processing goal file {goal_key}: {str(e)}", exc_info=True)
    
    async def generate_post_plans(
        self, 
        username: str, 
        num_posts: int,
        goal_data: Dict,
        prophet_data: Dict, 
        rec_data: Dict,
        profile_data: Dict,
        platform: str
    ) -> None:
        """Generate and upload multiple post plans based on strategy."""
        for i in range(1, num_posts + 1):
            post_prompt = RAGPromptManager.compose_post_prompt(
                goal_data, prophet_data, rec_data, profile_data, i, num_posts
            )
            
            post_data = await RAGProcessor.generate_post_plan(post_prompt)
            
            await self.file_manager.upload_post_plan(username, i, post_data, platform)
            
            # Brief pause to avoid API rate limits
            await asyncio.sleep(0.5)


# --- Watchdog Event Handler ---
class GoalFileEventHandler(FileSystemEventHandler):
    """File system event handler for new goal files."""
    
    def __init__(self, rag_handler: GoalRAGHandler):
        self.rag_handler = rag_handler
        self.loop = asyncio.get_event_loop()
    
    def on_created(self, event):
        """Handle file creation events."""
        if not event.is_directory and event.src_path.endswith(".json") and "goal_" in event.src_path:
            rel_path = os.path.relpath(event.src_path, os.getcwd())
            parts = rel_path.split(os.sep)
            
            # Find username as the parent directory of the file
            if len(parts) >= 4 and parts[0] == "tasks" and parts[1] == "goal":
                username = parts[2]
                goal_key = f"goal/{username}/" + os.path.basename(event.src_path)
                logger.info(f"New goal file detected: {goal_key}")
                self.loop.create_task(self.rag_handler.process_goal_file(goal_key))


# --- Scan existing files function ---
async def scan_existing_goal_files(rag_handler: GoalRAGHandler) -> None:
    """Scan and process all existing unprocessed goal files across all platforms."""
    logger.info("Scanning for existing unprocessed goal files across all platforms...")
    
    total_processed = 0
    platforms = ["instagram", "twitter"]
    
    for platform in platforms:
        platform_prefix = f"goal/{platform}/"
        objects = await rag_handler.r2_tasks.list_objects(platform_prefix)
        platform_count = 0
        
        for obj in objects:
            key = obj["Key"]
            if key.endswith(".json") and "goal_" in key:
                logger.info(f"Found {platform} goal file: {key}")
                goal_data = await rag_handler.r2_tasks.read_json(key)
                
                if not goal_data:
                    logger.warning(f"Could not read {platform} goal file: {key}")
                    continue
                    
                if goal_data.get("status") == "processed":
                    logger.info(f"{platform} goal file already processed (skipped): {key}")
                    continue
                    
                logger.info(f"Processing existing {platform} goal file: {key}")
                await rag_handler.process_goal_file(key)
                platform_count += 1
        
        logger.info(f"Processed {platform_count} existing {platform} goal files.")
        total_processed += platform_count
    
    logger.info(f"Total processed {total_processed} existing goal files across all platforms.")


# --- Main Entrypoint ---
def main():
    """Main entry point for the application."""
    logger.info("Starting GoalRAGHandler service")
    
    # Initialize the RAG handler
    rag_handler = GoalRAGHandler()
    
    # Set up file system monitoring
    event_handler = GoalFileEventHandler(rag_handler)
    observer = Observer()
    watch_dir = os.path.join("tasks", "goal")
    os.makedirs(watch_dir, exist_ok=True)  # Ensure directory exists
    observer.schedule(event_handler, watch_dir, recursive=True)
    observer.start()
    logger.info(f"Started GoalRAGHandler watcher on {watch_dir}")
    
    # Scan all existing files on startup
    loop = asyncio.get_event_loop()
    loop.run_until_complete(scan_existing_goal_files(rag_handler))
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        logger.info("Stopping GoalRAGHandler service")
    
    observer.join()


if __name__ == "__main__":
    main()