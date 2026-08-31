import json
from channels.generic.websocket import AsyncWebsocketConsumer

class StockPriceConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # আমরা একটি গ্লোবাল গ্রুপ বানাচ্ছি, যেখানে সব লাইভ আপডেট পাঠানো হবে
        self.group_name = 'live_stock_prices'
        
        # ক্লায়েন্টকে গ্রুপে যুক্ত করা
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        
        # কানেকশন অ্যাক্সেপ্ট করা
        await self.accept()
        
        # কানেক্ট হওয়ার সাথে সাথে একটি ওয়েলকাম মেসেজ পাঠানো (টেস্ট করার জন্য)
        await self.send(text_data=json.dumps({
            'type': 'connection_established',
            'message': 'Connected to live stock prices stream!'
        }))

    async def disconnect(self, close_code):
        # ক্লায়েন্ট ডিসকানেক্ট হলে তাকে গ্রুপ থেকে বাদ দেওয়া
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )

    # এই ফাংশনটি গ্রুপের মাধ্যমে ডেটা রিসিভ করে ফ্লাটার অ্যাপে পাঠাবে
    async def stock_update(self, event):
        data = event['data']
        # ফ্লাটারে JSON ফরম্যাটে ডেটা পাঠানো হচ্ছে
        await self.send(text_data=json.dumps(data))
