from __future__ import annotations

from typing import Any

from .config import is_hashem_chat_enabled
from .loader import HashemModuleLoadError, load_hashem_orchestrator_module
from .response_mapper import map_hashem_response
from .role_mapper import HashemRoleMapper


class HashemIntegrationError(RuntimeError):
    pass


class HashemChatService:
    def __init__(self, role_mapper: HashemRoleMapper | None = None) -> None:
        self.role_mapper = role_mapper or HashemRoleMapper()

    def handle(
        self,
        user_request: str,
        response_language: str,
        user_id: int | None = None,
        conversation_id: int | None = None,
    ) -> dict[str, Any]:
        del user_id, conversation_id

        if not is_hashem_chat_enabled():
            raise HashemIntegrationError("L'integration Hashem est desactivee.")

        try:
            orchestrator_module = load_hashem_orchestrator_module()
            orchestrator = orchestrator_module.OrchestratorAgent(api_key="")
        except HashemModuleLoadError as exc:
            raise HashemIntegrationError(str(exc)) from exc
        except Exception as exc:
            raise HashemIntegrationError(
                f"Echec d'initialisation de l'orchestrateur Hashem: {exc}"
            ) from exc

        role = self.role_mapper.resolve(user_request)
        try:
            raw_response = orchestrator.run(user_request)
        except Exception as exc:
            raise HashemIntegrationError(
                f"Echec d'execution de l'orchestrateur Hashem: {exc}"
            ) from exc
        finally:
            close = getattr(orchestrator, "close", None)
            if callable(close):
                try:
                    close()
                except Exception:
                    pass

        if not isinstance(raw_response, dict):
            raise HashemIntegrationError(
                "L'orchestrateur Hashem n'a pas retourne une reponse exploitable."
            )

        return map_hashem_response(
            raw_response=raw_response,
            response_language=response_language,
            role=role,
        )
