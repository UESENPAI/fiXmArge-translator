#!/usr/bin/env python3
"""Optional UniDic 2.1.2 source-CSV importer; no MeCab executable is required."""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import re
import stat
import sys
import time
import urllib.request
import zipfile
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath, PureWindowsPath

import prepare_external_lexicons as common

SOURCE = {
    "id": "unidic", "version": "2.1.2", "license": "BSD-3-Clause",
    "filename": "unidic-mecab-2.1.2_src.zip",
    "url": "https://clrd.ninjal.ac.jp/unidic_archive/cwj/2.1.2/unidic-mecab-2.1.2_src.zip",
    "license_url": "https://clrd.ninjal.ac.jp/unidic/copying/BSD",
    "layout_url": "https://clrd.ninjal.ac.jp/unidic/faq.html",
    "known_archive_bytes": 140517811,
    "size_evidence": "https://mirrors.mit.edu/gentoo-distfiles/distfiles/d4/",
}
MAX_UNCOMPRESSED = 1024 * 1024 * 1024


def checked_members(archive: zipfile.ZipFile):
    members, total = {}, 0
    for member in archive.infolist():
        name = member.filename.replace("\\", "/")
        parts = PurePosixPath(name).parts
        if name.startswith("/") or PureWindowsPath(name).drive or ".." in parts:
            raise ValueError(f"Unsafe ZIP member path: {member.filename!r}")
        if stat.S_ISLNK(member.external_attr >> 16) or member.flag_bits & 1:
            raise ValueError("Symlink/encrypted ZIP members are not accepted")
        total += member.file_size
        if total > MAX_UNCOMPRESSED:
            raise ValueError("ZIP uncompressed total exceeds 1 GiB; no members were extracted")
        if not member.is_dir():
            basename = PurePosixPath(name).name
            if basename not in {"lex.csv", "BSD", "AUTHORS", "dicrc", "rewrite.def", "README", "README.md", "README.txt"}:
                continue
            if basename in members:
                raise ValueError(f"Ambiguous duplicate ZIP member basename: {basename}")
            members[basename] = member
    for required in ("lex.csv", "BSD", "AUTHORS"):
        if required not in members:
            raise ValueError(f"Required official source member is missing: {required}")
    return members, total


def verify_layout(archive, members) -> str:
    """UniDic features follow the four MeCab columns; f[6]=lForm, f[7]=lemma."""
    expected = {6: "lForm", 7: "lemma", 8: "orth", 9: "pron"}
    found = {}
    for filename in ("dicrc", "rewrite.def", "README", "README.md", "README.txt"):
        if filename not in members:
            continue
        if members[filename].file_size > 2 * 1024 * 1024:
            raise ValueError("Unexpectedly large package layout metadata")
        text = archive.read(members[filename]).decode("utf-8", errors="replace")
        for index, label in re.findall(r"f\[\s*(\d+)\s*\]\s*:\s*([A-Za-z_]+)", text):
            found[int(index)] = label
        if filename == "rewrite.def":
            for index, label in re.findall(r"\$(\d+)\s*:\s*([A-Za-z_]+)", text):
                found[int(index) - 1] = label
    for index, label in expected.items():
        if index in found and found[index] != label:
            raise ValueError(f"Package feature f[{index}]={found[index]!r}; expected {label!r}")
    if all(found.get(index) == label for index, label in expected.items()):
        return "package dicrc/rewrite.def labels plus official UniDic FAQ"
    return "fixed UniDic 2.1.2 feature layout from official FAQ; package labels absent/incomplete"


