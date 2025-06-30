"""
SmartWaste AI - Response Formatting Utilities
Standardizes API response formats and handles error formatting
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class ResponseFormatter:
    def __init__(self):
        self.api_version = "1.0.0"
    
    def format_prediction_response(self, predictions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Format prediction results into standardized response
        
        Args:
            predictions: List of prediction dictionaries
            
        Returns:
            Formatted response dictionary
        """
        # Calculate summary statistics
        total_products = len(predictions)
        high_risk_count = sum(1 for p in predictions if p.get('waste_probability', 0) > 0.6)
        
        # Group by recommended actions
        action_summary = {}
        for prediction in predictions:
            action = prediction.get('recommended_action', 'unknown')
            if action not in action_summary:
                action_summary[action] = 0
            action_summary[action] += 1
        
        # Calculate total predicted waste
        total_predicted_waste = sum(p.get('predicted_waste_amount', 0) for p in predictions)
        
        return {
            "status": "success",
            "api_version": self.api_version,
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_products_analyzed": total_products,
                "high_risk_products": high_risk_count,
                "total_predicted_waste_units": total_predicted_waste,
                "action_breakdown": action_summary
            },
            "predictions": predictions,
            "metadata": {
                "processing_time_ms": None,  # Could be added by middleware
                "model_version": "1.0.0",
                "confidence_threshold": 0.5
            }
        }
    
    def format_error_response(self, error_message: str, error_code: str = "GENERAL_ERROR",
                            details: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Format error response
        
        Args:
            error_message: Human-readable error message
            error_code: Machine-readable error code
            details: Additional error details
            
        Returns:
            Formatted error response
        """
        response = {
            "status": "error",
            "api_version": self.api_version,
            "timestamp": datetime.now().isoformat(),
            "error": {
                "code": error_code,
                "message": error_message
            }
        }
        
        if details:
            response["error"]["details"] = details
        
        return response
    
    def format_validation_error_response(self, validation_errors: List[str]) -> Dict[str, Any]:
        """
        Format validation error response
        
        Args:
            validation_errors: List of validation error messages
            
        Returns:
            Formatted validation error response
        """
        return self.format_error_response(
            error_message="Validation failed",
            error_code="VALIDATION_ERROR",
            details={
                "validation_errors": validation_errors,
                "error_count": len(validation_errors)
            }
        )
    
    def format_success_response(self, data: Any, message: str = "Operation completed successfully") -> Dict[str, Any]:
        """
        Format generic success response
        
        Args:
            data: Response data
            message: Success message
            
        Returns:
            Formatted success response
        """
        return {
            "status": "success",
            "api_version": self.api_version,
            "timestamp": datetime.now().isoformat(),
            "message": message,
            "data": data
        }
    
    def format_analytics_response(self, analytics_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format analytics data response
        
        Args:
            analytics_data: Analytics data dictionary
            
        Returns:
            Formatted analytics response
        """
        return {
            "status": "success",
            "api_version": self.api_version,
            "timestamp": datetime.now().isoformat(),
            "analytics": analytics_data,
            "metadata": {
                "data_freshness": "real-time",
                "calculation_method": "statistical_analysis"
            }
        }
    
    def format_inventory_response(self, inventory_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format inventory data response
        
        Args:
            inventory_data: Inventory data dictionary
            
        Returns:
            Formatted inventory response
        """
        return {
            "status": "success",
            "api_version": self.api_version,
            "timestamp": datetime.now().isoformat(),
            "inventory": inventory_data,
            "metadata": {
                "last_updated": inventory_data.get('last_updated'),
                "data_source": "inventory_management_system"
            }
        }
    
    def format_action_recommendations_response(self, recommendations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Format action recommendations response
        
        Args:
            recommendations: List of action recommendation dictionaries
            
        Returns:
            Formatted recommendations response
        """
        # Calculate summary statistics
        total_recommendations = len(recommendations)
        urgency_breakdown = {}
        action_breakdown = {}
        
        for rec in recommendations:
            urgency = rec.get('urgency', 'unknown')
            action = rec.get('recommended_action', 'unknown')
            
            urgency_breakdown[urgency] = urgency_breakdown.get(urgency, 0) + 1
            action_breakdown[action] = action_breakdown.get(action, 0) + 1
        
        return {
            "status": "success",
            "api_version": self.api_version,
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_recommendations": total_recommendations,
                "urgency_breakdown": urgency_breakdown,
                "action_breakdown": action_breakdown
            },
            "recommendations": recommendations,
            "metadata": {
                "recommendation_engine_version": "1.0.0",
                "generated_at": datetime.now().isoformat()
            }
        }
    
    def format_model_performance_response(self, performance_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format model performance response
        
        Args:
            performance_data: Model performance metrics
            
        Returns:
            Formatted performance response
        """
        return {
            "status": "success",
            "api_version": self.api_version,
            "timestamp": datetime.now().isoformat(),
            "performance": performance_data,
            "metadata": {
                "metrics_calculated_at": datetime.now().isoformat(),
                "evaluation_method": "cross_validation"
            }
        }
    
    def add_pagination_metadata(self, response: Dict[str, Any], page: int, limit: int,
                              total_items: int) -> Dict[str, Any]:
        """
        Add pagination metadata to response
        
        Args:
            response: Existing response dictionary
            page: Current page number
            limit: Items per page
            total_items: Total number of items
            
        Returns:
            Response with pagination metadata
        """
        total_pages = (total_items + limit - 1) // limit  # Ceiling division
        
        pagination = {
            "current_page": page,
            "items_per_page": limit,
            "total_items": total_items,
            "total_pages": total_pages,
            "has_next_page": page < total_pages,
            "has_previous_page": page > 1
        }
        
        if "metadata" not in response:
            response["metadata"] = {}
        
        response["metadata"]["pagination"] = pagination
        return response
    
    def format_export_response(self, data: Any, export_format: str, filename: str) -> Dict[str, Any]:
        """
        Format data export response
        
        Args:
            data: Exported data
            export_format: Format of the export (json, csv, etc.)
            filename: Suggested filename
            
        Returns:
            Formatted export response
        """
        return {
            "status": "success",
            "api_version": self.api_version,
            "timestamp": datetime.now().isoformat(),
            "export": {
                "format": export_format,
                "filename": filename,
                "data": data
            },
            "metadata": {
                "export_generated_at": datetime.now().isoformat(),
                "data_size": len(str(data)) if isinstance(data, (str, list, dict)) else None
            }
        }
    
    def sanitize_response_data(self, data: Any) -> Any:
        """
        Sanitize response data to ensure it's JSON serializable
        
        Args:
            data: Data to sanitize
            
        Returns:
            Sanitized data
        """
        if isinstance(data, dict):
            return {key: self.sanitize_response_data(value) for key, value in data.items()}
        elif isinstance(data, list):
            return [self.sanitize_response_data(item) for item in data]
        elif isinstance(data, (str, int, float, bool)) or data is None:
            return data
        elif hasattr(data, 'isoformat'):  # datetime objects
            return data.isoformat()
        else:
            # Convert other types to string
            return str(data)