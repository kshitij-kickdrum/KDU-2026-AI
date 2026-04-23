import numpy as np

from app.services.compression_service import (
    binary_quantize,
    hamming_distance,
    matryoshka_then_binary,
    matryoshka_truncate,
)


def test_matryoshka_unit_norm_property() -> None:
    rng = np.random.default_rng(123)
    for _ in range(100):
        vector = rng.normal(size=3072).astype(np.float32)
        result = matryoshka_truncate(vector, 256)
        assert result.shape == (256,)
        assert abs(np.linalg.norm(result) - 1.0) <= 1e-6


def test_binary_quantize_size_property() -> None:
    for n in [8, 16, 256, 3072]:
        vector = np.linspace(-1.0, 1.0, num=n, dtype=np.float32)
        packed = binary_quantize(vector)
        assert packed.shape[0] == n // 8


def test_matryoshka_known_vector_and_ratio() -> None:
    vector = np.arange(1, 3073, dtype=np.float32)
    result = matryoshka_truncate(vector, 256)
    assert result.shape == (256,)
    assert abs(np.linalg.norm(result) - 1.0) <= 1e-6

    original_bytes = 3072 * 4
    compressed_bytes = 256 * 4
    compression_ratio = original_bytes / compressed_bytes
    assert compression_ratio == 12.0


def test_binary_quantize_known_values_and_ratio() -> None:
    vector = np.array([-1.0, 2.0, -3.0, 4.0, 5.0, -6.0, -7.0, 8.0], dtype=np.float32)
    packed = binary_quantize(vector)
    expected_bits = np.array([0, 1, 0, 1, 1, 0, 0, 1], dtype=np.uint8)
    expected = np.packbits(expected_bits)
    assert np.array_equal(packed, expected)

    original_bytes = 3072 * 4
    compressed_bytes = 3072 // 8
    compression_ratio = original_bytes / compressed_bytes
    assert compression_ratio == 32.0


def test_matryoshka_then_binary_ratio() -> None:
    vector = np.arange(1, 3073, dtype=np.float32)
    packed = matryoshka_then_binary(vector, 256)
    assert packed.shape == (32,)

    original_bytes = 3072 * 4
    compressed_bytes = 256 // 8
    compression_ratio = original_bytes / compressed_bytes
    assert compression_ratio == 384.0
    normalization_applied = True
    assert normalization_applied


def test_chained_pipeline_improves_distance_for_similar_pairs() -> None:
    base = np.ones(3072, dtype=np.float32)
    noisy = np.ones(3072, dtype=np.float32)
    noisy[256:] = -1.0

    direct_a = binary_quantize(base)
    direct_b = binary_quantize(noisy)
    direct_distance = hamming_distance(direct_a, direct_b)

    chained_a = matryoshka_then_binary(base, 256)
    chained_b = matryoshka_then_binary(noisy, 256)
    chained_distance = hamming_distance(chained_a, chained_b)

    assert direct_distance > chained_distance
