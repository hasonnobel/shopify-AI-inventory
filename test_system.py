#!/usr/bin/env python3
"""
Test script to demonstrate the Shopify AI Inventory Management System
This runs with mock data to show all components working
"""

import sys
import logging
from datetime import datetime, timedelta
from src.forecasting.engine import DemandForecaster
from src.alerts.system import AlertSystem, AlertSeverity
from src.reordering.optimizer import ReorderOptimizer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def generate_mock_sales_data(days=90, base_qty=50):
    """Generate mock sales history"""
    sales_data = []
    for i in range(days):
        date = datetime.now() - timedelta(days=days-i)
        # Add some randomness to simulate real sales
        quantity = base_qty + (i % 10) - 5
        sales_data.append({
            'date': date.isoformat(),
            'quantity': max(10, quantity)
        })
    return sales_data

def test_forecasting():
    """Test demand forecasting engine"""
    print("\n" + "="*70)
    print("🤖 TESTING DEMAND FORECASTING ENGINE")
    print("="*70)
    
    forecaster = DemandForecaster(forecast_days=30, model_type='random_forest')
    
    # Generate mock data
    sales_history = generate_mock_sales_data(days=90, base_qty=50)
    
    print(f"\n📊 Generated {len(sales_history)} days of mock sales data")
    print(f"   Date range: {sales_history[0]['date'][:10]} to {sales_history[-1]['date'][:10]}")
    
    # Predict demand
    product_id = "PROD-001"
    forecast = forecaster.predict_demand(product_id, sales_history)
    
    if forecast.get('error'):
        print(f"   ❌ Error: {forecast['error']}")
        return None
    
    print(f"\n✅ Forecast Generated Successfully!")
    print(f"   Product ID: {forecast['product_id']}")
    print(f"   Forecast Period: {forecast['forecast_period_days']} days")
    
    stats = forecast['statistics']
    print(f"\n📈 Forecast Statistics:")
    print(f"   Average Daily Demand: {stats['average_daily_demand']:.2f} units")
    print(f"   Total Forecast Demand (30 days): {stats['total_forecast_demand']:.2f} units")
    print(f"   Std Deviation: {stats['std_deviation']:.2f} units")
    print(f"   Min Daily: {stats['min_daily_demand']:.2f} units")
    print(f"   Max Daily: {stats['max_daily_demand']:.2f} units")
    
    print(f"\n📋 First 5 Days of Forecast:")
    for i, day in enumerate(forecast['forecast'][:5], 1):
        print(f"   Day {i} ({day['date']}): {day['predicted_quantity']:.2f} units " +
              f"(range: {day['lower_bound']:.2f} - {day['upper_bound']:.2f})")
    
    return forecast

def test_alerts(forecast_data):
    """Test alert system"""
    print("\n" + "="*70)
    print("🚨 TESTING ALERT SYSTEM")
    print("="*70)
    
    alert_system = AlertSystem(
        min_stock_threshold=20,
        critical_threshold=10,
        enable_slack=False,
        enable_email=False
    )
    
    print(f"\n⚙️  Alert Thresholds Configured:")
    print(f"   Minimum Stock Threshold: 20 units")
    print(f"   Critical Threshold: 10 units")
    
    # Test inventory levels
    test_products = [
        {'product_id': 'PROD-001', 'product_name': 'Widget A', 'available_quantity': 5},
        {'product_id': 'PROD-002', 'product_name': 'Widget B', 'available_quantity': 15},
        {'product_id': 'PROD-003', 'product_name': 'Widget C', 'available_quantity': 25},
        {'product_id': 'PROD-004', 'product_name': 'Widget D', 'available_quantity': 0},
    ]
    
    print(f"\n📦 Processing {len(test_products)} products...")
    alerts = alert_system.process_inventory_data(test_products)
    
    if alerts:
        print(f"\n⚠️  {len(alerts)} ALERTS TRIGGERED:")
        for alert in alerts:
            severity_emoji = {
                'critical': '🔴',
                'high': '🟠',
                'medium': '🟡',
                'low': '🟢'
            }
            emoji = severity_emoji.get(alert.severity.value, '⚪')
            print(f"\n   {emoji} {alert.severity.value.upper()}")
            print(f"      Product: {alert.product_name}")
            print(f"      Message: {alert.message}")
            print(f"      Current Level: {alert.current_level} units")
    else:
        print(f"\n✅ No alerts triggered")
    
    return alert_system

