"""Local, weights-unchanged lexical checks; draft references are not gold."""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from fixmarge.infer import ModelRunner, resolve_revision
from fixmarge.grounding import ground_generation
from fixmarge.rag import DIRECTIONS, DEFAULT_PUNCTUATION_ALIASES, LexiconRAG, build_prompt

WARNINGS = [
    "Local research check only; source rights metadata does not establish permission for training or public redistribution.",
    "Candidate references are draft lexical exercises, not validated sentence gold. Exact match is a diagnostic, not translation-quality certification.",
    "RAG can retrieve the reference from the dictionary. Its metric measures lookup-assisted consistency and must not be compared as held-out plain translation accuracy.",
    "This script uses no optimizer, backward pass, trainer, or training-data import. Generation leaves model weights unchanged.",
    "RAG output is grounded from dictionary evidence; raw model scores are reported separately. Grounded scores are not evidence of model translation quality.",
]


def candidate(row: dict[str, Any]) -> tuple[list[dict[str, str]], str, str, str]:
    if not isinstance(row, dict) or not isinstance(row.get("metadata", {}), dict):
        raise ValueError("Candidate and metadata must be objects")
    messages = row.get("messages", [])
    if len(messages) < 2 or messages[-1].get("role") != "assistant":
        raise ValueError("A candidate needs prompt messages followed by an assistant reference")
    prompt = [{"role": m["role"], "content": m["content"]} for m in messages[:-1]]
    user = next((m["content"] for m in reversed(prompt) if m["role"] == "user"), "")
    direction = row.get("metadata", {}).get("direction")
    if direction not in DIRECTIONS:
        raise ValueError("Candidate metadata.direction is missing or unsupported")
    _, separator, query = user.partition(":")
    if not separator or not query.strip():
        raise ValueError("Expected a lexical user prompt with a colon and query")
    return prompt, str(messages[-1]["content"]), direction, query.strip()


def normalize_answer(text: str, punctuation_aliases: bool = False) -> str:
    if punctuation_aliases:
        table = {ord(char): canonical for canonical, variants in DEFAULT_PUNCTUATION_ALIASES.items() for char in canonical + variants}
        text = text.translate(table)
    return re.sub(r"\s+", " ", text).strip()


def exact_reference(output: str, reference: str, alternatives: list[str] | None = None,
                    punctuation_aliases: bool = False) -> bool:
    try:
        parsed = json.loads(output)
        if isinstance(parsed, dict):
            output = parsed.get("translation")
            if not isinstance(output, str):
                return False
    except (json.JSONDecodeError, TypeError):
        pass
    accepted = [reference] + list(alternatives or [])
    return any(normalize_answer(output, punctuation_aliases) == normalize_answer(value, punctuation_aliases)
               for value in accepted)


def evaluate_rows(rows: list[dict[str, Any]], *, mode: str = "plain", limit: int = 10,
                  rag: LexiconRAG | None = None, runner: Any = None,
                  punctuation_aliases: bool = False, direction_filter: str | None = None) -> dict[str, Any]:
    counts: Counter[str] = Counter()
    rights: Counter[str] = Counter()
    records = []
    for number, row in enumerate(rows, 1):
        counts["rows_seen"] += 1
        if not isinstance(row, dict) or not isinstance(row.get("metadata", {}), dict):
            counts["skipped_invalid"] += 1
            continue
        task = row.get("metadata", {}).get("task")
        if task != "lexical_translation":
            counts["skipped_rule_explanation" if task == "rule_explanation" else "skipped_other_task"] += 1
            continue
        try:
            prompt, reference, direction, query = candidate(row)
        except (KeyError, TypeError, ValueError):
            counts["skipped_invalid"] += 1
            continue
        counts["valid_lexical_candidates"] += 1
        if direction_filter and direction != direction_filter:
            counts["skipped_direction"] += 1
            continue
        if len(records) >= limit:
            continue
        lookup = None
        if mode == "rag":
            if rag is None:
                raise ValueError("RAG mode requires a LexiconRAG instance")
            lookup = rag.lookup(query, direction)
            prompt = build_prompt(lookup)
        metadata = row.get("metadata", {})
        rights[metadata.get("rights_status", "unspecified")] += 1
        record = {"row": number, "direction": direction, "query": query, "prompt": prompt,
                  "reference": reference, "metadata": metadata}
        if lookup is not None:
            record["lookup"] = lookup
        if runner is not None:
            raw = runner.generate(prompt)
            raw_matched = exact_reference(raw, reference, metadata.get("alternatives"), punctuation_aliases)
            if lookup is not None:
                grounded = ground_generation(lookup, raw)
                output = json.dumps(grounded, ensure_ascii=False)
                record["grounding"] = grounded["grounding"]
            else:
                output = raw
            matched = exact_reference(output, reference, metadata.get("alternatives"), punctuation_aliases)
            record.update({"raw_output": raw, "raw_exact_reference": raw_matched,
                           "output": output, "exact_reference": matched})
            counts["scored"] += 1
            counts["exact_matches"] += int(matched)
            counts["raw_exact_matches"] += int(raw_matched)
        records.append(record)
    counts["selected"] = len(records)
    scored = counts["scored"]
    return {"execution": "generate" if runner is not None else "dry-run", "mode": mode, "direction_filter": direction_filter,
            "metric": f"{mode}_exact_draft_reference", "counts": dict(counts),
            "exact_reference_rate": counts["exact_matches"] / scored if scored else None,
            "raw_exact_reference_rate": counts["raw_exact_matches"] / scored if scored else None,
            "output_source": ("dictionary_grounded" if mode == "rag" else "model") if runner is not None else "none",
            "normalization": {"case_preserved": True, "punctuation_aliases": punctuation_aliases},
            "rights_status_counts": dict(rights), "warnings": WARNINGS, "records": records}


