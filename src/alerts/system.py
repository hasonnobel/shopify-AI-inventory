"""
Alert System
Monitors inventory levels and generates alerts
"""

import logging
import requests
from typing import Dict, List, Optional
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)

class AlertSeverity(Enum):
    """Alert severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class Alert:
    """Represents a single alert"""
    
    def __init__(self, product_id: str, product_name: str, severity: AlertSeverity,
                 message: str, current_level: int, threshold: int):
        """Initialize alert"""
        self.product_id = product_id
        self.product_name = product_name
        self.severity = severity
        self.message = message
        self.current_level = current_level
        self.threshold = threshold
        self.created_at = datetime.now()
        self.acknowledged = False
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'product_id': self.product_id,
            'product_name': self.product_name,
            'severity': self.severity.value,
            'message': self.message,
            'current_level': self.current_level,
            'threshold': self.threshold,
            'created_at': self.created_at.isoformat(),
            'acknowledged': self.acknowledged
        }

class AlertSystem:
    """Manages inventory alerts and notifications"""
    
    def __init__(self, min_stock_threshold: int = 10, critical_threshold: int = 5,
                 enable_slack: bool = False, slack_webhook: Optional[str] = None,
                 enable_email: bool = False, email_config: Optional[Dict] = None):
        """
        Initialize alert system
        
        Args:
            min_stock_threshold: Low stock alert threshold
            critical_threshold: Critical stock alert threshold
            enable_slack: Enable Slack notifications
            slack_webhook: Slack webhook URL
            enable_email: Enable email notifications
            email_config: Email configuration
        """
        self.min_stock_threshold = min_stock_threshold
        self.critical_threshold = critical_threshold
        self.enable_slack = enable_slack
        self.slack_webhook = slack_webhook
        self.enable_email = enable_email
        self.email_config = email_config or {}
        self.alerts = []
        self.alert_history = []
        
        logger.info(f"Alert system initialized: min_threshold={min_stock_threshold}, "
                   f"critical_threshold={critical_threshold}")
    
    def check_inventory_level(self, product_id: str, product_name: str,
                             current_level: int) -> Optional[Alert]:
        """
        Check if inventory level triggers an alert
        
        Args:
            product_id: Product ID
            product_name: Product name
            current_level: Current inventory level
            
        Returns:
            Alert object if triggered, None otherwise
        """
        
        if current_level <= 0:
            severity = AlertSeverity.CRITICAL
            message = f"CRITICAL: {product_name} is out of stock!"
        elif current_level <= self.critical_threshold:
            severity = AlertSeverity.CRITICAL
            message = f"CRITICAL: {product_name} stock is critically low ({current_level} units)"
        elif current_level <= self.min_stock_threshold:
            severity = AlertSeverity.HIGH
            message = f"WARNING: {product_name} stock is low ({current_level} units)"
        else:
            return None
        
        alert = Alert(
            product_id=product_id,
            product_name=product_name,
            severity=severity,
            message=message,
            current_level=current_level,
            threshold=self.min_stock_threshold
        )
        
        logger.warning(f"Alert triggered: {message}")
        return alert
    
    def add_alert(self, alert: Alert) -> None:
        """Add alert to system"""
        self.alerts.append(alert)
        self.alert_history.append(alert)
    
    def process_inventory_data(self, inventory_data: List[Dict]) -> List[Alert]:
        """
        Process inventory data and generate alerts
        
        Args:
            inventory_data: List of inventory records
            
        Returns:
            List of new alerts
        """
        new_alerts = []
        
        for item in inventory_data:
            alert = self.check_inventory_level(
                product_id=item['product_id'],
                product_name=item.get('product_name', 'Unknown'),
                current_level=item['available_quantity']
            )
            
            if alert:
                self.add_alert(alert)
                new_alerts.append(alert)
        
        if new_alerts:
            logger.info(f"Generated {len(new_alerts)} alerts")
            self.notify_alerts(new_alerts)
        
        return new_alerts
    
    def notify_alerts(self, alerts: List[Alert]) -> bool:
        """
        Send alert notifications
        
        Args:
            alerts: List of alerts to notify
            
        Returns:
            Success status
        """
        success = True
        
        for alert in alerts:
            if self.enable_slack and self.slack_webhook:
                if not self._send_slack_notification(alert):
                    success = False
            
            if self.enable_email:
                if not self._send_email_notification(alert):
                    success = False
        
        return success
    
    def _send_slack_notification(self, alert: Alert) -> bool:
        """Send Slack notification"""
        try:
            color_map = {
                AlertSeverity.LOW: '#FFD700',
                AlertSeverity.MEDIUM: '#FFA500',
                AlertSeverity.HIGH: '#FF6347',
                AlertSeverity.CRITICAL: '#DC143C'
            }
            
            payload = {
                "attachments": [{
                    "color": color_map.get(alert.severity, '#999999'),
                    "title": f"Inventory Alert - {alert.severity.value.upper()}",
                    "text": alert.message,
                    "fields": [
                        {
                            "title": "Product",
                            "value": f"{alert.product_name} (ID: {alert.product_id})",
                            "short": False
                        },
                        {
                            "title": "Current Level",
                            "value": str(alert.current_level),
                            "short": True
                        },
                        {
                            "title": "Threshold",
                            "value": str(alert.threshold),
                            "short": True
                        },
                        {
                            "title": "Time",
                            "value": alert.created_at.isoformat(),
                            "short": False
                        }
                    ]
                }]
            }
            
            response = requests.post(self.slack_webhook, json=payload)
            response.raise_for_status()
            
            logger.info(f"Slack notification sent for {alert.product_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send Slack notification: {str(e)}")
            return False
    
    def _send_email_notification(self, alert: Alert) -> bool:
        """Send email notification"""
        try:
            # Placeholder for email notification
            # In production, use smtplib or a service like SendGrid
            logger.info(f"Email notification would be sent for {alert.product_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to send email notification: {str(e)}")
            return False
    
    def get_active_alerts(self) -> List[Dict]:
        """Get currently active alerts"""
        return [alert.to_dict() for alert in self.alerts if not alert.acknowledged]
    
    def acknowledge_alert(self, product_id: str) -> bool:
        """Acknowledge an alert"""
        for alert in self.alerts:
            if alert.product_id == product_id:
                alert.acknowledged = True
                logger.info(f"Alert acknowledged for product: {product_id}")
                return True
        return False
    
    def clear_alerts(self) -> None:
        """Clear all active alerts"""
        self.alerts = []
        logger.info("All alerts cleared")