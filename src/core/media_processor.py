import os
import requests
import time
import ffmpeg
import subprocess
import shlex
import glob
from datetime import timedelta, datetime, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed
from firebase_admin import storage
from urllib.parse import unquote
from pydub import AudioSegment

from .diarization import diarize_audio
from .transcription import transcribe_audio
from ..services.firebase_service import update_firestore
from ..utils.logger import logger

def process_media(media_url, firestore_ref, language):
    start_time = time.time()
    original_file_name = None
    wav_file_name = None

    try:
        logger.info(f"[{firestore_ref}] Updating status to DOWNLOADING")
        update_firestore(firestore_ref, {"status": "DOWNLOADING"})

        if media_url.startswith('gs://'):
            bucket_name = os.getenv('FIREBASE_STORAGE_BUCKET')
            bucket = storage.bucket(bucket_name)
            blob_path = media_url.replace(f'gs://{bucket_name}/', '')
            blob = bucket.blob(blob_path)
            download_url = blob.generate_signed_url(version="v4", expiration=timedelta(minutes=15))
        else:
            download_url = media_url

        logger.info(f"[{firestore_ref}] Downloading from {download_url}")
        response = requests.get(download_url)
        response.raise_for_status()

        decoded_path = unquote(download_url.split('?')[0])
        original_file_name = os.path.basename(decoded_path)
        with open(original_file_name, "wb") as f:
            f.write(response.content)
        logger.info(f"[{firestore_ref}] Downloaded to {original_file_name}")

        wav_file_name = f"{os.path.splitext(original_file_name)[0]}.wav"
        logger.info(f"[{firestore_ref}] Converting {original_file_name} to {wav_file_name} using ffmpeg-python library")
        
        try:
            # Final attempt: combine two fixes:
            # 1. Add -nostdin as a global parameter.
            # 2. Use the correct .overwrite_output() method.
            (
                ffmpeg
                .input(original_file_name)
                .output(wav_file_name, ac=1, ar=16000)
                .overwrite_output()
                .run(capture_stdout=True, capture_stderr=True, cmd=['ffmpeg', '-nostdin'])
            )
            logger.info(f"[{firestore_ref}] Conversion successful")
        except ffmpeg.Error as e:
            logger.error(f"[{firestore_ref}] FFMPEG Error: {e.stderr.decode()}", exc_info=True)
            raise

        logger.info(f"[{firestore_ref}] Updating status to PROCESSING")
        update_firestore(firestore_ref, {"status": "PROCESSING"})

        logger.info(f"[{firestore_ref}] Starting diarization on {wav_file_name}")
        diarization = diarize_audio(wav_file_name)
        logger.info(f"[{firestore_ref}] Finished diarization")

        logger.info(f"[{firestore_ref}] Starting parallel transcription of {len(diarization)} segments")
        full_transcript_map = {}
        speakers = set()
        
        # Load audio for segment slicing after conversion
        logger.info(f"[{firestore_ref}] Loading converted WAV file for segmentation.")
        audio_segment = AudioSegment.from_wav(wav_file_name)

        # First, merge consecutive segments from the same speaker
        merged_segments = []
        current_speaker = None
        current_start = None
        current_end = None
        temp_audio = None

        for turn, _, speaker in diarization.itertracks(yield_label=True):
            speakers.add(speaker)
            if current_speaker != speaker:
                # Save previous segment if exists
                if current_speaker is not None and temp_audio is not None:
                    segment_file_path = f"temp_segment_{current_speaker}_{int(current_start * 1000)}.wav"
                    temp_audio.export(segment_file_path, format="wav")
                    merged_segments.append((current_speaker, current_start, current_end, segment_file_path))
                # Start new segment
                current_speaker = speaker
                current_start = turn.start
                current_end = turn.end
                temp_audio = audio_segment[int(turn.start * 1000):int(turn.end * 1000)]
            else:
                # Extend current segment
                current_end = turn.end
                temp_audio = temp_audio + audio_segment[int(turn.start * 1000):int(turn.end * 1000)]

        # Don't forget the last segment
        if current_speaker is not None and temp_audio is not None:
            segment_file_path = f"temp_segment_{current_speaker}_{int(current_start * 1000)}.wav"
            temp_audio.export(segment_file_path, format="wav")
            merged_segments.append((current_speaker, current_start, current_end, segment_file_path))

        # Use ThreadPoolExecutor for parallel requests with merged segments
        with ThreadPoolExecutor(max_workers=10) as executor:
            future_to_segment = {}
            for speaker, start, end, segment_file_path in merged_segments:
                # Submit task to thread pool
                future = executor.submit(transcribe_audio, segment_file_path, language)
                future_to_segment[future] = (speaker, int(start * 1000), segment_file_path)
            
            for future in as_completed(future_to_segment):
                speaker, start_ms, segment_path = future_to_segment[future]
                try:
                    response = future.result()
                    if response.results:
                        transcript_text = response.results[0].alternatives[0].transcript
                        # Save result with timestamp for further sorting
                        full_transcript_map[start_ms] = f"{speaker}: {transcript_text}"
                except Exception as exc:
                    logger.error(f"Segment at {start_ms} generated an exception: {exc}")
                finally:
                    # Remove temporary segment file
                    os.remove(segment_path)

        # Sort transcripts by start time and combine
        sorted_transcripts = [full_transcript_map[key] for key in sorted(full_transcript_map.keys())]
        final_transcript_text = "\n".join(sorted_transcripts)
        logger.info(f"[{firestore_ref}] Finished transcription")

        processing_time = time.time() - start_time
        metadata = {
            "duration": len(audio_segment) / 1000,
            "speakers_count": len(speakers),
            "processing_time": round(processing_time, 2),
            "language": language
        }

        logger.info(f"[{firestore_ref}] Updating status to DONE")
        update_firestore(firestore_ref, {
            "status": "DONE",
            "transcript": final_transcript_text,
            "metadata": metadata,
            "finished_at": datetime.now(timezone.utc) # Add finish time
        })

    except Exception as e:
        logger.error(f"[{firestore_ref}] Error during processing: {e}", exc_info=True)
        update_firestore(firestore_ref, {
            "status": "ERROR", 
            "error_message": str(e),
            "finished_at": datetime.now(timezone.utc) # Add finish time even on error
        })

    finally:
        logger.info(f"[{firestore_ref}] Cleaning up temporary files")
        # Remove main files
        if original_file_name and os.path.exists(original_file_name):
            os.remove(original_file_name)
        if wav_file_name and os.path.exists(wav_file_name):
            os.remove(wav_file_name)
        
        # Find and remove all temporary segments
        for temp_file in glob.glob("temp_segment_*.wav"):
            try:
                os.remove(temp_file)
                logger.info(f"[{firestore_ref}] Removed temporary segment file: {temp_file}")
            except OSError as e:
                logger.error(f"[{firestore_ref}] Error removing temporary file {temp_file}: {e}")
