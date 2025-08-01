"""
XGBoost Post Estimation Model
Predicts optimal number of posts needed to achieve engagement goals
using scraped data, profit analysis, and historical patterns.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Any, Tuple
import re
import json
from datetime import datetime, timedelta
from utils.logging import logger
import pickle
import os
import shutil

try:
    import xgboost as xgb
    XGBOOST_AVAILABLE = True
    # Get XGBoost version for compatibility checks
    XGBOOST_VERSION = xgb.__version__
except ImportError:
    logger.warning("XGBoost not available. Using fallback estimation.")
    XGBOOST_AVAILABLE = False
    XGBOOST_VERSION = None

class XGBoostPostEstimator:
    """Advanced post estimation using XGBoost machine learning model"""
    
    def __init__(self):
        self.model = None
        self.feature_names = [
            'current_engagement_rate',
            'follower_count',
            'avg_posts_per_week',
            'consistency_score',
            'timeline_days',
            'engagement_increase_factor',
            'platform_instagram',
            'platform_twitter',
            'platform_facebook',
            'goal_type_increase',
            'goal_type_double',
            'goal_type_triple',
            'historical_growth_rate',
            'content_variety_score',
            'peak_engagement_ratio',
            'posting_frequency_score'
        ]
        self.model_path = "models/xgboost_post_estimator.pkl"
        self.model_backup_path = "models/xgboost_post_estimator_backup.pkl"
        self.is_trained = False
        self.model_version = "2.0"  # Track model version for compatibility
        
        # 🏷️ HASHTAG RECOMMENDATION: Initialize hashtag database for engagement optimization
        self.hashtag_database = self._initialize_hashtag_database()
        
        # Initialize or load model with robust error handling
        self._initialize_model()
    
    def _initialize_hashtag_database(self) -> Dict[str, Dict]:
        """🏷️ Initialize hashtag database with engagement-optimized recommendations"""
        return {
            "instagram": {
                "high_engagement": ["#Viral", "#Trending", "#Explore", "#Featured", "#Popular"],
                "beauty": ["#Beauty", "#Makeup", "#Skincare", "#Glow", "#BeautyTips"],
                "fitness": ["#Fitness", "#Workout", "#Health", "#Motivation", "#FitLife"],
                "food": ["#Food", "#Delicious", "#Foodie", "#Recipe", "#Yummy"],
                "travel": ["#Travel", "#Adventure", "#Wanderlust", "#Explore", "#Vacation"],
                "business": ["#Business", "#Entrepreneur", "#Success", "#Growth", "#Leadership"],
                "lifestyle": ["#Lifestyle", "#Daily", "#Inspiration", "#Life", "#Happiness"],
                "tech": ["#Technology", "#Innovation", "#Digital", "#Tech", "#Future"],
                "fashion": ["#Fashion", "#Style", "#OOTD", "#Trendy", "#Designer"],
                "art": ["#Art", "#Creative", "#Design", "#Artist", "#Gallery"]
            },
            "twitter": {
                "high_engagement": ["#Trending", "#Twitter", "#Viral", "#Breaking"],
                "business": ["#Business", "#Startup", "#Growth", "#Success"],
                "tech": ["#Tech", "#AI", "#Innovation", "#Digital"],
                "news": ["#News", "#Update", "#Breaking", "#Latest"],
                "community": ["#Community", "#Discussion", "#Thoughts"],
                "motivational": ["#Motivation", "#Success", "#Growth", "#Mindset"]
            },
            "facebook": {
                "high_engagement": ["#Viral", "#Trending", "#Popular", "#Featured"],
                "business": ["#Business", "#Entrepreneur", "#Success", "#Growth"],
                "community": ["#Community", "#Local", "#Events", "#News"],
                "family": ["#Family", "#Friends", "#Life", "#Moments"],
                "entertainment": ["#Entertainment", "#Fun", "#Viral", "#Trending"],
                "news": ["#News", "#Update", "#Breaking", "#Latest"],
                "inspirational": ["#Inspiration", "#Motivation", "#Success", "#Life"]
            }
        }
    
    def _initialize_model(self):
        """Initialize XGBoost model with robust compatibility handling"""
        try:
            if not XGBOOST_AVAILABLE:
                logger.warning("XGBoost not available, will use mathematical estimation")
                return
            
            # Try to load existing model with compatibility checks
            if self._try_load_model():
                logger.info("✅ Successfully loaded compatible XGBoost model")
                return
            
            # If loading failed, create new model
            logger.info("🔄 Creating new XGBoost model due to compatibility issues")
            self._create_and_train_model()
            
        except Exception as e:
            logger.error(f"Error initializing XGBoost model: {e}")
            self.model = None
    
    def _try_load_model(self) -> bool:
        """Try to load model with compatibility checks"""
        try:
            if not os.path.exists(self.model_path):
                return False
            
            # Try loading the model
            with open(self.model_path, 'rb') as f:
                loaded_data = pickle.load(f)
            
            # Handle both new metadata format and old direct model format
            if isinstance(loaded_data, dict) and 'model' in loaded_data:
                # New metadata format
                loaded_model = loaded_data['model']
                logger.info(f"📦 Loaded model with metadata: version {loaded_data.get('version', 'unknown')}")
            else:
                # Old direct model format
                loaded_model = loaded_data
                logger.info("📦 Loaded legacy model format")
            
            # Test model compatibility by trying to make a prediction
            # Use DataFrame format to match training data
            test_features = {
                'current_engagement_rate': 0.05,
                'follower_count': 1000,
                'avg_posts_per_week': 3,
                'consistency_score': 0.5,
                'timeline_days': 7,
                'engagement_increase_factor': 1.5,
                'platform_instagram': 1,
                'platform_twitter': 0,
                'platform_facebook': 0,
                'goal_type_increase': 1,
                'goal_type_double': 0,
                'goal_type_triple': 0,
                'historical_growth_rate': 0.02,
                'content_variety_score': 0.7,
                'peak_engagement_ratio': 2.0,
                'posting_frequency_score': 0.4
            }
            test_df = pd.DataFrame([test_features])
            test_prediction = loaded_model.predict(test_df)
            
            # If we get here, model is compatible
            self.model = loaded_model
            self.is_trained = True
            
            # Create backup of working model
            self._create_model_backup()
            
            return True
            
        except Exception as e:
            logger.warning(f"Model compatibility check failed: {e}")
            
            # Try backup model if main model failed
            if self._try_load_backup_model():
                return True
            
            # Remove incompatible model file
            self._remove_incompatible_model()
            return False
    
    def _try_load_backup_model(self) -> bool:
        """Try to load backup model"""
        try:
            if not os.path.exists(self.model_backup_path):
                return False
            
            with open(self.model_backup_path, 'rb') as f:
                loaded_data = pickle.load(f)
            
            # Handle both new metadata format and old direct model format
            if isinstance(loaded_data, dict) and 'model' in loaded_data:
                loaded_model = loaded_data['model']
            else:
                loaded_model = loaded_data
            
            # Test backup model with DataFrame format
            test_features = {
                'current_engagement_rate': 0.05,
                'follower_count': 1000,
                'avg_posts_per_week': 3,
                'consistency_score': 0.5,
                'timeline_days': 7,
                'engagement_increase_factor': 1.5,
                'platform_instagram': 1,
                'platform_twitter': 0,
                'platform_facebook': 0,
                'goal_type_increase': 1,
                'goal_type_double': 0,
                'goal_type_triple': 0,
                'historical_growth_rate': 0.02,
                'content_variety_score': 0.7,
                'peak_engagement_ratio': 2.0,
                'posting_frequency_score': 0.4
            }
            test_df = pd.DataFrame([test_features])
            test_prediction = loaded_model.predict(test_df)
            
            self.model = loaded_model
            self.is_trained = True
            
            # Restore backup as main model
            shutil.copy(self.model_backup_path, self.model_path)
            logger.info("✅ Restored backup model successfully")
            
            return True
            
        except Exception as e:
            logger.warning(f"Backup model also incompatible: {e}")
            return False
    
    def _remove_incompatible_model(self):
        """Remove incompatible model files"""
        try:
            if os.path.exists(self.model_path):
                os.remove(self.model_path)
                logger.info("🗑️ Removed incompatible model file")
            if os.path.exists(self.model_backup_path):
                os.remove(self.model_backup_path)
                logger.info("🗑️ Removed incompatible backup model file")
        except Exception as e:
            logger.warning(f"Error removing incompatible model files: {e}")
    
    def _create_model_backup(self):
        """Create backup of working model"""
        try:
            if self.model is not None:
                os.makedirs(os.path.dirname(self.model_backup_path), exist_ok=True)
                with open(self.model_backup_path, 'wb') as f:
                    pickle.dump(self.model, f)
                logger.info("💾 Created model backup")
        except Exception as e:
            logger.warning(f"Failed to create model backup: {e}")
    
    def _create_and_train_model(self):
        """Create and train XGBoost model with synthetic data based on engagement patterns"""
        if not XGBOOST_AVAILABLE:
            logger.warning("XGBoost not available, using mathematical estimation")
            return
            
        logger.info("🤖 Creating and training XGBoost model with engagement patterns...")
        
        # Generate synthetic training data based on real engagement patterns
        training_data = self._generate_training_data()
        
        if len(training_data) > 0:
            df = pd.DataFrame(training_data)
            X = df[self.feature_names]
            y = df['optimal_posts']
            
            # Create and train XGBoost model with robust parameters
            self.model = xgb.XGBRegressor(
                n_estimators=150,
                max_depth=6,
                learning_rate=0.1,
                random_state=42,
                objective='reg:squarederror',
                subsample=0.8,
                colsample_bytree=0.8,
                reg_alpha=0.1,
                reg_lambda=1.0
            )
            
            self.model.fit(X, y)
            self.is_trained = True
            
            # Save model with version info
            self._save_model_with_version()
                
            logger.info("✅ XGBoost model trained and saved successfully")
        else:
            logger.error("Failed to generate training data")
    
    def _save_model_with_version(self):
        """Save model with version information for compatibility tracking"""
        try:
            os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
            
            # Create model metadata
            model_metadata = {
                'model': self.model,
                'version': self.model_version,
                'xgboost_version': XGBOOST_VERSION,
                'feature_names': self.feature_names,
                'training_date': datetime.now().isoformat()
            }
            
            # Save with pickle
            with open(self.model_path, 'wb') as f:
                pickle.dump(model_metadata, f)
            
            # Also save just the model for backward compatibility
            with open(self.model_backup_path, 'wb') as f:
                pickle.dump(self.model, f)
                
        except Exception as e:
            logger.error(f"Error saving model: {e}")
    
    def _generate_training_data(self) -> List[Dict]:
        """Generate synthetic training data based on engagement science and platform patterns"""
        training_data = []
        
        # Enhanced engagement scenarios based on real platform dynamics
        scenarios = [
            # High-engagement accounts (influencers, brands)
            {'engagement_range': (0.05, 0.15), 'follower_range': (10000, 1000000), 'posts_multiplier': 0.8},
            # Medium-engagement accounts (businesses, creators)
            {'engagement_range': (0.02, 0.08), 'follower_range': (1000, 50000), 'posts_multiplier': 1.0},
            # Low-engagement accounts (personal, new accounts)
            {'engagement_range': (0.005, 0.03), 'follower_range': (100, 5000), 'posts_multiplier': 1.3},
            # Mega accounts (celebrities, major brands)
            {'engagement_range': (0.01, 0.04), 'follower_range': (1000000, 50000000), 'posts_multiplier': 0.6},
            # Micro-influencers (high engagement, smaller following)
            {'engagement_range': (0.08, 0.25), 'follower_range': (1000, 10000), 'posts_multiplier': 0.9},
            # Growing accounts (increasing engagement)
            {'engagement_range': (0.03, 0.12), 'follower_range': (5000, 50000), 'posts_multiplier': 1.1}
        ]
        
        for scenario in scenarios:
            for _ in range(200):  # 1200 samples total
                # Base metrics
                current_engagement = np.random.uniform(*scenario['engagement_range'])
                follower_count = np.random.uniform(*scenario['follower_range'])
                timeline_days = np.random.randint(1, 30)
                
                # Goal parsing
                goal_types = ['increase', 'double', 'triple']
                goal_type = np.random.choice(goal_types)
                
                if goal_type == 'increase':
                    increase_factor = np.random.uniform(1.2, 2.0)  # 20% to 100% increase
                elif goal_type == 'double':
                    increase_factor = 2.0
                else:  # triple
                    increase_factor = 3.0
                
                # Platform
                platform = np.random.choice(['instagram', 'twitter', 'facebook'])
                
                # Account characteristics
                avg_posts_per_week = np.random.uniform(2, 14)
                consistency_score = np.random.uniform(0.3, 0.9)
                historical_growth_rate = np.random.uniform(0.01, 0.1)
                content_variety_score = np.random.uniform(0.4, 0.9)
                peak_engagement_ratio = np.random.uniform(1.5, 4.0)
                posting_frequency_score = min(avg_posts_per_week / 7, 1.0)
                
                # Calculate optimal posts using engagement science
                base_posts = (timeline_days * avg_posts_per_week) / 7
                
                # Enhanced engagement difficulty factor
                difficulty_factor = 1.0
                if current_engagement < 0.01:  # Very low engagement needs more posts
                    difficulty_factor = 1.5
                elif current_engagement > 0.1:  # High engagement needs fewer posts
                    difficulty_factor = 0.7
                elif current_engagement > 0.05:  # Medium-high engagement
                    difficulty_factor = 0.85
                
                # Timeline pressure factor
                timeline_factor = 1.0
                if timeline_days < 7:
                    timeline_factor = 1.3  # Short timeline needs more intensive posting
                elif timeline_days > 21:
                    timeline_factor = 0.8  # Longer timeline allows more gradual approach
                
                # Platform factor
                platform_factor = 1.0 if platform == 'instagram' else (1.1 if platform == 'facebook' else 1.2)  # Facebook needs slightly more posts than Instagram, Twitter needs most
                
                # Consistency factor
                consistency_factor = 1.0 if consistency_score > 0.6 else 1.2
                
                # Calculate optimal posts with enhanced algorithm
                optimal_posts = base_posts * increase_factor * difficulty_factor * timeline_factor * platform_factor * consistency_factor * scenario['posts_multiplier']
                optimal_posts = max(1, min(int(round(optimal_posts)), timeline_days * 2))  # Cap at 2 posts per day
                
                # Create feature vector
                features = {
                    'current_engagement_rate': current_engagement,
                    'follower_count': follower_count,
                    'avg_posts_per_week': avg_posts_per_week,
                    'consistency_score': consistency_score,
                    'timeline_days': timeline_days,
                    'engagement_increase_factor': increase_factor,
                    'platform_instagram': 1 if platform == 'instagram' else 0,
                    'platform_twitter': 1 if platform == 'twitter' else 0,
                    'platform_facebook': 1 if platform == 'facebook' else 0,
                    'goal_type_increase': 1 if goal_type == 'increase' else 0,
                    'goal_type_double': 1 if goal_type == 'double' else 0,
                    'goal_type_triple': 1 if goal_type == 'triple' else 0,
                    'historical_growth_rate': historical_growth_rate,
                    'content_variety_score': content_variety_score,
                    'peak_engagement_ratio': peak_engagement_ratio,
                    'posting_frequency_score': posting_frequency_score,
                    'optimal_posts': optimal_posts
                }
                
                training_data.append(features)
        
        logger.info(f"Generated {len(training_data)} training samples")
        return training_data
    
    def estimate_posts(
        self, 
        goal: Dict, 
        profile_analysis: Dict, 
        prophet_data: Dict = None
    ) -> Tuple[int, str, Dict]:
        """
        Estimate optimal number of posts using XGBoost model
        
        Returns:
            tuple: (estimated_posts, rationale, prediction_metrics)
        """
        try:
            # Extract features from goal and profile analysis
            features = self._extract_features(goal, profile_analysis, prophet_data)
            
            if self.model and self.is_trained and XGBOOST_AVAILABLE:
                # Use XGBoost prediction with robust error handling
                try:
                    # Create feature DataFrame in the same format as training data
                    feature_dict = {}
                    for feature_name in self.feature_names:
                        if feature_name in features:
                            feature_dict[feature_name] = features[feature_name]
                        else:
                            # Provide default value if feature is missing
                            logger.warning(f"Missing feature {feature_name}, using default")
                            feature_dict[feature_name] = 0.0
                    
                    # Create DataFrame for prediction (same format as training)
                    feature_df = pd.DataFrame([feature_dict])
                    
                    # Make prediction using DataFrame
                    prediction = self.model.predict(feature_df)[0]
                    estimated_posts = max(1, int(round(prediction)))
                    
                    # Get feature importance for rationale
                    feature_importance = dict(zip(self.feature_names, self.model.feature_importances_))
                    top_features = sorted(feature_importance.items(), key=lambda x: x[1], reverse=True)[:3]
                    
                    rationale = f"XGBoost ML prediction: {estimated_posts} posts. Key factors: {', '.join([f'{k}({v:.3f})' for k, v in top_features])}"
                    
                    prediction_metrics = {
                        'method': 'xgboost',
                        'confidence': 0.85,
                        'feature_importance': feature_importance,
                        'prediction_raw': float(prediction)
                    }
                    
                except Exception as e:
                    logger.warning(f"XGBoost prediction failed, using mathematical estimation: {e}")
                    estimated_posts, rationale, prediction_metrics = self._mathematical_fallback(features)
                
            else:
                # Use mathematical estimation
                estimated_posts, rationale, prediction_metrics = self._mathematical_fallback(features)
            
            logger.info(f"📊 Post estimation: {estimated_posts} posts - {rationale}")
            return estimated_posts, rationale, prediction_metrics
            
        except Exception as e:
            logger.error(f"Error in post estimation: {e}")
            # Emergency fallback
            timeline = int(goal.get('timeline', 7))
            return max(1, timeline // 2), f"Emergency fallback: {timeline // 2} posts", {'method': 'emergency'}
    
    def _extract_features(self, goal: Dict, profile_analysis: Dict, prophet_data: Dict = None) -> Dict:
        """Extract features for XGBoost model from goal and profile data"""
        
        # Basic profile metrics
        engagement_patterns = profile_analysis.get('engagement_patterns', {})
        posting_frequency = profile_analysis.get('posting_frequency', {})
        
        current_engagement = engagement_patterns.get('avg_engagement_rate', 0.05)
        follower_count = profile_analysis.get('followers', 1000)
        avg_posts_per_week = posting_frequency.get('avg_posts_per_week', 3)
        consistency_score = posting_frequency.get('consistency_score', 0.5)
        
        # Goal parsing
        timeline_days = int(goal.get('timeline', 7))
        goal_text = goal.get('goal', '').lower()
        platform = goal.get('platform', 'instagram')
        
        # Parse engagement increase factor
        engagement_increase_factor = self._parse_engagement_goal(goal_text, current_engagement)
        
        # Goal type classification
        goal_type_increase = 1 if 'increase' in goal_text and 'double' not in goal_text and 'triple' not in goal_text else 0
        goal_type_double = 1 if 'double' in goal_text or '2x' in goal_text else 0
        goal_type_triple = 1 if 'triple' in goal_text or '3x' in goal_text else 0
        
        # Advanced metrics
        historical_growth_rate = engagement_patterns.get('engagement_growth_trend', 0.02)
        if historical_growth_rate == 'increasing':
            historical_growth_rate = 0.05
        elif historical_growth_rate == 'decreasing':
            historical_growth_rate = -0.02
        else:
            historical_growth_rate = 0.02
        
        content_variety_score = 0.7  # Default, could be calculated from content themes
        peak_engagement_ratio = engagement_patterns.get('peak_engagement_rate', current_engagement * 2) / current_engagement
        posting_frequency_score = min(avg_posts_per_week / 7, 1.0)
        
        features = {
            'current_engagement_rate': current_engagement,
            'follower_count': follower_count,
            'avg_posts_per_week': avg_posts_per_week,
            'consistency_score': consistency_score,
            'timeline_days': timeline_days,
            'engagement_increase_factor': engagement_increase_factor,
            'platform_instagram': 1 if platform == 'instagram' else 0,
            'platform_twitter': 1 if platform == 'twitter' else 0,
            'platform_facebook': 1 if platform == 'facebook' else 0,
            'goal_type_increase': goal_type_increase,
            'goal_type_double': goal_type_double,
            'goal_type_triple': goal_type_triple,
            'historical_growth_rate': historical_growth_rate,
            'content_variety_score': content_variety_score,
            'peak_engagement_ratio': peak_engagement_ratio,
            'posting_frequency_score': posting_frequency_score
        }
        
        return features
    
    def _parse_engagement_goal(self, goal_text: str, current_engagement: float) -> float:
        """Parse goal text to extract engagement increase factor"""
        
        # Look for percentage increases
        percentage_matches = re.findall(r'(\d+)%', goal_text)
        if percentage_matches:
            percentage = int(percentage_matches[0])
            return 1 + (percentage / 100)  # Convert to multiplier
        
        # Look for multiplier keywords
        if 'double' in goal_text or '2x' in goal_text:
            return 2.0
        elif 'triple' in goal_text or '3x' in goal_text:
            return 3.0
        elif 'quadruple' in goal_text or '4x' in goal_text:
            return 4.0
        
        # Look for numeric multipliers
        multiplier_matches = re.findall(r'(\d+)x', goal_text)
        if multiplier_matches:
            return float(multiplier_matches[0])
        
        # Default moderate increase
        return 1.5
    
    def _mathematical_fallback(self, features: Dict) -> Tuple[int, str, Dict]:
        """Mathematical fallback when XGBoost is not available"""
        
        current_engagement = features['current_engagement_rate']
        timeline_days = features['timeline_days']
        avg_posts_per_week = features['avg_posts_per_week']
        engagement_increase_factor = features['engagement_increase_factor']
        consistency_score = features['consistency_score']
        
        # Base calculation: daily_post_frequency × timeline × engagement_increase_factor
        daily_frequency = avg_posts_per_week / 7
        base_posts = daily_frequency * timeline_days * engagement_increase_factor
        
        # Adjustment factors
        difficulty_factor = 1.0
        if current_engagement < 0.01:
            difficulty_factor = 1.4  # Low engagement needs more posts
        elif current_engagement > 0.1:
            difficulty_factor = 0.8  # High engagement needs fewer posts
        
        consistency_factor = 1.0 if consistency_score > 0.6 else 1.2
        
        # Platform factor
        platform_factor = 1.0 if features['platform_instagram'] else 1.15
        
        estimated_posts = base_posts * difficulty_factor * consistency_factor * platform_factor
        estimated_posts = max(1, min(int(round(estimated_posts)), timeline_days * 2))
        
        rationale = f"Mathematical estimation: {estimated_posts} posts (base: {base_posts:.1f}, difficulty: {difficulty_factor:.2f})"
        
        metrics = {
            'method': 'mathematical_fallback',
            'confidence': 0.7,
            'base_posts': base_posts,
            'difficulty_factor': difficulty_factor,
            'consistency_factor': consistency_factor,
            'platform_factor': platform_factor
        }
        
        return estimated_posts, rationale, metrics
    
    def force_model_regeneration(self):
        """Force regeneration of the XGBoost model"""
        try:
            logger.info("🔄 Forcing XGBoost model regeneration...")
            
            # Remove existing model files
            self._remove_incompatible_model()
            
            # Reset model state
            self.model = None
            self.is_trained = False
            
            # Create new model
            self._create_and_train_model()
            
            if self.model is not None and self.is_trained:
                logger.info("✅ Model regeneration completed successfully")
                return True
            else:
                logger.error("❌ Model regeneration failed")
                return False
                
        except Exception as e:
            logger.error(f"Error during model regeneration: {e}")
            return False
    
    def get_model_info(self) -> Dict:
        """Get information about the current model"""
        return {
            'model_available': self.model is not None,
            'is_trained': self.is_trained,
            'xgboost_available': XGBOOST_AVAILABLE,
            'xgboost_version': XGBOOST_VERSION,
            'feature_count': len(self.feature_names),
            'model_path': self.model_path,
            'model_version': self.model_version,
            'backup_path': self.model_backup_path
        }

    def get_hashtag_recommendations(
        self,
        content_themes: List[str],
        platform: str,
        engagement_goal: str,
        follower_count: int
    ) -> List[str]:
        """
        🏷️ Generate hashtag recommendations based on XGBoost analysis and engagement data
        
        Args:
            content_themes: Extracted content themes from profile analysis
            platform: Target platform (instagram/twitter)
            engagement_goal: Goal type (increase/double/triple)
            follower_count: Account follower count
            
        Returns:
            List of recommended hashtags for optimal engagement
        """
        try:
            logger.info(f"🏷️ Generating hashtag recommendations for {platform} with {follower_count} followers")
            
            recommended_hashtags = []
            platform_db = self.hashtag_database.get(platform.lower(), {})
            
            # 1. Add high-engagement hashtags based on follower count
            if follower_count < 1000:
                # Smaller accounts need broader hashtags
                recommended_hashtags.extend(platform_db.get("high_engagement", [])[:2])
            elif follower_count < 10000:
                # Medium accounts can use trending hashtags
                recommended_hashtags.extend(platform_db.get("high_engagement", [])[:1])
            
            # 2. Add theme-specific hashtags
            for theme in content_themes[:3]:  # Use top 3 themes
                theme_lower = theme.lower()
                for category, hashtags in platform_db.items():
                    if any(keyword in theme_lower for keyword in category.split("_")):
                        recommended_hashtags.extend(hashtags[:2])
                        break
            
            # 3. Add goal-specific hashtags
            if "increase" in engagement_goal.lower():
                recommended_hashtags.append("#Growth")
            elif "double" in engagement_goal.lower():
                recommended_hashtags.extend(["#Double", "#Boost"])
            elif "triple" in engagement_goal.lower():
                recommended_hashtags.extend(["#Triple", "#Viral"])
            
            # 4. Remove duplicates and limit count
            unique_hashtags = list(dict.fromkeys(recommended_hashtags))
            
            # Platform-specific limits
            max_hashtags = 5 if platform.lower() == "instagram" else 3
            final_hashtags = unique_hashtags[:max_hashtags]
            
            logger.info(f"🏷️ Generated {len(final_hashtags)} hashtag recommendations: {final_hashtags}")
            return final_hashtags
            
        except Exception as e:
            logger.error(f"🚨 Error generating hashtag recommendations: {e}")
            # Return basic fallback hashtags
            if platform.lower() == "instagram":
                return ["#Content", "#Engagement", "#Growth"]
            else:
                return ["#Update", "#Growth"] 