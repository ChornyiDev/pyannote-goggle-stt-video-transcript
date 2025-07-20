import logging
import os
from logging.handlers import RotatingFileHandler

 # Create logs directory if it does not exist
if not os.path.exists('logs'):
    os.makedirs('logs')

 # Logger setup
logger = logging.getLogger('pyannote-api')
logger.setLevel(logging.INFO)

 # Create handler to write logs to file
 # RotatingFileHandler automatically manages file size
file_handler = RotatingFileHandler('logs/app.log', maxBytes=5*1024*1024, backupCount=2)
file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(file_formatter)

 # Create handler for console log output
stream_handler = logging.StreamHandler()
stream_formatter = logging.Formatter('%(levelname)s: %(message)s')
stream_handler.setFormatter(stream_formatter)

 # Add handlers to logger
logger.addHandler(file_handler)
logger.addHandler(stream_handler)
