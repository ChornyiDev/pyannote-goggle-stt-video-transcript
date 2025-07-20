from flask import Flask, request, jsonify
from dotenv import load_dotenv
import os
import multiprocessing
import atexit
from datetime import datetime, timezone
from rq import Worker
from .tasks import q
from .utils.logger import logger
from .services.firebase_service import update_firestore

 # Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

logger.info(f"Flask app connecting to Redis at {os.getenv('REDIS_URL')}")

def run_worker():
    """Function to start the worker in a separate process."""
    worker = Worker([q], connection=q.connection)
    logger.info(f"Starting worker for queues: {', '.join(worker.queue_names())}")
    worker.work()

worker_process = None

def start_worker():
    global worker_process
    if worker_process is None or not worker_process.is_alive():
        worker_process = multiprocessing.Process(target=run_worker)
        worker_process.start()
        logger.info(f"Started worker process with PID: {worker_process.pid}")

def stop_worker():
    global worker_process
    if worker_process and worker_process.is_alive():
        logger.info(f"Terminating worker process with PID: {worker_process.pid}")
        worker_process.terminate()
        worker_process.join()

@app.route('/api/health', methods=['GET'])
def health_check():
    """Checks the status of the queue."""
    try:
        queue_length = len(q)
        return jsonify({
            "status": "ok",
            "queue_name": q.name,
            "queue_length": queue_length,
            "queued_job_ids": q.job_ids,
            "failed_job_count": q.failed_job_registry.count,
        }), 200
    except Exception as e:
        logger.error(f"Health check failed: {e}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/transcribe', methods=['POST'])
def transcribe():
    data = request.get_json()
    logger.info(f"Received request: {data}")
    media_url = data.get('media_url')
    firestore_ref = data.get('firestore_ref')
    language = data.get('language', 'en-US')
    api_key = data.get('api_key')

    # API key validation (placeholder)
    if not api_key:
        logger.warning("API key is missing")
        return jsonify({"error": "API key is missing"}), 401

    if not media_url or not firestore_ref:
        logger.error("media_url or firestore_ref is missing")
        return jsonify({"error": "media_url and firestore_ref are required"}), 400

    # Record the time the request was received in Firestore
    try:
        received_time = datetime.now(timezone.utc)
        update_firestore(firestore_ref, {"received_at": received_time, "status": "QUEUED"})
        logger.info(f"[{firestore_ref}] Request received at {received_time}, status set to QUEUED.")
    except Exception as e:
        logger.error(f"[{firestore_ref}] Failed to update Firestore on request received: {e}", exc_info=True)
        # The process is not interrupted, the error is only logged

    logger.info(f"Enqueuing task for {media_url}")
    # Increase timeout to 2 hours (7200 seconds) for processing large files
    q.enqueue('src.tasks.process_media_task', media_url, firestore_ref, language, job_timeout=7200)
    logger.info(f"Task enqueued. Current queue length: {len(q)}")

    return jsonify({"message": "Processing started"})

if __name__ == '__main__':
    # Start the worker in a background process
    start_worker()
    # Register function to stop the worker on exit
    atexit.register(stop_worker)
    
    logger.info("Starting Flask app")
    # Start Flask application
    # use_reloader=False is important to avoid double worker startup
    app.run(host='0.0.0.0', port=5012, debug=True, use_reloader=False)
