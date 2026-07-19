"""
Reorder Optimizer
Generates intelligent reorder recommendations based on demand forecast
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import math

logger = logging.getLogger(__name__)

class ReorderRecommendation:
    """Represents a reorder recommendation"""
    
    def __init__(self, product_id: str, product_name: str, current_stock: int,
                 recommended_quantity: int, reorder_date: str, urgency: str,
                 reason: str, estimated_stockout_date: Optional[str] = None):
        """Initialize recommendation"""
        self.product_id = product_id
        self.product_name = product_name
        self.current_stock = current_stock
        self.recommended_quantity = recommended_quantity
        self.reorder_date = reorder_date
        self.urgency = urgency
        self.reason = reason
        self.estimated_stockout_date = estimated_stockout_date
        self.created_at = datetime.now()
        self.executed = False
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'product_id': self.product_id,
            'product_name': self.product_name,
            'current_stock': self.current_stock,
            'recommended_quantity': self.recommended_quantity,
            'reorder_date': self.reorder_date,
            'urgency': self.urgency,
            'reason': self.reason,
            'estimated_stockout_date': self.estimated_stockout_date,
            'created_at': self.created_at.isoformat(),
            'executed': self.executed
        }

class ReorderOptimizer:
    """Generates optimal reorder recommendations"""
    
    def __init__(self, reorder_point: int = 15, safety_stock: int = 5,
                 lead_time_days: int = 7, holding_cost_per_unit: float = 0.5):
        """
        Initialize reorder optimizer
        
        Args:
            reorder_point: Stock level that triggers reorder
            safety_stock: Buffer stock to maintain
            lead_time_days: Supplier lead time
            holding_cost_per_unit: Cost to hold one unit per day
        """
        self.reorder_point = reorder_point
        self.safety_stock = safety_stock
        self.lead_time_days = lead_time_days
        self.holding_cost_per_unit = holding_cost_per_unit
        self.recommendations = []
        
        logger.info(f"Reorder optimizer initialized: reorder_point={reorder_point}, "
                   f"safety_stock={safety_stock}, lead_time={lead_time_days} days")
    
    def calculate_eoq(self, annual_demand: int, order_cost: float, holding_cost: float) -> int:
        """
        Calculate Economic Order Quantity (EOQ)
        
        Args:
            annual_demand: Annual demand for product
            order_cost: Cost per order
            holding_cost: Annual holding cost per unit
            
        Returns:
            Optimal order quantity
        """
        if holding_cost == 0:
            return max(1, int(annual_demand / 12))
        
        eoq = math.sqrt((2 * annual_demand * order_cost) / holding_cost)
        return max(1, int(eoq))
    
    def estimate_stockout_date(self, current_stock: int, daily_demand: float) -> Optional[str]:
        """
        Estimate when stock will run out
        
        Args:
            current_stock: Current inventory level
            daily_demand: Average daily demand
            
        Returns:
            Estimated stockout date or None
        """
        if daily_demand <= 0:
            return None
        
        days_until_stockout = current_stock / daily_demand
        stockout_date = datetime.now() + timedelta(days=days_until_stockout)
        
        return stockout_date.strftime('%Y-%m-%d') if days_until_stockout > 0 else "IMMEDIATE"
    
    def generate_recommendation(self, product_id: str, product_name: str,
                              current_stock: int, forecast_data: Dict) -> Optional[ReorderRecommendation]:
        """
        Generate reorder recommendation for a product
        
        Args:
            product_id: Product ID
            product_name: Product name
            current_stock: Current stock level
            forecast_data: Forecast statistics
            
        Returns:
            ReorderRecommendation or None
        """
        
        avg_daily_demand = forecast_data.get('statistics', {}).get('average_daily_demand', 0)
        
        # Calculate when reorder should arrive
        reorder_arrival_date = datetime.now() + timedelta(days=self.lead_time_days)
        days_until_arrival = self.lead_time_days
        
        # Calculate demand during lead time
        demand_during_lead_time = avg_daily_demand * days_until_arrival
        stock_at_arrival = current_stock - demand_during_lead_time
        
        # Determine if reorder is needed
        needs_reorder = stock_at_arrival <= self.reorder_point
        
        if not needs_reorder:
            return None
        
        # Calculate recommended quantity
        # Target: maintain safety stock + enough for 30 days
        target_stock = self.safety_stock + (avg_daily_demand * 30)
        recommended_quantity = max(1, int(target_stock - stock_at_arrival))
        
        # Determine urgency
        if current_stock <= self.safety_stock:
            urgency = "CRITICAL"
            reason = "Stock critically low - immediate reorder required"
            reorder_date = datetime.now().strftime('%Y-%m-%d')
        elif stock_at_arrival <= self.safety_stock:
            urgency = "HIGH"
            reason = "Stock will drop below safety level during lead time"
            reorder_date = datetime.now().strftime('%Y-%m-%d')
        else:
            urgency = "NORMAL"
            reason = "Scheduled reorder to maintain optimal stock level"
            reorder_date = (datetime.now() + timedelta(days=2)).strftime('%Y-%m-%d')
        
        # Estimate stockout date
        estimated_stockout = self.estimate_stockout_date(current_stock, avg_daily_demand)
        
        recommendation = ReorderRecommendation(
            product_id=product_id,
            product_name=product_name,
            current_stock=current_stock,
            recommended_quantity=recommended_quantity,
            reorder_date=reorder_date,
            urgency=urgency,
            reason=reason,
            estimated_stockout_date=estimated_stockout
        )
        
        logger.info(f"Generated {urgency} reorder recommendation for {product_name}: "
                   f"reorder {recommended_quantity} units")
        
        return recommendation
    
    def generate_batch_recommendations(self, products_data: List[Dict]) -> List[ReorderRecommendation]:
        """
        Generate reorder recommendations for multiple products
        
        Args:
            products_data: List of product data with current stock and forecasts
            
        Returns:
            List of recommendations
        """
        logger.info(f"Generating reorder recommendations for {len(products_data)} products")
        
        recommendations = []
        
        for product in products_data:
            recommendation = self.generate_recommendation(
                product_id=product['product_id'],
                product_name=product.get('product_name', 'Unknown'),
                current_stock=product['current_stock'],
                forecast_data=product.get('forecast_data', {})
            )
            
            if recommendation:
                self.recommendations.append(recommendation)
                recommendations.append(recommendation)
        
        # Sort by urgency
        urgency_order = {'CRITICAL': 0, 'HIGH': 1, 'NORMAL': 2}
        recommendations.sort(key=lambda r: urgency_order.get(r.urgency, 3))
        
        return recommendations
    
    def get_recommendations(self, urgency_filter: Optional[str] = None) -> List[Dict]:
        """
        Get current recommendations
        
        Args:
            urgency_filter: Filter by urgency level (optional)
            
        Returns:
            List of recommendation dictionaries
        """
        recommendations = self.recommendations
        
        if urgency_filter:
            recommendations = [r for r in recommendations if r.urgency == urgency_filter]
        
        return [r.to_dict() for r in recommendations]
    
    def execute_recommendation(self, product_id: str) -> bool:
        """Mark recommendation as executed"""
        for rec in self.recommendations:
            if rec.product_id == product_id:
                rec.executed = True
                logger.info(f"Recommendation executed for {product_id}")
                return True
        return False
    
    def clear_recommendations(self) -> None:
        """Clear all recommendations"""
        self.recommendations = []
        logger.info("Recommendations cleared")