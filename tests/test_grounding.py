"""Verify lexical grounding against independent, model-free fixtures."""
from copy import deepcopy
import json
from pathlib import Path
import unittest

from fixmarge.grounding import build_lexical_contract, ground_generation
from fixmarge.rag import LexiconRAG


def entry(identifier, form, *, en=(), ja=(), ko=(), aliases=(), conflict=False):
    return {
        "id": identifier, "form": form, "aliases": list(aliases),
        "senses": {"en": list(en), "ja": list(ja), "ko": list(ko)},
        "sources": ["fixture-source"], "status": "unreviewed",
        "rights_status": "game_derived_not_eligible", "has_conflict": conflict,
        "etymology": [{"text": "fixture hypothesis", "status": "fan_hypothesis"}],
    }


def raw_answer(translation, *, evidence_ids=(), unknown_tokens=(), analysis="Model lexical analysis.", warnings=()):
    return json.dumps({
        "translation": translation, "analysis": analysis,
        "evidence_ids": list(evidence_ids), "unknown_tokens": list(unknown_tokens),
        "warnings": list(warnings),
    }, ensure_ascii=False)


def candidate_texts(segment):
    return [candidate["text"] for candidate in segment["candidates"]]


class GroundingTests(unittest.TestCase):
    def rag(self, entries):
        return LexiconRAG(entries=entries, rules=[],
                          external_dir=Path(__file__).parent / "fixtures" / "missing_external")

    def truth_rag(self, *, ko=()):
        return self.rag([entry("truth", "sinruits", en=["truth"], ja=["真実"], ko=ko)])

    def assert_answer_fields(self, answer):
        for key in ("translation", "analysis", "evidence_ids", "unknown_tokens", "warnings",
                    "alternatives", "grounding"):
            self.assertIn(key, answer)
        for key in ("status", "scope", "target_language", "issues", "model_translation_matches",
                    "analysis_source", "model_analysis_verified", "candidate_coverage"):
            self.assertIn(key, answer["grounding"])

    def test_all_six_direction_contracts_select_only_requested_language(self):
        rag = self.truth_rag(ko=["진실"])
        cases = [("fix-to-en", "sinruits", "fix", "en", "truth"),
                 ("fix-to-ja", "sinruits", "fix", "ja", "真実"),
                 ("fix-to-ko", "sinruits", "fix", "ko", "진실"),
                 ("en-to-fix", "truth", "en", "fix", "sinruits"),
                 ("ja-to-fix", "真実", "ja", "fix", "sinruits"),
                 ("ko-to-fix", "진실", "ko", "fix", "sinruits")]
        for direction, text, source, target, expected in cases:
            with self.subTest(direction=direction):
                contract = build_lexical_contract(rag.lookup(text, direction))
                self.assertEqual(contract["direction"], direction)
                self.assertEqual(contract["source_language"], source)
                self.assertEqual(contract["target_language"], target)
                self.assertEqual(contract["scope"], "single_lexical")
                self.assertEqual(contract["expected_translation"], expected)
                self.assertEqual(contract["abstention_reasons"], [])
                self.assertEqual(candidate_texts(contract["segments"][0]), [expected])
                self.assertEqual(contract["segments"][0]["candidates"][0]["language"], target)

    def test_forward_multiple_senses_keep_existing_reference_separator(self):
        lookup = self.rag([entry("exit", "Dasou", en=["exit", "go out"])]).lookup("Dasou", "fix-to-en")
        contract = build_lexical_contract(lookup)
        self.assertEqual(contract["candidate_separator"], "; ")
        self.assertEqual(contract["expected_translation"], "exit; go out")
        answer = ground_generation(lookup, raw_answer("exit; go out", evidence_ids=["exit"]))
        self.assertEqual(answer["translation"], "exit; go out")
        self.assertEqual(answer["grounding"]["issues"], [])
        coverage = answer["grounding"]["candidate_coverage"][0]
        self.assertEqual(coverage["raw_returned"], ["exit", "go out"])
        self.assertEqual(coverage["missing"], [])
        # This is the format already used by prepare.py's lexical references.
        from scripts.evaluate import exact_reference
        self.assertTrue(exact_reference(json.dumps(answer), "exit; go out"))

    def test_forward_partial_sense_output_reports_the_omitted_candidate(self):
        lookup = self.rag([entry("exit", "Dasou", en=["exit", "go out"])]).lookup("Dasou", "fix-to-en")
        answer = ground_generation(lookup, raw_answer("exit", evidence_ids=["exit"]))
        self.assertEqual(answer["translation"], "exit; go out")
        self.assertTrue(answer["grounding"]["issues"])
        coverage = answer["grounding"]["candidate_coverage"][0]
        self.assertEqual(coverage["raw_returned"], ["exit"])
        self.assertEqual(coverage["missing"], ["go out"])
        self.assertEqual(coverage["final_alternatives"], ["exit", "go out"])

    def test_literal_delimiters_inside_source_senses_are_not_split(self):
        lookup = self.rag([entry("literal", "word", en=["input / output", "a; b"])]).lookup("word", "fix-to-en")
        contract = build_lexical_contract(lookup)
        self.assertEqual(candidate_texts(contract["segments"][0]), ["input / output", "a; b"])
        self.assertEqual(contract["expected_translation"], "input / output; a; b")
        complete = ground_generation(lookup, raw_answer("input / output; a; b", evidence_ids=["literal"]))
        self.assertEqual(complete["grounding"]["candidate_coverage"][0]["raw_returned"], ["input / output", "a; b"])
        self.assertEqual(complete["grounding"]["issues"], [])
        # The second candidate contains the display separator itself. Equality
        # of the entire returned literal must still count it as one candidate.
        partial = ground_generation(lookup, raw_answer("a; b", evidence_ids=["literal"]))
        coverage = partial["grounding"]["candidate_coverage"][0]
        self.assertEqual(coverage["raw_returned"], ["a; b"])
        self.assertEqual(coverage["missing"], ["input / output"])
        self.assertEqual(candidate_texts(partial["alternatives"][0]), ["input / output", "a; b"])

    def test_reverse_candidate_separator_stays_slash(self):
        lookup = self.rag([entry("first", "Alpha", en=["same"]),
                           entry("second", "Beta", en=["same"])]).lookup("same", "en-to-fix")
        contract = build_lexical_contract(lookup)
        self.assertEqual(contract["candidate_separator"], " / ")
        self.assertEqual(contract["expected_translation"], "Alpha / Beta")
        answer = ground_generation(lookup, raw_answer("Beta", evidence_ids=["first", "second"]))
        self.assertEqual(answer["translation"], "Alpha / Beta")
        self.assertEqual(answer["grounding"]["candidate_coverage"][0]["missing"], ["Alpha"])

    def test_provenance_and_duplicate_sense_sources_survive_deduplication(self):
        rag = self.rag([entry("source-a", "word", en=["truth"]),
                        entry("source-b", "word", en=["truth"])])
        contract = build_lexical_contract(rag.lookup("word", "fix-to-en"))
        segment = contract["segments"][0]
        self.assertEqual(candidate_texts(segment), ["truth"])
        self.assertEqual(set(segment["entry_ids"]), {"source-a", "source-b"})
        evidence = segment["candidates"][0]["evidence"]
        self.assertEqual({item["entry_id"] for item in evidence}, {"source-a", "source-b"})
        for item in evidence:
            self.assertEqual(item["form"], "word")
            self.assertEqual(item["sources"], ["fixture-source"])
            self.assertEqual(item["status"], "unreviewed")
            self.assertEqual(item["rights_status"], "game_derived_not_eligible")
            self.assertFalse(item["has_conflict"])
        # Etymology and rights labels do not erase the attested lexical sense.
        self.assertEqual(contract["expected_translation"], "truth")

    def test_reverse_missing_shorter_candidate_is_not_a_substring_match(self):
        rag = self.rag([entry("singular", "sinRuit", ja=["真実"]),
                        entry("plural", "sinruits", ja=["真実"])])
        lookup = rag.lookup("真実", "ja-to-fix")
        answer = ground_generation(lookup, raw_answer("sinruits", evidence_ids=["singular", "plural"]))
        self.assert_answer_fields(answer)
        self.assertEqual(answer["translation"], "sinRuit / sinruits")
        self.assertTrue(answer["grounding"]["issues"])
        coverage = answer["grounding"]["candidate_coverage"][0]
        self.assertEqual(coverage["expected"], ["sinRuit", "sinruits"])
        self.assertEqual(coverage["raw_returned"], ["sinruits"])
        self.assertEqual(coverage["missing"], ["sinRuit"])
        self.assertEqual(coverage["final_alternatives"], ["sinRuit", "sinruits"])
        self.assertFalse(answer["grounding"]["model_translation_matches"])

    def test_reverse_exact_prefix_is_not_reported_as_a_returned_candidate(self):
        rag = self.rag([entry("short", "term", en=["same"]),
                        entry("long", "terms", en=["same"])])
        answer = ground_generation(rag.lookup("same", "en-to-fix"),
                                   raw_answer("terms", evidence_ids=["short", "long"]))
        self.assertEqual(answer["translation"], "term / terms")
        coverage = answer["grounding"]["candidate_coverage"][0]
        self.assertEqual(coverage["raw_returned"], ["terms"])
        self.assertEqual(coverage["missing"], ["term"])

    def test_unknown_token_metadata_is_repaired_even_with_a_correct_translation(self):
        lookup = self.truth_rag().lookup("sinruits", "fix-to-en")
        answer = ground_generation(lookup, raw_answer("truth", evidence_ids=["truth"],
                                                     unknown_tokens=["sinruits"]))
        self.assertEqual(answer["translation"], "truth")
        self.assertEqual(answer["unknown_tokens"], [])
        self.assertTrue(answer["grounding"]["issues"])
        self.assertTrue(answer["grounding"]["model_translation_matches"])

    def test_different_target_language_is_replaced_with_listed_target_sense(self):
        lookup = self.truth_rag().lookup("sinruits", "fix-to-en")
        answer = ground_generation(lookup, raw_answer("真実", evidence_ids=["truth"]))
        self.assertEqual(answer["translation"], "truth")
        self.assertTrue(answer["grounding"]["issues"])
        self.assertFalse(answer["grounding"]["model_translation_matches"])

    def test_correct_translation_and_metadata_need_no_correction(self):
        lookup = self.truth_rag().lookup("sinruits", "fix-to-en")
        answer = ground_generation(lookup, raw_answer("truth", evidence_ids=["truth"],
                                                     analysis="A deliberately concise source-based analysis."))
        self.assert_answer_fields(answer)
        self.assertEqual(answer["translation"], "truth")
        self.assertIsInstance(answer["analysis"], str)
        self.assertEqual(answer["grounding"]["analysis_source"], "dictionary_evidence")
        self.assertEqual(answer["evidence_ids"], ["truth"])
        self.assertEqual(answer["unknown_tokens"], [])
        self.assertEqual(answer["grounding"]["issues"], [])
        self.assertEqual(answer["grounding"]["status"], "model_output_validated")
        self.assertTrue(answer["grounding"]["model_translation_matches"])
        self.assertFalse(answer["grounding"]["model_analysis_verified"])

    def test_case_distinct_canonical_forms_are_not_collapsed(self):
        rag = self.rag([entry("upper", "cOnzAI", en=["being"]),
                        entry("lower", "cOnzAi", en=["existence"])])
        self.assertEqual(build_lexical_contract(rag.lookup("cOnzAI", "fix-to-en"))["expected_translation"], "being")
        self.assertEqual(build_lexical_contract(rag.lookup("cOnzAi", "fix-to-en"))["expected_translation"], "existence")
        collision = build_lexical_contract(rag.lookup("CONZAI", "fix-to-en"))
        self.assertIsNone(collision["expected_translation"])
        self.assertEqual(set(candidate_texts(collision["segments"][0])), {"being", "existence"})
        self.assertTrue(collision["abstention_reasons"])

    def test_reverse_case_distinct_alternatives_are_both_retained(self):
        rag = self.rag([entry("upper", "AbC", en=["same"]),
                        entry("lower", "abc", en=["same"])])
        contract = build_lexical_contract(rag.lookup("same", "en-to-fix"))
        self.assertEqual(candidate_texts(contract["segments"][0]), ["AbC", "abc"])
        self.assertEqual(contract["expected_translation"], "AbC / abc")

    def test_punctuation_alias_lookup_uses_original_canonical_spelling(self):
        rag = self.rag([entry("quote", "Iz'u", en=["is"]),
                        entry("dot", "Cro·JI", en=["cross"])])
        for text, direction, expected in [("Iz’u", "fix-to-en", "is"),
                                           ("Cro・JI", "fix-to-en", "cross"),
                                           ("is", "en-to-fix", "Iz'u")]:
            with self.subTest(text=text):
                contract = build_lexical_contract(rag.lookup(text, direction))
                self.assertEqual(contract["expected_translation"], expected)
                self.assertEqual(contract["segments"][0]["text"], text)

    def test_multiword_headword_and_outer_whitespace_are_single_lexical(self):
        rag = self.rag([entry("phrase", "Two Words", en=["one lexical phrase"])])
        text = "  Two\tWords\n"
        contract = build_lexical_contract(rag.lookup(text, "fix-to-en"))
        self.assertEqual(contract["scope"], "single_lexical")
        self.assertEqual(contract["expected_translation"], "one lexical phrase")
        segment = contract["segments"][0]
        self.assertEqual(text[segment["start"]:segment["end"]], "Two\tWords")
        self.assertEqual(segment["text"], "Two\tWords")

    def test_source_conflict_abstains_but_keeps_all_senses_and_provenance(self):
        rag = self.rag([entry("court", "Syu Tain", ja=["開廷", "閉廷"], conflict=True)])
        lookup = rag.lookup("Syu Tain", "fix-to-ja")
        contract = build_lexical_contract(lookup)
        self.assertIsNone(contract["expected_translation"])
        self.assertEqual(contract["segments"][0]["conflicting_entry_ids"], ["court"])
        self.assertEqual(candidate_texts(contract["segments"][0]), ["開廷", "閉廷"])
        answer = ground_generation(lookup, raw_answer("開廷", evidence_ids=["court"]))
        self.assertIsNone(answer["translation"])
        self.assertEqual(candidate_texts(answer["alternatives"][0]), ["開廷", "閉廷"])
        self.assertTrue(answer["grounding"]["issues"])

    def test_missing_korean_sense_is_not_an_unknown_headword(self):
        lookup = self.truth_rag().lookup("sinruits", "fix-to-ko")
        contract = build_lexical_contract(lookup)
        self.assertIsNone(contract["expected_translation"])
        self.assertEqual(contract["scope"], "single_lexical")
        self.assertEqual(contract["segments"][0]["missing_target_entry_ids"], ["truth"])
        self.assertEqual(candidate_texts(contract["segments"][0]), [])
        answer = ground_generation(lookup, raw_answer("진실", evidence_ids=["truth"],
                                                     unknown_tokens=["sinruits"]))
        self.assertIsNone(answer["translation"])
        self.assertEqual(answer["unknown_tokens"], [])
        self.assertTrue(answer["grounding"]["issues"])

    def test_any_matched_entry_missing_target_sense_prevents_silent_omission(self):
        rag = self.rag([entry("known", "word", en=["truth"]), entry("missing", "word", ja=["真実"])])
        contract = build_lexical_contract(rag.lookup("word", "fix-to-en"))
        self.assertIsNone(contract["expected_translation"])
        self.assertEqual(candidate_texts(contract["segments"][0]), ["truth"])
        self.assertEqual(contract["segments"][0]["missing_target_entry_ids"], ["missing"])

    def test_unknown_korean_reverse_query_preserves_original_token_objects(self):
        lookup = self.truth_rag().lookup("진실", "ko-to-fix")
        answer = ground_generation(lookup, raw_answer("sinruits", evidence_ids=["invented"]))
        self.assertIsNone(answer["translation"])
        self.assertEqual(answer["unknown_tokens"], [{"text": "진실", "start": 0, "end": 2}])
        self.assertEqual(answer["evidence_ids"], [])
        self.assertEqual(answer["grounding"]["scope"], "no_lexical_evidence")

    def test_multiple_spans_and_repeated_words_are_not_joined_as_a_translation(self):
        rag = self.rag([entry("truth", "sinruits", en=["truth"]),
                        entry("blood", "ChiDd", en=["blood"])])
        for text in ("truth blood", "truth truth"):
            with self.subTest(text=text):
                lookup = rag.lookup(text, "en-to-fix")
                contract = build_lexical_contract(lookup)
                self.assertEqual(contract["scope"], "partial_lexical")
                self.assertIsNone(contract["expected_translation"])
                self.assertEqual(len(contract["segments"]), 2)
                answer = ground_generation(lookup, raw_answer("sinruits / ChiDd", evidence_ids=["truth", "blood"]))
                self.assertIsNone(answer["translation"])
                self.assertEqual(len(answer["alternatives"]), 2)
        segments = build_lexical_contract(rag.lookup("truth blood", "en-to-fix"))["segments"]
        self.assertEqual([candidate_texts(segment) for segment in segments], [["sinruits"], ["ChiDd"]])

    def test_partial_known_input_preserves_unknown_tokens_and_abstains(self):
        lookup = self.truth_rag().lookup("sinruits qzxv987", "fix-to-en")
        contract = build_lexical_contract(lookup)
        self.assertEqual(contract["scope"], "partial_lexical")
        answer = ground_generation(lookup, raw_answer("truth mystery", evidence_ids=["truth"]))
        self.assertIsNone(answer["translation"])
        self.assertEqual(answer["unknown_tokens"], [{"text": "qzxv987", "start": 9, "end": 16}])
        self.assertEqual(candidate_texts(answer["alternatives"][0]), ["truth"])

    def test_wordnet_evidence_alone_cannot_create_fixmarge_candidates(self):
        lookup = self.rag([]).lookup("cat", "en-to-fix")
        lookup["external_evidence"] = [{"entry": {"id": "wordnet-cat", "lemma": "cat", "language": "en",
                                                   "glosses": ["a feline"], "source": "wordnet"}}]
        lookup["external_status"] = {"available": True, "matched_entry_count": 1}
        contract = build_lexical_contract(lookup)
        self.assertEqual(contract["scope"], "no_lexical_evidence")
        self.assertEqual(contract["segments"], [])
        self.assertIsNone(contract["expected_translation"])
        answer = ground_generation(lookup, raw_answer("invented-cat"))
        self.assertIsNone(answer["translation"])

    def test_supplied_contract_cannot_override_recomputed_evidence(self):
        lookup = self.truth_rag().lookup("sinruits", "fix-to-en")
        lookup["lexical_contract"] = {"expected_translation": "injected", "scope": "single_lexical",
                                      "segments": [], "direction": "fix-to-ko"}
        answer = ground_generation(lookup, raw_answer("injected", evidence_ids=["forged"]))
        self.assertEqual(answer["translation"], "truth")
        self.assertEqual(answer["evidence_ids"], ["truth"])
        self.assertEqual(answer["grounding"]["target_language"], "en")
        self.assertEqual(candidate_texts(answer["alternatives"][0]), ["truth"])

    def test_malformed_or_wrongly_typed_model_output_is_handled(self):
        lookup = self.truth_rag().lookup("sinruits", "fix-to-en")
        for raw in ("not JSON", "[]", "null", '{"translation": 7}',
                    '{"translation": "truth", "unknown_tokens": "oops", "evidence_ids": "truth", "warnings": 7}'):
            with self.subTest(raw=raw):
                answer = ground_generation(lookup, raw)
                self.assert_answer_fields(answer)
                self.assertEqual(answer["translation"], "truth")
                self.assertEqual(answer["unknown_tokens"], [])
                self.assertEqual(answer["evidence_ids"], ["truth"])
                self.assertIsInstance(answer["warnings"], list)
                self.assertTrue(answer["grounding"]["issues"])

    def test_grounding_does_not_mutate_lookup_or_source_entries(self):
        lookup = self.truth_rag().lookup("sinruits", "fix-to-en")
        before = deepcopy(lookup)
        build_lexical_contract(lookup)
        ground_generation(lookup, raw_answer("真実", evidence_ids=["forged"], unknown_tokens=["sinruits"]))
        self.assertEqual(lookup, before)


if __name__ == "__main__":
    unittest.main()
