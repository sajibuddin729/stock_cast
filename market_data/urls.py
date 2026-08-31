from django.urls import path
from .views import StockListView, StockPriceHistoryView

urlpatterns = [
    path('stocks/', StockListView.as_view(), name='stock-list'),
    path('stocks/<str:symbol>/history/', StockPriceHistoryView.as_view(), name='stock-history'),
]
