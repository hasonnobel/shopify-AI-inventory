"""
Shopify API Client
Handles all communication with Shopify API
"""

import logging
import requests
import json
from typing import Dict, List, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class ShopifyClient:
    """Client for interacting with Shopify API"""
    
    def __init__(self, store_url: str, access_token: str):
        """
        Initialize Shopify client
        
        Args:
            store_url: Shopify store URL (e.g., 'mystore.myshopify.com')
            access_token: Shopify API access token
        """
        self.store_url = store_url.replace('.myshopify.com', '').replace('https://', '').replace('http://', '')
        self.access_token = access_token
        self.base_url = f"https://{self.store_url}.myshopify.com/admin/api/2024-01"
        self.headers = {
            "X-Shopify-Access-Token": access_token,
            "Content-Type": "application/json"
        }
        logger.info(f"Shopify client initialized for store: {self.store_url}")
    
    def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Dict:
        """
        Make API request to Shopify
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint
            data: Request body data
            
        Returns:
            Response JSON
        """
        url = f"{self.base_url}/{endpoint}.json"
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=self.headers)
            elif method == 'POST':
                response = requests.post(url, headers=self.headers, json=data)
            elif method == 'PUT':
                response = requests.put(url, headers=self.headers, json=data)
            elif method == 'DELETE':
                response = requests.delete(url, headers=self.headers)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Shopify API request failed: {str(e)}")
            raise
    
    def get_products(self, status: str = 'active', limit: int = 100) -> List[Dict]:
        """
        Get products from Shopify store
        
        Args:
            status: Product status (active, archived, draft)
            limit: Number of products to retrieve
            
        Returns:
            List of products
        """
        logger.info(f"Fetching {limit} products with status: {status}")
        
        response = self._make_request('GET', f'products?status={status}&limit={limit}')
        return response.get('products', [])
    
    def get_product(self, product_id: str) -> Dict:
        """Get single product details"""
        logger.info(f"Fetching product: {product_id}")
        response = self._make_request('GET', f'products/{product_id}')
        return response.get('product', {})
    
    def get_inventory_levels(self, location_id: Optional[str] = None) -> List[Dict]:
        """
        Get inventory levels for all products
        
        Args:
            location_id: Specific location ID (optional)
            
        Returns:
            List of inventory levels
        """
        logger.info("Fetching inventory levels")
        response = self._make_request('GET', 'inventory_levels')
        return response.get('inventory_levels', [])
    
    def get_orders(self, days_back: int = 30, status: str = 'any') -> List[Dict]:
        """
        Get orders from the past N days
        
        Args:
            days_back: Number of days to look back
            status: Order status filter
            
        Returns:
            List of orders
        """
        start_date = (datetime.now() - timedelta(days=days_back)).isoformat()
        logger.info(f"Fetching orders from last {days_back} days")
        
        response = self._make_request(
            'GET', 
            f'orders?status={status}&created_at_min={start_date}&limit=100'
        )
        return response.get('orders', [])
    
    def update_inventory(self, inventory_item_id: str, available_quantity: int, 
                        location_id: str) -> bool:
        """
        Update inventory for a product
        
        Args:
            inventory_item_id: Inventory item ID
            available_quantity: New quantity
            location_id: Location ID
            
        Returns:
            Success status
        """
        logger.info(f"Updating inventory for item {inventory_item_id} to {available_quantity}")
        
        data = {
            "inventory_level": {
                "inventory_item_id": inventory_item_id,
                "available": available_quantity,
                "location_id": location_id
            }
        }
        
        try:
            self._make_request('POST', 'inventory_levels/set', data)
            return True
        except Exception as e:
            logger.error(f"Failed to update inventory: {str(e)}")
            return False
    
    def create_purchase_order(self, po_data: Dict) -> Optional[Dict]:
        """
        Create a purchase order
        
        Args:
            po_data: Purchase order data
            
        Returns:
            Created purchase order or None on failure
        """
        logger.info("Creating purchase order")
        
        try:
            response = self._make_request('POST', 'purchase_orders', {"purchase_order": po_data})
            return response.get('purchase_order')
        except Exception as e:
            logger.error(f"Failed to create purchase order: {str(e)}")
            return None
    
    def get_locations(self) -> List[Dict]:
        """Get all store locations"""
        logger.info("Fetching store locations")
        response = self._make_request('GET', 'locations')
        return response.get('locations', [])
    
    def sync_products_with_orders(self) -> Dict:
        """
        Sync product data with order history
        
        Returns:
            Summary of sync operation
        """
        logger.info("Syncing products with order history")
        
        products = self.get_products()
        orders = self.get_orders(days_back=90)
        
        # Build product sales map
        product_sales = {}
        for order in orders:
            for line_item in order.get('line_items', []):
                product_id = str(line_item.get('product_id'))
                quantity = line_item.get('quantity', 0)
                
                if product_id not in product_sales:
                    product_sales[product_id] = 0
                product_sales[product_id] += quantity
        
        logger.info(f"Synced {len(products)} products with {len(orders)} orders")
        
        return {
            'products_count': len(products),
            'orders_count': len(orders),
            'product_sales': product_sales
        }