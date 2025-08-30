"""
Robust Usage Tracking API for Social Media Management Platform
Handles user-specific usage tracking with backend synchronization
"""

import json
import os
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from flask import Flask, request, jsonify
from flask_cors import CORS
import uuid

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

class UsageTracker:
    def __init__(self, data_dir: str = "usage_data"):
        """Initialize usage tracker with persistent storage"""
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)
        logger.info(f"✅ UsageTracker initialized with data directory: {data_dir}")
    
    def _get_user_file_path(self, user_id: str, platform: str) -> str:
        """Get the file path for user's usage data"""
        return os.path.join(self.data_dir, f"{user_id}_{platform}_usage.json")
    
    def _get_current_period(self) -> str:
        """Get current period (YYYY-MM format)"""
        return datetime.now().strftime("%Y-%m")
    
    def _load_user_usage(self, user_id: str, platform: str) -> Dict[str, Any]:
        """Load user usage data from file"""
        file_path = self._get_user_file_path(user_id, platform)
        
        if not os.path.exists(file_path):
            # Create new usage record
            usage_data = {
                "platform": platform,
                "username": user_id,
                "period": self._get_current_period(),
                "postsUsed": 0,
                "discussionsUsed": 0,
                "aiRepliesUsed": 0,
                "campaignsUsed": 0,
                "viewsUsed": 0,
                "resetsUsed": 0,
                "lastUpdated": datetime.now().isoformat(),
                "createdAt": datetime.now().isoformat()
            }
            self._save_user_usage(user_id, platform, usage_data)
            logger.info(f"📁 Created new usage file for {user_id} on {platform}")
            return usage_data
        
        try:
            with open(file_path, 'r') as f:
                usage_data = json.load(f)
                
            # Check if we need to reset for new period
            current_period = self._get_current_period()
            if usage_data.get("period") != current_period:
                logger.info(f"🔄 Resetting usage for new period: {current_period}")
                usage_data.update({
                    "period": current_period,
                    "postsUsed": 0,
                    "discussionsUsed": 0,
                    "aiRepliesUsed": 0,
                    "campaignsUsed": 0,
                    "viewsUsed": 0,
                    "resetsUsed": 0,
                    "lastUpdated": datetime.now().isoformat()
                })
                self._save_user_usage(user_id, platform, usage_data)
            
            return usage_data
            
        except Exception as e:
            logger.error(f"❌ Error loading usage data for {user_id}: {e}")
            # Return default data if file is corrupted
            return self._load_user_usage(user_id, platform)
    
    def _save_user_usage(self, user_id: str, platform: str, usage_data: Dict[str, Any]) -> None:
        """Save user usage data to file"""
        file_path = self._get_user_file_path(user_id, platform)
        usage_data["lastUpdated"] = datetime.now().isoformat()
        
        try:
            with open(file_path, 'w') as f:
                json.dump(usage_data, f, indent=2)
            logger.info(f"💾 Saved usage data for {user_id} on {platform}")
        except Exception as e:
            logger.error(f"❌ Error saving usage data for {user_id}: {e}")
    
    def increment_feature_usage(self, user_id: str, platform: str, feature: str, increment: int = 1) -> Dict[str, Any]:
        """
        Increment usage for a specific feature
        Features: posts, discussions, aiReplies, campaigns, views, resets
        """
        logger.info(f"🚀 Incrementing {feature} usage for {user_id} on {platform} by {increment}")
        
        # Load current usage
        usage_data = self._load_user_usage(user_id, platform)
        
        # Map feature names to storage keys
        feature_map = {
            "posts": "postsUsed",
            "discussions": "discussionsUsed", 
            "aiReplies": "aiRepliesUsed",
            "campaigns": "campaignsUsed",
            "views": "viewsUsed",
            "resets": "resetsUsed"
        }
        
        if feature not in feature_map:
            logger.error(f"❌ Invalid feature: {feature}")
            raise ValueError(f"Invalid feature: {feature}")
        
        storage_key = feature_map[feature]
        old_count = usage_data.get(storage_key, 0)
        new_count = old_count + increment
        usage_data[storage_key] = new_count
        
        # Save updated usage
        self._save_user_usage(user_id, platform, usage_data)
        
        logger.info(f"✅ {feature} usage updated: {old_count} → {new_count}")
        
        return {
            "success": True,
            "feature": feature,
            "oldCount": old_count,
            "newCount": new_count,
            "increment": increment,
            "platform": platform,
            "username": user_id,
            "total": usage_data
        }
    
    def get_user_usage(self, user_id: str, platform: str) -> Dict[str, Any]:
        """Get current usage data for user"""
        usage_data = self._load_user_usage(user_id, platform)
        logger.info(f"📊 Retrieved usage data for {user_id} on {platform}")
        return {
            "success": True,
            "usage": {
                "posts": usage_data.get("postsUsed", 0),
                "discussions": usage_data.get("discussionsUsed", 0),
                "aiReplies": usage_data.get("aiRepliesUsed", 0),
                "campaigns": usage_data.get("campaignsUsed", 0),
                "views": usage_data.get("viewsUsed", 0),
                "resets": usage_data.get("resetsUsed", 0)
            },
            "platform": platform,
            "username": user_id,
            "period": usage_data.get("period"),
            "lastUpdated": usage_data.get("lastUpdated")
        }
    
    def reset_user_usage(self, user_id: str, platform: str) -> Dict[str, Any]:
        """Reset usage for user (admin function)"""
        logger.info(f"🔄 Resetting usage for {user_id} on {platform}")
        
        usage_data = {
            "platform": platform,
            "username": user_id,
            "period": self._get_current_period(),
            "postsUsed": 0,
            "discussionsUsed": 0,
            "aiRepliesUsed": 0,
            "campaignsUsed": 0,
            "viewsUsed": 0,
            "resetsUsed": 0,
            "lastUpdated": datetime.now().isoformat(),
            "createdAt": datetime.now().isoformat()
        }
        
        self._save_user_usage(user_id, platform, usage_data)
        
        return {
            "success": True,
            "message": "Usage reset successfully",
            "usage": self.get_user_usage(user_id, platform)["usage"]
        }

