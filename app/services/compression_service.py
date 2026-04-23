import numpy as np


def matryoshka_truncate(vector: np.ndarray, target_dims: int = 256) -> np.ndarray:
    if vector.ndim != 1:
        raise ValueError("matryoshka_truncate expects a 1-D vector")
    if target_dims < 1 or target_dims > vector.shape[0]:
        raise ValueError("target_dims must be between 1 and vector length")
    truncated = vector[:target_dims].astype(np.float32, copy=False)
    norm = np.linalg.norm(truncated)
    return truncated / norm if norm > 0 else truncated


def binary_quantize(vector: np.ndarray) -> np.ndarray:
    if vector.ndim != 1:
        raise ValueError("binary_quantize expects a 1-D vector")
    if vector.shape[0] % 8 != 0:
        raise ValueError("vector length must be divisible by 8 for exact bit packing")
    bits = (vector >= 0).astype(np.uint8)
    return np.packbits(bits)


def hamming_distance(a: np.ndarray, b: np.ndarray) -> int:
    if a.shape != b.shape:
        raise ValueError("hamming_distance expects vectors with equal shape")
    if a.dtype != np.uint8 or b.dtype != np.uint8:
        raise ValueError("hamming_distance expects uint8 packed vectors")
    return int(np.unpackbits(a ^ b).sum())


def matryoshka_then_binary(vector: np.ndarray, target_dims: int = 256) -> np.ndarray:
    truncated_normalized = matryoshka_truncate(vector=vector, target_dims=target_dims)
    return binary_quantize(truncated_normalized)
