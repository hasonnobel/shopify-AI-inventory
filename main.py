#!/usr/bin/env python3
"""
Shopify AI Inventory Management System
Main entry point for the application
"""

import os
import sys
import logging
from dotenv import load_dotenv
from flask import Flask
from src.shopify.client import ShopifyClient
from src.forecasting.engine import DemandForecaster
from src.alerts.system import AlertSystem
from src.reordering.optimizer import ReorderOptimizer
from src.dashboard.app import create_dashboard

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/application.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def initialize_system():
    """Initialize all system components"""
    logger.info("Initializing Shopify AI Inventory Management System...")
    
    # Verify environment variables
    required_vars = ['SHOPIFY_STORE_URL', 'SHOPIFY_ACCESS_TOKEN']
    missing = [var for var in required_vars if not os.getenv(var)]
    
    if missing:
        logger.error(f"Missing required environment variables: {', '.join(missing)}")
        logger.error("Please configure .env file with Shopify credentials")
        sys.exit(1)
    
    logger.info("✓ Environment variables validated")
    
    # Initialize Shopify client
    shopify_client = ShopifyClient(
        store_url=os.getenv('SHOPIFY_STORE_URL'),
        access_token=os.getenv('SHOPIFY_ACCESS_TOKEN')
    )
    logger.info("✓ Shopify client initialized")
    
    # Initialize forecasting engine
    forecaster = DemandForecaster(
        forecast_days=int(os.getenv('FORECAST_DAYS', 30)),
        model_type=os.getenv('MODEL_TYPE', 'prophet')
    )
    logger.info("✓ Demand forecasting engine initialized")
    
    # Initialize alert system
    alerts = AlertSystem(
        min_stock_threshold=int(os.getenv('MIN_STOCK_THRESHOLD', 10)),
        enable_slack=os.getenv('ENABLE_SLACK_NOTIFICATIONS', 'false').lower() == 'true'
    )
    logger.info("✓ Alert system initialized")
    
    # Initialize reorder optimizer
    optimizer = ReorderOptimizer(
        reorder_point=int(os.getenv('REORDER_POINT', 15)),
        safety_stock=int(os.getenv('SAFETY_STOCK', 5))
    )
    logger.info("✓ Reorder optimizer initialized")
    
    return {
        'shopify': shopify_client,
        'forecaster': forecaster,
        'alerts': alerts,
        'optimizer': optimizer
    }

def main():
    """Main application entry point"""
    try:
        # Initialize system components
        components = initialize_system()
        logger.info("All systems initialized successfully!")
        
        # Create and run dashboard
        logger.info("Starting dashboard server...")
        app = create_dashboard(components)
        
        port = int(os.getenv('DASHBOARD_PORT', 5000))
        debug = os.getenv('FLASK_DEBUG', 'false').lower() == 'true'
        
        logger.info(f"Dashboard running on http://localhost:{port}")
        app.run(host='0.0.0.0', port=port, debug=debug)
        
    except Exception as e:
        logger.error(f"Failed to start application: {str(e)}", exc_info=True)
        sys.exit(1)

if __name__ == '__main__':
    main()