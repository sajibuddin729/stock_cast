from django.db import models
from django.contrib.auth.models import User
from market_data.models import Stock

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    current_balance = models.DecimalField(max_digits=15, decimal_places=2, default=50000.00)  # ডেমো ব্যালেন্স

    def __str__(self):
        return f"{self.user.username}'s Profile"

class Watchlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='watchlist')
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'stock')  # একজন ইউজার একই স্টক দুবার অ্যাড করতে পারবে না

    def __str__(self):
        return f"{self.user.username} - {self.stock.symbol}"

class Transaction(models.Model):
    TRANSACTION_TYPES = (
        ('BUY', 'Buy'),
        ('SELL', 'Sell'),
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='transactions')
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE)
    transaction_type = models.CharField(max_length=4, choices=TRANSACTION_TYPES)
    quantity = models.IntegerField()
    price_per_share = models.DecimalField(max_digits=15, decimal_places=4)
    timestamp = models.DateTimeField(auto_now_add=True)

    def total_amount(self):
        return self.quantity * self.price_per_share

    def __str__(self):
        return f"{self.user.username} - {self.transaction_type} {self.quantity} {self.stock.symbol} @ {self.price_per_share}"


class WalletTransaction(models.Model):
    TRANSACTION_TYPES = (
        ('CASH_IN', 'Cash In / Deposit'),
        ('WITHDRAW', 'Withdrawal Payout'),
    )
    STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
        ('CANCELLED', 'Cancelled'),
    )
    PAYMENT_METHODS = (
        ('bKash', 'bKash Mobile Banking'),
        ('Nagad', 'Nagad Mobile Banking'),
        ('Rocket', 'Rocket Mobile Banking'),
        ('SSLCommerz', 'SSLCommerz Gateway'),
        ('Bank', 'Bank Transfer'),
        ('Card', 'Debit/Credit Card'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='wallet_transactions')
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS, default='bKash')
    tran_id = models.CharField(max_length=64, unique=True)
    val_id = models.CharField(max_length=64, blank=True, null=True)
    
    gross_amount = models.DecimalField(max_digits=15, decimal_places=2)  # Requested amount
    fee_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)  # e.g., 1.00%
    fee_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)  # Gross * fee%
    net_amount = models.DecimalField(max_digits=15, decimal_places=2)  # Net balance credited or debited
    amount_bdt = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)  # BDT equivalent
    
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default='PENDING')
    account_number = models.CharField(max_length=50, blank=True, null=True)  # bKash/Nagad number
    reference_note = models.CharField(max_length=255, blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - {self.transaction_type} ({self.tran_id}): {self.net_amount} [{self.status}]"
