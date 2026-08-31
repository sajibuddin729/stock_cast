from celery import shared_task
import logging
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from .models import Stock
from .services import fetch_all_global_stocks, fetch_and_save_yfinance_data
from .dse_service import fetch_and_save_dse_data
from ml_engine.predictor import train_and_predict

logger = logging.getLogger(__name__)

@shared_task
def fetch_live_market_data():
    """
    Automated periodic market data fetching task running every 60s:
    1. Scrapes latest live stock prices from Dhaka Stock Exchange (dsebd.org).
    2. Fetches latest global market data (AAPL, TSLA, NVDA, MSFT, AMZN, etc.).
    3. Executes ML prediction models for active stocks.
    4. Broadcasts real-time prices & ML forecasts over WebSockets.
    """
    channel_layer = get_channel_layer()
    
    # 1. Scrape DSE Market
    try:
        dse_count = fetch_and_save_dse_data()
        logger.info(f"DSE Market: Updated {dse_count} stocks.")
    except Exception as e:
        logger.error(f"Error updating DSE market: {e}")
        dse_count = 0

    # 2. Fetch Global Market
    try:
        global_count = fetch_all_global_stocks()
        logger.info(f"Global Market: Updated {global_count} stocks.")
    except Exception as e:
        logger.error(f"Error updating Global market: {e}")
        global_count = 0

    # 3. Train & Predict ML models for active/tracked stocks
    # Select key global stocks + top DSE stocks for forecasting
    tracked_symbols = ['AAPL', 'TSLA', 'NVDA', 'MSFT', 'AMZN', 'GP', 'BEXIMCO', 'SQURPHARMA', 'BRACBANK', 'BATBC', 'WALTONHIL', 'ROBI']
    active_stocks = Stock.objects.filter(symbol__in=tracked_symbols, is_active=True)
    
    forecast_count = 0
    for stock in active_stocks:
        try:
            prediction_data = train_and_predict(stock)
            if prediction_data and channel_layer:
                forecast_count += 1
                async_to_sync(channel_layer.group_send)(
                    'live_stock_prices',
                    {
                        'type': 'stock_update',
                        'data': prediction_data
                    }
                )
        except Exception as e:
            logger.error(f"Error predicting stock {stock.symbol}: {e}")

    summary = f"Celery Cycle Complete: {dse_count} DSE stocks, {global_count} Global stocks, {forecast_count} ML forecasts updated."
    logger.info(summary)
    return summary
