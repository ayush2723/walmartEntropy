import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split
import warnings
warnings.filterwarnings('ignore')

class PerishableDataProcessor:
    def __init__(self):
        self.scaler = StandardScaler()
        self.label_encoders = {}
        
    def create_features(self, df):
        """
        Create comprehensive features for perishable product forecasting
        Expected columns: date, product_id, sales_qty, inventory, expiry_date, 
                         category, price, discount_rate
        """
        df = df.copy()
        df['date'] = pd.to_datetime(df['date'])
        df['expiry_date'] = pd.to_datetime(df['expiry_date'])
        
        # Time-based features
        df['days_to_expiry'] = (df['expiry_date'] - df['date']).dt.days
        df['day_of_week'] = df['date'].dt.dayofweek
        df['month'] = df['date'].dt.month
        df['is_weekend'] = df['day_of_week'].isin([5, 6]).astype(int)
        df['quarter'] = df['date'].dt.quarter
        
        # Product lifecycle features
        df['shelf_life'] = df.groupby('product_id')['days_to_expiry'].transform('max')
        df['freshness_ratio'] = df['days_to_expiry'] / df['shelf_life']
        df['expiry_urgency'] = np.where(df['days_to_expiry'] <= 3, 2,
                                       np.where(df['days_to_expiry'] <= 7, 1, 0))
        
        # Sales velocity features (rolling windows)
        for window in [3, 7, 14]:
            df[f'sales_velocity_{window}d'] = df.groupby('product_id')['sales_qty'].transform(
                lambda x: x.rolling(window, min_periods=1).mean()
            )
            df[f'sales_std_{window}d'] = df.groupby('product_id')['sales_qty'].transform(
                lambda x: x.rolling(window, min_periods=1).std().fillna(0)
            )
        
        # Inventory turnover features
        df['turnover_rate'] = df['sales_qty'] / (df['inventory'] + 1e-6)
        df['inventory_days'] = df['inventory'] / (df['sales_velocity_7d'] + 1e-6)
        df['overstock_risk'] = (df['inventory_days'] > df['days_to_expiry']).astype(int)
        
        # Price elasticity features
        df['price_discount_impact'] = df['discount_rate'] * df['price']
        df['relative_price'] = df.groupby(['category', 'date'])['price'].transform(
            lambda x: x / x.mean()
        )
        
        # Seasonal patterns
        df['sales_seasonality'] = df.groupby(['product_id', 'month'])['sales_qty'].transform('mean')
        df['seasonal_deviation'] = df['sales_qty'] / (df['sales_seasonality'] + 1e-6)
        
        # Target variables
        df['will_expire_unsold'] = ((df['inventory'] > 0) & 
                                   (df['days_to_expiry'] <= 0)).astype(int)
        df['waste_risk_score'] = np.clip(
            (df['inventory_days'] / df['days_to_expiry']) * df['overstock_risk'], 0, 1
        )
        
        return df
    
    def create_action_labels(self, df):
        """
        Create action labels based on business rules
        """
        df = df.copy()
        
        def determine_action(row):
            if row['days_to_expiry'] <= 1 and row['waste_risk_score'] > 0.8:
                return 'donate'
            elif row['days_to_expiry'] <= 3 and row['waste_risk_score'] > 0.6:
                return 'discount'
            elif row['waste_risk_score'] > 0.7:
                return 'reroute'
            else:
                return 'keep'
        
        df['action_label'] = df.apply(determine_action, axis=1)
        return df
    
    def prepare_forecasting_data(self, df):
        """
        Prepare data for time series forecasting (Prophet format)
        """
        forecast_data = []
        
        for product_id in df['product_id'].unique():
            product_df = df[df['product_id'] == product_id].copy()
            product_df = product_df.sort_values('date')
            
            # Prophet format
            prophet_df = pd.DataFrame({
                'ds': product_df['date'],
                'y': product_df['sales_qty'],
                'product_id': product_id,
                'inventory': product_df['inventory'],
                'days_to_expiry': product_df['days_to_expiry'],
                'price': product_df['price'],
                'discount_rate': product_df['discount_rate'],
                'is_weekend': product_df['is_weekend'],
                'expiry_urgency': product_df['expiry_urgency']
            })
            
            forecast_data.append(prophet_df)
        
        return pd.concat(forecast_data, ignore_index=True)
    
    def prepare_classification_data(self, df):
        """
        Prepare data for classification models
        """
        feature_cols = [
            'days_to_expiry', 'freshness_ratio', 'expiry_urgency',
            'sales_velocity_3d', 'sales_velocity_7d', 'sales_velocity_14d',
            'sales_std_7d', 'turnover_rate', 'inventory_days', 'overstock_risk',
            'price_discount_impact', 'relative_price', 'seasonal_deviation',
            'day_of_week', 'month', 'is_weekend', 'inventory', 'waste_risk_score'
        ]
        
        # Encode categorical variables
        if 'category' in df.columns:
            if 'category' not in self.label_encoders:
                self.label_encoders['category'] = LabelEncoder()
                df['category_encoded'] = self.label_encoders['category'].fit_transform(df['category'])
            else:
                df['category_encoded'] = self.label_encoders['category'].transform(df['category'])
            feature_cols.append('category_encoded')
        
        X = df[feature_cols].fillna(0)
        y_binary = df['will_expire_unsold']
        y_multiclass = df['action_label']
        
        return X, y_binary, y_multiclass

# Example usage
def load_sample_data():
    """
    Generate sample data for demonstration
    """
    np.random.seed(42)
    
    dates = pd.date_range('2023-01-01', '2024-01-31', freq='D')
    products = [f'PROD_{i:03d}' for i in range(1, 51)]  # 50 products
    categories = ['dairy', 'bakery', 'produce', 'meat', 'deli']
    
    data = []
    for date in dates:
        for product in np.random.choice(products, size=np.random.randint(10, 30)):
            category = np.random.choice(categories)
            shelf_life = {'dairy': 7, 'bakery': 3, 'produce': 5, 'meat': 5, 'deli': 4}[category]
            
            # Simulate expiry date based on shelf life
            expiry_date = date + timedelta(days=np.random.randint(-2, shelf_life + 3))

            
            data.append({
                'date': date,
                'product_id': product,
                'category': category,
                'sales_qty': max(0, np.random.poisson(10) + np.random.randint(-5, 5)),
                'inventory': np.random.randint(5, 100),
                'expiry_date': expiry_date,
                'price': np.random.uniform(1, 20),
                'discount_rate': np.random.uniform(0, 0.3)
            })
    
    return pd.DataFrame(data)

# Initialize processor and create features
processor = PerishableDataProcessor()
sample_df = load_sample_data()
print("Sample data shape:", sample_df.shape)
print("\nSample data columns:", sample_df.columns.tolist())

# Process the data
processed_df = processor.create_features(sample_df)
processed_df = processor.create_action_labels(processed_df)

print(f"\nProcessed data shape: {processed_df.shape}")
print(f"Action label distribution:")
print(processed_df['action_label'].value_counts())
print(f"\nWaste risk score statistics:")
print(processed_df['waste_risk_score'].describe())