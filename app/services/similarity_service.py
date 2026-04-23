import numpy as np


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    if a.ndim != 1 or b.ndim != 1:
        raise ValueError("cosine_similarity expects 1-D vectors")
    if a.shape != b.shape:
        raise ValueError("cosine_similarity expects vectors with equal dimensions")
    denom = np.linalg.norm(a) * np.linalg.norm(b)
    if denom == 0:
        raise ValueError("cosine_similarity is undefined for zero vectors")
    return float(np.dot(a, b) / denom)
