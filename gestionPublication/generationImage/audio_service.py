from __future__ import annotations

import sys
from pathlib import Path
from typing import Any
from urllib.parse import quote

from .config import BASE_DIR


class ImageAudioGenerationError(RuntimeError):
    pass


class ImageAudioGenerationService:
    def __init__(self, duration: int = 5) -> None:
        self.duration = duration

    def generate(
        self,
        context: dict[str, Any],
        selected_product: dict[str, Any],
        output_dir: Path,
    ) -> dict[str, Any]:
        print("[AUDIO] status=start")
        modules = self._load_music_generation_modules()
        holiday_name = self._resolve_holiday_name(context)
        product_theme = self._resolve_product_theme(selected_product)
        print(
            "[AUDIO] status=context_resolved "
            f"holiday={holiday_name!r} product_theme={product_theme!r}"
        )

        occasion_context = self._build_context(
            modules=modules,
            context=context,
            holiday_name=holiday_name,
            product_theme=product_theme,
        )
        prompt = self._build_prompt(
            modules=modules,
            occasion_context=occasion_context,
            holiday_name=holiday_name,
            product_theme=product_theme,
            selected_product=selected_product,
            context=context,
        )

        result: dict[str, Any] = {
            "music_prompt": prompt,
            "audio_generation_status": "musicgen_not_installed",
            "audio_path": "",
            "audio_url": "",
            "audio_error": "",
        }

        if not modules["is_musicgen_available"]():
            result["audio_error"] = (
                "MusicGen n'est pas disponible. Installez audiocraft ou "
                "torch + transformers + scipy avant l'execution."
            )
            print(f"[AUDIO] status=skipped reason={result['audio_error']}")
            return result

        try:
            audio_path = modules["generate_audio_with_musicgen"](
                prompt=prompt,
                holiday_name=holiday_name,
                product_theme=product_theme,
                duration=self.duration,
                output_dir=output_dir,
            )
        except Exception as exc:
            print(
                "[AUDIO] status=failed "
                f"reason={exc.__class__.__name__}: {exc}"
            )
            raise ImageAudioGenerationError(
                f"Echec de la generation audio MusicGen: {exc}"
            ) from exc

        if not audio_path:
            result["audio_generation_status"] = "musicgen_failed"
            result["audio_error"] = "MusicGen n'a pas retourne de fichier audio."
            print(f"[AUDIO] status=failed reason={result['audio_error']}")
            return result

        audio_path_string = str(audio_path)
        result.update(
            {
                "audio_generation_status": "audio_generated",
                "audio_path": audio_path_string,
                "audio_url": f"/media/generated-audio?path={quote(audio_path_string)}",
                "saved_files": {"audio_file": audio_path_string},
            }
        )
        print(f"[AUDIO] status=success audio_path={audio_path_string!r}")
        return result

    @staticmethod
    def _load_music_generation_modules() -> dict[str, Any]:
        project_dir = BASE_DIR / "music_generation" / "music_generation"
        if not project_dir.exists():
            raise ImageAudioGenerationError(
                f"Le projet music_generation est introuvable: {project_dir}"
            )

        project_dir_string = str(project_dir)
        if project_dir_string not in sys.path:
            sys.path.insert(0, project_dir_string)

        try:
            from src.mood_style_model import StylePrediction, predict_style, train_models
            from src.musicgen_generator import (
                generate_audio_with_musicgen,
                is_musicgen_available,
            )
            from src.preprocess_holidays import OccasionContext, build_occasion_context
            from src.prompt_generator import generate_music_prompt
        except Exception as exc:
            raise ImageAudioGenerationError(
                f"Impossible de charger les modules music_generation: {exc}"
            ) from exc

        return {
            "OccasionContext": OccasionContext,
            "StylePrediction": StylePrediction,
            "build_occasion_context": build_occasion_context,
            "predict_style": predict_style,
            "train_models": train_models,
            "generate_music_prompt": generate_music_prompt,
            "generate_audio_with_musicgen": generate_audio_with_musicgen,
            "is_musicgen_available": is_musicgen_available,
        }

    def _build_context(
        self,
        modules: dict[str, Any],
        context: dict[str, Any],
        holiday_name: str,
        product_theme: str,
    ):
        year = self._extract_year(context.get("date_occasion"))
        build_occasion_context = modules["build_occasion_context"]
        try:
            return build_occasion_context(
                holiday_name,
                product_theme,
                country="TN",
                year=year,
            )
        except Exception:
            OccasionContext = modules["OccasionContext"]
            return OccasionContext(
                holiday_name=holiday_name,
                product_theme=product_theme,
                occasion_type=str(context.get("occasion_type") or "occasion"),
                country="TN",
                year=year,
                date=str(context.get("date_occasion") or ""),
                local_name=holiday_name,
                description=str(context.get("style_visuel") or ""),
            )

    def _build_prompt(
        self,
        modules: dict[str, Any],
        occasion_context,
        holiday_name: str,
        product_theme: str,
        selected_product: dict[str, Any],
        context: dict[str, Any],
    ) -> str:
        try:
            modules["train_models"]()
            style = modules["predict_style"](occasion_context)
            return modules["generate_music_prompt"](
                occasion_context,
                style,
                self.duration,
            )
        except Exception:
            StylePrediction = modules["StylePrediction"]
            fallback_style = StylePrediction(
                target_mood="warm",
                genre="ambient wellness",
                instruments="soft oud, piano, light percussion",
                tempo="slow",
                prompt_style="",
                source="fallback",
            )
            try:
                return modules["generate_music_prompt"](
                    occasion_context,
                    fallback_style,
                    self.duration,
                )
            except Exception:
                product_name = str(selected_product.get("produit") or product_theme).strip()
                occasion_type = str(context.get("occasion_type") or "occasion").strip()
                return (
                    f"Warm instrumental background music for {holiday_name}, "
                    f"{occasion_type}, highlighting {product_name}. "
                    f"Short {self.duration}-second loop, soft oriental touches, "
                    f"wellness tone, no vocals."
                )

    @staticmethod
    def _resolve_holiday_name(context: dict[str, Any]) -> str:
        occasion = str(context.get("occasion") or "").strip()
        aliases = {
            "Periode Bac & Examens": "Ramadan",
            "Mother's Day": "Mother's Day",
            "Father's Day": "Father's Day",
            "Valentine's Day": "Valentine's Day",
            "Tunisian Women's Day": "Tunisian Women's Day",
        }
        return aliases.get(occasion, occasion or "Ramadan")

    @staticmethod
    def _resolve_product_theme(selected_product: dict[str, Any]) -> str:
        raw_theme = str(
            selected_product.get("theme")
            or selected_product.get("therapeutic_theme")
            or selected_product.get("produit")
            or "wellness"
        ).strip().lower()
        theme_mapping = {
            "digestif": "digestion",
            "digestion": "digestion",
            "energie": "energy",
            "énergie": "energy",
            "immunite": "immunity",
            "immunité": "immunity",
            "stress": "stress",
            "sommeil": "sleep",
            "allergie": "allergies",
            "allergies": "allergies",
            "vitamines": "vitamins",
            "hydratation": "hydration",
        }
        return theme_mapping.get(raw_theme, raw_theme.replace(" ", "_") or "wellness")

    @staticmethod
    def _extract_year(raw_date: Any) -> int | None:
        value = str(raw_date or "").strip()
        if len(value) >= 4 and value[:4].isdigit():
            return int(value[:4])
        return None
