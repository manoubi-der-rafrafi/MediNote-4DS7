from __future__ import annotations

import base64
import re
import tempfile
from pathlib import Path
from typing import Any

import pyttsx3


class VoiceSynthesisError(RuntimeError):
    pass


class VoiceSynthesisService:
    DEFAULT_RATE = 165
    DEFAULT_VOLUME = 1.0

    def synthesize_base64(self, text: str) -> dict[str, Any]:
        clean_text = self._normalize_text_for_speech(text)
        if not clean_text:
            raise VoiceSynthesisError("Le texte a convertir en vocal est vide.")

        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                output_path = Path(tmpdir) / "response.wav"

                engine = pyttsx3.init()
                engine.setProperty("rate", self.DEFAULT_RATE)
                engine.setProperty("volume", self.DEFAULT_VOLUME)
                engine.save_to_file(clean_text, str(output_path))
                engine.runAndWait()

                audio_bytes = output_path.read_bytes()
        except Exception as exc:
            raise VoiceSynthesisError(str(exc)) from exc

        if not audio_bytes:
            raise VoiceSynthesisError("Le fichier vocal genere est vide.")

        return {
            "available": True,
            "mime_type": "audio/wav",
            "encoding": "base64",
            "content": base64.b64encode(audio_bytes).decode("utf-8"),
        }

    def _normalize_text_for_speech(self, text: str) -> str:
        clean_text = str(text or "").strip()
        if not clean_text:
            return ""

        clean_text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", clean_text)
        clean_text = re.sub(r"https?://\S+", " lien ", clean_text)
        clean_text = re.sub(r"(?m)^\s*[-•]\s+", "", clean_text)

        replacements = {
            "\r": " ",
            "\n": ". ",
            "\t": " ",
            "*": " ",
            "`": " ",
            "#": " ",
            "_": " ",
            "|": " ",
            "\\": " ",
            "/": " ",
            "->": " puis ",
            "=>": " donc ",
            "&": " et ",
        }
        for old, new in replacements.items():
            clean_text = clean_text.replace(old, new)

        clean_text = re.sub(r"<[^>]+>", " ", clean_text)
        clean_text = re.sub(r"[\[\]{}()<>]", " ", clean_text)
        clean_text = re.sub(r"\s*[-]{2,}\s*", ". ", clean_text)
        clean_text = re.sub(r"\s+", " ", clean_text)
        clean_text = re.sub(r"\s+([,.;:!?])", r"\1", clean_text)
        clean_text = re.sub(r"([.;:!?]){2,}", r"\1", clean_text)

        return clean_text.strip()
