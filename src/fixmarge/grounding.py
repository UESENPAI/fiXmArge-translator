"""Direction-specific lexical contracts and transparent output grounding.

These functions preserve dictionary alternatives. They do not infer sentence
translations or turn an unreviewed dictionary into a translation benchmark.
"""
from __future__ import annotations

from copy import deepcopy
import json
from typing import Any, Mapping

LANGUAGE_NAMES = {"fix": "fiXmArge", "ko": "Korean", "ja": "Japanese", "en": "English"}
DIRECTION_LANGUAGES = {
    "fix-to-ko": ("fix", "ko"), "ko-to-fix": ("ko", "fix"),
    "fix-to-ja": ("fix", "ja"), "ja-to-fix": ("ja", "fix"),
    "fix-to-en": ("fix", "en"), "en-to-fix": ("en", "fix"),
}


def _unique(values):
    return list(dict.fromkeys(values))


def build_lexical_contract(lookup: Mapping[str, Any]) -> dict[str, Any]:
    """Enumerate target alternatives per input span, using direct evidence only."""
    direction = lookup.get("direction")
    if direction not in DIRECTION_LANGUAGES:
        raise ValueError(f"Unsupported lexical direction: {direction!r}")
    source, target = DIRECTION_LANGUAGES[direction]
    separator = " / " if target == "fix" else "; "
    text = lookup["text"]
    segments = []
    case_ambiguity = False
    for item in lookup.get("evidence", []):
        candidates: dict[str, dict[str, Any]] = {}
        missing = []
        conflicting = []
        entry_ids = []
        forms = []
        for entry in item["entries"]:
            identifier = entry.get("id")
            if isinstance(identifier, str):
                entry_ids.append(identifier)
            forms.append(entry["form"])
            terms = [entry["form"]] if target == "fix" else entry.get("senses", {}).get(target, [])
            terms = _unique(term for term in terms if isinstance(term, str) and term.strip())
            if not terms:
                missing.append(identifier)
            if entry.get("has_conflict"):
                conflicting.append(identifier)
            provenance = {"entry_id": identifier, "form": entry["form"],
                          "sources": deepcopy(entry.get("sources", [])),
                          "status": entry.get("status"), "rights_status": entry.get("rights_status"),
                          "has_conflict": bool(entry.get("has_conflict"))}
            for term in terms:
                candidate = candidates.setdefault(term, {"text": term, "language": target, "evidence": []})
                if provenance not in candidate["evidence"]:
                    candidate["evidence"].append(provenance)
        if target != "fix" and item.get("match_type") == "case_insensitive_fallback" and len(set(forms)) > 1:
            case_ambiguity = True
        segments.append({"text": item["text"], "start": item["start"], "end": item["end"],
                         "entry_ids": _unique(entry_ids), "candidates": list(candidates.values()),
                         "missing_target_entry_ids": _unique(missing),
                         "conflicting_entry_ids": _unique(conflicting)})
    single = len(segments) == 1 and not text[:segments[0]["start"]].strip() and not text[segments[0]["end"]:].strip()
    scope = "single_lexical" if single else "partial_lexical" if segments else "no_lexical_evidence"
    reasons = []
    if not segments:
        reasons.append("no_lexical_evidence")
    elif not single:
        reasons.append("partial_input")
    if lookup.get("unknown_tokens"):
        reasons.append("unknown_input_tokens")
    if any(segment["conflicting_entry_ids"] for segment in segments):
        reasons.append("source_conflict")
    if any(segment["missing_target_entry_ids"] for segment in segments):
        reasons.append("missing_target_senses")
    if case_ambiguity:
        reasons.append("case_ambiguity")
    choices = [candidate["text"] for candidate in segments[0]["candidates"]] if single else []
    expected = separator.join(choices) if choices and not reasons else None
    return {"direction": direction, "source_language": source, "target_language": target,
            "scope": scope, "segments": segments, "candidate_separator": separator,
            "expected_translation": expected,
            "abstention_reasons": reasons}


