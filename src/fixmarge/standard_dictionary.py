"""Independent, bounded lookup of the locally verified English/Japanese WordNets."""
from __future__ import annotations

from copy import deepcopy
from contextlib import closing
from itertools import islice
import json
from pathlib import Path
import re
import sqlite3
import unicodedata
from typing import Any, Iterable

MAX_QUERIES = 160
MAX_ENTRIES = 24
MAX_TOKENS = 64
VERIFIED_SOURCES = {
    "wnja:1.1": {
        "source": "wnja:1.1", "name": "Japanese WordNet", "version": "1.1",
        "license": "Japanese-WordNet + WordNet", "commercial_use": True,
        "credit": "Japanese WordNet 1.1 — NICT; Francis Bond; Takayuki Kuribayashi; Princeton University WordNet",
        "homepage": "https://bond-lab.github.io/wnja/index.en.html",
        "license_urls": [
            "https://raw.githubusercontent.com/bond-lab/wnja/7ad6d75bda9a94fe208d6aa083b55baf891100b1/LICENSE",
            "https://wordnet.princeton.edu/license-and-commercial-use",
        ],
        "notice_files": ["Japanese-WordNet.txt", "Princeton-WordNet.txt"],
    },
    "oewn:2025": {
        "source": "oewn:2025", "name": "Open English WordNet", "version": "2025",
        "license": "CC-BY-4.0 + WordNet", "commercial_use": True,
        "credit": "Open English WordNet Team; Princeton University WordNet",
        "homepage": "https://en-word.net/",
        "license_urls": [
            "https://raw.githubusercontent.com/globalwordnet/english-wordnet/2025-edition/LICENSE.md",
            "https://raw.githubusercontent.com/globalwordnet/english-wordnet/2025-edition/WNDB_License.txt",
        ],
        "notice_files": ["Open-English-WordNet.md", "OEWN-WNDB-License.txt"],
    },
}
TOKEN_PATTERN = re.compile(r"[^\W_]+(?:['’][^\W_]+)*", re.UNICODE)
JAPANESE_CHUNKS = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff々]+|[\u3040-\u309f]+|[\u30a0-\u30ffー]+")
LIMITATIONS = [
    "Direct dictionary definitions and synonyms are lexical evidence, not verified sentence translations or cross-language alignment.",
    "Japanese script runs are bounded query candidates, not verified morphological segmentation or lemmatization.",
    "Retain the source credits, license notices, and applicable change notices when using or redistributing this data.",
]


def default_external_dir() -> Path:
    return Path(__file__).resolve().parents[2] / "data" / "external"


def _queries(text: str, extra_queries: Iterable[tuple[str, str]], include_input: bool) -> list[dict[str, Any]]:
    text = unicodedata.normalize("NFC", text)
    queries: dict[str, list[str]] = {}

    def add(term, reason):
        if not isinstance(term, str) or not isinstance(reason, str):
            raise ValueError("Dictionary queries and reasons must be strings")
        term = unicodedata.normalize("NFC", term.strip())
        if not term or len(term) > 160:
            return
        if term not in queries and len(queries) >= MAX_QUERIES:
            return
        if reason not in queries.setdefault(term, []):
            queries[term].append(reason)

    for value in islice(extra_queries, MAX_QUERIES):
        if not isinstance(value, (list, tuple)) or len(value) != 2:
            raise ValueError("extra_queries must contain (query, reason) pairs")
        add(*value)
    if include_input:
        add(text, "input")
        tokens = [match.group() for match in islice(TOKEN_PATTERN.finditer(text), MAX_TOKENS)]
        # Individual words precede phrase windows so a long sentence cannot starve them.
        for token in tokens:
            add(token, "input")
        for match in islice(JAPANESE_CHUNKS.finditer(text), MAX_TOKENS):
            add(match.group(), "input_japanese_chunk")
        for width in (4, 3, 2):
            for start in range(len(tokens) - width + 1):
                add(" ".join(tokens[start:start + width]), "input")
    return [{"query": query, "reasons": reasons} for query, reasons in queries.items()]


