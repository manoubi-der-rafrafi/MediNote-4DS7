from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class PostStore:
    dataset_path: Path

    def load(self) -> dict[str, Any]:
        if self.dataset_path.exists():
            with self.dataset_path.open("r", encoding="utf-8") as handle:
                return json.load(handle)
        return {"posts": [], "meta": {"total": 0, "publies": 0}}

    def save(self, dataset: dict[str, Any]) -> None:
        dataset["meta"]["total"] = len(dataset["posts"])
        dataset["meta"]["publies"] = sum(1 for post in dataset["posts"] if post.get("publie"))
        self.dataset_path.parent.mkdir(parents=True, exist_ok=True)
        with self.dataset_path.open("w", encoding="utf-8") as handle:
            json.dump(dataset, handle, ensure_ascii=False, indent=2)

    def add_post(
        self,
        produit: str,
        plateforme: str,
        texte: str,
        fete: str | None = None,
        campagne_type: str = "standard",
    ) -> str:
        dataset = self.load()
        post_id = f"POST_{len(dataset['posts']) + 1:04d}"
        dataset["posts"].append(
            {
                "post_id": post_id,
                "produit": produit,
                "fete": fete,
                "type": campagne_type,
                "date_creation": str(date.today()),
                "plateforme": plateforme,
                "texte": texte,
                "likes": 0,
                "reach": 0,
                "commentaires": 0,
                "ctr": 0.0,
                "score_final": None,
                "publie": False,
            }
        )
        self.save(dataset)
        return post_id

    def update_metrics(self, post_id: str, likes: int, reach: int, commentaires: int, ctr: float) -> bool:
        dataset = self.load()
        for post in dataset["posts"]:
            if post["post_id"] != post_id:
                continue
            post.update(
                {
                    "likes": likes,
                    "reach": reach,
                    "commentaires": commentaires,
                    "ctr": ctr,
                    "publie": True,
                }
            )
            engagement_rate = (likes + commentaires) / max(reach, 1) * 100
            like_rate = likes / max(reach, 1) * 100
            post["score_final"] = round((engagement_rate * 0.40) + (ctr * 0.35) + (like_rate * 0.25), 2)
            self.save(dataset)
            return True
        return False
