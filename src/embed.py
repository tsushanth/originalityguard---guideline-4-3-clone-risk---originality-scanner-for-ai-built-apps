"""Shared embedding + similarity math.

The sentence-transformers model is only loaded lazily, inside
_get_model(), so importing this module (and testing cosine_similarity)
never requires downloading or loading the ML model.
"""

from functools import lru_cache

import numpy as np

MODEL_NAME = "all-MiniLM-L6-v2"


@lru_cache(maxsize=1)
def _get_model():
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(MODEL_NAME)


def embed_texts(texts):
    """Embed a list of strings, returning an (N, dim) numpy array."""
    model = _get_model()
    return np.asarray(model.encode(list(texts)))


def cosine_similarity(a, b):
    """Cosine similarity between two vectors, as a plain float."""
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    denom = np.linalg.norm(a) * np.linalg.norm(b)
    if denom == 0:
        return 0.0
    return float(np.dot(a, b) / denom)
