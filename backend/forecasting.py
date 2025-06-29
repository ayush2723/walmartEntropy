import pandas as pd
import numpy as np
from prophet import Prophet
import xgboost as xgb
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import TimeSeriesSplit
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

class PerishableForecastingSystem:
    def __init__(self):
        self.prophet_models = {}
        self.xgb_model = None
        self.forecast_horizon = 7  # days
        
    def train_prophet_models(self, df):
        """
        Train Prophet models for each product
        """
        print("Training Prophet models...")
        
        for product_id in df['product_id'].unique():
            product_df = df[df['product_id'] == product_id].copy()
            
            if len(product_df) < 10:  # Skip products with insufficient data
                continue
                
            # Prepare Prophet data
            prophet_df = product_df[['ds', 'y']].copy()
            
            # Add regressors
            prophet_df['inventory'] = product_df['inventory']
            prophet_df['price'] = product_df['price']
            prophet_df['discount_rate'] = product_df['discount_rate']
            prophet_df['is_weekend'] = product_df['is_weekend']
            prophet_df['expiry_urgency'] = product_df['expiry_urgency']
            
            # Initialize and configure Prophet
            model = Prophet(
                daily_seasonality=True,
                weekly_seasonality=True,
                yearly_seasonality=True,
                seasonality_mode='multiplicative',
                changepoint_prior_scale=0.05,
                seasonality_prior_scale=10
            )
            
            # Add regressors
            model.add_regressor('inventory')
            model.add_regressor('price')
            model.add_regressor('discount_rate')
            model.add_regressor('is_weekend')
            model.add_regressor('expiry_urgency')
            
            try:
                model.fit(prophet_df)
                self.prophet_models[product_id] = model
                print(f"✓ Trained Prophet model for {product_id}")
            except Exception as e:
                print(f"✗ Failed to train Prophet model for {product_id}: {str(e)}")
                
        print(f"Successfully trained {len(self.prophet_models)} Prophet models")
        
    def create_xgb_features(self, df):
        """
        Create features for XGBoost model
        """
        features = []
        
        for product_id in df['product_id'].unique():
            product_df = df[df['product_id'] == product_id].copy()
            product_df = product_df.sort_values('ds')
            
            # Lag features
            for lag in [1, 3, 7]:
                product_df[f'sales_lag_{lag}'] = product_df['y'].shift(lag)
                
            # Rolling statistics
            for window in [3, 7, 14]:
                product_df[f'sales_roll_mean_{window}'] = product_df['y'].rolling(window).mean()
                product_df[f'sales_roll_std_{window}'] = product_df['y'].rolling(window).std()
                
            # Trend features
            product_df['sales_trend_7d'] = product_df['y'].rolling(7).apply(
                lambda x: np.polyfit(range(len(x)), x, 1)[0] if len(x) == 7 else 0
            )
            
            features.append(product_df)
            
        return pd.concat(features, ignore_index=True)
    
    def train_xgb_model(self, df):
        """
        Train XGBoost model for ensemble forecasting
        """
        print("Training XGBoost model...")
        
        # Create features
        df_features = self.create_xgb_features(df)
        
        # Select features
        feature_cols = [
            'inventory', 'price', 'discount_rate', 'is_weekend', 'expiry_urgency',
            'sales_lag_1', 'sales_lag_3', 'sales_lag_7',
            'sales_roll_mean_3', 'sales_roll_mean_7', 'sales_roll_mean_14',
            'sales_roll_std_7', 'sales_trend_7d'
        ]
        
        # Add time features
        df_features['day_of_week'] = df_features['ds'].dt.dayofweek
        df_features['month'] = df_features['ds'].dt.month
        df_features['day_of_month'] = df_features['ds'].dt.day
        feature_cols.extend(['day_of_week', 'month', 'day_of_month'])
        
        # Prepare training data
        df_clean = df_features.dropna()
        X = df_clean[feature_cols]
        y = df_clean['y']
        
        # Train XGBoost
        self.xgb_model = xgb.XGBRegressor(
            n_estimators=100,
            max_depth=6,
            learning_rate=0.1,
            random_state=42,
            n_jobs=-1
        )
        
        self.xgb_model.fit(X, y)
        print("✓ XGBoost model trained successfully")
        
        # Feature importance
        importance = pd.DataFrame({
            'feature': feature_cols,
            'importance': self.xgb_model.feature_importances_
        }).sort_values('importance', ascending=False)
        
        print("\nTop 10 Most Important Features:")
        print(importance.head(10))
        
        return importance
    
    def forecast_prophet(self, product_id, future_dates, regressors):
        """
        Generate Prophet forecast for a specific product
        """
        if product_id not in self.prophet_models:
            return None
            
        model = self.prophet_models[product_id]
        
        # Prepare future dataframe
        future_df = pd.DataFrame({'ds': future_dates})
        for col, values in regressors.items():
            future_df[col] = values
            
        # Generate forecast
        forecast = model.predict(future_df)
        
        return forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']]
    
    def forecast_xgb(self, df_current, days_ahead=7):
        """
        Generate XGBoost forecast
        """
        if self.xgb_model is None:
            return None
            
        forecasts = []
        
        for product_id in df_current['product_id'].unique():
            product_df = df_current[df_current['product_id'] == product_id].copy()
            product_df = product_df.sort_values('ds').tail(30)  # Use last 30 days
            
            if len(product_df) < 7:
                continue
                
            # Generate features for future dates
            last_date = product_df['ds'].max()
            future_dates = [last_date + timedelta(days=i) for i in range(1, days_ahead + 1)]
            
            for future_date in future_dates:
                # Create features for future prediction
                future_features = self.create_future_features(product_df, future_date)
                
                if future_features is not None:
                    pred = self.xgb_model.predict([future_features])[0]
                    forecasts.append({
                        'product_id': product_id,
                        'ds': future_date,
                        'yhat_xgb': max(0, pred)  # Ensure non-negative
                    })
        
        return pd.DataFrame(forecasts)
    
    def create_future_features(self, product_df, future_date):
        """
        Create features for future prediction
        """
        try:
            # Get recent data for lag features
            recent_sales = product_df['y'].tail(14).values
            
            # Basic features (you would get these from your system)
            inventory = product_df['inventory'].iloc[-1]  # Use last known inventory
            price = product_df['price'].iloc[-1]
            discount_rate = product_df['discount_rate'].iloc[-1]
            
            # Time features
            is_weekend = 1 if future_date.weekday() >= 5 else 0
            day_of_week = future_date.weekday()
            month = future_date.month
            day_of_month = future_date.day
            
            # Lag features
            sales_lag_1 = recent_sales[-1] if len(recent_sales) >= 1 else 0
            sales_lag_3 = recent_sales[-3] if len(recent_sales) >= 3 else 0
            sales_lag_7 = recent_sales[-7] if len(recent_sales) >= 7 else 0
            
            # Rolling features
            sales_roll_mean_3 = np.mean(recent_sales[-3:]) if len(recent_sales) >= 3 else 0
            sales_roll_mean_7 = np.mean(recent_sales[-7:]) if len(recent_sales) >= 7 else 0
            sales_roll_mean_14 = np.mean(recent_sales) if len(recent_sales) > 0 else 0
            sales_roll_std_7 = np.std(recent_sales[-7:]) if len(recent_sales) >= 7 else 0
            
            # Trend feature
            if len(recent_sales) >= 7:
                sales_trend_7d = np.polyfit(range(7), recent_sales[-7:], 1)[0]
            else:
                sales_trend_7d = 0
                
            # Expiry urgency (would need to be calculated based on actual expiry dates)
            expiry_urgency = 0  # Placeholder
            
            features = [
                inventory, price, discount_rate, is_weekend, expiry_urgency,
                sales_lag_1, sales_lag_3, sales_lag_7,
                sales_roll_mean_3, sales_roll_mean_7, sales_roll_mean_14,
                sales_roll_std_7, sales_trend_7d,
                day_of_week, month, day_of_month
            ]
            
            return features
            
        except Exception as e:
            print(f"Error creating future features: {str(e)}")
            return None
    
    def ensemble_forecast(self, df_current, days_ahead=7):
        """
        Combine Prophet and XGBoost forecasts
        """
        # Get XGBoost forecasts
        xgb_forecasts = self.forecast_xgb(df_current, days_ahead)
        
        # Get Prophet forecasts
        prophet_forecasts = []
        
        for product_id in df_current['product_id'].unique():
            if product_id in self.prophet_models:
                # Create future dates
                last_date = df_current[df_current['product_id'] == product_id]['ds'].max()
                future_dates = [last_date + timedelta(days=i) for i in range(1, days_ahead + 1)]
                
                # Create dummy regressors (you would get actual values from your system)
                regressors = {
                    'inventory': [50] * len(future_dates),  # Placeholder
                    'price': [10] * len(future_dates),
                    'discount_rate': [0.1] * len(future_dates),
                    'is_weekend': [1 if d.weekday() >= 5 else 0 for d in future_dates],
                    'expiry_urgency': [0] * len(future_dates)
                }
                
                prophet_pred = self.forecast_prophet(product_id, future_dates, regressors)
                if prophet_pred is not None:
                    prophet_pred['product_id'] = product_id
                    prophet_forecasts.append(prophet_pred)
        
        # Combine forecasts
        if prophet_forecasts:
            prophet_df = pd.concat(prophet_forecasts, ignore_index=True)
            
            # Merge with XGBoost forecasts
            ensemble_df = prophet_df.merge(
                xgb_forecasts, 
                on=['product_id', 'ds'], 
                how='outer'
            )
            
            # Create ensemble prediction (weighted average)
            ensemble_df['yhat_xgb'] = ensemble_df['yhat_xgb'].fillna(ensemble_df['yhat'])
            ensemble_df['yhat_ensemble'] = (
                0.6 * ensemble_df['yhat'] + 0.4 * ensemble_df['yhat_xgb']
            )
            
            # Calculate confidence intervals
            ensemble_df['yhat_lower'] = ensemble_df['yhat_lower'].fillna(
                ensemble_df['yhat_ensemble'] * 0.8
            )
            ensemble_df['yhat_upper'] = ensemble_df['yhat_upper'].fillna(
                ensemble_df['yhat_ensemble'] * 1.2
            )
            
            return ensemble_df
        
        return xgb_forecasts
    
    def evaluate_forecasts(self, df_actual, df_forecast):
        """
        Evaluate forecast accuracy
        """
        merged = df_actual.merge(df_forecast, on=['product_id', 'ds'], how='inner')
        
        if len(merged) == 0:
            print("No matching data for evaluation")
            return None
            
        # Calculate metrics
        mae = mean_absolute_error(merged['y'], merged['yhat_ensemble'])
        mse = mean_squared_error(merged['y'], merged['yhat_ensemble'])
        rmse = np.sqrt(mse)
        
        # Calculate MAPE (Mean Absolute Percentage Error)
        mape = np.mean(np.abs((merged['y'] - merged['yhat_ensemble']) / 
                             (merged['y'] + 1e-6))) * 100
        
        metrics = {
            'MAE': mae,
            'MSE': mse,
            'RMSE': rmse,
            'MAPE': mape
        }
        
        print("Forecast Evaluation Metrics:")
        for metric, value in metrics.items():
            print(f"{metric}: {value:.4f}")
            
        return metrics

# Example usage
print("Forecasting System Example:")
print("=" * 50)

# This would be your actual data
# forecasting_system = PerishableForecastingSystem()
# forecasting_system.train_prophet_models(forecast_data)
# forecasting_system.train_xgb_model(forecast_data)
# forecasts = forecasting_system.ensemble_forecast(current_data)