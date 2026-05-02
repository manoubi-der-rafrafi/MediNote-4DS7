from __future__ import annotations

from werkzeug.datastructures import FileStorage

from google.genai import types

from gemini_keyring import (
    DEFAULT_MODEL_NAME,
    GeminiKeyConfigError,
    generate_content_with_key_rotation,
)


class VoiceValidationError(ValueError):
    pass


class VoiceTranscriptionConfigError(RuntimeError):
    pass


class VoiceTranscriptionRequestError(RuntimeError):
    pass


class VoiceTranscriptionService:
    ALLOWED_MIME_TYPES = {
        "audio/mpeg",
        "audio/mp3",
        "audio/wav",
        "audio/wave",
        "audio/x-wav",
        "audio/webm",
        "audio/mp4",
        "audio/m4a",
        "audio/x-m4a",
        "audio/ogg",
    }
    MAX_AUDIO_BYTES = 25 * 1024 * 1024

    def __init__(self, model_name: str = DEFAULT_MODEL_NAME) -> None:
        self.model_name = model_name

    def transcribe(self, audio_file: FileStorage | None) -> str:
        audio_bytes, mime_type = self._read_audio_file(audio_file)

        try:
            response = generate_content_with_key_rotation(
                model=self.model_name,
                contents=[
                    types.Part.from_bytes(data=audio_bytes, mime_type=mime_type),
                    (
                        "Transcris exactement le contenu vocal en texte brut. "
                        "Ne reponds pas a la demande, ne traduis pas, n'ajoute aucun commentaire."
                    ),
                ],
                config={
                    "temperature": 0,
                },
            )
        except GeminiKeyConfigError as exc:
            raise VoiceTranscriptionConfigError(str(exc)) from exc
        except Exception as exc:
            raise VoiceTranscriptionRequestError(str(exc)) from exc

        transcription = str(getattr(response, "text", "") or "").strip()
        if not transcription:
            raise VoiceTranscriptionRequestError(
                "La transcription audio est vide ou invalide."
            )

        return transcription

    def _read_audio_file(self, audio_file: FileStorage | None) -> tuple[bytes, str]:
        if audio_file is None:
            raise VoiceValidationError("Le fichier vocal 'voice' est obligatoire.")

        filename = str(audio_file.filename or "").strip()
        if not filename:
            raise VoiceValidationError("Le fichier vocal doit avoir un nom valide.")

        mime_type = str(audio_file.mimetype or "").strip().lower()
        if mime_type not in self.ALLOWED_MIME_TYPES:
            raise VoiceValidationError(
                "Format audio non supporte. Utilisez wav, mp3, m4a, webm ou ogg."
            )

        audio_bytes = audio_file.read()
        if not audio_bytes:
            raise VoiceValidationError("Le fichier vocal est vide.")

        if len(audio_bytes) > self.MAX_AUDIO_BYTES:
            raise VoiceValidationError(
                "Le fichier vocal depasse la taille maximale autorisee de 25 MB."
            )

        return audio_bytes, mime_type
