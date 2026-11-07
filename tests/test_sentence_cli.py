"""Sentence CLI checks with fixture dictionaries and mocked model generation."""
import contextlib
import io
import itertools
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import call, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts import test_sentence
from fixmarge.rag import LexiconRAG


def entry(identifier, form, en, ja, ko):
    return {"id": identifier, "form": form, "aliases": [],
            "senses": {"en": [en], "ja": [ja], "ko": [ko]},
            "sources": ["fixture"], "status": "fixture"}


class SentenceCliTests(unittest.TestCase):
    def setUp(self):
        self.rag = LexiconRAG(
            entries=[entry("truth", "sinruits", "truth", "真実", "진실"),
                     entry("blood", "ChiDd", "blood", "血", "피")],
            rules=[], external_dir=Path(__file__).parent / "fixtures" / "missing_external")
        self.standard_context = {
            "available": True, "languages": ["en", "ja"], "matched_entry_count": 1,
            "entries": [{"entry": {"id": "oewn:fixture-truth", "lemma": "truth", "language": "en",
                                    "glosses": ["fixture dictionary definition"], "source": "oewn:2025",
                                    "license": "CC-BY-4.0 + WordNet"},
                         "matches": [{"query": "truth", "reasons": ["input"]}]}],
            "attributions": [{"source": "oewn:2025", "license": "CC-BY-4.0 + WordNet"}],
            "source_policy": "verified_wnja_1.1_and_oewn_2025_only", "segmentation_verified": False,
            "limitations": ["Fixture lexical evidence, not sentence verification."],
        }
        standard_patch = patch.object(test_sentence, "lookup_standard_dictionary", return_value=self.standard_context)
        self.standard_lookup = standard_patch.start()
        self.addCleanup(standard_patch.stop)

    def run_cli(self, *arguments):
        output, errors = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(output), contextlib.redirect_stderr(errors):
            code = test_sentence.main(list(arguments))
        self.assertEqual(code, 0, errors.getvalue())
        return json.loads(output.getvalue())

    def test_twelve_directions_default_to_offline_dry_run_without_weights(self):
        words = {"fix": "sinruits", "en": "truth", "ja": "真実", "ko": "진실"}
        names = ("HF_HUB_OFFLINE", "TRANSFORMERS_OFFLINE", "HF_HUB_DISABLE_TELEMETRY")
        for source, target in itertools.permutations(words, 2):
            with self.subTest(source=source, target=target), patch.dict(os.environ, {name: "0" for name in names}):
                with patch.object(test_sentence, "LexiconRAG", return_value=self.rag) as constructor:
                    with patch.object(self.rag, "lookup", wraps=self.rag.lookup) as lookup:
                        with patch.object(test_sentence, "ModelRunner") as runner:
                            result = self.run_cli("--source", source, "--target", target, "--text", words[source])
                self.assertEqual(result["mode"], "dry-run")
                self.assertEqual(result["direction"], f"{source}-to-{target}")
                self.assertFalse(result["model"]["loaded"])
                self.assertFalse(result["model"]["allow_download"])
                self.assertFalse(result["sentence_verified"])
                self.assertFalse(result["training_performed"])
                self.assertEqual(result["input_provenance"], {"type": "user_supplied", "text": words[source]})
                self.assertNotIn("raw_output", result)
                self.assertNotIn("diagnostic", result)
                self.assertEqual(result["source_evidence"]["standard_dictionary"], self.standard_context)
                standard = json.loads(result["prompt"][1]["content"])["evidence"]["standard_dictionary"]
                self.assertTrue(standard["available"])
                self.assertEqual(standard["languages"], ["en", "ja"])
                self.assertEqual(standard["entries"][0]["entry"]["source"], "oewn:2025")
                self.assertEqual(standard["entries"][0]["entry"]["license"], "CC-BY-4.0 + WordNet")
                self.assertEqual(self.standard_lookup.call_args.kwargs["languages"], ("en", "ja"))
                self.assertEqual({name: os.environ[name] for name in names}, {name: "1" for name in names})
                runner.assert_not_called()
                if "fix" in (source, target):
                    constructor.assert_called_once_with()
                    lookup.assert_called_once_with(words[source], f"{source}-to-{target}")
                    self.assertTrue(result["source_evidence"]["dictionary_assessed"])
                else:
                    constructor.assert_not_called()
                    lookup.assert_not_called()
                    self.assertFalse(result["source_evidence"]["dictionary_assessed"])
                    self.assertEqual(json.loads(result["prompt"][1]["content"])["mode"], "general_language_control")

    def test_fix_source_adds_only_english_and_japanese_gloss_queries(self):
        with patch.object(test_sentence, "LexiconRAG", return_value=self.rag):
            with patch.object(test_sentence, "ModelRunner") as runner:
                result = self.run_cli("--source", "fix", "--target", "ko", "--text", "sinruits")
        self.standard_lookup.assert_called_once_with(
            "sinruits", external_dir=None, languages=("en", "ja"),
            extra_queries=[("truth", "fiXmArge_gloss:truth:en"), ("真実", "fiXmArge_gloss:truth:ja")],
            include_input=False)
        self.assertEqual(result["source_evidence"]["standard_dictionary"], self.standard_context)
        runner.assert_not_called()

    def test_same_language_nonpositive_length_and_download_flag_are_rejected(self):
        cases = [
            ["--source", "en", "--target", "en", "--text", "truth"],
            ["--source", "en", "--target", "ja", "--text", "truth", "--max-new-tokens", "0"],
            ["--source", "en", "--target", "ja", "--text", "truth", "--max-new-tokens", "-1"],
            ["--source", "en", "--target", "ja", "--text", "truth", "--allow-download"],
        ]
        for arguments in cases:
            with self.subTest(arguments=arguments), contextlib.redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit) as error:
                    test_sentence.main(arguments)
                self.assertEqual(error.exception.code, 2)

    def test_generated_fix_output_keeps_raw_and_audits_spelling_gaps_and_ids(self):
        tentative = "🙂 sinruits [UNRESOLVED: mystery] Bogus"
        raw = json.dumps({"tentative_translation": tentative, "evidence_ids": ["truth", "blood"],
                          "uncertainties": ["Grammar remains a hypothesis."]}, ensure_ascii=True)
        with patch.object(test_sentence, "LexiconRAG", return_value=self.rag):
            with patch.object(self.rag, "lookup", wraps=self.rag.lookup) as lookup:
                with patch.object(test_sentence, "ModelRunner") as runner:
                    runner.return_value.generate.return_value = raw
                    result = self.run_cli("--source", "en", "--target", "fix", "--text", "truth mystery",
                                          "--generate", "--device", "cpu", "--max-new-tokens", "17")
        runner.assert_called_once_with(model_name=test_sentence.DEFAULT_MODEL, adapter=None,
                                       revision="cdbee75f17c01a7cc42f958dc650907174af0554",
                                       device="cpu", allow_download=False, max_new_tokens=17)
        runner.return_value.generate.assert_called_once_with(result["prompt"])
        self.assertEqual(lookup.call_args_list, [call("truth mystery", "en-to-fix"), call(tentative, "fix-to-ja")])
        self.assertTrue(result["model"]["loaded"])
        self.assertEqual(result["raw_output"], raw)
        diagnostic = result["diagnostic"]
        self.assertEqual(diagnostic["raw_output"], raw)
        self.assertEqual(diagnostic["tentative_translation"], tentative)
        self.assertEqual(diagnostic["unsupported_evidence_ids"], ["blood"])
        self.assertEqual([span["text"] for span in diagnostic["registered_output_spans"]], ["sinruits"])
        self.assertEqual([span["text"] for span in diagnostic["unsupported_output_spans"]], ["Bogus"])
        self.assertEqual([span["text"] for span in diagnostic["explicit_gap_placeholders"]], ["[UNRESOLVED: mystery]"])
        for group in ("registered_output_spans", "unsupported_output_spans", "explicit_gap_placeholders"):
            for span in diagnostic[group]:
                self.assertEqual(tentative[span["start"]:span["end"]], span["text"])
        self.assertFalse(diagnostic["sentence_verified"])
        self.assertFalse(diagnostic["output_source_alignment_verified"])

    def test_generated_natural_language_control_never_constructs_rag(self):
        raw = json.dumps({"tentative_translation": "真実を知りたい。", "evidence_ids": [],
                          "uncertainties": ["Unverified control."]}, ensure_ascii=False)
        with patch.object(test_sentence, "LexiconRAG", side_effect=AssertionError("Natural controls must not use RAG")):
            with patch.object(test_sentence, "ModelRunner") as runner:
                runner.return_value.generate.return_value = raw
                result = self.run_cli("--source", "en", "--target", "ja", "--text", "I want to know the truth.",
                                      "--generate")
        runner.assert_called_once()
        self.assertEqual(result["raw_output"], raw)
        self.assertEqual(result["diagnostic"]["tentative_translation"], "真実を知りたい。")
        self.assertFalse(result["diagnostic"]["output_dictionary_assessed"])
        self.assertFalse(result["source_evidence"]["dictionary_assessed"])
        self.assertTrue(result["source_evidence"]["standard_dictionary"]["available"])
        self.standard_lookup.assert_called_once_with(
            "I want to know the truth.", external_dir=None, languages=("en", "ja"), extra_queries=[], include_input=True)

    def test_fix_to_natural_uses_input_lookup_without_output_audit(self):
        raw = json.dumps({"tentative_translation": "진실.", "evidence_ids": ["truth"],
                          "uncertainties": ["Machine paraphrase, not an attested reference."]}, ensure_ascii=False)
        with patch.object(test_sentence, "LexiconRAG", return_value=self.rag):
            with patch.object(self.rag, "lookup", wraps=self.rag.lookup) as lookup:
                with patch.object(test_sentence, "ModelRunner") as runner:
                    runner.return_value.generate.return_value = raw
                    result = self.run_cli("--source", "fix", "--target", "ko", "--text", "sinruits", "--generate")
        lookup.assert_called_once_with("sinruits", "fix-to-ko")
        self.assertEqual(result["diagnostic"]["tentative_translation"], "진실.")
        self.assertFalse(result["diagnostic"]["output_dictionary_assessed"])

    def test_invalid_raw_json_is_reported_without_a_fabricated_output_lookup(self):
        with patch.object(test_sentence, "LexiconRAG", return_value=self.rag):
            with patch.object(self.rag, "lookup", wraps=self.rag.lookup) as lookup:
                with patch.object(test_sentence, "ModelRunner") as runner:
                    runner.return_value.generate.return_value = "{unfinished"
                    result = self.run_cli("--source", "en", "--target", "fix", "--text", "truth", "--generate")
        lookup.assert_called_once_with("truth", "en-to-fix")
        self.assertEqual(result["raw_output"], "{unfinished")
        self.assertFalse(result["diagnostic"]["raw_json_valid"])
        self.assertIsNone(result["diagnostic"]["tentative_translation"])
        self.assertFalse(result["diagnostic"]["output_dictionary_assessed"])

    def test_optional_output_saves_the_same_json_as_stdout(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "nested" / "report.json"
            with patch.object(test_sentence, "LexiconRAG") as rag, patch.object(test_sentence, "ModelRunner") as runner:
                result = self.run_cli("--source", "ja", "--target", "en", "--text", "真実を知りたい。",
                                      "--output", str(path))
            self.assertEqual(json.loads(path.read_text(encoding="utf-8")), result)
            rag.assert_not_called()
            runner.assert_not_called()

    def test_cached_model_error_fails_without_an_output_artifact(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "report.json"
            output, errors = io.StringIO(), io.StringIO()
            with patch.object(test_sentence, "ModelRunner", side_effect=RuntimeError("Cached model missing")):
                with contextlib.redirect_stdout(output), contextlib.redirect_stderr(errors):
                    code = test_sentence.main(["--source", "en", "--target", "ja", "--text", "truth",
                                               "--generate", "--output", str(path)])
            self.assertEqual(code, 2)
            self.assertEqual(output.getvalue(), "")
            self.assertFalse(path.exists())
            error = json.loads(errors.getvalue())
            self.assertIn("Cached model missing", error["error"])
            self.assertFalse(error["sentence_verified"])
            self.assertFalse(error["training_performed"])


if __name__ == "__main__":
    unittest.main()
