"""
SmartWaste AI - Analytics and Reporting Service
Provides analytics, trends, and reporting capabilities
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import json
import os
from collections import defaultdict, deque
import statistics

logger = logging.getLogger(__name__)

class AnalyticsService:
    def __init__(self):
        self.prediction_history = deque(maxlen=10000)  # Store last 10k predictions
        self.waste_events = deque(maxlen=5000)  # Store waste events
        self.action_outcomes = deque(maxlen=5000)  # Store action results
        self.performance_metrics = {}
        self.load_historical_data()
    
    def load_historical_data(self):
        """Load historical analytics data"""
        try:
            if os.path.exists('data/analytics_history.json'):
                with open('data/analytics_history.json', 'r') as f:
                    data = json.load(f)
                    self.prediction_history = deque(data.get('predictions', []), maxlen=10000)
                    self.waste_events = deque(data.get('waste_events', []), maxlen=5000)
                    self.action_outcomes = deque(data.get('action_outcomes', []), maxlen=5000)
                logger.info("Loaded historical analytics data")
            else:
                self._generate_sample_historical_data()
        except Exception as e:
            logger.error(f"Error loading historical data: {e}")
            self._generate_sample_historical_data()
    
    def _generate_sample_historical_data(self):
        """Generate sample historical data for demonstration"""
        import random
        from datetime import datetime, timedelta
        
        # Generate sample predictions for the last 30 days
        base_date = datetime.now() - timedelta(days=30)
        categories = ['produce', 'dairy', 'bakery', 'meat', 'frozen']
        
        for i in range(200):  # 200 sample predictions
            prediction_date = base_date + timedelta(days=random.randint(0, 30))
            
            prediction = {
                'product_id': f'PROD_{random.randint(1, 50):03d}',
                'prediction_timestamp': prediction_date.isoformat(),
                'waste_probability': random.uniform(0.1, 0.9),
                'predicted_waste_amount': random.randint(1, 20),
                'recommended_action': random.choice(['keep', 'discount', 'donate', 'reroute']),
                'confidence_score': random.uniform(0.6, 0.95),
                'category': random.choice(categories),
                'days_until_expiry': random.randint(1, 14),
                'actual_outcome': random.choice(['prevented', 'wasted', 'sold', 'donated'])
            }
            
            self.prediction_history.append(prediction)
        
        # Generate sample waste events
        for i in range(50):
            waste_date = base_date + timedelta(days=random.randint(0, 30))
            
            waste_event = {
                'product_id': f'PROD_{random.randint(1, 50):03d}',
                'waste_date': waste_date.isoformat(),
                'waste_amount': random.randint(1, 15),
                'category': random.choice(categories),
                'reason': random.choice(['expired', 'damaged', 'overstocked', 'quality_issues']),
                'value_lost': random.uniform(5, 100),
                'was_predicted': random.choice([True, False])
            }
            
            self.waste_events.append(waste_event)
        
        logger.info("Generated sample historical data")
    
    def log_prediction(self, product_id: str, prediction_data: Dict[str, Any]):
        """Log a new prediction for analytics"""
        prediction_record = {
            'product_id': product_id,
            'prediction_timestamp': datetime.now().isoformat(),
            'waste_probability': prediction_data.get('waste_probability', 0),
            'predicted_waste_amount': prediction_data.get('predicted_waste_amount', 0),
            'recommended_action': prediction_data.get('recommended_action', 'keep'),
            'confidence_score': prediction_data.get('confidence_score', 0),
            'days_until_expiry': prediction_data.get('days_until_expiry', 0),
            'risk_factors': prediction_data.get('risk_factors', [])
        }
        
        self.prediction_history.append(prediction_record)
        logger.debug(f"Logged prediction for product {product_id}")
    
    def log_waste_event(self, product_id: str, waste_amount: int, category: str, 
                       reason: str, value_lost: float):
        """Log an actual waste event"""
        waste_record = {
            'product_id': product_id,
            'waste_date': datetime.now().isoformat(),
            'waste_amount': waste_amount,
            'category': category,
            'reason': reason,
            'value_lost': value_lost,
            'was_predicted': self._was_waste_predicted(product_id)
        }
        
        self.waste_events.append(waste_record)
        logger.info(f"Logged waste event: {waste_amount} units of {product_id}")
    
    def log_action_outcome(self, product_id: str, action_taken: str, outcome: str, 
                          value_recovered: float = 0):
        """Log the outcome of a recommended action"""
        outcome_record = {
            'product_id': product_id,
            'action_date': datetime.now().isoformat(),
            'action_taken': action_taken,
            'outcome': outcome,
            'value_recovered': value_recovered,
            'success': outcome in ['sold', 'donated', 'transferred']
        }
        
        self.action_outcomes.append(outcome_record)
        logger.info(f"Logged action outcome: {action_taken} -> {outcome} for {product_id}")
    
    def _was_waste_predicted(self, product_id: str) -> bool:
        """Check if waste was predicted for this product recently"""
        cutoff_date = datetime.now() - timedelta(days=7)
        
        for prediction in reversed(self.prediction_history):
            pred_date = datetime.fromisoformat(prediction['prediction_timestamp'])
            if pred_date < cutoff_date:
                break
            
            if (prediction['product_id'] == product_id and 
                prediction['waste_probability'] > 0.5):
                return True
        
        return False
    
    def get_risk_distribution(self) -> Dict[str, Any]:
        """Get current risk distribution across inventory"""
        if not self.prediction_history:
            return {'low': 0, 'medium': 0, 'high': 0, 'critical': 0}
        
        # Get recent predictions (last 24 hours)
        cutoff_date = datetime.now() - timedelta(hours=24)
        recent_predictions = []
        
        for prediction in reversed(self.prediction_history):
            pred_date = datetime.fromisoformat(prediction['prediction_timestamp'])
            if pred_date < cutoff_date:
                break
            recent_predictions.append(prediction)
        
        if not recent_predictions:
            return {'low': 0, 'medium': 0, 'high': 0, 'critical': 0}
        
        # Categorize by risk level
        risk_counts = {'low': 0, 'medium': 0, 'high': 0, 'critical': 0}
        
        for prediction in recent_predictions:
            waste_prob = prediction['waste_probability']
            days_until_expiry = prediction.get('days_until_expiry', 7)
            
            if waste_prob >= 0.8 or days_until_expiry <= 1:
                risk_counts['critical'] += 1
            elif waste_prob >= 0.6 or days_until_expiry <= 3:
                risk_counts['high'] += 1
            elif waste_prob >= 0.3 or days_until_expiry <= 7:
                risk_counts['medium'] += 1
            else:
                risk_counts['low'] += 1
        
        total = sum(risk_counts.values())
        if total == 0:
            return risk_counts
        
        # Convert to percentages
        risk_percentages = {
            level: round((count / total) * 100, 1)
            for level, count in risk_counts.items()
        }
        
        return {
            'counts': risk_counts,
            'percentages': risk_percentages,
            'total_products': total
        }
    
    def get_recent_predictions(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get the most recent predictions"""
        recent = list(self.prediction_history)[-limit:]
        return sorted(recent, key=lambda x: x['prediction_timestamp'], reverse=True)
    
    def get_latest_prediction(self, product_id: str) -> Optional[Dict[str, Any]]:
        """Get the latest prediction for a specific product"""
        for prediction in reversed(self.prediction_history):
            if prediction['product_id'] == product_id:
                return prediction
        return None
    
    def get_waste_trends(self, days: int = 30, category: Optional[str] = None) -> Dict[str, Any]:
        """Get waste trends over the specified period"""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # Filter waste events
        relevant_events = []
        for event in self.waste_events:
            event_date = datetime.fromisoformat(event['waste_date'])
            if event_date >= cutoff_date:
                if category is None or event['category'] == category:
                    relevant_events.append(event)
        
        if not relevant_events:
            return {
                'total_waste_amount': 0,
                'total_value_lost': 0,
                'daily_averages': {},
                'category_breakdown': {},
                'trend_direction': 'stable'
            }
        
        # Calculate totals
        total_waste = sum(event['waste_amount'] for event in relevant_events)
        total_value_lost = sum(event['value_lost'] for event in relevant_events)
        
        # Daily breakdown
        daily_waste = defaultdict(int)
        daily_value = defaultdict(float)
        
        for event in relevant_events:
            date_key = event['waste_date'][:10]  # YYYY-MM-DD
            daily_waste[date_key] += event['waste_amount']
            daily_value[date_key] += event['value_lost']
        
        # Category breakdown
        category_breakdown = defaultdict(lambda: {'amount': 0, 'value': 0, 'count': 0})
        for event in relevant_events:
            cat = event['category']
            category_breakdown[cat]['amount'] += event['waste_amount']
            category_breakdown[cat]['value'] += event['value_lost']
            category_breakdown[cat]['count'] += 1
        
        # Calculate trend direction
        if len(daily_waste) >= 7:
            recent_week = list(daily_waste.values())[-7:]
            previous_week = list(daily_waste.values())[-14:-7] if len(daily_waste) >= 14 else []
            
            if previous_week:
                recent_avg = statistics.mean(recent_week)
                previous_avg = statistics.mean(previous_week)
                
                if recent_avg > previous_avg * 1.1:
                    trend_direction = 'increasing'
                elif recent_avg < previous_avg * 0.9:
                    trend_direction = 'decreasing'
                else:
                    trend_direction = 'stable'
            else:
                trend_direction = 'insufficient_data'
        else:
            trend_direction = 'insufficient_data'
        
        return {
            'total_waste_amount': total_waste,
            'total_value_lost': round(total_value_lost, 2),
            'average_daily_waste': round(total_waste / max(days, 1), 2),
            'average_daily_value_lost': round(total_value_lost / max(days, 1), 2),
            'daily_breakdown': dict(daily_waste),
            'category_breakdown': dict(category_breakdown),
            'trend_direction': trend_direction,
            'prediction_accuracy': self._calculate_prediction_accuracy(days)
        }
    
    def _calculate_prediction_accuracy(self, days: int) -> Dict[str, float]:
        """Calculate prediction accuracy over the specified period"""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # Get predictions and actual outcomes
        correct_predictions = 0
        total_predictions = 0
        
        for prediction in self.prediction_history:
            pred_date = datetime.fromisoformat(prediction['prediction_timestamp'])
            if pred_date < cutoff_date:
                continue
            
            total_predictions += 1
            
            # Check if there was an actual waste event for this product
            product_id = prediction['product_id']
            predicted_waste = prediction['waste_probability'] > 0.5
            
            # Look for actual waste events within a reasonable timeframe
            actual_waste = False
            for event in self.waste_events:
                event_date = datetime.fromisoformat(event['waste_date'])
                if (event['product_id'] == product_id and 
                    abs((event_date - pred_date).days) <= 7):
                    actual_waste = True
                    break
            
            if predicted_waste == actual_waste:
                correct_predictions += 1
        
        accuracy = correct_predictions / max(total_predictions, 1)
        
        return {
            'overall_accuracy': round(accuracy, 3),
            'correct_predictions': correct_predictions,
            'total_predictions': total_predictions
        }
    
    def get_action_effectiveness(self) -> Dict[str, Any]:
        """Analyze the effectiveness of different actions"""
        if not self.action_outcomes:
            return {}
        
        action_stats = defaultdict(lambda: {
            'total_attempts': 0,
            'successful_outcomes': 0,
            'total_value_recovered': 0,
            'success_rate': 0
        })
        
        for outcome in self.action_outcomes:
            action = outcome['action_taken']
            action_stats[action]['total_attempts'] += 1
            
            if outcome['success']:
                action_stats[action]['successful_outcomes'] += 1
            
            action_stats[action]['total_value_recovered'] += outcome.get('value_recovered', 0)
        
        # Calculate success rates
        for action, stats in action_stats.items():
            if stats['total_attempts'] > 0:
                stats['success_rate'] = round(
                    stats['successful_outcomes'] / stats['total_attempts'], 3
                )
        
        return dict(action_stats)
    
    def export_predictions(self, days: int = 7, format_type: str = 'json') -> Any:
        """Export predictions data for the specified period"""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        relevant_predictions = []
        for prediction in self.prediction_history:
            pred_date = datetime.fromisoformat(prediction['prediction_timestamp'])
            if pred_date >= cutoff_date:
                relevant_predictions.append(prediction)
        
        if format_type.lower() == 'json':
            return relevant_predictions
        elif format_type.lower() == 'csv':
            if not relevant_predictions:
                return ""
            
            # Convert to CSV
            headers = list(relevant_predictions[0].keys())
            csv_lines = [','.join(headers)]
            
            for prediction in relevant_predictions:
                row = [str(prediction.get(header, '')) for header in headers]
                csv_lines.append(','.join(row))
            
            return '\n'.join(csv_lines)
        else:
            raise ValueError(f"Unsupported format: {format_type}")
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get overall performance summary"""
        total_predictions = len(self.prediction_history)
        total_waste_events = len(self.waste_events)
        total_actions = len(self.action_outcomes)
        
        # Calculate recent metrics (last 7 days)
        recent_trends = self.get_waste_trends(7)
        action_effectiveness = self.get_action_effectiveness()
        
        # Calculate waste prevention rate
        prevented_waste = sum(
            1 for outcome in self.action_outcomes
            if outcome['outcome'] in ['sold', 'donated', 'transferred']
        )
        
        prevention_rate = prevented_waste / max(total_actions, 1)
        
        return {
            'total_predictions_made': total_predictions,
            'total_waste_events': total_waste_events,
            'total_actions_taken': total_actions,
            'waste_prevention_rate': round(prevention_rate, 3),
            'recent_trends': recent_trends,
            'action_effectiveness': action_effectiveness,
            'last_updated': datetime.now().isoformat()
        }
    
    def save_analytics_data(self, filepath: str = 'data/analytics_history.json'):
        """Save analytics data to file"""
        try:
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
            data = {
                'predictions': list(self.prediction_history),
                'waste_events': list(self.waste_events),
                'action_outcomes': list(self.action_outcomes),
                'last_saved': datetime.now().isoformat()
            }
            
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)
            
            logger.info(f"Analytics data saved to {filepath}")
        except Exception as e:
            logger.error(f"Error saving analytics data: {e}")