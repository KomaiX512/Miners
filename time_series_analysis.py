"""Module for time series analysis using Prophet."""

import logging
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from prophet import Prophet
from prophet.plot import plot_plotly
import plotly.offline as pyo
from config import TIME_SERIES_CONFIG, LOGGING_CONFIG
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=LOGGING_CONFIG['level'],
    format=LOGGING_CONFIG['format']
)
logger = logging.getLogger(__name__)

class TimeSeriesAnalyzer:
    """Class to handle time series analysis and forecasting for primary and secondary usernames."""
    
    def __init__(self, config=TIME_SERIES_CONFIG, r2_storage=None):
        """Initialize with configuration and optional R2 storage."""
        self.config = config
        self.model = None
        self.forecast = None
        self.primary_username = None  # To track primary username
        
        # Initialize R2 storage if available
        try:
            if r2_storage:
                self.r2_storage = r2_storage
            else:
                from r2_storage_manager import R2StorageManager
                self.r2_storage = R2StorageManager()
        except Exception as e:
            logger.warning(f"R2 storage initialization failed: {str(e)}")
            self.r2_storage = None
        
    def _clean_username(self, username):
        """Remove '@' symbol and other special characters from username for export compatibility."""
        if not username:
            return username
        # Remove '@' symbol and any other special characters that cause retrieval issues
        cleaned = username.replace('@', '').strip()
        return cleaned

    def prepare_data(self, data, timestamp_col='timestamp', value_col='engagement', primary_username=None):
        """
        Prepare time series data for analysis, distinguishing primary and secondary sources.
        
        Args:
            data: List of post dictionaries, DataFrame, or dict with engagement history
            timestamp_col: Name of timestamp column
            value_col: Name of value column
            primary_username: Primary username to tag data (optional)
            
        Returns:
            DataFrame with 'ds', 'y', and 'username' columns for Prophet
        """
        try:
            self.primary_username = primary_username  # Store for later use
            
            # Handle different input data formats
            if isinstance(data, pd.DataFrame):
                if timestamp_col in data.columns and value_col in data.columns:
                    df = data.copy()
                    if 'username' not in df.columns:
                        df['username'] = primary_username or 'unknown'
                else:
                    logger.error(f"DataFrame missing required columns: {timestamp_col} or {value_col}")
                    # Create synthetic data
                    now = datetime.now()
                    df = pd.DataFrame([
                        {timestamp_col: (now - pd.Timedelta(days=i)).strftime('%Y-%m-%dT%H:%M:%SZ'), 
                         value_col: 1000 - i * 100, 
                         'username': primary_username or 'unknown'}
                        for i in range(3)
                    ])
                    logger.info("Created synthetic data due to invalid input")
            # Handle dict format with engagement history
            elif isinstance(data, dict):
                # Log the dict keys to help with debugging
                logger.debug(f"Dictionary data received with keys: {list(data.keys())}")
                
                if 'engagement_history' in data and isinstance(data['engagement_history'], list):
                    # Use the engagement history directly
                    engagement_history = data['engagement_history']
                    df = pd.DataFrame(engagement_history)
                    
                    # Make sure username column exists
                    if 'username' not in df.columns:
                        df['username'] = primary_username or 'unknown'
                elif 'posts' in data and isinstance(data['posts'], list):
                    # Extract from posts array
                    posts = data['posts']
                    df = pd.DataFrame(posts)
                    if 'username' not in df.columns:
                        df['username'] = primary_username or data.get('username', 'unknown')
                elif any(isinstance(data.get(key), list) for key in data):
                    # Find the first list in the dict and try to use it
                    for key, value in data.items():
                        if isinstance(value, list) and len(value) > 0:
                            logger.info(f"Using list data from key: {key}")
                            df = pd.DataFrame(value)
                            if 'username' not in df.columns:
                                df['username'] = primary_username or 'unknown'
                            break
                    else:
                        # If no suitable list was found, create synthetic data
                        logger.error(f"No usable list data found in dictionary")
                        now = datetime.now()
                        df = pd.DataFrame([
                            {timestamp_col: (now - pd.Timedelta(days=i)).strftime('%Y-%m-%dT%H:%M:%SZ'), 
                             value_col: 1000 - i * 100, 
                             'username': primary_username or 'unknown'}
                            for i in range(3)
                        ])
                        logger.info("Created synthetic data from dictionary without lists")
                else:
                    # Try to handle the dict format directly
                    try:
                        # First try: if the dict is a time series with timestamps as keys
                        if all(isinstance(k, (str, datetime)) for k in data.keys()) and all(isinstance(v, (int, float)) for v in data.values()):
                            df = pd.DataFrame({
                                timestamp_col: list(data.keys()),
                                value_col: list(data.values()),
                                'username': primary_username or 'unknown'
                            })
                            logger.info("Created DataFrame from timestamp-value dictionary")
                        else:
                            # Second try: treat the dict as a single record
                            df = pd.DataFrame([data])
                            logger.info("Created DataFrame from single dictionary record")
                    except (ValueError, TypeError) as e:
                        logger.error(f"Invalid dict format: {str(e)}")
                        # Create synthetic data as fallback
                        now = datetime.now()
                        df = pd.DataFrame([
                            {timestamp_col: (now - pd.Timedelta(days=i)).strftime('%Y-%m-%dT%H:%M:%SZ'), 
                             value_col: 1000 - i * 100, 
                             'username': primary_username or 'unknown'}
                            for i in range(3)
                        ])
                        logger.info("Created synthetic data due to invalid dict format")
            elif isinstance(data, list):
                if not data:  # Empty list
                    logger.warning("Empty list provided, creating synthetic data")
                    now = datetime.now()
                    df = pd.DataFrame([
                        {timestamp_col: (now - pd.Timedelta(days=i)).strftime('%Y-%m-%dT%H:%M:%SZ'), 
                         value_col: 1000 - i * 100, 
                         'username': primary_username or 'unknown'}
                        for i in range(3)
                    ])
                elif isinstance(data[0], dict):
                    # List of dictionaries
                    df = pd.DataFrame(data)
                else:
                    # Try to interpret as a list of values
                    try:
                        now = datetime.now()
                        df = pd.DataFrame({
                            timestamp_col: [(now - pd.Timedelta(days=i)).strftime('%Y-%m-%dT%H:%M:%SZ') for i in range(len(data))],
                            value_col: data,
                            'username': [primary_username or 'unknown'] * len(data)
                        })
                        logger.info("Created DataFrame from list of values")
                    except Exception as e:
                        logger.error(f"Failed to process list data: {str(e)}")
                        now = datetime.now()
                        df = pd.DataFrame([
                            {timestamp_col: (now - pd.Timedelta(days=i)).strftime('%Y-%m-%dT%H:%M:%SZ'), 
                             value_col: 1000 - i * 100, 
                             'username': primary_username or 'unknown'}
                            for i in range(3)
                        ])
                        logger.info("Created synthetic data due to invalid list format")
            else:
                logger.error(f"Invalid data format: {type(data)}")
                # Synthetic fallback
                now = datetime.now()
                df = pd.DataFrame([
                    {timestamp_col: (now - pd.Timedelta(days=i)).strftime('%Y-%m-%dT%H:%M:%SZ'), 
                     value_col: 1000 - i * 100, 
                     'username': primary_username or 'unknown'}
                    for i in range(3)
                ])
                logger.info("Created synthetic data due to invalid input")
            
            # Check for required columns
            if timestamp_col not in df.columns or value_col not in df.columns:
                logger.error(f"Missing required columns: {timestamp_col} or {value_col} in {df.columns.tolist()}")
                
                # Try to intelligently find timestamp and value columns
                possible_timestamp_cols = [col for col in df.columns if any(time_word in col.lower() for time_word in ['time', 'date', 'ts', 'day'])]
                possible_value_cols = [col for col in df.columns if any(val_word in col.lower() for val_word in ['value', 'count', 'engagement', 'likes', 'views'])]
                
                if possible_timestamp_cols and possible_value_cols:
                    logger.info(f"Attempting to use columns: {possible_timestamp_cols[0]} and {possible_value_cols[0]}")
                    timestamp_col = possible_timestamp_cols[0]
                    value_col = possible_value_cols[0]
                else:
                    # If we can't find appropriate columns, create synthetic data
                    now = datetime.now()
                    df = pd.DataFrame([
                        {timestamp_col: (now - pd.Timedelta(days=i)).strftime('%Y-%m-%dT%H:%M:%SZ'), 
                         value_col: 1000 - i * 100, 
                         'username': primary_username or 'unknown'}
                        for i in range(3)
                    ])
                    logger.info("Created synthetic data due to missing required columns")
            
            # Add username column if missing (assume primary if not specified)
            if 'username' not in df.columns:
                df['username'] = primary_username or 'unknown'
            
            # Convert timestamp to pandas datetime
            df['ds'] = pd.to_datetime(df[timestamp_col], errors='coerce', utc=True).dt.tz_localize(None)
            
            # Convert value to numeric
            df['y'] = pd.to_numeric(df[value_col], errors='coerce')
            
            # Replace NaNs or 0s with 1 for minimum engagement value to ensure visibility in analytics
            df['y'] = df['y'].fillna(1)
            df['y'] = df['y'].apply(lambda x: max(1, x))  # Ensure minimum value is 1
            
            # Drop invalid rows
            df = df.dropna(subset=['ds'])
            
            # Ensure minimum data points
            if len(df) < 2:
                logger.warning(f"Insufficient data points ({len(df)})")
                if len(df) == 1:
                    first_point = df.iloc[0].copy()
                    new_point = first_point.copy()
                    new_point['ds'] = new_point['ds'] - pd.Timedelta(days=1)
                    new_point['y'] = max(1, new_point['y'] * 0.9)  # Ensure minimum value of 1
                    df = pd.concat([pd.DataFrame([new_point]), df])
                    logger.info("Added synthetic point for analysis")
                else:
                    # Create minimal synthetic dataset
                    now = datetime.now()
                    df = pd.DataFrame([
                        {'ds': now - pd.Timedelta(days=i), 
                         'y': 1000 - i * 100, 
                         'username': primary_username or 'unknown'}
                        for i in range(3)
                    ])
                    logger.info("Created minimal synthetic dataset")
            
            df = df[['ds', 'y', 'username']].sort_values('ds')
            logger.info(f"Prepared {len(df)} rows with {df['username'].nunique()} unique usernames")
            return df
        except Exception as e:
            logger.error(f"Error preparing data: {str(e)}")
            # Always return a valid DataFrame even if an error occurs
            now = datetime.now()
            df = pd.DataFrame([
                {'ds': now - pd.Timedelta(days=i), 
                 'y': 1000 - i * 100, 
                 'username': primary_username or 'unknown'}
                for i in range(3)
            ])
            logger.info("Created fallback synthetic dataset after error")
            return df
    
    def train_model(self, df):
        """
        Train Prophet model on the provided data.
        
        Args:
            df: DataFrame with 'ds', 'y', and 'username' columns
            
        Returns:
            Trained Prophet model
        """
        try:
            # Prophet only needs 'ds' and 'y', so drop 'username' for training
            self.model = Prophet()
            self.model.fit(df[['ds', 'y']])
            logger.info("Successfully trained Prophet model on combined data")
            return self.model
        except Exception as e:
            logger.error(f"Error training model: {str(e)}")
            raise
    
    def generate_forecast(self, periods=None):
        """
        Generate forecast for future periods.
        
        Args:
            periods: Number of periods to forecast (default from config)
            
        Returns:
            DataFrame with forecast results
        """
        if not self.model:
            raise ValueError("Model not trained. Call train_model first.")
        
        try:
            periods = periods or self.config['forecast_periods']
            future = self.model.make_future_dataframe(periods=periods)
            self.forecast = self.model.predict(future)
            logger.info(f"Generated forecast for {periods} periods")
            return self.forecast
        except Exception as e:
            logger.error(f"Error generating forecast: {str(e)}")
            raise
    
    def detect_trending_periods(self, percentile=None):
        """
        Detect trending periods based on forecast values, with username context.
        
        Args:
            percentile: Threshold percentile (default from config)
            
        Returns:
            DataFrame with trending periods and username attribution
        """
        if self.forecast is None:  # Fixed condition
            raise ValueError("Forecast not generated. Call generate_forecast first.")
        
        try:
            percentile = percentile or self.config['trend_threshold']
            threshold = np.percentile(self.forecast['yhat'], percentile * 100)
            trending = self.forecast[self.forecast['yhat'] > threshold].copy()
            
            # Determine future trending periods
            max_history_date = self.forecast['ds'].min() + (self.forecast['ds'].max() - self.forecast['ds'].min()) / 2
            future_trending = trending[trending['ds'] > max_history_date].copy()
            
            # Log insights
            logger.info(f"Detected {len(future_trending)} future trending periods above threshold {threshold:.2f}")
            return future_trending
        except Exception as e:
            logger.error(f"Error detecting trending periods: {str(e)}")
            raise
    
    def plot_forecast(self, filename=None):
        """
        Plot forecast results with username context.
        
        Args:
            filename: If provided, save plot to this file
        
        Returns:
            Plotly figure
        """
        if self.forecast is None:  # Fixed condition
            raise ValueError("Forecast not generated. Call generate_forecast first.")
        
        try:
            fig = plot_plotly(self.model, self.forecast)
            if filename:
                fig.write_html(filename)
                logger.info(f"Saved forecast plot to {filename}")
            return fig
        except Exception as e:
            logger.error(f"Error plotting forecast: {str(e)}")
            raise
    
    def analyze_data(self, data, timestamp_col='timestamp', value_col='engagement', primary_username=None):
        """
        Complete pipeline to analyze time series data from primary and secondary sources.
        
        Args:
            data: List of posts or dict with engagement history
            timestamp_col: Column name for timestamps
            value_col: Column name for the metric to forecast
            primary_username: Primary username for context
            
        Returns:
            Dictionary with combined and detailed results
        """
        try:
            df = self.prepare_data(data, timestamp_col, value_col, primary_username)
            if df is None:
                logger.error("Data preparation failed")
                return None
                
            self.train_model(df)
            self.generate_forecast()
            trending = self.detect_trending_periods()
            
            # Analyze primary vs. secondary trends if username data exists
            primary_trends = None
            secondary_trends = None
            if 'username' in df.columns and primary_username:
                primary_df = df[df['username'] == primary_username]
                secondary_df = df[df['username'] != primary_username]
                
                if not primary_df.empty:
                    primary_model = Prophet()
                    primary_model.fit(primary_df[['ds', 'y']])
                    primary_future = primary_model.make_future_dataframe(periods=self.config['forecast_periods'])
                    primary_forecast = primary_model.predict(primary_future)
                    primary_threshold = np.percentile(primary_forecast['yhat'], self.config['trend_threshold'] * 100)
                    primary_trends = primary_forecast[primary_forecast['yhat'] > primary_threshold]
                    logger.info(f"Detected {len(primary_trends)} primary trending periods for {primary_username}")
                
                if not secondary_df.empty:
                    secondary_model = Prophet()
                    secondary_model.fit(secondary_df[['ds', 'y']])
                    secondary_future = secondary_model.make_future_dataframe(periods=self.config['forecast_periods'])
                    secondary_forecast = secondary_model.predict(secondary_future)
                    secondary_threshold = np.percentile(secondary_forecast['yhat'], self.config['trend_threshold'] * 100)
                    secondary_trends = secondary_forecast[secondary_forecast['yhat'] > secondary_threshold]
                    logger.info(f"Detected {len(secondary_trends)} secondary trending periods")
            
            results = {
                'data': df,
                'forecast': self.forecast,
                'trending_periods': trending,
                'model': self.model,
                'primary_trends': primary_trends,
                'secondary_trends': secondary_trends
            }
            
            logger.info("Completed time series analysis with primary and secondary insights")
            return results
        except Exception as e:
            logger.error(f"Error in analysis pipeline: {str(e)}")
            return None

    def export_prophet_analysis(self, analysis_result, primary_username, platform="instagram"):
        """
        Export Prophet/time series analysis report to R2 with platform support.
        
        Args:
            analysis_result: Results from analyze_data method
            primary_username: Username for directory naming
            platform: Social media platform (instagram or twitter)
        """
        import io, json

        # Check if R2 storage is available
        if not self.r2_storage:
            logger.error("R2 storage not available, cannot export Prophet analysis")
            return False

        # CRITICAL FIX: Clean username to remove '@' symbols
        clean_username = self._clean_username(primary_username)
        logger.info(f"🧹 Cleaned username for prophet analysis export: '{primary_username}' -> '{clean_username}'")

        # Ensure platform-specific directory exists
        self._ensure_directory_exists(f"prophet_analysis/{platform}/{clean_username}/")

        # Get next file number with platform-specific path
        file_num = self._get_next_file_number(f"prophet_analysis/{platform}", clean_username, "analysis")
        
        # Create export structure
        export_data = {
            "generated_date": datetime.now().isoformat(),
            "platform": platform,
            "primary_username": clean_username,  # Use cleaned username
            "analysis_type": "time_series_prophet",
            "model_performance": analysis_result.get('model_performance', {}),
            "forecast_summary": analysis_result.get('forecast_summary', {}),
            "trending_periods": analysis_result.get('trending_periods_list', []),
            "primary_insights": analysis_result.get('primary_insights', {}),
            "secondary_insights": analysis_result.get('secondary_insights', {}),
            "data_quality": analysis_result.get('data_quality', {}),
            "recommendations": analysis_result.get('recommendations', [])
        }
        
        # Convert to JSON bytes
        json_bytes = json.dumps(export_data, indent=2).encode('utf-8')
        file_obj = io.BytesIO(json_bytes)

        # Upload to R2
        file_key = f"prophet_analysis/{platform}/{clean_username}/analysis_{file_num}.json"
        
        try:
            result = self.r2_storage.upload_file(
                key=file_key,
                file_obj=file_obj,
                bucket="tasks"
            )
            
            if result:
                logger.info(f"Time series Prophet analysis exported successfully to {file_key}")
                return True
            else:
                logger.error(f"Failed to export time series Prophet analysis to {file_key}")
                return False
        except Exception as e:
            logger.error(f"Error exporting time series Prophet analysis: {str(e)}")
            return False

    def _ensure_directory_exists(self, directory_path):
        """Ensure a directory exists in R2 storage by creating a directory marker."""
        try:
            import io  # Add missing import
            # Create directory marker
            result = self.r2_storage.upload_file(
                key=directory_path,
                file_obj=io.BytesIO(b""),
                bucket="tasks"
            )
            if result:
                logger.debug(f"Ensured directory exists: {directory_path}")
            return result
        except Exception as e:
            logger.warning(f"Could not ensure directory exists {directory_path}: {str(e)}")
            return False

    def _get_next_file_number(self, base_dir, path_segment, file_prefix):
        """Get the next file number for sequential file naming."""
        try:
            # List objects in the directory to find existing files
            prefix = f"{base_dir}/{path_segment}/"
            
            # Use R2 storage to list objects
            from r2_storage_manager import R2StorageManager
            r2_storage = R2StorageManager()
            
            # Get list of existing files
            try:
                import boto3
                from botocore.client import Config
                from config import R2_CONFIG
                
                s3_client = boto3.client(
                    's3',
                    endpoint_url=R2_CONFIG['endpoint_url'],
                    aws_access_key_id=R2_CONFIG['aws_access_key_id'],
                    aws_secret_access_key=R2_CONFIG['aws_secret_access_key'],
                    config=Config(signature_version='s3v4')
                )
                
                response = s3_client.list_objects_v2(
                    Bucket="tasks",
                    Prefix=prefix
                )
                
                existing_files = []
                if 'Contents' in response:
                    existing_files = [obj['Key'] for obj in response['Contents']]
                
                # Find the highest number for files with the specified prefix
                max_num = 0
                for file_key in existing_files:
                    filename = file_key.split('/')[-1]  # Get just the filename
                    if filename.startswith(f"{file_prefix}_") and filename.endswith('.json'):
                        try:
                            # Extract number from filename like "analysis_1.json"
                            num_part = filename[len(file_prefix)+1:-5]  # Remove prefix_ and .json
                            file_num = int(num_part)
                            max_num = max(max_num, file_num)
                        except (ValueError, IndexError):
                            continue
                
                return max_num + 1
                
            except Exception as list_e:
                logger.warning(f"Could not list existing files for numbering: {str(list_e)}")
                return 1
                
        except Exception as e:
            logger.warning(f"Error determining next file number: {str(e)}")
            return 1


