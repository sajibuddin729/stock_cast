from django.contrib import admin
from .models import UserProfile, Watchlist, Transaction

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'current_balance')

@admin.register(Watchlist)
class WatchlistAdmin(admin.ModelAdmin):
    list_display = ('user', 'stock', 'added_at')
    list_filter = ('user', 'stock')

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('user', 'stock', 'transaction_type', 'quantity', 'price_per_share', 'timestamp')
    list_filter = ('user', 'stock', 'transaction_type')
