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

    # Get Hugging Face token from environment variables
    hf_token = os.getenv("HUGGING_FACE_TOKEN")
    if not hf_token:
        raise ValueError("HUGGING_FACE_TOKEN environment variable is not set")
        
    pipeline = Pipeline.from_pretrained(
        "pyannote/speaker-diarization@2.1",
        use_auth_token=hf_token
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
