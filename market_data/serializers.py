from rest_framework import serializers
from .models import Stock, StockPrice

class StockSerializer(serializers.ModelSerializer):
    latest_price = serializers.SerializerMethodField()
    change = serializers.SerializerMethodField()
    change_percent = serializers.SerializerMethodField()
    day_high = serializers.SerializerMethodField()
    day_low = serializers.SerializerMethodField()
    volume = serializers.SerializerMethodField()

    class Meta:
        model = Stock
        fields = [
            'id', 
            'symbol', 
            'name', 
            'market_type', 
            'latest_price', 
            'change', 
            'change_percent', 
            'day_high', 
            'day_low', 
            'volume'
        ]

    def _get_latest_price_obj(self, obj):
        if not hasattr(obj, '_cached_latest_price'):
            obj._cached_latest_price = obj.prices.order_by('-timestamp').first()
        return obj._cached_latest_price

    def _get_prev_price_obj(self, obj):
        if not hasattr(obj, '_cached_prev_price'):
            prices = list(obj.prices.order_by('-timestamp')[:2])
            obj._cached_prev_price = prices[1] if len(prices) > 1 else None
        return obj._cached_prev_price

    def get_latest_price(self, obj):
        latest = self._get_latest_price_obj(obj)
        return float(latest.close_price) if latest else 0.0

    def get_change(self, obj):
        latest = self._get_latest_price_obj(obj)
        prev = self._get_prev_price_obj(obj)
        if latest and prev and prev.close_price > 0:
            return round(float(latest.close_price - prev.close_price), 2)
        elif latest and latest.open_price > 0:
            return round(float(latest.close_price - latest.open_price), 2)
        return 0.0

    def get_change_percent(self, obj):
        latest = self._get_latest_price_obj(obj)
        prev = self._get_prev_price_obj(obj)
        if latest and prev and prev.close_price > 0:
            pct = ((latest.close_price - prev.close_price) / prev.close_price) * 100
            return round(float(pct), 2)
        elif latest and latest.open_price > 0:
            pct = ((latest.close_price - latest.open_price) / latest.open_price) * 100
            return round(float(pct), 2)
        return 0.0

    def get_day_high(self, obj):
        latest = self._get_latest_price_obj(obj)
        return float(latest.high_price) if latest else 0.0

    def get_day_low(self, obj):
        latest = self._get_latest_price_obj(obj)
        return float(latest.low_price) if latest else 0.0

    def get_volume(self, obj):
        latest = self._get_latest_price_obj(obj)
        return int(latest.volume) if latest else 0

class StockPriceSerializer(serializers.ModelSerializer):
    class Meta:
        model = StockPrice
        # ফ্লাটারের ক্যান্ডেলস্টিক চার্টের জন্য ফিল্ডগুলো
        fields = ['timestamp', 'open_price', 'high_price', 'low_price', 'close_price', 'volume']