def lookup_standard_dictionary(
    text: str,
    external_dir: str | Path | None = None,
    languages: Iterable[str] = ("en", "ja"),
    limit_per_language: int = 3,
    *,
    extra_queries: Iterable[tuple[str, str]] = (),
    include_input: bool = True,
) -> dict[str, Any]:
    """Read only the existing index, returning at most three senses/query/language by default.

    No fiXmArge files, models, downloads, packages, or Korean index rows are used.
    Exact NFC-normalized lemmas (English casefold) rank before synonym-only
    matches, with stable IDs breaking ties. Only the reviewed source/license
    combinations above are admitted. Set include_input=False for fiXmArge
    sources so only supplied natural-language glosses are searched.
    """
    if not isinstance(text, str):
        raise ValueError("Dictionary input must be a string")
    if type(include_input) is not bool:
        raise ValueError("include_input must be a boolean")
    if isinstance(languages, str):
        languages = (languages,)
    selected_languages = tuple(dict.fromkeys(languages))
    if not selected_languages or any(language not in ("en", "ja") for language in selected_languages):
        raise ValueError("Standard dictionary languages must be en and/or ja")
    if isinstance(limit_per_language, bool) or not isinstance(limit_per_language, int) or not 1 <= limit_per_language <= MAX_ENTRIES:
        raise ValueError("limit_per_language must be an integer from 1 to 24")
    directory = Path(external_dir) if external_dir is not None else default_external_dir()
    database = directory / "lexicons.sqlite3"
    queries = _queries(text, extra_queries, include_input)
    result = {"available": database.is_file(), "entries": [], "matched_entry_count": 0,
              "queries": queries, "languages": list(selected_languages), "attributions": [],
              "source_policy": "verified_wnja_1.1_and_oewn_2025_only",
              "query_policy": {"include_input": include_input, "exact_spelling_filter": "fiXmArge_gloss_only"},
              "segmentation_verified": False, "limitations": LIMITATIONS[:],
              "limits": {"queries": MAX_QUERIES, "entries": MAX_ENTRIES,
                         "per_query_language": limit_per_language}}
    if not result["available"]:
        return result
    found: dict[str, dict[str, Any]] = {}
    try:
        with closing(sqlite3.connect(database.resolve().as_uri() + "?mode=ro", uri=True)) as connection:
            for query_record in queries:
                query, reasons = query_record["query"], query_record["reasons"]
                for language in selected_languages:
                    key = query.casefold() if language == "en" else query
                    rows = connection.execute(
                        "SELECT e.id,e.payload FROM terms t JOIN entries e ON e.id=t.entry_id "
                        "WHERE t.key=? AND e.language=? GROUP BY e.id", (key, language))
                    candidates = []
                    for identifier, payload in rows:
                        entry = json.loads(payload)
                        if not isinstance(entry, dict):
                            raise ValueError("Dictionary payload must be an object")
                        source = VERIFIED_SOURCES.get(entry.get("source"))
                        if source is None or entry.get("license") != source["license"] or entry.get("language") != language:
                            continue
                        if not isinstance(entry.get("lemma"), str):
                            raise ValueError("Dictionary lemma must be a string")
                        candidates.append((identifier, entry))

                    # English casefold indexes mix ordinary words with symbols
                    # such as no/No. For gloss bridges, suppress a proven case-only
                    # match when exact spelling exists; retain fallback otherwise.
                    # Natural input keeps alternatives: sentence-initial No can
                    # be ordinary negation rather than a chemical symbol.
                    # Indexed aliases absent from payload metadata stay eligible.
                    def spelling(candidate):
                        _, entry = candidate
                        forms = [entry['lemma'], *entry.get('synonyms', [])]
                        forms = [unicodedata.normalize("NFC", form.strip())
                                 for form in forms if isinstance(form, str)]
                        matched = [form for form in forms if form.casefold() == key]
                        return query in matched, bool(matched) and query not in matched

                    bridge_only = reasons and all(reason.startswith("fiXmArge_gloss:") for reason in reasons)
                    if language == "en" and bridge_only and any(spelling(item)[0] for item in candidates):
                        candidates = [item for item in candidates if not spelling(item)[1]]

                    def rank(candidate):
                        identifier, entry = candidate
                        lemma = unicodedata.normalize("NFC", entry["lemma"].strip())
                        return ((lemma.casefold() if language == "en" else lemma) != key, identifier)

                    for identifier, entry in sorted(candidates, key=rank)[:limit_per_language]:
                        if identifier not in found and len(found) >= MAX_ENTRIES:
                            break
                        record = found.setdefault(identifier, {"entry": entry, "matches": []})
                        match = {"query": query, "reasons": reasons[:]}
                        if match not in record["matches"]:
                            record["matches"].append(match)
                    if len(found) >= MAX_ENTRIES:
                        break
                if len(found) >= MAX_ENTRIES:
                    break
    except (sqlite3.Error, OSError, json.JSONDecodeError, ValueError) as error:
        raise ValueError(f"Cannot read standard dictionary index {database}: {error}") from error
    result["entries"] = list(found.values())
    result["matched_entry_count"] = len(found)
    used = list(dict.fromkeys(item["entry"]["source"] for item in found.values()))
    result["attributions"] = [deepcopy(VERIFIED_SOURCES[source]) for source in used]
    return result


def gloss_queries(entries: Iterable[dict[str, Any]]) -> list[tuple[str, str]]:
    """Preserve every EN/JA sense and its source entry as a lexical bridge."""
    result = []
    for entry in entries:
        for language in ('en', 'ja'):
            for sense in entry.get('senses', {}).get(language, []):
                if isinstance(sense, str):
                    query = (sense, f"fiXmArge_gloss:{entry.get('id', entry['form'])}:{language}")
                    if query not in result:
                        result.append(query)
    return result
