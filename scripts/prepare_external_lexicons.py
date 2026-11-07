#!/usr/bin/env python3
"""Fetch versioned WordNets and build sense-level JSONL (Python standard library)."""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import sqlite3
import sys
import tempfile
import unicodedata
import urllib.request
import urllib.error
import uuid
import xml.etree.ElementTree as ET
from collections import defaultdict
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMMITTED_LOCK = ROOT / "configs" / "external-sources.lock.json"
SOURCES = {
    "wnja": {
        "version": "1.1", "filename": "wnjpn.db.gz", "format": "sqlite-gzip",
        "url": "https://github.com/bond-lab/wnja/releases/download/v1.1/wnjpn.db.gz",
        "homepage": "https://bond-lab.github.io/wnja/eng/downloads.html",
        "license": "Japanese-WordNet + WordNet",
        "licenses": {
            "Japanese-WordNet.txt": "https://raw.githubusercontent.com/bond-lab/wnja/7ad6d75bda9a94fe208d6aa083b55baf891100b1/LICENSE",
            "Princeton-WordNet.txt": "https://wordnet.princeton.edu/license-and-commercial-use",
        },
    },
    "oewn": {
        "version": "2025", "filename": "english-wordnet-2025.xml.gz", "format": "lmf-gzip",
        "url": "https://en-word.net/static/english-wordnet-2025.xml.gz",
        "homepage": "https://en-word.net/downloads",
        "license": "CC-BY-4.0 + WordNet",
        "licenses": {
            "Open-English-WordNet.md": "https://raw.githubusercontent.com/globalwordnet/english-wordnet/2025-edition/LICENSE.md",
            "OEWN-WNDB-License.txt": "https://raw.githubusercontent.com/globalwordnet/english-wordnet/2025-edition/WNDB_License.txt",
        },
    },
}
MAX_COMPRESSED_BYTES = 128 * 1024 * 1024
MAX_UNCOMPRESSED_BYTES = 1024 * 1024 * 1024

