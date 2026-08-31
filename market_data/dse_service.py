import ssl
import urllib.request
import logging
from datetime import datetime, timedelta
from decimal import Decimal
import random
from bs4 import BeautifulSoup
from django.utils import timezone
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from .models import Stock, StockPrice

logger = logging.getLogger(__name__)

# Known popular DSE companies mapping for friendly display names
DSE_COMPANY_NAMES = {
    'GP': 'Grameenphone Ltd.',
    'BEXIMCO': 'Beximco Limited',
    'SQURPHARMA': 'Square Pharmaceuticals PLC',
    'BRACBANK': 'BRAC Bank PLC',
    'BATBC': 'British American Tobacco BD',
    'RENATA': 'Renata PLC',
    'WALTONHIL': 'Walton Hi-Tech Industries',
    'ROBI': 'Robi Axiata Limited',
    'ISLAMIBANK': 'Islami Bank Bangladesh PLC',
    'LHBL': 'LafargeHolcim Bangladesh',
    'BEACONPHAR': 'Beacon Pharmaceuticals',
    'CITYBANK': 'The City Bank Limited',
    'OLYMPIC': 'Olympic Industries Limited',
    'EBL': 'Eastern Bank PLC',
    'BSRMSTEEL': 'BSRM Steels Limited',
    'TITASGAS': 'Titas Gas Transmission',
    'PUBALIBANK': 'Pubali Bank PLC',
    'SUMITPOWER': 'Summit Power Limited',
    'UPGDCL': 'United Power Generation',
    'MARICO': 'Marico Bangladesh Limited',
    'BXPHARMA': 'Beximco Pharmaceuticals',
    'IFIC': 'IFIC Bank PLC',
    'UCB': 'United Commercial Bank',
    'DELTALIFE': 'Delta Life Insurance',
    'JAMUNABANK': 'Jamuna Bank PLC',
    'NBL': 'National Bank Limited',
    'ALARABANK': 'Al-Arafah Islami Bank',
    'PRIMEBANK': 'Prime Bank PLC',
    'SHAHJABANK': 'Shahjalal Islami Bank',
    'SOUTHEASTB': 'Southeast Bank PLC',
    'DUTCHBANGL': 'Dutch-Bangla Bank PLC',
    'POWERGRID': 'Power Grid Company of BD',
    'HEIDELBCEM': 'Heidelberg Materials BD',
    'MJLBD': 'MJL Bangladesh PLC',
    'ORIONPHARM': 'Orion Pharma Limited',
    'ACI': 'ACI Limited',
    'ACIFORMULA': 'ACI Formulations Limited',
    'BSRMLTD': 'Bangladesh Steel Re-Rolling',
    'PADMAOIL': 'Padma Oil Company',
    'MEGHNALIFE': 'Meghna Life Insurance',
    'LANKABAFIN': 'LankaBangla Finance PLC',
    'IDLC': 'IDLC Finance PLC',
    'APEXFOOT': 'Apex Footwear Limited',
    'UNIQUEHRL': 'Unique Hotel & Resorts',
    'SINGERBD': 'Singer Bangladesh Limited',
    'RAHIMAFOOD': 'Rahima Food Corporation',
    'BSC': 'Bangladesh Shipping Corp',
    'KOHINOOR': 'Kohinoor Chemical Company',
    'SONALIPAPR': 'Sonali Paper & Board Mills',
    'GENEXIL': 'Genex Infosys Limited',
    'AAMRANET': 'aamra networks limited',
    'AAMRATECH': 'aamra technologies limited',
    'BDTHAI': 'BD Thai Aluminium',
    'SEAPEARL': 'Sea Pearl Beach Resort',
}

def parse_float_safe(val, default=0.0):
    try:
        clean = str(val).replace(',', '').strip()
        if not clean or clean == '-' or clean == '0':
            return default
        return float(clean)
    except (ValueError, TypeError):
        return default

def parse_int_safe(val, default=0):
    try:
        clean = str(val).replace(',', '').strip()
        if not clean or clean == '-':
            return default
        return int(float(clean))
    except (ValueError, TypeError):
        return default

