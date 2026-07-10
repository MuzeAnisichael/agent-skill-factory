import json
import unittest
from pathlib import Path

from skill_factory.schemas import EVAL_SCHEMA, TRACE_SCHEMA


class SchemaTests(unittest.TestCase):
    def test_eval_schema_is_valid_json_payload(self) -> None:
        payload = json.loads(json.dumps(EVAL_SCHEMA))

        self.assertEqual(payload["$schema"], "https://json-schema.org/draft/2020-12/schema")
        self.assertIn("trigger_tests", payload["properties"])
        self.assertIn("task_tests", payload["properties"])

    def test_published_eval_schema_matches_package_schema(self) -> None:
        docs_schema_path = Path(__file__).parents[1] / "docs" / "eval-schema.json"
        docs_schema = json.loads(docs_schema_path.read_text(encoding="utf-8"))

        self.assertEqual(docs_schema, EVAL_SCHEMA)

    def test_trace_schema_is_valid_json_payload(self) -> None:
        payload = json.loads(json.dumps(TRACE_SCHEMA))

        self.assertEqual(payload["properties"]["schema_version"]["const"], 1)
        self.assertEqual(payload["$defs"]["run"]["properties"]["status"]["enum"], ["success", "failure"])

    def test_published_trace_schema_matches_package_schema(self) -> None:
        docs_schema_path = Path(__file__).parents[1] / "docs" / "trace-schema.json"
        docs_schema = json.loads(docs_schema_path.read_text(encoding="utf-8"))

        self.assertEqual(docs_schema, TRACE_SCHEMA)


if __name__ == "__main__":
    unittest.main()
