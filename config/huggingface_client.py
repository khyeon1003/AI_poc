from huggingface_hub import InferenceClient
from .config import settings

huggingface_client=InferenceClient(
    provider="hf-inference",
    api_key=settings.HUGGING_FACE_KEY
)
