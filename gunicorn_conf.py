# gunicorn_conf.py
# This is a configuration file for gunicorn to properly use uvicorn workers with FastAPI

# Bind to all network interfaces on port 5000
bind = "0.0.0.0:5000"

# Use uvicorn worker for ASGI compatibility with FastAPI
worker_class = "uvicorn.workers.UvicornWorker"

# Number of worker processes
workers = 1

# Enable reloading when code changes
reload = True

# Reuse port for faster restarting
reuse_port = True

# Log level
loglevel = "debug"

# Enable auto-reload
reload_engine = "auto"