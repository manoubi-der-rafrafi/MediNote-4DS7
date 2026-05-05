import unittest
from types import SimpleNamespace

from orchestrateur.hashem_router import HashemRouter, should_try_hashem_fallback
from orchestrateur.orchestrator_service import OrchestratorService
from hashem_integration.response_mapper import map_hashem_response


class FakeRouter:
    def __init__(self, should_route: bool) -> None:
        self.should_route = should_route
        self.calls: list[str] = []

    def detect(self, user_request: str):
        self.calls.append(user_request)
        return SimpleNamespace(
            should_route=self.should_route,
            confidence=0.91 if self.should_route else 0.0,
            reason="test",
            task_id="pharmacy_churn_risk" if self.should_route else None,
        )


class FakeHashemChatService:
    def __init__(self) -> None:
        self.calls: list[dict] = []

    def handle(self, **kwargs):
        self.calls.append(kwargs)
        return {
            "status": "success",
            "intent": "hashem_chat",
            "action": "delegate_to_hashem",
            "response_language": kwargs["response_language"],
            "message": "Hashem answer",
            "data": {"source": "hashem_orchestrator"},
            "display": {"kind": "hashem_analysis"},
            "choices": [],
            "missing_fields": [],
        }


class HashemIntegrationTests(unittest.TestCase):
    def test_should_try_hashem_fallback_for_unknown_intent(self):
        self.assertTrue(should_try_hashem_fallback({"intent": "inconnue"}))
        self.assertFalse(should_try_hashem_fallback({"intent": "rapport", "action": "structure_report"}))

    def test_router_matches_hashem_domain_keywords(self):
        router = HashemRouter()
        decision = router._detect_with_local_keywords(
            "Donne moi le risque de churn pour cette pharmacie et le ranking des delegues."
        )
        self.assertTrue(decision.should_route)
        self.assertGreaterEqual(decision.confidence, 0.5)

    def test_response_mapper_normalizes_success_payload(self):
        payload = map_hashem_response(
            raw_response={
                "status": "success",
                "task_id": "pharmacy_churn_risk",
                "mode": "mode1",
                "top_results": [{"entity_id": "PH001"}],
                "explanation": "Analyse Medinote",
            },
            response_language="French",
            role="supervisor",
        )
        self.assertEqual(payload["intent"], "hashem_chat")
        self.assertEqual(payload["action"], "delegate_to_hashem")
        self.assertEqual(payload["status"], "success")
        self.assertEqual(payload["message"], "Analyse Medinote")

    def test_orchestrator_delegates_unknown_gemini_intent_to_hashem(self):
        fake_router = FakeRouter(should_route=True)
        fake_hashem_service = FakeHashemChatService()
        service = OrchestratorService(
            hashem_router=fake_router,
            hashem_chat_service=fake_hashem_service,
        )

        from orchestrateur import orchestrator_service as orchestrator_module

        original_generate = orchestrator_module.generate_content_with_key_rotation
        orchestrator_module.generate_content_with_key_rotation = lambda **kwargs: SimpleNamespace(
            parsed={"intent": "inconnue", "response_language": "French"}
        )
        try:
            result = service.handle("Quel est le risque de churn de cette pharmacie ?")
        finally:
            orchestrator_module.generate_content_with_key_rotation = original_generate

        self.assertEqual(result["intent"], "hashem_chat")
        self.assertEqual(len(fake_hashem_service.calls), 1)
        self.assertEqual(fake_hashem_service.calls[0]["response_language"], "French")

    def test_orchestrator_keeps_current_flow_for_supported_gemini_intent(self):
        fake_router = FakeRouter(should_route=True)
        fake_hashem_service = FakeHashemChatService()
        service = OrchestratorService(
            hashem_router=fake_router,
            hashem_chat_service=fake_hashem_service,
        )
        service._finalize_response = lambda *args, **kwargs: {"status": "success", "intent": "rapport"}  # type: ignore[method-assign]

        from orchestrateur import orchestrator_service as orchestrator_module

        original_generate = orchestrator_module.generate_content_with_key_rotation
        orchestrator_module.generate_content_with_key_rotation = lambda **kwargs: SimpleNamespace(
            parsed={"intent": "rapport", "action": "structure_report", "response_language": "French"}
        )
        try:
            result = service.handle("Structure ce rapport")
        finally:
            orchestrator_module.generate_content_with_key_rotation = original_generate

        self.assertEqual(result["intent"], "rapport")
        self.assertEqual(len(fake_hashem_service.calls), 0)


if __name__ == "__main__":
    unittest.main()
