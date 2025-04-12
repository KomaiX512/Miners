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
    
    def __init__(self, config=TIME_SERIES_CONFIG):
        """Initialize with configuration."""
        self.config = config
        self.model = None
        self.forecast = None
        self.primary_username = None  # To track primary username
        
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
            elif isinstance(data, dict) and 'engagement_history' in data:
                engagement_history = data['engagement_history']
                df = pd.DataFrame(engagement_history)
            elif isinstance(data, list):
                df = pd.DataFrame(data)
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
                logger.error(f"Missing required columns: {timestamp_col} or {value_col}")
                return None
            
            # Add username column if missing (assume primary if not specified)
            if 'username' not in df.columns:
                df['username'] = primary_username or 'unknown'
            
            # Convert timestamp to pandas datetime
            df['ds'] = pd.to_datetime(df[timestamp_col], errors='coerce', utc=True).dt.tz_localize(None)
            
            # Convert value to numeric
            df['y'] = pd.to_numeric(df[value_col], errors='coerce')
            
            # Drop invalid rows
            df = df.dropna(subset=['ds', 'y'])
            
            # Ensure minimum data points
            if len(df) < 2:
                logger.warning(f"Insufficient data points ({len(df)})")
                if len(df) == 1:
                    first_point = df.iloc[0].copy()
                    new_point = first_point.copy()
                    new_point['ds'] = new_point['ds'] - pd.Timedelta(days=1)
                    new_point['y'] = max(0, new_point['y'] * 0.9)
                    df = pd.concat([pd.DataFrame([new_point]), df])
                    logger.info("Added synthetic point for analysis")
                else:
                    return None
            
            df = df[['ds', 'y', 'username']].sort_values('ds')
            logger.info(f"Prepared {len(df)} rows with {df['username'].nunique()} unique usernames")
            return df
        except Exception as e:
            logger.error(f"Error preparing data: {str(e)}")
            return None
    
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


if __name__ == "__main__":
    success = test_time_series_analysis_multi_user()
    print(f"Multi-user time series analysis test {'successful' if success else 'failed'}")