from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import ModelPerformance, StockPrediction
from .serializers import ModelPerformanceSerializer, StockPredictionSerializer
from market_data.models import Stock

class ModelStatsView(generics.ListAPIView):
    """
    অ্যাপের ফোরকাস্ট স্ক্রিনে মডেলের নাম এবং অ্যাকুরেসি দেখানোর জন্য।
    """
    queryset = ModelPerformance.objects.filter(is_active=True)
    serializer_class = ModelPerformanceSerializer

class NextForecastView(APIView):
    """
    নির্দিষ্ট স্টকের আগামী কয়েক মিনিটের/দিনের প্রেডিকশন লিস্ট দেখানোর জন্য।
    """
    def get(self, request, symbol):
        try:
            stock = Stock.objects.get(symbol=symbol.upper())
            # সর্বশেষ ১০টি প্রেডিকশন পাঠানো হচ্ছে
            predictions = StockPrediction.objects.filter(stock=stock).order_by('-predicted_for_time')[:10]
            serializer = StockPredictionSerializer(predictions, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Stock.DoesNotExist:
            return Response({"error": "Stock not found"}, status=status.HTTP_404_NOT_FOUND)
