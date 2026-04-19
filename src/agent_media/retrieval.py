from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd


@dataclass(slots=True)
class RetrievalEngine:
    df_profils: pd.DataFrame
    model: Any = None
    index: Any = None
    embeddings: np.ndarray | None = None
    backend: str = "token"

    @classmethod
    def build(cls, df_profils: pd.DataFrame) -> "RetrievalEngine":
        texts = df_profils["texte_rag"].tolist()
        try:
            from sentence_transformers import SentenceTransformer
            import faiss

            model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
            embeddings = model.encode(texts, show_progress_bar=False, batch_size=32).astype("float32")
            index = faiss.IndexFlatL2(int(embeddings.shape[1]))
            index.add(embeddings)
            return cls(df_profils=df_profils, model=model, index=index, embeddings=embeddings, backend="faiss")
        except Exception:
            return cls(df_profils=df_profils, embeddings=None, backend="token")

    def search(self, query: str, top_k: int = 3) -> pd.DataFrame:
        if self.backend == "faiss" and self.model is not None and self.index is not None:
            vector = self.model.encode([query]).astype("float32")
            _, indices = self.index.search(vector, top_k)
            return self.df_profils.iloc[indices[0]].copy()

        tokens = set(_normalize(query).split())
        scores: list[tuple[int, int]] = []
        for idx, text in enumerate(self.df_profils["texte_rag"].tolist()):
            overlap = len(tokens.intersection(set(_normalize(text).split())))
            scores.append((idx, overlap))
        ranked = sorted(scores, key=lambda item: item[1], reverse=True)
        selected = [idx for idx, score in ranked[:top_k] if score > 0]
        if not selected:
            selected = list(range(min(top_k, len(self.df_profils))))
        return self.df_profils.iloc[selected].copy()

    def save_index(self, path) -> bool:
        if self.backend != "faiss" or self.index is None:
            return False
        try:
            import faiss

            faiss.write_index(self.index, str(path))
            return True
        except Exception:
            return False


def _normalize(text: str) -> str:
    return (
        text.lower()
        .replace("é", "e")
        .replace("è", "e")
        .replace("ê", "e")
        .replace("à", "a")
        .replace("ù", "u")
        .replace("ï", "i")
        .replace("î", "i")
        .replace("ô", "o")
        .replace("\n", " ")
    )
