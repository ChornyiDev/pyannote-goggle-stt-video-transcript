# System Architecture

This document describes the architecture of the API service for diarization and transcription of media files.

---

## 1. System Components

The system is built on a microservice architecture and consists of the following key components:

1.  **API Server (Gunicorn + Flask):**
    -   Production-ready WSGI server running Flask application.
    -   Accepts `POST` requests at the `/api/transcribe` endpoint.
    -   Validates input data (`media_url`, `firestore_ref`, `language`, `api_key`, `notification`).
    -   Immediately puts heavy media processing tasks into the Redis queue.
    -   Responds to the client instantly, without blocking the connection.
    -   Also provides the `/api/health` endpoint for queue monitoring.

2.  **Task Queue (Redis + RQ):**
    -   Used for managing asynchronous tasks.
    -   Allows the API server to remain fast and responsive by offloading long operations to the background.
    -   Configured with 2-hour timeout for processing large files.

3.  **Background Worker (RQ Worker):**
    -   A single worker process launched alongside the main application.
    -   Continuously listens to the Redis queue.
    -   When a new task appears, the worker picks it up and sequentially executes all processing stages.

4.  **Google Cloud & Firebase Services:**
    -   **Firebase Firestore:** Used as a database to store processing statuses (`QUEUED`, `DOWNLOADING`, `PROCESSING`, `DONE`, `ERROR`) and the final result (transcript, metadata).
    -   **Google Cloud Storage:** Used for temporary storage of long audio segments (> 60 seconds) for asynchronous transcription.

5.  **Notification System:**
    -   Optional webhook notifications sent after processing completion.
    -   Configurable via `NOTIFICATION_SERVICE_URL` environment variable.
    -   Supports both success and error notifications.

---

## 2. Request Lifecycle

1.  **Initiation:** The client sends a `POST` request to `/api/transcribe` with the media file URL, Firestore reference, and optional notification flag.

**Request Format:**
```json
{
    "media_url": "https://example.com/video.mp4",
    "firestore_ref": "context/BEmVPZbX0owhv6OvjQgy",
    "language": "en-US",
    "api_key": "your_api_key",
    "notification": true
}
```

2.  **Queueing:**
    -   The Flask server receives the request.
    -   Updates the Firestore document, setting `status: 'QUEUED'` and the `received_at` timestamp.
    -   Creates a `process_media_task` and adds it to the Redis queue.
    -   Responds to the client with `{"message": "Processing started"}`.

3.  **Worker Execution:**
    -   The RQ worker in the background picks up the task from the queue.
    -   **Downloading:**
        -   Updates the status in Firestore to `DOWNLOADING`.
        -   Downloads the media file from the specified URL.
    -   **Conversion:**
        -   Converts the downloaded file to WAV format (`mono`, `16000 Hz`) using **FFMPEG**. The `ffmpeg-python` library is used with the `-nostdin` flag for stable background operation.
    -   **Diarization:**
        -   Updates the status to `PROCESSING`.
        -   Applies the `pyannote/speaker-diarization` model to split audio into speaker segments.
        -   **Speaker Segment Merging:** Consecutive segments from the same speaker are automatically merged to create more coherent transcripts.
    -   **Transcription (Parallel):**
        -   All obtained audio segments are sent for transcription to Google Cloud Speech-to-Text **simultaneously** using `ThreadPoolExecutor`.
        -   **Long segment handling:** If a segment is longer than 60 seconds, it is uploaded to Google Cloud Storage and transcribed using the asynchronous API (`long_running_recognize`).
    -   **Completion:**
        -   Transcription results are collected and sorted.
        -   The Firestore document is updated: `status: 'DONE'`, final transcript, metadata, and `finished_at` timestamp are added.
        -   **Notification:** If `notification: true` was specified, a webhook is sent to `NOTIFICATION_SERVICE_URL` with the `firestore_ref`.
    -   **Error handling:** If an error occurs at any stage, the status is changed to `ERROR`, an error message and `finished_at` timestamp are recorded. Error notifications are also sent if enabled.
    -   **Cleanup:** All temporary files (downloaded media, WAV, audio segments) are deleted from the server's local storage.

---

## 3. Production Deployment

The application runs in production mode using Gunicorn WSGI server with systemd service management.

**Launch Command:**
```bash
gunicorn -c gunicorn.conf.py wsgi:app
```

**Configuration:**
- **Single Worker:** Optimized for sequential processing of media files
- **2-Hour Timeout:** Allows processing of large video files
- **Production Logging:** Structured logging with proper log levels
- **Auto-restart:** Systemd manages process lifecycle and restarts

**Development Mode:**
For development, the application can still be launched directly:
```bash
python3 -m src.app
```

When started in development mode, `src/app.py` automatically launches the worker process using the `multiprocessing` module.

---

## 4. Notification System

When `notification: true` is specified in the request, the system will send a POST webhook to the configured `NOTIFICATION_SERVICE_URL` after processing completion.

**Webhook Payload:**
```json
{
    "firestore_ref": "context/BEmVPZbX0owhv6OvjQgy"
}
```

**Notification Triggers:**
- Successful completion (`status: "DONE"`)
- Processing errors (`status: "ERROR"`)

**Configuration:**
Set the `NOTIFICATION_SERVICE_URL` environment variable in the `.env` file.
