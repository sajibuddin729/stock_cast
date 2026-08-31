from django.db import models
from market_data.models import Stock

class StockPrediction(models.Model):
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE, related_name='predictions')
    predicted_for_time = models.DateTimeField(db_index=True)  # কোন সময়ের জন্য ফোরকাস্ট করা হয়েছে
    predicted_close_price = models.DecimalField(max_digits=15, decimal_places=4)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-predicted_for_time']

    def __str__(self):
        return f"{self.stock.symbol} - Forecast for {self.predicted_for_time}: {self.predicted_close_price}"

class ModelPerformance(models.Model):
    model_name = models.CharField(max_length=50)  # e.g., 'Linear Regression', 'LSTM'
    accuracy_percentage = models.DecimalField(max_digits=5, decimal_places=2)  # e.g., 87.20
    is_active = models.BooleanField(default=True)
    last_trained = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.model_name} - {self.accuracy_percentage}%"
