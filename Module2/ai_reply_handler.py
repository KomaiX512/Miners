import asyncio
import os
import json
from pathlib import Path
from utils.r2_client import R2Client
from utils.logging import logger
from config import R2_CONFIG, STRUCTUREDB_R2_CONFIG, GEMINI_CONFIG
import google.generativeai as genai
# from gemini_client import GeminiClient  # Assuming you have a Gemini client as in other modules

class AIReplyHandler:
    def __init__(self, ai_reply_root="ai_reply", poll_interval=10):
        self.ai_reply_root = Path(ai_reply_root)
        self.poll_interval = poll_interval
        self.tasks_client = R2Client(config=R2_CONFIG)
        self.structuredb_client = R2Client(config=STRUCTUREDB_R2_CONFIG)
        self.platforms = ["instagram", "twitter", "facebook"]  # Support all three platforms
        genai.configure(api_key=GEMINI_CONFIG["api_key"])
        self.model = genai.GenerativeModel(
            model_name=GEMINI_CONFIG["model"],
            generation_config={
                "max_output_tokens": GEMINI_CONFIG["max_tokens"],
                "temperature": GEMINI_CONFIG["temperature"],
                "top_p": GEMINI_CONFIG["top_p"],
                "top_k": GEMINI_CONFIG["top_k"]
            }
        )
        # self.gemini = GeminiClient()  # Use your existing Gemini client

    async def watch_and_process(self):
        logger.info("Starting AIReplyHandler watcher loop...")
        while True:
            try:
                await self.process_pending_replies()
            except Exception as e:
                logger.error(f"Error in watcher loop: {e}")
            await asyncio.sleep(self.poll_interval)

    async def process_pending_replies(self):
        # Scan both platforms for AI reply files - NEW SCHEMA: ai_reply/platform/username/ai_dm_*.json
        for platform in self.platforms:
            platform_prefix = f"ai_reply/{platform}/"
            objects = await self.tasks_client.list_objects(platform_prefix)
            
        for obj in objects:
            key = obj["Key"]
            if not key.endswith(".json"):
                continue
            # Only process ai_dm_*.json or ai_comment_*.json
            base = key.split("/")[-1]
            if not (base.startswith("ai_dm_") or base.startswith("ai_comment_")):
                continue
                
                # Extract username from new schema: ai_reply/platform/username/file.json
                key_parts = key.split("/")
                if len(key_parts) < 4:
                    continue
                username = key_parts[2]  # ai_reply/platform/username/file.json
                
            if await self.is_pending(key):
                    await self.handle_reply_file(username, key, platform)

    async def is_pending(self, key):
        # Download and check status
        data = await self.tasks_client.read_json(key)
        try:
            payload = data
            return payload.get("status") == "pending"
        except Exception:
            return False

    async def handle_reply_file(self, username, key, platform):
        logger.info(f"Processing {key} for user {username} on platform {platform}")
        # Download DM/comment JSON
        dm_json = await self.tasks_client.read_json(key)
        # Fetch profile
        profile = await self.fetch_profile(username, platform)
        # Fetch rules (optional)
        rules = await self.fetch_rules(username, platform)
        # Compose RAG prompt and get reply
        reply = await self.generate_reply(dm_json, profile, rules)
        # Upload reply
        await self.upload_reply(username, key, reply, platform)
        # Optionally, mark original as processed
        await self.mark_as_processed(key)

    async def fetch_profile(self, username, platform="instagram"):
        # NEW SCHEMA: platform/username/username.json
        profile_key = f"{platform}/{username}/{username}.json"
        try:
            data = await self.structuredb_client.read_json(profile_key)
            return data
        except Exception as e:
            logger.warning(f"Profile not found for {username} on {platform}: {e}")
            return None

    async def fetch_rules(self, username, platform="instagram"):
        # NEW SCHEMA: rules/platform/username/rules.json
        rules_key = f"rules/{platform}/{username}/rules.json"
        try:
            data = await self.tasks_client.read_json(rules_key)
            return data
        except Exception:
            return None

    async def generate_reply(self, dm_json, profile, rules):
        # Compose the query text
        query_text = dm_json.get("text", "")
        username = dm_json.get("username", "unknown")
        logger.info(f"Generating reply for user {username} with query: {query_text}")

        # Prepare context
        context = json.dumps(profile, ensure_ascii=False, indent=2) if profile else ""
        rules_text = json.dumps(rules, ensure_ascii=False, indent=2) if rules else ""

        # 1. Rule check: If rules exist, check if query violates any rule
        if rules_text:
            rule_check_prompt = (
                f"Query: {query_text}\n"
                f"Rules: {rules_text}\n"
                f"Does this query violate any rules? If yes, respond with 'Better not to say on this'. "
                f"Otherwise, return 'Proceed'."
            )
            try:
                rule_response = await asyncio.wait_for(
                    self.model.generate_content_async(rule_check_prompt),
                    timeout=30
                )
                logger.debug(f"Rule check response: {rule_response.text}")
                if rule_response.text.strip() == "Better not to say on this":
                    return "I'm sorry, I'm not allowed to respond on that."
            except Exception as e:
                logger.warning(f"Rule check failed: {e}, proceeding with caution.")

        # 2. Compose RAG prompt for Gemini
        prompt = (
            f"You are a highly skilled, human-like social media manager. Your job is to reply to DMs or comments as if you are the real account holder, using the following information.\n\n"
            f"MESSAGE TYPE: {dm_json.get('type', 'message')}\n"
            f"MESSAGE: {query_text}\n\n"
            f"PROFILE DATA (psychology, theme, knowledge, tone, accent, etc.):\n{context}\n\n"
            f"RULES (if any):\n{rules_text}\n\n"
            f"INSTRUCTIONS: Reply in a way that is extremely specific, contextually relevant, and feels like a real human wrote it.\n"
            f"- If the message is a DM, reply as if you are having a private conversation.\n"
            f"- If the message is a comment, reply as if you are responding publicly.\n"
            f"- Use the account's style, tone, and knowledge from the profile.\n"
            f"- If the query is about a forbidden topic (see rules), politely decline.\n"
            f"- Be concise, authentic, and engaging.\n"
            f"- Do NOT reveal any sensitive or forbidden information.\n"
            f"- Respond ONLY with the reply text, no extra explanation.\n"
        )

        fallback_reply = "Thank you for your message! We'll get back to you soon."
        try:
            response = await asyncio.wait_for(
                self.model.generate_content_async(prompt),
                timeout=60
            )
            reply_text = response.text.strip()
            # Remove any extra formatting or code blocks
            if reply_text.startswith('"') and reply_text.endswith('"'):
                reply_text = reply_text[1:-1]
            if reply_text.startswith("Reply:"):
                reply_text = reply_text[len("Reply:"):].strip()
            logger.info(f"Generated reply: {reply_text}")
            return reply_text
        except asyncio.TimeoutError:
            logger.error("Timeout while generating reply, using fallback.")
            return fallback_reply
        except Exception as e:
            logger.error(f"Error generating reply: {e}, using fallback.")
            return fallback_reply

    async def upload_reply(self, username, orig_key, reply, platform):
        # Compose new key based on original file type
        base = os.path.basename(orig_key)
        if base.startswith("ai_dm_"):
            num = base[len("ai_dm_"):].split(".")[0]
            replied_key = f"ai_reply/{platform}/{username}/ai_dm_replied_{num}.json"
        elif base.startswith("ai_comment_"):
            num = base[len("ai_comment_"):].split(".")[0]
            replied_key = f"ai_reply/{platform}/{username}/ai_comment_replied_{num}.json"
        else:
            # fallback for unexpected cases
            num = base.split("_")[2].split(".")[0] if "_" in base else "unknown"
            replied_key = f"ai_reply/{platform}/{username}/ai_replied_{num}.json"
        payload = {"reply": reply}
        await self.tasks_client.write_json(replied_key, payload)
        logger.info(f"Uploaded reply to {replied_key}")

    async def mark_as_processed(self, key):
        # Optionally update status or move/delete original
        try:
            payload = await self.tasks_client.read_json(key)
            payload["status"] = "processed"
            await self.tasks_client.write_json(key, payload)
        except Exception as e:
            logger.warning(f"Failed to mark {key} as processed: {e}")

async def main():
    handler = AIReplyHandler()
    await handler.watch_and_process()

if __name__ == "__main__":
    asyncio.run(main()) 