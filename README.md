
# Media File Processing API

This project is an API service for automatic diarization (speaker recognition) and transcription (speech-to-text) of audio and video files.

## 🚀 Technologies

-   **Server:** Flask
-   **Background tasks:** Redis + RQ (Redis Queue)
-   **Diarization:** `pyannote`
-   **Transcription:** Google Cloud Speech-to-Text
-   **Data storage:** Firebase (Firestore, Storage)
-   **Conversion:** FFMPEG

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
    git clone <repository_url>
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
    ```

2.  **Login to Hugging Face:**
    ```bash
    huggingface-cli login
    ```

3.  **Accept model usage terms:**
    -   [pyannote/speaker-diarization](https://huggingface.co/pyannote/speaker-diarization)

---

## ▶️ Running

To start the server and worker, run the command from the **project root directory**:

```bash
# Activate the virtual environment
# source venv/bin/activate

python3 -m src.app
```

**Important:** Running via `python3 -m src.app` is critical for correct imports.

The server will be available at `http://localhost:5012`.

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
      "api_key": "your_api_key"
    }
    ```

-   **Response (202):**
    ```json
    {
      "message": "Processing started"
    }
    ```

### Check Status

-   **Endpoint:** `GET /api/health`
-   **Description:** Returns the status of the task queue.