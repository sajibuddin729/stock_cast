import yfinance as yf
import logging
from decimal import Decimal
from django.utils import timezone
from .models import Stock, StockPrice
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

logger = logging.getLogger(__name__)

GLOBAL_STOCKS_METADATA = {
    'AAPL': 'Apple Inc.',
    'TSLA': 'Tesla, Inc.',
    'NVDA': 'NVIDIA Corporation',
    'MSFT': 'Microsoft Corporation',
    'AMZN': 'Amazon.com, Inc.',
    'GOOGL': 'Alphabet Inc. (Google)',
    'META': 'Meta Platforms, Inc.',
    'NFLX': 'Netflix, Inc.',
    'AMD': 'Advanced Micro Devices',
}

def fetch_and_save_yfinance_data(symbol, period="5d", interval="1m"):
    name = GLOBAL_STOCKS_METADATA.get(symbol, f"{symbol} Inc.")
    stock, created = Stock.objects.get_or_create(
        symbol=symbol,
        defaults={'name': name, 'market_type': 'GLOBAL', 'is_active': True}
    )
    if stock.name != name:
        stock.name = name
        stock.save(update_fields=['name'])
    
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period=period, interval=interval)

        if df.empty:
            # Fallback to period='1mo', interval='1d' or '5m'
            df = ticker.history(period="1mo", interval="5m")

        if df.empty:
            logger.warning(f"No yfinance data returned for {symbol}")
            return False

        prices_to_create = []
        latest_price_data = None
        
        for index, row in df.iterrows():
            timestamp = index.to_pydatetime()
            
            latest_price_data = {
                'symbol': symbol,
                'market_type': 'GLOBAL',
                'name': name,
                'timestamp': str(timestamp),
                'open_price': float(row['Open']),
                'high_price': float(row['High']),
                'low_price': float(row['Low']),
                'close_price': float(row['Close']),
                'volume': int(row['Volume'])
            }
            
            prices_to_create.append(
                StockPrice(
                    stock=stock,
                    timestamp=timestamp,
                    open_price=Decimal(str(round(row['Open'], 4))),
                    high_price=Decimal(str(round(row['High'], 4))),
                    low_price=Decimal(str(round(row['Low'], 4))),
                    close_price=Decimal(str(round(row['Close'], 4))),
                    volume=int(row['Volume'])
                )
            )
        
        StockPrice.objects.bulk_create(prices_to_create, ignore_conflicts=True)
        
        # Broadcast latest price data over WebSockets
        if latest_price_data:
            channel_layer = get_channel_layer()
            if channel_layer:
                async_to_sync(channel_layer.group_send)(
                    'live_stock_prices',
                    {
                        'type': 'stock_update',
                        'data': latest_price_data
                    }
                )
            
        return True
    except Exception as e:
        logger.error(f"Error fetching yfinance data for {symbol}: {e}")
        return False

def fetch_all_global_stocks():
    """
    Fetches latest data for all configured global stocks.
    """
    success_count = 0
    for symbol in GLOBAL_STOCKS_METADATA.keys():
        if fetch_and_save_yfinance_data(symbol, period="1d", interval="1m"):
            success_count += 1
    return success_count
