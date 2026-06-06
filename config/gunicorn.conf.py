"""Gunicorn — production (Render)."""
import os

bind = f"0.0.0.0:{os.environ.get('PORT', '8000')}"
workers = int(os.environ.get("WEB_CONCURRENCY", 2))
threads = int(os.environ.get("WEB_THREADS", 2))
worker_class = "gthread"
timeout = int(os.environ.get("GUNICORN_TIMEOUT", 120))
keepalive = 5
max_requests = int(os.environ.get("GUNICORN_MAX_REQUESTS", 1000))
max_requests_jitter = 50
preload_app = True
accesslog = "-"
errorlog = "-"
capture_output = True
