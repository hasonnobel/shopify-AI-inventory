"""
Dashboard Web Application
Provides UI for inventory management and AI insights
"""

import logging
from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

def create_dashboard(components: dict) -> Flask:
    """
    Create and configure Flask dashboard application
    
    Args:
        components: Dictionary of system components (shopify, forecaster, alerts, optimizer)
        
    Returns:
        Configured Flask app
    """
    app = Flask(__name__)
    CORS(app)
    
    # Store components in app context
    app.components = components
    
    # Health check endpoint
    @app.route('/api/health', methods=['GET'])
    def health():
        """Health check endpoint"""
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'version': '1.0.0'
        })
    
    # Inventory endpoints
    @app.route('/api/inventory', methods=['GET'])
    def get_inventory():
        """Get current inventory status"""
        try:
            shopify_client = app.components['shopify']
            products = shopify_client.get_products(limit=50)
            
            inventory_data = []
            for product in products:
                variants = product.get('variants', [])
                for variant in variants:
                    inventory_data.append({
                        'product_id': product['id'],
                        'product_name': product['title'],
                        'sku': variant.get('sku', 'N/A'),
                        'quantity': variant.get('inventory_quantity', 0),
                        'price': variant.get('price', '0')
                    })
            
            return jsonify({
                'status': 'success',
                'inventory': inventory_data,
                'total_products': len(inventory_data),
                'timestamp': datetime.now().isoformat()
            })
        except Exception as e:
            logger.error(f"Error fetching inventory: {str(e)}")
            return jsonify({'status': 'error', 'message': str(e)}), 500
    
    # Forecast endpoints
    @app.route('/api/forecast/<product_id>', methods=['GET'])
    def get_forecast(product_id):
        """Get demand forecast for product"""
        try:
            forecaster = app.components['forecaster']
            
            # Get historical sales data
            shopify_client = app.components['shopify']
            orders = shopify_client.get_orders(days_back=90)
            
            # Build sales history for product
            sales_history = []
            for order in orders:
                for line_item in order.get('line_items', []):
                    if str(line_item.get('product_id')) == product_id:
                        sales_history.append({
                            'date': order.get('created_at', datetime.now().isoformat()),
                            'quantity': line_item.get('quantity', 0)
                        })
            
            if not sales_history:
                return jsonify({
                    'status': 'error',
                    'message': 'Insufficient sales history for forecasting'
                }), 400
            
            # Generate forecast
            forecast = forecaster.predict_demand(product_id, sales_history)
            
            return jsonify({
                'status': 'success',
                'forecast': forecast
            })
        except Exception as e:
            logger.error(f"Error generating forecast: {str(e)}")
            return jsonify({'status': 'error', 'message': str(e)}), 500
    
    # Alerts endpoints
    @app.route('/api/alerts', methods=['GET'])
    def get_alerts():
        """Get active alerts"""
        try:
            alert_system = app.components['alerts']
            alerts = alert_system.get_active_alerts()
            
            return jsonify({
                'status': 'success',
                'alerts': alerts,
                'count': len(alerts),
                'timestamp': datetime.now().isoformat()
            })
        except Exception as e:
            logger.error(f"Error fetching alerts: {str(e)}")
            return jsonify({'status': 'error', 'message': str(e)}), 500
    
    @app.route('/api/alerts/<product_id>/acknowledge', methods=['POST'])
    def acknowledge_alert(product_id):
        """Acknowledge an alert"""
        try:
            alert_system = app.components['alerts']
            success = alert_system.acknowledge_alert(product_id)
            
            return jsonify({
                'status': 'success' if success else 'error',
                'message': 'Alert acknowledged' if success else 'Alert not found'
            })
        except Exception as e:
            logger.error(f"Error acknowledging alert: {str(e)}")
            return jsonify({'status': 'error', 'message': str(e)}), 500
    
    # Reorder recommendations endpoints
    @app.route('/api/recommendations', methods=['GET'])
    def get_recommendations():
        """Get reorder recommendations"""
        try:
            optimizer = app.components['optimizer']
            urgency = request.args.get('urgency')
            
            recommendations = optimizer.get_recommendations(urgency_filter=urgency)
            
            return jsonify({
                'status': 'success',
                'recommendations': recommendations,
                'count': len(recommendations),
                'timestamp': datetime.now().isoformat()
            })
        except Exception as e:
            logger.error(f"Error fetching recommendations: {str(e)}")
            return jsonify({'status': 'error', 'message': str(e)}), 500
    
    @app.route('/api/recommendations/<product_id>/execute', methods=['POST'])
    def execute_recommendation(product_id):
        """Execute a reorder recommendation"""
        try:
            optimizer = app.components['optimizer']
            success = optimizer.execute_recommendation(product_id)
            
            return jsonify({
                'status': 'success' if success else 'error',
                'message': 'Recommendation executed' if success else 'Recommendation not found'
            })
        except Exception as e:
            logger.error(f"Error executing recommendation: {str(e)}")
            return jsonify({'status': 'error', 'message': str(e)}), 500
    
    # Dashboard stats
    @app.route('/api/stats', methods=['GET'])
    def get_stats():
        """Get dashboard statistics"""
        try:
            shopify_client = app.components['shopify']
            alert_system = app.components['alerts']
            optimizer = app.components['optimizer']
            
            products = shopify_client.get_products(limit=100)
            active_alerts = alert_system.get_active_alerts()
            recommendations = optimizer.get_recommendations()
            
            total_value = sum(
                sum(v.get('inventory_quantity', 0) * float(v.get('price', 0))
                    for v in p.get('variants', []))
                for p in products
            )
            
            return jsonify({
                'status': 'success',
                'stats': {
                    'total_products': len(products),
                    'active_alerts': len(active_alerts),
                    'pending_reorders': len([r for r in recommendations if r['urgency'] == 'CRITICAL']),
                    'total_inventory_value': float(total_value),
                    'timestamp': datetime.now().isoformat()
                }
            })
        except Exception as e:
            logger.error(f"Error fetching stats: {str(e)}")
            return jsonify({'status': 'error', 'message': str(e)}), 500
    
    return app