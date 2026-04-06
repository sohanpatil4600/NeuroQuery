import logging
import os
import sys
import warnings

def silence_ai_noise():
    """Forcefully silences all library warnings (Transformers, HF, Torch, etc.)"""
    
    # 1. Environment Variables (Must be set before imports)
    os.environ["TOKENIZERS_PARALLELISM"] = "false"
    os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
    os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"
    os.environ["TRANSFORMERS_VERBOSITY"] = "error"
    os.environ["TRANSFORMERS_NO_ADVISORY_WARNINGS"] = "1"

    # 2. Python Warnings
    warnings.filterwarnings("ignore", category=UserWarning)
    warnings.filterwarnings("ignore", message=".*unauthenticated requests.*")
    warnings.filterwarnings("ignore", message=".*embeddings.position_ids.*")

    # 3. Standard Logging
    for logger_name in [
        "transformers", 
        "huggingface_hub", 
        "sentence_transformers", 
        "mem0", 
        "qdrant_client"
    ]:
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.ERROR)
        logger.propagate = False

    # 4. Silence Transformers specifically via its own utility if available
    try:
        import transformers
        transformers.utils.logging.set_verbosity_error()
        transformers.utils.logging.disable_progress_bar()
    except ImportError:
        pass

if __name__ == "__main__":
    silence_ai_noise()
