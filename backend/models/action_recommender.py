"""
SmartWaste AI - Action Recommendation Engine
Intelligent system for recommending actions based on waste predictions
"""

import logging
from datetime import datetime
from typing import Dict, List, Any

logger = logging.getLogger(__name__)

class ActionRecommender:
    def __init__(self):
        self.action_rules = {}
        self.category_specific_rules = {}
        self.discount_calculator = DiscountCalculator()
        
    def initialize_rules(self):
        """Initialize action recommendation rules"""
        self.action_rules = {
            'donate': {
                'conditions': {
                    'waste_probability': 0.8,
                    'days_until_expiry': 2,
                    'stock_velocity_ratio': 8
                },
                'priority': 1,
                'description': 'Product is very likely to expire with high stock levels'
            },
            'discount': {
                'conditions': {
                    'waste_probability': 0.5,
                    'days_until_expiry': 5,
                    'stock_velocity_ratio': 4
                },
                'priority': 2,
                'description': 'Product has moderate waste risk and can benefit from discounting'
            },
            'reroute': {
                'conditions': {
                    'waste_probability': 0.3,
                    'days_until_expiry': 7,
                    'stock_velocity_ratio': 6
                },
                'priority': 3,
                'description': 'Product is overstocked but still fresh enough for redistribution'
            },
            'keep': {
                'conditions': {
                    'waste_probability': 0.3,
                    'days_until_expiry': 3,
                    'stock_velocity_ratio': 3
                },
                'priority': 4,
                'description': 'Product is performing well with low waste risk'
            }
        }
        
        # Category-specific adjustments
        self.category_specific_rules = {
            'produce': {
                'donate_threshold_days': 1,
                'discount_threshold_days': 3,
                'reroute_threshold_days': 5,
                'urgency_multiplier': 1.5
            },
            'dairy': {
                'donate_threshold_days': 2,
                'discount_threshold_days': 5,
                'reroute_threshold_days': 10,
                'urgency_multiplier': 1.2
            },
            'bakery': {
                'donate_threshold_days': 1,
                'discount_threshold_days': 2,
                'reroute_threshold_days': 3,
                'urgency_multiplier': 1.8
            },
            'meat': {
                'donate_threshold_days': 1,
                'discount_threshold_days': 3,
                'reroute_threshold_days': 5,
                'urgency_multiplier': 1.4
            },
            'frozen': {
                'donate_threshold_days': 7,
                'discount_threshold_days': 14,
                'reroute_threshold_days': 30,
                'urgency_multiplier': 0.8
            }
        }
        
        logger.info("Action recommendation rules initialized")

    def recommend_action(self, waste_probability: float, days_until_expiry: int,
                        current_stock: int, sales_velocity: float, category: str) -> Dict[str, Any]:
        """
        Recommend the best action for a product based on its risk factors
        
        Args:
            waste_probability: Predicted probability of waste (0-1)
            days_until_expiry: Days until product expires
            current_stock: Current inventory level
            sales_velocity: Average daily sales
            category: Product category
            
        Returns:
            Dict containing recommended action, urgency, reasoning, and additional details
        """
        try:
            # Calculate key metrics
            stock_velocity_ratio = current_stock / max(sales_velocity, 1)
            
            # Get category-specific rules
            category_rules = self.category_specific_rules.get(category, self.category_specific_rules['produce'])
            
            # Determine action based on rules and thresholds
            action, urgency, reasoning = self._evaluate_action_rules(
                waste_probability, days_until_expiry, stock_velocity_ratio, category_rules
            )
            
            # Calculate suggested discount if action is discount
            suggested_discount = 0
            if action == 'discount':
                suggested_discount = self.discount_calculator.calculate_optimal_discount(
                    waste_probability, days_until_expiry, category, current_stock, sales_velocity
                )
            
            # Generate detailed reasoning
            detailed_reasoning = self._generate_detailed_reasoning(
                action, waste_probability, days_until_expiry, stock_velocity_ratio, category
            )
            
            # Calculate action timeline
            timeline = self._calculate_action_timeline(action, days_until_expiry, urgency)
            
            return {
                'action': action,
                'urgency': urgency,
                'suggested_discount': suggested_discount,
                'reasoning': detailed_reasoning,
                'timeline': timeline,
                'confidence': self._calculate_confidence(waste_probability, days_until_expiry),
                'alternative_actions': self._get_alternative_actions(action, waste_probability, days_until_expiry),
                'recommendation_timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in action recommendation: {str(e)}")
            return {
                'action': 'monitor',
                'urgency': 'low',
                'suggested_discount': 0,
                'reasoning': ['Error in recommendation system - defaulting to monitoring'],
                'timeline': {'immediate': [], 'short_term': [], 'long_term': []},
                'confidence': 0.5,
                'error': str(e)
            }

    def _evaluate_action_rules(self, waste_probability: float, days_until_expiry: int,
                              stock_velocity_ratio: float, category_rules: Dict) -> tuple:
        """Evaluate which action to recommend based on rules"""
        
        # Apply urgency multiplier for category
        urgency_factor = category_rules['urgency_multiplier']
        
        # Determine action based on thresholds
        if (days_until_expiry <= category_rules['donate_threshold_days'] and 
            waste_probability >= 0.8 and stock_velocity_ratio >= 8):
            return 'donate', 'critical', ['Very high waste risk with imminent expiry']
            
        elif (days_until_expiry <= category_rules['donate_threshold_days'] and 
              waste_probability >= 0.7):
            return 'donate', 'high', ['High waste risk with very short shelf life']
            
        elif (days_until_expiry <= category_rules['discount_threshold_days'] and 
              waste_probability >= 0.5):
            urgency = 'high' if urgency_factor > 1.2 else 'medium'
            return 'discount', urgency, ['Moderate to high waste risk - discounting can help move inventory']
            
        elif (days_until_expiry <= category_rules['discount_threshold_days'] and 
              stock_velocity_ratio >= 5):
            return 'discount', 'medium', ['Overstocked with approaching expiry']
            
        elif (days_until_expiry <= category_rules['reroute_threshold_days'] and 
              stock_velocity_ratio >= 6 and waste_probability >= 0.3):
            return 'reroute', 'medium', ['Overstocked but still fresh - consider redistribution']
            
        elif waste_probability >= 0.6:
            return 'discount', 'high', ['High waste probability requires immediate action']
            
        elif waste_probability >= 0.4:
            return 'discount', 'medium', ['Moderate waste risk - preventive discounting recommended']
            
        elif stock_velocity_ratio >= 8:
            return 'reroute', 'low', ['Significantly overstocked - consider redistribution']
            
        else:
            return 'keep', 'low', ['Low waste risk - continue monitoring']

    def _generate_detailed_reasoning(self, action: str, waste_probability: float,
                                   days_until_expiry: int, stock_velocity_ratio: float,
                                   category: str) -> List[str]:
        """Generate detailed reasoning for the recommended action"""
        reasoning = []
        
        # Waste probability reasoning
        if waste_probability >= 0.8:
            reasoning.append(f"Very high waste probability ({waste_probability:.1%}) indicates urgent action needed")
        elif waste_probability >= 0.6:
            reasoning.append(f"High waste probability ({waste_probability:.1%}) suggests significant risk")
        elif waste_probability >= 0.4:
            reasoning.append(f"Moderate waste probability ({waste_probability:.1%}) warrants preventive measures")
        else:
            reasoning.append(f"Low waste probability ({waste_probability:.1%}) indicates manageable risk")
        
        # Expiry timing reasoning
        if days_until_expiry <= 1:
            reasoning.append("Product expires within 24 hours - immediate action critical")
        elif days_until_expiry <= 3:
            reasoning.append(f"Product expires in {days_until_expiry} days - time-sensitive situation")
        elif days_until_expiry <= 7:
            reasoning.append(f"Product expires in {days_until_expiry} days - proactive measures recommended")
        
        # Stock level reasoning
        if stock_velocity_ratio >= 10:
            reasoning.append("Severely overstocked relative to sales velocity")
        elif stock_velocity_ratio >= 6:
            reasoning.append("Moderately overstocked - inventory levels exceed normal sales pace")
        elif stock_velocity_ratio >= 3:
            reasoning.append("Slightly overstocked but manageable")
        
        # Category-specific reasoning
        category_insights = {
            'produce': "Fresh produce requires rapid action due to short shelf life",
            'dairy': "Dairy products have moderate shelf life but strict temperature requirements",
            'bakery': "Baked goods have very short shelf life and lose quality quickly",
            'meat': "Meat products require careful handling due to safety concerns",
            'frozen': "Frozen products have extended shelf life but high storage costs"
        }
        
        if category in category_insights:
            reasoning.append(category_insights[category])
        
        # Action-specific reasoning
        action_explanations = {
            'donate': "Donation maximizes social impact while minimizing total loss",
            'discount': "Strategic discounting can recover partial value while moving inventory",
            'reroute': "Redistribution to high-demand locations can optimize sales",
            'keep': "Current strategy is working well - maintain monitoring"
        }
        
        reasoning.append(action_explanations.get(action, "Recommended action based on risk assessment"))
        
        return reasoning

    def _calculate_action_timeline(self, action: str, days_until_expiry: int, urgency: str) -> Dict[str, List[str]]:
        """Calculate timeline for implementing the recommended action"""
        timeline = {
            'immediate': [],
            'short_term': [],
            'long_term': []
        }
        
        if action == 'donate':
            if urgency == 'critical':
                timeline['immediate'] = [
                    'Contact NGO partners immediately',
                    'Prepare donation documentation',
                    'Arrange pickup within 2-4 hours'
                ]
            else:
                timeline['immediate'] = ['Contact NGO partners']
                timeline['short_term'] = ['Schedule pickup within 24 hours', 'Prepare donation paperwork']
                
        elif action == 'discount':
            if urgency == 'high':
                timeline['immediate'] = [
                    'Apply discount immediately',
                    'Update pricing systems',
                    'Notify customers via app/email'
                ]
            else:
                timeline['immediate'] = ['Calculate optimal discount percentage']
                timeline['short_term'] = ['Implement discount within 4-8 hours', 'Monitor sales response']
                
        elif action == 'reroute':
            timeline['immediate'] = ['Identify target locations with higher demand']
            timeline['short_term'] = ['Arrange transportation', 'Update inventory systems']
            timeline['long_term'] = ['Monitor performance at new location']
            
        elif action == 'keep':
            timeline['immediate'] = ['Continue current monitoring']
            timeline['short_term'] = ['Review sales performance daily']
            timeline['long_term'] = ['Reassess if conditions change']
        
        return timeline

    def _calculate_confidence(self, waste_probability: float, days_until_expiry: int) -> float:
        """Calculate confidence in the recommendation"""
        base_confidence = 0.7
        
        # Higher confidence for extreme cases
        if waste_probability >= 0.8 or days_until_expiry <= 1:
            base_confidence += 0.2
        elif waste_probability >= 0.6 or days_until_expiry <= 3:
            base_confidence += 0.1
        
        # Lower confidence for edge cases
        if 0.3 <= waste_probability <= 0.5:
            base_confidence -= 0.1
        
        return min(0.95, max(0.5, base_confidence))

    def _get_alternative_actions(self, primary_action: str, waste_probability: float,
                               days_until_expiry: int) -> List[Dict[str, Any]]:
        """Get alternative actions with their feasibility"""
        alternatives = []
        
        if primary_action != 'discount':
            alternatives.append({
                'action': 'discount',
                'feasibility': 'high' if waste_probability >= 0.4 else 'medium',
                'description': 'Apply strategic discount to accelerate sales'
            })
        
        if primary_action != 'donate' and days_until_expiry <= 3:
            alternatives.append({
                'action': 'donate',
                'feasibility': 'high' if waste_probability >= 0.7 else 'medium',
                'description': 'Donate to local food banks or charities'
            })
        
        if primary_action != 'reroute' and days_until_expiry >= 3:
            alternatives.append({
                'action': 'reroute',
                'feasibility': 'medium',
                'description': 'Transfer to locations with higher demand'
            })
        
        return alternatives


class DiscountCalculator:
    """Calculate optimal discount percentages based on various factors"""
    
    def calculate_optimal_discount(self, waste_probability: float, days_until_expiry: int,
                                 category: str, current_stock: int, sales_velocity: float) -> int:
        """Calculate the optimal discount percentage"""
        
        # Base discount based on waste probability
        base_discount = min(70, waste_probability * 80)
        
        # Urgency multiplier based on days until expiry
        if days_until_expiry <= 1:
            urgency_multiplier = 1.5
        elif days_until_expiry <= 3:
            urgency_multiplier = 1.3
        elif days_until_expiry <= 7:
            urgency_multiplier = 1.1
        else:
            urgency_multiplier = 1.0
        
        # Category-specific adjustments
        category_multipliers = {
            'produce': 1.2,
            'bakery': 1.3,
            'dairy': 1.1,
            'meat': 1.15,
            'frozen': 0.9
        }
        
        category_multiplier = category_multipliers.get(category, 1.0)
        
        # Stock level adjustment
        stock_velocity_ratio = current_stock / max(sales_velocity, 1)
        if stock_velocity_ratio >= 10:
            stock_multiplier = 1.2
        elif stock_velocity_ratio >= 6:
            stock_multiplier = 1.1
        else:
            stock_multiplier = 1.0
        
        # Calculate final discount
        final_discount = base_discount * urgency_multiplier * category_multiplier * stock_multiplier
        
        # Round to nearest 5% and cap at 70%
        final_discount = min(70, max(5, round(final_discount / 5) * 5))
        
        return int(final_discount)