# Initialize global tracker
tracker = UsageTracker()

@app.route('/api/usage/increment', methods=['POST'])
def increment_usage():
    """API endpoint to increment feature usage"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"success": False, "error": "No data provided"}), 400
        
        # Extract required fields
        user_id = data.get('user_id') or data.get('username')
        platform = data.get('platform', 'instagram')
        feature = data.get('feature')
        increment = data.get('increment', 1)
        
        if not user_id or not feature:
            return jsonify({
                "success": False, 
                "error": "user_id and feature are required"
            }), 400
        
        # Increment usage
        result = tracker.increment_feature_usage(user_id, platform, feature, increment)
        
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"❌ Error in increment_usage: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/usage/get', methods=['GET'])
def get_usage():
    """API endpoint to get current usage"""
    try:
        user_id = request.args.get('user_id') or request.args.get('username')
        platform = request.args.get('platform', 'instagram')
        
        if not user_id:
            return jsonify({
                "success": False,
                "error": "user_id is required"
            }), 400
        
        result = tracker.get_user_usage(user_id, platform)
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"❌ Error in get_usage: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/usage/reset', methods=['POST'])
def reset_usage():
    """API endpoint to reset usage (admin only)"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"success": False, "error": "No data provided"}), 400
        
        user_id = data.get('user_id') or data.get('username')
        platform = data.get('platform', 'instagram')
        
        if not user_id:
            return jsonify({
                "success": False,
                "error": "user_id is required"
            }), 400
        
        result = tracker.reset_user_usage(user_id, platform)
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"❌ Error in reset_usage: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/usage/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "success": True,
        "message": "Usage tracking API is running",
        "timestamp": datetime.now().isoformat()
    }), 200

if __name__ == '__main__':
    logger.info("🚀 Starting Usage Tracking API...")
    app.run(debug=True, host='0.0.0.0', port=5001)
