import aiohttp
import asyncio
import json
from utils.r2_client import R2Client
from utils.status_manager import StatusManager
from utils.logging import logger
from config import GEMINI_CONFIG, R2_CONFIG, STRUCTUREDB_R2_CONFIG
import chromadb
from langchain.docstore.document import Document
from tenacity import retry, stop_after_attempt, wait_exponential
import google.generativeai as genai
from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np
import asyncio
from fastapi import FastAPI, BackgroundTasks, Request
import uvicorn

class SimpleEmbeddings:
    def __init__(self):
        self.vectorizer = TfidfVectorizer()
        self.fitted = False
        self.documents = []
        
    def fit(self, texts):
        self.documents = texts
        self.vectorizer.fit(texts)
        self.fitted = True
        
    def embed_documents(self, texts):
        if not self.fitted:
            self.fit(texts)
        return self.vectorizer.transform(texts).toarray().tolist()
        
    def embed_query(self, text):
        if not self.fitted:
            self.fit([text])
        return self.vectorizer.transform([text]).toarray().tolist()[0]

class QueryHandler:
    def __init__(self):
        self.r2_client = R2Client(config=R2_CONFIG)  # Tasks bucket
        self.r2_client_structuredb = R2Client(config=STRUCTUREDB_R2_CONFIG)  # Structuredb bucket
        self.status_manager = StatusManager()
        self.input_prefix = "queries/"
        self.output_prefix = "next_posts/"  # Changed from "queries/" to "next_posts/"
        self.rules_prefix = "rules/"
        self.platforms = ["instagram", "twitter"]  # Support both platforms
        self.embeddings = SimpleEmbeddings()
        self.chroma_client = chromadb.Client()
        self.collection = self.chroma_client.get_or_create_collection("rag_docs")
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
        self.app = FastAPI()
        self.setup_routes()
        
    def setup_routes(self):
        @self.app.post("/process-query")
        async def process_query_endpoint(request: Request, background_tasks: BackgroundTasks):
            data = await request.json()
            key = data.get("key")
            if key and key.startswith(self.input_prefix) and key.endswith(".json") and "query_" in key:
                background_tasks.add_task(self.process_query, key)
                return {"status": "processing", "key": key}
            return {"status": "error", "message": "Invalid query key"}
            
        @self.app.post("/scan-pending-queries")
        async def scan_pending_queries(background_tasks: BackgroundTasks):
            background_tasks.add_task(self.scan_for_pending_queries)
            return {"status": "scanning"}
    
    async def scan_for_pending_queries(self):
        """Scan for pending queries and process them - can be triggered periodically"""
        try:
            logger.info("Scanning for pending queries across all platforms...")
            processed_count = 0
            tasks = []
            
            # Scan both platforms for queries
            for platform in self.platforms:
                platform_prefix = f"{self.input_prefix}{platform}/"
                objects = await self.r2_client.list_objects(platform_prefix)
                logger.debug(f"Found {len(objects)} objects under {platform_prefix}")
            
            for obj in objects:
                key = obj["Key"]
                if key.endswith(".json") and "query_" in key:
                    if await self.status_manager.is_pending(key):
                        logger.debug(f"Processing pending query: {key}")
                        tasks.append(self.process_query(key))
                        processed_count += 1
            
            if tasks:
                await asyncio.gather(*tasks)
                logger.info(f"Processed {processed_count} pending queries across all platforms")
            else:
                logger.debug("No pending queries found")
                
        except Exception as e:
            logger.error(f"Error in scanning pending queries: {e}")

    async def load_documents(self, username, platform="instagram"):
        try:
            # Reset collection
            self.collection = self.chroma_client.get_or_create_collection("rag_docs")
            
            # Case-insensitive username pattern for searching
            username_pattern = username.lower()
            
            # Find profiles by pattern searching with platform awareness
            logger.info(f"Scanning for {platform} files related to {username}")
            
            profile_data = None
            tried_profile_paths = []
            
            # Platform-aware profile paths - NEW SCHEMA: platform/username/username.json
            exact_profile_paths = [
                f"{platform}/{username}/{username}.json",
                f"{platform}/maccosmetics/maccosmetics.json",
                f"{platform}/anastasiabeverlyhills/maccosmetics.json",
                f"{platform}/fenty beauty/maccosmetics.json",
                f"{platform}/fentybeauty/maccosmetics.json"
            ]
            
            # Try exact paths first
            for profile_path in exact_profile_paths:
                tried_profile_paths.append(profile_path)
                logger.debug(f"Attempting to read profile from exact path: {profile_path}")
                profile_data = await self.r2_client_structuredb.read_json(profile_path)
                if profile_data:
                    logger.info(f"Successfully loaded profile from exact path: {profile_path}")
                    break
            
            # If direct paths don't work, fall back to pattern search within platform
            if not profile_data:
                platform_pattern = f"{platform}/{username_pattern}"
                profile_candidates = await self.r2_client_structuredb.find_file_by_pattern(platform_pattern)
                for profile_path in profile_candidates:
                    if profile_path not in tried_profile_paths:
                        tried_profile_paths.append(profile_path)
                        logger.debug(f"Attempting to read profile from found path: {profile_path}")
                        profile_data = await self.r2_client_structuredb.read_json(profile_path)
                        if profile_data:
                            logger.info(f"Successfully loaded profile from found path: {profile_path}")
                            break
            
            if profile_data:
                profile_doc = Document(
                    page_content=json.dumps(profile_data),
                    metadata={"source": "profile", "username": username, "platform": platform}
                )
                self.collection.add(
                    documents=[profile_doc.page_content],
                    metadatas=[profile_doc.metadata],
                    ids=[f"profile_{platform}_{username}"]
                )
            else:
                logger.warning(f"No {platform} profile found after trying multiple paths: {', '.join(tried_profile_paths)}")
            
            # Load rules data with platform awareness - NEW SCHEMA: rules/platform/username/rules.json
            rules_data = None
            tried_rules_paths = []
            
            # Platform-aware rules paths
            exact_rules_paths = [
                f"rules/{platform}/{username}/rules.json",
                f"rules/{platform}/maccosmetics/rules.json"
            ]
            
            # Try exact paths first
            for rules_path in exact_rules_paths:
                tried_rules_paths.append(rules_path)
                logger.debug(f"Attempting to read rules from exact path: {rules_path}")
                rules_data = await self.r2_client.read_json(rules_path)
                if rules_data:
                    logger.info(f"Successfully loaded rules from exact path: {rules_path}")
                    break
            
            # If direct paths don't work, fall back to pattern search within platform
            if not rules_data:
                platform_rules_pattern = f"rules/{platform}/{username_pattern}"
                rules_candidates = await self.r2_client.find_file_by_pattern(platform_rules_pattern)
                for rules_path in rules_candidates:
                    if rules_path not in tried_rules_paths:
                        tried_rules_paths.append(rules_path)
                        logger.debug(f"Attempting to read rules from found path: {rules_path}")
                        rules_data = await self.r2_client.read_json(rules_path)
                        if rules_data:
                            logger.info(f"Successfully loaded rules from found path: {rules_path}")
                            break
            
            if rules_data:
                rules_doc = Document(
                    page_content=json.dumps(rules_data),
                    metadata={"source": "rules", "username": username, "platform": platform}
                )
                self.collection.add(
                    documents=[rules_doc.page_content],
                    metadatas=[rules_doc.metadata],
                    ids=[f"rules_{platform}_{username}"]
                )
            else:
                logger.warning(f"No {platform} rules found after trying multiple paths: {', '.join(tried_rules_paths)}")

            # Fit the embeddings
            documents = []
            if profile_data:
                documents.append(json.dumps(profile_data))
            if rules_data:
                documents.append(json.dumps(rules_data))
                
            if documents:
                self.embeddings.fit(documents)

            doc_count = self.collection.count()
            logger.info(f"Loaded {doc_count} {platform} documents for {username}")
            return doc_count > 0
        except Exception as e:
            logger.error(f"Failed to load {platform} documents for {username}: {e}")
            return False

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def generate_post_content(self, query, username):
        """Generate social media post content based on the query and user profile"""
        try:
            doc_count = self.collection.count()
            k = min(2, doc_count) if doc_count > 0 else 0

            context = ""
            rules = ""
            if k > 0:
                results = self.collection.query(
                    query_texts=[query],
                    n_results=k
                )
                
                for i, metadata in enumerate(results.get('metadatas', [[]])[0]):
                    doc_content = results['documents'][0][i]
                    if metadata.get("source") == "rules":
                        rules += doc_content + "\n"
                    else:
                        context += doc_content + "\n"
                logger.debug(f"Retrieved for query '{query}': rules={rules}, context={context}")

            # Define a fallback response in case of timeout or other errors
            fallback_response = {
                "caption": f"Check out our latest products! {query}",
                "hashtags": ["#MACCosmetics", "#Beauty", "#MakeupLover", "#NewCollection", "#MustHave"],
                "call_to_action": "Shop now and tell us what you think in the comments!",
                "visual_prompt": f"A professional, high-quality image showcasing {query} with the brand's signature aesthetic. Clean background, perfect lighting, and stylish arrangement."
            }

            if rules:
                try:
                    rule_check_prompt = (
                        f"Query: {query}\n"
                        f"Rules: {rules}\n"
                        f"Does this query violate any rules? If yes, respond with 'Better not to say on this'. "
                        f"Otherwise, return 'Proceed'."
                    )
                    rule_response = await asyncio.wait_for(
                        self.model.generate_content_async(rule_check_prompt),
                        timeout=30  # 30 second timeout for rule check
                    )
                    logger.debug(f"Rule check for '{query}': {rule_response.text}")
                    if rule_response.text.strip() == "Better not to say on this":
                        return None
                except asyncio.TimeoutError:
                    logger.warning(f"Rule check timed out for query '{query}', proceeding with caution")
                except Exception as e:
                    logger.warning(f"Rule check failed for query '{query}': {e}, proceeding with caution")

            # Enhanced prompt for generating high-quality, contextual social media post content
            prompt = (
                f"You are a premium social media content creator for a top brand. Your task is to create a perfect social media post based on the following instruction and context.\n\n"
                f"INSTRUCTION: {query}\n\n"
                f"PROFILE DATA & CONTEXT: {context}\n\n"
                f"BRAND RULES: {rules}\n\n"
                f"Create social media post content that perfectly matches the brand's style, voice, and theme. "
                f"The content should be authentic, engaging, and completely aligned with existing posts from this account. "
                f"Maintain consistency with the account's aesthetics and messaging patterns. "
                f"Include appropriate tone, language style, and visual descriptions that would resonate with their audience.\n\n"
                f"Respond ONLY with a JSON object containing these exact fields:\n"
                f"1. 'caption': An engaging and authentic caption perfectly matching the brand voice (1-3 sentences)\n"
                f"2. 'hashtags': An array of 5-7 relevant, brand-aligned hashtags (include the # symbol)\n"
                f"3. 'call_to_action': A compelling call-to-action that would drive engagement\n"
                f"4. 'visual_prompt': A detailed description for creating an image that perfectly matches the brand aesthetic\n\n"
                f"The JSON should be properly formatted with no additional text. Example format:\n"
                f"{{\n"
                f"  \"caption\": \"...\",\n"
                f"  \"hashtags\": [\"#tag1\", \"#tag2\", \"#tag3\", \"#tag4\", \"#tag5\"],\n"
                f"  \"call_to_action\": \"...\",\n"
                f"  \"visual_prompt\": \"...\"\n"
                f"}}"
            )
            
            try:
                # Use asyncio.wait_for to implement a timeout
                response = await asyncio.wait_for(
                    self.model.generate_content_async(prompt),
                    timeout=60  # 60 second timeout for content generation
                )
                response_text = response.text.strip()
                
                # Extract JSON part if there's any surrounding text
                if response_text.startswith("{") and response_text.endswith("}"):
                    try:
                        # Already in JSON format
                        content = json.loads(response_text)
                        return content
                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to parse response as JSON: {e}")
                        logger.info(f"Falling back to default response due to JSON parse error")
                        return fallback_response
                else:
                    # Try to extract JSON from text
                    try:
                        json_start = response_text.find("{")
                        json_end = response_text.rfind("}") + 1
                        if json_start >= 0 and json_end > json_start:
                            json_str = response_text[json_start:json_end]
                            content = json.loads(json_str)
                            return content
                        else:
                            logger.error(f"Could not find JSON in response text")
                            logger.info(f"Falling back to default response due to missing JSON")
                            return fallback_response
                    except (json.JSONDecodeError, ValueError) as e:
                        logger.error(f"Failed to extract JSON from response: {e}")
                        logger.info(f"Falling back to default response due to JSON extraction error")
                        return fallback_response
            except asyncio.TimeoutError:
                logger.error(f"Request timed out while generating content for query '{query}'")
                logger.info(f"Using fallback response due to timeout")
                return fallback_response
            except Exception as e:
                logger.error(f"Error generating content for query '{query}': {e}")
                logger.info(f"Using fallback response due to error: {str(e)}")
                return fallback_response
            
            # This should never be reached, but as a final fallback
            logger.warning(f"Unexpected code path in generate_post_content for '{query}'")
            return fallback_response
            
        except Exception as e:
            logger.error(f"Failed to generate post content for query '{query}': {e}")
            logger.info(f"Using fallback response due to unexpected error")
            # Return fallback response instead of None
            return {
                "caption": f"Check out our latest products! {query}",
                "hashtags": ["#MACCosmetics", "#Beauty", "#MakeupLover", "#NewCollection", "#MustHave"],
                "call_to_action": "Shop now and tell us what you think in the comments!",
                "visual_prompt": f"A professional, high-quality image showcasing {query} with the brand's signature aesthetic. Clean background, perfect lighting, and stylish arrangement."
            }

    async def process_query(self, key):
        if not await self.status_manager.is_pending(key):
            return

        data = await self.r2_client.read_json(key)
        if not data or "query" not in data:
            logger.error(f"Invalid JSON format in {key}")
            return

        query = data["query"]
        # Extract platform and username from new schema: queries/platform/username/query_*.json
        key_parts = key.split("/")
        if len(key_parts) < 4:
            logger.error(f"Invalid key format for new schema: {key}")
            return
            
        platform = key_parts[1]  # queries/platform/username/file.json
        username = key_parts[2]
        
        logger.info(f"Processing {platform} query for {key}")

        # Try loading documents with platform awareness
        docs_loaded = await self.load_documents(username, platform)
        if not docs_loaded:
            logger.warning(f"Processing {key} with no {platform} documents")
        
        # Generate post content
        post_content = await self.generate_post_content(query, username)
        if not post_content:
            logger.error(f"Failed to generate post content for {key}")
            data["status"] = "error"
            data["status_message"] = "Post content generation failed"
            await self.r2_client.write_json(key, data)
            return

        # Add status to the output
        post_content["status"] = "processed"

        # Create platform-aware output directory path - NEW SCHEMA: next_posts/platform/username/
        output_dir = f"{self.output_prefix}{platform}/{username}/"
        
        # Get sequential post number
        try:
            objects = await self.r2_client.list_objects(output_dir)
            urgent_number = len([o for o in objects if "urgent_" in o["Key"]]) + 1
        except Exception as e:
            logger.warning(f"Error listing objects in {output_dir}, assuming first urgent post: {e}")
            urgent_number = 1
            
        output_key = f"{output_dir}urgent_{urgent_number}.json"

        if await self.r2_client.write_json(output_key, post_content):
            await self.status_manager.mark_processed(key)
            logger.info(f"Successfully processed {key} to {output_key}")
        else:
            logger.error(f"Failed to write output for {key}")
            data["status"] = "error"
            data["status_message"] = "Failed to write output"
            await self.r2_client.write_json(key, data)

    async def run(self, host="0.0.0.0", port=8000):
        """Run the API server to handle query processing events"""
        try:
            # Do an initial scan for any pending queries
            await self.scan_for_pending_queries()
            
            # Start the FastAPI server
            config = uvicorn.Config(app=self.app, host=host, port=port)
            server = uvicorn.Server(config)
            await server.serve()
        except Exception as e:
            logger.error(f"Failed to start query handler service: {e}")

# Add a standalone function to run the handler
async def run_handler():
    handler = QueryHandler()
    await handler.run()

if __name__ == "__main__":
    asyncio.run(run_handler())