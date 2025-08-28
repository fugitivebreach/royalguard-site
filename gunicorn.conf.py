import os

bind = f"0.0.0.0:{os.environ.get('PORT', 5000)}"
workers = 1
timeout = 120
keepalive = 2
max_requests = 1000
max_requests_jitter = 100
preload_app = True
worker_class = "sync"

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'

# Process naming
proc_name = "royal-guard-dashboard"

# Worker process management
worker_tmp_dir = "/dev/shm"
tmp_upload_dir = None