def iter_readings(archive, member):
    seen = set()
    csv.field_size_limit(16 * 1024 * 1024)
    with archive.open(member) as binary, io.TextIOWrapper(binary, encoding="utf-8-sig", newline="") as text:
        for number, fields in enumerate(csv.reader(text), 1):
            if not fields:
                continue
            if len(fields) < 21 or not all(re.fullmatch(r"[+-]?\d+", value) for value in fields[1:4]):
                raise ValueError(f"Unexpected lex.csv schema at row {number}")
            # surface,left-id,right-id,cost + f[0..]; therefore lForm=10, lemma=11.
            reading, lemma = fields[10], fields[11]
            pos = "-".join(value for value in fields[4:8] if value and value != "*")
            if not lemma or lemma == "*" or not reading or reading == "*":
                continue
            key = (lemma, reading, pos)
            if key in seen:
                continue
            seen.add(key)
            identifier = hashlib.sha256("\0".join(key).encode("utf-8")).hexdigest()[:32]
            yield {"id": "unidic:" + identifier, "language": "ja", "lemma": lemma,
                   "reading": reading, "glosses": [], "synonyms": [], "pos": pos,
                   "source": "unidic:2.1.2", "license": "BSD-3-Clause",
                   "kind": "morphological_reading"}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=common.ROOT / "data" / "external")
    parser.add_argument("--input", type=Path, help="Use an already obtained official source ZIP")
    parser.add_argument("--dry-run", action="store_true", help="Show source and limits; no network or writes")
    parser.add_argument("--max-archive-mib", type=int, default=128, help="Explicit operator size budget; default 128 MiB")
    parser.add_argument("--timeout", type=int, default=20)
    parser.add_argument("--index", choices=("auto", "combined", "separate", "none"), default="auto")
    args = parser.parse_args(argv)
    if args.max_archive_mib <= 0 or args.timeout <= 0:
        parser.error("Size and timeout must be positive")
    maximum = args.max_archive_mib * 1024 * 1024
    if args.dry_run:
        print(json.dumps({"source": SOURCE, "max_archive_bytes": maximum,
                          "source_download_status": "unverified_download",
                          "within_default_budget": SOURCE["known_archive_bytes"] <= maximum,
                          "max_uncompressed_bytes": MAX_UNCOMPRESSED,
                          "notice": "The known 134 MiB archive exceeds the default 128 MiB budget; no automatic download was made."},
                         ensure_ascii=False, indent=2))
        return 0
    base = args.out.resolve()
    source = args.input.resolve() if args.input else base / "raw" / SOURCE["filename"]
    if source.exists():
        size = source.stat().st_size
    else:
        if args.input:
            raise FileNotFoundError(source)
        if SOURCE["known_archive_bytes"] > maximum:
            raise ValueError("Known archive size exceeds the configured budget; use --dry-run to inspect it")
        request = urllib.request.Request(SOURCE["url"], method="HEAD")
        with urllib.request.urlopen(request, timeout=args.timeout) as response:
            size = int(response.headers["Content-Length"])
        if size > maximum:
            raise ValueError("HEAD response exceeds the configured archive budget; download stopped")
        common.download(SOURCE["url"], source, args.timeout, maximum=maximum)
        size = source.stat().st_size
    if size > maximum:
        raise ValueError("Local archive exceeds the configured size budget")
    base.mkdir(parents=True, exist_ok=True)
    lock_path = base / "sources.lock.json"
    seed = lock_path if lock_path.exists() else common.COMMITTED_LOCK
    lock = json.loads(seed.read_text(encoding="utf-8")) if seed.exists() else {"schema_version": 1, "sources": {}}
    digest = common.sha256(source)
    old = lock.get("sources", {}).get("unidic")
    if old and old["sha256"] != digest:
        raise ValueError("UniDic SHA256 differs from the source lock")
    started, count = time.monotonic(), 0
    output = base / "unidic-2.1.2.jsonl"
    temporary = output.with_suffix(".jsonl.part")
    try:
        with zipfile.ZipFile(source) as archive:
            members, total = checked_members(archive)
            layout = verify_layout(archive, members)
            for filename in ("BSD", "AUTHORS"):
                if members[filename].file_size > 1024 * 1024:
                    raise ValueError("Unexpectedly large license/authorship notice")
                notice = base / "licenses" / f"UniDic-2.1.2-{filename}.txt"
                notice.parent.mkdir(parents=True, exist_ok=True)
                notice.write_bytes(archive.read(members[filename]))
                if filename == "BSD" and b"Redistribution and use" not in notice.read_bytes():
                    raise ValueError("BSD notice did not contain the expected license grant")
                lock.setdefault("license_notices", {})[notice.name] = {
                    "source_url": SOURCE["url"] + "#" + members[filename].filename,
                    "sha256": common.sha256(notice), "method": "official source ZIP member"}
            with temporary.open("w", encoding="utf-8", newline="\n") as handle:
                for record in iter_readings(archive, members["lex.csv"]):
                    handle.write(json.dumps(record, ensure_ascii=False) + "\n")
                    count += 1
            if not count:
                raise ValueError("No reading records were produced")
            temporary.replace(output)
    finally:
        temporary.unlink(missing_ok=True)
    lock.setdefault("sources", {})["unidic"] = {
        "version": "2.1.2", "origin": SOURCE["url"], "sha256": digest, "bytes": size,
        "locked_at": old.get("locked_at") if old else datetime.now(timezone.utc).isoformat(),
        "verification": "first-import lock (TOFU); no independent publisher checksum supplied",
        "acquisition": "local archive" if args.input else "official HTTPS download"}
    common.write_json(lock_path, lock)
    elapsed = time.monotonic() - started
    common.write_json(base / "unidic.manifest.json", {
        "source": SOURCE, "records": count, "output_sha256": common.sha256(output),
        "uncompressed_archive_bytes": total, "layout_verification": layout,
        "normalization_seconds": round(elapsed, 3), "transformation": "deduplicate (lemma,lForm,POS); no definitions generated"})
    mode = "separate" if args.index == "auto" and elapsed > 120 else args.index
    if mode in ("auto", "combined"):
        common.build_index(common.normalized_paths(base), base / "lexicons.sqlite3")
    elif mode == "separate":
        common.build_index([output], base / "lexicons-readings.sqlite3")
    print(json.dumps({"records": count, "output": str(output), "index_mode": mode}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, KeyError, zipfile.BadZipFile, csv.Error) as error:
        print(f"error: {error}", file=sys.stderr)
        raise SystemExit(1)
