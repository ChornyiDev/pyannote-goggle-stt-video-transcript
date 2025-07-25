# Gunicorn configuration file
import multiprocessing

# Server socket
bind = "0.0.0.0:5012"
backlog = 2048

# Worker processes
workers = 1
worker_class = "sync"
worker_connections = 1000
timeout = 7200  # 2 hours timeout for long-running transcription tasks
keepalive = 2

# Restart workers after this many requests, to help prevent memory leaks
max_requests = 1000
max_requests_jitter = 100

# Logging
loglevel = "info"
accesslog = "-"
errorlog = "-"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = 'gunicorn_video_transcript'

# Server mechanics
daemon = False
pidfile = '/tmp/gunicorn_video_transcript.pid'
tmp_upload_dir = None

# SSL (if needed)
# keyfile = None
# certfile = None
