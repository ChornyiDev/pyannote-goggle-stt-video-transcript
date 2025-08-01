
# Media File Processing API

This project is a **production-ready** API service for automatic diarization (speaker recognition) and transcription (speech-to-text) of audio and video files with optional webhook notifications.

## 🚀 Technologies

-   **Server:** Gunicorn + Flask (Production WSGI)
-   **Background tasks:** Redis + RQ (Redis Queue)
-   **Diarization:** `pyannote` with speaker segment merging
-   **Transcription:** Google Cloud Speech-to-Text
-   **Data storage:** Firebase (Firestore, Storage)
-   **Conversion:** FFMPEG
-   **Notifications:** Webhook system for completion alerts

## ✨ Key Features

-   **Structured Transcript Format:** Results stored as organized array with speaker, time, and text for each segment
-   **Speaker Segment Merging:** Consecutive segments from the same speaker are automatically merged for coherent transcripts
-   **Production Ready:** Gunicorn WSGI server with systemd service management
-   **Webhook Notifications:** Optional POST notifications when processing completes
-   **Long File Support:** 2-hour timeout for processing large video files
-   **Parallel Transcription:** Multiple audio segments processed simultaneously
-   **Auto Cleanup:** Temporary files automatically removed after processing

---

## 🛠️ Setup

### 1. Prerequisites

-   **Python 3.9+**
-   **FFMPEG:** Install `ffmpeg` on your system.
    -   **Ubuntu/Debian:** `sudo apt update && sudo apt install ffmpeg`
    -   **macOS (Homebrew):** `brew install ffmpeg`

### 2. Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/ChornyiDev/pyannote-goggle-stt-video-transcript.git
    cd video-transcript
    ```

2.  **Create a virtual environment:**
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

### 3. Configuration

1.  **Create a `.env` file** in the project root and add the following variables:

    ```env
    # Google Cloud and Firebase credentials
    GOOGLE_APPLICATION_CREDENTIALS=service_account.json
    FIREBASE_CREDENTIALS_PATH=service_account.json
    FIREBASE_STORAGE_BUCKET=your-bucket-name.appspot.com

    # Your Redis URL
    REDIS_URL=redis://localhost:6379

    # Hugging Face access token
    HUGGING_FACE_TOKEN=your_hugging_face_token

    # Optional: Webhook notification URL
    NOTIFICATION_SERVICE_URL=https://your-webhook-service.com/webhook
    ```

2.  **Login to Hugging Face:**
    ```bash
    huggingface-cli login
    ```

3.  **Accept model usage terms:**
    -   [pyannote/speaker-diarization](https://huggingface.co/pyannote/speaker-diarization)

---

## ▶️ Running

### Development Mode

To start the server and worker in development mode, run from the **project root directory**:

```bash
# Activate the virtual environment
source venv/bin/activate

python3 -m src.app
```

**Important:** Running via `python3 -m src.app` is critical for correct imports.

### Production Mode

For production deployment with Gunicorn:

```bash
# Install production dependencies
pip install gunicorn

# Run with Gunicorn
gunicorn -c gunicorn.conf.py wsgi:app
```

The server will be available at `http://localhost:5012`.

### Systemd Service (Recommended for Production)

Configure as a systemd service for automatic startup and management:

```bash
# The service is already configured if using the included setup
sudo systemctl start video-transcript
sudo systemctl enable video-transcript
sudo systemctl status video-transcript
```

---

## ⚙️ Diarization Model Selection

You can easily change the diarization model to balance speed and accuracy.

1.  **Open the file:** `src/core/diarization.py`
2.  **Find the line** with `Pipeline.from_pretrained(...)`.
3.  **Replace the model name** with one of the options below.

#### Available models:

