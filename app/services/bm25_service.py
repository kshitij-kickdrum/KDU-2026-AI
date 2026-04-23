import math
from collections import Counter

try:
    from rank_bm25 import BM25Okapi
except ImportError:  # pragma: no cover - fallback for environments without rank_bm25
    class BM25Okapi:  # type: ignore[no-redef]
        def __init__(self, corpus: list[list[str]], k1: float = 1.5, b: float = 0.75) -> None:
            self.corpus = corpus
            self.k1 = k1
            self.b = b
            self.doc_len = [len(doc) for doc in corpus]
            self.avgdl = sum(self.doc_len) / len(self.doc_len) if corpus else 0.0
            self.term_freq = [Counter(doc) for doc in corpus]
            self.doc_freq: Counter[str] = Counter()
            for doc in corpus:
                for token in set(doc):
                    self.doc_freq[token] += 1
            self.n_docs = len(corpus)

        def get_scores(self, query_tokens: list[str]) -> list[float]:
            scores: list[float] = []
            for idx, tf in enumerate(self.term_freq):
                dl = self.doc_len[idx]
                score = 0.0
                for token in query_tokens:
                    if token not in tf:
                        continue
                    df = self.doc_freq[token]
                    idf = math.log(1 + (self.n_docs - df + 0.5) / (df + 0.5))
                    freq = tf[token]
                    denom = freq + self.k1 * (1 - self.b + self.b * dl / (self.avgdl or 1.0))
                    score += idf * ((freq * (self.k1 + 1)) / denom)
                scores.append(score)
            return scores

from app.models.schemas import ChildChunk


class BM25Service:
    def __init__(self, chunks: list[ChildChunk]) -> None:
        self._chunks = chunks
        self._tokenized = [self._tokenize(chunk.text) for chunk in chunks]
        self._index = BM25Okapi(self._tokenized)

    @staticmethod
    def _tokenize(text: str) -> list[str]:
        return text.lower().split()

    def search(self, query: str, k: int = 10) -> list[tuple[int, float]]:
        if not query.strip() or k <= 0:
            return []
        tokens = self._tokenize(query)
        scores = self._index.get_scores(tokens)
        ranked = sorted(
            ((self._chunks[i].child_id, float(score)) for i, score in enumerate(scores)),
            key=lambda x: x[1],
            reverse=True,
        )
        return ranked[:k]
