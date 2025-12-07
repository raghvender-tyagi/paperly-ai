# Gunicorn configuration file
# This file is read automatically by Gunicorn regardless of start command

# Timeout for LLM API calls (10 minutes)
timeout = 600

# Workers - keep low for memory constraints (512MB free tier)
workers = 1

# Threads for I/O concurrency
threads = 4

# Bind to Render's expected port
bind = "0.0.0.0:10000"

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"
