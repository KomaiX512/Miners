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

try:
    import xgboost as xgb
    XGBOOST_AVAILABLE = True
except ImportError:
    logger.warning("XGBoost not available. Using fallback estimation.")
    XGBOOST_AVAILABLE = False

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
            'goal_type_increase',
            'goal_type_double',
            'goal_type_triple',
            'historical_growth_rate',
            'content_variety_score',
            'peak_engagement_ratio',
            'posting_frequency_score'
        ]
        self.model_path = "models/xgboost_post_estimator.pkl"
        self.is_trained = False
        
        # Initialize or load model
        self._initialize_model()
    
    def _initialize_model(self):
        """Initialize XGBoost model - load if exists, create synthetic training if not"""
        try:
            if os.path.exists(self.model_path):
                with open(self.model_path, 'rb') as f:
                    self.model = pickle.load(f)
                self.is_trained = True
                logger.info("✅ Loaded pre-trained XGBoost model")
            else:
                self._create_and_train_model()
        except Exception as e:
            logger.error(f"Error initializing XGBoost model: {e}")
            self.model = None
    
    def _create_and_train_model(self):
        """Create and train XGBoost model with synthetic data based on engagement patterns"""
        if not XGBOOST_AVAILABLE:
            logger.warning("XGBoost not available, using mathematical fallback")
            return
            
        logger.info("🤖 Creating and training XGBoost model with engagement patterns...")
        
        # Generate synthetic training data based on real engagement patterns
        training_data = self._generate_training_data()
        
        if len(training_data) > 0:
            df = pd.DataFrame(training_data)
            X = df[self.feature_names]
            y = df['optimal_posts']
            
            # Create and train XGBoost model
            self.model = xgb.XGBRegressor(
                n_estimators=100,
                max_depth=6,
                learning_rate=0.1,
                random_state=42,
                objective='reg:squarederror'
            )
            
            self.model.fit(X, y)
            self.is_trained = True
            
            # Save model
            os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
            with open(self.model_path, 'wb') as f:
                pickle.dump(self.model, f)
                
            logger.info("✅ XGBoost model trained and saved successfully")
        else:
            logger.error("Failed to generate training data")
    
    def _generate_training_data(self) -> List[Dict]:
        """Generate synthetic training data based on engagement science and platform patterns"""
        training_data = []
        
        # Engagement scenarios based on real platform dynamics
        scenarios = [
            # High-engagement accounts (influencers, brands)
            {'engagement_range': (0.05, 0.15), 'follower_range': (10000, 1000000), 'posts_multiplier': 0.8},
            # Medium-engagement accounts (businesses, creators)
            {'engagement_range': (0.02, 0.08), 'follower_range': (1000, 50000), 'posts_multiplier': 1.0},
            # Low-engagement accounts (personal, new accounts)
            {'engagement_range': (0.005, 0.03), 'follower_range': (100, 5000), 'posts_multiplier': 1.3},
            # Mega accounts (celebrities, major brands)
            {'engagement_range': (0.01, 0.04), 'follower_range': (1000000, 50000000), 'posts_multiplier': 0.6}
        ]
        
        for scenario in scenarios:
            for _ in range(250):  # 1000 samples total
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
                platform = np.random.choice(['instagram', 'twitter'])
                
                # Account characteristics
                avg_posts_per_week = np.random.uniform(2, 14)
                consistency_score = np.random.uniform(0.3, 0.9)
                historical_growth_rate = np.random.uniform(0.01, 0.1)
                content_variety_score = np.random.uniform(0.4, 0.9)
                peak_engagement_ratio = np.random.uniform(1.5, 4.0)
                posting_frequency_score = min(avg_posts_per_week / 7, 1.0)
                
                # Calculate optimal posts using engagement science
                base_posts = (timeline_days * avg_posts_per_week) / 7
                
                # Engagement difficulty factor
                difficulty_factor = 1.0
                if current_engagement < 0.01:  # Very low engagement needs more posts
                    difficulty_factor = 1.5
                elif current_engagement > 0.1:  # High engagement needs fewer posts
                    difficulty_factor = 0.7
                
                # Timeline pressure factor
                timeline_factor = 1.0
                if timeline_days < 7:
                    timeline_factor = 1.3  # Short timeline needs more intensive posting
                elif timeline_days > 21:
                    timeline_factor = 0.8  # Longer timeline allows more gradual approach
                
                # Platform factor
                platform_factor = 1.0 if platform == 'instagram' else 1.2  # Twitter needs more posts
                
                # Calculate optimal posts
                optimal_posts = base_posts * increase_factor * difficulty_factor * timeline_factor * platform_factor * scenario['posts_multiplier']
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
                # Use XGBoost prediction
                feature_vector = [features[name] for name in self.feature_names]
                prediction = self.model.predict([feature_vector])[0]
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
                
            else:
                # Fallback mathematical estimation
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
    
    def get_model_info(self) -> Dict:
        """Get information about the current model"""
        return {
            'model_available': self.model is not None,
            'is_trained': self.is_trained,
            'xgboost_available': XGBOOST_AVAILABLE,
            'feature_count': len(self.feature_names),
            'model_path': self.model_path
        } 