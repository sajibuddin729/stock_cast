from rest_framework import serializers
from .models import StockPrediction, ModelPerformance

class ModelPerformanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = ModelPerformance
        fields = ['id', 'model_name', 'accuracy_percentage', 'last_trained']

class StockPredictionSerializer(serializers.ModelSerializer):
    stock_symbol = serializers.CharField(source='stock.symbol', read_only=True)

    class Meta:
        model = StockPrediction
        fields = ['stock_symbol', 'predicted_for_time', 'predicted_close_price', 'created_at']
