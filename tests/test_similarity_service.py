import numpy as np

from app.services.similarity_service import cosine_similarity


def test_cosine_similarity_range_property() -> None:
    rng = np.random.default_rng(42)
    for _ in range(200):
        a = rng.normal(size=128).astype(np.float32)
        b = rng.normal(size=128).astype(np.float32)
        score = cosine_similarity(a, b)
        assert -1.0 <= score <= 1.0


def test_cosine_similarity_symmetry_property() -> None:
    rng = np.random.default_rng(7)
    for _ in range(200):
        a = rng.normal(size=64).astype(np.float32)
        b = rng.normal(size=64).astype(np.float32)
        ab = cosine_similarity(a, b)
        ba = cosine_similarity(b, a)
        assert abs(ab - ba) <= 1e-6


def test_cosine_similarity_known_cases() -> None:
    orth_a = np.array([1.0, 0.0], dtype=np.float32)
    orth_b = np.array([0.0, 1.0], dtype=np.float32)
    assert abs(cosine_similarity(orth_a, orth_b) - 0.0) <= 1e-6

    ident_a = np.array([1.0, 2.0, 3.0], dtype=np.float32)
    ident_b = np.array([1.0, 2.0, 3.0], dtype=np.float32)
    assert abs(cosine_similarity(ident_a, ident_b) - 1.0) <= 1e-6

    opp_a = np.array([1.0, -1.0], dtype=np.float32)
    opp_b = np.array([-1.0, 1.0], dtype=np.float32)
    assert abs(cosine_similarity(opp_a, opp_b) + 1.0) <= 1e-6

    x = np.array([1.0, 2.0, 2.0], dtype=np.float32)
    y = np.array([2.0, 1.0, 2.0], dtype=np.float32)
    expected = float(np.dot(x, y) / (np.linalg.norm(x) * np.linalg.norm(y)))
    assert abs(cosine_similarity(x, y) - expected) <= 1e-6
