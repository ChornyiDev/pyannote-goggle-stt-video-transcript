from google.cloud import speech
from google.cloud import storage
import os
from pydub import AudioSegment
from ..utils.logger import logger

def upload_to_gcs(file_path, bucket_name):
    """Завантажує файл у Google Cloud Storage та повертає його gs:// URI."""
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    
    # Використання унікального імені для файлу в сховищі
    destination_blob_name = f"temp_transcription_segments/{os.path.basename(file_path)}"
    blob = bucket.blob(destination_blob_name)

    blob.upload_from_filename(file_path)
    
    gcs_uri = f"gs://{bucket_name}/{destination_blob_name}"
    logger.info(f"File {file_path} uploaded to {gcs_uri}")
    return gcs_uri, destination_blob_name

def delete_from_gcs(bucket_name, blob_name):
    """Видаляє файл з Google Cloud Storage."""
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(blob_name)
    blob.delete()
    logger.info(f"Blob {blob_name} deleted.")

def transcribe_audio(audio_path, language_code="en-US"):
    client = speech.SpeechClient()
    
    # Визначення тривалості аудіо
    audio_segment = AudioSegment.from_wav(audio_path)
    duration_seconds = len(audio_segment) / 1000.0

    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=16000,
        language_code=language_code,
    )

    # Якщо аудіо коротше 60 секунд, використовується синхронний метод
    if duration_seconds < 60:
        with open(audio_path, "rb") as audio_file:
            content = audio_file.read()
        audio = speech.RecognitionAudio(content=content)
        response = client.recognize(config=config, audio=audio)
        return response

    # Інакше, використовується асинхронний метод
    else:
        logger.info(f"Audio segment is longer than 60s ({duration_seconds}s). Using long-running recognition.")
        bucket_name = os.getenv('FIREBASE_STORAGE_BUCKET')
        gcs_uri, blob_name = upload_to_gcs(audio_path, bucket_name)
        
        audio = speech.RecognitionAudio(uri=gcs_uri)
        
        operation = client.long_running_recognize(config=config, audio=audio)
        logger.info("Waiting for long-running transcription operation to complete...")
        response = operation.result(timeout=900) # 15 хвилин тайм-аут на операцію
        
        # Видалення тимчасового файлу зі сховища
        delete_from_gcs(bucket_name, blob_name)
        
        return response
