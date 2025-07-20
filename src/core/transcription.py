from google.cloud import speech
from google.cloud import storage
import os
from pydub import AudioSegment
from ..utils.logger import logger

def upload_to_gcs(file_path, bucket_name):
    """Uploads a file to Google Cloud Storage and returns its gs:// URI."""
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    
    # Use a unique name for the file in storage
    destination_blob_name = f"temp_transcription_segments/{os.path.basename(file_path)}"
    blob = bucket.blob(destination_blob_name)

    blob.upload_from_filename(file_path)
    
    gcs_uri = f"gs://{bucket_name}/{destination_blob_name}"
    logger.info(f"File {file_path} uploaded to {gcs_uri}")
    return gcs_uri, destination_blob_name

def delete_from_gcs(bucket_name, blob_name):
    """Deletes a file from Google Cloud Storage."""
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(blob_name)
    blob.delete()
    logger.info(f"Blob {blob_name} deleted.")

def transcribe_audio(audio_path, language_code="en-US"):
    client = speech.SpeechClient()
    
    # Determine audio duration
    audio_segment = AudioSegment.from_wav(audio_path)
    duration_seconds = len(audio_segment) / 1000.0

    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=16000,
        language_code=language_code,
    )

    # If audio is shorter than 60 seconds, use synchronous method
    if duration_seconds < 60:
        with open(audio_path, "rb") as audio_file:
            content = audio_file.read()
        audio = speech.RecognitionAudio(content=content)
        response = client.recognize(config=config, audio=audio)
        return response

    # Otherwise, use asynchronous method
    else:
        logger.info(f"Audio segment is longer than 60s ({duration_seconds}s). Using long-running recognition.")
        bucket_name = os.getenv('FIREBASE_STORAGE_BUCKET')
        gcs_uri, blob_name = upload_to_gcs(audio_path, bucket_name)
        
        audio = speech.RecognitionAudio(uri=gcs_uri)
        
        operation = client.long_running_recognize(config=config, audio=audio)
        logger.info("Waiting for long-running transcription operation to complete...")
        response = operation.result(timeout=900) # 15 minute timeout for the operation
        
        # Delete temporary file from storage
        delete_from_gcs(bucket_name, blob_name)
        
        return response
