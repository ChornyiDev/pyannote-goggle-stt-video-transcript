from pyannote.audio import Pipeline
from ..utils.logger import logger
import os
import torch

def diarize_audio(audio_path):
    # Функція-хук для відстеження прогресу
    # Додано **kwargs, щоб приймати будь-які додаткові аргументи
    def hook(step_name: str, step_artefact, **kwargs):
        # `step_artefact` може бути різним: слайдер, число, і т.д.
        # Логується тільки назва кроку для простоти.
        logger.info(f"Diarization step '{step_name}' completed.")

    # use_auth_token=True використовує токен, 
    # збережений через `huggingface-cli login`
    pipeline = Pipeline.from_pretrained(
        "pyannote/speaker-diarization@2.1",
        use_auth_token=True
    )
    
    # Перевірка наявності GPU та переміщення моделі на нього
    if torch.cuda.is_available():
        logger.info("GPU detected, moving diarization pipeline to CUDA device.")
        pipeline.to(torch.device("cuda"))
    else:
        logger.info("No GPU detected, running diarization on CPU.")
    
    logger.info("Applying diarization pipeline with progress hook...")
    diarization = pipeline(audio_path, hook=hook)
    logger.info("Diarization pipeline finished.")
    return diarization
