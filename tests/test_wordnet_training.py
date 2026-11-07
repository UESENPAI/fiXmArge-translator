"""Small synthetic SQLite/JSONL fixtures; no models or downloads."""
from collections import Counter
import gzip
import json
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts import prepare_wordnet_training as preparation
from scripts.train_qlora import validate_record, validate_split


def database(path=":memory:", count=200):
    connection = sqlite3.connect(path)
    connection.executescript(
        "CREATE TABLE word(wordid INTEGER,lang TEXT,lemma TEXT,pos TEXT);"
        "CREATE TABLE sense(synset TEXT,wordid INTEGER);"
        "CREATE TABLE synset(synset TEXT,pos TEXT);"
        'CREATE TABLE synset_def(synset TEXT,lang TEXT,def TEXT,sid TEXT);')
    for number in range(count):
        synset = f"{number:08d}-n"
        connection.execute("INSERT INTO synset VALUES(?,?)", (synset, "n"))
        for offset, (language, lemma) in enumerate([("eng", f"word{number}"), ("eng", f"term{number}"),
                                                  ("jpn", f"語{number}"), ("jpn", f"単語{number}")]):
            wordid = number * 4 + offset
            connection.execute("INSERT INTO word VALUES(?,?,?,?)", (wordid, language, lemma, "n"))
            connection.execute("INSERT INTO sense VALUES(?,?)", (synset, wordid))
        connection.executemany("INSERT INTO synset_def VALUES(?,?,?,?)",
                               [(synset, "eng", f"English definition {number}", "0"),
                                (synset, "jpn", f"日本語の定義{number}", "0")])
    connection.commit()
    return connection


def oewn(number, lemma=None):
    return {"id": f"oewn:fixture-{number}", "lemma": lemma or f"word{number}",
            "synonyms": [f"term{number}"] if lemma is None else [],
            "glosses": [f"English source definition {number}"], "pos": "n",
            "language": "en", "source": "oewn:2025", "license": "CC-BY-4.0 + WordNet"}


