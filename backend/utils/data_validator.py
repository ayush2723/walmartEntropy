"""
SmartWaste AI - Data Validation Utilities
Validates input data for API endpoints and model predictions
"""

from typing import Dict, List, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class DataValidator:
    def __init__(self):
        self.required_fields = {
            'inventory_item': [
                'product_id', 'product_name', 'category', 'current_stock',
                'expiry_date', 'sales_velocity_7d'
            ],
            'prediction_request': [
                'inventory_items'
            ]
        }
        
        self.valid_categories = [
            'produce', 'dairy', 'bakery', 'meat', 'frozen', 'canned',
            'beverages', 'snacks', 'household', 'personal_care'
        ]
        
        self.valid_actions = ['keep', 'discount', 'donate', 'reroute']
    
    def validate_inventory_item(self, item: Dict[str, Any]) -> List[str]:
        """
        Validate a single inventory item
        
        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []
        
        # Check required fields
        for field in self.required_fields['inventory_item']:
            if field not in item:
                errors.append(f"Missing required field: {field}")
            elif item[field] is None:
                errors.append(f"Field cannot be null: {field}")
        
        if errors:  # Don't continue if basic fields are missing
            return errors
        
        # Validate data types and ranges
        try:
            # Product ID validation
            if not isinstance(item['product_id'], str) or len(item['product_id'].strip()) == 0:
                errors.append("product_id must be a non-empty string")
            
            # Product name validation
            if not isinstance(item['product_name'], str) or len(item['product_name'].strip()) == 0:
                errors.append("product_name must be a non-empty string")
            
            # Category validation
            if item['category'].lower() not in self.valid_categories:
                errors.append(f"Invalid category. Must be one of: {', '.join(self.valid_categories)}")
            
            # Stock validation
            if not isinstance(item['current_stock'], (int, float)) or item['current_stock'] < 0:
                errors.append("current_stock must be a non-negative number")
            
            # Sales velocity validation
            if not isinstance(item['sales_velocity_7d'], (int, float)) or item['sales_velocity_7d'] < 0:
                errors.append("sales_velocity_7d must be a non-negative number")
            
            # Date validation
            try:
                expiry_date = datetime.strptime(item['expiry_date'], '%Y-%m-%d')
                if 'purchase_date' in item:
                    purchase_date = datetime.strptime(item['purchase_date'], '%Y-%m-%d')
                    if purchase_date >= expiry_date:
                        errors.append("purchase_date must be before expiry_date")
            except ValueError:
                errors.append("expiry_date must be in YYYY-MM-DD format")
            
            # Optional field validations
            if 'price' in item:
                if not isinstance(item['price'], (int, float)) or item['price'] <= 0:
                    errors.append("price must be a positive number")
            
            if 'discount_rate' in item:
                if not isinstance(item['discount_rate'], (int, float)) or not (0 <= item['discount_rate'] <= 1):
                    errors.append("discount_rate must be between 0 and 1")
            
            if 'temperature' in item:
                if not isinstance(item['temperature'], (int, float)) or not (-50 <= item['temperature'] <= 150):
                    errors.append("temperature must be between -50 and 150 degrees")
            
            if 'humidity' in item:
                if not isinstance(item['humidity'], (int, float)) or not (0 <= item['humidity'] <= 100):
                    errors.append("humidity must be between 0 and 100 percent")
            
            if 'is_weekend' in item:
                if not isinstance(item['is_weekend'], bool):
                    errors.append("is_weekend must be a boolean")
            
            if 'promotion_active' in item:
                if not isinstance(item['promotion_active'], bool):
                    errors.append("promotion_active must be a boolean")
            
        except Exception as e:
            errors.append(f"Validation error: {str(e)}")
        
        return errors
    
    def validate_prediction_request(self, request_data: Dict[str, Any]) -> List[str]:
        """
        Validate a prediction request
        
        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []
        
        # Check required fields
        if 'inventory_items' not in request_data:
            errors.append("Missing required field: inventory_items")
            return errors
        
        inventory_items = request_data['inventory_items']
        
        # Validate inventory_items is a list
        if not isinstance(inventory_items, list):
            errors.append("inventory_items must be a list")
            return errors
        
        # Check if list is not empty
        if len(inventory_items) == 0:
            errors.append("inventory_items cannot be empty")
            return errors
        
        # Check maximum number of items (to prevent abuse)
        if len(inventory_items) > 1000:
            errors.append("Maximum 1000 inventory items allowed per request")
        
        # Validate each inventory item
        for i, item in enumerate(inventory_items):
            if not isinstance(item, dict):
                errors.append(f"Item {i+1}: Must be an object")
                continue
            
            item_errors = self.validate_inventory_item(item)
            for error in item_errors:
                errors.append(f"Item {i+1}: {error}")
        
        return errors
    
    def validate_action_recommendation(self, recommendation: Dict[str, Any]) -> List[str]:
        """
        Validate an action recommendation
        
        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []
        
        required_fields = ['product_id', 'recommended_action']
        
        # Check required fields
        for field in required_fields:
            if field not in recommendation:
                errors.append(f"Missing required field: {field}")
        
        if errors:
            return errors
        
        # Validate action
        if recommendation['recommended_action'] not in self.valid_actions:
            errors.append(f"Invalid action. Must be one of: {', '.join(self.valid_actions)}")
        
        # Validate optional fields
        if 'suggested_discount' in recommendation:
            discount = recommendation['suggested_discount']
            if not isinstance(discount, (int, float)) or not (0 <= discount <= 100):
                errors.append("suggested_discount must be between 0 and 100")
        
        if 'urgency' in recommendation:
            valid_urgencies = ['low', 'medium', 'high', 'critical']
            if recommendation['urgency'] not in valid_urgencies:
                errors.append(f"Invalid urgency. Must be one of: {', '.join(valid_urgencies)}")
        
        if 'confidence' in recommendation:
            confidence = recommendation['confidence']
            if not isinstance(confidence, (int, float)) or not (0 <= confidence <= 1):
                errors.append("confidence must be between 0 and 1")
        
        return errors
    
    def sanitize_input(self, data: Any) -> Any:
        """
        Sanitize input data by removing potentially harmful content
        """
        if isinstance(data, dict):
            return {key: self.sanitize_input(value) for key, value in data.items()}
        elif isinstance(data, list):
            return [self.sanitize_input(item) for item in data]
        elif isinstance(data, str):
            # Remove potentially harmful characters
            sanitized = data.strip()
            # Remove null bytes and control characters
            sanitized = ''.join(char for char in sanitized if ord(char) >= 32 or char in '\t\n\r')
            return sanitized
        else:
            return data
    
    def validate_date_range(self, start_date: str, end_date: str) -> List[str]:
        """
        Validate a date range
        
        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []
        
        try:
            start = datetime.strptime(start_date, '%Y-%m-%d')
            end = datetime.strptime(end_date, '%Y-%m-%d')
            
            if start >= end:
                errors.append("start_date must be before end_date")
            
            # Check if date range is reasonable (not too far in the past or future)
            now = datetime.now()
            max_past = now - timedelta(days=365 * 2)  # 2 years ago
            max_future = now + timedelta(days=365)  # 1 year in the future
            
            if start < max_past:
                errors.append("start_date cannot be more than 2 years in the past")
            
            if end > max_future:
                errors.append("end_date cannot be more than 1 year in the future")
            
        except ValueError as e:
            errors.append(f"Invalid date format: {str(e)}")
        
        return errors
    
    def validate_pagination_params(self, page: int, limit: int) -> List[str]:
        """
        Validate pagination parameters
        
        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []
        
        if not isinstance(page, int) or page < 1:
            errors.append("page must be a positive integer")
        
        if not isinstance(limit, int) or limit < 1 or limit > 1000:
            errors.append("limit must be between 1 and 1000")
        
        return errors