def scrape_dse_live_data():
    """
    Scrapes all live stock records from Dhaka Stock Exchange official portal.
    URL: https://www.dsebd.org/latest_share_price_scroll_l.php
    """
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    url = 'https://www.dsebd.org/latest_share_price_scroll_l.php'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    }

    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, context=ctx, timeout=20) as response:
            html = response.read().decode('utf-8', errors='ignore')
            
        soup = BeautifulSoup(html, 'html.parser')
        rows = soup.find_all('tr')
        
        parsed_stocks = []
        for row in rows:
            cells = [c.get_text(strip=True) for c in row.find_all(['td', 'th'])]
            # Format: [#, TRADING CODE, LTP*, HIGH, LOW, CLOSEP*, YCP*, CHANGE, TRADE, VALUE (mn), VOLUME]
            if len(cells) >= 11 and cells[0].isdigit():
                symbol = cells[1].strip().upper()
                ltp = parse_float_safe(cells[2])
                high = parse_float_safe(cells[3])
                low = parse_float_safe(cells[4])
                closep = parse_float_safe(cells[5])
                ycp = parse_float_safe(cells[6])
                change = parse_float_safe(cells[7])
                trades = parse_int_safe(cells[8])
                value_mn = parse_float_safe(cells[9])
                volume = parse_int_safe(cells[10])

                # Determine effective current price
                current_price = ltp if ltp > 0 else (closep if closep > 0 else ycp)
                if current_price <= 0:
                    continue

                eff_high = high if high > 0 else current_price
                eff_low = low if low > 0 else current_price
                eff_open = ycp if ycp > 0 else current_price

                parsed_stocks.append({
                    'symbol': symbol,
                    'ltp': current_price,
                    'high': eff_high,
                    'low': eff_low,
                    'open': eff_open,
                    'ycp': ycp,
                    'change': change,
                    'trades': trades,
                    'value_mn': value_mn,
                    'volume': volume,
                })
                
        return parsed_stocks
    except Exception as e:
        logger.error(f"Error scraping DSE data: {e}")
        return []

def seed_dse_history_if_needed(stock, current_price, high_price, low_price, open_price, volume):
    """
    If a DSE stock has fewer than 25 historical records, generates realistic intraday/daily
    candlestick history so charts and ML models can operate immediately with rich data.
    """
    count = StockPrice.objects.filter(stock=stock).count()
    if count >= 30:
        return

    prices_to_create = []
    now = timezone.now()
    base_price = float(current_price)

    # Generate 60 past minute records leading up to current price
    for i in range(60, 0, -1):
        record_time = now - timedelta(minutes=i)
        drift = (random.random() - 0.48) * (base_price * 0.008)
        p_close = max(1.0, round(base_price + drift, 2))
        p_open = max(1.0, round(p_close + (random.random() - 0.5) * (base_price * 0.004), 2))
        p_high = max(p_open, p_close, round(max(p_open, p_close) + random.random() * (base_price * 0.005), 2))
        p_low = min(p_open, p_close, round(min(p_open, p_close) - random.random() * (base_price * 0.005), 2))
        p_vol = max(100, int(volume / 60) + random.randint(100, 2000))

        prices_to_create.append(
            StockPrice(
                stock=stock,
                timestamp=record_time,
                open_price=Decimal(str(p_open)),
                high_price=Decimal(str(p_high)),
                low_price=Decimal(str(p_low)),
                close_price=Decimal(str(p_close)),
                volume=p_vol
            )
        )

    StockPrice.objects.bulk_create(prices_to_create, ignore_conflicts=True)

def fetch_and_save_dse_data():
    """
    Main DSE pipeline:
    1. Scrapes live data for all DSE stocks.
    2. Inserts or updates Stock records in PostgreSQL with market_type='DSE'.
    3. Saves latest StockPrice record for time series.
    4. Seeds historical records if missing.
    5. Broadcasts top updated stocks over Django Channels WebSockets.
    """
    dse_items = scrape_dse_live_data()
    if not dse_items:
        logger.warning("No DSE stocks parsed from dsebd.org")
        return 0

    channel_layer = get_channel_layer()
    now = timezone.now()
    updated_count = 0

    for item in dse_items:
        symbol = item['symbol']
        friendly_name = DSE_COMPANY_NAMES.get(symbol, f"{symbol} Bangladesh")

        stock, created = Stock.objects.get_or_create(
            symbol=symbol,
            defaults={
                'name': friendly_name,
                'market_type': 'DSE',
                'is_active': True,
            }
        )
        if stock.market_type != 'DSE' or stock.name != friendly_name:
            stock.market_type = 'DSE'
            stock.name = friendly_name
            stock.save(update_fields=['market_type', 'name'])

        # Seed initial history if new
        seed_dse_history_if_needed(
            stock=stock,
            current_price=item['ltp'],
            high_price=item['high'],
            low_price=item['low'],
            open_price=item['open'],
            volume=item['volume']
        )

        # Save latest price point
        StockPrice.objects.create(
            stock=stock,
            timestamp=now,
            open_price=Decimal(str(item['open'])),
            high_price=Decimal(str(item['high'])),
            low_price=Decimal(str(item['low'])),
            close_price=Decimal(str(item['ltp'])),
            volume=item['volume']
        )
        updated_count += 1

        # Broadcast live price update over WebSockets
        if channel_layer:
            live_payload = {
                'symbol': symbol,
                'market_type': 'DSE',
                'name': friendly_name,
                'timestamp': str(now),
                'open_price': float(item['open']),
                'high_price': float(item['high']),
                'low_price': float(item['low']),
                'close_price': float(item['ltp']),
                'volume': int(item['volume']),
                'change': float(item['change']),
            }
            async_to_sync(channel_layer.group_send)(
                'live_stock_prices',
                {
                    'type': 'stock_update',
                    'data': live_payload
                }
            )

    return updated_count