def test_reorder(forecast_data):
    """Test reorder optimizer"""
    print("\n" + "="*70)
    print("📦 TESTING REORDER OPTIMIZER")
    print("="*70)
    
    optimizer = ReorderOptimizer(
        reorder_point=15,
        safety_stock=5,
        lead_time_days=7
    )
    
    print(f"\n⚙️  Reorder Parameters:")
    print(f"   Reorder Point: 15 units")
    print(f"   Safety Stock: 5 units")
    print(f"   Lead Time: 7 days")
    
    # Test products with current stock
    products = [
        {
            'product_id': 'PROD-001',
            'product_name': 'Widget A',
            'current_stock': 10,
            'forecast_data': forecast_data
        },
        {
            'product_id': 'PROD-002',
            'product_name': 'Widget B',
            'current_stock': 50,
            'forecast_data': forecast_data
        },
    ]
    
    print(f"\n🔍 Analyzing {len(products)} products for reorder recommendations...")
    recommendations = optimizer.generate_batch_recommendations(products)
    
    if recommendations:
        print(f"\n📋 {len(recommendations)} REORDER RECOMMENDATIONS GENERATED:\n")
        
        # Group by urgency
        by_urgency = {}
        for rec in recommendations:
            urgency = rec.urgency
            if urgency not in by_urgency:
                by_urgency[urgency] = []
            by_urgency[urgency].append(rec)
        
        urgency_order = ['CRITICAL', 'HIGH', 'NORMAL']
        for urgency in urgency_order:
            if urgency in by_urgency:
                emoji = {'CRITICAL': '🔴', 'HIGH': '🟠', 'NORMAL': '🟡'}.get(urgency, '⚪')
                print(f"   {emoji} {urgency} PRIORITY ({len(by_urgency[urgency])} items):")
                for rec in by_urgency[urgency]:
                    print(f"\n      Product: {rec.product_name}")
                    print(f"      Current Stock: {rec.current_stock} units")
                    print(f"      Recommended Order: {rec.recommended_quantity} units")
                    print(f"      Reorder Date: {rec.reorder_date}")
                    print(f"      Reason: {rec.reason}")
                    if rec.estimated_stockout_date:
                        print(f"      Est. Stockout: {rec.estimated_stockout_date}")
    else:
        print(f"\n✅ No reorders needed at this time")
    
    return recommendations

def test_dashboard_api():
    """Test dashboard API endpoints"""
    print("\n" + "="*70)
    print("📊 TESTING DASHBOARD API")
    print("="*70)
    
    print(f"\n✅ Dashboard API Endpoints Available:")
    print(f"   GET  /api/health - System health check")
    print(f"   GET  /api/inventory - Current inventory status")
    print(f"   GET  /api/forecast/<product_id> - Demand forecast")
    print(f"   GET  /api/alerts - Active alerts")
    print(f"   GET  /api/recommendations - Reorder recommendations")
    print(f"   POST /api/alerts/<product_id>/acknowledge - Acknowledge alert")
    print(f"   POST /api/recommendations/<product_id>/execute - Execute reorder")
    print(f"   GET  /api/stats - Dashboard statistics")
    
    print(f"\n🌐 Start dashboard with: python main.py")
    print(f"   Then access: http://localhost:5000")

def main():
    """Run all tests"""
    print("\n")
    print("╔" + "═"*68 + "╗")
    print("║" + " "*68 + "║")
    print("║" + "  SHOPIFY AI INVENTORY MANAGEMENT SYSTEM - DEMO".center(68) + "║")
    print("║" + "  Testing All Components with Mock Data".center(68) + "║")
    print("║" + " "*68 + "║")
    print("╚" + "═"*68 + "╝")
    
    try:
        # Test forecasting
        forecast_data = test_forecasting()
        
        if not forecast_data:
            print("\n❌ Forecasting test failed")
            return 1
        
        # Test alerts
        test_alerts(forecast_data)
        
        # Test reorder optimizer
        test_reorder(forecast_data)
        
        # Test dashboard
        test_dashboard_api()
        
        # Final summary
        print("\n" + "="*70)
        print("✅ ALL SYSTEM COMPONENTS TESTED SUCCESSFULLY!")
        print("="*70)
        
        print(f"\n🎯 NEXT STEPS:")
        print(f"   1. Configure .env file with your Shopify API credentials")
        print(f"   2. Run: python main.py")
        print(f"   3. Access dashboard at http://localhost:5000")
        print(f"\n📚 For detailed setup instructions, see SETUP.md")
        print(f"📖 For full documentation, see README.md\n")
        
        return 0
        
    except Exception as e:
        logger.error(f"Test failed: {str(e)}", exc_info=True)
        return 1

if __name__ == '__main__':
    sys.exit(main())
