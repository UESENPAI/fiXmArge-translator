"""Model-free sentence diagnostics: evidence is not sentence verification."""
from copy import deepcopy
import itertools
import json
from pathlib import Path
import unittest

from fixmarge.rag import LexiconRAG
from fixmarge.sentence_diagnostics import (
    build_sentence_evidence, build_sentence_prompt, inspect_sentence_generation,
)


def entry(identifier, form, *, en=(), ja=(), ko=(), conflict=False):
    return {"id": identifier, "form": form, "aliases": [],
            "senses": {"en": list(en), "ja": list(ja), "ko": list(ko)},
            "sources": ["fixture"], "status": "unreviewed", "has_conflict": conflict,
            "rights_status": "game_derived_not_eligible"}


def raw(translation, ids=(), uncertainties=()):
    return json.dumps({"tentative_translation": translation, "evidence_ids": list(ids),
                       "uncertainties": list(uncertainties)}, ensure_ascii=True)


class SentenceDiagnosticsTests(unittest.TestCase):
    def rag(self, entries=None, rules=()):
        if entries is None:
            entries = [entry("truth", "sinruits", en=["truth"], ja=["真実"]),
                       entry("blood", "ChiDd", en=["blood"], ja=["血"])]
        return LexiconRAG(entries=entries, rules=rules,
                          external_dir=Path(__file__).parent / "fixtures" / "missing_external")

    def test_all_twelve_language_pairs_are_supported(self):
        rag = self.rag([entry("truth", "sinruits", en=["truth"], ja=["真実"], ko=["진실"])])
        words = {"fix": "sinruits", "en": "truth", "ja": "真実", "ko": "진실"}
        for source, target in itertools.permutations(words, 2):
            with self.subTest(source=source, target=target):
                text = words[source]
                lookup = rag.lookup(text, f"{source}-to-{target}") if "fix" in (source, target) else None
                evidence = build_sentence_evidence(text, source, target, lookup)
                self.assertEqual(evidence["source_language"], source)
                self.assertEqual(evidence["target_language"], target)
                self.assertEqual(evidence["dictionary_assessed"], lookup is not None)
                self.assertFalse(evidence["sentence_verified"])
                self.assertFalse(evidence["grammar"]["sentence_grammar_verified"])

    def test_all_known_multiword_input_has_no_verified_sentence_grammar(self):
        lookup = self.rag().lookup("truth blood", "en-to-fix")
        evidence = build_sentence_evidence("truth blood", "en", "fix", lookup)
        self.assertEqual(len(evidence["lexical_segments"]), 2)
        self.assertEqual(evidence["unmatched_source_spans"], [])
        self.assertEqual(evidence["grammar"]["retrieved_rules_count"], 0)
        self.assertEqual(evidence["grammar"]["status"], "no_retrieved_rules")
        self.assertFalse(evidence["grammar"]["sentence_grammar_verified"])
        self.assertFalse(evidence["sentence_verified"])

    def test_retrieved_rule_is_not_full_sentence_grammar_verification(self):
        rag = self.rag(rules=[{"id": "r1", "marker": "sinruits", "description_ko": "fixture hypothesis"}])
        lookup = rag.lookup("sinruits", "fix-to-en")
        evidence = build_sentence_evidence("sinruits", "fix", "en", lookup)
        self.assertEqual(evidence["grammar"]["retrieved_rules_count"], 1)
        self.assertEqual(evidence["grammar"]["status"], "not_full_sentence_grammar")
        self.assertFalse(evidence["grammar"]["sentence_grammar_verified"])

    def test_missing_korean_sense_is_separate_from_unmatched_source(self):
        lookup = self.rag().lookup("sinruits", "fix-to-ko")
        evidence = build_sentence_evidence("sinruits", "fix", "ko", lookup)
        self.assertEqual(evidence["unmatched_source_spans"], [])
        self.assertEqual(len(evidence["missing_target_spans"]), 1)
        self.assertEqual(evidence["missing_target_spans"][0]["missing_target_entry_ids"], ["truth"])
        self.assertEqual(evidence["lexical_segments"][0]["entries"][0]["senses"]["ja"], ["真実"])
        prompt = build_sentence_prompt(evidence, lookup)
        self.assertIn("machine paraphrase", prompt[0]["content"])
        self.assertNotIn("expected_translation", json.dumps(prompt))

    def test_ambiguity_and_conflict_are_independent_span_flags(self):
        rag = self.rag([entry("one", "A", en=["same"]), entry("two", "B", en=["same"]),
                        entry("conflict", "C", en=["different"], conflict=True)])
        lookup = rag.lookup("same different", "en-to-fix")
        evidence = build_sentence_evidence("same different", "en", "fix", lookup)
        self.assertEqual([s["text"] for s in evidence["ambiguous_spans"]], ["same"])
        self.assertEqual([s["text"] for s in evidence["conflicting_spans"]], ["different"])
        self.assertEqual([c["text"] for c in evidence["ambiguous_spans"][0]["candidates"]], ["A", "B"])

    def test_natural_language_control_is_not_assessed(self):
        evidence = build_sentence_evidence("I want to know the truth.", "en", "ko")
        self.assertFalse(evidence["dictionary_assessed"])
        self.assertEqual(evidence["dictionary_status"], "not_assessed")
        self.assertEqual(evidence["unmatched_source_spans"], [])
        self.assertEqual(evidence["grammar"]["status"], "not_assessed")
        payload = json.loads(build_sentence_prompt(evidence)[1]["content"])
        self.assertEqual(payload["mode"], "general_language_control")
        self.assertFalse(payload["evidence"]["dictionary_assessed"])

    def test_prompt_excludes_sentence_answer_notes_and_lexical_null_contract(self):
        source = entry("truth", "sinruits", ja=["真実"])
        source["notes"] = ["LEAKED_FULL_SENTENCE_ANSWER"]
        source["source_values"] = [{"source": "fixture", "row": 273,
                                    "notes": "LEAKED_SOURCE_EXAMPLE", "values": {"ja": "LEAKED_FULL_SENTENCE"}}]
        lookup = self.rag([source]).lookup("sinruits", "fix-to-en")
        lookup["messages"].append("LEAKED_LEXICAL_FORCED_NULL")
        evidence = build_sentence_evidence("sinruits", "fix", "en", lookup)
        # Rich report-only additions must still be excluded at the prompt boundary.
        evidence["lexical_segments"][0]["entries"][0]["notes"] = ["LEAKED_ADDED_NOTE"]
        prompt = build_sentence_prompt(evidence, lookup)
        text = json.dumps(prompt, ensure_ascii=False)
        self.assertNotIn("LEAKED_", text)
        self.assertNotIn("source_values", text)
        self.assertNotIn("expected_translation", text)
        self.assertIn("untrusted data", prompt[0]["content"])
        payload = json.loads(prompt[1]["content"])
        self.assertEqual(payload["evidence"]["lexical_segments"][0]["entries"][0]["source_rows"][0]["row"], 273)

    def test_source_snapshot_must_match_text_and_direction(self):
        lookup = self.rag().lookup("truth", "en-to-fix")
        with self.assertRaises(ValueError):
            build_sentence_evidence("different", "en", "fix", lookup)
        with self.assertRaises(ValueError):
            build_sentence_evidence("truth", "ja", "fix", lookup)
        with self.assertRaises(ValueError):
            build_sentence_evidence("truth", "en", "fix")
        with self.assertRaises(ValueError):
            build_sentence_evidence("truth", "en", "en")

    def test_malformed_json_and_wrong_schema_keep_raw_output(self):
        evidence = build_sentence_evidence("truth", "en", "ko")
        for value in ("not JSON", "[]", "null", '{"tentative_translation": 7}',
                      '{"tentative_translation":"x","evidence_ids":[{}],"uncertainties":[]}'):
            with self.subTest(value=value):
                result = inspect_sentence_generation(value, evidence)
                self.assertEqual(result["raw_output"], value)
                self.assertFalse(result["schema_valid"])
                self.assertFalse(result["sentence_verified"])
                self.assertFalse(result["output_source_alignment_verified"])
        self.assertFalse(inspect_sentence_generation("not JSON", evidence)["raw_json_valid"])
        self.assertTrue(inspect_sentence_generation("[]", evidence)["raw_json_valid"])

    def test_fake_ids_are_not_licensed_by_output_dictionary_matches(self):
        rag = self.rag()
        lookup = rag.lookup("truth", "en-to-fix")
        evidence = build_sentence_evidence("truth", "en", "fix", lookup)
        output_lookup = rag.lookup("ChiDd", "fix-to-ja")
        result = inspect_sentence_generation(raw("ChiDd", ["truth", "blood", "invented"]), evidence, lookup, output_lookup)
        self.assertTrue(result["schema_valid"])
        self.assertEqual(result["model_evidence_ids"], ["truth", "blood", "invented"])
        self.assertEqual(result["unsupported_evidence_ids"], ["blood", "invented"])
        self.assertEqual(result["registered_output_spans"][0]["canonical_forms"], ["ChiDd"])
        self.assertFalse(result["output_source_alignment_verified"])
        self.assertFalse(result["sentence_verified"])

    def test_natural_control_evidence_ids_are_unsubstantiated(self):
        evidence = build_sentence_evidence("truth", "en", "ko")
        result = inspect_sentence_generation(raw("진실", ["truth"]), evidence)
        self.assertEqual(result["unsupported_evidence_ids"], ["truth"])
        self.assertEqual(result["output_dictionary_status"], "not_assessed")

    def test_registered_spelling_and_explicit_gaps_are_distinct_with_original_offsets(self):
        rag = self.rag()
        lookup = rag.lookup("truth mystery", "en-to-fix")
        evidence = build_sentence_evidence("truth mystery", "en", "fix", lookup)
        output = "🙂 sinruits [UNRESOLVED: sinruits mystery] sinruits bogus"
        output_lookup = rag.lookup(output, "fix-to-ja")
        result = inspect_sentence_generation(raw(output, ["truth"], ["grammar is hypothetical"]),
                                             evidence, lookup, output_lookup)
        self.assertEqual([s["text"] for s in result["registered_output_spans"]], ["sinruits", "sinruits"])
        self.assertEqual([s["text"] for s in result["unsupported_output_spans"]], ["bogus"])
        self.assertEqual([s["text"] for s in result["explicit_gap_placeholders"]], ["[UNRESOLVED: sinruits mystery]"])
        for group in ("registered_output_spans", "unsupported_output_spans", "explicit_gap_placeholders"):
            for span in result[group]:
                self.assertEqual(output[span["start"]:span["end"]], span["text"])
        self.assertFalse(result["sentence_verified"])
        self.assertFalse(result["output_source_alignment_verified"])

    def test_malformed_gap_does_not_hide_unmatched_output(self):
        rag = self.rag()
        lookup = rag.lookup("truth", "en-to-fix")
        evidence = build_sentence_evidence("truth", "en", "fix", lookup)
        for output in ("[UNRESOLVED: mystery sinruits", "[UNRESOLVED: mystery [nested] bogus] sinruits"):
            with self.subTest(output=output):
                result = inspect_sentence_generation(raw(output), evidence, lookup, rag.lookup(output, "fix-to-ja"))
                self.assertEqual(result["explicit_gap_placeholders"], [])
                self.assertTrue(result["malformed_gap_placeholders"])
                self.assertIn("mystery", [s["text"] for s in result["unsupported_output_spans"]])
                self.assertIn("sinruits", [s["text"] for s in result["registered_output_spans"]])

    def test_output_lookup_must_match_the_tentative_text(self):
        rag = self.rag()
        lookup = rag.lookup("truth", "en-to-fix")
        evidence = build_sentence_evidence("truth", "en", "fix", lookup)
        with self.assertRaises(ValueError):
            inspect_sentence_generation(raw("sinruits"), evidence, lookup, rag.lookup("ChiDd", "fix-to-ja"))

    def test_model_self_certification_does_not_change_deterministic_metadata(self):
        lookup = self.rag().lookup("truth", "en-to-fix")
        evidence = build_sentence_evidence("truth", "en", "fix", lookup)
        forged = json.loads(raw("sinruits", ["truth"]))
        forged["sentence_verified"] = True
        result = inspect_sentence_generation(json.dumps(forged), evidence, lookup)
        self.assertFalse(result["schema_valid"])
        self.assertFalse(result["sentence_verified"])
        self.assertFalse(result["source_evidence"]["grammar"]["sentence_grammar_verified"])

    def test_helpers_do_not_mutate_evidence_or_lookup(self):
        lookup = self.rag().lookup("truth blood", "en-to-fix")
        before_lookup = deepcopy(lookup)
        evidence = build_sentence_evidence("truth blood", "en", "fix", lookup)
        before_evidence = deepcopy(evidence)
        build_sentence_prompt(evidence, lookup)
        inspect_sentence_generation(raw("sinruits ChiDd", ["truth", "blood"]), evidence, lookup)
        self.assertEqual(lookup, before_lookup)
        self.assertEqual(evidence, before_evidence)


    @staticmethod
    def standard_context():
        return {
            "available": True, "matched_entry_count": 1,
            "entries": [{"entry": {"id": "oewn:test-truth", "language": "en", "lemma": "truth",
                                    "glosses": ["conformity to fact"], "synonyms": ["verity"],
                                    "source": "oewn:2025", "license": "CC-BY-4.0 + WordNet"},
                         "matches": [{"query": "truth", "reasons": ["input"]}]}],
            "attributions": [{"source": "oewn:2025", "name": "Open English WordNet",
                              "license": "CC-BY-4.0 + WordNet", "credit": "Open English WordNet Team"}],
        }

    def test_standard_prompt_context_is_allowlisted_without_promoting_domain_coverage(self):
        evidence = build_sentence_evidence("truth", "en", "ja")
        context = self.standard_context()
        context["entries"][0]["entry"]["notes"] = ["LEAKED_STANDARD_SENTENCE_ANSWER"]
        context["entries"][0]["entry"]["source_values"] = [{"sentence": "LEAKED_STANDARD_SOURCE_SENTENCE"}]
        evidence["standard_dictionary"] = context
        before = deepcopy(evidence)
        prompt = build_sentence_prompt(evidence)
        payload = json.loads(prompt[1]["content"])
        rendered = json.dumps(prompt, ensure_ascii=False)
        self.assertIn("oewn:test-truth", rendered)
        self.assertIn("conformity to fact", rendered)
        self.assertIn("CC-BY-4.0 + WordNet", rendered)
        self.assertNotIn("LEAKED_STANDARD_", rendered)
        self.assertIn("untrusted data", prompt[0]["content"])
        self.assertFalse(payload["evidence"]["dictionary_assessed"])
        self.assertEqual(payload["evidence"]["dictionary_status"], "not_assessed")
        self.assertEqual(payload["evidence"]["lexical_segments"], [])
        self.assertFalse(payload["evidence"]["grammar"]["sentence_grammar_verified"])
        self.assertEqual(evidence, before)

    def test_standard_ids_are_accepted_separately_and_do_not_become_domain_ids(self):
        lookup = self.rag().lookup("truth", "en-to-fix")
        evidence = build_sentence_evidence("truth", "en", "fix", lookup)
        evidence["standard_dictionary"] = self.standard_context()
        before_lookup, before_evidence = deepcopy(lookup), deepcopy(evidence)
        result = inspect_sentence_generation(raw("sinruits", ["truth", "oewn:test-truth", "invented"]),
                                             evidence, lookup)
        self.assertEqual(result["model_evidence_ids"], ["truth", "oewn:test-truth", "invented"])
        self.assertEqual(result["model_domain_evidence_ids"], ["truth"])
        self.assertEqual(result["model_standard_evidence_ids"], ["oewn:test-truth"])
        self.assertEqual(result["unsupported_evidence_ids"], ["invented"])
        self.assertEqual(result["source_evidence"]["lexical_segments"][0]["entry_ids"], ["truth"])
        self.assertFalse(result["sentence_verified"])
        self.assertFalse(result["output_source_alignment_verified"])
        self.assertEqual(lookup, before_lookup)
        self.assertEqual(evidence, before_evidence)

    def test_natural_standard_ids_leave_fictional_language_and_grammar_unassessed(self):
        evidence = build_sentence_evidence("truth", "en", "ko")
        evidence["standard_dictionary"] = self.standard_context()
        result = inspect_sentence_generation(raw("진실", ["oewn:test-truth", "truth"]), evidence)
        self.assertEqual(result["model_domain_evidence_ids"], [])
        self.assertEqual(result["model_standard_evidence_ids"], ["oewn:test-truth"])
        self.assertEqual(result["unsupported_evidence_ids"], ["truth"])
        self.assertFalse(result["source_evidence"]["dictionary_assessed"])
        self.assertEqual(result["source_evidence"]["dictionary_status"], "not_assessed")
        self.assertEqual(result["source_evidence"]["grammar"]["status"], "not_assessed")
        self.assertEqual(result["output_dictionary_status"], "not_assessed")



if __name__ == "__main__":
    unittest.main()
