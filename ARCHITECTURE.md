# System Architecture

This document describes the architecture of the API service for diarization and transcription of media files.

---

## 1. System Components

The system is built on a microservice architecture and consists of the following key components:

1.  **API Server (Flask):**
    -   Accepts `POST` requests at the `/api/transcribe` endpoint.
    -   Validates input data (`media_url`, `firestore_ref`, etc.).
    -   Immediately puts heavy media processing tasks into the Redis queue.
    -   Responds to the client instantly, without blocking the connection.
    -   Also provides the `/api/health` endpoint for queue monitoring.

2.  **Task Queue (Redis + RQ):**
    -   Used for managing asynchronous tasks.
    -   Allows the API server to remain fast and responsive by offloading long operations to the background.

3.  **Background Worker (RQ Worker):**
    -   A separate process launched alongside the main application.
    -   Continuously listens to the Redis queue.
    -   When a new task appears, the worker picks it up and sequentially executes all processing stages.

4.  **Google Cloud & Firebase Services:**
    -   **Firebase Firestore:** Used as a database to store processing statuses (`QUEUED`, `DOWNLOADING`, `PROCESSING`, `DONE`, `ERROR`) and the final result (transcript, metadata).
    -   **Google Cloud Storage:** Used for temporary storage of long audio segments (> 60 seconds) for asynchronous transcription.

---

## 2. Request Lifecycle

1.  **Initiation:** The client sends a `POST` request to `/api/transcribe` with the media file URL and a reference to a Firestore document.

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
    -   **Transcription (Parallel):**
        -   All obtained audio segments are sent for transcription to Google Cloud Speech-to-Text **simultaneously** using `ThreadPoolExecutor`.
        -   **Long segment handling:** If a segment is longer than 60 seconds, it is uploaded to Google Cloud Storage and transcribed using the asynchronous API (`long_running_recognize`).
    -   **Completion:**
        -   Transcription results are collected and sorted.
        -   The Firestore document is updated: `status: 'DONE'`, final transcript, metadata, and `finished_at` timestamp are added.
    -   **Error handling:** If an error occurs at any stage, the status is changed to `ERROR`, an error message and `finished_at` timestamp are recorded.
    -   **Cleanup:** All temporary files (downloaded media, WAV, audio segments) are deleted from the server's local storage.

---

## 3. Application Launch

The application is launched as a Python module from the project root directory. This is critical for correct relative imports between project files.

```bash
python3 -m src.app
```

When started, `src/app.py` automatically launches the worker process using the `multiprocessing` module.
