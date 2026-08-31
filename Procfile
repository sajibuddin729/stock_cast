web: python manage.py migrate && daphne -b 0.0.0.0 -p $PORT core.asgi:application
worker: celery -A core worker --loglevel=info
beat: celery -A core beat --loglevel=info
