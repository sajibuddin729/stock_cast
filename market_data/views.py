from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from .models import Stock, StockPrice
from .serializers import StockSerializer, StockPriceSerializer

class StockListView(APIView):
    """
    অ্যাপের হোমপেজ বা ওয়াচলিস্টের জন্য এভেইলেবল সব স্টকের লিস্ট দিবে।
    Supports filtering: ?market_type=DSE or ?market_type=GLOBAL or ?search=GP
    """
    def get(self, request):
        stocks = Stock.objects.filter(is_active=True)
        
        market_type = request.query_params.get('market_type')
        if market_type:
            stocks = stocks.filter(market_type=market_type.upper())
            
        search = request.query_params.get('search')
        if search:
            stocks = stocks.filter(symbol__icontains=search) | stocks.filter(name__icontains=search)

        serializer = StockSerializer(stocks, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class StockPriceHistoryView(APIView):
    """
    ফ্লাটার অ্যাপের চার্ট ড্র করার জন্য নির্দিষ্ট স্টকের OHLC ডেটা দিবে।
    """
    def get(self, request, symbol):
        stock = get_object_or_404(Stock, symbol=symbol.upper(), is_active=True)
        
        # ডিফল্টভাবে লেটেস্ট ১০০ ডেটা পয়েন্ট পাঠাবো চার্টের জন্য
        limit = int(request.query_params.get('limit', 100))
        
        prices = StockPrice.objects.filter(stock=stock).order_by('-timestamp')[:limit]
        
        # চার্ট সাধারণত পুরোনো থেকে নতুন ডেটা রেন্ডার করে, তাই ডাটা রিভার্স করে দিচ্ছি
        prices = list(reversed(prices))
        
        serializer = StockPriceSerializer(prices, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
