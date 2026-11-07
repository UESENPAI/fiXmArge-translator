"""Independent standard-dictionary lookups use only fixture SQLite indexes."""
from pathlib import Path
import json
import sqlite3
import tempfile
import unicodedata
import unittest

from fixmarge.standard_dictionary import lookup_standard_dictionary


def entry(identifier, lemma, language="en", source=None, license=None):
    source = source or ("wnja:1.1" if language == "ja" else "oewn:2025")
    license = license or ("Japanese-WordNet + WordNet" if source == "wnja:1.1" else "CC-BY-4.0 + WordNet")
    return {"id": identifier, "lemma": lemma, "language": language, "reading": None,
            "synonyms": [], "glosses": ["fixture definition"], "source": source, "license": license}


class StandardDictionaryTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.directory = Path(directory.name)
        self.database = self.directory / "lexicons.sqlite3"
        with sqlite3.connect(self.database) as connection:
            connection.executescript("CREATE TABLE entries(id TEXT PRIMARY KEY,language TEXT,payload TEXT);"
                                     "CREATE TABLE terms(key TEXT,entry_id TEXT); CREATE INDEX terms_key ON terms(key);")

    def add(self, record, keys=None):
        if keys is None:
            keys = [record["lemma"]]
        with sqlite3.connect(self.database) as connection:
            connection.execute("INSERT INTO entries VALUES(?,?,?)",
                               (record["id"], record["language"], json.dumps(record, ensure_ascii=False)))
            for value in keys:
                key = unicodedata.normalize("NFC", value.strip())
                if record["language"] == "en":
                    key = key.casefold()
                connection.execute("INSERT INTO terms VALUES(?,?)", (key, record["id"]))

    def lookup(self, text, **options):
        return lookup_standard_dictionary(text, self.directory, **options)

    def test_exact_lemma_priority_unicode_casefold_and_synonym_fallback(self):
        for number, (language, lemma, query) in enumerate([("en", "cat", "CAT"),
                                                         ("en", "Straße", "STRASSE"),
                                                         ("ja", "猫", "猫")]):
            with self.subTest(language=language, query=query):
                prefix = str(number)
                for suffix, candidate in [("a-synonym", "other-a"), ("b-synonym", "other-b"),
                                          ("c-synonym", "other-c"), ("z-exact-2", lemma),
                                          ("z-exact-1", lemma)]:
                    keys = [lemma] + ([f"fallback{number}"] if "synonym" in suffix else [])
                    self.add(entry(prefix + suffix, candidate, language), keys)
                result = self.lookup(query)
                self.assertEqual([item["entry"]["id"] for item in result["entries"]],
                                 [prefix + "z-exact-1", prefix + "z-exact-2", prefix + "a-synonym"])
                fallback = self.lookup(f"fallback{number}")
                self.assertEqual([item["entry"]["id"] for item in fallback["entries"]],
                                 [prefix + "a-synonym", prefix + "b-synonym", prefix + "c-synonym"])

    def test_english_sentence_tokens_and_bounded_japanese_script_runs(self):
        self.add(entry("truth", "truth"))
        self.add(entry("ja-truth", "真実", "ja"))
        english = self.lookup("I want to know the truth.")
        japanese = self.lookup("私は真実を知りたい。")
        self.assertEqual([item["entry"]["id"] for item in english["entries"]], ["truth"])
        self.assertEqual([item["entry"]["id"] for item in japanese["entries"]], ["ja-truth"])
        self.assertIn("真実", [item["query"] for item in japanese["queries"]])
        self.assertFalse(japanese["segmentation_verified"])
        self.assertTrue(japanese["limitations"])

    def test_decomposed_accents_and_kana_remain_lookup_candidates_in_sentences(self):
        self.add(entry("cafe", "café"))
        self.add(entry("glass", "ガラス", "ja"))
        self.assertEqual([item["entry"]["id"] for item in self.lookup("A cafe\u0301 opens.")["entries"]], ["cafe"])
        self.assertEqual([item["entry"]["id"] for item in self.lookup("私はカ\u3099ラスを見た。")["entries"]], ["glass"])

    def test_unverified_sources_and_mismatched_licenses_are_excluded_before_limit(self):
        self.add(entry("a-unknown", "truth", source="fixture", license="fixture"))
        self.add(entry("b-new-version", "truth", source="wnja:2.1", license="Japanese-WordNet + WordNet"))
        self.add(entry("c-bad-license", "truth", license="unverified"))
        self.add(entry("d-korean", "truth", language="ko", source="oewn:2025"))
        self.add(entry("z-reviewed", "truth"))
        result = self.lookup("truth")
        self.assertEqual([item["entry"]["id"] for item in result["entries"]], ["z-reviewed"])
        self.assertEqual(result["entries"][0]["entry"]["source"], "oewn:2025")
        self.assertEqual(result["entries"][0]["entry"]["license"], "CC-BY-4.0 + WordNet")
        self.assertEqual([item["source"] for item in result["attributions"]], ["oewn:2025"])

    def test_extra_etymology_queries_preserve_reasons_and_deduplicate(self):
        self.add(entry("devil", "devil"))
        self.add(entry("ja-devil", "悪魔", "ja"))
        result = self.lookup("devil", extra_queries=[("悪魔", "etymology:one"), ("devil", "etymology:two")])
        records = {item["entry"]["id"]: item for item in result["entries"]}
        self.assertEqual(set(records), {"devil", "ja-devil"})
        self.assertEqual(records["ja-devil"]["matches"][0]["reasons"], ["etymology:one"])
        self.assertEqual(records["devil"]["matches"][0]["reasons"], ["etymology:two", "input"])
        self.assertEqual([item["query"] for item in result["queries"]].count("devil"), 1)

    def test_query_and_entry_limits_hold_for_long_input(self):
        for number in range(64):
            self.add(entry(f"entry-{number}", f"word{number}"))
        result = self.lookup(" ".join(f"word{number}" for number in range(64)))
        self.assertLessEqual(len(result["queries"]), 160)
        self.assertEqual(len(result["entries"]), 24)
        extra = self.lookup("truth", extra_queries=[(f"extra{number}", "fixture") for number in range(300)])
        self.assertEqual(len(extra["queries"]), 160)

    def test_language_selection_and_per_query_language_limit(self):
        for number in range(3):
            self.add(entry(f"cat-{number}", "cat"))
        result = self.lookup("cat", languages=("en",), limit_per_language=1)
        self.assertEqual([item["entry"]["id"] for item in result["entries"]], ["cat-0"])
        for languages in [("ko",), ("en", "ko"), ()]:
            with self.subTest(languages=languages), self.assertRaises(ValueError):
                self.lookup("cat", languages=languages)
        for limit in [0, -1, True, 25]:
            with self.subTest(limit=limit), self.assertRaises(ValueError):
                self.lookup("cat", limit_per_language=limit)

    def test_missing_index_is_unavailable_without_creating_files(self):
        absent = self.directory / "missing"
        result = lookup_standard_dictionary("truth", absent)
        self.assertFalse(result["available"])
        self.assertEqual(result["entries"], [])
        self.assertFalse(absent.exists())

    def test_invalid_index_is_a_readable_error(self):
        self.database.unlink()
        self.database.write_text("invalid SQLite data", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "Cannot read standard dictionary index"):
            self.lookup("truth")


if __name__ == "__main__":
    unittest.main()
