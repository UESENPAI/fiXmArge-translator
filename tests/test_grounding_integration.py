import contextlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.evaluate import evaluate_rows
from fixmarge.infer import ModelRunner, main
from fixmarge.rag import LexiconRAG, build_prompt


def lexical_entry(identifier, form, english):
    return {"id": identifier, "form": form, "aliases": [],
            "senses": {"ja": ["真実"], "en": english, "ko": []},
            "sources": ["fixture"], "notes": [], "status": "fixture"}


def evaluation_row(query, reference, direction):
    return {"messages": [{"role": "user", "content": direction + ": " + query},
                         {"role": "assistant", "content": reference}],
            "metadata": {"direction": direction, "task": "lexical_translation",
                         "rights_status": "self_authored"}}


class FakeRunner:
    def __init__(self, output):
        self.output = output
        self.prompts = []

    def generate(self, messages):
        self.prompts.append(messages)
        return self.output


class GroundingIntegrationTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.directory = Path(temporary.name)
        self.entries = [lexical_entry("singular", "sinRuit", []),
                        lexical_entry("plural", "sinruits", ["truth"])]
        (self.directory / "lexicon.jsonl").write_text(
            "".join(json.dumps(entry, ensure_ascii=False) + "\n" for entry in self.entries),
            encoding="utf-8")
        (self.directory / "rules.jsonl").write_text("", encoding="utf-8")
        self.external = self.directory / "missing-external"
        self.rag = LexiconRAG(entries=self.entries, rules=[], external_dir=self.external)

    def run_cli(self, query, direction, *options):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            code = main(["--data-dir", str(self.directory), "--external-dir", str(self.external),
                         "--text", query, "--direction", direction, *options])
        self.assertEqual(code, 0)
        return json.loads(output.getvalue())

    def test_cli_reverse_english_preserves_raw_wrong_language_and_null(self):
        for translation in ["錯語", None]:
            raw = json.dumps({"translation": translation}, ensure_ascii=False)
            with self.subTest(raw=raw), patch("fixmarge.infer.generate", return_value=raw) as generate:
                result = self.run_cli("truth", "en-to-fix", "--generate", "--model", "fixture")
            generate.assert_called_once()
            final = json.loads(result["generation"])
            self.assertEqual(final["translation"], "sinruits")
            self.assertEqual(final["grounding"]["target_language"], "fix")
            self.assertEqual(result["generation_raw"], raw)
            self.assertIn("lexical_contract", result)

    def test_cli_reverse_japanese_keeps_every_canonical_candidate(self):
        raw = json.dumps({"translation": "sinRuit"})
        with patch("fixmarge.infer.generate", return_value=raw):
            result = self.run_cli("真実", "ja-to-fix", "--generate", "--model", "fixture")
        final = json.loads(result["generation"])
        self.assertEqual(final["translation"], "sinRuit / sinruits")
        self.assertEqual(final["grounding"]["target_language"], "fix")
        self.assertEqual(result["generation_raw"], raw)

    def test_default_dry_run_never_calls_generation_or_loads_weights(self):
        with patch("fixmarge.infer.generate") as generate, patch("fixmarge.infer._load_bundle") as load:
            result = self.run_cli("truth", "en-to-fix", "--model", "missing-model",
                                  "--device", "cuda", "--load-in-4bit")
        generate.assert_not_called()
        load.assert_not_called()
        self.assertEqual(result["mode"], "dry-run")
        self.assertIn("lexical_contract", result)
        self.assertNotIn("generation", result)
        self.assertNotIn("generation_raw", result)

    def test_model_runner_keeps_the_raw_generation_api(self):
        raw = json.dumps({"translation": "錯語"}, ensure_ascii=False)
        with patch("fixmarge.infer._load_bundle", return_value=("torch", "tokenizer", "model")):
            with patch("fixmarge.infer._generate_bundle", return_value=raw):
                runner = ModelRunner(model_name="fixture", adapter=None, allow_download=False)
                self.assertEqual(runner.generate([{"role": "user", "content": "fixture"}]), raw)

    def assert_rag_evaluation(self, query, reference, direction, raw):
        runner = FakeRunner(raw)
        row = evaluation_row(query, reference, direction)
        report = evaluate_rows([row], mode="rag", rag=self.rag, runner=runner)
        record = report["records"][0]
        self.assertEqual(record["raw_output"], raw)
        self.assertFalse(record["raw_exact_reference"])
        self.assertEqual(report["raw_exact_reference_rate"], 0.0)
        self.assertEqual(report["output_source"], "dictionary_grounded")
        self.assertTrue(record["exact_reference"])
        self.assertEqual(report["exact_reference_rate"], 1.0)
        final = json.loads(record["output"])
        self.assertEqual(final["translation"], reference)
        self.assertEqual(final["grounding"]["target_language"], "fix")
        expected_prompt = build_prompt(self.rag.lookup(query, direction))
        self.assertEqual(record["prompt"], expected_prompt)
        self.assertEqual(runner.prompts, [expected_prompt])
        self.assertNotIn(row["messages"][-1], record["prompt"])
        self.assertFalse(any(message["role"] == "assistant" for message in record["prompt"]))
        return final

    def test_rag_evaluation_separates_wrong_language_raw_and_grounded_scores(self):
        raw = json.dumps({"translation": "錯語"}, ensure_ascii=False)
        self.assert_rag_evaluation("truth", "sinruits", "en-to-fix", raw)

    def test_rag_evaluation_preserves_all_reverse_candidates(self):
        raw = json.dumps({"translation": "sinRuit"})
        final = self.assert_rag_evaluation("真実", "sinRuit / sinruits", "ja-to-fix", raw)
        self.assertEqual(final["translation"].split(" / "), ["sinRuit", "sinruits"])
        coverage = final["grounding"]["candidate_coverage"][0]
        self.assertEqual(coverage["expected"], ["sinRuit", "sinruits"])
        self.assertEqual(coverage["raw_returned"], ["sinRuit"])
        self.assertEqual(coverage["missing"], ["sinruits"])
        self.assertEqual(coverage["final_alternatives"], ["sinRuit", "sinruits"])

    def test_rag_evaluation_dry_run_has_no_model_or_grounded_score(self):
        row = evaluation_row("truth", "sinruits", "en-to-fix")
        report = evaluate_rows([row], mode="rag", rag=self.rag)
        self.assertEqual(report["execution"], "dry-run")
        self.assertEqual(report["output_source"], "none")
        self.assertIsNone(report["exact_reference_rate"])
        self.assertIsNone(report["raw_exact_reference_rate"])
        self.assertNotIn("output", report["records"][0])
        self.assertNotIn("raw_output", report["records"][0])

    def test_plain_evaluation_keeps_wrong_language_output_unchanged(self):
        raw = json.dumps({"translation": "錯語"}, ensure_ascii=False)
        runner = FakeRunner(raw)
        row = evaluation_row("truth", "sinruits", "en-to-fix")
        report = evaluate_rows([row], mode="plain", runner=runner)
        record = report["records"][0]
        self.assertEqual(record["output"], raw)
        self.assertEqual(record["raw_output"], raw)
        self.assertEqual(report["output_source"], "model")
        self.assertFalse(record["exact_reference"])
        self.assertEqual(report["exact_reference_rate"], 0.0)
        self.assertNotIn("lookup", record)
        self.assertEqual(runner.prompts, [[row["messages"][0]]])


if __name__ == "__main__":
    unittest.main()
