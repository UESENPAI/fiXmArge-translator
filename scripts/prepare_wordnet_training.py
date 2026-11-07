"""Prepare offline, source-derived English/Japanese WordNet adapter examples."""
from __future__ import annotations

import argparse
from collections import Counter
from contextlib import closing
import gzip
import hashlib
import heapq
import json
from pathlib import Path
import random
import shutil
import sqlite3
import tempfile
import unicodedata

ROOT = Path(__file__).resolve().parents[1]
SPLITS = ("train", "validation", "test")
SOURCE_LICENSES = {"wnja:1.1": "Japanese-WordNet + WordNet", "oewn:2025": "CC-BY-4.0 + WordNet"}
SOURCE_URLS = {
    "wnja:1.1": ["https://github.com/bond-lab/wnja/releases/download/v1.1/wnjpn.db.gz",
                 "https://bond-lab.github.io/wnja/eng/downloads.html"],
    "oewn:2025": ["https://en-word.net/static/english-wordnet-2025.xml.gz",
                  "https://raw.githubusercontent.com/globalwordnet/english-wordnet/2025-edition/LICENSE.md"],
}
CONTROL_TOKENS = ("<|im_start|>", "<|im_end|>", "<|endoftext|>", "<think>", "</think>")


def digest(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def unique(values):
    return list(dict.fromkeys(value for value in values if isinstance(value, str) and value.strip()))


def partition(group_id, seed):
    value = int(hashlib.sha256(f"{seed}|partition|{group_id}".encode()).hexdigest()[:8], 16) % 10000
    return "train" if value < 8000 else "validation" if value < 9000 else "test"


def rank(group_id, seed):
    return int(hashlib.sha256(f"{seed}|selection|{group_id}".encode()).hexdigest(), 16)


def metadata(group_id, source, task, direction, source_language, target_language, lexical_terms):
    return {"group_id": group_id, "source": source, "status": "source_dictionary_derived",
            "task": task, "direction": direction, "source_language": source_language,
            "target_language": target_language, "rights_status": "open_license",
            "license": SOURCE_LICENSES[source], "source_urls": SOURCE_URLS[source],
            "lexical_terms": lexical_terms, "synthetic": False,
            "instruction_template_authored": True, "model_generated_translation": False,
            "evaluation_scope": "Dictionary lexical senses/definitions; not sentence-translation gold."}


def row(user, answer, meta):
    if any(token in user or token in answer for token in CONTROL_TOKENS):
        raise ValueError("control_tokens")
    return {"messages": [{"role": "user", "content": user}, {"role": "assistant", "content": answer}],
            "metadata": meta}


def check_schema(connection):
    required = {"word": {"wordid", "lang", "lemma", "pos"}, "sense": {"synset", "wordid"},
                "synset": {"synset", "pos"}, "synset_def": {"synset", "lang", "def"}}
    observed = {}
    for table, columns in required.items():
        actual = [value[1] for value in connection.execute(f"PRAGMA table_info({table})")]
        if not columns.issubset(actual):
            raise ValueError(f"Unsupported JWN table schema: {table}")
        observed[table] = actual
    return observed


def jwn_examples(connection, synset, *, max_definition_chars=160, max_candidates=12, max_answer_chars=180):
    values = connection.execute(
        "SELECT DISTINCT w.lang,w.lemma FROM sense s JOIN word w ON w.wordid=s.wordid "
        "WHERE s.synset=? AND w.lang IN ('eng','jpn') ORDER BY w.lang,w.lemma", (synset,)).fetchall()
    terms = {"en": unique(value for lang, value in values if lang == "eng"),
             "ja": unique(value for lang, value in values if lang == "jpn")}
    definitions = {"en": [], "ja": []}
    for language, definition in connection.execute(
            'SELECT lang,def FROM synset_def WHERE synset=? ORDER BY lang,sid,def', (synset,)):
        key = {"eng": "en", "jpn": "ja"}.get(language)
        if key:
            definitions[key] = unique([*definitions[key], definition])
    if not all(terms.values()) or not all(definitions.values()):
        raise ValueError("missing_bilingual_terms_or_definitions")
    if any(len(values) > max_candidates for values in terms.values()):
        raise ValueError("too_many_complete_candidates")
    if any(len(" / ".join(values)) > max_answer_chars for values in terms.values()):
        raise ValueError("complete_candidate_answer_too_long")
    if any(len(value) > max_definition_chars for values in definitions.values() for value in values):
        raise ValueError("definition_too_long")
    if len("\n".join(definitions["ja"])) > max_definition_chars:
        raise ValueError("combined_japanese_definition_too_long")
    if any(len(value) > 80 for values in terms.values() for value in values):
        raise ValueError("lemma_too_long")
    pos = connection.execute("SELECT pos FROM synset WHERE synset=?", (synset,)).fetchone()[0]
    group_id = f"wnja:1.1:synset:{synset}"
    records = []
    for source, target in (("en", "ja"), ("ja", "en")):
        meta = metadata(group_id, "wnja:1.1", "wordnet_translation", f"{source}-to-{target}",
                        source, target, terms)
        meta.update({"synset_id": synset, "synset_namespace": "Princeton-WordNet-3.0",
                     "alternatives": terms[target], "source_lemma": terms[source][0],
                     "source_definition_context": definitions[source][0],
                     "transform": "Same original JWN/PWN3 synset; all target-language lemmas retained; no model translation."})
        user = (f"Translate this WordNet lexical sense from {source} to {target}. "
                "Return ALL listed-sense translation lemmas, separated by ' / '; preserve their spelling.\n"
                f"Source: Japanese WordNet 1.1; synset: {synset}; POS: {pos}\n"
                f"Lemma: {terms[source][0]}\nDefinition context: {definitions[source][0]}")
        records.append(row(user, " / ".join(terms[target]), meta))
    meta = metadata(group_id, "wnja:1.1", "wordnet_definition", "ja-definition", "ja", "ja", terms)
    meta.update({"synset_id": synset, "synset_namespace": "Princeton-WordNet-3.0",
                 "definitions": definitions["ja"], "source_lemma": terms["ja"][0],
                 "transform": "Verbatim original Japanese definitions for the specified JWN/PWN3 lexical sense."})
    records.append(row(f"Give the Japanese dictionary definition for this lexical sense.\n"
                       f"Source: Japanese WordNet 1.1; synset: {synset}; POS: {pos}\nLemma: {terms['ja'][0]}",
                       "\n".join(definitions["ja"]), meta))
    return records


def select_jwn(connection, quotas, seed=42, **limits):
    schema = check_schema(connection)
    universe = [value[0] for value in connection.execute("SELECT synset FROM synset ORDER BY synset")]
    candidates = {split: [] for split in SPLITS}
    for synset in universe:
        group = f"wnja:1.1:synset:{synset}"
        candidates[partition(group, seed)].append((rank(group, seed), synset))
    output = {split: [] for split in SPLITS}
    stats = {"source_synsets": len(universe), "examined_groups": Counter(), "dropped_groups": Counter(),
             "selected_groups": {}, "schema": schema}
    for split in SPLITS:
        selected = 0
        for _, synset in sorted(candidates[split]):
            if selected >= quotas[split]:
                break
            stats["examined_groups"][split] += 1
            try:
                records = jwn_examples(connection, synset, **limits)
            except ValueError as error:
                stats["dropped_groups"][str(error)] += 1
                continue
            output[split].extend(records)
            selected += 1
        if selected != quotas[split]:
            raise ValueError(f"Insufficient eligible JWN groups for {split}: {selected}/{quotas[split]}")
        stats["selected_groups"][split] = selected
    return output, stats


def oewn_example(record, max_definition_chars=160, max_candidates=12, max_answer_chars=180):
    if record.get("source") != "oewn:2025" or record.get("license") != SOURCE_LICENSES["oewn:2025"] or record.get("language") != "en":
        raise ValueError("unreviewed_source_or_license")
    terms = sorted(unique([record.get("lemma"), *record.get("synonyms", [])]))
    definitions = sorted(unique(record.get("glosses", [])))
    if not terms or not definitions:
        raise ValueError("empty_oewn_terms_or_definition")
    if len(terms) > max_candidates:
        raise ValueError("too_many_complete_candidates")
    if len("\n".join(definitions)) > max_definition_chars or any(len(value) > 80 for value in terms):
        raise ValueError("definition_or_lemma_too_long")
    signature = json.dumps({"terms": terms, "definitions": definitions, "pos": record.get("pos")},
                           ensure_ascii=False, sort_keys=True)
    group_id = "oewn:2025:definition-proxy:" + hashlib.sha256(signature.encode()).hexdigest()
    meta = metadata(group_id, "oewn:2025", "wordnet_definition", "en-definition", "en", "en", {"en": terms})
    meta.update({"source_record_id": record["id"], "source_lemma": terms[0], "definitions": definitions,
                 "grouping_basis": "Exact whole lemma/synonym set + definitions + POS proxy; normalized JSONL omits original synset IDs.",
                 "transform": "Verbatim OEWN2025 English definitions; no PWN3/OEWN cross-version alignment."})
    user = (f"Give the English dictionary definition for this lexical sense.\n"
            f"Source: Open English WordNet 2025; sense: {record['id']}; POS: {record.get('pos', '')}\n"
            f"Lemma: {terms[0]}")
    return group_id, row(user, "\n".join(definitions), meta)


def select_oewn(path, quotas, seed=42, **limits):
    heaps = {split: [] for split in SPLITS}
    seen = set()
    stats = {"source_rows": 0, "distinct_definition_proxy_groups": 0, "dropped_rows": Counter()}
    with Path(path).open(encoding="utf-8") as stream:
        for line in stream:
            if not line.strip():
                continue
            stats["source_rows"] += 1
            value = json.loads(line)
            try:
                group_id, record = oewn_example(value, **limits)
            except ValueError as error:
                stats["dropped_rows"][str(error)] += 1
                continue
            if group_id in seen:
                stats["dropped_rows"]["duplicate_definition_proxy_group"] += 1
                continue
            seen.add(group_id)
            split, priority = partition(group_id, seed), rank(group_id, seed)
            count = quotas[split]
            if not count:
                continue
            item = (-priority, group_id, record)
            if len(heaps[split]) < count:
                heapq.heappush(heaps[split], item)
            elif priority < -heaps[split][0][0]:
                heapq.heapreplace(heaps[split], item)
    stats["distinct_definition_proxy_groups"] = len(seen)
    output = {}
    for split in SPLITS:
        if len(heaps[split]) != quotas[split]:
            raise ValueError(f"Insufficient eligible OEWN groups for {split}")
        output[split] = [value[2] for value in sorted(heaps[split], key=lambda value: (-value[0], value[1]))]
    return output, stats


def split_audit(datasets):
    groups, terms, chats = {}, {}, {}
    for split, records in datasets.items():
        groups[split] = {record["metadata"]["group_id"] for record in records}
        terms[split] = {"en": set(), "ja": set()}
        chats[split] = {hashlib.sha256(json.dumps(record["messages"], sort_keys=True, ensure_ascii=False).encode()).hexdigest()
                        for record in records}
        for record in records:
            for language, values in record["metadata"]["lexical_terms"].items():
                terms[split][language].update(unicodedata.normalize("NFC", value).casefold() if language == "en"
                                               else unicodedata.normalize("NFC", value) for value in values)
    overlaps = {}
    for left, right in (("train", "validation"), ("train", "test"), ("validation", "test")):
        overlaps[f"{left}/{right}"] = {"group_ids": len(groups[left] & groups[right]),
                                      "identical_chats": len(chats[left] & chats[right]),
                                      "shared_english_lexical_terms": len(terms[left]["en"] & terms[right]["en"]),
                                      "shared_japanese_lexical_terms": len(terms[left]["ja"] & terms[right]["ja"])}
        if overlaps[f"{left}/{right}"]["group_ids"] or overlaps[f"{left}/{right}"]["identical_chats"]:
            raise ValueError("Group or identical-chat leakage between dataset splits")
    return {"pairwise": overlaps, "limitation": "Group separation is not lemma-disjoint: polysemy, synonyms, and cross-resource lexical overlap can remain."}


def verify_sources(external, lock_path=None):
    external = Path(external)
    lock_path = lock_path or ROOT / "configs/external-sources.lock.json"
    lock = json.loads(Path(lock_path).read_text(encoding="utf-8"))
    manifests = {name: json.loads((external / f"{name}.manifest.json").read_text(encoding="utf-8"))
                 for name in ("wnja", "oewn")}
    paths = {"wnja_raw": external / "raw/wnjpn.db.gz",
             "oewn_raw": external / "raw/english-wordnet-2025.xml.gz",
             "oewn_normalized": external / "oewn-2025.jsonl"}
    hashes = {name: {"path": str(path.resolve()), "sha256": digest(path), "bytes": path.stat().st_size}
              for name, path in paths.items()}
    for name, key in (("wnja", "wnja_raw"), ("oewn", "oewn_raw")):
        if hashes[key]["sha256"] != lock["sources"][name]["sha256"]:
            raise ValueError(f"Original source hash mismatch: {name}")
    if hashes["oewn_normalized"]["sha256"] != manifests["oewn"]["output_sha256"]:
        raise ValueError("OEWN normalized JSONL hash mismatch")
    notices = {}
    for filename, value in lock["license_notices"].items():
        path = external / "licenses" / filename
        if digest(path) != value["sha256"]:
            raise ValueError(f"License notice hash mismatch: {filename}")
        notices[filename] = {"source_url": value["source_url"], "sha256": value["sha256"],
                             "bytes": path.stat().st_size}
    return {"source_files": hashes, "source_manifests": manifests,
            "source_manifest_hashes": {name: digest(external / f"{name}.manifest.json") for name in manifests},
            "source_lock_sha256": digest(lock_path), "license_notices": notices}


def prepare(external, output, counts=None, seed=42, **limits):
    external, output = Path(external).resolve(), Path(output).resolve()
    counts = counts or {"train": 4096, "validation": 256, "test": 256}
    if set(counts) != set(SPLITS) or any(not isinstance(value, int) or value < 4 for value in counts.values()):
        raise ValueError("Each split needs at least four requested records")
    if output == external or output in external.parents or external in output.parents:
        raise ValueError("Output overlaps original source directory")
    if output.exists():
        raise ValueError("Use a new output directory; existing data is never overwritten")
    provenance = verify_sources(external)
    quotas = {split: counts[split] // 4 for split in SPLITS}
    with tempfile.TemporaryDirectory(prefix="fixmarge-wordnet-source-") as temporary:
        database = Path(temporary) / "wnjpn.db"
        size = 0
        with gzip.open(external / "raw/wnjpn.db.gz", "rb") as inp, database.open("wb") as out:
            while chunk := inp.read(1024 * 1024):
                size += len(chunk)
                if size > 1024 ** 3:
                    raise ValueError("JWN decompression exceeds 1GiB")
                out.write(chunk)
        with closing(sqlite3.connect(database.as_uri() + "?mode=ro", uri=True)) as connection:
            jwn, jwn_stats = select_jwn(connection, quotas, seed, **limits)
    oewn, oewn_stats = select_oewn(external / "oewn-2025.jsonl", quotas, seed, **limits)
    datasets = {}
    for number, split in enumerate(SPLITS):
        datasets[split] = jwn[split] + oewn[split]
        random.Random(seed + number).shuffle(datasets[split])
    audit = split_audit(datasets)
    manifest = {"schema_version": 1, "dataset": "wordnet-en-ja-v1", "seed": seed,
                "requested_records": counts, "actual_records": {key: len(value) for key, value in datasets.items()},
                "sampling": "Hash partition 80/10/10 and deterministic SHA256 rank across full source group populations; balanced four task/direction strata.",
                "grouping": {"JWN": "All original PWN3 synset members, both translation directions and Japanese definition share one split.",
                             "OEWN": "Exact definition/POS/full synonym-set proxy, not a recovered synset ID. No cross-version mapping."},
                "length_filter": {"max_definition_chars": limits.get("max_definition_chars", 160),
                                  "max_candidates": limits.get("max_candidates", 12),
                                  "max_complete_translation_answer_chars": limits.get("max_answer_chars", 180),
                                  "max_lemma_chars": 80, "tokenizer_length_verified": False,
                                  "note": "Character limits are conservative preparation filters; actual max_length=384 is checked by the training tokenizer."},
                "source_provenance": provenance, "selection_stats": {"JWN": jwn_stats, "OEWN": oewn_stats},
                "split_audit": audit, "training_performed": False, "model_generated_records": False,
                "contains_fixmarge_or_korean": False, "sentence_parallel_corpus": False,
                "transformation_notice": "Authored instruction wrappers around verbatim licensed dictionary definitions and same-JWN-synset lexical alternatives. No synthetic model translation or source-version synset alignment.",
                "credits": ["Japanese WordNet 1.1: NICT; Francis Bond; Takayuki Kuribayashi; Princeton University WordNet.",
                            "Open English WordNet 2025: Open English WordNet Team; underlying Princeton University WordNet."],
                "license_urls": {name: value["source"]["licenses"] for name, value in provenance["source_manifests"].items()},
                "task_counts": {split: dict(Counter(record["metadata"]["direction"] for record in records))
                                for split, records in datasets.items()},
                "target_language_counts": {split: dict(Counter(record["metadata"]["target_language"] for record in records))
                                           for split, records in datasets.items()}}
    output.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=f".{output.name}-", dir=output.parent))
    try:
        for split, records in datasets.items():
            path = staging / f"{split}.jsonl"
            with path.open("w", encoding="utf-8", newline="\n") as stream:
                for record in records:
                    stream.write(json.dumps(record, ensure_ascii=False) + "\n")
        (staging / "licenses").mkdir()
        for filename in provenance["license_notices"]:
            shutil.copyfile(external / "licenses" / filename, staging / "licenses" / filename)
        (staging / "NOTICE.txt").write_text(
            "\n".join(manifest["credits"]) + "\n\n" + manifest["transformation_notice"] +
            "\n\nRetain all accompanying license notices, source attribution and change notices when redistributing.\n",
            encoding="utf-8")
        manifest["output_files"] = {f"{split}.jsonl": {"sha256": digest(staging / f"{split}.jsonl"),
                                                       "bytes": (staging / f"{split}.jsonl").stat().st_size}
                                    for split in SPLITS}
        (staging / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        if output.exists():
            raise ValueError("Output appeared while preparing; refusing to overwrite")
        staging.rename(output)
    finally:
        if staging.exists():
            shutil.rmtree(staging)
    return manifest


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--external-dir", type=Path, default=ROOT / "data/external")
    parser.add_argument("--output", type=Path, default=ROOT / "data/training/wordnet-en-ja-v1")
    parser.add_argument("--train-rows", type=int, default=4096)
    parser.add_argument("--validation-rows", type=int, default=256)
    parser.add_argument("--test-rows", type=int, default=256)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--max-definition-chars", type=int, default=160)
    parser.add_argument("--max-candidates", type=int, default=12)
    parser.add_argument("--max-answer-chars", type=int, default=180)
    args = parser.parse_args(argv)
    if min(args.max_definition_chars, args.max_candidates, args.max_answer_chars) < 1:
        parser.error("Length/candidate limits must be positive")
    result = prepare(args.external_dir, args.output,
                     {"train": args.train_rows, "validation": args.validation_rows, "test": args.test_rows},
                     args.seed, max_definition_chars=args.max_definition_chars,
                     max_candidates=args.max_candidates, max_answer_chars=args.max_answer_chars)
    print(json.dumps({"output": str(args.output), "actual_records": result["actual_records"],
                      "task_counts": result["task_counts"], "target_language_counts": result["target_language_counts"],
                      "split_audit": result["split_audit"]}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, sqlite3.Error) as error:
        print(f"error: {error}")
        raise SystemExit(2)
