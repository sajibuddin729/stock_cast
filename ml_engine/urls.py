from django.urls import path
from .views import ModelStatsView, NextForecastView

urlpatterns = [
    path('stats/', ModelStatsView.as_view(), name='model-stats'),
    path('forecast/<str:symbol>/', NextForecastView.as_view(), name='next-forecast'),
]
