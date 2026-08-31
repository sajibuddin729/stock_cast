from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    # ফ্লাটার অ্যাপ এই URL এ কানেক্ট করবে: ws://127.0.0.1:8000/ws/live/
    re_path(r'ws/live/$', consumers.StockPriceConsumer.as_asgi()),
]
