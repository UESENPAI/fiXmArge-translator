#!/usr/bin/env python3
"""Check an adapter release; upload only with explicit --upload."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import sys

ALLOW = ["adapter_config.json", "adapter_model.safetensors", "tokenizer.json",
         "tokenizer_config.json", "special_tokens_map.json", "added_tokens.json",
         "merges.txt", "vocab.json", "README.md", "LICENSE", "NOTICE",
         "training_manifest.json", "evaluation.json", "publication_review.json"]


def inspect_release(folder: Path) -> dict:
    required = ["adapter_config.json", "adapter_model.safetensors",
                "tokenizer_config.json", "README.md", "LICENSE",
                "training_manifest.json", "evaluation.json", "publication_review.json"]
    blockers = [f"Missing {name}" for name in required if not (folder / name).is_file()]
    for name in ("README.md", "LICENSE"):
        if (folder / name).is_file() and (folder / name).stat().st_size == 0:
            blockers.append(f"Empty {name}")
    review_path = folder / "publication_review.json"
    if review_path.is_file():
        review = json.loads(review_path.read_text(encoding="utf-8-sig"))
        if review.get("source_rights_status") != "cleared":
            blockers.append("Source data rights are not recorded as cleared")
        if review.get("evaluation_status") != "reviewed":
            blockers.append("Evaluation has not been recorded as reviewed")
    adapter_path = folder / "adapter_config.json"
    if adapter_path.is_file():
        adapter = json.loads(adapter_path.read_text(encoding="utf-8-sig"))
        if adapter.get("base_model_name_or_path") not in (
                "Qwen/Qwen3-4B-Instruct-2507", "Qwen/Qwen3-1.7B"):
            blockers.append("Unexpected base model; review its license and recipe first")
    readme = folder / "README.md"
    if readme.is_file():
        text = readme.read_text(encoding="utf-8-sig")
        if "TODO" in text or "{{" in text:
            blockers.append("Model card still contains template placeholders")
        if "license: apache-2.0" not in text:
            blockers.append("Model card must state reviewed adapter license metadata")
    return {"folder": str(folder.resolve()), "ready": not blockers, "blockers": blockers,
            "upload_files": [name for name in ALLOW if (folder / name).is_file()],
            "mode": "validation_only"}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("folder", type=Path)
    parser.add_argument("--repo-id", help="Your Hugging Face namespace/repository")
    parser.add_argument("--upload", action="store_true")
    parser.add_argument("--public", action="store_true", help="Create a public repository (default: private)")
    args = parser.parse_args(argv)
    result = inspect_release(args.folder)
    if args.upload:
        if not args.repo_id or args.repo_id.count("/") != 1:
            parser.error("--upload requires --repo-id namespace/name")
        if not result["ready"]:
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return 2
        try:
            from huggingface_hub import HfApi
        except ImportError:
            parser.error("Install requirements-train.txt first")
        api = HfApi()  # Standard HF_TOKEN/environment or an existing HF login; never save credentials.
        api.create_repo(args.repo_id, repo_type="model", private=not args.public, exist_ok=True)
        info = api.upload_folder(repo_id=args.repo_id, repo_type="model",
            folder_path=str(args.folder), allow_patterns=ALLOW,
            commit_message="Publish LoRA adapter")
        result.update({"mode": "uploaded", "repo_id": args.repo_id, "commit_url": str(info.commit_url)})
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(2)
