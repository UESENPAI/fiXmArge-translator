"""Korean query bridges preserve indirect provenance and never mint fiXmArge forms."""
from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock

from fixmarge.demo import DemoService
from fixmarge.rag import LexiconRAG


def domain_entry(identifier, form, *, en=(), ja=()):
    return {"id": identifier, "form": form, "aliases": [],
            "senses": {"en": list(en), "ja": list(ja), "ko": []},
            "sources": ["fixture"], "status": "unreviewed",
            "rights_status": "game_derived_not_eligible", "has_conflict": False}


def rewrite(queries):
    return json.dumps({"queries": queries}, ensure_ascii=False)


def answer(text="sinruits", identifiers=("truth",)):
    return json.dumps({"tentative_translation": text, "evidence_ids": list(identifiers),
                       "uncertainties": ["Machine query paraphrase; fiXmArge grammar unverified."]},
                      ensure_ascii=False)


class KoreanRetrievalTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.external = Path(temporary.name) / "absent-external-index"
        self.entries = [domain_entry("truth", "sinruits", en=["truth"], ja=["真実"]),
                        domain_entry("blood", "ChiDd", en=["blood"], ja=["血"])]
        self.queries = [{"language": "ja", "text": "真実"}, {"language": "en", "text": "truth"}]

    def service(self, outputs):
        rag = LexiconRAG(entries=self.entries, rules=[], external_dir=self.external)
        runner = Mock()
        runner.generate.side_effect = outputs
        runner_factory = Mock(return_value=runner)
        service = DemoService(external_dir=self.external, runner_factory=runner_factory,
                              rag_factory=Mock(return_value=rag))
        return service, runner, runner_factory

    def test_korean_bridge_retrieves_existing_forms_and_preserves_indirect_provenance(self):
        original = deepcopy(self.entries)
        raw = answer()
        service, runner, runner_factory = self.service([rewrite(self.queries), raw])
        result = service.run("진실", "ko", "fix", generate=True)
        self.assertTrue(result["query_rewrite_performed"])
        self.assertTrue(result["generation_performed"])
        self.assertEqual(runner.generate.call_count, 2)
        runner_factory.assert_called_once()
        evidence = result["source_evidence"]
        self.assertEqual(evidence["source_text"], "진실")
        self.assertEqual(evidence["lexical_segments"], [])
        self.assertEqual([span["text"] for span in evidence["unmatched_source_spans"]], ["진실"])
        self.assertFalse(evidence["grammar"]["sentence_grammar_verified"])
        indirect = evidence["indirect_dictionary"]
        self.assertFalse(indirect["query_translation_verified"])
        self.assertEqual({record["entry"]["id"] for record in indirect["entries"]}, {"truth"})
        self.assertEqual(len(indirect["entries"]), 1)
        self.assertTrue(indirect["entries"][0]["matches"])
        prompt = runner.generate.call_args_list[1].args[0]
        payload = json.loads(prompt[1]["content"])
        supplied = payload["evidence"]["indirect_dictionary"]
        self.assertEqual(supplied["entries"][0]["entry"]["form"], "sinruits")
        self.assertFalse(supplied["query_translation_verified"])
        diagnostic = result["diagnostic"]
        self.assertEqual(diagnostic["raw_output"], raw)
        self.assertEqual(diagnostic["model_indirect_evidence_ids"], ["truth"])
        self.assertEqual(diagnostic["model_domain_evidence_ids"], [])
        self.assertEqual(diagnostic["unsupported_evidence_ids"], [])
        self.assertEqual(diagnostic["registered_output_spans"][0]["canonical_forms"], ["sinruits"])
        self.assertFalse(result["sentence_verified"])
        self.assertEqual(self.entries, original)
        self.assertFalse(self.external.exists())

    def test_rewrite_text_matching_a_fix_form_is_not_itself_a_supported_target(self):
        service, runner, _ = self.service([rewrite([{"language": "en", "text": "sinruits"}])])
        result = service.run("진실", "ko", "fix", generate=True)
        self.assertTrue(result["query_rewrite_performed"])
        self.assertEqual(result["answer_source"], "abstained")
        self.assertNotIn("dictionary_answer", result)
        self.assertNotIn("diagnostic", result)
        self.assertEqual(runner.generate.call_count, 1)
        self.assertFalse(result["sentence_verified"])

    def test_invalid_rewrites_abstain_without_a_second_model_call(self):
        invalid = [
            "not JSON", "null", "[]", "{}", '{"queries":null}',
            rewrite([{ "language": "ko", "text": "진실"}]),
            rewrite([{ "language": "fix", "text": "sinruits"}]),
            rewrite([{ "language": "en", "text": 42}]),
            rewrite([{ "language": "en", "text": "truth", "form": "MadeUp"}]),
            rewrite([{ "language": "en", "text": "x" * 81}]),
            rewrite([{ "language": "en", "text": "truth"}] * 9),
            json.dumps({"queries": self.queries, "tentative_translation": "MadeUp"}),
        ]
        for raw in invalid:
            with self.subTest(raw=raw):
                service, runner, _ = self.service([raw])
                result = service.run("진실", "ko", "fix", generate=True)
                self.assertEqual(result["answer_source"], "abstained")
                self.assertTrue(result["query_rewrite_performed"])
                self.assertEqual(runner.generate.call_count, 1)
                self.assertNotIn("dictionary_answer", result)
                self.assertNotIn("diagnostic", result)
                self.assertFalse(result["sentence_verified"])

    def test_valid_queries_without_dictionary_hits_abstain_without_translation(self):
        service, runner, _ = self.service([rewrite([{"language": "en", "text": "unmatched"}])])
        result = service.run("알수없음", "ko", "fix", generate=True)
        self.assertEqual(result["answer_source"], "abstained")
        self.assertTrue(result["query_rewrite_performed"])
        self.assertEqual(runner.generate.call_count, 1)
        self.assertEqual(result["source_evidence"]["lexical_segments"], [])
        self.assertEqual([span["text"] for span in result["source_evidence"]["unmatched_source_spans"]], ["알수없음"])
        self.assertNotIn("diagnostic", result)

    def test_korean_dry_run_does_not_call_a_model_or_rewrite_queries(self):
        service, runner, runner_factory = self.service([])
        result = service.run("진실", "ko", "fix", generate=False)
        self.assertFalse(result.get("query_rewrite_performed", False))
        self.assertFalse(result["generation_performed"])
        self.assertFalse(result["model_loaded"])
        self.assertEqual(result["source_evidence"]["lexical_segments"], [])
        runner.generate.assert_not_called()
        runner_factory.assert_not_called()

    def test_generated_unknown_output_and_fabricated_citations_are_still_audited(self):
        raw = answer("sinruits MadeUp", ("truth", "invented"))
        service, runner, _ = self.service([rewrite(self.queries), raw])
        result = service.run("진실", "ko", "fix", generate=True)
        diagnostic = result["diagnostic"]
        self.assertEqual(diagnostic["raw_output"], raw)
        self.assertEqual(diagnostic["model_indirect_evidence_ids"], ["truth"])
        self.assertEqual(diagnostic["model_domain_evidence_ids"], [])
        self.assertEqual(diagnostic["unsupported_evidence_ids"], ["invented"])
        self.assertEqual([span["text"] for span in diagnostic["unsupported_output_spans"]], ["MadeUp"])
        self.assertFalse(diagnostic["output_source_alignment_verified"])
        self.assertFalse(result["sentence_verified"])
        self.assertEqual(runner.generate.call_count, 2)


if __name__ == "__main__":
    unittest.main()
