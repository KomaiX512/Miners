"""API for Instagram scraper and content recommendation system."""

from flask import Flask, request, jsonify
from flask_cors import CORS
import logging
import json
import os
from instagram_scraper import InstagramScraper
from config import LOGGING_CONFIG

# Set up logging
logging.basicConfig(
    level=LOGGING_CONFIG['level'],
    format=LOGGING_CONFIG['format']
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Initialize scraper
scraper = InstagramScraper()

# Import main module functions instead of the class
import main

@app.route('/api/scrape', methods=['POST'])
def scrape_profile():
    """Scrape Instagram profile and upload to R2."""
    try:
        data = request.json
        username = data.get('username')
        
        if not username:
            return jsonify({"success": False, "message": "Username is required"}), 400
        
        # Scrape and upload
        result = scraper.scrape_and_upload(username)
        
        if not result["success"]:
            return jsonify(result), 500
        
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"Error in scrape_profile: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/analyze', methods=['POST'])
def analyze_profile():
    """Analyze Instagram profile and generate recommendations."""
    try:
        data = request.json
        username = data.get('username')
        
        if not username:
            return jsonify({"success": False, "message": "Username is required"}), 400
        
        # First, scrape and upload
        scrape_result = scraper.scrape_and_upload(username)
        
        if not scrape_result["success"]:
            return jsonify({"success": False, "message": "Failed to scrape profile"}), 500
        
        # Then, run the recommendation pipeline using the main function
        object_key = scrape_result["object_key"]
        
        # Call the main function to run the pipeline
        # This assumes your main.py has a function that can be called to run the pipeline
        pipeline_result = main.run_pipeline(object_key)
        
        if not pipeline_result or not pipeline_result.get("success", False):
            return jsonify({
                "success": False, 
                "message": "Failed to generate recommendations",
                "details": pipeline_result
            }), 500
        
        # Return success with content plan
        return jsonify({
            "success": True,
            "message": "Successfully generated recommendations",
            "details": pipeline_result
        }), 200
        
    except Exception as e:
        logger.error(f"Error in analyze_profile: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/content_plan', methods=['GET'])
def get_content_plan():
    """Get the latest content plan."""
    try:
        # Check if content plan file exists
        if not os.path.exists('content_plan.json'):
            return jsonify({
                "success": False,
                "message": "No content plan available"
            }), 404
            
        # Load the content plan from file
        with open('content_plan.json', 'r') as f:
            content_plan = json.load(f)
        
        return jsonify({
            "success": True,
            "content_plan": content_plan
        }), 200
        
    except Exception as e:
        logger.error(f"Error in get_content_plan: {str(e)}")
        return jsonify({"success": False, "message": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True, port=5000) 