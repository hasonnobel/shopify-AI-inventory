# Shopify AI Inventory Management - Setup Guide

Complete setup instructions to get your AI inventory automation running.

## Prerequisites

- Python 3.8+ or Node.js 14+
- Shopify store with admin access
- Git installed

## Step 1: Clone Repository

```bash
git clone https://github.com/hasonnobel/shopify-ai-inventory.git
cd shopify-ai-inventory
```

## Step 2: Set Up Shopify API

### Create a Shopify App

1. Go to your Shopify Admin Dashboard
2. Navigate to **Settings** → **Apps and integrations** → **Develop apps**
3. Click **Create an app**
4. Name it "Inventory Manager"
5. Click **Create app**

### Configure API Scopes

In the app settings:

1. Go to **Configuration** tab
2. Under **Admin API scopes**, enable:
   - `read_products`
   - `write_products`
   - `read_inventory`
   - `write_inventory`
   - `read_orders`
3. Click **Save**

### Get API Credentials

1. Go to **API credentials** tab
2. Copy your:
   - **API Key**
   - **API Password** (if using REST API with basic auth)
   - **Access Token** (if using OAuth)
3. Keep these safe - you'll need them in the next step

## Step 3: Install Python Dependencies

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Linux/Mac:
source venv/bin/activate
# On Windows:
venv\\Scripts\\activate

# Install dependencies
pip install -r requirements.txt
```

## Step 4: Configure Environment Variables

```bash
# Copy example env file
cp .env.example .env

# Edit .env with your credentials
nano .env  # or use your preferred editor
```

Fill in the following required fields:

```
SHOPIFY_STORE_URL=your-store.myshopify.com
SHOPIFY_API_KEY=your_api_key
SHOPIFY_ACCESS_TOKEN=your_access_token

# Database (optional - uses SQLite by default)
DATABASE_URL=sqlite:///inventory.db

# Forecasting
FORECAST_DAYS=30
MIN_STOCK_THRESHOLD=10
CRITICAL_THRESHOLD=5
```

## Step 5: Initialize Database (Optional)

For production deployments with PostgreSQL:

```bash
# Create PostgreSQL database
createdb inventory_db

# Run migrations
python scripts/init_db.py
```

## Step 6: Start the Application

```bash
# Development mode
python main.py

# Production mode
export FLASK_ENV=production
gunicorn -w 4 main:app
```

The dashboard will be available at `http://localhost:5000`

## Step 7: Set Up Background Tasks (Optional)

For automated forecasting and alerting:

```bash
# Start Celery worker
celery -A src.tasks worker --loglevel=info

# Start Celery beat (scheduler)
celery -A src.tasks beat --loglevel=info
```

## Step 8: Configure Notifications (Optional)

### Slack Notifications

1. Create a Slack Workspace webhook:
   - Go to your Slack workspace
   - Create an incoming webhook
   - Copy the webhook URL

2. Add to `.env`:
   ```
   ENABLE_SLACK_NOTIFICATIONS=true
   SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
   ```

### Email Notifications

1. Set up SMTP credentials in `.env`:
   ```
   ENABLE_EMAIL_NOTIFICATIONS=true
   SMTP_SERVER=smtp.gmail.com
   SMTP_PORT=587
   SMTP_USERNAME=your-email@gmail.com
   SMTP_PASSWORD=your-app-password
   ALERT_EMAIL=recipient@example.com
   ```

## Step 9: Test the System

```bash
# Run tests
pytest tests/

# Test Shopify connection
python -c "from src.shopify.client import ShopifyClient; client = ShopifyClient('your-store', 'token'); print(client.get_products(limit=1))"

# Run forecasting
python -c "from src.forecasting.engine import DemandForecaster; f = DemandForecaster(); print('Forecaster ready')"
```

## Step 10: Deploy

### Docker Deployment

```bash
# Build Docker image
docker build -t shopify-inventory .

# Run container
docker run -p 5000:5000 \
  -e SHOPIFY_STORE_URL=your-store.myshopify.com \
  -e SHOPIFY_ACCESS_TOKEN=your_token \
  shopify-inventory
```

### Cloud Deployment (Heroku)

```bash
# Create Heroku app
heroku create your-app-name

# Set environment variables
heroku config:set SHOPIFY_STORE_URL=your-store.myshopify.com
heroku config:set SHOPIFY_ACCESS_TOKEN=your_token

# Deploy
git push heroku main
```

## Verification

Once running, verify the system:

1. **Check API Health**: `curl http://localhost:5000/api/health`
2. **View Dashboard**: Open `http://localhost:5000` in browser
3. **Check Inventory**: `curl http://localhost:5000/api/inventory`
4. **View Alerts**: `curl http://localhost:5000/api/alerts`
5. **View Recommendations**: `curl http://localhost:5000/api/recommendations`

## Troubleshooting

### Connection Issues
- Verify Shopify API credentials are correct
- Check store URL format (must include `.myshopify.com`)
- Ensure API scopes are properly configured

### Forecasting Not Working
- Need at least 60 days of historical sales data
- Check Prophet is installed: `pip show prophet`
- Review logs: `tail -f logs/forecasting.log`

### Database Connection Errors
- Verify DATABASE_URL is correct
- For PostgreSQL: ensure database exists and user has access
- Check connection string format: `postgresql://user:password@localhost:5432/db_name`

### Port Already in Use
- Change port: `DASHBOARD_PORT=8000 python main.py`
- Or kill existing process: `lsof -i :5000` then `kill -9 <PID>`

## Next Steps

1. **Add More Products**: System automatically discovers products from Shopify
2. **Customize Thresholds**: Edit config/forecasting.json to adjust alert levels
3. **Integrate External Services**: Add webhooks for custom integrations
4. **Monitor Performance**: Review logs and metrics in dashboard
5. **Scale Infrastructure**: Move to production database and hosting

## Support

For issues or questions:
- Check logs in `/logs` directory
- Review documentation in `/docs`
- Open issue on GitHub: https://github.com/hasonnobel/shopify-ai-inventory/issues