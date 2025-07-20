from pyannote.audio import Pipeline
from ..utils.logger import logger
import os
import torch

def diarize_audio(audio_path):
    # Hook function for tracking progress
    # Added **kwargs to accept any additional arguments
    def hook(step_name: str, step_artefact, **kwargs):
        # `step_artefact` can be different: slider, number, etc.
        # Only the step name is logged for simplicity.
        logger.info(f"Diarization step '{step_name}' completed.")

    # use_auth_token=True uses the token
    # saved via `huggingface-cli login`
    pipeline = Pipeline.from_pretrained(
        "pyannote/speaker-diarization@2.1",
        use_auth_token=True
    )
    
    # Check for GPU and move model to it
    if torch.cuda.is_available():
        logger.info("GPU detected, moving diarization pipeline to CUDA device.")
        pipeline.to(torch.device("cuda"))
    else:
        logger.info("No GPU detected, running diarization on CPU.")
    
    logger.info("Applying diarization pipeline with progress hook...")
    diarization = pipeline(audio_path, hook=hook)
    logger.info("Diarization pipeline finished.")
    return diarization
