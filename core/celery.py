import os
from celery import Celery

# Celery এর জন্য ডিফল্ট জ্যাঙ্গো সেটিংস মডিউল সেট করা
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

app = Celery('core')

# সেটিংসে CELERY_ দিয়ে শুরু হওয়া কনফিগারেশনগুলো লোড করবে
app.config_from_object('django.conf:settings', namespace='CELERY')

# আমাদের প্রজেক্টের সব অ্যাপ থেকে tasks.py ফাইল স্বয়ংক্রিয়ভাবে খুঁজে নিবে
app.autodiscover_tasks()
