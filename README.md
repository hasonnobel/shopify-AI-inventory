# Shopify AI Inventory Management

An AI-powered inventory management automation system for Shopify that uses machine learning to forecast demand, optimize stock levels, and automate reordering.

## Features

- **AI Demand Forecasting** - Predict product demand using historical sales data
- **Automated Low-Stock Alerts** - Get notified when inventory drops below thresholds
- **Smart Reorder Recommendations** - AI suggests optimal reorder quantities and timing
- **Inventory Optimization** - Reduce overstock and stockouts
- **Shopify API Integration** - Seamless integration with your Shopify store
- **Real-time Monitoring** - Track inventory metrics and trends
- **Dashboard** - Visualize inventory health and forecasts

## Quick Start

### Prerequisites
- Python 3.8+ or Node.js 14+
- Shopify store with API access
- Shopify API credentials (API key, API password/access token)

### Installation

1. Clone the repository
```bash
git clone https://github.com/hasonnobel/shopify-ai-inventory.git
cd shopify-ai-inventory
```

2. Install dependencies
```bash
# For Python
pip install -r requirements.txt

# For Node.js
npm install
```

3. Set up environment variables
```bash
cp .env.example .env
# Edit .env with your Shopify API credentials
```

4. Run the system
```bash
# For Python
python main.py

# For Node.js
npm start
```

## Configuration

### Shopify API Setup

1. Go to your Shopify Admin Dashboard
2. Navigate to Settings → Apps and integrations → Develop apps
3. Create a new app with these scopes:
   - `read_products`
   - `write_products`
   - `read_inventory`
   - `write_inventory`
   - `read_orders`

4. Copy your API credentials to `.env`

### AI Forecasting Parameters

Edit `config/forecasting.json` to customize:
- `forecast_days` - Number of days to forecast ahead (default: 30)
- `min_stock_threshold` - Alert when stock drops below this (default: 10)
- `reorder_point` - Automatic reorder trigger level
- `safety_stock` - Buffer stock to maintain

## System Architecture

```
shopify-ai-inventory/
├── src/
│   ├── shopify/          # Shopify API integration
│   ├── forecasting/      # AI demand forecasting engine
│   ├── alerts/           # Alert system
│   ├── reordering/       # Reorder automation
│   └── dashboard/        # Web dashboard
├── config/               # Configuration files
├── data/                 # Historical data & models
├── logs/                 # Application logs
└── main.py/main.js       # Entry point
```

## Usage

### Get Inventory Status
```python
from src.shopify import ShopifyClient

client = ShopifyClient()
inventory = client.get_inventory()
print(inventory)
```

### Run Demand Forecast
```python
from src.forecasting import DemandForecaster

forecaster = DemandForecaster()
forecast = forecaster.predict_demand(product_id, days=30)
print(forecast)
```

### Check Low Stock Items
```python
from src.alerts import AlertSystem

alerts = AlertSystem()
low_stock_items = alerts.get_low_stock_alerts()
print(low_stock_items)
```

### Generate Reorder Recommendations
```python
from src.reordering import ReorderOptimizer

optimizer = ReorderOptimizer()
recommendations = optimizer.get_recommendations()
print(recommendations)
```

## API Endpoints

### Dashboard
- `GET /api/inventory` - Current inventory status
- `GET /api/forecast/:productId` - Demand forecast for product
- `GET /api/alerts` - Current alerts
- `GET /api/recommendations` - Reorder recommendations
- `POST /api/reorder` - Create reorder

### Webhooks
- `/webhook/product-updated` - Handle Shopify product updates
- `/webhook/order-created` - Handle new orders

## Monitoring & Logs

Logs are stored in `logs/` directory:
- `forecasting.log` - Forecasting engine logs
- `alerts.log` - Alert system logs
- `reordering.log` - Reorder automation logs
- `shopify_sync.log` - Shopify API sync logs

## Troubleshooting

### Connection Issues
- Verify Shopify API credentials in `.env`
- Check store URL format (e.g., `store-name.myshopify.com`)
- Ensure API scopes are correctly set

### Forecasting Accuracy
- Requires at least 60 days of historical sales data
- Seasonal patterns improve accuracy over time
- Adjust `forecast_confidence` in config if needed

### Low Stock Alerts Not Working
- Verify `min_stock_threshold` is set in config
- Check alert notification settings in `.env`
- Review logs in `logs/alerts.log`

## Performance Tips

1. **Run forecasting during off-peak hours** - Schedule via cron job
2. **Cache Shopify data** - Reduce API calls with local caching
3. **Batch reorder creation** - Combine multiple reorders into one request
4. **Monitor API rate limits** - Shopify has rate limits; adjust batch sizes accordingly

## Advanced Configuration

### Custom ML Models
Replace the default forecasting model in `src/forecasting/models/`

### External Integrations
- Slack notifications (see `config/notifications.json`)
- Email alerts (configure SMTP in `.env`)
- Google Sheets export (add service account credentials)

## Support & Contribution

For issues or feature requests, open an issue on GitHub.

## License

MIT License - See LICENSE file for details

## Disclaimer

This system provides recommendations based on historical data and AI models. Always review recommendations before implementing. Past performance does not guarantee future results.