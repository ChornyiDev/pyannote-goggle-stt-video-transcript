#!/usr/bin/env python3
"""WSGI entry point for production deployment with Gunicorn."""

import multiprocessing
import atexit
from src.app import app, start_worker, stop_worker
from src.utils.logger import logger

# Start the worker when the WSGI app is created
start_worker()

# Register function to stop the worker on exit
atexit.register(stop_worker)

logger.info("WSGI app initialized with worker process")

if __name__ == "__main__":
    app.run()