def main(argv: list[str] | None = None) -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, default=ROOT / "data/research/validation_candidates.jsonl")
    parser.add_argument("--mode", choices=("plain", "rag"), default="plain")
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--direction", choices=DIRECTIONS, help="Optional direction filter; both modes retain the same example order")
    execution = parser.add_mutually_exclusive_group()
    execution.add_argument("--dry-run", action="store_true", help="Validate rows and build prompts without loading weights (default)")
    execution.add_argument("--generate", action="store_true")
    parser.add_argument("--model")
    parser.add_argument("--adapter")
    parser.add_argument("--revision")
    parser.add_argument("--device", choices=("auto", "cpu", "cuda"), default="auto")
    parser.add_argument("--load-in-4bit", action="store_true")
    parser.add_argument("--allow-download", action="store_true")
    parser.add_argument("--max-new-tokens", type=int, default=256)
    parser.add_argument("--data-dir")
    parser.add_argument("--external-dir")
    parser.add_argument("--punctuation-aliases", action="store_true", help="Allow declared dot/apostrophe equivalence in exact match; retain case")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    if args.limit < 1 or args.max_new_tokens < 1:
        parser.error("--limit and --max-new-tokens must be positive")
    if args.generate and not args.model:
        parser.error("--generate requires --model")
    if args.load_in_4bit and args.device == "cpu":
        parser.error("--load-in-4bit requires CUDA")
    try:
        rows = [json.loads(line) for line in args.dataset.read_text(encoding="utf-8-sig").splitlines() if line.strip()]
        rag = LexiconRAG(args.data_dir, external_dir=args.external_dir) if args.mode == "rag" else None
        runner = ModelRunner(model_name=args.model, adapter=args.adapter, revision=args.revision,
                             device=args.device, load_in_4bit=args.load_in_4bit,
                             allow_download=args.allow_download, max_new_tokens=args.max_new_tokens) if args.generate else None
        report = evaluate_rows(rows, mode=args.mode, limit=args.limit, rag=rag, runner=runner,
                               punctuation_aliases=args.punctuation_aliases, direction_filter=args.direction)
        report["dataset"] = str(args.dataset)
        report["model"] = {"name": args.model, "revision": resolve_revision(args.model, args.revision) if args.model else None,
                           "adapter": args.adapter, "device": args.device, "nf4": args.load_in_4bit}
        output = args.output or ROOT / "runs" / ("evaluation-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ") + "-" + args.mode + ".json")
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({"output": str(output), "execution": report["execution"], "mode": report["mode"],
                          "counts": report["counts"], "exact_reference_rate": report["exact_reference_rate"],
                          "raw_exact_reference_rate": report["raw_exact_reference_rate"], "output_source": report["output_source"],
                          "warnings": report["warnings"]}, ensure_ascii=False, indent=2))
        return 0
    except (OSError, ValueError, RuntimeError, TypeError) as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
