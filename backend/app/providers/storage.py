from __future__ import annotations

from pathlib import Path
from uuid import uuid4


class LocalStorageProvider:
    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)

    def save(self, *, content: bytes, suffix: str) -> str:
        self.root.mkdir(parents=True, exist_ok=True)
        normalized_suffix = suffix if suffix.startswith(".") else f".{suffix}"
        relative_path = f"{uuid4().hex}{normalized_suffix.lower()}"
        target = self.root / relative_path
        target.write_bytes(content)
        return relative_path
