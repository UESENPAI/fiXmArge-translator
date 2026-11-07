import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.evaluate import candidate, evaluate_rows, exact_reference
from fixmarge.infer import ModelRunner
from fixmarge.rag import LexiconRAG


def row(query="test", reference="secret_gold", direction="fix-to-ko", task="lexical_translation"):
    return {"messages": [{"role": "user", "content": "fiXmArge -> ko: " + query},
                         {"role": "assistant", "content": reference}],
            "metadata": {"direction": direction, "task": task, "rights_status": "game_derived_not_eligible"}}


class EvaluationTests(unittest.TestCase):
    def test_gold_is_removed_and_rule_examples_are_counted_separately(self):
        report = evaluate_rows([row(), row(task="rule_explanation"), {"metadata": {"task": "lexical_translation"}}])
        self.assertEqual(report["counts"]["selected"], 1)
        self.assertEqual(report["counts"]["skipped_rule_explanation"], 1)
        self.assertEqual(report["counts"]["skipped_invalid"], 1)
        self.assertNotIn("secret_gold", json.dumps(report["records"][0]["prompt"]))
        self.assertIsNone(report["exact_reference_rate"])

    def test_reverse_alternatives_case_and_optional_punctuation(self):
        self.assertTrue(exact_reference("B", "A / B", ["A", "B"]))
        self.assertFalse(exact_reference("b", "A / B", ["A", "B"]))
        self.assertFalse(exact_reference("Iz’u", "Iz'u"))
        self.assertTrue(exact_reference("Iz’u", "Iz'u", punctuation_aliases=True))
        self.assertTrue(exact_reference('{"translation":"B"}', "A / B", ["A", "B"]))

    def test_direction_filter_uses_metadata_and_preserves_query_colons(self):
        report = evaluate_rows([row(), row(query="word:detail", direction="en-to-fix"), []], direction_filter="en-to-fix")
        self.assertEqual(report["counts"]["selected"], 1)
        self.assertEqual(report["records"][0]["query"], "word:detail")
        self.assertEqual(report["counts"]["skipped_invalid"], 1)

    def test_rag_builds_data_prompt_and_labels_assisted_metric(self):
        rag = LexiconRAG(entries=[{"id": "x", "form": "test", "senses": {"ko": ["attested"]}}],
                         rules=[], external_dir="missing_fixture_external")
        report = evaluate_rows([row()], mode="rag", rag=rag)
        self.assertEqual(report["metric"], "rag_exact_draft_reference")
        self.assertIn("attested", json.dumps(report["records"][0]["prompt"]))
        self.assertNotIn("secret_gold", json.dumps(report["records"][0]["prompt"]))

    def test_runner_loads_once_and_reuses_bundle(self):
        with patch("fixmarge.infer._load_bundle", return_value=("torch", "tokenizer", "model")) as load:
            with patch("fixmarge.infer._generate_bundle", return_value="secret_gold") as generate:
                runner = ModelRunner(model_name="fixture", adapter=None, allow_download=False)
                report = evaluate_rows([row(), row(query="second")], runner=runner)
                self.assertEqual(load.call_count, 1)
                self.assertEqual(generate.call_count, 2)
                self.assertEqual(report["exact_reference_rate"], 1.0)


if __name__ == "__main__":
    unittest.main()
