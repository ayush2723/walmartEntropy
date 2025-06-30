"""
SmartWaste AI - Waste Prediction Model
Advanced machine learning model for predicting product waste probability
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from sklearn.preprocessing import StandardScaler, LabelEncoder
import joblib
import logging
from datetime import datetime, timedelta
import os

logger = logging.getLogger(__name__)

class WastePredictor:
    def __init__(self):
        self.model = None
        self.scaler = StandardScaler()
        self.label_encoders = {}
        self.feature_names = [
            'current_stock', 'days_until_expiry', 'sales_velocity_7d',
            'temperature', 'humidity', 'discount_rate', 'is_weekend',
            'promotion_active', 'category_encoded', 'stock_to_velocity_ratio',
            'expiry_urgency', 'environmental_risk', 'seasonal_factor'
        ]
        self.model_performance = {}
        self.is_trained = False
        
    def initialize_model(self):
        """Initialize the model with default parameters"""
        try:
            # Try to load existing model
            if os.path.exists('models/waste_predictor_model.pkl'):
                self.load_model()
                logger.info("Loaded existing waste prediction model")
            else:
                # Train with synthetic data if no model exists
                self._train_with_synthetic_data()
                logger.info("Initialized waste prediction model with synthetic data")
                
        except Exception as e:
            logger.error(f"Error initializing model: {str(e)}")
            # Fallback to rule-based predictions
            self.is_trained = False

    def _create_synthetic_training_data(self, n_samples=1000):
        """Create synthetic training data for initial model training"""
        np.random.seed(42)
        
        categories = ['produce', 'dairy', 'bakery', 'meat', 'frozen']
        
        data = []
        for _ in range(n_samples):
            category = np.random.choice(categories)
            
            # Generate realistic features based on category
            if category == 'produce':
                days_until_expiry = np.random.randint(1, 8)
                sales_velocity = np.random.normal(10, 3)
                temperature = np.random.normal(68, 5)
                humidity = np.random.normal(65, 10)
            elif category == 'dairy':
                days_until_expiry = np.random.randint(1, 14)
                sales_velocity = np.random.normal(15, 4)
                temperature = np.random.normal(38, 3)
                humidity = np.random.normal(45, 5)
            elif category == 'bakery':
                days_until_expiry = np.random.randint(1, 5)
                sales_velocity = np.random.normal(8, 2)
                temperature = np.random.normal(72, 4)
                humidity = np.random.normal(55, 8)
            elif category == 'meat':
                days_until_expiry = np.random.randint(1, 7)
                sales_velocity = np.random.normal(12, 3)
                temperature = np.random.normal(35, 2)
                humidity = np.random.normal(40, 5)
            else:  # frozen
                days_until_expiry = np.random.randint(7, 90)
                sales_velocity = np.random.normal(6, 2)
                temperature = np.random.normal(0, 5)
                humidity = np.random.normal(30, 10)
            
            current_stock = np.random.randint(10, 100)
            discount_rate = np.random.uniform(0, 0.5)
            is_weekend = np.random.choice([0, 1], p=[0.7, 0.3])
            promotion_active = np.random.choice([0, 1], p=[0.8, 0.2])
            
            # Calculate derived features
            stock_to_velocity_ratio = current_stock / max(sales_velocity, 1)
            expiry_urgency = max(0, (7 - days_until_expiry) / 7)
            environmental_risk = (abs(temperature - 70) / 70 + abs(humidity - 50) / 50) / 2
            seasonal_factor = np.random.uniform(0.8, 1.2)
            
            # Calculate waste probability based on realistic factors
            waste_prob = 0.1  # Base probability
            
            # Days until expiry factor
            if days_until_expiry <= 1:
                waste_prob += 0.6
            elif days_until_expiry <= 3:
                waste_prob += 0.3
            elif days_until_expiry <= 7:
                waste_prob += 0.1
            
            # Stock to velocity ratio factor
            if stock_to_velocity_ratio > 10:
                waste_prob += 0.4
            elif stock_to_velocity_ratio > 5:
                waste_prob += 0.2
            
            # Environmental risk factor
            waste_prob += environmental_risk * 0.2
            
            # Discount and promotion effects
            waste_prob -= discount_rate * 0.3
            waste_prob -= promotion_active * 0.1
            
            # Category-specific adjustments
            category_risk = {
                'produce': 0.1, 'dairy': 0.05, 'bakery': 0.15,
                'meat': 0.08, 'frozen': -0.05
            }
            waste_prob += category_risk[category]
            
            # Ensure probability is between 0 and 1
            waste_prob = max(0, min(1, waste_prob))
            
            # Determine if will expire unsold
            will_expire_unsold = 1 if waste_prob > 0.5 else 0
            
            data.append({
                'current_stock': current_stock,
                'days_until_expiry': days_until_expiry,
                'sales_velocity_7d': max(0, sales_velocity),
                'temperature': temperature,
                'humidity': max(0, min(100, humidity)),
                'discount_rate': discount_rate,
                'is_weekend': is_weekend,
                'promotion_active': promotion_active,
                'category': category,
                'stock_to_velocity_ratio': stock_to_velocity_ratio,
                'expiry_urgency': expiry_urgency,
                'environmental_risk': environmental_risk,
                'seasonal_factor': seasonal_factor,
                'will_expire_unsold': will_expire_unsold,
                'waste_probability': waste_prob
            })
        
        return pd.DataFrame(data)

    def _train_with_synthetic_data(self):
        """Train the model with synthetic data"""
        # Generate synthetic training data
        df = self._create_synthetic_training_data(1000)
        
        # Prepare features
        X = self._prepare_features(df)
        y = df['will_expire_unsold'].values
        
        # Train the model
        self._train_model(X, y)
        
        # Save the model
        self.save_model()

    def _prepare_features(self, df):
        """Prepare features for model training/prediction"""
        # Encode categorical variables
        if 'category' in df.columns:
            if 'category' not in self.label_encoders:
                self.label_encoders['category'] = LabelEncoder()
                df['category_encoded'] = self.label_encoders['category'].fit_transform(df['category'])
            else:
                df['category_encoded'] = self.label_encoders['category'].transform(df['category'])
        
        # Select features
        feature_columns = [col for col in self.feature_names if col in df.columns]
        X = df[feature_columns].fillna(0)
        
        return X

    def _train_model(self, X, y):
        """Train the waste prediction model"""
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Try different models and select the best one
        models = {
            'RandomForest': RandomForestClassifier(
                n_estimators=100, max_depth=10, random_state=42, class_weight='balanced'
            ),
            'GradientBoosting': GradientBoostingClassifier(
                n_estimators=100, max_depth=6, learning_rate=0.1, random_state=42
            ),
            'LogisticRegression': LogisticRegression(
                random_state=42, class_weight='balanced', max_iter=1000
            )
        }
        
        best_score = 0
        best_model = None
        best_name = None
        
        for name, model in models.items():
            # Cross-validation
            cv_scores = cross_val_score(model, X_train_scaled, y_train, cv=5, scoring='f1')
            avg_score = cv_scores.mean()
            
            logger.info(f"{name} CV F1 Score: {avg_score:.4f} (+/- {cv_scores.std() * 2:.4f})")
            
            if avg_score > best_score:
                best_score = avg_score
                best_model = model
                best_name = name
        
        # Train the best model
        self.model = best_model
        self.model.fit(X_train_scaled, y_train)
        
        # Evaluate on test set
        y_pred = self.model.predict(X_test_scaled)
        y_pred_proba = self.model.predict_proba(X_test_scaled)[:, 1]
        
        # Store performance metrics
        self.model_performance = {
            'model_name': best_name,
            'accuracy': accuracy_score(y_test, y_pred),
            'precision': precision_score(y_test, y_pred),
            'recall': recall_score(y_test, y_pred),
            'f1_score': f1_score(y_test, y_pred),
            'cv_score': best_score,
            'training_date': datetime.now().isoformat(),
            'training_samples': len(X_train)
        }
        
        self.is_trained = True
        logger.info(f"Model trained successfully: {best_name} with F1 score: {best_score:.4f}")

    def predict_waste_probability(self, current_stock, days_until_expiry, sales_velocity,
                                category, temperature=70, humidity=60, discount_rate=0.0,
                                is_weekend=False, promotion_active=False):
        """
        Predict waste probability for a single product
        
        Returns:
            dict: Prediction results including probability, confidence, and risk factors
        """
        try:
            # Calculate derived features
            stock_to_velocity_ratio = current_stock / max(sales_velocity, 1)
            expiry_urgency = max(0, (7 - days_until_expiry) / 7)
            environmental_risk = (abs(temperature - 70) / 70 + abs(humidity - 50) / 50) / 2
            seasonal_factor = 1.0  # Could be enhanced with actual seasonal data
            
            # Create feature vector
            features_dict = {
                'current_stock': current_stock,
                'days_until_expiry': days_until_expiry,
                'sales_velocity_7d': sales_velocity,
                'temperature': temperature,
                'humidity': humidity,
                'discount_rate': discount_rate,
                'is_weekend': 1 if is_weekend else 0,
                'promotion_active': 1 if promotion_active else 0,
                'category': category,
                'stock_to_velocity_ratio': stock_to_velocity_ratio,
                'expiry_urgency': expiry_urgency,
                'environmental_risk': environmental_risk,
                'seasonal_factor': seasonal_factor
            }
            
            # Convert to DataFrame for consistent processing
            df = pd.DataFrame([features_dict])
            X = self._prepare_features(df)
            
            if self.is_trained and self.model is not None:
                # Use trained model
                X_scaled = self.scaler.transform(X)
                waste_probability = self.model.predict_proba(X_scaled)[0, 1]
                confidence = 0.85  # Model-based confidence
            else:
                # Fallback to rule-based prediction
                waste_probability = self._rule_based_prediction(features_dict)
                confidence = 0.65  # Lower confidence for rule-based
            
            # Calculate predicted waste amount
            predicted_waste_amount = int(current_stock * waste_probability)
            
            # Identify risk factors
            risk_factors = self._identify_risk_factors(features_dict, waste_probability)
            
            return {
                'waste_probability': waste_probability,
                'predicted_waste_amount': predicted_waste_amount,
                'confidence': confidence,
                'risk_factors': risk_factors,
                'model_used': 'ml' if self.is_trained else 'rule_based'
            }
            
        except Exception as e:
            logger.error(f"Error in waste prediction: {str(e)}")
            # Return safe fallback prediction
            return {
                'waste_probability': 0.3,
                'predicted_waste_amount': int(current_stock * 0.3),
                'confidence': 0.5,
                'risk_factors': ['prediction_error'],
                'model_used': 'fallback',
                'error': str(e)
            }

    def _rule_based_prediction(self, features):
        """Fallback rule-based prediction when ML model is not available"""
        waste_prob = 0.1  # Base probability
        
        # Days until expiry factor
        days = features['days_until_expiry']
        if days <= 1:
            waste_prob += 0.6
        elif days <= 3:
            waste_prob += 0.3
        elif days <= 7:
            waste_prob += 0.1
        
        # Stock to velocity ratio factor
        ratio = features['stock_to_velocity_ratio']
        if ratio > 10:
            waste_prob += 0.4
        elif ratio > 5:
            waste_prob += 0.2
        
        # Environmental risk
        waste_prob += features['environmental_risk'] * 0.2
        
        # Discount and promotion effects
        waste_prob -= features['discount_rate'] * 0.3
        waste_prob -= features['promotion_active'] * 0.1
        
        # Category-specific risk
        category_risk = {
            'produce': 0.1, 'dairy': 0.05, 'bakery': 0.15,
            'meat': 0.08, 'frozen': -0.05
        }
        waste_prob += category_risk.get(features['category'], 0)
        
        return max(0, min(1, waste_prob))

    def _identify_risk_factors(self, features, waste_probability):
        """Identify key risk factors contributing to waste probability"""
        risk_factors = []
        
        if features['days_until_expiry'] <= 2:
            risk_factors.append('expiring_soon')
        
        if features['stock_to_velocity_ratio'] > 7:
            risk_factors.append('overstocked')
        
        if features['environmental_risk'] > 0.3:
            risk_factors.append('poor_storage_conditions')
        
        if features['sales_velocity_7d'] < 3:
            risk_factors.append('low_sales_velocity')
        
        if features['category'] in ['produce', 'bakery']:
            risk_factors.append('perishable_category')
        
        if waste_probability > 0.7:
            risk_factors.append('high_waste_risk')
        elif waste_probability > 0.4:
            risk_factors.append('medium_waste_risk')
        
        return risk_factors

    def retrain_model(self, new_training_data=None):
        """Retrain the model with new data"""
        try:
            if new_training_data is not None:
                # Use provided training data
                df = pd.DataFrame(new_training_data)
            else:
                # Generate new synthetic data (in production, use real historical data)
                df = self._create_synthetic_training_data(1200)
            
            # Prepare features and target
            X = self._prepare_features(df)
            y = df['will_expire_unsold'].values
            
            # Retrain the model
            self._train_model(X, y)
            
            # Save the updated model
            self.save_model()
            
            return {
                'status': 'success',
                'training_samples': len(df),
                'performance': self.model_performance,
                'retrain_date': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error retraining model: {str(e)}")
            return {
                'status': 'error',
                'error': str(e)
            }

    def get_performance_metrics(self):
        """Get current model performance metrics"""
        return self.model_performance

    def save_model(self):
        """Save the trained model and preprocessors"""
        try:
            os.makedirs('models', exist_ok=True)
            
            model_data = {
                'model': self.model,
                'scaler': self.scaler,
                'label_encoders': self.label_encoders,
                'feature_names': self.feature_names,
                'performance': self.model_performance,
                'is_trained': self.is_trained
            }
            
            joblib.dump(model_data, 'models/waste_predictor_model.pkl')
            logger.info("Model saved successfully")
            
        except Exception as e:
            logger.error(f"Error saving model: {str(e)}")

    def load_model(self):
        """Load a previously trained model"""
        try:
            model_data = joblib.load('models/waste_predictor_model.pkl')
            
            self.model = model_data['model']
            self.scaler = model_data['scaler']
            self.label_encoders = model_data['label_encoders']
            self.feature_names = model_data['feature_names']
            self.model_performance = model_data['performance']
            self.is_trained = model_data['is_trained']
            
            logger.info("Model loaded successfully")
            
        except Exception as e:
            logger.error(f"Error loading model: {str(e)}")
            self.is_trained = False