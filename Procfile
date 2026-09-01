web: gunicorn paperlydjango.wsgi:application --config gunicorn.conf.py
worker: celery -A paperlydjango worker --loglevel=info --concurrency=2