class WordNetTrainingTests(unittest.TestCase):
    def test_jwn_keeps_all_candidates_and_reverse_in_the_same_synset_group(self):
        connection = database(count=1)
        self.addCleanup(connection.close)
        records = preparation.jwn_examples(connection, "00000000-n")
        self.assertEqual(len(records), 3)
        self.assertEqual(len({record["metadata"]["group_id"] for record in records}), 1)
        forward = next(record for record in records if record["metadata"]["direction"] == "en-to-ja")
        reverse = next(record for record in records if record["metadata"]["direction"] == "ja-to-en")
        self.assertEqual(set(forward["metadata"]["alternatives"]), {"語0", "単語0"})
        self.assertEqual(set(reverse["metadata"]["alternatives"]), {"word0", "term0"})
        self.assertIn("POS: n", forward["messages"][0]["content"])
        self.assertIn("Definition context: English definition 0", forward["messages"][0]["content"])
        self.assertEqual(forward["messages"][-1]["content"].split(" / "), forward["metadata"]["alternatives"])
        for record in records:
            validate_record(record)
            self.assertEqual(record["metadata"]["rights_status"], "open_license")
            self.assertFalse(record["metadata"]["model_generated_translation"])

    def test_whole_synset_sampling_is_deterministic_and_split_disjoint(self):
        connection = database()
        self.addCleanup(connection.close)
        quotas = {"train": 2, "validation": 1, "test": 1}
        first, _ = preparation.select_jwn(connection, quotas, seed=42)
        second, _ = preparation.select_jwn(connection, quotas, seed=42)
        self.assertEqual(first, second)
        audit = preparation.split_audit(first)
        self.assertTrue(all(value["group_ids"] == 0 for value in audit["pairwise"].values()))
        for split, rows in first.items():
            self.assertEqual(len(rows), quotas[split] * 3)
            directions = Counter(row["metadata"]["direction"] for row in rows)
            self.assertEqual(directions["en-to-ja"], quotas[split])
            self.assertEqual(directions["ja-to-en"], quotas[split])

    def test_overlong_definitions_or_complete_candidate_sets_are_dropped(self):
        connection = database(count=1)
        self.addCleanup(connection.close)
        with self.assertRaisesRegex(ValueError, "too_many_complete_candidates"):
            preparation.jwn_examples(connection, "00000000-n", max_candidates=1)
        with self.assertRaisesRegex(ValueError, "definition_too_long"):
            preparation.jwn_examples(connection, "00000000-n", max_definition_chars=3)
        with self.assertRaisesRegex(ValueError, "complete_candidate_answer_too_long"):
            preparation.jwn_examples(connection, "00000000-n", max_answer_chars=2)

    def test_oewn_exact_signature_groups_synonyms_without_claiming_synset_alignment(self):
        first = oewn(1)
        second = {**first, "id": "oewn:other", "lemma": first["synonyms"][0], "synonyms": [first["lemma"]]}
        group_a, record_a = preparation.oewn_example(first)
        group_b, _ = preparation.oewn_example(second)
        self.assertEqual(group_a, group_b)
        self.assertNotIn("synset_id", record_a["metadata"])
        self.assertIn("proxy", record_a["metadata"]["grouping_basis"])
        self.assertEqual(record_a["messages"][-1]["content"], "English source definition 1")
        with self.assertRaisesRegex(ValueError, "unreviewed_source_or_license"):
            preparation.oewn_example({**first, "source": "fan_fixture", "license": "unknown"})

    def test_oewn_full_stream_hash_sampling_and_duplicate_group_elimination(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "oewn.jsonl"
            records = [oewn(number) for number in range(200)]
            records.append(records[0])
            path.write_text("".join(json.dumps(record) + "\n" for record in records), encoding="utf-8")
            result, stats = preparation.select_oewn(path, {"train": 2, "validation": 1, "test": 1})
            self.assertEqual(stats["source_rows"], 201)
            self.assertEqual(stats["dropped_rows"]["duplicate_definition_proxy_group"], 1)
            self.assertEqual({key: len(value) for key, value in result.items()},
                             {"train": 2, "validation": 1, "test": 1})
            self.assertTrue(all(value["group_ids"] == 0 for value in preparation.split_audit(result)["pairwise"].values()))

    def test_prepare_balances_languages_copies_notices_and_never_overwrites(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            external = root / "external"
            (external / "raw").mkdir(parents=True)
            (external / "licenses").mkdir()
            raw = root / "fixture.sqlite3"
            connection = database(raw)
            connection.close()
            with raw.open("rb") as inp, gzip.open(external / "raw/wnjpn.db.gz", "wb") as out:
                out.write(inp.read())
            (external / "oewn-2025.jsonl").write_text(
                "".join(json.dumps(oewn(number)) + "\n" for number in range(200)), encoding="utf-8")
            for filename in ["Japanese-WordNet.txt", "Princeton-WordNet.txt", "Open-English-WordNet.md", "OEWN-WNDB-License.txt"]:
                (external / "licenses" / filename).write_text("fixture full license notice", encoding="utf-8")
            provenance = {"source_manifests": {name: {"source": {"licenses": {"fixture": "https://example.invalid/license"}}}
                                               for name in ("wnja", "oewn")},
                          "license_notices": {p.name: {"sha256": preparation.digest(p)}
                                              for p in (external / "licenses").iterdir()}}
            output = root / "prepared"
            with patch.object(preparation, "verify_sources", return_value=provenance):
                manifest = preparation.prepare(external, output, {"train": 8, "validation": 4, "test": 4})
            self.assertEqual(manifest["actual_records"], {"train": 8, "validation": 4, "test": 4})
            self.assertEqual(manifest["target_language_counts"]["train"], {"en": 4, "ja": 4})
            loaded = {}
            for split in preparation.SPLITS:
                loaded[split] = [json.loads(line) for line in (output / f"{split}.jsonl").read_text().splitlines()]
                for record in loaded[split]:
                    validate_record(record)
                self.assertEqual(preparation.digest(output / f"{split}.jsonl"),
                                 manifest["output_files"][f"{split}.jsonl"]["sha256"])
            validate_split(loaded["train"], loaded["validation"])
            self.assertTrue((output / "NOTICE.txt").is_file())
            self.assertEqual(len(list((output / "licenses").iterdir())), 4)
            self.assertFalse(manifest["training_performed"])
            self.assertFalse(manifest["contains_fixmarge_or_korean"])
            with self.assertRaisesRegex(ValueError, "never overwritten"):
                preparation.prepare(external, output, {"train": 8, "validation": 4, "test": 4})

    def test_source_hash_mismatch_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "raw").mkdir()
            for filename in ["wnjpn.db.gz", "english-wordnet-2025.xml.gz"]:
                (root / "raw" / filename).write_bytes(b"fixture source")
            (root / "oewn-2025.jsonl").write_bytes(b"fixture normalized")
            for source in ("wnja", "oewn"):
                (root / f"{source}.manifest.json").write_text(
                    json.dumps({"output_sha256": preparation.digest(root / "oewn-2025.jsonl")}), encoding="utf-8")
            lock = root / "lock.json"
            lock.write_text(json.dumps({"sources": {"wnja": {"sha256": "mismatch"},
                                                   "oewn": {"sha256": preparation.digest(root / "raw/english-wordnet-2025.xml.gz")}},
                                       "license_notices": {}}), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Original source hash mismatch"):
                preparation.verify_sources(root, lock)


if __name__ == "__main__":
    unittest.main()
