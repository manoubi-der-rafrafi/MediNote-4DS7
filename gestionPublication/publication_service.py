import json
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib import request
from urllib.error import HTTPError

from .generation_config import (
    DEFAULT_MODEL_NAME,
    OPENAI_VIDEOS_URL,
    OUTPUT_DIR,
    PublicationGeminiConfigError,
    PublicationOpenAIConfigError,
    VIDEO_MODEL_NAME,
    VIDEO_OUTPUT_FILENAME,
    VIDEO_SECONDS,
    VIDEO_SIZE,
    VIDEO_STATUS_POLL_SECONDS,
    build_gemini_client,
    build_video_prompt,
    get_openai_api_key,
)
from .occasion_service import OccasionService, OccasionServiceError


class PublicationConfigError(RuntimeError):
    pass


class PublicationRequestError(RuntimeError):
    pass


class PublicationResponseError(RuntimeError):
    pass


class PublicationPersistenceError(RuntimeError):
    pass


class PublicationService:
    def __init__(self, model_name: str = DEFAULT_MODEL_NAME) -> None:
        self.model_name = model_name
        self.occasion_service = OccasionService()

    def handle(self, orchestrator_payload: dict[str, Any]) -> dict[str, Any]:
        media_type = str(orchestrator_payload.get("media_type", "")).strip().lower()
        generation_mode = str(orchestrator_payload.get("generation_mode", "")).strip().lower()

        if media_type != "video":
            raise PublicationRequestError(
                "Le service video attend media_type='video'."
            )

        if generation_mode != "next_occasion":
            raise PublicationRequestError(
                "La generation video n'est supportee que pour generation_mode='next_occasion'."
            )

        try:
            publication_context = self.occasion_service.get_next_occasion_with_product()
        except OccasionServiceError as exc:
            raise PublicationRequestError(str(exc)) from exc

        generation_result = self._generate_content(publication_context)
        self._validate_date_window(
            publication_context["date_actuelle"],
            publication_context["date_occasion"],
            generation_result["date_publication"],
        )

        final_result: dict[str, Any] = {
            "status": "success",
            "intent": "publication",
            "type_publication": "video",
            "generation_mode": "next_occasion",
            "occasion": publication_context["occasion"],
            "date_occasion": publication_context["date_occasion"],
            "date_publication": generation_result["date_publication"],
            "saison": publication_context["saison"],
            "produit": publication_context["produit"],
            "produit_source": publication_context["produit_source"],
            "code_article": publication_context["code_article"],
            "product_url": publication_context["product_url"],
            "image_url": publication_context["image_url"],
            "description_post": generation_result["description_post"],
            "prompt_VDO": generation_result["prompt_VDO"],
        }

        output_dir = self._prepare_output_dir(final_result)
        saved_files = self._write_metadata(output_dir, final_result)
        asset_files = self._generate_video_asset(output_dir, final_result)
        saved_files.update(asset_files)
        final_result["saved_files"] = saved_files
        self._write_metadata(output_dir, final_result)
        return final_result

    def _generate_content(
        self,
        publication_context: dict[str, Any],
    ) -> dict[str, str]:
        try:
            client = build_gemini_client()
        except PublicationGeminiConfigError as exc:
            raise PublicationConfigError(str(exc)) from exc

        prompt = build_video_prompt(publication_context)

        try:
            response = client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config={
                    "temperature": 0.7,
                    "response_mime_type": "application/json",
                },
            )
        except Exception as exc:
            raise PublicationRequestError(str(exc)) from exc

        try:
            payload_text = getattr(response, "text", "")
            payload = json.loads(payload_text)
            if not isinstance(payload, dict):
                raise TypeError("La reponse publication doit etre un objet JSON.")
        except Exception as exc:
            raise PublicationResponseError(
                "La reponse Gemini pour la publication n'est pas un JSON valide."
            ) from exc

        required_keys = {"description_post", "date_publication", "prompt_VDO"}
        missing = [key for key in required_keys if not str(payload.get(key, "")).strip()]
        if missing:
            raise PublicationResponseError(
                f"La reponse publication est incomplete. Champs manquants: {', '.join(missing)}."
            )

        return {
            key: str(value).strip()
            for key, value in payload.items()
            if isinstance(value, (str, int, float))
        }

    @staticmethod
    def _validate_date_window(
        start_iso: str,
        end_iso: str,
        publication_iso: str,
    ) -> None:
        start_date = datetime.strptime(start_iso, "%Y-%m-%d").date()
        end_date = datetime.strptime(end_iso, "%Y-%m-%d").date()
        publication_date = datetime.strptime(publication_iso, "%Y-%m-%d").date()

        if not (start_date <= publication_date <= end_date):
            raise PublicationResponseError(
                "La date_publication retournee par Gemini est hors intervalle."
            )

    def _prepare_output_dir(self, result: dict[str, Any]) -> Path:
        safe_occasion = self._slugify(result["occasion"])
        safe_media = self._slugify(result["type_publication"])
        output_dir = OUTPUT_DIR / f'{result["date_occasion"]}_{safe_occasion}_{safe_media}'

        try:
            output_dir.mkdir(parents=True, exist_ok=True)
        except Exception as exc:
            raise PublicationPersistenceError(
                f"Echec de la preparation du dossier publication: {exc}"
            ) from exc

        return output_dir

    def _write_metadata(self, output_dir: Path, result: dict[str, Any]) -> dict[str, str]:
        metadata_path = output_dir / "metadata.json"
        try:
            metadata_path.write_text(
                json.dumps(result, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except Exception as exc:
            raise PublicationPersistenceError(
                f"Echec de la sauvegarde des metadonnees publication: {exc}"
            ) from exc

        return {
            "output_dir": str(output_dir),
            "metadata_json": str(metadata_path),
        }

    def _generate_video_asset(
        self,
        output_dir: Path,
        result: dict[str, Any],
    ) -> dict[str, str]:
        try:
            openai_api_key = get_openai_api_key()
        except PublicationOpenAIConfigError as exc:
            raise PublicationConfigError(str(exc)) from exc

        body, content_type = self._build_multipart_form_data(
            {
                "model": VIDEO_MODEL_NAME,
                "prompt": result["prompt_VDO"],
                "size": VIDEO_SIZE,
                "seconds": VIDEO_SECONDS,
            }
        )

        create_request = request.Request(
            OPENAI_VIDEOS_URL,
            data=body,
            headers={
                "Authorization": f"Bearer {openai_api_key}",
                "Content-Type": content_type,
            },
            method="POST",
        )

        try:
            with request.urlopen(create_request, timeout=300) as response:
                video_job = json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            error_body = exc.read().decode("utf-8", errors="replace")
            raise PublicationRequestError(
                f"Echec API OpenAI video ({exc.code}): {error_body}"
            ) from exc
        except Exception as exc:
            raise PublicationRequestError(f"Echec demarrage generation video: {exc}") from exc

        video_id = video_job.get("id")
        if not video_id:
            raise PublicationResponseError(
                "La reponse OpenAI video ne contient pas d'identifiant de generation."
            )

        while video_job.get("status") in {"queued", "in_progress"}:
            time.sleep(VIDEO_STATUS_POLL_SECONDS)

            status_request = request.Request(
                f"{OPENAI_VIDEOS_URL}/{video_id}",
                headers={"Authorization": f"Bearer {openai_api_key}"},
                method="GET",
            )

            try:
                with request.urlopen(status_request, timeout=300) as response:
                    video_job = json.loads(response.read().decode("utf-8"))
            except HTTPError as exc:
                error_body = exc.read().decode("utf-8", errors="replace")
                raise PublicationRequestError(
                    f"Echec API OpenAI video status ({exc.code}): {error_body}"
                ) from exc
            except Exception as exc:
                raise PublicationRequestError(
                    f"Echec verification statut video: {exc}"
                ) from exc

        if video_job.get("status") != "completed":
            raise PublicationResponseError(
                f"La generation video a echoue: {json.dumps(video_job, ensure_ascii=False)}"
            )

        download_request = request.Request(
            f"{OPENAI_VIDEOS_URL}/{video_id}/content",
            headers={"Authorization": f"Bearer {openai_api_key}"},
            method="GET",
        )

        try:
            with request.urlopen(download_request, timeout=300) as response:
                video_bytes = response.read()
        except HTTPError as exc:
            error_body = exc.read().decode("utf-8", errors="replace")
            raise PublicationRequestError(
                f"Echec telechargement video OpenAI ({exc.code}): {error_body}"
            ) from exc
        except Exception as exc:
            raise PublicationRequestError(
                f"Echec telechargement du fichier video: {exc}"
            ) from exc

        video_path = output_dir / VIDEO_OUTPUT_FILENAME
        try:
            video_path.write_bytes(video_bytes)
        except Exception as exc:
            raise PublicationPersistenceError(
                f"Echec de sauvegarde du fichier video: {exc}"
            ) from exc

        return {
            "video_file": str(video_path),
        }

    @staticmethod
    def _build_multipart_form_data(fields: dict[str, str]) -> tuple[bytes, str]:
        boundary = f"----CodexBoundary{int(time.time() * 1000)}"
        body = bytearray()

        for name, value in fields.items():
            body.extend(f"--{boundary}\r\n".encode("utf-8"))
            body.extend(
                f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode("utf-8")
            )
            body.extend(str(value).encode("utf-8"))
            body.extend(b"\r\n")

        body.extend(f"--{boundary}--\r\n".encode("utf-8"))
        return bytes(body), f"multipart/form-data; boundary={boundary}"

    @staticmethod
    def _slugify(value: str) -> str:
        lowered = value.strip().lower()
        lowered = re.sub(r"[^a-z0-9]+", "_", lowered)
        return lowered.strip("_") or "publication"