def _valid_schema(response):
    if not isinstance(response, dict):
        return False
    if not all(key in response for key in ("translation", "analysis", "evidence_ids", "unknown_tokens", "warnings")):
        return False
    return ((response["translation"] is None or isinstance(response["translation"], str))
            and isinstance(response["analysis"], str)
            and isinstance(response["unknown_tokens"], list)
            and all(isinstance(response[key], list) and all(isinstance(value, str) for value in response[key])
                    for key in ("evidence_ids", "warnings")))


def ground_generation(lookup: Mapping[str, Any], raw_output: str) -> dict[str, Any]:
    """Validate raw generation and expose a dictionary-grounded lexical answer.

    The caller must retain raw_output separately. Canonical alternatives and
    abstentions are computed again from lookup, never from a model-supplied
    contract or a language/script heuristic.
    """
    contract = build_lexical_contract(lookup)
    expected = contract["expected_translation"]
    identifiers = _unique(identifier for segment in contract["segments"] for identifier in segment["entry_ids"])
    unknown = deepcopy(lookup.get("unknown_tokens", []))
    issues = []
    parsed = None
    try:
        parsed = json.loads(raw_output)
    except (json.JSONDecodeError, TypeError):
        issues.append("invalid_json")
    if not _valid_schema(parsed):
        issues.append("invalid_response_schema")
    response = parsed if isinstance(parsed, dict) else {}
    translation_matches = "translation" in response and response["translation"] == expected
    if not translation_matches:
        issues.append("unsupported_translation" if expected is None else "target_candidates_mismatch")
    if response.get("unknown_tokens") != unknown:
        issues.append("unknown_tokens_changed")
    raw_ids = response.get("evidence_ids")
    if not isinstance(raw_ids, list) or any(not isinstance(value, str) for value in raw_ids) or set(raw_ids) != set(identifiers):
        issues.append("evidence_ids_changed")
    raw_translation = response.get("translation")
    raw_parts = raw_translation.split(contract["candidate_separator"]) if isinstance(raw_translation, str) else []
    coverage = []
    for segment in contract["segments"]:
        choices = [candidate["text"] for candidate in segment["candidates"]]
        # Equality of complete alternatives is intentional: sinRuit must not
        # count as present merely because sinruits contains it as a substring.
        returned = choices[:] if contract["scope"] == "single_lexical" and raw_translation == expected and expected is not None else [choice for choice in choices if raw_translation == choice or choice in raw_parts]
        coverage.append({"start": segment["start"], "end": segment["end"], "expected": choices,
                         "raw_returned": returned, "missing": [choice for choice in choices if choice not in returned],
                         "final_alternatives": choices[:]})
    reasons = contract["abstention_reasons"]
    language = LANGUAGE_NAMES[contract["target_language"]]
    if expected is not None:
        analysis = f"Dictionary lexical alternatives in {language}: {expected}. No sentence grammar was inferred."
    elif "source_conflict" in reasons:
        analysis = "The sources conflict. Candidate alternatives remain grouped by input span; no sense was selected."
    elif "case_ambiguity" in reasons:
        analysis = "Case fallback matched distinct canonical forms. Their alternatives remain separate; no meaning was selected."
    elif "missing_target_senses" in reasons:
        analysis = f"The input is registered, but the matched entry has no {language} sense. This does not make the input an unknown word."
    elif contract["scope"] == "no_lexical_evidence":
        analysis = "No attested lexical match supports the requested direction."
    else:
        analysis = "Only lexical alternatives for separate input spans are available. No sentence translation was inferred."
    warnings = list(lookup.get("messages", []))
    if reasons:
        warnings.append("Translation was withheld under the lexical evidence contract: " + ", ".join(reasons) + ".")
    if issues:
        warnings.append("The raw model response differed from the evidence contract; the final lexical response was grounded from dictionary evidence.")
    status = "model_output_validated" if not issues else "corrected_from_dictionary" if expected is not None else "unsupported_generation_rejected"
    return {"translation": expected, "analysis": analysis, "evidence_ids": identifiers,
            "unknown_tokens": unknown, "warnings": _unique(warnings),
            "alternatives": deepcopy(contract["segments"]),
            "grounding": {"status": status, "scope": contract["scope"],
                          "target_language": contract["target_language"], "issues": issues,
                          "model_translation_matches": translation_matches,
                          "analysis_source": "dictionary_evidence", "model_analysis_verified": False,
                          "candidate_coverage": coverage}}
