import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from market_data.models import StockPrice
from .models import StockPrediction
from datetime import timedelta

def train_and_predict(stock):
    """
    নির্দিষ্ট স্টকের পূর্বের ডেটা নিয়ে ML মডেল ট্রেন করবে 
    এবং আগামী ১ মিনিটের দাম প্রেডিক্ট করবে।
    """
    # স্টকের সর্বশেষ ২০০ ডেটা পয়েন্ট নিয়ে আসা (মডেল ট্রেনের জন্য)
    prices_qs = StockPrice.objects.filter(stock=stock).order_by('-timestamp')[:200]
    
    # কমপক্ষে ১০টি ডেটা পয়েন্ট থাকলে মডেল কাজ করতে পারবে
    if prices_qs.count() < 10:
        return None 
    
    # Django QuerySet কে Pandas DataFrame-এ রূপান্তর
    prices_list = list(prices_qs.values('timestamp', 'close_price'))[::-1]
    df = pd.DataFrame(prices_list)
    
    # X (ইনপুট) হিসেবে টাইম ইনডেক্স এবং Y (আউটপুট) হিসেবে দাম ব্যবহার করছি
    df['time_index'] = np.arange(len(df))
    X = df[['time_index']]
    y = df['close_price']
    
    # মডেল ইনিশিয়ালাইজ ও ট্রেইনিং
    model = LinearRegression()
    model.fit(X, y)
    
    # ঠিক পরের ক্যান্ডেলের (time_index) দাম প্রেডিক্ট করা
    next_index = pd.DataFrame({'time_index': [len(df)]})
    predicted_price = float(model.predict(next_index)[0])
    
    # আগামী ১ মিনিটের টাইমস্ট্যাম্প বের করা
    last_real_time = df['timestamp'].iloc[-1]
    next_forecast_time = last_real_time + timedelta(minutes=1)
    
    # প্রেডিকশন ডাটাবেসে সেভ করা
    StockPrediction.objects.create(
        stock=stock,
        predicted_for_time=next_forecast_time,
        predicted_close_price=predicted_price
    )
    
    # ফ্লাটার অ্যাপে পাঠানোর জন্য ডেটা রিটার্ন করা
    return {
        'symbol': stock.symbol,
        'market_type': stock.market_type,
        'is_prediction': True,
        'predicted_for_time': str(next_forecast_time),
        'predicted_close_price': round(predicted_price, 4)
    }