-   `pyannote/speaker-diarization@2.1`
    -   **Speed:** High (recommended for CPU).
    -   **Accuracy:** Good.
    -   **Terms to accept:**
        -   [pyannote/speaker-diarization](https://huggingface.co/pyannote/speaker-diarization)
        -   [pyannote/segmentation](https://huggingface.co/pyannote/segmentation)

-   `pyannote/speaker-diarization-3.1`
    -   **Speed:** Low (recommended **only** for GPU).
    -   **Accuracy:** Very high.
    -   **Terms to accept:**
        -   [pyannote/speaker-diarization-3.1](https://huggingface.co/pyannote/speaker-diarization-3.1)
        -   [pyannote/segmentation-3.0](https://huggingface.co/pyannote/segmentation-3.0)

**Important:** Before using a new model, make sure you have accepted its terms (and its dependencies) on the Hugging Face website.

---

## 🔌 API

### Start Processing

-   **Endpoint:** `POST /api/transcribe`
-   **Description:** Initiates asynchronous media file processing.

-   **API Key Validation:**
    > The system only checks for the presence of the `api_key` field in the request. The actual validity of the key is not verified. If the key is missing, the request will be rejected with a 401 error.

-   **Request body (JSON):**
    ```json
    {
      "media_url": "gs://your-bucket/path/to/file.mp4",
      "firestore_ref": "collection_name/document_id",
      "language": "en-US",
      "api_key": "your_api_key",
      "notification": true
    }
    ```

#### Request Parameters:

- `media_url` (required): URL to the media file (supports HTTP/HTTPS and gs:// URLs)
- `firestore_ref` (required): Firestore document reference for storing results
- `language` (optional): Language code for transcription (default: "en-US")
- `api_key` (required): API key for authentication
- `notification` (optional): Set to `true` to receive webhook notification when processing completes

-   **Response (202):**
    ```json
    {
      "message": "Processing started"
    }
    ```

**Processing Results:** The transcription results are stored in Firestore as a structured array. See the [Response Format](#-response-format) section for detailed structure.

### Check Status

-   **Endpoint:** `GET /api/health`
-   **Description:** Returns the status of the task queue.

---

## 🔔 Webhook Notifications

When `notification: true` is included in the transcription request, the system will send a POST webhook to the configured `NOTIFICATION_SERVICE_URL` after processing completes.

### Webhook Payload

The webhook sends a JSON payload containing the Firestore reference:

```json
{
  "firestore_ref": "collection_name/document_id"
}
```

### Notification Triggers

- **Success:** When transcription completes successfully (`status: "DONE"`)
- **Error:** When processing fails (`status: "ERROR"`)

### Configuration

Set the webhook URL in your `.env` file:

```env
NOTIFICATION_SERVICE_URL=https://your-webhook-service.com/webhook
```

### Example Integration

Use notifications to trigger downstream processes like:
- Sending completion emails
- Updating external systems
- Starting additional processing workflows
- Analytics and monitoring

---

## 🏗️ Architecture

For detailed system architecture and component descriptions, see [ARCHITECTURE.md](ARCHITECTURE.md).

---

## 📝 Speaker Segment Processing

The system automatically processes and merges consecutive audio segments from the same speaker to create coherent and readable transcripts in structured format.

### Segment Merging

**Raw segments (before merging):**
```
SPEAKER_00: hello hello
SPEAKER_00: hello  
SPEAKER_00: what's up how are you doing
```

**Processed result (after merging):**
```json
{
  "speaker": "SPEAKER_00",
  "time": "00:00",
  "transcript": "hello hello hello what's up how are you doing"
}
```

### Time Stamping

Each merged segment includes:
- **Speaker identification** for clear dialogue attribution
- **Time stamps** in HH:MM format for easy navigation
- **Clean text** with merged consecutive utterances

This processing significantly improves transcript readability and provides structured data for frontend applications.

---

## 📋 Response Format

### Firestore Document Structure

When processing completes, the following data is stored in Firestore:

```json
{
  "status": "DONE",
  "transcript": [
    {
      "speaker": "SPEAKER_00",
      "time": "00:00",
      "transcript": "Hello, how are you today?"
    },
    {
      "speaker": "SPEAKER_01", 
      "time": "00:15",
      "transcript": "I am doing great, thank you for asking!"
    },
    {
      "speaker": "SPEAKER_00",
      "time": "00:30",
      "transcript": "That is wonderful to hear."
    }
  ],
  "metadata": {
    "duration": 125.5,
    "speakers_count": 2,
    "processing_time": 45.3,
    "language": "en-US"
  },
  "received_at": "2025-08-01T10:00:00Z",
  "finished_at": "2025-08-01T10:02:15Z"
}
```

### Status Values

- `"QUEUED"` - Task has been queued for processing
- `"DOWNLOADING"` - Media file is being downloaded
- `"PROCESSING"` - Diarization and transcription in progress
- `"DONE"` - Processing completed successfully
- `"ERROR"` - Processing failed (includes `error_message` field)

### Transcript Structure

Each transcript segment contains:
- `speaker` - Speaker identifier (e.g., "SPEAKER_00", "SPEAKER_01")
- `time` - Start time in HH:MM format for easy display
- `transcript` - The transcribed text for this segment

### Features

- Segments are automatically sorted by time
- Consecutive segments from the same speaker are merged
- Time format is optimized for frontend consumption
- Structured format enables easy filtering and searching