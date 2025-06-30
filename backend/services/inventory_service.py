"""
SmartWaste AI - Inventory Management Service
Handles inventory data operations and management
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import json
import os

logger = logging.getLogger(__name__)

class InventoryService:
    def __init__(self):
        self.inventory_data = {}
        self.load_sample_inventory()
    
    def load_sample_inventory(self):
        """Load sample inventory data for demonstration"""
        self.inventory_data = {
            "PROD_001": {
                "product_id": "PROD_001",
                "product_name": "Organic Bananas",
                "category": "produce",
                "current_stock": 45,
                "purchase_date": "2024-01-15",
                "expiry_date": "2024-01-22",
                "price": 2.99,
                "discount_rate": 0.0,
                "sales_velocity_7d": 8.5,
                "temperature": 68,
                "humidity": 65,
                "location": "Produce Section A",
                "supplier": "Fresh Farms Co",
                "last_updated": datetime.now().isoformat()
            },
            "PROD_002": {
                "product_id": "PROD_002",
                "product_name": "Fresh Milk",
                "category": "dairy",
                "current_stock": 24,
                "purchase_date": "2024-01-10",
                "expiry_date": "2024-01-17",
                "price": 3.99,
                "discount_rate": 0.15,
                "sales_velocity_7d": 12.3,
                "temperature": 38,
                "humidity": 45,
                "location": "Dairy Section B",
                "supplier": "Local Dairy Farm",
                "last_updated": datetime.now().isoformat()
            },
            "PROD_003": {
                "product_id": "PROD_003",
                "product_name": "Premium Bread",
                "category": "bakery",
                "current_stock": 18,
                "purchase_date": "2024-01-12",
                "expiry_date": "2024-01-15",
                "price": 2.99,
                "discount_rate": 0.25,
                "sales_velocity_7d": 6.8,
                "temperature": 72,
                "humidity": 55,
                "location": "Bakery Section",
                "supplier": "Artisan Bakery",
                "last_updated": datetime.now().isoformat()
            },
            "PROD_004": {
                "product_id": "PROD_004",
                "product_name": "Greek Yogurt",
                "category": "dairy",
                "current_stock": 32,
                "purchase_date": "2024-01-08",
                "expiry_date": "2024-01-20",
                "price": 4.49,
                "discount_rate": 0.0,
                "sales_velocity_7d": 9.2,
                "temperature": 38,
                "humidity": 48,
                "location": "Dairy Section A",
                "supplier": "Premium Dairy Co",
                "last_updated": datetime.now().isoformat()
            },
            "PROD_005": {
                "product_id": "PROD_005",
                "product_name": "Mixed Vegetables",
                "category": "produce",
                "current_stock": 28,
                "purchase_date": "2024-01-14",
                "expiry_date": "2024-01-18",
                "price": 3.79,
                "discount_rate": 0.10,
                "sales_velocity_7d": 7.1,
                "temperature": 68,
                "humidity": 62,
                "location": "Produce Section B",
                "supplier": "Garden Fresh Supplies",
                "last_updated": datetime.now().isoformat()
            }
        }
        
        logger.info(f"Loaded {len(self.inventory_data)} sample inventory items")
    
    def get_product_data(self, product_id: str) -> Optional[Dict[str, Any]]:
        """Get data for a specific product"""
        return self.inventory_data.get(product_id)
    
    def get_all_products(self) -> List[Dict[str, Any]]:
        """Get all products in inventory"""
        return list(self.inventory_data.values())
    
    def get_products_by_category(self, category: str) -> List[Dict[str, Any]]:
        """Get all products in a specific category"""
        return [
            product for product in self.inventory_data.values()
            if product['category'].lower() == category.lower()
        ]
    
    def get_expiring_products(self, days_threshold: int = 3) -> List[Dict[str, Any]]:
        """Get products expiring within the specified number of days"""
        expiring_products = []
        current_date = datetime.now()
        
        for product in self.inventory_data.values():
            expiry_date = datetime.strptime(product['expiry_date'], '%Y-%m-%d')
            days_until_expiry = (expiry_date - current_date).days
            
            if days_until_expiry <= days_threshold:
                product_copy = product.copy()
                product_copy['days_until_expiry'] = days_until_expiry
                expiring_products.append(product_copy)
        
        # Sort by days until expiry (most urgent first)
        expiring_products.sort(key=lambda x: x['days_until_expiry'])
        return expiring_products
    
    def get_overstocked_products(self, velocity_threshold: float = 5.0) -> List[Dict[str, Any]]:
        """Get products that are overstocked based on sales velocity"""
        overstocked_products = []
        
        for product in self.inventory_data.values():
            stock_velocity_ratio = product['current_stock'] / max(product['sales_velocity_7d'], 1)
            
            if stock_velocity_ratio > velocity_threshold:
                product_copy = product.copy()
                product_copy['stock_velocity_ratio'] = round(stock_velocity_ratio, 2)
                product_copy['days_of_inventory'] = round(stock_velocity_ratio, 1)
                overstocked_products.append(product_copy)
        
        # Sort by stock velocity ratio (most overstocked first)
        overstocked_products.sort(key=lambda x: x['stock_velocity_ratio'], reverse=True)
        return overstocked_products
    
    def update_product_stock(self, product_id: str, new_stock: int) -> bool:
        """Update the stock level for a product"""
        if product_id in self.inventory_data:
            self.inventory_data[product_id]['current_stock'] = new_stock
            self.inventory_data[product_id]['last_updated'] = datetime.now().isoformat()
            logger.info(f"Updated stock for {product_id} to {new_stock}")
            return True
        return False
    
    def update_product_discount(self, product_id: str, discount_rate: float) -> bool:
        """Update the discount rate for a product"""
        if product_id in self.inventory_data:
            self.inventory_data[product_id]['discount_rate'] = discount_rate
            self.inventory_data[product_id]['last_updated'] = datetime.now().isoformat()
            logger.info(f"Updated discount for {product_id} to {discount_rate:.1%}")
            return True
        return False
    
    def add_product(self, product_data: Dict[str, Any]) -> bool:
        """Add a new product to inventory"""
        try:
            product_id = product_data['product_id']
            product_data['last_updated'] = datetime.now().isoformat()
            self.inventory_data[product_id] = product_data
            logger.info(f"Added new product: {product_id}")
            return True
        except KeyError as e:
            logger.error(f"Missing required field when adding product: {e}")
            return False
    
    def remove_product(self, product_id: str) -> bool:
        """Remove a product from inventory"""
        if product_id in self.inventory_data:
            del self.inventory_data[product_id]
            logger.info(f"Removed product: {product_id}")
            return True
        return False
    
    def get_inventory_summary(self) -> Dict[str, Any]:
        """Get a summary of the current inventory status"""
        total_products = len(self.inventory_data)
        total_stock = sum(product['current_stock'] for product in self.inventory_data.values())
        
        # Category breakdown
        category_breakdown = {}
        for product in self.inventory_data.values():
            category = product['category']
            if category not in category_breakdown:
                category_breakdown[category] = {
                    'count': 0,
                    'total_stock': 0,
                    'avg_sales_velocity': 0
                }
            category_breakdown[category]['count'] += 1
            category_breakdown[category]['total_stock'] += product['current_stock']
            category_breakdown[category]['avg_sales_velocity'] += product['sales_velocity_7d']
        
        # Calculate averages
        for category_data in category_breakdown.values():
            if category_data['count'] > 0:
                category_data['avg_sales_velocity'] = round(
                    category_data['avg_sales_velocity'] / category_data['count'], 2
                )
        
        # Risk analysis
        expiring_soon = len(self.get_expiring_products(3))
        overstocked = len(self.get_overstocked_products(5.0))
        
        # Calculate total value
        total_value = sum(
            product['current_stock'] * product['price'] * (1 - product['discount_rate'])
            for product in self.inventory_data.values()
        )
        
        return {
            'total_products': total_products,
            'total_stock_units': total_stock,
            'total_inventory_value': round(total_value, 2),
            'category_breakdown': category_breakdown,
            'risk_indicators': {
                'expiring_soon_count': expiring_soon,
                'overstocked_count': overstocked,
                'high_risk_percentage': round((expiring_soon + overstocked) / max(total_products, 1) * 100, 1)
            },
            'last_updated': datetime.now().isoformat()
        }
    
    def get_products_needing_attention(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get products that need immediate attention"""
        return {
            'expiring_soon': self.get_expiring_products(2),
            'overstocked': self.get_overstocked_products(7.0),
            'low_velocity': [
                product for product in self.inventory_data.values()
                if product['sales_velocity_7d'] < 3.0
            ],
            'high_discount': [
                product for product in self.inventory_data.values()
                if product['discount_rate'] > 0.3
            ]
        }
    
    def simulate_sales_update(self, product_id: str, units_sold: int) -> bool:
        """Simulate a sales transaction and update inventory"""
        if product_id in self.inventory_data:
            product = self.inventory_data[product_id]
            
            # Update stock
            new_stock = max(0, product['current_stock'] - units_sold)
            product['current_stock'] = new_stock
            
            # Update sales velocity (simple moving average simulation)
            current_velocity = product['sales_velocity_7d']
            # Simulate daily sales impact
            daily_impact = units_sold / 7  # Spread over week
            new_velocity = (current_velocity * 6 + daily_impact) / 7
            product['sales_velocity_7d'] = round(new_velocity, 2)
            
            product['last_updated'] = datetime.now().isoformat()
            
            logger.info(f"Simulated sale: {units_sold} units of {product_id}, new stock: {new_stock}")
            return True
        return False
    
    def export_inventory_data(self, format_type: str = 'json') -> str:
        """Export inventory data in specified format"""
        if format_type.lower() == 'json':
            return json.dumps(self.inventory_data, indent=2)
        elif format_type.lower() == 'csv':
            # Convert to CSV format
            if not self.inventory_data:
                return ""
            
            # Get headers from first product
            headers = list(next(iter(self.inventory_data.values())).keys())
            csv_lines = [','.join(headers)]
            
            for product in self.inventory_data.values():
                row = [str(product.get(header, '')) for header in headers]
                csv_lines.append(','.join(row))
            
            return '\n'.join(csv_lines)
        else:
            raise ValueError(f"Unsupported format: {format_type}")
    
    def save_inventory_data(self, filepath: str = 'data/inventory.json'):
        """Save inventory data to file"""
        try:
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            with open(filepath, 'w') as f:
                json.dump(self.inventory_data, f, indent=2)
            logger.info(f"Inventory data saved to {filepath}")
        except Exception as e:
            logger.error(f"Error saving inventory data: {e}")
    
    def load_inventory_data(self, filepath: str = 'data/inventory.json'):
        """Load inventory data from file"""
        try:
            with open(filepath, 'r') as f:
                self.inventory_data = json.load(f)
            logger.info(f"Inventory data loaded from {filepath}")
        except FileNotFoundError:
            logger.warning(f"Inventory file not found: {filepath}, using sample data")
            self.load_sample_inventory()
        except Exception as e:
            logger.error(f"Error loading inventory data: {e}")
            self.load_sample_inventory()