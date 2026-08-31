from django.contrib import admin
from .models import StockPrediction, ModelPerformance

@admin.register(StockPrediction)
class StockPredictionAdmin(admin.ModelAdmin):
    list_display = ('stock', 'predicted_for_time', 'predicted_close_price', 'created_at')
    list_filter = ('stock',)

@admin.register(ModelPerformance)
class ModelPerformanceAdmin(admin.ModelAdmin):
    list_display = ('model_name', 'accuracy_percentage', 'is_active', 'last_trained')
    list_filter = ('is_active',)
