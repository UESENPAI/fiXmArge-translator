"""Run unverified sentence diagnostics with cached models and direct evidence."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from fixmarge.infer import ModelRunner, resolve_revision
from fixmarge.rag import LexiconRAG
from fixmarge.standard_dictionary import gloss_queries, lookup_standard_dictionary
from fixmarge.sentence_diagnostics import (
    build_sentence_evidence, build_sentence_prompt, inspect_sentence_generation,
)

LANGUAGES = ("fix", "ko", "en", "ja")
DEFAULT_MODEL = "Qwen/Qwen3-4B-Instruct-2507"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", choices=LANGUAGES, required=True)
    parser.add_argument("--target", choices=LANGUAGES, required=True)
    parser.add_argument("--text", required=True)
    parser.add_argument("--generate", action="store_true", help="Load a cached model and propose an unverified sentence")
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--device", choices=("auto", "cpu", "cuda"), default="auto")
    parser.add_argument("--max-new-tokens", type=int, default=512)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    if args.source == args.target:
        parser.error("--source and --target must be different")
    if args.max_new_tokens <= 0:
        parser.error("--max-new-tokens must be positive")
    for name in ("HF_HUB_OFFLINE", "TRANSFORMERS_OFFLINE", "HF_HUB_DISABLE_TELEMETRY"):
        os.environ[name] = "1"
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    mode = "generate" if args.generate else "dry-run"
    direction = f"{args.source}-to-{args.target}"
    try:
        rag = LexiconRAG() if "fix" in (args.source, args.target) else None
        lookup = rag.lookup(args.text, direction) if rag is not None else None
        evidence = build_sentence_evidence(args.text, args.source, args.target, lookup)
        extra_queries = (gloss_queries(entry for segment in evidence['lexical_segments']
                                      for entry in segment['entries']) if args.source == 'fix' else [])
        evidence["standard_dictionary"] = lookup_standard_dictionary(
            args.text, external_dir=None, languages=("en", "ja"), extra_queries=extra_queries,
            include_input=args.source in ("en", "ja"))
        prompt = build_sentence_prompt(evidence, lookup)
        revision = resolve_revision(args.model, None)
        result = {
            "mode": mode, "direction": direction,
            "input_provenance": {"type": "user_supplied", "text": args.text},
            "source_evidence": evidence, "prompt": prompt,
            "model": {"name": args.model, "revision": revision, "device": args.device,
                      "max_new_tokens": args.max_new_tokens, "loaded": False,
                      "allow_download": False},
            "sentence_verified": False, "training_performed": False,
        }
        if args.generate:
            runner = ModelRunner(model_name=args.model, adapter=None, revision=revision,
                                 device=args.device, allow_download=False,
                                 max_new_tokens=args.max_new_tokens)
            result["model"]["loaded"] = True
            raw = runner.generate(prompt)
            try:
                parsed = json.loads(raw)
            except (json.JSONDecodeError, TypeError):
                parsed = None
            tentative = parsed.get("tentative_translation") if isinstance(parsed, dict) else None
            output_lookup = (rag.lookup(tentative, "fix-to-ja")
                             if args.target == "fix" and isinstance(tentative, str) else None)
            result["raw_output"] = raw
            result["diagnostic"] = inspect_sentence_generation(raw, evidence, lookup, output_lookup)
        serialized = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(serialized, encoding="utf-8")
        print(serialized, end="")
        return 0
    except (OSError, ValueError, RuntimeError, TypeError) as error:
        print(json.dumps({"error": str(error), "mode": mode,
                          "sentence_verified": False, "training_performed": False},
                         ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
