"""Embedding Provider abstract base."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class EmbeddingResult:
    embedding: list[float]
    model: str = ""
    dimension: int = 0

    def __post_init__(self) -> None:
        if self.dimension == 0:
            self.dimension = len(self.embedding)


class EmbeddingProvider(ABC):
    @abstractmethod
    def embed(self, texts: list[str]) -> list[EmbeddingResult]:
        """Generate embeddings for one or more texts."""

    def embed_single(self, text: str) -> EmbeddingResult:
        return self.embed([text])[0]

    @abstractmethod
    def health_check(self) -> bool:
        """Check whether the embedding service is reachable."""
