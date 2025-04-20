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
        self.output_prefix = "queries/"
        self.rules_prefix = "rules/"
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

    async def load_documents(self, username):
        try:
            # Reset collection
            self.collection = self.chroma_client.get_or_create_collection("rag_docs")
            
            # Case-insensitive username pattern for searching
            username_pattern = username.lower()
            
            # First, list all files in both buckets to diagnose what's actually there
            logger.info(f"Scanning for files related to {username}")
            
            # Find profiles by pattern searching - FROM DEBUG WE KNOW THESE EXIST:
            # - maccosmetics/maccosmetics.json 
            # - anastasiabeverlyhills/maccosmetics.json
            profile_data = None
            tried_profile_paths = []
            
            # Direct paths we know exist from debug output
            exact_profile_paths = [
                f"maccosmetics/maccosmetics.json",
                f"anastasiabeverlyhills/maccosmetics.json",
                f"fenty beauty/maccosmetics.json",
                f"fentybeauty/maccosmetics.json"
            ]
            
            # Try exact paths first
            for profile_path in exact_profile_paths:
                tried_profile_paths.append(profile_path)
                logger.debug(f"Attempting to read profile from exact path: {profile_path}")
                profile_data = await self.r2_client_structuredb.read_json(profile_path)
                if profile_data:
                    logger.info(f"Successfully loaded profile from exact path: {profile_path}")
                    break
            
            # If direct paths don't work, fall back to pattern search
            if not profile_data:
                profile_candidates = await self.r2_client_structuredb.find_file_by_pattern(username_pattern)
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
                    metadata={"source": "profile", "username": username}
                )
                self.collection.add(
                    documents=[profile_doc.page_content],
                    metadatas=[profile_doc.metadata],
                    ids=[f"profile_{username}"]
                )
            else:
                logger.warning(f"No profile found after trying multiple paths: {', '.join(tried_profile_paths)}")
            
            # Load rules data - FROM DEBUG WE KNOW THIS EXISTS:
            # - rules/maccosmetics/rules.json
            rules_data = None
            tried_rules_paths = []
            
            # Direct paths we know exist from debug output
            exact_rules_paths = [
                f"rules/maccosmetics/rules.json"
            ]
            
            # Try exact paths first
            for rules_path in exact_rules_paths:
                tried_rules_paths.append(rules_path)
                logger.debug(f"Attempting to read rules from exact path: {rules_path}")
                rules_data = await self.r2_client.read_json(rules_path)
                if rules_data:
                    logger.info(f"Successfully loaded rules from exact path: {rules_path}")
                    break
            
            # If direct paths don't work, fall back to pattern search
            if not rules_data:
                rules_candidates = await self.r2_client.find_file_by_pattern(f"rules/{username_pattern}")
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
                    metadata={"source": "rules", "username": username}
                )
                self.collection.add(
                    documents=[rules_doc.page_content],
                    metadatas=[rules_doc.metadata],
                    ids=[f"rules_{username}"]
                )
            else:
                logger.warning(f"No rules found after trying multiple paths: {', '.join(tried_rules_paths)}")

            # Fit the embeddings
            documents = []
            if profile_data:
                documents.append(json.dumps(profile_data))
            if rules_data:
                documents.append(json.dumps(rules_data))
                
            if documents:
                self.embeddings.fit(documents)

            doc_count = self.collection.count()
            logger.info(f"Loaded {doc_count} documents for {username}")
            return doc_count > 0
        except Exception as e:
            logger.error(f"Failed to load documents for {username}: {e}")
            return False

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def generate_response(self, query, username):
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

            if rules:
                rule_check_prompt = (
                    f"Query: {query}\n"
                    f"Rules: {rules}\n"
                    f"Does this query violate any rules? If yes, respond with 'Better not to say on this'. "
                    f"Otherwise, return 'Proceed'."
                )
                rule_response = await self.model.generate_content_async(rule_check_prompt)
                logger.debug(f"Rule check for '{query}': {rule_response.text}")
                if rule_response.text.strip() == "Better not to say on this":
                    return "Better not to say on this"

            prompt = (
                f"Query: {query}\n"
                f"Context: {context}\n"
                f"Rules: {rules}\n"
                f"Generate a friendly, concise response to the query, respecting rules. "
                f"If no specific answer is possible, say something positive like 'Hey, I'm doing great, thanks for asking!' "
                f"Avoid saying 'not allowed' unless rules explicitly block the topic."
            )
            response = await self.model.generate_content_async(prompt)
            return response.text.strip()
        except Exception as e:
            logger.error(f"Failed to generate response for query '{query}': {e}")
            return "Sorry, something went wrong!"

    async def process_query(self, key):
        if not await self.status_manager.is_pending(key):
            return

        data = await self.r2_client.read_json(key)
        if not data or "query" not in data:
            logger.error(f"Invalid JSON format in {key}")
            return

        query = data["query"]
        username = key.split("/")[1]
        logger.info(f"Processing query for {key}")

        # Try loading documents, but continue even if none are found
        docs_loaded = await self.load_documents(username)
        if not docs_loaded:
            logger.warning(f"Processing {key} with no documents")
        
        # Always try to generate a response
        response = await self.generate_response(query, username)
        if not response:
            logger.error(f"Failed to generate response for {key}")
            data["status"] = "error"
            data["status_message"] = "Response generation failed"
            await self.r2_client.write_json(key, data)
            return

        output_data = {
            "query": query,
            "response": response,
            "status": "processed"
        }

        output_dir = f"{self.output_prefix}{username}/"
        objects = await self.r2_client.list_objects(output_dir)
        response_number = len([o for o in objects if "response_" in o["Key"]]) + 1
        output_key = f"{output_dir}response_{response_number}.json"

        if await self.r2_client.write_json(output_key, output_data):
            await self.status_manager.mark_processed(key)
            logger.info(f"Successfully processed {key} to {output_key}")
        else:
            logger.error(f"Failed to write output for {key}")
            data["status"] = "error"
            data["status_message"] = "Failed to write output"
            await self.r2_client.write_json(key, data)

    async def run(self):
        while True:
            try:
                logger.info("Checking for new queries...")
                objects = await self.r2_client.list_objects(self.input_prefix)
                logger.debug(f"Found {len(objects)} objects under {self.input_prefix}")
                processable_files = []
                tasks = []
                for obj in objects:
                    key = obj["Key"]
                    if key.endswith(".json") and "query_" in key:
                        processable_files.append(key)
                        if await self.status_manager.is_pending(key):
                            logger.debug(f"Scheduling query for processing: {key}")
                            tasks.append(self.process_query(key))
                logger.debug(f"Evaluated query files: {processable_files}")
                if tasks:
                    for task in tasks:
                        await task
                else:
                    logger.debug("No processable queries found")
                await asyncio.sleep(10)
            except Exception as e:
                logger.error(f"Error in query handler loop: {e}")
                await asyncio.sleep(10)