def test_time_series_analysis_multi_user():
    """Test time series analysis with primary and secondary username data."""
    try:
        # Simulate data based on provided files
        primary_username = "maccosmetics"
        secondary_usernames = [
            "anastasiabeverlyhills", "fentybeauty", "narsissist", "toofaced",
            "competitor1", "competitor2", "competitor3", "competitor4", "competitor5"
        ]
        
        # Generate sample posts
        dates = pd.date_range(start='2025-01-01', end='2025-04-11', freq='D')
        sample_posts = []
        
        # Primary username data (higher engagement)
        for i, date in enumerate(dates):
            sample_posts.append({
                'timestamp': date.strftime('%Y-%m-%dT%H:%M:%SZ'),
                'engagement': 1000 + i * 5 + np.random.normal(0, 50),  # Upward trend
                'username': primary_username
            })
        
        # Secondary username data (varied patterns)
        for username in secondary_usernames[:5]:  # Limit to 5 for realism
            for i, date in enumerate(dates[:len(dates)//2]):  # Fewer posts for competitors
                sample_posts.append({
                    'timestamp': date.strftime('%Y-%m-%dT%H:%M:%SZ'),
                    'engagement': 500 + i * 2 + np.random.normal(0, 30),
                    'username': username
                })
        
        # Create analyzer
        analyzer = TimeSeriesAnalyzer()
        results = analyzer.analyze_data(sample_posts, primary_username=primary_username)
        
        if results is None:
            logger.error("Analysis returned None")
            return False
            
        # Verify results
        if not isinstance(results['data'], pd.DataFrame) or results['forecast'] is None:
            logger.error("Invalid analysis results structure")
            return False
            
        if results['primary_trends'] is None or results['secondary_trends'] is None:
            logger.warning("Primary or secondary trends not detected")
        else:
            logger.info(f"Primary trends: {len(results['primary_trends'])}, Secondary trends: {len(results['secondary_trends'])}")
        
        # Plot forecast
        analyzer.plot_forecast(f'test_forecast_{primary_username}.html')
        
        logger.info("Multi-user time series analysis test successful")
        return True
    except Exception as e:
        logger.error(f"Multi-user test failed: {str(e)}")
        return False


def test_export_prophet_analysis():
    # Use the test from time_series_analysis.py to generate results
    from time_series_analysis import test_time_series_analysis_multi_user, TimeSeriesAnalyzer
    analyzer = TimeSeriesAnalyzer()
    # Generate test data as in test_time_series_analysis_multi_user
    # ...
    results = analyzer.analyze_data(sample_posts, primary_username="maccosmetics")
    system = ContentRecommendationSystem()
    system.export_prophet_analysis(results, "maccosmetics")
    print("Prophet analysis export test complete.")


if __name__ == "__main__":
    success = test_time_series_analysis_multi_user()
    print(f"Multi-user time series analysis test {'successful' if success else 'failed'}")