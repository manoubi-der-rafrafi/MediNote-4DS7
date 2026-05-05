from __future__ import annotations

import importlib
import os
import sys
from contextlib import contextmanager
from datetime import date, datetime
from pathlib import Path
from typing import Any, Iterator

from gestionPublication.generationImage.selectors import (
    detect_exam_period,
    detect_next_occasion,
    resolve_given_occasion,
)


class MusicRecommendationError(RuntimeError):
    pass


class MusicRecommendationService:
    def __init__(self, top_k: int = 5) -> None:
        self.top_k = top_k

    def handle(self, payload: dict[str, Any]) -> dict[str, Any]:
        generation_mode = str(payload.get("generation_mode", "")).strip().lower()
        if generation_mode not in {"next_occasion", "exam_period", "given_occasion"}:
            raise MusicRecommendationError(
                "generation_mode doit etre 'next_occasion', 'exam_period' ou 'given_occasion'."
            )

        reference_date = self._parse_reference_date(payload.get("date"))
        context = self._resolve_context(
            generation_mode=generation_mode,
            occasion=payload.get("occasion"),
            reference_date=reference_date,
        )
        top_k = self._resolve_top_k(payload)
        recommendation = self._recommend(context["occasion"], top_k=top_k)
        tracks = recommendation.get("results", [])

        return {
            "status": "success",
            "intent": "publication",
            "action": "recommend_music",
            "type_publication": "audio",
            "media_type": "audio",
            "generation_mode": generation_mode,
            "occasion": context["occasion"],
            "occasion_type": context["occasion_type"],
            "date_occasion": context["date_occasion"],
            "date_publication": context["date_actuelle"],
            "saison": context["saison"],
            "queries": list(recommendation.get("queries", [])),
            "base_queries": list(recommendation.get("base_queries", [])),
            "top_k": top_k,
            "recommendations": [
                self._normalize_track(track, index)
                for index, track in enumerate(tracks[:top_k], start=1)
            ],
            "debug": recommendation.get("debug", {}),
        }

    @staticmethod
    def _resolve_context(
        generation_mode: str,
        occasion: Any,
        reference_date: date | None,
    ) -> dict[str, Any]:
        if generation_mode == "next_occasion":
            return detect_next_occasion(reference_date)
        if generation_mode == "exam_period":
            return detect_exam_period(reference_date)
        return resolve_given_occasion(str(occasion or ""), reference_date)

    @staticmethod
    def _parse_reference_date(raw_date: Any) -> date | None:
        if raw_date is None:
            return None
        try:
            return datetime.strptime(str(raw_date).strip(), "%Y-%m-%d").date()
        except ValueError as exc:
            raise MusicRecommendationError(
                "Le champ 'date' doit etre au format YYYY-MM-DD lorsqu'il est fourni."
            ) from exc

    def _resolve_top_k(self, payload: dict[str, Any]) -> int:
        raw_top_k = payload.get("top_k", self.top_k)
        try:
            top_k = int(raw_top_k)
        except (TypeError, ValueError) as exc:
            raise MusicRecommendationError("top_k doit etre un entier.") from exc
        return min(max(top_k, 1), 10)

    def _recommend(self, occasion: str, top_k: int) -> dict[str, Any]:
        project_dir = self._project_dir()
        with self._isolated_recommender_import(project_dir):
            try:
                module = importlib.import_module("src.recommender")
            except Exception as exc:
                raise MusicRecommendationError(
                    f"Impossible de charger le module music_recommender: {exc}"
                ) from exc

            try:
                return module.recommend_music(occasion, top_k=top_k)
            except Exception as exc:
                raise MusicRecommendationError(
                    f"Echec de la recommandation musicale: {exc}"
                ) from exc

    @staticmethod
    def _normalize_track(track: dict[str, Any], rank: int) -> dict[str, Any]:
        return {
            "rank": rank,
            "title": str(track.get("title", "")).strip(),
            "artist": str(track.get("artist", "")).strip(),
            "url": str(track.get("url", "")).strip(),
            "source": str(track.get("source", "")).strip(),
            "matched_query": str(track.get("matched_query", "")).strip(),
            "final_score": float(track.get("final_score", 0.0) or 0.0),
            "relevance_score": float(track.get("relevance_score", 0.0) or 0.0),
            "trend_score": float(track.get("trend_score", 0.0) or 0.0),
            "freshness_score": float(track.get("freshness_score", 0.0) or 0.0),
        }

    @staticmethod
    def _project_dir() -> Path:
        project_dir = (
            Path(__file__).resolve().parents[2]
            / "music_recommender copy"
            / "music_recommender copy"
        )
        if not project_dir.exists():
            raise MusicRecommendationError(
                f"Le projet music_recommender est introuvable: {project_dir}"
            )
        return project_dir

    @contextmanager
    def _isolated_recommender_import(self, project_dir: Path) -> Iterator[None]:
        project_dir_string = str(project_dir)
        previous_cwd = os.getcwd()
        previous_src_modules = {
            name: module
            for name, module in sys.modules.items()
            if name == "src" or name.startswith("src.")
        }

        for name in list(previous_src_modules.keys()):
            sys.modules.pop(name, None)

        inserted = False
        if project_dir_string not in sys.path:
            sys.path.insert(0, project_dir_string)
            inserted = True

        os.chdir(project_dir)
        try:
            yield
        finally:
            loaded_src_modules = [
                name for name in sys.modules if name == "src" or name.startswith("src.")
            ]
            for name in loaded_src_modules:
                sys.modules.pop(name, None)
            sys.modules.update(previous_src_modules)
            if inserted:
                try:
                    sys.path.remove(project_dir_string)
                except ValueError:
                    pass
            os.chdir(previous_cwd)
