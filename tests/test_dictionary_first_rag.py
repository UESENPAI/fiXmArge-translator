"""Dictionary-first retrieval regressions use local fixtures, without a model."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sqlite3
import tempfile
import unicodedata
import unittest
from unittest.mock import Mock

from fixmarge.demo import DemoService, present_result
from fixmarge.rag import LexiconRAG
from fixmarge.standard_dictionary import lookup_standard_dictionary


def standard_entry(identifier, lemma, *, synonyms=(), language="en"):
    return {
        "id": identifier, "lemma": lemma, "language": language,
        "synonyms": list(synonyms), "glosses": ["fixture definition"],
        "source": "oewn:2025" if language == "en" else "wnja:1.1",
        "license": "CC-BY-4.0 + WordNet" if language == "en" else "Japanese-WordNet + WordNet",
    }


def domain_entry(identifier, form, *, en=(), ja=(), etymology=()):
    return {
        "id": identifier, "form": form, "aliases": [],
        "senses": {"en": list(en), "ja": list(ja), "ko": []},
        "sources": ["fixture"], "status": "unreviewed",
        "rights_status": "game_derived_not_eligible", "has_conflict": False,
        "etymology": list(etymology),
    }


class DictionaryFirstRagTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.directory = Path(temporary.name)
        self.database = self.directory / "lexicons.sqlite3"
        with sqlite3.connect(self.database) as connection:
            connection.executescript(
                "CREATE TABLE entries(id TEXT PRIMARY KEY, language TEXT, payload TEXT);"
                "CREATE TABLE terms(key TEXT, entry_id TEXT); CREATE INDEX terms_key ON terms(key);"
            )
        self.add(standard_entry("currency", "riel"))
        self.add(standard_entry("negative", "no"))
        self.add(standard_entry("no-more", "no more", synonyms=["no"]))
        self.add(standard_entry("chemical-symbol", "No"))
        self.add(standard_entry("chemical-name", "nobelium", synonyms=["No"]))
        self.add(standard_entry("return-ja", "帰る", language="ja"))

    def add(self, record):
        with sqlite3.connect(self.database) as connection:
            connection.execute("INSERT INTO entries VALUES(?,?,?)", (
                record["id"], record["language"], json.dumps(record, ensure_ascii=False)))
            for term in dict.fromkeys([record["lemma"], *record["synonyms"]]):
                key = unicodedata.normalize("NFC", term.strip())
                if record["language"] == "en":
                    key = key.casefold()
                connection.execute("INSERT INTO terms VALUES(?,?)", (key, record["id"]))

    def lookup(self, text, **options):
        return lookup_standard_dictionary(text, self.directory, limit_per_language=24, **options)

    @staticmethod
    def ids(result):
        return {record["entry"]["id"] for record in result["entries"]}

    def test_gloss_only_lookup_does_not_query_the_fix_source_or_its_tokens(self):
        result = self.lookup(
            "riEl Nii", include_input=False,
            extra_queries=[("帰る", "fiXmArge_gloss:return:ja"), ("no", "fiXmArge_gloss:negative:en")])
        self.assertEqual(self.ids(result), {"return-ja", "negative", "no-more"})
        self.assertEqual({record["query"] for record in result["queries"]}, {"帰る", "no"})
        self.assertTrue(all(reason.startswith("fiXmArge_gloss:")
                            for record in result["queries"] for reason in record["reasons"]))

    def test_unknown_fix_source_cannot_create_wordnet_evidence_without_a_gloss(self):
        result = self.lookup("riEl", include_input=False)
        self.assertTrue(result["available"])
        self.assertEqual(result["queries"], [])
        self.assertEqual(result["entries"], [])

    def test_exact_lowercase_gloss_preserves_synonyms_and_excludes_chemical_symbols(self):
        result = self.lookup("", include_input=False, extra_queries=[("no", "fiXmArge_gloss:negative:en")])
        self.assertEqual(self.ids(result), {"negative", "no-more"})
        self.assertEqual({record["matches"][0]["query"] for record in result["entries"]}, {"no"})

    def test_actual_capitalized_chemical_symbol_remains_available(self):
        self.assertTrue({"chemical-symbol", "chemical-name"}.issubset(self.ids(self.lookup("No"))))
        # A capitalized sentence-initial No can also be ordinary negation.
        self.assertIn("negative", self.ids(self.lookup("No")))

    def test_casefold_fallback_survives_when_no_exact_spelling_exists(self):
        self.add(standard_entry("cat", "cat"))
        self.add(standard_entry("street", "Straße"))
        for text, expected in [("CAT", "cat"), ("STRASSE", "street")]:
            with self.subTest(text=text):
                self.assertEqual(self.ids(self.lookup(text)), {expected})

    def test_unambiguous_synonym_fallback_survives(self):
        self.add(standard_entry("feline", "cat", synonyms=["feline"]))
        self.assertEqual(self.ids(self.lookup("feline")), {"feline"})

    def test_rag_external_context_uses_glosses_without_treating_fix_form_as_english(self):
        entries = [domain_entry("return", "riEl", ja=["帰る"]),
                   domain_entry("negative", "Nii", en=["no"])]
        before = deepcopy(entries)
        rag = LexiconRAG(entries=entries, rules=[], external_dir=self.directory)
        result = rag.lookup("riEl Nii", "fix-to-en")
        self.assertEqual({record["entry"]["id"] for record in result["external_evidence"]},
                         {"return-ja", "negative", "no-more"})
        self.assertEqual(result["text"], "riEl Nii")
        self.assertEqual(entries, before)
        self.assertEqual(result["unknown_tokens"], [])
        self.assertEqual(result["rules"], [])

    def test_natural_input_retains_independent_wordnet_lookup(self):
        rag = LexiconRAG(entries=[], rules=[], external_dir=self.directory)
        result = rag.lookup("riel", "en-to-fix")
        self.assertEqual({record["entry"]["id"] for record in result["external_evidence"]}, {"currency"})

    def test_demo_prompt_retrieval_is_dictionary_first_and_keeps_grammar_unverified(self):
        entries = [domain_entry("return", "riEl", ja=["帰る"]),
                   domain_entry("negative", "Nii", en=["no"])]
        before = deepcopy(entries)
        original_database_hash = hashlib.sha256(self.database.read_bytes()).hexdigest()
        runner_factory = Mock(side_effect=AssertionError("Dry run must not load a model"))
        rag = LexiconRAG(entries=entries, rules=[], external_dir=self.directory)
        service = DemoService(external_dir=self.directory, runner_factory=runner_factory,
                              rag_factory=Mock(return_value=rag))
        result = service.run("riEl Nii", "fix", "ja", generate=False)
        self.assertEqual(self.ids(result["standard_dictionary"]), {"return-ja", "negative", "no-more"})
        queries = result["standard_dictionary"]["queries"]
        self.assertEqual({record["query"] for record in queries}, {"帰る", "no"})
        self.assertEqual(result["source_text"], "riEl Nii")
        self.assertFalse(result["sentence_verified"])
        self.assertFalse(result["source_evidence"]["grammar"]["sentence_grammar_verified"])
        self.assertFalse(result["model_loaded"])
        self.assertFalse(result["training_performed"])
        self.assertEqual(entries, before)
        self.assertEqual(hashlib.sha256(self.database.read_bytes()).hexdigest(), original_database_hash)
        runner_factory.assert_not_called()

    def test_dictionary_answer_uses_all_direct_alternatives_without_loading_model(self):
        entries = [domain_entry("first", "firstForm", en=["no"]),
                   domain_entry("second", "secondForm", en=["no"])]
        rag = LexiconRAG(entries=entries, rules=[], external_dir=self.directory)
        runner_factory = Mock(side_effect=AssertionError("Direct dictionary answer must not load a model"))
        service = DemoService(external_dir=self.directory, runner_factory=runner_factory,
                              rag_factory=Mock(return_value=rag))
        result = service.run("no", "en", "fix", generate=True)
        self.assertEqual(result["answer_source"], "dictionary")
        self.assertEqual(result["dictionary_answer"]["translation"], "firstForm / secondForm")
        self.assertEqual(set(result["dictionary_answer"]["evidence_ids"]), {"first", "second"})
        self.assertEqual(result["dictionary_answer"]["scope"], "single_lexical")
        self.assertFalse(result["dictionary_answer"]["sentence_verified"])
        self.assertFalse(result["generation_performed"])
        self.assertFalse(result["model_loaded"])
        runner_factory.assert_not_called()

    def test_unrelated_wordnet_evidence_cannot_generate_new_fix_vocabulary(self):
        rag = LexiconRAG(entries=[], rules=[], external_dir=self.directory)
        runner_factory = Mock(side_effect=AssertionError("No fiXmArge evidence must abstain"))
        service = DemoService(external_dir=self.directory, runner_factory=runner_factory,
                              rag_factory=Mock(return_value=rag))
        result = service.run("riel", "en", "fix", generate=True)
        self.assertEqual(self.ids(result["standard_dictionary"]), {"currency"})
        self.assertEqual(result["answer_source"], "abstained")
        self.assertEqual(result["abstention_reason"], "no_fiXmArge_dictionary_evidence")
        self.assertFalse(result["generation_performed"])
        self.assertFalse(result["sentence_verified"])
        runner_factory.assert_not_called()

    def test_unknown_fix_input_abstains_without_loading_model(self):
        rag = LexiconRAG(entries=[], rules=[], external_dir=self.directory)
        runner_factory = Mock(side_effect=AssertionError("Unknown fiXmArge input must abstain"))
        service = DemoService(external_dir=self.directory, runner_factory=runner_factory,
                              rag_factory=Mock(return_value=rag))
        result = service.run("riEl", "fix", "en", generate=True)
        self.assertEqual(result["answer_source"], "abstained")
        self.assertEqual(result["abstention_reason"], "no_fiXmArge_dictionary_evidence")
        self.assertEqual(result["standard_dictionary"]["entries"], [])
        self.assertFalse(result["generation_performed"])
        runner_factory.assert_not_called()

    def test_missing_target_gloss_still_allows_a_tentative_language_bridge(self):
        rag = LexiconRAG(entries=[domain_entry("return", "riEl", ja=["帰る"])],
                         rules=[], external_dir=self.directory)
        raw = json.dumps({"glosses": [{"entry_id": "return", "korean": ["돌아가다"]}]}, ensure_ascii=False)
        runner = Mock()
        runner.generate.return_value = raw
        runner_factory = Mock(return_value=runner)
        service = DemoService(external_dir=self.directory, runner_factory=runner_factory,
                              rag_factory=Mock(return_value=rag))
        result = service.run("riEl", "fix", "ko", generate=True)
        self.assertEqual(result["answer_source"], "model_with_dictionary")
        self.assertTrue(result["generation_performed"])
        self.assertEqual(result["source_evidence"]["korean_lexical_bridge"]["raw_output"], raw)
        self.assertEqual(result["korean_bridge_answer"]["translation"], "돌아가다")
        self.assertNotIn("dictionary_answer", result)
        self.assertFalse(result["sentence_verified"])
        runner_factory.assert_called_once()
        runner.generate.assert_called_once()

    def test_research_opt_out_generates_even_for_a_direct_dictionary_answer(self):
        rag = LexiconRAG(entries=[domain_entry("negative", "Nii", en=["no"])],
                         rules=[], external_dir=self.directory)
        raw = json.dumps({"tentative_translation": "no", "evidence_ids": ["negative"],
                          "uncertainties": []})
        runner = Mock()
        runner.generate.return_value = raw
        runner_factory = Mock(return_value=runner)
        service = DemoService(external_dir=self.directory, runner_factory=runner_factory,
                              rag_factory=Mock(return_value=rag), dictionary_first=False)
        result = service.run("Nii", "fix", "en", generate=True)
        self.assertEqual(result["answer_source"], "model_with_dictionary")
        self.assertTrue(result["generation_performed"])
        self.assertEqual(result["diagnostic"]["raw_output"], raw)
        runner.generate.assert_called_once()

    def test_source_claims_are_exposed_without_resolution_and_case_collisions_stay_tentative(self):
        conflicted = domain_entry("conflict", "riEl", ja=["帰る"])
        conflicted["has_conflict"] = True
        scenarios = [
            ("source_conflict", [conflicted], "riEl"),
            ("case_collision", [domain_entry("upper", "Alpha", ja=["一"]),
                                domain_entry("lower", "alpha", ja=["二"])], "ALPHA"),
        ]
        for name, entries, text in scenarios:
            with self.subTest(scenario=name):
                rag = LexiconRAG(entries=entries, rules=[], external_dir=self.directory)
                raw = json.dumps({"tentative_translation": None,
                                  "evidence_ids": [entry["id"] for entry in entries],
                                  "uncertainties": ["Unresolved dictionary alternatives."]})
                runner = Mock()
                runner.generate.return_value = raw
                runner_factory = Mock(return_value=runner)
                service = DemoService(external_dir=self.directory, runner_factory=runner_factory,
                                      rag_factory=Mock(return_value=rag))
                result = service.run(text, "fix", "ja", generate=True)
                self.assertNotIn("dictionary_answer", result)
                self.assertFalse(result["sentence_verified"])
                if name == 'source_conflict':
                    self.assertEqual(result['answer_source'], 'dictionary_claims')
                    self.assertFalse(result['dictionary_claims_answer']['conflicts_resolved'])
                    self.assertFalse(result['generation_performed'])
                    runner.generate.assert_not_called()
                else:
                    self.assertEqual(result['answer_source'], 'model_with_dictionary')
                    self.assertTrue(result['generation_performed'])
                    self.assertEqual(result['diagnostic']['raw_output'], raw)
                    runner.generate.assert_called_once()

    def test_full_multiword_entries_answer_directly_on_all_six_routes_but_separate_spans_do_not(self):
        lexical = domain_entry("eleven", "tone wachi", en=["number eleven"], ja=["数 十一"])
        lexical["senses"]["ko"] = ["숫자 열하나"]
        phrases = {"fix": "tone wachi", "en": "number eleven", "ja": "数 十一", "ko": "숫자 열하나"}
        routes = [("fix", "en"), ("en", "fix"), ("fix", "ja"),
                  ("ja", "fix"), ("fix", "ko"), ("ko", "fix")]
        for source, target in routes:
            with self.subTest(source=source, target=target):
                rag = LexiconRAG(entries=[lexical], rules=[], external_dir=self.directory)
                runner_factory = Mock(side_effect=AssertionError("Full lexical entry must answer without model"))
                service = DemoService(external_dir=self.directory, runner_factory=runner_factory,
                                      rag_factory=Mock(return_value=rag))
                result = service.run(phrases[source], source, target, generate=True)
                self.assertEqual(result["answer_source"], "dictionary")
                self.assertEqual(result["dictionary_answer"]["translation"], phrases[target])
                self.assertEqual(result["dictionary_answer"]["scope"], "single_lexical")
                self.assertFalse(result["generation_performed"])
                self.assertFalse(result["model_loaded"])
                presentation = present_result(result)
                self.assertEqual(presentation[0], phrases[target])
                status = json.JSONDecoder().raw_decode(presentation[3])[0]
                self.assertEqual(status["answer_source"], "dictionary")
                runner_factory.assert_not_called()
        rag = LexiconRAG(entries=[domain_entry("one", "first", en=["one"]),
                                 domain_entry("two", "second", en=["two"])],
                         rules=[], external_dir=self.directory)
        raw = json.dumps({"tentative_translation": "one two", "evidence_ids": ["one", "two"],
                          "uncertainties": ["Word order remains a hypothesis."]})
        runner = Mock()
        runner.generate.return_value = raw
        runner_factory = Mock(return_value=runner)
        service = DemoService(external_dir=self.directory, runner_factory=runner_factory,
                              rag_factory=Mock(return_value=rag))
        result = service.run("first second", "fix", "en", generate=True)
        self.assertEqual(result["answer_source"], "model_with_dictionary")
        self.assertTrue(result["generation_performed"])
        self.assertNotIn("dictionary_answer", result)
        self.assertFalse(result["sentence_verified"])
        self.assertEqual(result["diagnostic"]["raw_output"], raw)
        runner.generate.assert_called_once()


if __name__ == "__main__":
    unittest.main()
