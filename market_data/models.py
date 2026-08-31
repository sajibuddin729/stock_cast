from django.db import models

class Stock(models.Model):
    MARKET_CHOICES = (
        ('GLOBAL', 'Global Market'),
        ('DSE', 'Dhaka Stock Exchange'),
    )
    
    symbol = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100, blank=True, null=True)
    market_type = models.CharField(max_length=20, choices=MARKET_CHOICES, default='GLOBAL')
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.symbol} ({self.market_type})"

class StockPrice(models.Model):
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE, related_name='prices')
    timestamp = models.DateTimeField(db_index=True)  # db_index=True রাখা জরুরি টাইম-সিরিজ ডেটা দ্রুত খোঁজার জন্য
    open_price = models.DecimalField(max_digits=15, decimal_places=4)
    high_price = models.DecimalField(max_digits=15, decimal_places=4)
    low_price = models.DecimalField(max_digits=15, decimal_places=4)
    close_price = models.DecimalField(max_digits=15, decimal_places=4)
    volume = models.BigIntegerField(default=0)

    class Meta:
        # একই স্টকের একই সময়ের ডেটা যেন দুবার সেভ না হয়
        unique_together = ('stock', 'timestamp')
        ordering = ['-timestamp']  # সবসময় লেটেস্ট ডেটা আগে আসবে

    def __str__(self):
        return f"{self.stock.symbol} - {self.timestamp} - Close: {self.close_price}"
