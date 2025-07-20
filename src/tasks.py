from redis import Redis
from rq import Queue
import os
from dotenv import load_dotenv

# Завантаження змінних середовища на самому початку,
# для їх доступності у всіх наступних імпортах.
load_dotenv()

from .utils.logger import logger
from .core.media_processor import process_media

redis_conn = Redis.from_url(os.getenv('REDIS_URL'))
q = Queue(connection=redis_conn)

def process_media_task(media_url, firestore_ref, language):
    logger.info(f"Starting media processing for {media_url}")
    try:
        process_media(media_url, firestore_ref, language)
        logger.info(f"Finished media processing for {media_url}")
    except Exception as e:
        logger.error(f"Error processing {media_url}: {e}", exc_info=True)
