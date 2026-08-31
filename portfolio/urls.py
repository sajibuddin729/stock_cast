from django.urls import path
from .views import (
    UserProfileView,
    WatchlistView,
    WatchlistDeleteView,
    TransactionListCreateView,
    PortfolioHistoryOverviewView,
    WalletTransactionListCreateView,
    SSLCommerzInitiateView,
    SSLCommerzSuccessCallbackView,
    SSLCommerzFailCallbackView,
    SSLCommerzCancelCallbackView,
)

urlpatterns = [
    path('profile/', UserProfileView.as_view(), name='user-profile'),
    path('watchlist/', WatchlistView.as_view(), name='watchlist-list-create'),
    path('watchlist/<int:pk>/', WatchlistDeleteView.as_view(), name='watchlist-delete'),
    path('transactions/', TransactionListCreateView.as_view(), name='transaction-list-create'),
    path('history-overview/', PortfolioHistoryOverviewView.as_view(), name='portfolio-history-overview'),
    
    # Wallet & Payment Gateway APIs
    path('wallet/transactions/', WalletTransactionListCreateView.as_view(), name='wallet-transactions-list'),
    path('wallet/transaction/', WalletTransactionListCreateView.as_view(), name='wallet-transaction-create'),
    path('payment/sslcommerz/initiate/', SSLCommerzInitiateView.as_view(), name='sslcommerz-initiate'),
    path('payment/sslcommerz/success/', SSLCommerzSuccessCallbackView.as_view(), name='sslcommerz-success'),
    path('payment/sslcommerz/fail/', SSLCommerzFailCallbackView.as_view(), name='sslcommerz-fail'),
    path('payment/sslcommerz/cancel/', SSLCommerzCancelCallbackView.as_view(), name='sslcommerz-cancel'),
]