# Official WordNet 3.0 notice transcribed from the URL above, checked 2026-11-05.
# Some Princeton servers deny automated GETs even though the public notice is readable.
PRINCETON_NOTICE = """WordNet Release 3.0
This software and database is being provided to you, the LICENSEE, by Princeton University under the following license.
By obtaining, using and/or copying this software and database, you agree that you have read, understood, and will comply with these terms and conditions:
Permission to use, copy, modify and distribute this software and database and its documentation for any purpose and without fee or royalty is hereby granted, provided that you agree to comply with the following copyright notice and statements, including the disclaimer, and that the same appear on ALL copies of the software, database and documentation, including modifications that you make for internal use or for distribution.
WordNet 3.0 Copyright 2006 by Princeton University. All rights reserved.
THIS SOFTWARE AND DATABASE IS PROVIDED "AS IS" AND PRINCETON UNIVERSITY MAKES NO REPRESENTATIONS OR WARRANTIES, EXPRESS OR IMPLIED.
BY WAY OF EXAMPLE, BUT NOT LIMITATION, PRINCETON UNIVERSITY MAKES NO REPRESENTATIONS OR WARRANTIES OF MERCHANT- ABILITY OR FITNESS FOR ANY PARTICULAR PURPOSE OR THAT THE USE OF THE LICENSED SOFTWARE, DATABASE OR DOCUMENTATION WILL NOT INFRINGE ANY THIRD PARTY PATENTS, COPYRIGHTS, TRADEMARKS OR OTHER RIGHTS.
The name of Princeton University or Princeton may not be used in advertising or publicity pertaining to distribution of the software and/or database.
Title to copyright in this software, database and any associated documentation shall at all times remain with Princeton University and LICENSEE agrees to preserve same.
"""


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".part")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def download(url: str, path: Path, timeout: int, maximum: int = MAX_COMPRESSED_BYTES) -> None:
    """No archive extraction: only a fixed filename beneath the selected output root."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".part")
    request = urllib.request.Request(url, headers={"User-Agent": "fiXmArge-lexicons/0.1"})
    total = 0
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response, temporary.open("wb") as out:
            if response.headers.get("Content-Length") and int(response.headers["Content-Length"]) > maximum:
                raise ValueError("Download exceeds configured size limit")
            while chunk := response.read(1024 * 1024):
                total += len(chunk)
                if total > maximum:
                    raise ValueError("Download exceeds configured size limit")
                out.write(chunk)
        if not total:
            raise ValueError("Empty download")
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def probe(name: str, timeout: int) -> dict:
    request = urllib.request.Request(SOURCES[name]["url"], headers={
        "Range": "bytes=0-65535", "User-Agent": "fiXmArge-lexicons/0.1"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        sample = response.read(65536)
        return {"source": name, "url": SOURCES[name]["url"], "status": response.status,
                "sample_bytes": len(sample), "gzip_magic": sample.startswith(b"\x1f\x8b"),
                "content_range": response.headers.get("Content-Range"),
                "note": "Connectivity probe only; this is not a complete dataset or content hash."}


def acquire(name: str, base: Path, lock: dict, timeout: int, offline: bool, local: Path | None) -> Path:
    spec = SOURCES[name]
    path = local if local is not None else base / "raw" / spec["filename"]
    if not path.exists():
        if offline or local is not None:
            raise FileNotFoundError(f"Missing local data: {path}")
        download(spec["url"], path, timeout)
    digest = sha256(path)
    # A different local fixture/input cannot silently replace a production cache lock.
    origin = str(path.resolve()) if local is not None else spec["url"]
    key = name if local is None else name + ":local:" + origin
    old = lock.get("sources", {}).get(key)
    if old and (old["sha256"] != digest or old["origin"] != origin):
        raise ValueError(f"SHA256/origin changed for {key}; inspect the source before replacing its lock")
    if not old:
        lock.setdefault("sources", {})[key] = {
            "version": spec["version"], "origin": origin, "sha256": digest,
            "bytes": path.stat().st_size, "locked_at": datetime.now(timezone.utc).isoformat(),
            "verification": "first-download lock (TOFU); no independently published checksum supplied",
        }
    return path


def bounded_decompress(source: Path, target: Path) -> None:
    total = 0
    with gzip.open(source, "rb") as inp, target.open("wb") as out:
        while chunk := inp.read(1024 * 1024):
            total += len(chunk)
            if total > MAX_UNCOMPRESSED_BYTES:
                raise ValueError("Uncompressed data exceeds size limit")
            out.write(chunk)


def unique(values) -> list:
    return list(dict.fromkeys(value for value in values if value))


def row(identifier, language, lemma, reading, glosses, synonyms, pos, name):
    return {"id": identifier, "language": language, "lemma": lemma,
            "reading": reading or None, "glosses": unique(glosses),
            "synonyms": unique(x for x in synonyms if x != lemma), "pos": pos,
            "source": name + ":" + SOURCES[name]["version"], "license": SOURCES[name]["license"]}


def iter_wnja(source: Path):
    """Keep each word/synset sense separate; never deduplicate polysemy by spelling."""
    with tempfile.TemporaryDirectory(prefix="fixmarge-wnja-") as directory:
        database = Path(directory) / "wnjpn.db"
        bounded_decompress(source, database)
        with closing(sqlite3.connect(database.as_uri() + "?mode=ro", uri=True)) as conn:
            columns = {item[1] for item in conn.execute("PRAGMA table_info(word)")}
            reading = "w.pron" if "pron" in columns else "NULL"
            glosses = defaultdict(list)
            for synset, lang, definition in conn.execute('SELECT synset, lang, def FROM synset_def'):
                glosses[(synset, lang)].append(definition)
            synonyms = defaultdict(list)
            for synset, lang, lemma in conn.execute(
                    'SELECT DISTINCT s.synset, w.lang, w.lemma FROM sense s JOIN word w ON w.wordid=s.wordid'):
                synonyms[(synset, lang)].append(lemma)
            query = (f'SELECT DISTINCT w.wordid,w.lang,w.lemma,{reading},w.pos,s.synset '
                     'FROM word w JOIN sense s ON s.wordid=w.wordid '
                     "WHERE w.lang IN ('jpn','eng') ORDER BY w.lang,w.wordid,s.synset")
            for wordid, lang, lemma, pronunciation, pos, synset in conn.execute(query):
                yield row(f"wnja:{wordid}:{synset}", {"jpn": "ja", "eng": "en"}[lang],
                          lemma, pronunciation, glosses[(synset, lang)], synonyms[(synset, lang)], pos, "wnja")


def tag_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def term_key(value: str, language: str) -> str:
    value = unicodedata.normalize("NFC", value).strip()
    return value.casefold() if language == "en" else value


def normalized_paths(base: Path) -> list[Path]:
    candidates = [base / f"{name}-{spec['version']}.jsonl" for name, spec in SOURCES.items()]
    candidates.append(base / "unidic-2.1.2.jsonl")
    return [path for path in candidates if path.exists()]


def build_index(jsonl_paths: list[Path], database: Path) -> dict:
    """Bulk-build a disposable staging DB; readers only see the completed index."""
    if not jsonl_paths:
        raise ValueError("No normalized JSONL files to index")
    database.parent.mkdir(parents=True, exist_ok=True)
    if database.exists():
        # Recover any hot rollback journal from an interrupted older build before replacing it.
        with closing(sqlite3.connect(database)) as previous:
            previous.execute("SELECT name FROM sqlite_master LIMIT 1").fetchone()
    counts = {}
    # A moved file retains its ACL on Windows. Create beside the destination so it
    # inherits the workspace ACL, rather than a TemporaryDirectory's private ACL.
    staging = database.with_name(f".lexicons-{uuid.uuid4().hex}.building")
    try:
        with closing(sqlite3.connect(staging)) as conn:
            # A crash only discards this staging file; the published DB stays intact.
            conn.execute("PRAGMA journal_mode = OFF")
            conn.execute("PRAGMA synchronous = OFF")
            conn.execute("PRAGMA cache_size = -65536")
            conn.executescript('CREATE TABLE entries (id TEXT PRIMARY KEY, language TEXT, payload TEXT); '
                               'CREATE TABLE terms (key TEXT, entry_id TEXT); BEGIN;')
            for jsonl in jsonl_paths:
                entries, terms, count = [], [], 0
                with jsonl.open(encoding="utf-8") as handle:
                    for line in handle:
                        record = json.loads(line)
                        entries.append((record["id"], record["language"], line.strip()))
                        values = [record["lemma"], record.get("reading"), *record["synonyms"]]
                        terms.extend((key, record["id"]) for key in unique(
                            term_key(value, record["language"]) for value in values if value))
                        count += 1
                        if len(entries) >= 1000:
                            conn.executemany('INSERT INTO entries VALUES (?,?,?)', entries)
                            conn.executemany('INSERT INTO terms VALUES (?,?)', terms)
                            entries.clear()
                            terms.clear()
                conn.executemany('INSERT INTO entries VALUES (?,?,?)', entries)
                conn.executemany('INSERT INTO terms VALUES (?,?)', terms)
                counts[jsonl.name] = count
            conn.execute('CREATE INDEX terms_key ON terms(key)')
            conn.commit()
            if conn.execute("PRAGMA quick_check").fetchone()[0] != "ok":
                raise ValueError("Generated SQLite index failed quick_check")
        staging.replace(database)
    finally:
        staging.unlink(missing_ok=True)
    return counts


def iter_oewn(source: Path):
    with tempfile.TemporaryDirectory(prefix="fixmarge-oewn-") as directory:
        xml_path = Path(directory) / "oewn.xml"
        bounded_decompress(source, xml_path)
        yield from _iter_oewn_xml(xml_path)


def _iter_oewn_xml(source: Path):
    # ElementTree does not load external DTDs or resolve external entities.
    entries = []
    synsets = {}
    by_synset = defaultdict(list)
    with source.open("rb") as handle:
        total = 0
        for _, element in ET.iterparse(handle, events=("end",)):
            kind = tag_name(element.tag)
            if kind == "LexicalEntry":
                lemma = next((x for x in element if tag_name(x.tag) == "Lemma"), None)
                if lemma is not None:
                    written, pos = lemma.get("writtenForm", ""), lemma.get("partOfSpeech", "")
                    # Do not invent a kana/IPA pronunciation if upstream has none.
                    pronunciation = next((x.text for x in element.iter() if tag_name(x.tag) == "Pronunciation" and x.text), None)
                    for sense in element:
                        if tag_name(sense.tag) == "Sense":
                            synset = sense.get("synset", "")
                            entries.append((sense.get("id", element.get("id", "")), written, pronunciation, pos, synset))
                            by_synset[synset].append(written)
                    total += 1
                element.clear()
            elif kind == "Synset":
                synsets[element.get("id", "")] = unique(
                    "".join(x.itertext()).strip() for x in element if tag_name(x.tag) == "Definition")
                element.clear()
            if total > 1000000:
                raise ValueError("XML lexical entry count exceeds configured limit")
    if not entries or not synsets:
        raise ValueError("No LMF lexical entries/synsets found; check source format")
    for identifier, lemma, reading, pos, synset in entries:
        yield row("oewn:" + identifier, "en", lemma, reading, synsets.get(synset, []), by_synset[synset], pos, "oewn")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", choices=["all", *SOURCES], default="all")
    parser.add_argument("--out", type=Path, default=ROOT / "data" / "external")
    parser.add_argument("--dry-run", action="store_true", help="Print manifest without network or filesystem writes")
    parser.add_argument("--probe", action="store_true", help="Read at most 64KiB/source; do not save data")
    parser.add_argument("--offline", action="store_true", help="Use cached files only")
    parser.add_argument("--reindex-only", action="store_true", help="Rebuild index from existing normalized JSONL; no network")
    parser.add_argument("--prepare-only", action="store_true", help="Download/normalize only; postpone combined search index")
    parser.add_argument("--input", type=Path, help="Use a local gzip input; requires a single --source")
    parser.add_argument("--limit", type=int, default=0, help="Emit at most this many senses per source; 0=all")
    parser.add_argument("--timeout", type=int, default=20)
    args = parser.parse_args(argv)
    if args.input and args.source == "all":
        parser.error("--input requires --source wnja or --source oewn")
    if args.limit < 0 or args.timeout <= 0:
        parser.error("--limit must be >=0 and --timeout must be >0")
    names = list(SOURCES) if args.source == "all" else [args.source]
    if args.dry_run:
        print(json.dumps({"output": str(args.out.resolve()), "sources": {n: SOURCES[n] for n in names},
                          "committed_lock": str(COMMITTED_LOCK),
                          "checksum_policy": "Use the committed source lock; otherwise lock the first complete download and verify subsequent runs."},
                         ensure_ascii=False, indent=2))
        return 0
    if args.probe:
        failed = False
        for name in names:
            try:
                print(json.dumps(probe(name, args.timeout), ensure_ascii=False))
            except (OSError, ValueError) as error:
                failed = True
                print(json.dumps({"source": name, "error": str(error)}, ensure_ascii=False))
        return int(failed)
    base = args.out.resolve()
    base.mkdir(parents=True, exist_ok=True)
    if args.reindex_only:
        counts = build_index(normalized_paths(base), base / "lexicons.sqlite3")
        print(json.dumps({"index": str(base / "lexicons.sqlite3"), "records": counts}, ensure_ascii=False))
        return 0
    lock_path = base / "sources.lock.json"
    seed = lock_path if lock_path.exists() else COMMITTED_LOCK
    lock = json.loads(seed.read_text(encoding="utf-8")) if seed.exists() else {"schema_version": 1, "sources": {}}
    for name in names:
        path = acquire(name, base, lock, args.timeout, args.offline, args.input)
        write_json(lock_path, lock)
        if args.input is None:
            for filename, url in SOURCES[name]["licenses"].items():
                notice = base / "licenses" / filename
                if not notice.exists():
                    if args.offline:
                        raise FileNotFoundError(f"Required license notice missing: {notice}")
                    if filename == "Princeton-WordNet.txt":
                        # Always emit the full, reviewed plain-text notice rather than a web site's navigation HTML.
                        notice.parent.mkdir(parents=True, exist_ok=True)
                        notice.write_text(PRINCETON_NOTICE, encoding="utf-8")
                    else:
                        download(url, notice, args.timeout, maximum=1024 * 1024)
                lock.setdefault("license_notices", {})[filename] = {
                    "source_url": url, "sha256": sha256(notice),
                    "method": "reviewed official notice transcription (2026-11-05)" if filename == "Princeton-WordNet.txt" else "download",
                }
            write_json(lock_path, lock)
        output = base / f"{name}-{SOURCES[name]['version']}.jsonl"
        temporary = output.with_suffix(".jsonl.part")
        count = 0
        try:
            with temporary.open("w", encoding="utf-8", newline="\n") as handle:
                iterator = iter_wnja(path) if name == "wnja" else iter_oewn(path)
                try:
                    for record in iterator:
                        handle.write(json.dumps(record, ensure_ascii=False) + "\n")
                        count += 1
                        if args.limit and count >= args.limit:
                            break
                finally:
                    iterator.close()
            if not count:
                raise ValueError(f"No normalized entries produced for {name}")
            temporary.replace(output)
        finally:
            temporary.unlink(missing_ok=True)
        write_json(base / f"{name}.manifest.json", {"source": SOURCES[name], "output": str(output),
                   "output_sha256": sha256(output), "records": count, "limit": args.limit,
                   "local_input": args.input is not None, "transformation": "sense-level JSONL; original text retained; no machine-generated readings"})
        print(json.dumps({"source": name, "records": count, "output": str(output)}, ensure_ascii=False), flush=True)
    if not args.prepare_only:
        counts = build_index(normalized_paths(base), base / "lexicons.sqlite3")
        print(json.dumps({"index": str(base / "lexicons.sqlite3"), "records": counts}, ensure_ascii=False), flush=True)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, EOFError, ValueError, sqlite3.Error, ET.ParseError) as error:
        print(f"error: {error}", file=sys.stderr)
        raise SystemExit(1)
