from typing import List
from sentence_transformers import SentenceTransformer
from app.core.config import get_settings

class EmbeddingService:
    _model: SentenceTransformer | None = None

    def __init__(self, model_name: str | None = None):
        self.model_name = model_name or get_settings().embedding_model

    def _load(self):
        if EmbeddingService._model is None:
            EmbeddingService._model = SentenceTransformer(self.model_name)
        return EmbeddingService._model

    def generate(self, text: str) -> List[float]:
        if not text or not text.strip():
            return [0.0] * 384
        model = self._load()
        vec = model.encode(text, normalize_embeddings=True)
        return vec.tolist()

    def generate_batch(self, texts: List[str]) -> List[List[float]]:
        model = self._load()
        vecs = model.encode(texts, normalize_embeddings=True)
        return vecs.tolist()
