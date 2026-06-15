"""Fake Embedding Provider for deterministic tests and demos."""

from __future__ import annotations

import hashlib

from app.providers.embedding import EmbeddingProvider, EmbeddingResult


class FakeEmbeddingProvider(EmbeddingProvider):
    """Deterministic fake embeddings based on text hash for testing.

    Produces 128-dim vectors where each element is derived from the SHA-256
    hash of the input text so that identical texts yield identical vectors
    and cosine similarity degrades smoothly for different texts.
    """

    DIMENSION = 128

    def embed(self, texts: list[str]) -> list[EmbeddingResult]:
        results: list[EmbeddingResult] = []
        for text in texts:
            vec = self._hash_vector(text)
            results.append(EmbeddingResult(embedding=vec, model="fake-v1", dimension=self.DIMENSION))
        return results

    def health_check(self) -> bool:
        return True

    def _hash_vector(self, text: str) -> list[float]:
        """Build a deterministic float vector from text hash."""
        digest = hashlib.sha256(text.encode("utf-8")).digest()
        vec: list[float] = []
        for i in range(0, min(len(digest), self.DIMENSION * 4), 4):
            # Convert 4 bytes to a float in [-1, 1]
            val = int.from_bytes(digest[i : i + 4], "big", signed=True)
            vec.append(val / 2_147_483_648.0)  # normalize by max i32
        # Pad if needed
        while len(vec) < self.DIMENSION:
            vec.append(0.0)
        return vec[: self.DIMENSION]
