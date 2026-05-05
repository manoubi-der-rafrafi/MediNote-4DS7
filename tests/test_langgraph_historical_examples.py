import unittest

from gestionBDD.interrogation.service import _normalize_sql_filter_values
from orchestrateur.classification.langgraph_classifier import LangGraphClassifier
from orchestrateur.orchestrator_service import OrchestratorService


class LangGraphHistoricalExamplesTests(unittest.TestCase):
    def setUp(self):
        self.legacy_service = OrchestratorService()
        self.classifier = LangGraphClassifier(self.legacy_service)

    def test_builds_keyword_hits_from_request(self):
        result = self.classifier._extract_keywords(
            {"user_request": "Montre moi les publications video generees"}
        )
        self.assertIn("publication", result["keyword_hits"])
        self.assertIn("publication_query", result["keyword_hits"])

    def test_classifies_from_historical_examples_for_reports(self):
        classification = self.classifier._classify_from_historical_examples(
            {
                "user_request": "Montre moi les rapports existants",
                "historical_examples": [
                    {
                        "user_text": "Liste les rapports existants",
                        "intent": "rapport",
                        "action": "query_database",
                        "shared_keywords": ["liste", "rapports"],
                        "score": 3,
                    },
                    {
                        "user_text": "Montre les rapports sauvegardes",
                        "intent": "rapport",
                        "action": "query_database",
                        "shared_keywords": ["montre", "rapports"],
                        "score": 3,
                    },
                ],
            }
        )
        self.assertIsNotNone(classification)
        self.assertEqual(classification["intent"], "rapport")
        self.assertEqual(classification["action"], "query_database")

    def test_rejects_weak_historical_match(self):
        classification = self.classifier._classify_from_historical_examples(
            {
                "user_request": "Bonjour",
                "historical_examples": [
                    {
                        "user_text": "bonjour rapport",
                        "intent": "rapport",
                        "action": "query_database",
                        "shared_keywords": ["rapport"],
                        "score": 1,
                    }
                ],
            }
        )
        self.assertIsNone(classification)

    def test_local_structuring_rule_keeps_priority_over_examples(self):
        result = self.classifier._classify_request(
            {
                "user_request": "je veux structurer ce rapport",
                "historical_examples": [
                    {
                        "user_text": "je veux voir les rapports structures",
                        "intent": "rapport",
                        "action": "query_database",
                        "shared_keywords": ["rapport", "structurer"],
                        "score": 4,
                    }
                ],
            }
        )
        self.assertEqual(result["classification"]["intent"], "rapport")
        self.assertEqual(result["classification"]["action"], "structure_report")
        self.assertIsNone(result["classification"]["rapport"])

    def test_publication_db_phrase_in_english_is_detected(self):
        normalized = self.legacy_service._normalize_text(
            "give me all the pubplication image from the DB"
        )
        self.assertTrue(
            self.legacy_service._looks_like_publication_database_query(normalized)
        )

    def test_union_query_with_branch_limits_is_wrapped(self):
        sql = (
            "SELECT id, image_path, description_post FROM generated_images WHERE accepted = 1 LIMIT 10 "
            "UNION ALL "
            "SELECT id, video_path, description_post FROM generated_videos WHERE accepted = 1 LIMIT 10"
        )
        normalized = _normalize_sql_filter_values(sql)
        self.assertIn(
            "(SELECT id, image_path, description_post FROM generated_images WHERE accepted = 1 LIMIT 10)",
            normalized,
        )
        self.assertIn(
            "(SELECT id, video_path, description_post FROM generated_videos WHERE accepted = 1 LIMIT 10)",
            normalized,
        )


if __name__ == "__main__":
    unittest.main()
