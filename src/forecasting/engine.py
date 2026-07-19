"""
AI Demand Forecasting Engine
Uses Prophet and machine learning to predict product demand
"""

import logging
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestRegressor

try:
    from prophet import Prophet
except ImportError:
    Prophet = None

logger = logging.getLogger(__name__)

class DemandForecaster:
    """AI-powered demand forecasting using Prophet and machine learning"""
    
    def __init__(self, forecast_days: int = 30, model_type: str = 'prophet',
                 min_history_days: int = 60):
        """
        Initialize forecaster
        
        Args:
            forecast_days: Number of days to forecast
            model_type: Forecasting model type ('prophet' or 'random_forest')
            min_history_days: Minimum historical data required
        """
        self.forecast_days = forecast_days
        self.model_type = model_type
        self.min_history_days = min_history_days
        self.models = {}
        self.last_forecast_time = {}
        
        if model_type == 'prophet' and Prophet is None:
            logger.warning("Prophet not available, falling back to Random Forest")
            self.model_type = 'random_forest'
        
        logger.info(f"Forecaster initialized with model: {self.model_type}")
    
    def prepare_historical_data(self, sales_history: List[Dict]) -> pd.DataFrame:
        """
        Prepare historical sales data for forecasting
        
        Args:
            sales_history: List of sales records with date and quantity
            
        Returns:
            Prepared DataFrame
        """
        if not sales_history:
            logger.warning("No sales history provided")
            return pd.DataFrame()
        
        df = pd.DataFrame(sales_history)
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date')
        
        # Check minimum history requirement
        days_of_data = (df['date'].max() - df['date'].min()).days
        if days_of_data < self.min_history_days:
            logger.warning(f"Insufficient history: {days_of_data} days (need {self.min_history_days})")
        
        return df
    
    def forecast_prophet(self, sales_df: pd.DataFrame) -> Optional[pd.DataFrame]:
        """
        Generate forecast using Prophet model
        
        Args:
            sales_df: Historical sales data with 'date' and 'quantity' columns
            
        Returns:
            Forecast DataFrame
        """
        try:
            # Prepare data for Prophet
            df_prophet = sales_df.rename(columns={'date': 'ds', 'quantity': 'y'})
            df_prophet = df_prophet[['ds', 'y']].groupby('ds').sum().reset_index()
            
            # Initialize and fit model
            model = Prophet(
                yearly_seasonality=True,
                weekly_seasonality=True,
                daily_seasonality=False,
                interval_width=0.95
            )
            model.fit(df_prophet)
            
            # Generate forecast
            future = model.make_future_dataframe(periods=self.forecast_days)
            forecast = model.predict(future)
            
            # Extract forecast period only
            forecast_start = df_prophet['ds'].max()
            forecast_df = forecast[forecast['ds'] > forecast_start].copy()
            
            logger.info(f"Generated Prophet forecast for {len(forecast_df)} days")
            return forecast_df
            
        except Exception as e:
            logger.error(f"Prophet forecasting failed: {str(e)}")
            return None
    
    def forecast_random_forest(self, sales_df: pd.DataFrame) -> pd.DataFrame:
        """
        Generate forecast using Random Forest model
        
        Args:
            sales_df: Historical sales data
            
        Returns:
            Forecast DataFrame
        """
        try:
            # Engineer features
            sales_df = sales_df.copy()
            sales_df['date'] = pd.to_datetime(sales_df['date'])
            sales_df['day_of_week'] = sales_df['date'].dt.dayofweek
            sales_df['month'] = sales_df['date'].dt.month
            sales_df['day'] = sales_df['date'].dt.day
            
            # Create lag features
            sales_df['quantity_lag1'] = sales_df['quantity'].shift(1)
            sales_df['quantity_lag7'] = sales_df['quantity'].shift(7)
            sales_df['quantity_lag30'] = sales_df['quantity'].shift(30)
            
            sales_df = sales_df.dropna()
            
            # Prepare training data
            feature_cols = ['day_of_week', 'month', 'day', 'quantity_lag1', 
                          'quantity_lag7', 'quantity_lag30']
            X = sales_df[feature_cols]
            y = sales_df['quantity']
            
            # Train model
            model = RandomForestRegressor(n_estimators=100, random_state=42)
            model.fit(X, y)
            
            # Generate forecast
            forecast_data = []
            last_date = sales_df['date'].max()
            
            for i in range(1, self.forecast_days + 1):
                forecast_date = last_date + timedelta(days=i)
                
                features = {
                    'day_of_week': forecast_date.dayofweek,
                    'month': forecast_date.month,
                    'day': forecast_date.day,
                    'quantity_lag1': y.iloc[-1] if i == 1 else forecast_data[-1]['yhat'],
                    'quantity_lag7': y.iloc[-7] if i <= 7 else forecast_data[-7]['yhat'],
                    'quantity_lag30': y.iloc[-30] if i <= 30 else y.mean()
                }
                
                X_pred = pd.DataFrame([features])
                prediction = model.predict(X_pred)[0]
                
                forecast_data.append({
                    'ds': forecast_date,
                    'yhat': max(0, prediction),  # Ensure non-negative
                    'yhat_lower': max(0, prediction * 0.8),
                    'yhat_upper': prediction * 1.2
                })
            
            logger.info(f"Generated Random Forest forecast for {len(forecast_data)} days")
            return pd.DataFrame(forecast_data)
            
        except Exception as e:
            logger.error(f"Random Forest forecasting failed: {str(e)}")
            return pd.DataFrame()
    
    def predict_demand(self, product_id: str, sales_history: List[Dict]) -> Dict:
        """
        Predict demand for a product
        
        Args:
            product_id: Product ID
            sales_history: Historical sales data
            
        Returns:
            Forecast with statistics
        """
        logger.info(f"Predicting demand for product: {product_id}")
        
        # Prepare data
        sales_df = self.prepare_historical_data(sales_history)
        
        if sales_df.empty:
            logger.warning(f"Cannot forecast for {product_id}: no data")
            return {
                'product_id': product_id,
                'forecast': [],
                'error': 'Insufficient data'
            }
        
        # Generate forecast
        if self.model_type == 'prophet':
            forecast_df = self.forecast_prophet(sales_df)
        else:
            forecast_df = self.forecast_random_forest(sales_df)
        
        if forecast_df is None or forecast_df.empty:
            return {
                'product_id': product_id,
                'forecast': [],
                'error': 'Forecasting failed'
            }
        
        # Calculate statistics
        forecast_values = forecast_df['yhat'].values
        avg_demand = float(np.mean(forecast_values))
        total_demand = float(np.sum(forecast_values))
        std_dev = float(np.std(forecast_values))
        min_demand = float(np.min(forecast_values))
        max_demand = float(np.max(forecast_values))
        
        return {
            'product_id': product_id,
            'forecast_period_days': self.forecast_days,
            'forecast': [
                {
                    'date': row['ds'].strftime('%Y-%m-%d'),
                    'predicted_quantity': float(row['yhat']),
                    'lower_bound': float(row.get('yhat_lower', row['yhat'] * 0.8)),
                    'upper_bound': float(row.get('yhat_upper', row['yhat'] * 1.2))
                }
                for _, row in forecast_df.iterrows()
            ],
            'statistics': {
                'average_daily_demand': avg_demand,
                'total_forecast_demand': total_demand,
                'std_deviation': std_dev,
                'min_daily_demand': min_demand,
                'max_daily_demand': max_demand,
                'forecast_generated_at': datetime.now().isoformat()
            }
        }
    
    def batch_forecast(self, products_sales_data: Dict[str, List[Dict]]) -> List[Dict]:
        """
        Generate forecasts for multiple products
        
        Args:
            products_sales_data: Dict of product_id -> sales_history
            
        Returns:
            List of forecasts for each product
        """
        logger.info(f"Generating batch forecasts for {len(products_sales_data)} products")
        
        forecasts = []
        for product_id, sales_history in products_sales_data.items():
            forecast = self.predict_demand(product_id, sales_history)
            forecasts.append(forecast)
        
        return forecasts