from django.contrib import admin
from .models import Stock, StockPrice

@admin.register(Stock)
class StockAdmin(admin.ModelAdmin):
    list_display = ('symbol', 'name', 'market_type', 'is_active')
    list_filter = ('market_type', 'is_active')

@admin.register(StockPrice)
class StockPriceAdmin(admin.ModelAdmin):
    list_display = ('stock', 'timestamp', 'close_price', 'volume')
    list_filter = ('stock',)
