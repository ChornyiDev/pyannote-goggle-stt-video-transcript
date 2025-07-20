# API для Обробки Медіафайлів

Цей проєкт є API-сервісом для автоматичної діаризації (розпізнавання спікерів) та транскрипції (перетворення мови в текст) аудіо та відео.

## 🚀 Технології

-   **Сервер:** Flask
-   **Фонові задачі:** Redis + RQ (Redis Queue)
-   **Діаризація:** `pyannote
-   **Транскрипція:** Google Cloud Speech-to-Text
-   **Зберігання даних:** Firebase (Firestore, Storage)
-   **Конвертація:** FFMPEG

---

## 🛠️ Налаштування

### 1. Передумови

-   **Python 3.9+**
-   **FFMPEG:** Встановіть `ffmpeg` у вашій системі.
    -   **Ubuntu/Debian:** `sudo apt update && sudo apt install ffmpeg`
    -   **macOS (Homebrew):** `brew install ffmpeg`

### 2. Встановлення

1.  **Клонуйте репозиторій:**
    ```bash
    git clone <repository_url>
    cd video-transcript
    ```

2.  **Створіть віртуальне середовище:**
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Встановіть залежності:**
    ```bash
    pip install -r requirements.txt
    ```

### 3. Конфігурація

1.  **Створіть файл `.env`** у корені проєкту та додайте наступні змінні:

    ```env
    # Доступ до Google Cloud та Firebase
    GOOGLE_APPLICATION_CREDENTIALS=service_account.json
    FIREBASE_CREDENTIALS_PATH=service_account.json
    FIREBASE_STORAGE_BUCKET=your-bucket-name.appspot.com

    # URL вашого Redis
    REDIS_URL=redis://localhost:6379

    # Токен доступу до Hugging Face
    HUGGING_FACE_TOKEN=your_hugging_face_token
    ```

2.  **Авторизуйтесь у Hugging Face:**
    ```bash
    huggingface-cli login
    ```

3.  **Прийміть умови використання моделі:**
    -   [pyannote/speaker-diarization](https://huggingface.co/pyannote/speaker-diarization)

---

## ▶️ Запуск

Для запуску сервера та воркера виконайте команду з **кореневої директорії проєкту**:

```bash
# Активуйте віртуальне середовище
# source venv/bin/activate

python3 -m src.app
```

**Важливо:** Запуск через `python3 -m src.app` є критичним для правильної роботи імпортів.

Сервер буде доступний за адресою `http://localhost:5012`.

---

## ⚙️ Вибір моделі діаризації

Передбачена можливість легко змінити модель, яка використовується для діаризації, щоб знайти баланс між швидкістю та точністю.

1.  **Відкрити файл:** `src/core/diarization.py`
2.  **Знайти рядок** з `Pipeline.from_pretrained(...)`.
3.  **Замінити назву моделі** на одну з наведених нижче.

#### Доступні моделі:

-   `pyannote/speaker-diarization@2.1`
    -   **Швидкість:** Висока (рекомендовано для CPU).
    -   **Точність:** Добра.
    -   **Необхідно прийняти умови:**
        -   [pyannote/speaker-diarization](https://huggingface.co/pyannote/speaker-diarization)
        -   [pyannote/segmentation](https://huggingface.co/pyannote/segmentation)

-   `pyannote/speaker-diarization-3.1`
    -   **Швидкість:** Низька (рекомендовано **тільки** для GPU).
    -   **Точність:** Дуже висока.
    -   **Необхідно прийняти умови:**
        -   [pyannote/speaker-diarization-3.1](https://huggingface.co/pyannote/speaker-diarization-3.1)
        -   [pyannote/segmentation-3.0](https://huggingface.co/pyannote/segmentation-3.0)

**Важливо:** Перед використанням нової моделі необхідно переконатися, що умови її використання (та її залежностей) прийняті на сайті Hugging Face.

---

## 🔌 API


### Запуск обробки

-   **Ендпоінт:** `POST /api/transcribe`
-   **Опис:** Ініціює асинхронну обробку медіафайлу.

-   **Перевірка API ключа:**
    > Cистема перевіряє лише наявність поля `api_key` у запиті. Валідність ключа не перевіряється. Якщо ключ відсутній, запит буде відхилено з помилкою 401.

-   **Тіло запиту (JSON):**
    ```json
    {
      "media_url": "gs://your-bucket/path/to/file.mp4",
      "firestore_ref": "collection_name/document_id",
      "language": "en-US",
      "api_key": "your_api_key"
    }
    ```

-   **Відповідь (202):**
    ```json
    {
      "message": "Processing started"
    }
    ```

### Перевірка стану

-   **Ендпоінт:** `GET /api/health`
-   **Опис:** Повертає стан черги завдань.